import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.remediation.model import (
    RemediationContent,
    RemediationRecheck,
    RemediationSession,
)


class RemediationRepository:
    @staticmethod
    def create_session_with_content(
        db: Session,
        session: RemediationSession,
        content: RemediationContent,
    ) -> RemediationSession:
        db.add(session)
        db.flush()

        content.remediation_session_id = session.id
        db.add(content)

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def get_session_for_user(
        db: Session,
        remediation_session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RemediationSession | None:
        return db.scalar(
            select(RemediationSession).where(
                RemediationSession.id == remediation_session_id,
                RemediationSession.user_id == user_id,
            )
        )

    @staticmethod
    def get_content(
        db: Session,
        remediation_session_id: uuid.UUID,
    ) -> RemediationContent | None:
        return db.scalar(
            select(RemediationContent).where(
                RemediationContent.remediation_session_id == remediation_session_id,
            )
        )

    @staticmethod
    def list_rechecks(
        db: Session,
        remediation_session_id: uuid.UUID,
    ) -> list[RemediationRecheck]:
        return list(
            db.scalars(
                select(RemediationRecheck)
                .where(RemediationRecheck.remediation_session_id == remediation_session_id)
                .order_by(RemediationRecheck.created_at.asc())
            ).all()
        )

    @staticmethod
    def add_recheck(
        db: Session,
        session: RemediationSession,
        recheck: RemediationRecheck,
        new_status: str,
    ) -> RemediationRecheck:
        session.status = new_status

        db.add(recheck)
        db.commit()
        db.refresh(recheck)

        return recheck

    @staticmethod
    def list_user_topic_sessions(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
    ) -> list[RemediationSession]:
        return list(
            db.scalars(
                select(RemediationSession)
                .where(
                    RemediationSession.user_id == user_id,
                    RemediationSession.topic_id == topic_id,
                )
                .order_by(RemediationSession.created_at.desc())
            ).all()
        )