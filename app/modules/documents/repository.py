import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.documents.model import Document, DocumentPage


class DocumentRepository:
    @staticmethod
    def get_by_id(
        db: Session,
        document_id: uuid.UUID,
    ) -> Document | None:
        return db.get(Document, document_id)

    @staticmethod
    def get_textbook_by_chapter_and_language(
        db: Session,
        chapter_id: uuid.UUID,
        language: str,
    ) -> Document | None:
        return db.scalar(
            select(Document).where(
                Document.chapter_id == chapter_id,
                Document.language == language,
                Document.source_type == "textbook",
            )
        )

    @staticmethod
    def create_with_pages(
        db: Session,
        document: Document,
        pages: list[dict],
    ) -> Document:
        db.add(document)
        db.flush()

        for page_data in pages:
            page = DocumentPage(
                document_id=document.id,
                page_number=page_data["page_number"],
                extracted_text=page_data["extracted_text"],
                has_text=page_data["has_text"],
            )
            db.add(page)

        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def list_by_chapter(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> list[Document]:
        return list(
            db.scalars(
                select(Document)
                .where(Document.chapter_id == chapter_id)
                .order_by(Document.language.asc())
            ).all()
        )

    @staticmethod
    def list_pages(
        db: Session,
        document_id: uuid.UUID,
    ) -> list[DocumentPage]:
        return list(
            db.scalars(
                select(DocumentPage)
                .where(DocumentPage.document_id == document_id)
                .order_by(DocumentPage.page_number.asc())
            ).all()
        )

    @staticmethod
    def approve(
        db: Session,
        document: Document,
    ) -> Document:
        document.processing_status = "approved"
        document.is_approved = True

        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def delete(
        db: Session,
        document: Document,
    ) -> None:
        db.delete(document)
        db.commit()