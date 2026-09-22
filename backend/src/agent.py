"""
Module Agent
============
Ce module définit les agents IA (basés sur PydanticAI et Mistral) utilisés 
par l'application NewsFoundry. Il contient l'agent de chat interactif avec 
ses outils de recherche, ainsi que l'agent spécialisé dans la génération 
de revues de presse structurées.
"""

import os
import httpx
from dataclasses import dataclass
from sqlmodel import Session
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel

from models import PressReviewOutput, Chat


# =============================================================================
# DÉPENDANCES ET CONFIGURATION GLOBALE
# =============================================================================

@dataclass
class AgentDeps:
    """
    Structure de dépendances (Dependency Injection) passée au contexte de l'agent.
    Permet de transmettre des variables d'état métier sans utiliser de variables globales.
    
    Attributs:
        system_prompt_context (str): Le résumé des actualités du jour.
        session (Session): La session active de la base de données SQLModel.
        chat_id (int): L'identifiant unique de la discussion en cours.
    """
    system_prompt_context: str
    session: Session
    chat_id: int

# Initialisation du modèle Mistral partagé par tous les agents
model = MistralModel("open-mistral-nemo")


# =============================================================================
# AGENT 1 : ASSISTANT DE CHAT INTERACTIF
# =============================================================================

# Déclaration de l'agent principal. Il utilise `AgentDeps` pour pouvoir interagir 
# avec la base de données depuis ses outils internes.
agent = Agent(
    model,
    deps_type=AgentDeps
)

@agent.system_prompt
def inject_daily_news(ctx: RunContext[AgentDeps]) -> str:
    """
    Génère le prompt système dynamique de l'agent.
    Il combine les règles de base et injecte le contexte des actualités du jour.
    """
    base_prompt = (
        "Tu es l'assistant IA de NewsFoundry. Ton rôle est d'analyser l'actualité "
        "et de répondre aux questions des utilisateurs de manière claire, concise et sourcée, "
        "toujours au format Markdown.\n\n"
        "RÈGLES D'UTILISATION DES OUTILS :\n"
        "- Si l'utilisateur pose une question générale, sers-toi du contexte fourni.\n"
        "- Si l'utilisateur demande d'approfondir un sujet qui n'est pas dans le contexte, "
        "utilise systématiquement ton outil 'search_news' pour trouver de nouveaux articles.\n"
        "- Si tu as l'URL d'un article et que l'utilisateur veut en connaître tous les détails, "
        "utilise ton outil 'read_full_article' pour en extraire le texte intégral.\n"
        "- Affiche toujours les URL en texte brut à la fin de tes résumés. Ne les masque jamais "
        "sous des liens cliquables Markdown.\n\n"
    )
    
    # Injection du contexte stocké lors de la création du Chat
    if ctx.deps.system_prompt_context:
        return base_prompt + "Contexte des actualités du jour :\n" + ctx.deps.system_prompt_context
        
    return base_prompt

@agent.tool_plain
async def search_news(query: str) -> str:
    """
    Outil IA : Recherche des articles de presse récents.
    
    Args:
        query (str): La requête de recherche générée par le LLM.
        
    Returns:
        str: Une liste d'articles formatée en Markdown, ou un message d'erreur.
    """
    api_key = os.getenv("WORLD_NEWS_API_KEY")
    if not api_key:
        return "Impossible d'effectuer la recherche : clé API manquante."

    try:
        # Appel HTTP asynchrone pour ne pas bloquer le serveur FastAPI
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.worldnewsapi.com/search-news",
                params={"text": query, "language": "fr", "number": 3},
                headers={"x-api-key": api_key},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

        articles = data.get("news", [])
        if not articles:
            return f"Aucun article trouvé pour la recherche : '{query}'."

        # Formatage des résultats pour que le LLM puisse facilement les lire
        formatted_articles = []
        for item in articles:
            title = item.get("title", "Sans titre")
            summary = item.get("summary", "Pas de résumé disponible")
            url = item.get("url", "")
            formatted_articles.append(f"- **{title}** : {summary} (Lien : {url})")

        return "\n\n".join(formatted_articles)

    except Exception as error:
        return f"Erreur technique lors de la recherche : {str(error)}"

@agent.tool
async def read_full_article(ctx: RunContext[AgentDeps], url: str) -> str:
    """
    Outil IA : Extrait le texte intégral d'un article de presse et l'archive pour le RAG.
    
    Args:
        ctx (RunContext[AgentDeps]): Le contexte injecté contenant la session de base de données.
        url (str): L'URL cible de l'article à analyser.
        
    Returns:
        str: Le contenu de l'article (tronqué) pour que le LLM le lise.
    """
    # --- ÉTAPE 1 : Mémorisation de l'URL ---
    # On sauvegarde l'URL lue dans le chat pour que l'agent de revue de presse 
    # (le système RAG LlamaIndex) sache plus tard quels articles ont été consultés.
    session = ctx.deps.session
    chat = session.get(Chat, ctx.deps.chat_id)
    
    if chat:
        loaded = list(chat.loaded_articles) if chat.loaded_articles else []
        if url not in loaded:
            loaded.append(url)
            chat.loaded_articles = loaded
            session.add(chat)
            session.commit()

    # --- ÉTAPE 2 : Extraction du texte ---
    api_key = os.getenv("WORLD_NEWS_API_KEY")
    if not api_key:
        return "Impossible d'extraire l'article : clé API manquante."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.worldnewsapi.com/extract-news",
                params={"url": url, "analyze": "false"},
                headers={"x-api-key": api_key},
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
            
            title = data.get("title", "Sans titre")
            text = data.get("text", "")
            
            if not text:
                return "Le texte de cet article n'a pas pu être extrait."
                
            # Limitation volontaire à 4000 caractères pour éviter de saturer 
            # la fenêtre de contexte du LLM (Token Limit).
            return f"Titre: {title}\n\nContenu:\n{text[:4000]}..."

    except Exception as error:
        return f"Erreur technique lors de l'extraction : {str(error)}"


# =============================================================================
# AGENT 2 : GÉNÉRATEUR DE REVUES DE PRESSE
# =============================================================================

# Agent secondaire qui ne gère aucune interaction directe avec les outils de recherche.
# Il est strictement contraint de générer une réponse respectant le schéma JSON
# défini par `PressReviewOutput`.
press_review_agent = Agent(
    model,
    output_type=PressReviewOutput,
    system_prompt=(
        "Tu es un journaliste rédacteur en chef expert. Ton rôle est de lire "
        "un historique de discussion et le contenu d'articles sources fournis en contexte, "
        "puis de générer une revue de presse structurée sur le sujet demandé.\n"
        "Tu dois extraire une synthèse générale précise, et lister les articles "
        "pertinents avec un résumé enrichi par les détails des textes sources.\n"
        "Tu réponds UNIQUEMENT via le format JSON strict demandé."
    )
)