import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InboxThread(Base):
    __tablename__ = "inbox_threads"

    __table_args__ = (
        CheckConstraint(
            "source IN ('custom_tutor', 'help', 'feedback')",
            name="ck_inbox_thread_source",
        ),
        CheckConstraint(
            "status IN ('open', 'answered', 'closed')",
            name="ck_inbox_thread_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high')",
            name="ck_inbox_thread_priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
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

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="custom_tutor",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
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

    messages: Mapped[list["InboxMessage"]] = relationship(
        "InboxMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
    )


class InboxMessage(Base):
    __tablename__ = "inbox_messages"

    __table_args__ = (
        CheckConstraint(
            "sender_role IN ('student', 'admin', 'system')",
            name="ck_inbox_message_sender_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inbox_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    thread: Mapped["InboxThread"] = relationship(
        "InboxThread",
        back_populates="messages",
    )