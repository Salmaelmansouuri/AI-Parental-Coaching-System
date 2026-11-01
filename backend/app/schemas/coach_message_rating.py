from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.models.rating import RatingValue


class CoachMessageRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    coach_id: int
    value: RatingValue
    created_at: datetime
    updated_at: datetime