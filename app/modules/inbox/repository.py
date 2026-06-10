import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inbox.model import InboxMessage, InboxThread


class InboxRepository:
    @staticmethod
    def create_thread_with_message(
        db: Session,
        thread: InboxThread,
        message: InboxMessage,
    ) -> InboxThread:
        db.add(thread)
        db.flush()

        message.thread_id = thread.id
        db.add(message)

        db.commit()
        db.refresh(thread)

        return thread

    @staticmethod
    def get_thread(
        db: Session,
        thread_id: uuid.UUID,
    ) -> InboxThread | None:
        return db.get(InboxThread, thread_id)

    @staticmethod
    def list_student_threads(
        db: Session,
        student_id: uuid.UUID,
    ) -> list[InboxThread]:
        return list(
            db.scalars(
                select(InboxThread)
                .where(InboxThread.student_id == student_id)
                .order_by(InboxThread.updated_at.desc())
            ).all()
        )

    @staticmethod
    def list_all_threads(
        db: Session,
        status: str | None = None,
    ) -> list[InboxThread]:
        statement = select(InboxThread)

        if status:
            statement = statement.where(InboxThread.status == status)

        return list(
            db.scalars(
                statement.order_by(InboxThread.updated_at.desc())
            ).all()
        )

    @staticmethod
    def list_messages(
        db: Session,
        thread_id: uuid.UUID,
    ) -> list[InboxMessage]:
        return list(
            db.scalars(
                select(InboxMessage)
                .where(InboxMessage.thread_id == thread_id)
                .order_by(InboxMessage.created_at.asc())
            ).all()
        )

    @staticmethod
    def add_message(
        db: Session,
        thread: InboxThread,
        message: InboxMessage,
        new_status: str,
    ) -> InboxMessage:
        thread.status = new_status
        thread.updated_at = datetime.now(timezone.utc)

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def update_thread(
        db: Session,
        thread: InboxThread,
    ) -> InboxThread:
        thread.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(thread)

        return thread