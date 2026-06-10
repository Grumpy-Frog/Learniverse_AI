import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ThreadSource = Literal["custom_tutor", "help", "feedback"]
ThreadStatus = Literal["open", "answered", "closed"]
ThreadPriority = Literal["low", "normal", "high"]


class InboxThreadCreateRequest(BaseModel):
    subject_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None

    title: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=1, max_length=5000)

    source: ThreadSource = "custom_tutor"
    priority: ThreadPriority = "normal"


class InboxMessageCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class InboxThreadStatusUpdateRequest(BaseModel):
    status: ThreadStatus | None = None
    priority: ThreadPriority | None = None
    assigned_admin_id: uuid.UUID | None = None


class InboxMessageResponse(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    sender_id: uuid.UUID
    sender_role: str
    body: str
    is_internal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InboxThreadResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    assigned_admin_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    chapter_id: uuid.UUID | None
    title: str
    source: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InboxThreadDetailResponse(BaseModel):
    thread: InboxThreadResponse
    messages: list[InboxMessageResponse]


class InboxThreadListResponse(BaseModel):
    threads: list[InboxThreadResponse]