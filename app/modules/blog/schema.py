import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LanguageCode = Literal["en", "bn"]
BlogCategory = Literal["physics", "chemistry", "biology", "math"]
BlogStatus = Literal["draft", "published"]


class BlogGenerateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=255)
    short_description: str = Field(min_length=10, max_length=1000)
    language: LanguageCode = "en"


class BlogValidationResult(BaseModel):
    is_allowed: bool
    category: BlogCategory | None = None
    reason: str = Field(min_length=2, max_length=1000)

    @model_validator(mode="after")
    def validate_category(self):
        if self.is_allowed and self.category is None:
            raise ValueError("category is required when is_allowed is true")

        return self


class BlogGeneratedContent(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    slug: str = Field(min_length=3, max_length=255)
    category: BlogCategory
    excerpt: str = Field(min_length=10, max_length=1000)
    content_markdown: str = Field(min_length=300)


class BlogPostResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    slug: str
    topic: str
    short_description: str
    category: str
    language: str
    excerpt: str
    content_markdown: str
    status: str
    is_ai_generated: bool
    model_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogListItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    topic: str
    category: str
    language: str
    excerpt: str
    status: str
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogGenerateResponse(BaseModel):
    post: BlogPostResponse
    validation_reason: str
    note: str = "AI-generated blog draft created. Review before publishing."