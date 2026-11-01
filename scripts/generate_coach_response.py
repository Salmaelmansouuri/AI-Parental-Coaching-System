from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai


PROMPT_FILE = Path("data/processed/last_prompt.txt")
MODEL_NAME = "gemini-3.6-flash"


def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Prompt introuvable : {PROMPT_FILE}. "
            "Lance d'abord build_prompt.py."
        )

    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError("Le fichier du prompt est vide.")

    return prompt


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "La variable GEMINI_API_KEY est absente du fichier .env."
        )

    prompt = load_prompt()

    client = genai.Client(api_key=api_key)

    print("Génération de la réponse en cours...")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    answer = response.text

    if not answer:
        raise ValueError("Gemini n'a retourné aucune réponse.")

    output_file = Path("data/processed/last_coach_response.txt")
    output_file.write_text(answer, encoding="utf-8")

    print()
    print("=" * 80)
    print("RÉPONSE DU COACH PARENTAL")
    print("=" * 80)
    print(answer)
    print()
    print(f"Réponse enregistrée dans : {output_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("ERREUR :")
        print(error)