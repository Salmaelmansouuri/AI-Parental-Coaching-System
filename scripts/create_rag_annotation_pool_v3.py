from pathlib import Path
import json

from backend.app.services.rag_service import retrieve_pet_sources


TEST_SET_FILE = Path("data/evaluation/rag_test_set.json")
OLD_POOL_FILE = Path("data/evaluation/rag_annotation_pool_v2.json")
METADATA_FILE = Path("data/vector_store/pet_metadata.json")
OUTPUT_FILE = Path("data/evaluation/rag_annotation_pool_v3.json")

POOL_SIZE = 20


def stable_key(item):
    return (
        item.get("document_name"),
        item.get("page_number"),
        item.get("chunk_position"),
    )


def main():

    test_set = json.loads(
        TEST_SET_FILE.read_text(encoding="utf-8")
    )

    metadata = json.loads(
        METADATA_FILE.read_text(encoding="utf-8")
    )

    metadata_by_id = {
        item["chunk_id"]: item
        for item in metadata
    }

    # Anciennes annotations réutilisables
    old_annotations = {}

    if OLD_POOL_FILE.exists():

        old_pool = json.loads(
            OLD_POOL_FILE.read_text(encoding="utf-8")
        )

        for question in old_pool["questions"]:

            qid = question["id"]

            for candidate in question["candidates"]:

                if candidate.get("relevant") is None:
                    continue

                key = (
                    qid,
                    candidate.get("document_name"),
                    candidate.get("page_number"),
                    candidate.get("chunk_position"),
                )

                old_annotations[key] = candidate["relevant"]

    questions_output = []

    reused = 0
    new_to_annotate = 0

    print()
    print("=" * 70)
    print("CREATION DU POOL RAG V3 - CORPUS ENRICHI")
    print("=" * 70)

    for question in test_set["questions"]:

        qid = question["id"]
        text = question["question"]

        print()
        print(f"Question {qid} : {text}")

        sources = retrieve_pet_sources(
            text,
            top_k=POOL_SIZE,
        )

        candidates = []

        for rank, source in enumerate(sources, start=1):

            metadata_item = metadata_by_id[
                source["chunk_id"]
            ]

            position = metadata_item[
                "chunk_position"
            ]

            annotation_key = (
                qid,
                source["document_name"],
                source["page_number"],
                position,
            )

            previous_label = old_annotations.get(
                annotation_key
            )

            if previous_label is not None:
                reused += 1
            else:
                new_to_annotate += 1

            candidates.append(
                {
                    "rank": rank,
                    "chunk_id": source["chunk_id"],
                    "document_name": source["document_name"],
                    "page_number": source["page_number"],
                    "chunk_position": position,
                    "text": source["text"],
                    "relevant": previous_label,
                }
            )

        questions_output.append(
            {
                "id": qid,
                "question": text,
                "candidates": candidates,
            }
        )

        print(
            f"  {len(candidates)} candidats"
        )

    output = {
        "metadata": {
            "name": "PET RAG annotation pool v3",
            "corpus_documents": 19,
            "corpus_chunks": len(metadata),
            "candidate_pool_size": POOL_SIZE,
            "retrieval_top_k": 4,
            "annotation_method": "Manual relevance annotation",
            "note": (
                "Corpus PET enrichi. Les anciennes annotations "
                "compatibles sont réutilisées via document + page "
                "+ position du chunk."
            ),
        },
        "questions": questions_output,
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
    print("=" * 70)
    print("POOL V3 CREE")
    print("=" * 70)
    print("Corpus :", 19, "documents")
    print("Chunks :", len(metadata))
    print("Annotations réutilisées :", reused)
    print("Nouvelles annotations nécessaires :", new_to_annotate)
    print("Fichier :", OUTPUT_FILE)


if __name__ == "__main__":
    main()
