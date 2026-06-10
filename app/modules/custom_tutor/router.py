import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.custom_tutor.model import CustomTutorChat
from app.modules.custom_tutor.schema import (
    CustomTutorChatCreateRequest,
    CustomTutorChatDetailResponse,
    CustomTutorChatListResponse,
    CustomTutorChatRenameRequest,
    CustomTutorChatResponse,
    CustomTutorMessageCreateRequest,
    CustomTutorTurnResponse,
    DeleteCustomTutorChatResponse,
)
from app.modules.custom_tutor.service import CustomTutorService


router = APIRouter(
    prefix="/custom-tutor",
    tags=["Custom Tutor"],
)


@router.post(
    "/chats",
    response_model=CustomTutorChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat(
    payload: CustomTutorChatCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CustomTutorChat:
    return CustomTutorService.create_chat(
        db,
        payload,
        current_user,
    )


@router.get(
    "/chats",
    response_model=CustomTutorChatListResponse,
)
def list_chats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return CustomTutorService.list_chats(
        db,
        current_user,
    )


@router.get(
    "/chats/{chat_id}",
    response_model=CustomTutorChatDetailResponse,
)
def get_chat(
    chat_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return CustomTutorService.get_chat_detail(
        db,
        chat_id,
        current_user,
    )


@router.patch(
    "/chats/{chat_id}/rename",
    response_model=CustomTutorChatResponse,
)
def rename_chat(
    chat_id: uuid.UUID,
    payload: CustomTutorChatRenameRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CustomTutorChat:
    return CustomTutorService.rename_chat(
        db,
        chat_id,
        payload,
        current_user,
    )


@router.delete(
    "/chats/{chat_id}",
    response_model=DeleteCustomTutorChatResponse,
)
def delete_chat(
    chat_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return CustomTutorService.delete_chat(
        db,
        chat_id,
        current_user,
    )


@router.post(
    "/chats/{chat_id}/messages",
    response_model=CustomTutorTurnResponse,
)
async def send_message(
    chat_id: uuid.UUID,
    payload: CustomTutorMessageCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return await CustomTutorService.send_message(
        db,
        chat_id,
        payload,
        current_user,
    )