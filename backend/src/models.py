from typing import Optional, List
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import Column, JSON

# --- SCHÉMAS PYDANTIC POUR LA SORTIE STRUCTURÉE DE L'IA ---
class ArticleSummary(PydanticBaseModel):
    title: str = PydanticField(description="Le titre exact de l'article")
    summary: str = PydanticField(description="Un résumé clair et concis des informations de cet article")

class PressReviewOutput(PydanticBaseModel):
    title: str = PydanticField(description="Un titre accrocheur pour cette revue de presse")
    general_summary: str = PydanticField(description="Une synthèse globale de la situation basée sur la discussion")
    articles: List[ArticleSummary] = PydanticField(description="La liste des articles abordés avec leurs résumés")

# --- MODÈLES DE BASE DE DONNÉES ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str

class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    system_prompt: str = ""
    messages: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    press_reviews: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    
    # NOUVEAU : Historique des URL lues par l'outil de l'agent
    loaded_articles: list[str] = Field(default_factory=list, sa_column=Column(JSON))