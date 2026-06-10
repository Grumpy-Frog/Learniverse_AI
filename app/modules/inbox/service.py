import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.model import User
from app.modules.catalog.repository import CatalogRepository
from app.modules.inbox.model import InboxMessage, InboxThread
from app.modules.inbox.repository import InboxRepository
from app.modules.inbox.schema import (
    InboxMessageCreateRequest,
    InboxThreadCreateRequest,
    InboxThreadStatusUpdateRequest,
)


class InboxService:
    @staticmethod
    def _ensure_thread_access(
        thread: InboxThread,
        current_user: User,
        admin_allowed: bool = True,
    ) -> None:
        if admin_allowed and current_user.role == "admin":
            return

        if thread.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this inbox thread",
            )

    @staticmethod
    def _validate_subject_and_chapter(
        db: Session,
        subject_id: uuid.UUID | None,
        chapter_id: uuid.UUID | None,
    ) -> tuple[uuid.UUID | None, uuid.UUID | None]:
        final_subject_id = subject_id

        if chapter_id:
            chapter = CatalogRepository.get_chapter_by_id(
                db,
                chapter_id,
            )

            if not chapter or not chapter.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chapter not found",
                )

            if subject_id and chapter.subject_id != subject_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chapter does not belong to the selected subject",
                )

            final_subject_id = chapter.subject_id

        elif subject_id:
            subject = CatalogRepository.get_subject_by_id(
                db,
                subject_id,
            )

            if not subject or not subject.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found",
                )

        return final_subject_id, chapter_id

    @staticmethod
    def _thread_detail(
        db: Session,
        thread: InboxThread,
    ) -> dict:
        return {
            "thread": thread,
            "messages": InboxRepository.list_messages(
                db,
                thread.id,
            ),
        }

    @staticmethod
    def create_thread(
        db: Session,
        payload: InboxThreadCreateRequest,
        current_user: User,
    ) -> dict:
        subject_id, chapter_id = InboxService._validate_subject_and_chapter(
            db,
            payload.subject_id,
            payload.chapter_id,
        )

        thread = InboxThread(
            student_id=current_user.id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            title=payload.title,
            source=payload.source,
            priority=payload.priority,
            status="open",
        )

        message = InboxMessage(
            thread_id=thread.id,
            sender_id=current_user.id,
            sender_role="student",
            body=payload.body,
            is_internal=False,
        )

        created_thread = InboxRepository.create_thread_with_message(
            db,
            thread,
            message,
        )

        return InboxService._thread_detail(
            db,
            created_thread,
        )

    @staticmethod
    def list_my_threads(
        db: Session,
        current_user: User,
    ) -> dict:
        return {
            "threads": InboxRepository.list_student_threads(
                db,
                current_user.id,
            )
        }

    @staticmethod
    def list_admin_threads(
        db: Session,
        status_filter: str | None,
    ) -> dict:
        return {
            "threads": InboxRepository.list_all_threads(
                db,
                status_filter,
            )
        }

    @staticmethod
    def get_thread(
        db: Session,
        thread_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        thread = InboxRepository.get_thread(
            db,
            thread_id,
        )

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inbox thread not found",
            )

        InboxService._ensure_thread_access(
            thread,
            current_user,
        )

        return InboxService._thread_detail(
            db,
            thread,
        )

    @staticmethod
    def get_admin_thread(
        db: Session,
        thread_id: uuid.UUID,
    ) -> dict:
        thread = InboxRepository.get_thread(
            db,
            thread_id,
        )

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inbox thread not found",
            )

        return InboxService._thread_detail(
            db,
            thread,
        )

    @staticmethod
    def add_student_message(
        db: Session,
        thread_id: uuid.UUID,
        payload: InboxMessageCreateRequest,
        current_user: User,
    ) -> dict:
        thread = InboxRepository.get_thread(
            db,
            thread_id,
        )

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inbox thread not found",
            )

        InboxService._ensure_thread_access(
            thread,
            current_user,
            admin_allowed=False,
        )

        if thread.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This inbox thread is closed",
            )

        message = InboxMessage(
            thread_id=thread.id,
            sender_id=current_user.id,
            sender_role="student",
            body=payload.body,
            is_internal=False,
        )

        InboxRepository.add_message(
            db,
            thread,
            message,
            new_status="open",
        )

        return InboxService._thread_detail(
            db,
            thread,
        )

    @staticmethod
    def add_admin_message(
        db: Session,
        thread_id: uuid.UUID,
        payload: InboxMessageCreateRequest,
        admin_user: User,
    ) -> dict:
        thread = InboxRepository.get_thread(
            db,
            thread_id,
        )

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inbox thread not found",
            )

        if thread.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This inbox thread is closed",
            )

        message = InboxMessage(
            thread_id=thread.id,
            sender_id=admin_user.id,
            sender_role="admin",
            body=payload.body,
            is_internal=False,
        )

        if thread.assigned_admin_id is None:
            thread.assigned_admin_id = admin_user.id

        InboxRepository.add_message(
            db,
            thread,
            message,
            new_status="answered",
        )

        return InboxService._thread_detail(
            db,
            thread,
        )

    @staticmethod
    def update_admin_thread(
        db: Session,
        thread_id: uuid.UUID,
        payload: InboxThreadStatusUpdateRequest,
    ) -> InboxThread:
        thread = InboxRepository.get_thread(
            db,
            thread_id,
        )

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inbox thread not found",
            )

        update_data = payload.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(thread, field, value)

        return InboxRepository.update_thread(
            db,
            thread,
        )

    @staticmethod
    def close_my_thread(
        db: Session,
        thread_id: uuid.UUID,
        current_user: User,
    ) -> InboxThread:
        thread = InboxRepository.get_thread(
            db,
            thread_id,
        )

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inbox thread not found",
            )

        InboxService._ensure_thread_access(
            thread,
            current_user,
            admin_allowed=False,
        )

        thread.status = "closed"

        return InboxRepository.update_thread(
            db,
            thread,
        )