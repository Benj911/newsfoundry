from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
import uvicorn
import os
import httpx

from database import init_db, get_session
from models import User, Chat, PressReviewOutput
from auth import verify_password, create_access_token, get_current_user_id
from agent import agent, press_review_agent, AgentDeps

# LlamaIndex Imports
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="NewsFoundry API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def fetch_daily_news() -> str:
    api_key = os.getenv("WORLD_NEWS_API_KEY")
    if not api_key:
        return ""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.worldnewsapi.com/top-news?source-country=fr&language=fr",
                headers={"x-api-key": api_key}
            )
            response.raise_for_status()
            data = response.json()
            news_context = ""
            for top in data.get("top_news", []):
                for article in top.get("news", [])[:5]: 
                    title = article.get("title", "")
                    summary = article.get("summary", "")
                    news_context += f"- {title} : {summary}\n"
            return news_context
    except Exception:
        return ""

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageRequest(BaseModel):
    content: str

class PressReviewRequest(BaseModel):
    topic: str

@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == credentials.email)
    user = session.exec(statement).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return LoginResponse(access_token=token)

@app.post("/chats")
async def create_chat(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    news_context = await fetch_daily_news()
    new_chat = Chat(user_id=user_id, messages=[], system_prompt=news_context, loaded_articles=[])
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)
    return {"chat_id": new_chat.id}

@app.get("/chats")
async def list_chats(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    statement = select(Chat).where(Chat.user_id == user_id)
    chats = session.exec(statement).all()
    return [{"id": c.id, "preview": c.messages[0]["content"] if c.messages else "Nouvelle discussion"} for c in chats]

@app.get("/chats/{chat_id}")
async def get_chat(chat_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    chat = session.get(Chat, chat_id)
    if not chat or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat introuvable")
    return {"id": chat.id, "messages": chat.messages}

@app.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: int, 
    message: MessageRequest, 
    user_id: int = Depends(get_current_user_id), 
    session: Session = Depends(get_session)
):
    chat = session.get(Chat, chat_id)
    if not chat or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat introuvable")
    
    history_text = "Historique récent :\n"
    for msg in chat.messages[-4:]:
        role = "Utilisateur" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    
    full_query = f"{history_text}\n\nNouveau message : {message.content}"
    
    updated_messages = list(chat.messages)
    updated_messages.append({"role": "user", "content": message.content})
    
    # Injection du nouveau contexte (AgentDeps)
    deps = AgentDeps(system_prompt_context=chat.system_prompt, session=session, chat_id=chat.id)
    
    try:
        result = await agent.run(full_query, deps=deps)
        ai_response = result.output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'IA: {str(e)}")

    updated_messages.append({"role": "assistant", "content": ai_response})
    chat.messages = updated_messages
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return {"reply": ai_response, "messages": chat.messages}

@app.post("/chats/{chat_id}/press-reviews")
async def generate_press_review(
    chat_id: int, 
    request: PressReviewRequest, 
    user_id: int = Depends(get_current_user_id), 
    session: Session = Depends(get_session)
):
    chat = session.get(Chat, chat_id)
    if not chat or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat introuvable")

    # --- ÉTAPE 8 : RAG avec LlamaIndex ---
    rag_context = ""
    if chat.loaded_articles:
        documents = []
        api_key = os.getenv("WORLD_NEWS_API_KEY")
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        
        # 1. Extraction du texte complet des URL lues
        async with httpx.AsyncClient() as client:
            for url in chat.loaded_articles:
                try:
                    resp = await client.get(
                        "https://api.worldnewsapi.com/extract-news",
                        params={"url": url, "analyze": "false"},
                        headers={"x-api-key": api_key},
                        timeout=15.0
                    )
                    if resp.status_code == 200:
                        text = resp.json().get("text", "")
                        if text:
                            documents.append(Document(text=text, metadata={"url": url}))
                except Exception as e:
                    print(f"Erreur extraction RAG pour {url}: {e}")

        # 2. Création de l'index vectoriel et recherche des extraits pertinents
        if documents and mistral_api_key:
            Settings.embed_model = MistralAIEmbedding(api_key=mistral_api_key)
            index = VectorStoreIndex.from_documents(documents)
            retriever = index.as_retriever(similarity_top_k=4)
            nodes = retriever.retrieve(request.topic)
            
            rag_context = "\n\n--- DÉTAILS DES ARTICLES LUS (RAG LLAMAINDEX) ---\n"
            for node in nodes:
                rag_context += f"Source ({node.metadata.get('url')}):\n{node.text}\n\n"

    # --- GÉNÉRATION DE LA REVUE DE PRESSE ---
    history_text = f"Sujet demandé : {request.topic}\n\nHistorique du chat :\n"
    for msg in chat.messages:
        role = "Utilisateur" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
        
    # On ajoute le fruit de notre recherche LlamaIndex au prompt final
    if rag_context:
        history_text += rag_context

    try:
        result = await press_review_agent.run(history_text)
        review_data = result.data.model_dump() if hasattr(result, 'data') else result.output.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA Revue de Presse: {str(e)}")

    updated_reviews = list(chat.press_reviews)
    updated_reviews.append(review_data)
    chat.press_reviews = updated_reviews
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return review_data

@app.get("/press-reviews")
async def get_all_press_reviews(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    statement = select(Chat).where(Chat.user_id == user_id)
    chats = session.exec(statement).all()
    
    all_reviews = []
    for chat in chats:
        if chat.press_reviews:
            for review in chat.press_reviews:
                review_with_context = dict(review)
                review_with_context["chat_id"] = chat.id
                all_reviews.append(review_with_context)
                
    return all_reviews

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)