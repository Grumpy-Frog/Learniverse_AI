import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.dashboard.schema import (
    ChapterProgressResponse,
    DashboardOverviewResponse,
    GradeProgressResponse,
    SubjectProgressResponse,
)
from app.modules.dashboard.service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/me/overview",
    response_model=DashboardOverviewResponse,
)
def get_my_dashboard_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DashboardService.get_overview(
        db,
        current_user,
    )


@router.get(
    "/me/grades/{grade_id}",
    response_model=GradeProgressResponse,
)
def get_my_grade_progress(
    grade_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DashboardService.get_grade_progress(
        db,
        grade_id,
        current_user,
    )


@router.get(
    "/me/subjects/{subject_id}",
    response_model=SubjectProgressResponse,
)
def get_my_subject_progress(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DashboardService.get_subject_progress(
        db,
        subject_id,
        current_user,
    )


@router.get(
    "/me/chapters/{chapter_id}",
    response_model=ChapterProgressResponse,
)
def get_my_chapter_progress(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DashboardService.get_chapter_progress(
        db,
        chapter_id,
        current_user,
    )