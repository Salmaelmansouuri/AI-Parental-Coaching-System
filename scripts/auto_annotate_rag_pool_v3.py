from pathlib import Path
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

POOL_FILE = Path(
    "data/evaluation/rag_annotation_pool_v3.json"
)

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


def save(data):
    POOL_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY absente du fichier .env"
        )

    data = json.loads(
        POOL_FILE.read_text(encoding="utf-8")
    )

    client = genai.Client(api_key=api_key)

    total_new = 0

    for question in data["questions"]:

        candidates = [
            c for c in question["candidates"]
            if c.get("relevant") is None
        ]

        if not candidates:
            continue

        print()
        print("=" * 70)
        print(
            f"Question {question['id']} : "
            f"{question['question']}"
        )
        print(
            f"{len(candidates)} passages à annoter"
        )

        passages = "\n\n".join(
            [
                (
                    f"CHUNK_ID: {c['chunk_id']}\n"
                    f"DOCUMENT: {c['document_name']}\n"
                    f"PAGE: {c['page_number']}\n"
                    f"TEXTE:\n{c['text']}"
                )
                for c in candidates
            ]
        )

        prompt = f"""
Tu évalues la pertinence de passages documentaires
pour un système RAG basé sur Parent Effectiveness
Training (P.E.T.).

QUESTION UTILISATEUR :
{question['question']}

Pour chaque passage, décide s'il est pertinent.

Un passage est PERTINENT s'il contient une information
qui pourrait réellement aider à répondre à la question,
par exemple :
- écoute active ;
- sentiments et besoins ;
- message-je ;
- ownership du problème ;
- résolution de conflit ;
- Method III ;
- limites ;
- communication parent-enfant ;
- conseil PET directement applicable à la situation.

Un passage est NON PERTINENT s'il :
- parle principalement d'un autre sujet ;
- contient seulement des informations administratives,
  bibliographiques ou statistiques sans utilité pour la réponse ;
- mentionne PET sans apporter d'information utile ;
- est trop vague pour aider à répondre à la question.

Ne juge pas la qualité rédactionnelle.
Juge uniquement la pertinence pour répondre à la QUESTION.

PASSAGES :

{passages}
""".strip()

        schema = {
            "type": "object",
            "properties": {
                "labels": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chunk_id": {
                                "type": "integer"
                            },
                            "relevant": {
                                "type": "boolean"
                            },
                            "reason": {
                                "type": "string"
                            },
                        },
                        "required": [
                            "chunk_id",
                            "relevant",
                            "reason",
                        ],
                    },
                }
            },
            "required": ["labels"],
        }

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0,
            ),
        )

        result = json.loads(response.text)

        labels = {
            item["chunk_id"]: item
            for item in result["labels"]
        }

        for candidate in candidates:

            label = labels.get(
                candidate["chunk_id"]
            )

            if label is None:
                print(
                    "ATTENTION : pas de label pour",
                    candidate["chunk_id"]
                )
                continue

            candidate["relevant"] = bool(
                label["relevant"]
            )

            candidate[
                "automatic_annotation_reason"
            ] = label["reason"]

            candidate[
                "annotation_source"
            ] = "LLM"

            total_new += 1

        save(data)

        print(
            f"Annotations enregistrées. "
            f"Total automatique : {total_new}"
        )

        time.sleep(1)

    data["metadata"][
        "annotation_method"
    ] = (
        "Hybrid relevance annotation: "
        "existing human labels + LLM-assisted labels"
    )

    data["metadata"][
        "automatic_annotation_model"
    ] = MODEL

    save(data)

    remaining = sum(
        1
        for q in data["questions"]
        for c in q["candidates"]
        if c.get("relevant") is None
    )

    relevant = sum(
        1
        for q in data["questions"]
        for c in q["candidates"]
        if c.get("relevant") is True
    )

    print()
    print("=" * 70)
    print("ANNOTATION AUTOMATIQUE TERMINEE")
    print("=" * 70)
    print("Annotations automatiques :", total_new)
    print("Passages pertinents :", relevant)
    print("Restants sans annotation :", remaining)
    print("Fichier :", POOL_FILE)


if __name__ == "__main__":
    main()
