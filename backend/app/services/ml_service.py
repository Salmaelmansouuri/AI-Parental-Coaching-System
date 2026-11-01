import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.coach_evaluation import CoachEvaluation
from backend.app.models.coaching_path import CoachingPath
from backend.app.models.message import MessageSender
from backend.app.services.rag_service import load_rag_resources


MIN_TRAINING_SAMPLES = 3
MAX_NEIGHBORS = 3

AGE_WEIGHT = 0.35
GENDER_WEIGHT = 0.35


def _gender_vector(gender) -> np.ndarray:
    gender_name = getattr(
        gender,
        "name",
        "NOT_SPECIFIED",
    )

    values = [
        "BOY",
        "GIRL",
        "OTHER",
        "NOT_SPECIFIED",
    ]

    return np.asarray(
        [
            1.0 if gender_name == value else 0.0
            for value in values
        ],
        dtype=np.float32,
    )


def _build_path_text(path: CoachingPath) -> str:
    child = path.child

    llm_messages = [
        message.content
        for message in path.messages
        if message.sender == MessageSender.LLM
    ]

    recent_llm_messages = llm_messages[-3:]

    parts = [
        f"Situation parentale : {path.trigger_message}",
    ]

    if child.family_context:
        parts.append(
            f"Contexte familial : {child.family_context}"
        )

    if child.additional_information:
        parts.append(
            "Informations complémentaires : "
            f"{child.additional_information}"
        )

    if recent_llm_messages:
        parts.append(
            "Réponses récentes du coach IA : "
            + " ".join(recent_llm_messages)
        )

    return "\n".join(parts)


def _build_feature_vector(
    path: CoachingPath,
    embedding_model,
) -> np.ndarray:
    text = _build_path_text(path)

    text_embedding = embedding_model.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0].astype(np.float32)

    age = float(path.child.age)
    normalized_age = np.clip(
        age / 18.0,
        0.0,
        1.0,
    )

    age_feature = np.asarray(
        [normalized_age * AGE_WEIGHT],
        dtype=np.float32,
    )

    gender_features = (
        _gender_vector(path.child.gender)
        * GENDER_WEIGHT
    )

    return np.concatenate(
        [
            text_embedding,
            age_feature,
            gender_features,
        ]
    ).astype(np.float32)


def _load_path(
    database: Session,
    path_id: int,
) -> CoachingPath | None:
    statement = (
        select(CoachingPath)
        .options(
            joinedload(CoachingPath.child),
            joinedload(CoachingPath.messages),
        )
        .where(CoachingPath.id == path_id)
    )

    return (
        database.execute(statement)
        .unique()
        .scalars()
        .first()
    )


def _load_training_evaluations(
    database: Session,
    *,
    exclude_path_id: int | None = None,
) -> list[CoachEvaluation]:
    statement = (
        select(CoachEvaluation)
        .options(
            joinedload(
                CoachEvaluation.coaching_path
            ).joinedload(CoachingPath.child),
            joinedload(
                CoachEvaluation.coaching_path
            ).joinedload(CoachingPath.messages),
        )
    )

    if exclude_path_id is not None:
        statement = statement.where(
            CoachEvaluation.path_id != exclude_path_id
        )

    return (
        database.execute(statement)
        .unique()
        .scalars()
        .all()
    )


def predict_path_evaluation(
    database: Session,
    path_id: int,
) -> dict:
    path = _load_path(database, path_id)

    if path is None:
        return {
            "available": False,
            "reason": "Parcours introuvable.",
            "training_samples": 0,
        }

    evaluations = _load_training_evaluations(
        database,
        exclude_path_id=path_id,
    )

    training_samples = len(evaluations)

    if training_samples < MIN_TRAINING_SAMPLES:
        return {
            "available": False,
            "reason": (
                "Pas assez de parcours évalués "
                "pour produire une estimation ML fiable. "
                f"Minimum requis : {MIN_TRAINING_SAMPLES}."
            ),
            "training_samples": training_samples,
        }

    _, _, embedding_model = load_rag_resources()

    x_train = np.vstack(
        [
            _build_feature_vector(
                evaluation.coaching_path,
                embedding_model,
            )
            for evaluation in evaluations
        ]
    )

    y_train = np.asarray(
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

    x_current = _build_feature_vector(
        path,
        embedding_model,
    ).reshape(1, -1)

    neighbors_used = min(
        MAX_NEIGHBORS,
        training_samples,
    )

    model = KNeighborsRegressor(
        n_neighbors=neighbors_used,
        weights="distance",
        metric="euclidean",
    )

    model.fit(x_train, y_train)

    prediction = model.predict(x_current)[0]
    prediction = np.clip(prediction, 1.0, 5.0)
    predicted_global_score = float(
    np.mean(prediction)
    )
    distances, indices = model.kneighbors(
        x_current,
        n_neighbors=neighbors_used,
    )

    neighbors = []

    for distance, index in zip(
        distances[0],
        indices[0],
    ):
        evaluation = evaluations[int(index)]

        neighbors.append(
            {
                "path_id": evaluation.path_id,
                "distance": round(
                    float(distance),
                    4,
                ),
                "global_score": round(
                predicted_global_score,
                 2,
                ),
            }
        )

    return {
        "available": True,
        "algorithm": "KNN regression",
        "training_samples": training_samples,
        "neighbors_used": neighbors_used,
        "neighbors": neighbors,
        "prediction": {
            "relevance_score": round(
                float(prediction[0]),
                2,
            ),
            "safety_score": round(
                float(prediction[1]),
                2,
            ),
            "personalization_score": round(
                float(prediction[2]),
                2,
            ),
            "document_fidelity_score": round(
                float(prediction[3]),
                2,
            ),
            "global_score": round(
                float(np.mean(prediction)),
                2,
            ),
        },
    }