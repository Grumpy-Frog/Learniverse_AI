import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.diagnostics.model import DiagnosticQuestion, DiagnosticSession
from app.modules.diagnostics.schema import (
    ChapterStatusResponse,
    DeleteDiagnosticResponse,
    DiagnosticGenerateRequest,
    DiagnosticQuestionResponse,
    DiagnosticResultResponse,
    DiagnosticSessionResponse,
    PublicDiagnosticQuestionResponse,
    SessionSubmitRequest,
    SubjectSummaryResponse,
)
from app.modules.diagnostics.service import DiagnosticsService


router = APIRouter(
    prefix="/diagnostics",
    tags=["Diagnostics"],
)


@router.post(
    "/chapters/{chapter_id}/understanding-check/generate",
    response_model=DiagnosticSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_understanding_check(
    chapter_id: uuid.UUID,
    payload: DiagnosticGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DiagnosticSession:
    return await DiagnosticsService.generate_understanding_check(
        db,
        chapter_id,
        payload,
        current_user,
    )


@router.post(
    "/chapters/{chapter_id}/quiz/generate",
    response_model=DiagnosticSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_chapter_quiz(
    chapter_id: uuid.UUID,
    payload: DiagnosticGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DiagnosticSession:
    return await DiagnosticsService.generate_chapter_quiz(
        db,
        chapter_id,
        payload,
        current_user,
    )


@router.get(
    "/sessions/{session_id}/questions",
    response_model=list[PublicDiagnosticQuestionResponse],
)
def get_questions(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[DiagnosticQuestion]:
    return DiagnosticsService.get_questions(
        db,
        session_id,
        current_user,
    )


@router.get(
    "/sessions/{session_id}/questions/admin-view",
    response_model=list[DiagnosticQuestionResponse],
)
def get_questions_admin_view(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[DiagnosticQuestion]:
    return DiagnosticsService.get_questions(
        db,
        session_id,
        current_user,
    )


@router.post(
    "/sessions/{session_id}/submit",
    response_model=DiagnosticSessionResponse,
)
async def submit_session(
    session_id: uuid.UUID,
    payload: SessionSubmitRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DiagnosticSession:
    return await DiagnosticsService.submit_session(
        db,
        session_id,
        payload,
        current_user,
    )


@router.get(
    "/sessions/{session_id}/result",
    response_model=DiagnosticResultResponse,
)
def get_result(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.get_result(
        db,
        session_id,
        current_user,
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=DeleteDiagnosticResponse,
)
def delete_session(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.delete_session(
        db,
        session_id,
        current_user,
    )


@router.get(
    "/me/chapters/{chapter_id}/status",
    response_model=ChapterStatusResponse,
)
def get_chapter_status(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.get_chapter_status(
        db,
        chapter_id,
        current_user,
    )


@router.get(
    "/me/subjects/{subject_id}/summary",
    response_model=SubjectSummaryResponse,
)
def get_subject_summary(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.get_subject_summary(
        db,
        subject_id,
        current_user,
    )