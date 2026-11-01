import json
from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


INPUT_FILE = Path(
    "data/aco_gemini_comparison.json"
)

OUTPUT_FILE = Path(
    "data/aco_evaluation_results.json"
)


load_dotenv()


def evaluate_answer(
    situation,
    answer,
):

    client = genai.Client(
        api_key=os.getenv(
            "GEMINI_API_KEY"
        )
    )

    prompt = f"""
Tu es un évaluateur expert d'un système
de coaching parental basé sur P.E.T.
(Parent Effectiveness Training).

Évalue uniquement cette réponse.

SITUATION DU PARENT :

{situation}


RÉPONSE DU COACH :

{answer}


Donne quatre scores entre 0 et 1 :

- faithfulness_pet :
respect des principes PET

- relevance :
adéquation avec la situation

- pet_structure :
présence des étapes PET adaptées

- completeness :
niveau de couverture du problème


Retourne uniquement un JSON :

{{
"faithfulness_pet": 0.0,
"relevance": 0.0,
"pet_structure": 0.0,
"completeness": 0.0
}}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    return json.loads(
        response.text
    )


def main():

    data = json.loads(
        INPUT_FILE.read_text(
            encoding="utf-8"
        )
    )


    situation = (
        "Mon fils de 10 ans se met en colère "
        "lorsque je lui demande d'arrêter "
        "la tablette."
    )


    results = {}


    for version in [
        "without_aco",
        "with_aco",
    ]:

        print(
            f"\nEvaluation {version}"
        )

        answer = data[version]["content"]

        results[version] = evaluate_answer(
            situation,
            answer,
        )

        print(
            results[version]
        )


    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


    print(
        "\nRésultat enregistré :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()