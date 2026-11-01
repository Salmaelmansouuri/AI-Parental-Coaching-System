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


def load_resources():
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"Index introuvable : {INDEX_FILE}")

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"MÃ©tadonnÃ©es introuvables : {METADATA_FILE}"
        )

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration introuvable : {CONFIG_FILE}"
        )

    index = faiss.read_index(str(INDEX_FILE))

    with METADATA_FILE.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = json.load(file)

    return index, metadata, config


def search(
    question: str,
    model: SentenceTransformer,
    index,
    metadata: list[dict],
    top_k: int = TOP_K,
) -> list[dict]:
    question_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    question_embedding = np.asarray(
        question_embedding,
        dtype="float32",
    )

    scores, positions = index.search(
        question_embedding,
        top_k,
    )

    results = []

    for score, position in zip(scores[0], positions[0]):
        if position < 0:
            continue

        chunk = metadata[position]

        results.append(
            {
                "score": float(score),
                "chunk_id": chunk["chunk_id"],
                "document_name": chunk["document_name"],
                "page_number": chunk["page_number"],
                "text": chunk["text"],
            }
        )

    return results


def main() -> None:
    index, metadata, config = load_resources()

    model_name = config["model_name"]

    print(f"ModÃ¨le : {model_name}")
    print(f"Vecteurs chargÃ©s : {index.ntotal}")
    print()

    print("Tape une question sur le coaching parental.")
    print("Tape 'quitter' pour arrÃªter.")
    print()

    model = SentenceTransformer(model_name)

    while True:
        question = input("Question : ").strip()

        if question.lower() in {"quitter", "exit", "quit"}:
            print("Fin de la recherche.")
            break

        if not question:
            print("La question ne doit pas Ãªtre vide.\n")
            continue

        results = search(
            question=question,
            model=model,
            index=index,
            metadata=metadata,
        )

        print()
        print(f"{len(results)} passages trouvÃ©s :")
        print("=" * 80)

        for rank, result in enumerate(results, start=1):
            print(f"\nRÃ‰SULTAT {rank}")
            print(f"Score : {result['score']:.4f}")
            print(f"Document : {result['document_name']}")
            print(f"Page : {result['page_number']}")
            print(f"Chunk : {result['chunk_id']}")
            print()
            print(result["text"])
            print("-" * 80)

        print()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("ERREUR :")
        print(error)
