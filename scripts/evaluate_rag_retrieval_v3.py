from pathlib import Path
import json

from backend.app.services.rag_service import (
    retrieve_pet_sources,
)


TEST_SET_FILE = Path(
    "data/evaluation/rag_test_set_v3.json"
)

METADATA_FILE = Path(
    "data/vector_store/pet_metadata.json"
)

RESULTS_FILE = Path(
    "data/evaluation/rag_retrieval_results_v3.json"
)

TOP_K = 4


def stable_key(
    document_name: str,
    page_number: int,
    chunk_position: int,
) -> tuple:

    return (
        document_name,
        page_number,
        chunk_position,
    )


def precision_at_k(
    retrieved: list[tuple],
    relevant: set[tuple],
) -> float:

    if not retrieved:
        return 0.0

    correct = sum(
        1
        for item in retrieved
        if item in relevant
    )

    return correct / len(retrieved)


def recall_at_k(
    retrieved: list[tuple],
    relevant: set[tuple],
) -> float:

    if not relevant:
        return 0.0

    correct = sum(
        1
        for item in retrieved
        if item in relevant
    )

    return correct / len(relevant)


def reciprocal_rank(
    retrieved: list[tuple],
    relevant: set[tuple],
) -> float:

    for rank, item in enumerate(
        retrieved,
        start=1,
    ):

        if item in relevant:
            return 1.0 / rank

    return 0.0


def main() -> None:

    test_set = json.loads(
        TEST_SET_FILE.read_text(
            encoding="utf-8"
        )
    )

    metadata = json.loads(
        METADATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    metadata_by_id = {
        item["chunk_id"]: item
        for item in metadata
    }

    results = []

    print()
    print("=" * 60)
    print("Ã‰VALUATION DU RETRIEVAL RAG V2")
    print("=" * 60)
    print()

    for question in test_set["questions"]:

        relevant = {
            stable_key(
                item["document_name"],
                item["page_number"],
                item["chunk_position"],
            )
            for item in question["relevant_chunks"]
        }

        sources = retrieve_pet_sources(
            question["question"],
            top_k=TOP_K,
        )

        retrieved = []

        retrieved_ids = []

        for source in sources:

            chunk_id = source["chunk_id"]

            metadata_item = metadata_by_id.get(
                chunk_id
            )

            if metadata_item is None:
                continue

            retrieved_ids.append(
                chunk_id
            )

            retrieved.append(
                stable_key(
                    metadata_item[
                        "document_name"
                    ],
                    metadata_item[
                        "page_number"
                    ],
                    metadata_item[
                        "chunk_position"
                    ],
                )
            )

        precision = precision_at_k(
            retrieved,
            relevant,
        )

        recall = recall_at_k(
            retrieved,
            relevant,
        )

        mrr = reciprocal_rank(
            retrieved,
            relevant,
        )

        results.append(
            {
                "id":
                    question["id"],

                "question":
                    question["question"],

                "retrieved_chunk_ids":
                    retrieved_ids,

                "precision_at_4":
                    round(
                        precision,
                        4,
                    ),

                "recall_at_4_pool":
                    round(
                        recall,
                        4,
                    ),

                "reciprocal_rank":
                    round(
                        mrr,
                        4,
                    ),
            }
        )

        print(
            f"Question {question['id']}"
        )

        print(
            f"  Chunks rÃ©cupÃ©rÃ©s : "
            f"{retrieved_ids}"
        )

        print(
            f"  Precision@4      : "
            f"{precision:.2f}"
        )

        print(
            f"  Recall@4 (pool)  : "
            f"{recall:.2f}"
        )

        print(
            f"  Reciprocal Rank  : "
            f"{mrr:.2f}"
        )

        print()

    mean_precision = sum(
        item["precision_at_4"]
        for item in results
    ) / len(results)

    mean_recall = sum(
        item["recall_at_4_pool"]
        for item in results
    ) / len(results)

    mean_mrr = sum(
        item["reciprocal_rank"]
        for item in results
    ) / len(results)

    output = {
        "evaluation": {
            "top_k":
                TOP_K,

            "number_of_questions":
                len(results),

            "corpus_chunks":
                test_set[
                    "metadata"
                ][
                    "corpus_chunks"
                ],

            "reference_format":
                (
                    "document_name + "
                    "page_number + "
                    "chunk_position"
                ),

            "note":
                (
                    "Benchmark historique migrÃ© "
                    "vers le corpus agrandi."
                ),
        },

        "summary": {
            "precision_at_4":
                round(
                    mean_precision,
                    4,
                ),

            "recall_at_4_pool":
                round(
                    mean_recall,
                    4,
                ),

            "mrr":
                round(
                    mean_mrr,
                    4,
                ),
        },

        "questions":
            results,
    }

    RESULTS_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print("MOYENNES")
    print("=" * 60)

    print(
        f"Precision@4     : "
        f"{mean_precision:.2f}"
    )

    print(
        f"Recall@4 (pool) : "
        f"{mean_recall:.2f}"
    )

    print(
        f"MRR             : "
        f"{mean_mrr:.2f}"
    )

    print()

    print(
        f"RÃ©sultats enregistrÃ©s dans : "
        f"{RESULTS_FILE}"
    )


if __name__ == "__main__":
    main()
