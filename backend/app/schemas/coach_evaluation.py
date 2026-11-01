from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CoachEvaluationCreate(BaseModel):
    relevance_score: int = Field(
        ge=1,
        le=5,
    )

    safety_score: int = Field(
        ge=1,
        le=5,
    )

    personalization_score: int = Field(
        ge=1,
        le=5,
    )

    document_fidelity_score: int = Field(
        ge=1,
        le=5,
    )

    comment: str | None = Field(
        default=None,
        max_length=5000,
    )

    validated: bool


class CoachEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path_id: int
    coach_id: int
    relevance_score: int
    safety_score: int
    personalization_score: int
    document_fidelity_score: int
    global_score: float
    comment: str | None
    validated: bool
    created_at: datetime
    updated_at: datetime