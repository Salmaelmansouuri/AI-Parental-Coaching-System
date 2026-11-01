from pathlib import Path
import json


POOL_FILE = Path(
    "data/evaluation/rag_annotation_pool_v2.json"
)

METADATA_FILE = Path(
    "data/vector_store/pet_metadata.json"
)


def save_pool(data: dict) -> None:
    POOL_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:

    if not POOL_FILE.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {POOL_FILE}"
        )

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {METADATA_FILE}"
        )

    data = json.loads(
        POOL_FILE.read_text(
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

    # Ajoute chunk_position pour avoir
    # une référence plus stable que chunk_id.
    for question in data["questions"]:

        for candidate in question["candidates"]:

            chunk_id = candidate["chunk_id"]

            item = metadata_by_id.get(
                chunk_id
            )

            if item:
                candidate["chunk_position"] = (
                    item["chunk_position"]
                )

    save_pool(data)

    total = sum(
        len(question["candidates"])
        for question in data["questions"]
    )

    answered = sum(
        1
        for question in data["questions"]
        for candidate in question["candidates"]
        if candidate.get("relevant") is not None
    )

    print()
    print("=" * 70)
    print("ANNOTATION MANUELLE DU RETRIEVAL RAG")
    print("=" * 70)

    print(
        f"Déjà annotés : {answered}/{total}"
    )

    print()
    print("O = pertinent")
    print("N = non pertinent")
    print("P = passer ce passage")
    print("Q = quitter et sauvegarder")
    print()

    for question in data["questions"]:

        candidates = question["candidates"]

        unanswered = [
            candidate
            for candidate in candidates
            if candidate.get("relevant") is None
        ]

        if not unanswered:
            continue

        print()
        print("=" * 70)
        print(
            f"QUESTION {question['id']}"
        )
        print("=" * 70)

        print(question["question"])
        print()

        for candidate in candidates:

            if candidate.get("relevant") is not None:
                continue

            print("-" * 70)

            print(
                f"Rang : {candidate['rank']}"
            )

            print(
                f"Chunk : {candidate['chunk_id']}"
            )

            print(
                f"Document : "
                f"{candidate['document_name']}"
            )

            print(
                f"Page : "
                f"{candidate['page_number']}"
            )

            print(
                f"Position : "
                f"{candidate.get('chunk_position', '?')}"
            )

            print()
            print(candidate["text"])
            print()

            while True:

                answer = input(
                    "Pertinent ? [O/N/P/Q] : "
                ).strip().lower()

                if answer in {
                    "o",
                    "n",
                    "p",
                    "q",
                }:
                    break

                print(
                    "Réponds seulement par "
                    "O, N, P ou Q."
                )

            if answer == "q":

                save_pool(data)

                print()
                print("Annotation sauvegardée.")
                print(
                    "Tu pourras reprendre "
                    "avec la même commande."
                )

                return

            if answer == "p":
                continue

            candidate["relevant"] = (
                answer == "o"
            )

            save_pool(data)

    print()
    print("=" * 70)
    print("ANNOTATION TERMINÉE")
    print("=" * 70)

    relevant_count = sum(
        1
        for question in data["questions"]
        for candidate in question["candidates"]
        if candidate.get("relevant") is True
    )

    print(
        f"Passages pertinents : "
        f"{relevant_count}"
    )

    print(
        f"Fichier sauvegardé : "
        f"{POOL_FILE}"
    )


if __name__ == "__main__":
    main()