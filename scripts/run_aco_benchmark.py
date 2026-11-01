import json
import time
from pathlib import Path

from backend.app.services.rag_service import (
    generate_parental_coach_response,
)


INPUT_FILE = Path(
    "data/aco_test_situations.json"
)

OUTPUT_FILE = Path(
    "data/aco_benchmark_results.json"
)


PROFILES = {
    1: {
        "child_age": 10,
        "child_gender": "garçon",
    },
    2: {
        "child_age": 8,
        "child_gender": "fille",
    },
    3: {
        "child_age": 15,
        "child_gender": "garçon",
    },
    4: {
        "child_age": 10,
        "child_gender": "non précisé",
    },
    5: {
        "child_age": 11,
        "child_gender": "garçon",
    },
    6: {
        "child_age": 10,
        "child_gender": "fille",
    },
}


def load_results():
    if not OUTPUT_FILE.exists():
        return {
            "questions": []
        }

    try:
        return json.loads(
            OUTPUT_FILE.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError:
        return {
            "questions": []
        }


def save_results(data):
    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main():

    situations = json.loads(
        INPUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    results = load_results()

    completed_ids = {
        item["id"]
        for item in results["questions"]
        if item.get("status") == "completed"
    }

    print()
    print("=" * 70)
    print("BENCHMARK ACO - SANS ACO / AVEC ACO")
    print("=" * 70)

    for item in situations:

        question_id = item["id"]

        if question_id in completed_ids:
            print(
                f"\nSituation {question_id} déjà terminée : ignorée."
            )
            continue

        situation = item["situation"]
        profile = PROFILES[question_id]

        print()
        print("-" * 70)
        print(f"SITUATION {question_id}")
        print(situation)
        print("-" * 70)

        result = {
            "id": question_id,
            "situation": situation,
            "profile": profile,
            "status": "in_progress",
        }

        # Supprime une ancienne tentative incomplète
        results["questions"] = [
            item
            for item in results["questions"]
            if item["id"] != question_id
        ]

        results["questions"].append(result)
        save_results(results)

        common_args = {
            "child_age": profile["child_age"],
            "child_gender": profile["child_gender"],
            "family_context": None,
            "additional_information": None,
            "trigger_message": situation,
            "messages": [],
        }

        # --------------------------------------------------
        # SANS ACO
        # --------------------------------------------------

        print()
        print("1/2 Génération SANS ACO...")

        try:

            without_aco = (
                generate_parental_coach_response(
                    **common_args,
                    use_aco=False,
                )
            )

            result["without_aco"] = {
                "message_type": (
                    without_aco["message_type"]
                ),
                "content": (
                    without_aco["content"]
                ),
                "source_chunk_ids": [
                    source["chunk_id"]
                    for source in without_aco["sources"]
                ],
            }

            print("SANS ACO terminé.")

        except Exception as error:

            result["without_aco_error"] = str(
                error
            )

            print(
                "Erreur SANS ACO :",
                error,
            )

            result["status"] = "partial"

            save_results(results)

            continue

        save_results(results)

        time.sleep(2)

        # --------------------------------------------------
        # AVEC ACO
        # --------------------------------------------------

        print()
        print("2/2 Génération AVEC ACO...")

        try:

            with_aco = (
                generate_parental_coach_response(
                    **common_args,
                    use_aco=True,
                )
            )

            result["with_aco"] = {
                "message_type": (
                    with_aco["message_type"]
                ),
                "content": (
                    with_aco["content"]
                ),
                "source_chunk_ids": [
                    source["chunk_id"]
                    for source in with_aco["sources"]
                ],
                "aco": with_aco.get(
                    "aco"
                ),
            }

            result["status"] = "completed"

            print("AVEC ACO terminé.")

        except Exception as error:

            result["with_aco_error"] = str(
                error
            )

            result["status"] = "partial"

            print(
                "Erreur AVEC ACO :",
                error,
            )

        save_results(results)

        if result["status"] == "completed":

            print()
            print(
                "Parcours ACO :",
                " -> ".join(
                    result["with_aco"]["aco"]["path"]
                ),
            )

            print(
                "Score ACO :",
                result["with_aco"]["aco"]["score"],
            )

        print()
        print(
            "Résultat sauvegardé."
        )

        time.sleep(3)

    print()
    print("=" * 70)
    print("BENCHMARK TERMINÉ / INTERROMPU")
    print("=" * 70)

    completed = sum(
        1
        for item in results["questions"]
        if item.get("status") == "completed"
    )

    print(
        f"Situations complètes : "
        f"{completed}/{len(situations)}"
    )

    print(
        "Fichier :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()