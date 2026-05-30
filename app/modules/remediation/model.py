from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RemediationSession(Base):
    __tablename__ = "remediation_sessions"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_remediation_session_language",
        ),
        CheckConstraint(
            "status IN ('generated', 'completed', 'needs_retry')",
            name="ck_remediation_session_status",
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

    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    diagnostic_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    weakness_label: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="generated",
    )

    is_source_grounded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    content: Mapped[RemediationContent | None] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False,
    )

    rechecks: Mapped[list[RemediationRecheck]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class RemediationContent(Base):
    __tablename__ = "remediation_contents"

    __table_args__ = (
        UniqueConstraint(
            "remediation_session_id",
            name="uq_remediation_content_session",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    remediation_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("remediation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    weakness_statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    micro_lesson: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    guided_example: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    partially_solved_problem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recheck_question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expected_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    next_action: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped[RemediationSession] = relationship(
        back_populates="content",
    )


class RemediationRecheck(Base):
    __tablename__ = "remediation_rechecks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    remediation_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("remediation_sessions.id", ondelete="CASCADE"),
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

    next_action: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped[RemediationSession] = relationship(
        back_populates="rechecks",
    )