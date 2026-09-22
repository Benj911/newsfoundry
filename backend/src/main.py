"""
Module Principal (Entry Point)
==============================
Ce module configure et expose l'API FastAPI de NewsFoundry.
Il définit les routes pour l'authentification, la gestion des discussions (chats),
l'interaction avec l'IA conversationnelle, ainsi que le pipeline RAG (Retrieval-Augmented Generation) 
utilisant LlamaIndex pour la génération de revues de presse sourcées.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
import uvicorn
import os
import httpx
from datetime import datetime, timezone

from database import init_db, get_session
from models import User, Chat, PressReviewOutput
from auth import verify_password, create_access_token, get_current_user_id
from agent import agent, press_review_agent, AgentDeps

# Imports dédiés au RAG via LlamaIndex
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding


# =============================================================================
# CONFIGURATION DE L'APPLICATION
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire de cycle de vie de l'application FastAPI.
    Exécute l'initialisation de la base de données au démarrage du serveur.
    """
    init_db()
    yield

app = FastAPI(title="NewsFoundry API", lifespan=lifespan)

# Configuration CORS pour autoriser les requêtes provenant du frontend (Vercel ou Localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

async def fetch_daily_news() -> str:
    """
    Récupère les actualités francophones du jour via la World News API.
    
    Returns:
        str: Une chaîne de caractères formatée listant les titres et résumés 
             des articles récents, destinée à enrichir le contexte initial de l'IA.
    """
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
                # Limitation à 5 articles par catégorie pour contrôler la taille du contexte
                for article in top.get("news", [])[:5]: 
                    title = article.get("title", "")
                    summary = article.get("summary", "")
                    news_context += f"- {title} : {summary}\n"
            return news_context
            
    except Exception:
        # En cas d'erreur API, on retourne un contexte vide pour ne pas bloquer la création du chat
        return ""


# =============================================================================
# SCHÉMAS DE REQUÊTES / RÉPONSES (PYDANTIC)
# =============================================================================

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


# =============================================================================
# ROUTES API : AUTHENTIFICATION
# =============================================================================

@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    """Authentifie un utilisateur et génère un jeton d'accès JWT."""
    statement = select(User).where(User.email == credentials.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
        
    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return LoginResponse(access_token=token)


# =============================================================================
# ROUTES API : GESTION DES DISCUSSIONS (CHATS)
# =============================================================================

@app.post("/chats")
async def create_chat(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Crée une nouvelle discussion et récupère le contexte d'actualité du jour."""
    news_context = await fetch_daily_news()
    new_chat = Chat(user_id=user_id, messages=[], system_prompt=news_context, loaded_articles=[])
    
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)
    
    return {"chat_id": new_chat.id}


@app.get("/chats")
async def list_chats(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Récupère l'historique des discussions de l'utilisateur."""
    statement = select(Chat).where(Chat.user_id == user_id)
    chats = session.exec(statement).all()
    
    # On ajoute created_at et updated_at dans la réponse de l'API
    return [
        {
            "id": c.id, 
            "preview": c.messages[0]["content"] if c.messages else "Nouvelle discussion",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if hasattr(c, "updated_at") and c.updated_at else None
        } 
        for c in chats
    ]


@app.get("/chats/{chat_id}")
async def get_chat(chat_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """Récupère le détail et les messages d'une discussion spécifique."""
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
    """
    Traite un nouveau message utilisateur.
    Construit l'historique contextuel, exécute l'agent IA, et met à jour la base de données
    avec les horodatages précis.
    """
    chat = session.get(Chat, chat_id)
    if not chat or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat introuvable")
    
    # Construction de l'historique récent (limité aux 4 derniers messages pour économiser les tokens)
    history_text = "Historique récent :\n"
    for msg in chat.messages[-4:]:
        role = "Utilisateur" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    
    full_query = f"{history_text}\n\nNouveau message : {message.content}"
    updated_messages = list(chat.messages)
    
    # Enregistrement du message utilisateur avec horodatage
    updated_messages.append({
        "role": "user", 
        "content": message.content,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Injection des dépendances (accès DB, contexte initial) requises par l'agent PydanticAI
    deps = AgentDeps(system_prompt_context=chat.system_prompt, session=session, chat_id=chat.id)
    
    try:
        result = await agent.run(full_query, deps=deps)
        ai_response = result.output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'IA: {str(e)}")

    # Enregistrement de la réponse IA avec horodatage
    updated_messages.append({
        "role": "assistant", 
        "content": ai_response,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    chat.messages = updated_messages
    
    # Mise à jour de l'horodatage global de la discussion pour le tri frontend
    if hasattr(chat, "updated_at"):
        chat.updated_at = datetime.now(timezone.utc)
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return {"reply": ai_response, "messages": chat.messages}


# =============================================================================
# ROUTES API : REVUES DE PRESSE ET RAG
# =============================================================================

@app.post("/chats/{chat_id}/press-reviews")
async def generate_press_review(
    chat_id: int, 
    request: PressReviewRequest, 
    user_id: int = Depends(get_current_user_id), 
    session: Session = Depends(get_session)
):
    """
    Génère une revue de presse structurée basée sur l'historique du chat.
    Implémente un pipeline RAG (LlamaIndex) pour extraire et analyser 
    le texte intégral des articles préalablement sourcés par l'agent.
    """
    chat = session.get(Chat, chat_id)
    if not chat or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat introuvable")

    rag_context = ""
    
    # Pipeline RAG conditionnel : Ne s'exécute que si l'agent a lu des URL durant la discussion
    if chat.loaded_articles:
        documents = []
        api_key = os.getenv("WORLD_NEWS_API_KEY")
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        
        # 1. Extraction asynchrone du texte brut des articles sourcés
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
                            # Transformation en document compatible LlamaIndex
                            documents.append(Document(text=text, metadata={"url": url}))
                except Exception as e:
                    print(f"Erreur extraction RAG pour {url}: {e}")

        # 2. Vectorisation et Recherche (Retrieval)
        if documents and mistral_api_key:
            Settings.embed_model = MistralAIEmbedding(api_key=mistral_api_key)
            index = VectorStoreIndex.from_documents(documents)
            
            # Récupération des 4 fragments les plus pertinents vis-à-vis du sujet demandé
            retriever = index.as_retriever(similarity_top_k=4)
            nodes = retriever.retrieve(request.topic)
            
            rag_context = "\n\n--- DÉTAILS DES ARTICLES LUS (RAG LLAMAINDEX) ---\n"
            for node in nodes:
                rag_context += f"Source ({node.metadata.get('url')}):\n{node.text}\n\n"

    # Construction du contexte final pour l'agent de synthèse
    history_text = f"Sujet demandé : {request.topic}\n\nHistorique du chat :\n"
    for msg in chat.messages:
        role = "Utilisateur" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
        
    if rag_context:
        history_text += rag_context

    # 3. Génération (Augmented Generation) via l'agent structuré
    try:
        result = await press_review_agent.run(history_text)
        review_data = result.data.model_dump() if hasattr(result, 'data') else result.output.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA Revue de Presse: {str(e)}")

    # Horodatage précis de la génération de la revue
    review_data["created_at"] = datetime.now(timezone.utc).isoformat()

    # Sauvegarde dans la base de données
    updated_reviews = list(chat.press_reviews)
    updated_reviews.append(review_data)
    chat.press_reviews = updated_reviews
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return review_data


@app.get("/press-reviews")
async def get_all_press_reviews(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    """
    Récupère l'ensemble des revues de presse générées par l'utilisateur 
    à travers toutes ses discussions.
    """
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