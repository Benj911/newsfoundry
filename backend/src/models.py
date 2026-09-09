from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str

class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    messages: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    # NOUVEAU : on stocke le contexte d'actualité figé au moment de la création
    system_prompt: str | None = Field(default="")
