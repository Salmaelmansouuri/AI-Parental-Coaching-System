from pathlib import Path
import json

POOL_FILE = Path(
    "data/evaluation/rag_annotation_pool_v3.json"
)

OUTPUT_FILE = Path(
    "data/evaluation/rag_test_set_v3.json"
)


def main():

    pool = json.loads(
        POOL_FILE.read_text(encoding="utf-8")
    )

    questions = []

    for question in pool["questions"]:

        relevant_chunks = []

        for candidate in question["candidates"]:

            if candidate.get("relevant") is True:

                relevant_chunks.append(
                    {
                        "chunk_id": candidate["chunk_id"],
                        "document_name": candidate["document_name"],
                        "page_number": candidate["page_number"],
                        "chunk_position": candidate["chunk_position"],
                    }
                )

        questions.append(
            {
                "id": question["id"],
                "question": question["question"],
                "relevant_chunks": relevant_chunks,
            }
        )

        print(
            f"Question {question['id']} : "
            f"{len(relevant_chunks)} passages pertinents"
        )

    output = {
        "metadata": {
            "name": "PET RAG retrieval evaluation set v3",
            "language": "fr",
            "retrieval_top_k": 4,
            "corpus_documents": 19,
            "corpus_chunks": 918,
            "candidate_pool_size": 20,
            "reference_format":
                "document_name + page_number + chunk_position",
            "annotation_method":
                "Hybrid relevance annotation: existing human labels + LLM-assisted labels",
            "note":
                "Benchmark construit sur le corpus PET enrichi.",
        },
        "questions": questions,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    total = sum(
        len(q["relevant_chunks"])
        for q in questions
    )

    print()
    print("Benchmark V3 créé :", OUTPUT_FILE)
    print("Total passages pertinents :", total)


if __name__ == "__main__":
    main()
