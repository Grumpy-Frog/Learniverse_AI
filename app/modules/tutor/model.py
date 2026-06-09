from __future__ import annotations

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


class TutorGroup(Base):
    __tablename__ = "tutor_groups"

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

    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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

    conversations: Mapped[list["TutorConversation"]] = relationship(
        "TutorConversation",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class TutorConversation(Base):
    __tablename__ = "tutor_conversations"

    __table_args__ = (
        CheckConstraint(
            "language IN ('en', 'bn')",
            name="ck_tutor_conversation_language",
        ),
        CheckConstraint(
            "rag_mode IN ('auto')",
            name="ck_tutor_conversation_rag_mode",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tutor_groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="deepseek",
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Internal only. Student does not choose this.
    rag_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="auto",
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

    group: Mapped["TutorGroup | None"] = relationship(
        "TutorGroup",
        back_populates="conversations",
    )

    messages: Mapped[list["TutorMessage"]] = relationship(
        "TutorMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_tutor_message_role",
        ),
        CheckConstraint(
            "message_type IN ('story', 'chat', 'refusal')",
            name="ck_tutor_message_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tutor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    message_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="chat",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_in_scope: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_source_grounded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    finish_reason: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped["TutorConversation"] = relationship(
        "TutorConversation",
        back_populates="messages",
    )