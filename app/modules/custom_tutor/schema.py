import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LanguageCode = Literal["en", "bn"]


class CustomTutorChatCreateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    language: LanguageCode = "en"

    grade_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None


class CustomTutorChatRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class CustomTutorMessageCreateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class CustomTutorChatResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    grade_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    chapter_id: uuid.UUID | None
    title: str
    language: str
    is_archived: bool
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomTutorMessageResponse(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    role: str
    content: str
    prompt_tokens: int | None
    completion_tokens: int | None
    finish_reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomTutorChatDetailResponse(BaseModel):
    chat: CustomTutorChatResponse
    messages: list[CustomTutorMessageResponse]


class CustomTutorChatListResponse(BaseModel):
    chats: list[CustomTutorChatResponse]


class CustomTutorTurnResponse(BaseModel):
    chat: CustomTutorChatResponse
    user_message: CustomTutorMessageResponse
    assistant_message: CustomTutorMessageResponse


class DeleteCustomTutorChatResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str