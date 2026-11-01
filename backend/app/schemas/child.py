from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.child import ChildGender


class ChildCreate(BaseModel):
    alias: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=18)
    gender: ChildGender

    family_context: str | None = Field(
        default=None,
        max_length=2000,
    )

    additional_information: str | None = Field(
        default=None,
        max_length=3000,
    )


class ChildUpdate(BaseModel):
    alias: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    age: int | None = Field(
        default=None,
        ge=0,
        le=18,
    )

    gender: ChildGender | None = None
    family_context: str | None = Field(default=None, max_length=2000)
    additional_information: str | None = Field(default=None, max_length=3000)


class ChildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    alias: str
    age: int
    gender: ChildGender
    family_context: str | None
    additional_information: str | None
    created_at: datetime