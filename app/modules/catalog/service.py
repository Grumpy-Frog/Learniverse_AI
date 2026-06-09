import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.catalog.model import Chapter, GradeLevel, Subject
from app.modules.catalog.repository import CatalogRepository
from app.modules.catalog.schema import (
    ChapterCreateRequest,
    GradeCreateRequest,
    SubjectCreateRequest,
)


class CatalogService:
    @staticmethod
    def create_grade(
        db: Session,
        payload: GradeCreateRequest,
    ) -> GradeLevel:
        existing = CatalogRepository.get_grade_by_slug(
            db,
            payload.slug,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Grade level with this slug already exists",
            )

        grade = GradeLevel(**payload.model_dump())

        return CatalogRepository.create(
            db,
            grade,
        )

    @staticmethod
    def list_grades(db: Session) -> list[GradeLevel]:
        return CatalogRepository.list_grades(db)

    @staticmethod
    def get_grade(
        db: Session,
        grade_id: uuid.UUID,
    ) -> GradeLevel:
        grade = CatalogRepository.get_grade_by_id(
            db,
            grade_id,
        )

        if not grade or not grade.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade level not found",
            )

        return grade

    @staticmethod
    def create_subject(
        db: Session,
        grade_id: uuid.UUID,
        payload: SubjectCreateRequest,
    ) -> Subject:
        grade = CatalogService.get_grade(
            db,
            grade_id,
        )

        existing = CatalogRepository.get_subject_by_slug(
            db,
            grade.id,
            payload.slug,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subject with this slug already exists in this grade",
            )

        subject = Subject(
            grade_level_id=grade.id,
            **payload.model_dump(),
        )

        return CatalogRepository.create(
            db,
            subject,
        )

    @staticmethod
    def list_subjects(
        db: Session,
        grade_id: uuid.UUID,
    ) -> list[Subject]:
        grade = CatalogService.get_grade(
            db,
            grade_id,
        )

        return CatalogRepository.list_subjects(
            db,
            grade.id,
        )

    @staticmethod
    def get_subject(
        db: Session,
        subject_id: uuid.UUID,
    ) -> Subject:
        subject = CatalogRepository.get_subject_by_id(
            db,
            subject_id,
        )

        if not subject or not subject.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        return subject

    @staticmethod
    def create_chapter(
        db: Session,
        subject_id: uuid.UUID,
        payload: ChapterCreateRequest,
    ) -> Chapter:
        subject = CatalogService.get_subject(
            db,
            subject_id,
        )

        existing_slug = CatalogRepository.get_chapter_by_slug(
            db,
            subject.id,
            payload.slug,
        )

        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chapter with this slug already exists in this subject",
            )

        existing_number = CatalogRepository.get_chapter_by_number(
            db,
            subject.id,
            payload.chapter_no,
        )

        if existing_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chapter number already exists in this subject",
            )

        chapter = Chapter(
            subject_id=subject.id,
            **payload.model_dump(),
        )

        return CatalogRepository.create(
            db,
            chapter,
        )

    @staticmethod
    def list_chapters(
        db: Session,
        subject_id: uuid.UUID,
    ) -> list[Chapter]:
        subject = CatalogService.get_subject(
            db,
            subject_id,
        )

        return CatalogRepository.list_chapters(
            db,
            subject.id,
        )

    @staticmethod
    def get_chapter(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> Chapter:
        chapter = CatalogRepository.get_chapter_by_id(
            db,
            chapter_id,
        )

        if not chapter or not chapter.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        return chapter

    @staticmethod
    def delete_grade(
        db: Session,
        grade_id: uuid.UUID,
    ) -> dict:
        grade = CatalogService.get_grade(
            db,
            grade_id,
        )

        CatalogRepository.soft_delete(
            db,
            grade,
        )

        return {
            "deleted_id": grade.id,
            "item_type": "grade",
            "soft_deleted": True,
            "message": "Grade level deleted successfully",
        }

    @staticmethod
    def delete_subject(
        db: Session,
        subject_id: uuid.UUID,
    ) -> dict:
        subject = CatalogService.get_subject(
            db,
            subject_id,
        )

        CatalogRepository.soft_delete(
            db,
            subject,
        )

        return {
            "deleted_id": subject.id,
            "item_type": "subject",
            "soft_deleted": True,
            "message": "Subject deleted successfully",
        }

    @staticmethod
    def delete_chapter(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> dict:
        chapter = CatalogService.get_chapter(
            db,
            chapter_id,
        )

        CatalogRepository.soft_delete(
            db,
            chapter,
        )

        return {
            "deleted_id": chapter.id,
            "item_type": "chapter",
            "soft_deleted": True,
            "message": "Chapter deleted successfully",
        }