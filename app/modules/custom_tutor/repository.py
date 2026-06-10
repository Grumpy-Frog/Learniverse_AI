import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.custom_tutor.model import (
    CustomTutorChat,
    CustomTutorMessage,
)


class CustomTutorRepository:
    @staticmethod
    def create_chat(
        db: Session,
        chat: CustomTutorChat,
    ) -> CustomTutorChat:
        db.add(chat)
        db.commit()
        db.refresh(chat)

        return chat

    @staticmethod
    def get_chat_for_user(
        db: Session,
        chat_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CustomTutorChat | None:
        return db.scalar(
            select(CustomTutorChat).where(
                CustomTutorChat.id == chat_id,
                CustomTutorChat.user_id == user_id,
                CustomTutorChat.is_archived.is_(False),
            )
        )

    @staticmethod
    def list_chats_for_user(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[CustomTutorChat]:
        return list(
            db.scalars(
                select(CustomTutorChat)
                .where(
                    CustomTutorChat.user_id == user_id,
                    CustomTutorChat.is_archived.is_(False),
                )
                .order_by(CustomTutorChat.updated_at.desc())
            ).all()
        )

    @staticmethod
    def list_messages(
        db: Session,
        chat_id: uuid.UUID,
    ) -> list[CustomTutorMessage]:
        return list(
            db.scalars(
                select(CustomTutorMessage)
                .where(CustomTutorMessage.chat_id == chat_id)
                .order_by(CustomTutorMessage.created_at.asc())
            ).all()
        )

    @staticmethod
    def list_recent_messages(
        db: Session,
        chat_id: uuid.UUID,
        limit: int = 12,
    ) -> list[CustomTutorMessage]:
        messages = list(
            db.scalars(
                select(CustomTutorMessage)
                .where(CustomTutorMessage.chat_id == chat_id)
                .order_by(CustomTutorMessage.created_at.desc())
                .limit(limit)
            ).all()
        )

        return list(reversed(messages))

    @staticmethod
    def add_message_pair(
        db: Session,
        chat: CustomTutorChat,
        user_message: CustomTutorMessage,
        assistant_message: CustomTutorMessage,
    ) -> tuple[CustomTutorMessage, CustomTutorMessage]:
        db.add(user_message)
        db.flush()

        db.add(assistant_message)

        chat.message_count += 2
        chat.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(chat)
        db.refresh(user_message)
        db.refresh(assistant_message)

        return user_message, assistant_message

    @staticmethod
    def rename_chat(
        db: Session,
        chat: CustomTutorChat,
        title: str,
    ) -> CustomTutorChat:
        chat.title = title
        chat.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(chat)

        return chat

    @staticmethod
    def archive_chat(
        db: Session,
        chat: CustomTutorChat,
    ) -> CustomTutorChat:
        chat.is_archived = True
        chat.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(chat)

        return chat