import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.model import User
from app.modules.catalog.model import Chapter, GradeLevel, Subject
from app.modules.catalog.schema import (
    ChapterCreateRequest,
    ChapterResponse,
    DeleteCatalogResponse,
    GradeCreateRequest,
    GradeResponse,
    SubjectCreateRequest,
    SubjectResponse,
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
    return CatalogService.create_grade(
        db,
        payload,
    )


@router.get(
    "/grades",
    response_model=list[GradeResponse],
)
def list_grades(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[GradeLevel]:
    return CatalogService.list_grades(db)


@router.get(
    "/grades/{grade_id}",
    response_model=GradeResponse,
)
def get_grade(
    grade_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GradeLevel:
    return CatalogService.get_grade(
        db,
        grade_id,
    )


@router.delete(
    "/grades/{grade_id}",
    response_model=DeleteCatalogResponse,
)
def delete_grade(
    grade_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> dict:
    return CatalogService.delete_grade(
        db,
        grade_id,
    )


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
    return CatalogService.create_subject(
        db,
        grade_id,
        payload,
    )


@router.get(
    "/grades/{grade_id}/subjects",
    response_model=list[SubjectResponse],
)
def list_subjects(
    grade_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Subject]:
    return CatalogService.list_subjects(
        db,
        grade_id,
    )


@router.get(
    "/subjects/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Subject:
    return CatalogService.get_subject(
        db,
        subject_id,
    )


@router.delete(
    "/subjects/{subject_id}",
    response_model=DeleteCatalogResponse,
)
def delete_subject(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> dict:
    return CatalogService.delete_subject(
        db,
        subject_id,
    )


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
    return CatalogService.create_chapter(
        db,
        subject_id,
        payload,
    )


@router.get(
    "/subjects/{subject_id}/chapters",
    response_model=list[ChapterResponse],
)
def list_chapters(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Chapter]:
    return CatalogService.list_chapters(
        db,
        subject_id,
    )


@router.get(
    "/chapters/{chapter_id}",
    response_model=ChapterResponse,
)
def get_chapter(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Chapter:
    return CatalogService.get_chapter(
        db,
        chapter_id,
    )


@router.delete(
    "/chapters/{chapter_id}",
    response_model=DeleteCatalogResponse,
)
def delete_chapter(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> dict:
    return CatalogService.delete_chapter(
        db,
        chapter_id,
    )