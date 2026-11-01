from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


VECTOR_FOLDER = Path("data/vector_store")
INDEX_FILE = VECTOR_FOLDER / "pet_faiss.index"
METADATA_FILE = VECTOR_FOLDER / "pet_metadata.json"
CONFIG_FILE = VECTOR_FOLDER / "pet_index_config.json"

TOP_K = 5


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
    expanded_terms = []

    normalized_question = question.lower()

    for keyword, expansion in QUERY_EXPANSIONS.items():
        if keyword in normalized_question:
            expanded_terms.append(expansion)

    if not expanded_terms:
        return question

    return question + " " + " ".join(expanded_terms)


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
    top_k: int = TOP_K,
) -> list[dict]:
    expanded_question = expand_query(question)

    embedding = model.encode(
        [expanded_question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embedding = np.asarray(embedding, dtype="float32")

    scores, positions = index.search(embedding, top_k)

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


def build_context(results: list[dict]) -> str:
    context_parts = []

    for rank, result in enumerate(results, start=1):
        source = (
            f"[Source {rank} — {result['document_name']} "
            f"— page {result['page_number']} "
            f"— score {result['score']:.4f}]"
        )

        context_parts.append(
            f"{source}\n{result['text']}"
        )

    return "\n\n".join(context_parts)


def main() -> None:
    index, metadata, config = load_resources()

    model = SentenceTransformer(config["model_name"])

    question = input("Question du parent : ").strip()

    if not question:
        print("La question est vide.")
        return

    expanded_question = expand_query(question)

    print()
    print("Requête enrichie :")
    print(expanded_question)

    results = retrieve(
        question=question,
        model=model,
        index=index,
        metadata=metadata,
    )

    context = build_context(results)

    print()
    print("=" * 80)
    print("CONTEXTE RAG")
    print("=" * 80)
    print(context)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERREUR :")
        print(error)