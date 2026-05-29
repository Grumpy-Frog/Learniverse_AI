import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.model import Chapter, Topic
from app.modules.diagnostics.model import (
    DiagnosticAnswer,
    DiagnosticQuestion,
    DiagnosticSession,
    UserTopicStatus,
)


class DiagnosticsRepository:
    @staticmethod
    def create_session_with_questions(
        db: Session,
        session: DiagnosticSession,
        questions: list[DiagnosticQuestion],
    ) -> DiagnosticSession:
        db.add(session)
        db.flush()

        for question in questions:
            question.session_id = session.id
            db.add(question)

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def get_session_for_user(
        db: Session,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DiagnosticSession | None:
        return db.scalar(
            select(DiagnosticSession).where(
                DiagnosticSession.id == session_id,
                DiagnosticSession.user_id == user_id,
            )
        )

    @staticmethod
    def list_questions(
        db: Session,
        session_id: uuid.UUID,
    ) -> list[DiagnosticQuestion]:
        return list(
            db.scalars(
                select(DiagnosticQuestion)
                .where(DiagnosticQuestion.session_id == session_id)
                .order_by(DiagnosticQuestion.display_order.asc())
            ).all()
        )

    @staticmethod
    def list_answers(
        db: Session,
        session_id: uuid.UUID,
    ) -> list[DiagnosticAnswer]:
        return list(
            db.scalars(
                select(DiagnosticAnswer)
                .where(DiagnosticAnswer.session_id == session_id)
                .order_by(DiagnosticAnswer.created_at.asc())
            ).all()
        )

    @staticmethod
    def get_topic_status(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
    ) -> UserTopicStatus | None:
        return db.scalar(
            select(UserTopicStatus).where(
                UserTopicStatus.user_id == user_id,
                UserTopicStatus.topic_id == topic_id,
            )
        )

    @staticmethod
    def save_evaluation(
        db: Session,
        session: DiagnosticSession,
        answers: list[DiagnosticAnswer],
        score: float,
        percentage: float,
        outcome: str,
        strengths: list[str],
        weaknesses: list[str],
        update_topic_status: bool,
        pass_percentage: float,
    ) -> DiagnosticSession:
        submitted_at = datetime.now(timezone.utc)

        db.add_all(answers)

        session.status = "evaluated"
        session.score = score
        session.percentage = percentage
        session.outcome = outcome
        session.submitted_at = submitted_at

        if update_topic_status:
            status_record = DiagnosticsRepository.get_topic_status(
                db,
                session.user_id,
                session.topic_id,
            )

            if status_record is None:
                status_record = UserTopicStatus(
                    user_id=session.user_id,
                    topic_id=session.topic_id,
                    completion_status="not_started",
                    strength_labels=[],
                    weakness_labels=[],
                )
                db.add(status_record)

            status_record.latest_score = percentage
            status_record.best_score = max(
                status_record.best_score or 0.0,
                percentage,
            )
            status_record.strength_labels = strengths
            status_record.weakness_labels = weaknesses

            if percentage >= pass_percentage:
                status_record.completion_status = "completed"

                if status_record.completed_at is None:
                    status_record.completed_at = submitted_at
            elif status_record.completion_status != "completed":
                status_record.completion_status = "needs_practice"

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def list_active_topic_ids_for_subject(
        db: Session,
        subject_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        return list(
            db.scalars(
                select(Topic.id)
                .join(Chapter, Topic.chapter_id == Chapter.id)
                .where(
                    Chapter.subject_id == subject_id,
                    Chapter.is_active.is_(True),
                    Topic.is_active.is_(True),
                )
            ).all()
        )

    @staticmethod
    def list_statuses_for_topics(
        db: Session,
        user_id: uuid.UUID,
        topic_ids: list[uuid.UUID],
    ) -> list[UserTopicStatus]:
        if not topic_ids:
            return []

        return list(
            db.scalars(
                select(UserTopicStatus).where(
                    UserTopicStatus.user_id == user_id,
                    UserTopicStatus.topic_id.in_(topic_ids),
                )
            ).all()
        )