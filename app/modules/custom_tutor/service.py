import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.model import User
from app.modules.catalog.model import Chapter, GradeLevel, Subject
from app.modules.catalog.repository import CatalogRepository
from app.modules.custom_tutor.model import CustomTutorChat, CustomTutorMessage
from app.modules.custom_tutor.prompts import custom_tutor_messages
from app.modules.custom_tutor.repository import CustomTutorRepository
from app.modules.custom_tutor.schema import (
    CustomTutorChatCreateRequest,
    CustomTutorChatRenameRequest,
    CustomTutorMessageCreateRequest,
)
from app.modules.tutor.deepseek_provider import DeepSeekProvider


class CustomTutorService:
    @staticmethod
    def _get_chat(
        db: Session,
        chat_id: uuid.UUID,
        current_user: User,
    ) -> CustomTutorChat:
        chat = CustomTutorRepository.get_chat_for_user(
            db,
            chat_id,
            current_user.id,
        )

        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom tutor chat not found",
            )

        return chat

    @staticmethod
    def _resolve_context(
        db: Session,
        grade_id: uuid.UUID | None,
        subject_id: uuid.UUID | None,
        chapter_id: uuid.UUID | None,
    ) -> tuple[GradeLevel | None, Subject | None, Chapter | None]:
        grade = None
        subject = None
        chapter = None

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

            subject = chapter.subject
            grade = subject.grade_level

            if subject_id and subject.id != subject_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chapter does not belong to selected subject",
                )

            if grade_id and grade.id != grade_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chapter does not belong to selected grade",
                )

            return grade, subject, chapter

        if subject_id:
            subject = CatalogRepository.get_subject_by_id(
                db,
                subject_id,
            )

            if not subject or not subject.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found",
                )

            grade = subject.grade_level

            if grade_id and grade.id != grade_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject does not belong to selected grade",
                )

            return grade, subject, None

        if grade_id:
            grade = CatalogRepository.get_grade_by_id(
                db,
                grade_id,
            )

            if not grade or not grade.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Grade not found",
                )

        return grade, None, None

    @staticmethod
    def create_chat(
        db: Session,
        payload: CustomTutorChatCreateRequest,
        current_user: User,
    ) -> CustomTutorChat:
        grade, subject, chapter = CustomTutorService._resolve_context(
            db,
            payload.grade_id,
            payload.subject_id,
            payload.chapter_id,
        )

        title = payload.title or "New chat"

        chat = CustomTutorChat(
            user_id=current_user.id,
            grade_id=grade.id if grade else None,
            subject_id=subject.id if subject else None,
            chapter_id=chapter.id if chapter else None,
            title=title,
            language=payload.language,
        )

        return CustomTutorRepository.create_chat(
            db,
            chat,
        )

    @staticmethod
    def list_chats(
        db: Session,
        current_user: User,
    ) -> dict:
        return {
            "chats": CustomTutorRepository.list_chats_for_user(
                db,
                current_user.id,
            )
        }

    @staticmethod
    def get_chat_detail(
        db: Session,
        chat_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        chat = CustomTutorService._get_chat(
            db,
            chat_id,
            current_user,
        )

        return {
            "chat": chat,
            "messages": CustomTutorRepository.list_messages(
                db,
                chat.id,
            ),
        }

    @staticmethod
    def rename_chat(
        db: Session,
        chat_id: uuid.UUID,
        payload: CustomTutorChatRenameRequest,
        current_user: User,
    ) -> CustomTutorChat:
        chat = CustomTutorService._get_chat(
            db,
            chat_id,
            current_user,
        )

        return CustomTutorRepository.rename_chat(
            db,
            chat,
            payload.title,
        )

    @staticmethod
    def delete_chat(
        db: Session,
        chat_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        chat = CustomTutorService._get_chat(
            db,
            chat_id,
            current_user,
        )

        deleted_id = chat.id

        CustomTutorRepository.archive_chat(
            db,
            chat,
        )

        return {
            "deleted_id": deleted_id,
            "message": "Custom tutor chat deleted successfully",
        }

    @staticmethod
    async def send_message(
        db: Session,
        chat_id: uuid.UUID,
        payload: CustomTutorMessageCreateRequest,
        current_user: User,
    ) -> dict:
        chat = CustomTutorService._get_chat(
            db,
            chat_id,
            current_user,
        )

        grade, subject, chapter = CustomTutorService._resolve_context(
            db,
            chat.grade_id,
            chat.subject_id,
            chat.chapter_id,
        )

        history = CustomTutorRepository.list_recent_messages(
            db,
            chat.id,
            limit=12,
        )

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete(
            messages=custom_tutor_messages(
                language=chat.language,
                grade=grade,
                subject=subject,
                chapter=chapter,
                history=history,
                student_message=payload.message,
            ),
            max_tokens=900,
            temperature=0.4,
        )

        user_message = CustomTutorMessage(
            chat_id=chat.id,
            role="user",
            content=payload.message,
        )

        assistant_message = CustomTutorMessage(
            chat_id=chat.id,
            role="assistant",
            content=completion.content,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            finish_reason=completion.finish_reason,
        )

        saved_user_message, saved_assistant_message = (
            CustomTutorRepository.add_message_pair(
                db,
                chat,
                user_message,
                assistant_message,
            )
        )

        if chat.title == "New chat":
            title = payload.message.strip()[:80]
            CustomTutorRepository.rename_chat(
                db,
                chat,
                title,
            )

        return {
            "chat": chat,
            "user_message": saved_user_message,
            "assistant_message": saved_assistant_message,
        }