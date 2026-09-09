from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel

# L'API key est lue automatiquement depuis la variable d'environnement MISTRAL_API_KEY
model = MistralModel("ministral-8b-2512")

# Définition du prompt système selon les consignes
system_prompt = (
    "Tu es l'assistant IA de NewsFoundry. Ton rôle est de répondre aux "
    "questions de l'utilisateur sur l'actualité de manière claire, "
    "concise, et toujours en utilisant le format Markdown pour structurer "
    "tes réponses (gras, listes à puces, etc.)."
)

agent = Agent(
    model,
    system_prompt=system_prompt
)