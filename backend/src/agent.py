from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel

# L'API key est lue automatiquement depuis la variable d'environnement MISTRAL_API_KEY
model = MistralModel("ministral-8b-2512")

# L'agent attend désormais une dépendance de type "str" (le texte de nos actualités)
agent = Agent(
    model,
    deps_type=str
)

# Génération dynamique du prompt système au moment de la requête
@agent.system_prompt
def inject_daily_news(ctx: RunContext[str]) -> str:
    base_prompt = (
        "Tu es l'assistant IA de NewsFoundry. Ton rôle est de répondre aux "
        "questions de l'utilisateur sur l'actualité de manière claire, "
        "concise, et toujours en utilisant le format Markdown pour structurer "
        "tes réponses (gras, listes à puces, etc.).\n\n"
    )
    
    # Si des actualités ont été passées dans les dépendances, on les ajoute au prompt
    if ctx.deps:
        return base_prompt + "Voici les actualités récentes pour t'aider à répondre :\n" + ctx.deps
        
    return base_prompt