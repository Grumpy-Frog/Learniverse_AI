import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.tutor.model import TutorConversation, TutorMessage


class TutorRepository:
    @staticmethod
    def create_conversation(
        db: Session,
        conversation: TutorConversation,
    ) -> TutorConversation:
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def list_user_conversations(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[TutorConversation]:
        return list(
            db.scalars(
                select(TutorConversation)
                .where(TutorConversation.user_id == user_id)
                .order_by(TutorConversation.updated_at.desc())
            ).all()
        )

    @staticmethod
    def get_conversation_for_user(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TutorConversation | None:
        return db.scalar(
            select(TutorConversation).where(
                TutorConversation.id == conversation_id,
                TutorConversation.user_id == user_id,
            )
        )

    @staticmethod
    def update_settings(
        db: Session,
        conversation: TutorConversation,
        use_rag: bool,
    ) -> TutorConversation:
        conversation.use_rag = use_rag
        conversation.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def add_message(
        db: Session,
        conversation: TutorConversation,
        message: TutorMessage,
    ) -> TutorMessage:
        conversation.updated_at = datetime.now(timezone.utc)

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def list_messages(
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[TutorMessage]:
        return list(
            db.scalars(
                select(TutorMessage)
                .where(TutorMessage.conversation_id == conversation_id)
                .order_by(TutorMessage.created_at.asc())
            ).all()
        )

    @staticmethod
    def list_recent_messages(
        db: Session,
        conversation_id: uuid.UUID,
        limit: int = 12,
    ) -> list[TutorMessage]:
        messages = list(
            db.scalars(
                select(TutorMessage)
                .where(TutorMessage.conversation_id == conversation_id)
                .order_by(TutorMessage.created_at.desc())
                .limit(limit)
            ).all()
        )

        return list(reversed(messages))