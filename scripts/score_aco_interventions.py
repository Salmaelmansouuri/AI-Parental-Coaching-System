import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

INPUT_FILE = Path("data/aco_test_situations.json")
OUTPUT_FILE = Path("data/aco_intervention_scores.json")


INTERVENTIONS = {
    "active_listening": (
        "Écoute active : comprendre les émotions de l'enfant, "
        "reformuler ce qu'il ressent et l'aider à exprimer son problème."
    ),

    "i_message": (
        "Message-je : le parent exprime son besoin, son ressenti "
        "et l'effet du comportement sans accuser l'enfant."
    ),

    "problem_ownership": (
        "Propriété du problème : déterminer si le problème appartient "
        "au parent ou à l'enfant afin de choisir une intervention adaptée."
    ),

    "method_iii": (
        "Méthode III : rechercher avec l'enfant une solution "
        "gagnant-gagnant lorsqu'il existe un conflit de besoins."
    ),
}


def similarity_to_score(similarity: float) -> float:
    """
    Transforme une similarité cosinus en score de 1 à 5.
    Ce score représente uniquement une pertinence sémantique.
    """
    similarity = max(0.0, min(1.0, similarity))
    return round(1.0 + 4.0 * similarity, 3)


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        situations = json.load(f)

    print("Chargement du modèle...")
    model = SentenceTransformer(MODEL_NAME)

    intervention_names = list(INTERVENTIONS.keys())
    intervention_texts = list(INTERVENTIONS.values())

    intervention_embeddings = model.encode(
        intervention_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    results = []

    for item in situations:

        situation = item["situation"]

        situation_embedding = model.encode(
            [situation],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]

        similarities = np.dot(
            intervention_embeddings,
            situation_embedding,
        )

        scores = {}

        for name, similarity in zip(
            intervention_names,
            similarities,
        ):
            scores[name] = {
                "similarity": round(float(similarity), 4),
                "semantic_score": similarity_to_score(
                    float(similarity)
                ),
            }

        results.append(
            {
                "id": item["id"],
                "situation": situation,
                "interventions": scores,
            }
        )

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

    print("\n=== SCORES ACO ===")

    for result in results:

        print(
            f"\nSituation {result['id']} : "
            f"{result['situation']}"
        )

        ranking = sorted(
            result["interventions"].items(),
            key=lambda x: x[1]["semantic_score"],
            reverse=True,
        )

        for name, values in ranking:

            print(
                f"  {name:20s} "
                f"similarité={values['similarity']:.4f} "
                f"score={values['semantic_score']:.3f}"
            )

    print(
        "\nRésultats enregistrés dans :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()