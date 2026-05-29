import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.diagnostics.model import DiagnosticQuestion
from app.modules.diagnostics.repository import DiagnosticsRepository
from app.modules.diagnostics.schema import (
    DiagnosticGenerateRequest,
    DiagnosticResultResponse,
    GeneratedAssessmentResponse,
    SafeQuestionResponse,
    SessionSubmitRequest,
    SubjectSummaryResponse,
    TopicStatusResponse,
)
from app.modules.diagnostics.service import DiagnosticsService


router = APIRouter(
    prefix="/diagnostics",
    tags=["Diagnostics"],
)


def build_generated_response(
    db: Session,
    session,
) -> GeneratedAssessmentResponse:
    questions = DiagnosticsRepository.list_questions(
        db,
        session.id,
    )

    return GeneratedAssessmentResponse(
        session=session,
        questions=questions,
    )


@router.post(
    "/topics/{topic_id}/understanding-check/generate",
    response_model=GeneratedAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_understanding_check(
    topic_id: uuid.UUID,
    payload: DiagnosticGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GeneratedAssessmentResponse:
    session = await DiagnosticsService.generate_understanding_check(
        db,
        topic_id,
        payload,
        current_user,
    )

    return build_generated_response(
        db,
        session,
    )


@router.post(
    "/topics/{topic_id}/quiz/generate",
    response_model=GeneratedAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_diagnostic_quiz(
    topic_id: uuid.UUID,
    payload: DiagnosticGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GeneratedAssessmentResponse:
    session = await DiagnosticsService.generate_diagnostic_quiz(
        db,
        topic_id,
        payload,
        current_user,
    )

    return build_generated_response(
        db,
        session,
    )


@router.get(
    "/sessions/{session_id}/questions",
    response_model=list[SafeQuestionResponse],
)
def get_session_questions(
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
    response_model=DiagnosticResultResponse,
)
async def submit_session(
    session_id: uuid.UUID,
    payload: SessionSubmitRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    await DiagnosticsService.submit_session(
        db,
        session_id,
        payload,
        current_user,
    )

    return DiagnosticsService.get_result(
        db,
        session_id,
        current_user,
    )


@router.get(
    "/sessions/{session_id}/result",
    response_model=DiagnosticResultResponse,
)
def get_session_result(
    session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.get_result(
        db,
        session_id,
        current_user,
    )


@router.get(
    "/me/topics/{topic_id}/status",
    response_model=TopicStatusResponse,
)
def get_my_topic_status(
    topic_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.get_topic_status(
        db,
        topic_id,
        current_user,
    )


@router.get(
    "/me/subjects/{subject_id}/summary",
    response_model=SubjectSummaryResponse,
)
def get_my_subject_summary(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return DiagnosticsService.get_subject_summary(
        db,
        subject_id,
        current_user,
    )