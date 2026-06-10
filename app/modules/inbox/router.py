import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.model import User
from app.modules.inbox.model import InboxThread
from app.modules.inbox.schema import (
    InboxMessageCreateRequest,
    InboxThreadCreateRequest,
    InboxThreadDetailResponse,
    InboxThreadListResponse,
    InboxThreadResponse,
    InboxThreadStatusUpdateRequest,
)
from app.modules.inbox.service import InboxService


router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"],
)


@router.post(
    "/threads",
    response_model=InboxThreadDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_thread(
    payload: InboxThreadCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return InboxService.create_thread(
        db,
        payload,
        current_user,
    )


@router.get(
    "/me/threads",
    response_model=InboxThreadListResponse,
)
def list_my_threads(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return InboxService.list_my_threads(
        db,
        current_user,
    )


@router.get(
    "/threads/{thread_id}",
    response_model=InboxThreadDetailResponse,
)
def get_thread(
    thread_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return InboxService.get_thread(
        db,
        thread_id,
        current_user,
    )


@router.post(
    "/threads/{thread_id}/messages",
    response_model=InboxThreadDetailResponse,
)
def add_student_message(
    thread_id: uuid.UUID,
    payload: InboxMessageCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return InboxService.add_student_message(
        db,
        thread_id,
        payload,
        current_user,
    )


@router.patch(
    "/threads/{thread_id}/close",
    response_model=InboxThreadResponse,
)
def close_my_thread(
    thread_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InboxThread:
    return InboxService.close_my_thread(
        db,
        thread_id,
        current_user,
    )


@router.get(
    "/admin/threads",
    response_model=InboxThreadListResponse,
)
def list_admin_threads(
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
    status_filter: str | None = Query(default=None, alias="status"),
) -> dict:
    return InboxService.list_admin_threads(
        db,
        status_filter,
    )


@router.get(
    "/admin/threads/{thread_id}",
    response_model=InboxThreadDetailResponse,
)
def get_admin_thread(
    thread_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> dict:
    return InboxService.get_admin_thread(
        db,
        thread_id,
    )


@router.post(
    "/admin/threads/{thread_id}/messages",
    response_model=InboxThreadDetailResponse,
)
def add_admin_message(
    thread_id: uuid.UUID,
    payload: InboxMessageCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> dict:
    return InboxService.add_admin_message(
        db,
        thread_id,
        payload,
        admin_user,
    )


@router.patch(
    "/admin/threads/{thread_id}",
    response_model=InboxThreadResponse,
)
def update_admin_thread(
    thread_id: uuid.UUID,
    payload: InboxThreadStatusUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> InboxThread:
    return InboxService.update_admin_thread(
        db,
        thread_id,
        payload,
    )