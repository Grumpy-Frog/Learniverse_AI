import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.model import Chapter, GradeLevel, Subject
from app.modules.diagnostics.model import DiagnosticSession, UserChapterStatus


class DashboardRepository:
    @staticmethod
    def list_active_grades(db: Session) -> list[GradeLevel]:
        return list(
            db.scalars(
                select(GradeLevel)
                .where(GradeLevel.is_active.is_(True))
                .order_by(GradeLevel.display_order.asc())
            ).all()
        )

    @staticmethod
    def list_active_subjects_for_grade(
        db: Session,
        grade_id: uuid.UUID,
    ) -> list[Subject]:
        return list(
            db.scalars(
                select(Subject)
                .where(
                    Subject.grade_level_id == grade_id,
                    Subject.is_active.is_(True),
                )
                .order_by(Subject.display_order.asc())
            ).all()
        )

    @staticmethod
    def list_active_chapters_for_subject(
        db: Session,
        subject_id: uuid.UUID,
    ) -> list[Chapter]:
        return list(
            db.scalars(
                select(Chapter)
                .where(
                    Chapter.subject_id == subject_id,
                    Chapter.is_active.is_(True),
                )
                .order_by(Chapter.chapter_no.asc())
            ).all()
        )

    @staticmethod
    def get_grade(
        db: Session,
        grade_id: uuid.UUID,
    ) -> GradeLevel | None:
        return db.get(GradeLevel, grade_id)

    @staticmethod
    def get_subject(
        db: Session,
        subject_id: uuid.UUID,
    ) -> Subject | None:
        return db.get(Subject, subject_id)

    @staticmethod
    def get_chapter(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> Chapter | None:
        return db.get(Chapter, chapter_id)

    @staticmethod
    def list_statuses_for_user(
        db: Session,
        user_id: uuid.UUID,
        chapter_ids: list[uuid.UUID],
    ) -> list[UserChapterStatus]:
        if not chapter_ids:
            return []

        return list(
            db.scalars(
                select(UserChapterStatus).where(
                    UserChapterStatus.user_id == user_id,
                    UserChapterStatus.chapter_id.in_(chapter_ids),
                )
            ).all()
        )

    @staticmethod
    def list_recent_diagnostic_sessions(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 5,
    ) -> list[DiagnosticSession]:
        return list(
            db.scalars(
                select(DiagnosticSession)
                .where(DiagnosticSession.user_id == user_id)
                .order_by(DiagnosticSession.created_at.desc())
                .limit(limit)
            ).all()
        )