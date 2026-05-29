import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.rag.model import DocumentChunk


class RagRepository:
    @staticmethod
    def replace_topic_chunks(
        db: Session,
        document_id: uuid.UUID,
        topic_id: uuid.UUID,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.topic_id == topic_id,
            )
        )

        db.add_all(chunks)
        db.commit()

        return list(
            db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.topic_id == topic_id,
                )
                .order_by(DocumentChunk.chunk_index.asc())
            ).all()
        )

    @staticmethod
    def list_document_topic_chunks(
        db: Session,
        document_id: uuid.UUID,
        topic_id: uuid.UUID,
    ) -> list[DocumentChunk]:
        return list(
            db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.topic_id == topic_id,
                    DocumentChunk.is_active.is_(True),
                )
                .order_by(DocumentChunk.chunk_index.asc())
            ).all()
        )

    @staticmethod
    def list_search_candidates(
        db: Session,
        topic_id: uuid.UUID,
        language: str,
    ) -> list[DocumentChunk]:
        return list(
            db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.topic_id == topic_id,
                    DocumentChunk.language == language,
                    DocumentChunk.is_active.is_(True),
                )
                .order_by(DocumentChunk.chunk_index.asc())
            ).all()
        )