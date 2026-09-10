import os
import httpx
from dataclasses import dataclass
from sqlmodel import Session
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel

from models import PressReviewOutput, Chat

# Structure pour injecter la base de données et l'ID du chat dans l'agent
@dataclass
class AgentDeps:
    system_prompt_context: str
    session: Session
    chat_id: int

model = MistralModel("open-mistral-nemo")

# ==========================================
# AGENT 1 : L'agent de chat interactif
# ==========================================
agent = Agent(
    model,
    deps_type=AgentDeps
)

@agent.system_prompt
def inject_daily_news(ctx: RunContext[AgentDeps]) -> str:
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
    
    if ctx.deps.system_prompt_context:
        return base_prompt + "Contexte des actualités du jour :\n" + ctx.deps.system_prompt_context
        
    return base_prompt

@agent.tool_plain
async def search_news(query: str) -> str:
    """Recherche des articles de presse récents en français sur un sujet précis."""
    api_key = os.getenv("WORLD_NEWS_API_KEY")
    if not api_key:
        return "Impossible d'effectuer la recherche : clé API manquante."

    try:
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
    """Extrait le texte intégral d'un article de presse à partir de son URL et le mémorise."""
    # 1. Sauvegarde de l'URL dans la base de données
    session = ctx.deps.session
    chat = session.get(Chat, ctx.deps.chat_id)
    if chat:
        loaded = list(chat.loaded_articles) if chat.loaded_articles else []
        if url not in loaded:
            loaded.append(url)
            chat.loaded_articles = loaded
            session.add(chat)
            session.commit()

    # 2. Extraction du texte
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
                
            return f"Titre: {title}\n\nContenu:\n{text[:4000]}..."

    except Exception as error:
        return f"Erreur technique lors de l'extraction : {str(error)}"

# ==========================================
# AGENT 2 : L'agent de revue de presse
# ==========================================
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