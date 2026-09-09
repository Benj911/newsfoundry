from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
import uvicorn
import os
import httpx

from database import init_db, get_session
from models import User, Chat
from auth import verify_password, create_access_token, get_current_user_id
from agent import agent

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
        print("Attention: WORLD_NEWS_API_KEY manquante")
        return ""
    
    try:
        # Appel à l'API (on filtre pour avoir la France)
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
    except Exception as e:
        print(f"Erreur API News: {e}")
        return ""

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageRequest(BaseModel):
    content: str

@app.get("/")
async def hello():
    return {"message": "👋"}

@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == credentials.email)
    user = session.exec(statement).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return LoginResponse(access_token=token)

@app.post("/chats")
async def create_chat(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    # On va chercher les actus au moment de la création de la discussion
    news_context = await fetch_daily_news()
    
    # On sauvegarde ce contexte figé dans la base de données
    new_chat = Chat(user_id=user_id, messages=[], system_prompt=news_context)
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)
    return {"chat_id": new_chat.id}

@app.get("/chats")
async def list_chats(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    statement = select(Chat).where(Chat.user_id == user_id)
    chats = session.exec(statement).all()
    return [
        {
            "id": c.id, 
            "preview": c.messages[0]["content"] if c.messages else "Nouvelle discussion"
        } 
        for c in chats
    ]

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
    
    updated_messages = list(chat.messages)
    updated_messages.append({"role": "user", "content": message.content})
    
    try:
        # On passe le system_prompt de la BDD à l'agent Mistral via `deps` !
        result = await agent.run(message.content, deps=chat.system_prompt)
        ai_response = result.output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'IA: {str(e)}")

    updated_messages.append({"role": "assistant", "content": ai_response})
    chat.messages = updated_messages
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return {"reply": ai_response, "messages": chat.messages}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)