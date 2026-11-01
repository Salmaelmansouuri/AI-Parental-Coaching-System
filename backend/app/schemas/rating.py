from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.rating import RatingValue


class RatingCreate(BaseModel):
    value: RatingValue

    comment: str | None = Field(
        default=None,
        max_length=2000,
    )


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    parent_id: int
    value: RatingValue
    comment: str | None
    created_at: datetime
    updated_at: datetime