
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.catalog.model import Chapter, GradeLevel, Subject, Topic
from app.modules.catalog.repository import CatalogRepository
from app.modules.catalog.schema import (
    ChapterCreateRequest,
    GradeCreateRequest,
    SubjectCreateRequest,
    TopicCreateRequest,
)


class CatalogService:
    @staticmethod
    def create_grade(db: Session, payload: GradeCreateRequest) -> GradeLevel:
        existing = CatalogRepository.get_grade_by_slug(db, payload.slug)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Grade level with this slug already exists",
            )

        grade = GradeLevel(**payload.model_dump())
        return CatalogRepository.create(db, grade)

    @staticmethod
    def list_grades(db: Session) -> list[GradeLevel]:
        return CatalogRepository.list_grades(db)

    @staticmethod
    def create_subject(
        db: Session,
        grade_id: uuid.UUID,
        payload: SubjectCreateRequest,
    ) -> Subject:
        grade = CatalogRepository.get_grade_by_id(db, grade_id)

        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade level not found",
            )

        existing = CatalogRepository.get_subject_by_slug(
            db,
            grade_id,
            payload.slug,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subject with this slug already exists in this grade",
            )

        subject = Subject(
            grade_level_id=grade_id,
            **payload.model_dump(),
        )

        return CatalogRepository.create(db, subject)

    @staticmethod
    def list_subjects(db: Session, grade_id: uuid.UUID) -> list[Subject]:
        grade = CatalogRepository.get_grade_by_id(db, grade_id)

        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade level not found",
            )

        return CatalogRepository.list_subjects(db, grade_id)

    @staticmethod
    def create_chapter(
        db: Session,
        subject_id: uuid.UUID,
        payload: ChapterCreateRequest,
    ) -> Chapter:
        subject = CatalogRepository.get_subject_by_id(db, subject_id)

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        existing = CatalogRepository.get_chapter_by_slug(
            db,
            subject_id,
            payload.slug,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chapter with this slug already exists in this subject",
            )

        chapter = Chapter(
            subject_id=subject_id,
            **payload.model_dump(),
        )

        return CatalogRepository.create(db, chapter)

    @staticmethod
    def list_chapters(db: Session, subject_id: uuid.UUID) -> list[Chapter]:
        subject = CatalogRepository.get_subject_by_id(db, subject_id)

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        return CatalogRepository.list_chapters(db, subject_id)

    @staticmethod
    def create_topic(
        db: Session,
        chapter_id: uuid.UUID,
        payload: TopicCreateRequest,
    ) -> Topic:
        chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        existing = CatalogRepository.get_topic_by_slug(
            db,
            chapter_id,
            payload.slug,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Topic with this slug already exists in this chapter",
            )

        topic = Topic(
            chapter_id=chapter_id,
            **payload.model_dump(),
        )

        return CatalogRepository.create(db, topic)

    @staticmethod
    def list_topics(db: Session, chapter_id: uuid.UUID) -> list[Topic]:
        chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        return CatalogRepository.list_topics(db, chapter_id)

    @staticmethod
    def get_topic(db: Session, topic_id: uuid.UUID) -> Topic:
        topic = CatalogRepository.get_topic_by_id(db, topic_id)

        if not topic or not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        return topic