import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.neighbors import KNeighborsRegressor

from backend.app.main import app  # noqa: F401
from backend.app.database import SessionLocal
from backend.app.services.ml_service import (
    MAX_NEIGHBORS,
    MIN_TRAINING_SAMPLES,
    _build_feature_vector,
    _load_training_evaluations,
)
from backend.app.services.rag_service import (
    load_rag_resources,
)


OUTPUT_PATH = Path(
    "data/evaluation/knn_evaluation_results.json"
)

CRITERIA = [
    "relevance_score",
    "safety_score",
    "personalization_score",
    "document_fidelity_score",
]


def main():
    database = SessionLocal()

    try:
        evaluations = _load_training_evaluations(
            database
        )

        sample_count = len(evaluations)

        print(
            f"Nombre de parcours évalués : "
            f"{sample_count}"
        )

        minimum_required = (
            MIN_TRAINING_SAMPLES + 1
        )

        if sample_count < minimum_required:
            print()
            print(
                "Évaluation KNN impossible pour "
                "le moment."
            )
            print(
                f"Il faut au minimum "
                f"{minimum_required} parcours "
                "évalués."
            )
            print(
                f"Actuellement : {sample_count}"
            )
            print()
            print(
                "Pourquoi ? Avec Leave-One-Out, "
                "un parcours sert de test et les "
                f"{MIN_TRAINING_SAMPLES} autres "
                "servent à l'apprentissage."
            )
            return

        print(
            "Chargement du modèle "
            "d'embeddings..."
        )

        _, _, embedding_model = (
            load_rag_resources()
        )

        features = np.vstack(
            [
                _build_feature_vector(
                    evaluation.coaching_path,
                    embedding_model,
                )
                for evaluation in evaluations
            ]
        )

        targets = np.asarray(
            [
                [
                    evaluation.relevance_score,
                    evaluation.safety_score,
                    evaluation.personalization_score,
                    evaluation.document_fidelity_score,
                ]
                for evaluation in evaluations
            ],
            dtype=np.float32,
        )

        predictions = []
        true_values = []

        predicted_globals = []
        true_globals = []

        details = []

        for test_index in range(sample_count):
            train_indices = [
                index
                for index in range(sample_count)
                if index != test_index
            ]

            x_train = features[train_indices]
            y_train = targets[train_indices]

            x_test = features[
                test_index
            ].reshape(1, -1)

            y_test = targets[test_index]

            neighbors_used = min(
                MAX_NEIGHBORS,
                len(train_indices),
            )

            model = KNeighborsRegressor(
                n_neighbors=neighbors_used,
                weights="distance",
                metric="euclidean",
            )

            model.fit(
                x_train,
                y_train,
            )

            prediction = model.predict(
                x_test
            )[0]

            prediction = np.clip(
                prediction,
                1.0,
                5.0,
            )

            predicted_global = float(
                np.mean(prediction)
            )

            true_global = float(
                evaluations[
                    test_index
                ].global_score
            )

            predictions.append(
                prediction
            )

            true_values.append(
                y_test
            )

            predicted_globals.append(
                predicted_global
            )

            true_globals.append(
                true_global
            )

            details.append(
                {
                    "path_id": evaluations[
                        test_index
                    ].path_id,
                    "actual": {
                        criterion: round(
                            float(y_test[index]),
                            2,
                        )
                        for index, criterion
                        in enumerate(CRITERIA)
                    },
                    "predicted": {
                        criterion: round(
                            float(
                                prediction[index]
                            ),
                            2,
                        )
                        for index, criterion
                        in enumerate(CRITERIA)
                    },
                    "actual_global_score":
                        round(
                            true_global,
                            2,
                        ),
                    "predicted_global_score":
                        round(
                            predicted_global,
                            2,
                        ),
                }
            )

        true_values = np.asarray(
            true_values
        )

        predictions = np.asarray(
            predictions
        )

        metrics = {}

        for index, criterion in enumerate(
            CRITERIA
        ):
            mae = mean_absolute_error(
                true_values[:, index],
                predictions[:, index],
            )

            rmse = np.sqrt(
                mean_squared_error(
                    true_values[:, index],
                    predictions[:, index],
                )
            )

            metrics[criterion] = {
                "mae": round(
                    float(mae),
                    3,
                ),
                "rmse": round(
                    float(rmse),
                    3,
                ),
            }

        global_mae = mean_absolute_error(
            true_globals,
            predicted_globals,
        )

        global_rmse = np.sqrt(
            mean_squared_error(
                true_globals,
                predicted_globals,
            )
        )

        results = {
            "algorithm": "KNN regression",
            "evaluation_method":
                "Leave-One-Out Cross Validation",
            "samples": sample_count,
            "neighbors_max": MAX_NEIGHBORS,
            "metrics": metrics,
            "global_score": {
                "mae": round(
                    float(global_mae),
                    3,
                ),
                "rmse": round(
                    float(global_rmse),
                    3,
                ),
            },
            "details": details,
        }

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                results,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print()
        print("===== ÉVALUATION KNN =====")
        print()

        labels = {
            "relevance_score":
                "Pertinence",
            "safety_score":
                "Sécurité",
            "personalization_score":
                "Personnalisation",
            "document_fidelity_score":
                "Fidélité PET",
        }

        for criterion in CRITERIA:
            print(
                f"{labels[criterion]:18} "
                f"| MAE = "
                f"{metrics[criterion]['mae']:.3f} "
                f"| RMSE = "
                f"{metrics[criterion]['rmse']:.3f}"
            )

        print()
        print(
            f"{'Note globale':18} "
            f"| MAE = {global_mae:.3f} "
            f"| RMSE = {global_rmse:.3f}"
        )

        print()
        print(
            "Résultats enregistrés dans :"
        )
        print(OUTPUT_PATH)

        print()
        print(
            "Attention : les résultats sont "
            "préliminaires car le nombre de "
            "parcours évalués reste faible."
        )

    finally:
        database.close()


if __name__ == "__main__":
    main()