from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


VECTOR_FOLDER = Path("data/vector_store")
INDEX_FILE = VECTOR_FOLDER / "pet_faiss.index"
METADATA_FILE = VECTOR_FOLDER / "pet_metadata.json"
CONFIG_FILE = VECTOR_FOLDER / "pet_index_config.json"

TOP_K = 4


QUERY_EXPANSIONS = {
    "conflit": (
        "conflict resolution Method III no-lose method "
        "mutually acceptable solution"
    ),
    "besoins opposés": (
        "conflicting needs parent child Method III "
        "no-lose conflict resolution"
    ),
    "écoute active": (
        "active listening reflect feelings attending "
        "passive listening empathy"
    ),
    "colère": (
        "anger strong feelings active listening empathy "
        "reflecting feelings"
    ),
}


def expand_query(question: str) -> str:
    question_lower = question.lower()
    expansions = []

    for keyword, expansion in QUERY_EXPANSIONS.items():
        if keyword in question_lower:
            expansions.append(expansion)

    if not expansions:
        return question

    return question + " " + " ".join(expansions)


def load_resources():
    index = faiss.read_index(str(INDEX_FILE))

    with METADATA_FILE.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = json.load(file)

    return index, metadata, config


def retrieve(
    question: str,
    model: SentenceTransformer,
    index,
    metadata: list[dict],
) -> list[dict]:
    expanded_question = expand_query(question)

    embedding = model.encode(
        [expanded_question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embedding = np.asarray(
        embedding,
        dtype="float32",
    )

    scores, positions = index.search(
        embedding,
        TOP_K,
    )

    results = []

    for score, position in zip(scores[0], positions[0]):
        if position < 0:
            continue

        chunk = metadata[position]

        results.append(
            {
                "score": float(score),
                "document_name": chunk["document_name"],
                "page_number": chunk["page_number"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
            }
        )

    return results


def build_sources(results: list[dict]) -> str:
    source_blocks = []

    for index, result in enumerate(results, start=1):
        source_blocks.append(
            f"""
SOURCE {index}
Document : {result["document_name"]}
Page : {result["page_number"]}
Score : {result["score"]:.4f}
Extrait :
{result["text"]}
""".strip()
        )

    return "\n\n".join(source_blocks)


def build_prompt(
    question: str,
    child_age: int,
    child_gender: str,
    family_context: str,
    previous_attempts: str,
    results: list[dict],
) -> str:
    sources = build_sources(results)

    return f"""
Tu es un assistant intelligent de coaching parental basé sur la méthode
Parent Effectiveness Training, dite P.E.T.

Tu accompagnes le parent sans le juger et sans culpabiliser l'enfant.

RÈGLES OBLIGATOIRES

1. Base ta réponse uniquement sur les sources PET fournies.
2. Ne pose aucun diagnostic médical ou psychologique.
3. Ne remplace pas un psychologue, un médecin ou un professionnel.
4. N'invente pas une information absente du contexte ou des sources.
5. Ne conseille pas la violence, l'humiliation, la menace ou la punition.
6. Utilise un langage simple, empathique et concret.
7. Prends en compte l'âge de l'enfant et le contexte familial.
8. Pose des questions de clarification si les informations sont insuffisantes.
9. Propose au maximum une intervention principale à la fois.
10. Explique au parent ce qu'il doit observer après l'intervention.
11. Cite les documents et les pages utilisés.
12. En cas de danger, de violence, d'abus ou d'urgence, recommande une aide
humaine immédiate au lieu de poursuivre un coaching normal.

INFORMATIONS SUR LA SITUATION

Âge de l'enfant : {child_age}
Sexe de l'enfant : {child_gender}
Contexte familial : {family_context}
Tentatives déjà réalisées : {previous_attempts}

QUESTION DU PARENT

{question}

SOURCES PET RÉCUPÉRÉES

{sources}

FORMAT DE RÉPONSE ATTENDU

1. Compréhension de la situation
2. Une à trois questions de clarification, seulement si nécessaire
3. Principe PET pertinent
4. Intervention concrète proposée
5. Exemple de phrase que le parent peut utiliser
6. Éléments à observer
7. Sources utilisées

Génère maintenant la réponse en français.
""".strip()


def main() -> None:
    index, metadata, config = load_resources()
    model = SentenceTransformer(config["model_name"])

    question = input("Question du parent : ").strip()
    child_age = int(input("Âge de l'enfant : ").strip())
    child_gender = input("Sexe de l'enfant : ").strip()
    family_context = input("Contexte familial : ").strip()
    previous_attempts = input(
        "Interventions déjà essayées : "
    ).strip()

    results = retrieve(
        question=question,
        model=model,
        index=index,
        metadata=metadata,
    )

    prompt = build_prompt(
        question=question,
        child_age=child_age,
        child_gender=child_gender,
        family_context=family_context,
        previous_attempts=previous_attempts,
        results=results,
    )

    output_file = Path("data/processed/last_prompt.txt")
    output_file.write_text(
        prompt,
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print("PROMPT GÉNÉRÉ")
    print("=" * 80)
    print(prompt)

    print()
    print(f"Prompt enregistré dans : {output_file}")


if __name__ == "__main__":
    try:
        main()
    except ValueError:
        print("L'âge doit être un nombre entier.")
    except Exception as error:
        print("ERREUR :")
        print(error)