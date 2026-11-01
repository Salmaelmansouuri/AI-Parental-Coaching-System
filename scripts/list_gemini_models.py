import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY absente du fichier .env")

client = genai.Client(api_key=api_key)

print("Modèles disponibles pour ta clé :\n")

for model in client.models.list():
    model_name = getattr(model, "name", "")
    supported_actions = getattr(model, "supported_actions", [])

    if "generateContent" in supported_actions:
        print(model_name)