
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LanguageCode = Literal["en", "bn", "both"]

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class SimulationCreateRequest(BaseModel):
    topic_id: uuid.UUID | None = None

    title: str = Field(min_length=2, max_length=200)

    slug: str = Field(
        min_length=2,
        max_length=180,
        pattern=SLUG_PATTERN,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    language: LanguageCode = "both"

    simulation_url: str = Field(
        min_length=2,
        max_length=500,
    )

    thumbnail_url: str | None = Field(
        default=None,
        max_length=500,
    )

    display_order: int = Field(default=1, ge=1)

    is_active: bool = True


class SimulationUpdateRequest(BaseModel):
    topic_id: uuid.UUID | None = None

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    language: LanguageCode | None = None

    simulation_url: str | None = Field(
        default=None,
        min_length=2,
        max_length=500,
    )

    thumbnail_url: str | None = Field(
        default=None,
        max_length=500,
    )

    display_order: int | None = Field(default=None, ge=1)

    is_active: bool | None = None


class SimulationResponse(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    topic_id: uuid.UUID | None
    title: str
    slug: str
    description: str | None
    language: str
    simulation_url: str
    thumbnail_url: str | None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)