
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class GradeCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(
        min_length=2,
        max_length=100,
        pattern=SLUG_PATTERN,
    )
    display_order: int = Field(default=1, ge=1)
    is_active: bool = True


class GradeResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    display_order: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(
        min_length=2,
        max_length=100,
        pattern=SLUG_PATTERN,
    )
    description: str | None = Field(default=None, max_length=1000)
    display_order: int = Field(default=1, ge=1)
    is_active: bool = True


class SubjectResponse(BaseModel):
    id: uuid.UUID
    grade_level_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    display_order: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChapterCreateRequest(BaseModel):
    chapter_no: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    slug: str = Field(
        min_length=2,
        max_length=150,
        pattern=SLUG_PATTERN,
    )
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class ChapterResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    chapter_no: int
    title: str
    slug: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    slug: str = Field(
        min_length=2,
        max_length=150,
        pattern=SLUG_PATTERN,
    )
    description: str | None = Field(default=None, max_length=1000)
    learning_objective: str | None = Field(default=None, max_length=2000)
    display_order: int = Field(default=1, ge=1)
    is_active: bool = True


class TopicResponse(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    title: str
    slug: str
    description: str | None
    learning_objective: str | None
    display_order: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)