import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.model import User
from app.modules.rag.model import DocumentChunk
from app.modules.rag.schema import (
    ChunkBuildRequest,
    ChunkResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from app.modules.rag.service import RagService


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


@router.post(
    "/documents/{document_id}/chunks/build",
    response_model=list[ChunkResponse],
    status_code=status.HTTP_201_CREATED,
)
def build_document_chunks(
    document_id: uuid.UUID,
    payload: ChunkBuildRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> list[DocumentChunk]:
    return RagService.build_chunks(
        db,
        document_id,
        payload,
    )


@router.get(
    "/documents/{document_id}/topics/{topic_id}/chunks",
    response_model=list[ChunkResponse],
)
def list_document_topic_chunks(
    document_id: uuid.UUID,
    topic_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> list[DocumentChunk]:
    return RagService.list_chunks(
        db,
        document_id,
        topic_id,
    )


@router.post(
    "/search",
    response_model=RagSearchResponse,
)
def search_topic_chunks(
    payload: RagSearchRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return RagService.search(
        db,
        payload,
    )