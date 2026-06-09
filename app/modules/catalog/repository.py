import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.model import Chapter, GradeLevel, Subject


class CatalogRepository:
    @staticmethod
    def create(db: Session, item):
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def soft_delete(db: Session, item):
        item.is_active = False
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_grade_by_id(
        db: Session,
        grade_id: uuid.UUID,
    ) -> GradeLevel | None:
        return db.get(GradeLevel, grade_id)

    @staticmethod
    def get_grade_by_slug(
        db: Session,
        slug: str,
    ) -> GradeLevel | None:
        return db.scalar(
            select(GradeLevel).where(
                GradeLevel.slug == slug,
            )
        )

    @staticmethod
    def list_grades(db: Session) -> list[GradeLevel]:
        return list(
            db.scalars(
                select(GradeLevel)
                .where(GradeLevel.is_active.is_(True))
                .order_by(GradeLevel.display_order.asc())
            ).all()
        )

    @staticmethod
    def get_subject_by_id(
        db: Session,
        subject_id: uuid.UUID,
    ) -> Subject | None:
        return db.get(Subject, subject_id)

    @staticmethod
    def get_subject_by_slug(
        db: Session,
        grade_id: uuid.UUID,
        slug: str,
    ) -> Subject | None:
        return db.scalar(
            select(Subject).where(
                Subject.grade_level_id == grade_id,
                Subject.slug == slug,
            )
        )

    @staticmethod
    def list_subjects(
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
    def get_chapter_by_id(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> Chapter | None:
        return db.get(Chapter, chapter_id)

    @staticmethod
    def get_chapter_by_slug(
        db: Session,
        subject_id: uuid.UUID,
        slug: str,
    ) -> Chapter | None:
        return db.scalar(
            select(Chapter).where(
                Chapter.subject_id == subject_id,
                Chapter.slug == slug,
            )
        )

    @staticmethod
    def get_chapter_by_number(
        db: Session,
        subject_id: uuid.UUID,
        chapter_no: int,
    ) -> Chapter | None:
        return db.scalar(
            select(Chapter).where(
                Chapter.subject_id == subject_id,
                Chapter.chapter_no == chapter_no,
            )
        )

    @staticmethod
    def list_chapters(
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