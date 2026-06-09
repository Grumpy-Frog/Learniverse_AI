import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_diagnostic_session_language",
        ),
        CheckConstraint(
            "assessment_type IN ('understanding_check', 'chapter_quiz', 'recheck')",
            name="ck_diagnostic_session_assessment_type",
        ),
        CheckConstraint(
            "status IN ('generated', 'evaluated')",
            name="ck_diagnostic_session_status",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('understood', 'needs_diagnostic', 'strong', 'needs_practice')",
            name="ck_diagnostic_session_outcome",
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

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tutor_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
    )

    assessment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="generated",
    )

    question_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    percentage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    outcome: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    questions: Mapped[list["DiagnosticQuestion"]] = relationship(
        "DiagnosticQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    answers: Mapped[list["DiagnosticAnswer"]] = relationship(
        "DiagnosticAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class DiagnosticQuestion(Base):
    __tablename__ = "diagnostic_questions"

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('mcq', 'short_answer')",
            name="ck_diagnostic_question_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    options: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    correct_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evaluation_rubric: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skill_label: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    max_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["DiagnosticSession"] = relationship(
        "DiagnosticSession",
        back_populates="questions",
    )

    answers: Mapped[list["DiagnosticAnswer"]] = relationship(
        "DiagnosticAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class DiagnosticAnswer(Base):
    __tablename__ = "diagnostic_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnostic_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    feedback: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    detected_weakness: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    confidence: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    evaluation_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["DiagnosticSession"] = relationship(
        "DiagnosticSession",
        back_populates="answers",
    )

    question: Mapped["DiagnosticQuestion"] = relationship(
        "DiagnosticQuestion",
        back_populates="answers",
    )


class UserChapterStatus(Base):
    __tablename__ = "user_chapter_statuses"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chapter_id",
            name="uq_user_chapter_status",
        ),
        CheckConstraint(
            "completion_status IN ('not_started', 'needs_practice', 'completed')",
            name="ck_user_chapter_completion_status",
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

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    completion_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="not_started",
    )

    latest_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    best_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    strength_labels: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    weakness_labels: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )