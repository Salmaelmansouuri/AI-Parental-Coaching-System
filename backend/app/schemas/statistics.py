from pydantic import BaseModel


class ParentStatisticsResponse(BaseModel):
    total_paths: int
    active_paths: int
    waiting_coach_review: int
    completed_paths: int
    positive_ratings: int
    negative_ratings: int
    total_ratings: int
    satisfaction_rate: float


class CoachStatisticsResponse(BaseModel):
    pending_paths: int
    evaluated_paths: int
    validated_paths: int
    rejected_paths: int
    validation_rate: float

    average_relevance_score: float
    average_safety_score: float
    average_personalization_score: float
    average_document_fidelity_score: float
    average_global_score: float

    rag_precision_at_4: float
    rag_recall_at_4_pool: float
    rag_mrr: float
    rag_faithfulness: float
    rag_answer_relevancy: float

    knn_samples: int = 0

    knn_mae_global: float = 0.0
    knn_rmse_global: float = 0.0

    knn_mae_relevance: float = 0.0
    knn_mae_safety: float = 0.0
    knn_mae_personalization: float = 0.0
    knn_mae_document_fidelity: float = 0.0