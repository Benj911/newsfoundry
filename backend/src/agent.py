import os
import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel

model = MistralModel("minimistral-8b-2512")

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
        "- Si l'utilisateur pose une question vague ou générale, sers-toi du contexte fourni.\n"
        "- Si l'utilisateur demande d'approfondir un sujet, de chercher des articles précis "
        "ou si le contexte fourni ne contient pas l'information, utilise systématiquement "
        "ton outil 'search_news' pour trouver de nouveaux articles.\n\n"
    )
    
    if ctx.deps:
        return base_prompt + "Contexte des actualités du jour :\n" + ctx.deps
        
    return base_prompt

@agent.tool_plain
async def search_news(query: str) -> str:
    """Recherche des articles de presse récents en français sur un sujet précis.

    Args:
        query: Le sujet, mot-clé ou entité à rechercher (ex: 'grève transports', 'SpaceX', 'budget 2026').
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
                    "number": 3  # On limite à 3 pour rester concis et préserver les tokens
                },
                headers={"x-api-key": api_key},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            articles = data.get("news", [])
            if not articles:
                return f"Aucun article trouvé pour la recherche : '{query}'."

            # Formatage synthétique pour le LLM
            formatted_articles = []
            for item in articles:
                title = item.get("title", "Sans titre")
                summary = item.get("summary", "Pas de résumé disponible")
                url = item.get("url", "")
                formatted_articles.append(f"- **{title}** : {summary} (Lien : {url})")

            return "\n\n".join(formatted_articles)

    except Exception as error:
        return f"Erreur technique lors de la recherche d'articles : {str(error)}"