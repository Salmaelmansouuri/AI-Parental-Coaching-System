import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.database import get_database
from backend.app.models.coach_evaluation import CoachEvaluation
from backend.app.models.coaching_path import (
    CoachingPath,
    CoachingPathStatus,
)
from backend.app.models.rating import Rating, RatingValue
from backend.app.models.user import User, UserRole
from backend.app.schemas.statistics import (
    CoachStatisticsResponse,
    ParentStatisticsResponse,
)


router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

RETRIEVAL_RESULTS_FILE = (
    PROJECT_ROOT / "data" / "evaluation" / "rag_retrieval_results.json"
)

GENERATION_RESULTS_FILE = (
    PROJECT_ROOT / "data" / "evaluation" / "rag_generation_results.json"
)


def load_rag_metrics() -> dict:
    metrics = {
        "rag_precision_at_4": 0.0,
        "rag_recall_at_4_pool": 0.0,
        "rag_mrr": 0.0,
        "rag_faithfulness": 0.0,
        "rag_answer_relevancy": 0.0,
    }

    if RETRIEVAL_RESULTS_FILE.exists():
        try:
            retrieval_data = json.loads(
                RETRIEVAL_RESULTS_FILE.read_text(
                    encoding="utf-8"
                )
            )

            summary = retrieval_data.get(
                "summary",
                {},
            )

            metrics["rag_precision_at_4"] = float(
                summary.get(
                    "precision_at_4",
                    0.0,
                )
            )

            metrics["rag_recall_at_4_pool"] = float(
                summary.get(
                    "recall_at_4_pool",
                    0.0,
                )
            )

            metrics["rag_mrr"] = float(
                summary.get(
                    "mrr",
                    0.0,
                )
            )

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
            ValueError,
        ):
            pass

    if GENERATION_RESULTS_FILE.exists():
        try:
            generation_data = json.loads(
                GENERATION_RESULTS_FILE.read_text(
                    encoding="utf-8"
                )
            )

            summary = generation_data.get(
                "summary",
                {},
            )

            metrics["rag_faithfulness"] = float(
                summary.get(
                    "faithfulness",
                    0.0,
                )
            )

            metrics["rag_answer_relevancy"] = float(
                summary.get(
                    "answer_relevancy",
                    0.0,
                )
            )

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
            ValueError,
        ):
            pass

    return metrics
def load_knn_metrics() -> dict:
    metrics = {
        "knn_samples": 0,
        "knn_mae_global": 0.0,
        "knn_rmse_global": 0.0,
        "knn_mae_relevance": 0.0,
        "knn_mae_safety": 0.0,
        "knn_mae_personalization": 0.0,
        "knn_mae_document_fidelity": 0.0,
    }

    knn_results_file = Path(
        "data/evaluation/knn_evaluation_results.json"
    )

    if not knn_results_file.exists():
        return metrics

    try:
        data = json.loads(
            knn_results_file.read_text(
                encoding="utf-8"
            )
        )

        criterion_metrics = data.get(
            "metrics",
            {},
        )

        global_metrics = data.get(
            "global_score",
            {},
        )

        metrics["knn_samples"] = int(
            data.get("samples", 0)
        )

        metrics["knn_mae_global"] = float(
            global_metrics.get("mae", 0.0)
        )

        metrics["knn_rmse_global"] = float(
            global_metrics.get("rmse", 0.0)
        )

        metrics["knn_mae_relevance"] = float(
            criterion_metrics
            .get("relevance_score", {})
            .get("mae", 0.0)
        )

        metrics["knn_mae_safety"] = float(
            criterion_metrics
            .get("safety_score", {})
            .get("mae", 0.0)
        )

        metrics["knn_mae_personalization"] = float(
            criterion_metrics
            .get("personalization_score", {})
            .get("mae", 0.0)
        )

        metrics["knn_mae_document_fidelity"] = float(
            criterion_metrics
            .get("document_fidelity_score", {})
            .get("mae", 0.0)
        )

    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ):
        pass

    return metrics

def ensure_parent(user: User) -> None:
    if user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est réservée aux parents.",
        )
def ensure_coach(user: User) -> None:
    if user.role != UserRole.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est réservée aux coachs humains.",
        )

