import os
import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel

# On importe notre nouveau modèle de sortie structurée
from models import PressReviewOutput

model = MistralModel("open-mistral-nemo")

# ==========================================
# AGENT 1 : L'agent de chat interactif
# ==========================================
agent = Agent(
    model,
    deps_type=str
)

@agent.system_prompt
def inject_daily_news(ctx: RunContext[str]) -> str:
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
        "sous des liens cliquables Markdown (interdiction absolue d'utiliser le format [texte](url)).\n\n"
    )
    
    if ctx.deps:
        return base_prompt + "Contexte des actualités du jour :\n" + ctx.deps
        
    return base_prompt

@agent.tool_plain
async def search_news(query: str) -> str:
    """Recherche des articles de presse récents en français sur un sujet précis.

    Args:
        query: Le sujet, mot-clé ou entité à rechercher (ex: 'grève transports', 'SpaceX', 'budget').
    """
    api_key = os.getenv("WORLD_NEWS_API_KEY")
    if not api_key:
        return "Impossible d'effectuer la recherche : clé API manquante."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.worldnewsapi.com/search-news",
                params={
                    "text": query,
                    "language": "fr",
                    "number": 3
                },
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
        return f"Erreur technique lors de la recherche d'articles : {str(error)}"

@agent.tool_plain
async def read_full_article(url: str) -> str:
    """Extrait le texte intégral d'un article de presse à partir de son URL.

    Args:
        url: L'URL exacte de l'article à lire.
    """
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
        return f"Erreur technique lors de l'extraction de l'article : {str(error)}"

# ==========================================
# AGENT 2 : L'agent de revue de presse
# ==========================================
press_review_agent = Agent(
    model,
    result_type=PressReviewOutput,
    system_prompt=(
        "Tu es un journaliste rédacteur en chef expert. Ton rôle est de lire "
        "un historique de discussion entre un utilisateur et un assistant IA, "
        "et de générer une revue de presse structurée sur un sujet précis demandé.\n"
        "Tu dois extraire une synthèse générale de l'évolution du sujet, et lister "
        "précisément chaque article mentionné dans l'historique avec son résumé.\n"
        "Tu réponds UNIQUEMENT via le format JSON strict demandé."
    )
)