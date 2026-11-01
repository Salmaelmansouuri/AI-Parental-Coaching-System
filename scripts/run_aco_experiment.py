import json
from pathlib import Path

from backend.app.services.aco_service import ACOService


INPUT_FILE = Path("data/aco_intervention_scores.json")
OUTPUT_FILE = Path("data/aco_experiment_results.json")


# Scores de transition du prototype.
# Ils représentent la cohérence de l'enchaînement
# entre deux interventions PET.
TRANSITION_SCORES = {
    ("problem_ownership", "active_listening"): 4.9,
    ("active_listening", "method_iii"): 4.8,

    ("problem_ownership", "i_message"): 4.4,
    ("i_message", "method_iii"): 4.5,

    ("active_listening", "i_message"): 4.0,
    ("i_message", "active_listening"): 3.6,

    ("method_iii", "active_listening"): 3.2,
    ("method_iii", "problem_ownership"): 2.8,

    ("active_listening", "problem_ownership"): 3.5,
    ("i_message", "problem_ownership"): 3.4,

    ("problem_ownership", "method_iii"): 4.3,
    ("method_iii", "i_message"): 3.4,
}


def path_score(path, scores):
    node_values = [
        scores[item]
        for item in path
    ]

    mean_nodes = sum(node_values) / len(node_values)

    transitions = []

    for i in range(len(path) - 1):
        transitions.append(
            TRANSITION_SCORES.get(
                (path[i], path[i + 1]),
                3.0,
            )
        )

    mean_transitions = (
        sum(transitions) / len(transitions)
        if transitions
        else 0.0
    )

    return round(
        0.6 * mean_nodes
        + 0.4 * mean_transitions,
        4,
    )


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    for item in data:

        scores = {
            name: values["semantic_score"]
            for name, values
            in item["interventions"].items()
        }

        interventions = list(scores.keys())

        # -------------------------
        # SANS ACO
        # -------------------------
        baseline_path = sorted(
            interventions,
            key=lambda x: scores[x],
            reverse=True,
        )[:3]

        baseline_score = path_score(
            baseline_path,
            scores,
        )

        # -------------------------
        # AVEC ACO
        # -------------------------
        aco = ACOService(
            n_ants=20,
            n_iterations=30,
            alpha=1.0,
            beta=2.0,
            evaporation_rate=0.3,
            random_seed=42,
        )

        aco_result = aco.optimize(
            interventions=interventions,
            intervention_scores=scores,
            transition_scores=TRANSITION_SCORES,
            path_length=3,
        )

        gain = round(
            aco_result["best_score"]
            - baseline_score,
            4,
        )

        result = {
            "id": item["id"],
            "situation": item["situation"],

            "without_aco": {
                "path": baseline_path,
                "score": baseline_score,
            },

            "with_aco": {
                "path": aco_result["best_path"],
                "score": aco_result["best_score"],
            },

            "gain": gain,
        }

        results.append(result)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n=== COMPARAISON SANS ACO / AVEC ACO ===")

    for result in results:

        print(
            f"\nSituation {result['id']}"
        )

        print(
            "Sans ACO :",
            " -> ".join(
                result["without_aco"]["path"]
            ),
            "| score =",
            result["without_aco"]["score"],
        )

        print(
            "Avec ACO :",
            " -> ".join(
                result["with_aco"]["path"]
            ),
            "| score =",
            result["with_aco"]["score"],
        )

        print(
            "Gain :",
            result["gain"],
        )

    mean_without = sum(
        r["without_aco"]["score"]
        for r in results
    ) / len(results)

    mean_with = sum(
        r["with_aco"]["score"]
        for r in results
    ) / len(results)

    print("\n=== MOYENNES ===")

    print(
        "Sans ACO :",
        round(mean_without, 4),
    )

    print(
        "Avec ACO :",
        round(mean_with, 4),
    )

    print(
        "Gain moyen :",
        round(mean_with - mean_without, 4),
    )

    print(
        "\nRésultats enregistrés dans :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()