@router.get(
    "/parent",
    response_model=ParentStatisticsResponse,
)
def get_parent_statistics(
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ParentStatisticsResponse:
    ensure_parent(current_user)

    total_paths = database.scalar(
        select(func.count(CoachingPath.id)).where(
            CoachingPath.parent_id == current_user.id,
        )
    ) or 0

    active_paths = database.scalar(
        select(func.count(CoachingPath.id)).where(
            CoachingPath.parent_id == current_user.id,
            CoachingPath.status == CoachingPathStatus.OPEN,
        )
    ) or 0

    waiting_coach_review = database.scalar(
        select(func.count(CoachingPath.id)).where(
            CoachingPath.parent_id == current_user.id,
            CoachingPath.status
            == CoachingPathStatus.WAITING_COACH_REVIEW,
        )
    ) or 0

    completed_paths = database.scalar(
        select(func.count(CoachingPath.id)).where(
            CoachingPath.parent_id == current_user.id,
            CoachingPath.status == CoachingPathStatus.COMPLETED,
        )
    ) or 0

    positive_ratings = database.scalar(
        select(func.count(Rating.id)).where(
            Rating.parent_id == current_user.id,
            Rating.value == RatingValue.POSITIVE,
        )
    ) or 0

    negative_ratings = database.scalar(
        select(func.count(Rating.id)).where(
            Rating.parent_id == current_user.id,
            Rating.value == RatingValue.NEGATIVE,
        )
    ) or 0

    total_ratings = positive_ratings + negative_ratings

    if total_ratings == 0:
        satisfaction_rate = 0.0
    else:
        satisfaction_rate = round(
            positive_ratings / total_ratings * 100,
            2,
        )

    return ParentStatisticsResponse(
        total_paths=total_paths,
        active_paths=active_paths,
        waiting_coach_review=waiting_coach_review,
        completed_paths=completed_paths,
        positive_ratings=positive_ratings,
        negative_ratings=negative_ratings,
        total_ratings=total_ratings,
        satisfaction_rate=satisfaction_rate,
    )
@router.get(
    "/coach",
    response_model=CoachStatisticsResponse,
)
def get_coach_statistics(
    database: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> CoachStatisticsResponse:
    ensure_coach(current_user)

    pending_paths = database.scalar(
        select(func.count(CoachingPath.id)).where(
            CoachingPath.status
            == CoachingPathStatus.WAITING_COACH_REVIEW,
        )
    ) or 0

    evaluated_paths = database.scalar(
        select(func.count(CoachEvaluation.id))
    ) or 0

    validated_paths = database.scalar(
        select(func.count(CoachEvaluation.id)).where(
            CoachEvaluation.validated.is_(True),
        )
    ) or 0

    rejected_paths = database.scalar(
        select(func.count(CoachEvaluation.id)).where(
            CoachEvaluation.validated.is_(False),
        )
    ) or 0

    if evaluated_paths == 0:
        validation_rate = 0.0
    else:
        validation_rate = round(
            validated_paths / evaluated_paths * 100,
            2,
        )

    average_relevance_score = database.scalar(
        select(func.avg(CoachEvaluation.relevance_score))
    ) or 0.0

    average_safety_score = database.scalar(
        select(func.avg(CoachEvaluation.safety_score))
    ) or 0.0

    average_personalization_score = database.scalar(
        select(
            func.avg(
                CoachEvaluation.personalization_score
            )
        )
    ) or 0.0

    average_document_fidelity_score = database.scalar(
        select(
            func.avg(
                CoachEvaluation.document_fidelity_score
            )
        )
    ) or 0.0

    average_global_score = database.scalar(
        select(func.avg(CoachEvaluation.global_score))
    ) or 0.0

    rag_metrics = load_rag_metrics()

    knn_metrics = load_knn_metrics()

    return CoachStatisticsResponse(
        pending_paths=pending_paths,
        evaluated_paths=evaluated_paths,
        validated_paths=validated_paths,
        rejected_paths=rejected_paths,
        validation_rate=validation_rate,
        average_relevance_score=round(
            float(average_relevance_score),
            2,
        ),
        average_safety_score=round(
            float(average_safety_score),
            2,
        ),
        average_personalization_score=round(
            float(average_personalization_score),
            2,
        ),
        average_document_fidelity_score=round(
            float(average_document_fidelity_score),
            2,
        ),
        average_global_score=round(
            float(average_global_score),
            2,
        ),
                rag_precision_at_4=rag_metrics[
            "rag_precision_at_4"
        ],
        rag_recall_at_4_pool=rag_metrics[
            "rag_recall_at_4_pool"
        ],
        rag_mrr=rag_metrics[
            "rag_mrr"
        ],
        rag_faithfulness=rag_metrics[
            "rag_faithfulness"
        ],
                rag_answer_relevancy=rag_metrics[
            "rag_answer_relevancy"
        ],

        knn_samples=knn_metrics[
            "knn_samples"
        ],

        knn_mae_global=knn_metrics[
            "knn_mae_global"
        ],

        knn_rmse_global=knn_metrics[
            "knn_rmse_global"
        ],

        knn_mae_relevance=knn_metrics[
            "knn_mae_relevance"
        ],

        knn_mae_safety=knn_metrics[
            "knn_mae_safety"
        ],

        knn_mae_personalization=knn_metrics[
            "knn_mae_personalization"
        ],

        knn_mae_document_fidelity=knn_metrics[
            "knn_mae_document_fidelity"
        ],
    )