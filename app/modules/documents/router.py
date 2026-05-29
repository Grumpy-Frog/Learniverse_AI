import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.model import User
from app.modules.documents.model import Document, DocumentPage
from app.modules.documents.schema import (
    DocumentPageResponse,
    DocumentResponse,
)
from app.modules.documents.service import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/chapters/{chapter_id}/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_textbook_pdf(
    chapter_id: uuid.UUID,
    title: Annotated[str, Form(min_length=2, max_length=255)],
    language: Annotated[Literal["en", "bn"], Form()],
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Document:
    return DocumentService.upload_textbook_pdf(
        db=db,
        chapter_id=chapter_id,
        title=title,
        language=language,
        file=file,
        admin_user=admin_user,
    )


@router.get(
    "/chapters/{chapter_id}",
    response_model=list[DocumentResponse],
)
def list_chapter_documents(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> list[Document]:
    return DocumentService.list_chapter_documents(
        db,
        chapter_id,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Document:
    return DocumentService.get_document(
        db,
        document_id,
    )


@router.get(
    "/{document_id}/pages",
    response_model=list[DocumentPageResponse],
)
def list_document_pages(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> list[DocumentPage]:
    return DocumentService.list_document_pages(
        db,
        document_id,
    )


@router.patch(
    "/{document_id}/approve",
    response_model=DocumentResponse,
)
def approve_document(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Document:
    return DocumentService.approve_document(
        db,
        document_id,
    )