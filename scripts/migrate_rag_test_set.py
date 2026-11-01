from pathlib import Path
import json


OLD_TEST_SET_FILE = Path(
    "data/evaluation/rag_test_set.json"
)

CHUNKS_FILE = Path(
    "data/processed/pet_chunks.json"
)

OUTPUT_FILE = Path(
    "data/evaluation/rag_test_set_v2.json"
)

OLD_CORPUS_SIZE = 655

# Dans l'ancien corpus :
# PET_01 = chunks 1 à 7
# PET_02 = chunks 8 à 14
# PET_03 commençait donc au chunk 15.
OLD_PET03_START = 15


def stable_reference(chunk: dict) -> dict:
    return {
        "document_name": chunk["document_name"],
        "page_number": chunk["page_number"],
        "chunk_position": chunk["chunk_position"],
    }


def main() -> None:

    if not OLD_TEST_SET_FILE.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {OLD_TEST_SET_FILE}"
        )

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {CHUNKS_FILE}"
        )

    old_test_set = json.loads(
        OLD_TEST_SET_FILE.read_text(
            encoding="utf-8"
        )
    )

    chunks = json.loads(
        CHUNKS_FILE.read_text(
            encoding="utf-8"
        )
    )

    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
    }

    new_pet03_chunks = [
        chunk
        for chunk in chunks
        if chunk["document_name"]
        == "PET_03_Fresh_Look_Research_Study.pdf"
    ]

    if not new_pet03_chunks:
        raise ValueError(
            "Impossible de trouver PET_03 dans le nouveau corpus."
        )

    new_pet03_start = min(
        chunk["chunk_id"]
        for chunk in new_pet03_chunks
    )

    shift = (
        new_pet03_start
        - OLD_PET03_START
    )

    print()
    print("=" * 60)
    print("MIGRATION DU BENCHMARK RAG")
    print("=" * 60)

    print(
        f"Ancien corpus : {OLD_CORPUS_SIZE} chunks"
    )

    print(
        f"Nouveau corpus : {len(chunks)} chunks"
    )

    print(
        f"Décalage détecté : +{shift} chunks"
    )

    print()

    new_questions = []

    for question in old_test_set["questions"]:

        migrated_chunks = []

        for old_chunk_id in question[
            "relevant_chunk_ids"
        ]:

            if old_chunk_id < OLD_PET03_START:
                new_chunk_id = old_chunk_id
            else:
                new_chunk_id = (
                    old_chunk_id + shift
                )

            chunk = chunks_by_id.get(
                new_chunk_id
            )

            if chunk is None:
                print(
                    f"ATTENTION : chunk "
                    f"{old_chunk_id} -> "
                    f"{new_chunk_id} introuvable."
                )
                continue

            migrated_chunks.append(
                {
                    "chunk_id": new_chunk_id,
                    **stable_reference(chunk),
                }
            )

        new_questions.append(
            {
                "id": question["id"],
                "question": question["question"],
                "relevant_chunks": migrated_chunks,
            }
        )

        print(
            f"Question {question['id']} : "
            f"{len(migrated_chunks)} "
            f"références migrées."
        )

    output = {
        "metadata": {
            "name":
                "PET RAG retrieval evaluation set v2",

            "language":
                "fr",

            "retrieval_top_k":
                4,

            "corpus_documents":
                8,

            "corpus_chunks":
                len(chunks),

            "previous_corpus_chunks":
                OLD_CORPUS_SIZE,

            "migration_shift":
                shift,

            "reference_format":
                "document_name + page_number + chunk_position",

            "note":
                (
                    "Les annotations de pertinence du benchmark "
                    "historique ont été migrées vers le nouveau "
                    "corpus. Les références stables évitent de "
                    "dépendre uniquement des chunk_id."
                ),
        },

        "questions":
            new_questions,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("MIGRATION TERMINÉE")
    print("=" * 60)

    print(
        f"Fichier créé : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()