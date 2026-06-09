import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.tutor.model import TutorConversation, TutorGroup, TutorMessage


class TutorRepository:
    @staticmethod
    def create_group(
        db: Session,
        group: TutorGroup,
    ) -> TutorGroup:
        db.add(group)
        db.commit()
        db.refresh(group)
        return group

    @staticmethod
    def list_user_groups(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[TutorGroup]:
        return list(
            db.scalars(
                select(TutorGroup)
                .where(TutorGroup.user_id == user_id)
                .order_by(TutorGroup.updated_at.desc())
            ).all()
        )

    @staticmethod
    def get_group_for_user(
        db: Session,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TutorGroup | None:
        return db.scalar(
            select(TutorGroup).where(
                TutorGroup.id == group_id,
                TutorGroup.user_id == user_id,
            )
        )

    @staticmethod
    def get_first_group_for_subject(
        db: Session,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
    ) -> TutorGroup | None:
        return db.scalar(
            select(TutorGroup)
            .where(
                TutorGroup.user_id == user_id,
                TutorGroup.subject_id == subject_id,
            )
            .order_by(TutorGroup.created_at.asc())
        )

    @staticmethod
    def delete_group(
        db: Session,
        group: TutorGroup,
    ) -> None:
        db.delete(group)
        db.commit()

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
    def list_subject_conversations(
        db: Session,
        user_id: uuid.UUID,
        subject_id: uuid.UUID,
    ) -> list[TutorConversation]:
        return list(
            db.scalars(
                select(TutorConversation)
                .where(
                    TutorConversation.user_id == user_id,
                    TutorConversation.subject_id == subject_id,
                )
                .order_by(TutorConversation.updated_at.desc())
            ).all()
        )

    @staticmethod
    def list_chapter_conversations(
        db: Session,
        user_id: uuid.UUID,
        chapter_id: uuid.UUID,
    ) -> list[TutorConversation]:
        return list(
            db.scalars(
                select(TutorConversation)
                .where(
                    TutorConversation.user_id == user_id,
                    TutorConversation.chapter_id == chapter_id,
                )
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
    def delete_conversation(
        db: Session,
        conversation: TutorConversation,
    ) -> None:
        db.delete(conversation)
        db.commit()

    @staticmethod
    def add_message(
        db: Session,
        conversation: TutorConversation,
        message: TutorMessage,
    ) -> TutorMessage:
        now = datetime.now(timezone.utc)

        conversation.updated_at = now

        if conversation.group:
            conversation.group.updated_at = now

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