import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB

class StudyDocument(Base):
    __tablename__ = "study_documents"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_study_document_language",
        ),
        CheckConstraint(
            "processing_status IN ('processed', 'needs_ocr', 'failed')",
            name="ck_study_document_processing_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grade_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("grade_levels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    processing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="processed")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AiNote(Base):
    __tablename__ = "ai_notes"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_ai_note_language",
        ),
        CheckConstraint(
            "source_type IN ('raw_text', 'pdf', 'note', 'chapter', 'custom_tutor_chat')",
            name="ck_ai_note_source_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("grade_levels.id", ondelete="SET NULL"), nullable=True, index=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True, index=True)

    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    ai_help_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="study_notes")
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class FlashcardDeck(Base):
    __tablename__ = "flashcard_decks"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_flashcard_deck_language",
        ),
        CheckConstraint(
            "source_type IN ('raw_text', 'pdf', 'note', 'chapter', 'custom_tutor_chat')",
            name="ck_flashcard_deck_source_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("grade_levels.id", ondelete="SET NULL"), nullable=True, index=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True, index=True)

    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    cards: Mapped[list["Flashcard"]] = relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
    )


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flashcard_decks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)

    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    deck: Mapped["FlashcardDeck"] = relationship(
        "FlashcardDeck",
        back_populates="cards",
    )

class StudyArtifact(Base):
    __tablename__ = "study_artifacts"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_study_artifact_language",
        ),
        CheckConstraint(
            "source_type IN ('raw_text', 'pdf', 'note', 'chapter', 'custom_tutor_chat')",
            name="ck_study_artifact_source_type",
        ),
        CheckConstraint(
            "artifact_type IN ('mind_map', 'worksheet', 'formula_sheet', 'important_questions')",
            name="ck_study_artifact_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grade_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("grade_levels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    artifact_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    content_markdown: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_json: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )