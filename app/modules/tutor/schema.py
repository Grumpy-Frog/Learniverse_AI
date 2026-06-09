import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LanguageCode = Literal["en", "bn"]


class TutorGroupCreateRequest(BaseModel):
    subject_id: uuid.UUID
    title: str | None = Field(default=None, min_length=2, max_length=255)


class TutorGroupResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreateRequest(BaseModel):
    chapter_id: uuid.UUID
    group_id: uuid.UUID | None = None
    language: LanguageCode = "en"


class StoryGenerateRequest(BaseModel):
    student_preference: str | None = Field(
        default=None,
        max_length=300,
        description="Example: Explain with a bicycle story.",
    )


class ChatMessageRequest(BaseModel):
    message: str = Field(
        min_length=2,
        max_length=2000,
    )


class TutorConversationResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID | None
    user_id: uuid.UUID
    subject_id: uuid.UUID
    chapter_id: uuid.UUID
    language: str
    title: str
    provider: str
    model_name: str
    rag_mode: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    message_type: str
    content: str
    is_in_scope: bool
    is_source_grounded: bool
    prompt_tokens: int | None
    completion_tokens: int | None
    finish_reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorSourceResponse(BaseModel):
    document_id: uuid.UUID
    page_start: int
    page_end: int
    content_preview: str


class TutorTurnResponse(BaseModel):
    conversation: TutorConversationResponse
    reply: TutorMessageResponse
    sources: list[TutorSourceResponse] = Field(default_factory=list)
    note: str


class DeleteTutorResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str