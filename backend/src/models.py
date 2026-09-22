"""
Module Modèles de Données
=========================
Ce module définit l'ensemble des structures de données de l'application.
Il est divisé en deux parties :
1. Les schémas Pydantic : utilisés pour contraindre l'agent IA à générer
   des réponses structurées (Structured Outputs).
2. Les modèles SQLModel : utilisés pour définir le schéma de la base de 
   données relationnelle (ORM).
"""

from typing import Optional, List
from datetime import datetime, timezone

from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import Column, JSON


# =============================================================================
# SCHÉMAS PYDANTIC (POUR LA SORTIE STRUCTURÉE DE L'IA)
# =============================================================================
# Les descriptions (PydanticField) agissent comme des instructions explicites
# pour le LLM, lui indiquant exactement ce qu'il doit générer pour chaque champ.

class ArticleSummary(PydanticBaseModel):
    """
    Structure individuelle représentant le résumé d'un article de presse.
    """
    title: str = PydanticField(
        description="Le titre exact de l'article abordé."
    )
    summary: str = PydanticField(
        description="Un résumé clair et concis des informations principales de cet article."
    )

class PressReviewOutput(PydanticBaseModel):
    """
    Structure principale (schéma racine) exigée en sortie de l'agent de revue de presse.
    L'agent est contraint de retourner un JSON respectant strictement cette arborescence.
    """
    title: str = PydanticField(
        description="Un titre accrocheur, pertinent et global pour cette revue de presse."
    )
    general_summary: str = PydanticField(
        description="Une synthèse globale de la situation ou du sujet basée sur la discussion."
    )
    articles: List[ArticleSummary] = PydanticField(
        description="La liste détaillée des articles abordés, incluant leurs résumés."
    )


# =============================================================================
# MODÈLES DE BASE DE DONNÉES (SQLMODEL / ORM)
# =============================================================================

class User(SQLModel, table=True):
    """
    Représente la table des utilisateurs dans la base de données.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    
    # Horodatage géré automatiquement lors de la création de l'enregistrement
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Chat(SQLModel, table=True):
    """
    Représente la table des discussions (chats) dans la base de données.
    Chaque discussion est liée à un utilisateur (relation One-to-Many).
    """
    id: int | None = Field(default=None, primary_key=True)
    
    # Clé étrangère reliant la discussion à l'utilisateur propriétaire
    user_id: int = Field(foreign_key="user.id")
    
    # Contexte initial injecté dans l'IA lors de la création (actualités du jour)
    system_prompt: str = ""
    
    # L'utilisation de sa_column=Column(JSON) permet de stocker des structures 
    # flexibles (listes de dictionnaires) tout en bénéficiant des avantages 
    # de la base de données relationnelle pour le modèle parent.
    messages: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    press_reviews: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Historique des URL consultées par l'agent IA, crucial pour le pipeline RAG
    loaded_articles: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Gestion de l'horodatage pour l'interface utilisateur
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # updated_at doit être mis à jour manuellement dans la route lors d'un nouveau message
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))