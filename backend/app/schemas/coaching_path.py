from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.coaching_path import CoachingPathStatus


class CoachingPathCreate(BaseModel):
    child_id: int = Field(gt=0)

    trigger_message: str = Field(
        min_length=10,
        max_length=5000,
    )


class CoachingPathConclusion(BaseModel):
    parent_conclusion: str = Field(
        min_length=10,
        max_length=5000,
    )


class CoachingPathResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    child_id: int
    trigger_message: str
    status: CoachingPathStatus
    parent_conclusion: str | None
    created_at: datetime
    completed_at: datetime | None