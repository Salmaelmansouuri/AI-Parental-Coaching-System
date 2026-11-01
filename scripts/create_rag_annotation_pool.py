from pathlib import Path
import json

from backend.app.services.rag_service import retrieve_pet_sources


TEST_SET_FILE = Path(
    "data/evaluation/rag_test_set.json"
)

OUTPUT_FILE = Path(
    "data/evaluation/rag_annotation_pool_v2.json"
)

POOL_SIZE = 20


def main() -> None:

    if not TEST_SET_FILE.exists():
        raise FileNotFoundError(
            f"Jeu de test introuvable : {TEST_SET_FILE}"
        )

    test_set = json.loads(
        TEST_SET_FILE.read_text(
            encoding="utf-8"
        )
    )

    annotation_questions = []

    print()
    print("=" * 60)
    print("CRÉATION DU POOL D'ANNOTATION RAG V2")
    print("=" * 60)
    print()

    for item in test_set["questions"]:

        question = item["question"]

        print(
            f"Question {item['id']} : {question}"
        )

        sources = retrieve_pet_sources(
            question,
            top_k=POOL_SIZE,
        )

        candidates = []

        for rank, source in enumerate(
            sources,
            start=1,
        ):

            candidate = {
                "rank": rank,

                "chunk_id":
                    source["chunk_id"],

                "document_name":
                    source["document_name"],

                "page_number":
                    source["page_number"],

                "text":
                    source["text"],

                "relevant":
                    None,
            }

            candidates.append(candidate)

        annotation_questions.append(
            {
                "id": item["id"],
                "question": question,
                "candidates": candidates,
            }
        )

        print(
            f"  {len(candidates)} candidats enregistrés."
        )

    output = {
        "metadata": {
            "name":
                "PET RAG annotation pool v2",

            "corpus_documents": 8,

            "corpus_chunks": 747,

            "candidate_pool_size":
                POOL_SIZE,

            "annotation_method":
                "Manual relevance annotation",
        },

        "questions":
            annotation_questions,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
    print("TERMINÉ")
    print("=" * 60)

    print(
        f"Fichier créé : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()