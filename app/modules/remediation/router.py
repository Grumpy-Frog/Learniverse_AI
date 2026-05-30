import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.remediation.schema import (
    RemediationDetailResponse,
    RemediationGenerateRequest,
    RemediationListResponse,
    RemediationRecheckRequest,
)
from app.modules.remediation.service import RemediationService


router = APIRouter(
    prefix="/remediation",
    tags=["Remediation"],
)


@router.post(
    "/diagnostic-sessions/{diagnostic_session_id}/generate",
    response_model=RemediationDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_remediation(
    diagnostic_session_id: uuid.UUID,
    payload: RemediationGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return await RemediationService.generate_from_diagnostic(
        db,
        diagnostic_session_id,
        payload,
        current_user,
    )


@router.get(
    "/sessions/{remediation_session_id}",
    response_model=RemediationDetailResponse,
)
def get_remediation_session(
    remediation_session_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return RemediationService.get_session(
        db,
        remediation_session_id,
        current_user,
    )


@router.post(
    "/sessions/{remediation_session_id}/recheck",
    response_model=RemediationDetailResponse,
)
async def submit_recheck(
    remediation_session_id: uuid.UUID,
    payload: RemediationRecheckRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return await RemediationService.submit_recheck(
        db,
        remediation_session_id,
        payload,
        current_user,
    )


@router.get(
    "/me/topics/{topic_id}",
    response_model=RemediationListResponse,
)
def list_my_topic_remediations(
    topic_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return RemediationService.list_my_topic_sessions(
        db,
        topic_id,
        current_user,
    )