
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.model import User
from app.modules.catalog.model import Chapter, GradeLevel, Subject, Topic
from app.modules.catalog.schema import (
    ChapterCreateRequest,
    ChapterResponse,
    GradeCreateRequest,
    GradeResponse,
    SubjectCreateRequest,
    SubjectResponse,
    TopicCreateRequest,
    TopicResponse,
)
from app.modules.catalog.service import CatalogService


router = APIRouter(
    prefix="/catalog",
    tags=["Catalog"],
)


@router.post(
    "/grades",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_grade(
    payload: GradeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> GradeLevel:
    return CatalogService.create_grade(db, payload)


@router.get(
    "/grades",
    response_model=list[GradeResponse],
)
def list_grades(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[GradeLevel]:
    return CatalogService.list_grades(db)


@router.post(
    "/grades/{grade_id}/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    grade_id: uuid.UUID,
    payload: SubjectCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Subject:
    return CatalogService.create_subject(db, grade_id, payload)


@router.get(
    "/grades/{grade_id}/subjects",
    response_model=list[SubjectResponse],
)
def list_subjects(
    grade_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Subject]:
    return CatalogService.list_subjects(db, grade_id)


@router.post(
    "/subjects/{subject_id}/chapters",
    response_model=ChapterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chapter(
    subject_id: uuid.UUID,
    payload: ChapterCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Chapter:
    return CatalogService.create_chapter(db, subject_id, payload)


@router.get(
    "/subjects/{subject_id}/chapters",
    response_model=list[ChapterResponse],
)
def list_chapters(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Chapter]:
    return CatalogService.list_chapters(db, subject_id)


@router.post(
    "/chapters/{chapter_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    chapter_id: uuid.UUID,
    payload: TopicCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Topic:
    return CatalogService.create_topic(db, chapter_id, payload)


@router.get(
    "/chapters/{chapter_id}/topics",
    response_model=list[TopicResponse],
)
def list_topics(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Topic]:
    return CatalogService.list_topics(db, chapter_id)


@router.get(
    "/topics/{topic_id}",
    response_model=TopicResponse,
)
def get_topic(
    topic_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Topic:
    return CatalogService.get_topic(db, topic_id)