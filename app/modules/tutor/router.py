import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.tutor.model import TutorConversation, TutorGroup, TutorMessage
from app.modules.tutor.schema import (
    ChatMessageRequest,
    ConversationCreateRequest,
    DeleteTutorResponse,
    StoryGenerateRequest,
    TutorConversationResponse,
    TutorGroupCreateRequest,
    TutorGroupResponse,
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
            "textbook chunks for the selected chapter."
        )

    return (
        "AI-generated explanation within the selected chapter scope. "
        "No approved textbook chunks were used for this response."
    )


@router.post(
    "/groups",
    response_model=TutorGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    payload: TutorGroupCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TutorGroup:
    return TutorService.create_group(
        db,
        payload,
        current_user,
    )


@router.get(
    "/groups",
    response_model=list[TutorGroupResponse],
)
def list_groups(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TutorGroup]:
    return TutorService.list_groups(
        db,
        current_user,
    )


@router.delete(
    "/groups/{group_id}",
    response_model=DeleteTutorResponse,
)
def delete_group(
    group_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return TutorService.delete_group(
        db,
        group_id,
        current_user,
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


@router.get(
    "/subjects/{subject_id}/conversations",
    response_model=list[TutorConversationResponse],
)
def list_subject_conversations(
    subject_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TutorConversation]:
    return TutorService.list_subject_conversations(
        db,
        subject_id,
        current_user,
    )


@router.get(
    "/chapters/{chapter_id}/conversations",
    response_model=list[TutorConversationResponse],
)
def list_chapter_conversations(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TutorConversation]:
    return TutorService.list_chapter_conversations(
        db,
        chapter_id,
        current_user,
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=DeleteTutorResponse,
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return TutorService.delete_conversation(
        db,
        conversation_id,
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