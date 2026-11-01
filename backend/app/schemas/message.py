from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from backend.app.models.message import (
    MessageSender,
    MessageType,
)


class ParentMessageCreate(BaseModel):
    content: str = Field(
        min_length=2,
        max_length=5000,
    )

    message_type: MessageType = (
        MessageType.PARENT_ANSWER
    )


class MessageSource(BaseModel):
    score: float
    document_name: str
    page_number: int
    chunk_id: int | str
    text: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    path_id: int
    sender: MessageSender
    message_type: MessageType
    content: str
    sources: list[MessageSource] = Field(
        default_factory=list
    )
    created_at: datetime