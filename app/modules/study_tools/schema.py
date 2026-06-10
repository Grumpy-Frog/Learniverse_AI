import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from typing import Any

LanguageCode = Literal["en", "bn"]
StudySourceType = Literal["raw_text", "pdf", "note", "chapter", "custom_tutor_chat"]
NoteMode = Literal["study_notes", "lecture_notes", "summary_notes", "writing_help"]


class StudyDocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    grade_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    chapter_id: uuid.UUID | None
    title: str
    language: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    summary: str | None
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyDocumentDetailResponse(StudyDocumentResponse):
    extracted_text: str | None


class AiNoteGenerateRequest(BaseModel):
    source_type: StudySourceType
    source_id: uuid.UUID | None = None
    raw_text: str | None = Field(default=None, max_length=30000)

    grade_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None

    title: str | None = Field(default=None, max_length=200)
    instruction: str | None = Field(default=None, max_length=1000)
    ai_help_mode: NoteMode = "study_notes"
    language: LanguageCode = "en"


class AiNoteUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)


class AiNoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    grade_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    chapter_id: uuid.UUID | None
    source_type: str
    source_id: uuid.UUID | None
    title: str
    content: str
    ai_help_mode: str
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PdfSummarizeRequest(BaseModel):
    instruction: str | None = Field(default=None, max_length=1000)
    language: LanguageCode = "en"


class FlashcardGenerateRequest(BaseModel):
    source_type: StudySourceType
    source_id: uuid.UUID | None = None
    raw_text: str | None = Field(default=None, max_length=30000)

    grade_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None

    title: str | None = Field(default=None, max_length=200)
    card_count: int = Field(default=12, ge=3, le=30)
    language: LanguageCode = "en"


class FlashcardDeckUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class FlashcardResponse(BaseModel):
    id: uuid.UUID
    deck_id: uuid.UUID
    front: str
    back: str
    hint: str | None
    display_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlashcardDeckResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    grade_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    chapter_id: uuid.UUID | None
    source_type: str
    source_id: uuid.UUID | None
    title: str
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlashcardDeckDetailResponse(BaseModel):
    deck: FlashcardDeckResponse
    cards: list[FlashcardResponse]


class DeleteStudyToolResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str

StudyArtifactType = Literal[
    "mind_map",
    "worksheet",
    "formula_sheet",
    "important_questions",
]


class StudyArtifactGenerateRequest(BaseModel):
    source_type: StudySourceType
    source_id: uuid.UUID | None = None
    raw_text: str | None = Field(default=None, max_length=30000)

    grade_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None

    title: str | None = Field(default=None, max_length=200)
    instruction: str | None = Field(default=None, max_length=1000)
    language: LanguageCode = "en"

    item_count: int = Field(default=10, ge=3, le=30)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"


class StudyArtifactUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content_markdown: str | None = Field(default=None, min_length=1)


class StudyArtifactResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    grade_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    chapter_id: uuid.UUID | None
    source_type: str
    source_id: uuid.UUID | None
    artifact_type: str
    title: str
    content_markdown: str
    content_json: Any | None
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)