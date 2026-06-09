import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LanguageCode = Literal["en", "bn"]


class ChunkBuildRequest(BaseModel):
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)

    # Optional metadata only.
    # Chunk is chapter-wise even if this is not provided.
    topic_id: uuid.UUID | None = None
    section_title: str | None = Field(default=None, max_length=255)

    chunk_size_words: int = Field(
        default=220,
        ge=80,
        le=500,
    )

    overlap_words: int = Field(
        default=35,
        ge=0,
        le=100,
    )

    @model_validator(mode="after")
    def validate_page_and_chunk_ranges(self):
        if self.page_end < self.page_start:
            raise ValueError(
                "page_end must be greater than or equal to page_start"
            )

        if self.overlap_words >= self.chunk_size_words:
            raise ValueError(
                "overlap_words must be smaller than chunk_size_words"
            )

        return self


class ChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chapter_id: uuid.UUID
    topic_id: uuid.UUID | None
    section_title: str | None
    language: str
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    word_count: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RagSearchRequest(BaseModel):
    chapter_id: uuid.UUID
    language: LanguageCode

    query: str = Field(
        min_length=2,
        max_length=500,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class RetrievedChunkResponse(ChunkResponse):
    score: int


class RagSearchResponse(BaseModel):
    query: str
    retrieval_method: str = "keyword"
    results: list[RetrievedChunkResponse]


class DeleteChunksResponse(BaseModel):
    deleted_count: int
    message: str