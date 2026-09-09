from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
import uvicorn

from database import init_db, get_session
from models import User
from auth import verify_password, create_access_token

from fastapi import Depends
from models import Chat
from auth import get_current_user_id

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


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/chats")
async def create_chat(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    new_chat = Chat(user_id=user_id, messages=[])
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)
    return {"chat_id": new_chat.id}

@app.get("/chats/{chat_id}")
async def get_chat(chat_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    chat = session.get(Chat, chat_id)
    if not chat or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat introuvable")
    return {"id": chat.id, "messages": chat.messages}

class MessageRequest(BaseModel):
    content: str

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
    
    # 1. Sauvegarder le message de l'utilisateur (réassignation pour forcer l'update SQL)
    updated_messages = list(chat.messages)
    updated_messages.append({"role": "user", "content": message.content})
    
    # 2. Interroger PydanticAI de manière asynchrone
    try:
        result = await agent.run(message.content)
        ai_response = result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'IA: {str(e)}")

    # 3. Sauvegarder la réponse de l'IA
    updated_messages.append({"role": "assistant", "content": ai_response})
    chat.messages = updated_messages
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return {"reply": ai_response, "messages": chat.messages}