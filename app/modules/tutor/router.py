import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.tutor.model import TutorConversation, TutorMessage
from app.modules.tutor.schema import (
    ChatMessageRequest,
    ConversationCreateRequest,
    ConversationSettingsUpdateRequest,
    StoryGenerateRequest,
    TutorConversationResponse,
    TutorMessageResponse,
    TutorTurnResponse,
)
from app.modules.tutor.service import TutorService


router = APIRouter(
    prefix="/tutor",
    tags=["Tutor"],
)


def response_note(is_source_grounded: bool) -> str:
    if is_source_grounded:
        return (
            "This response was generated using retrieved approved "
            "textbook chunks for the selected topic."
        )

    return (
        "AI-generated explanation. "
        "Textbook-grounded RAG was not used for this response."
    )


@router.post(
    "/conversations",
    response_model=TutorConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorConversation:
    return TutorService.create_conversation(
        db,
        payload,
        current_user,
    )


@router.get(
    "/conversations",
    response_model=list[TutorConversationResponse],
)
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TutorConversation]:
    return TutorService.list_conversations(
        db,
        current_user,
    )


@router.patch(
    "/conversations/{conversation_id}/settings",
    response_model=TutorConversationResponse,
)
def update_conversation_settings(
    conversation_id: uuid.UUID,
    payload: ConversationSettingsUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorConversation:
    return TutorService.update_conversation_settings(
        db,
        conversation_id,
        payload,
        current_user,
    )


@router.post(
    "/conversations/{conversation_id}/story",
    response_model=TutorTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_story(
    conversation_id: uuid.UUID,
    payload: StoryGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorTurnResponse:
    conversation, reply, sources = await TutorService.generate_story(
        db,
        conversation_id,
        payload,
        current_user,
    )

    return TutorTurnResponse(
        conversation=conversation,
        reply=reply,
        sources=sources,
        note=response_note(reply.is_source_grounded),
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=TutorTurnResponse,
)
async def send_chat_message(
    conversation_id: uuid.UUID,
    payload: ChatMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorTurnResponse:
    conversation, reply, sources = await TutorService.send_chat_message(
        db,
        conversation_id,
        payload,
        current_user,
    )

    return TutorTurnResponse(
        conversation=conversation,
        reply=reply,
        sources=sources,
        note=response_note(reply.is_source_grounded),
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[TutorMessageResponse],
)
def list_messages(
    conversation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TutorMessage]:
    return TutorService.list_messages(
        db,
        conversation_id,
        current_user,
    )