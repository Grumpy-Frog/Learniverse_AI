import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.rag.model import DocumentChunk


class RagRepository:
    @staticmethod
    def replace_document_chapter_chunks(
        db: Session,
        document_id: uuid.UUID,
        chapter_id: uuid.UUID,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chapter_id == chapter_id,
            )
        )

        db.add_all(chunks)
        db.commit()

        return list(
            db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.chapter_id == chapter_id,
                    DocumentChunk.is_active.is_(True),
                )
                .order_by(DocumentChunk.chunk_index.asc())
            ).all()
        )

    @staticmethod
    def get_chunk_by_id(
        db: Session,
        chunk_id: uuid.UUID,
    ) -> DocumentChunk | None:
        return db.get(DocumentChunk, chunk_id)

    @staticmethod
    def list_document_chapter_chunks(
        db: Session,
        document_id: uuid.UUID,
        chapter_id: uuid.UUID,
    ) -> list[DocumentChunk]:
        return list(
            db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.chapter_id == chapter_id,
                    DocumentChunk.is_active.is_(True),
                )
                .order_by(DocumentChunk.chunk_index.asc())
            ).all()
        )

    @staticmethod
    def list_chapter_chunks(
        db: Session,
        chapter_id: uuid.UUID,
        language: str | None = None,
    ) -> list[DocumentChunk]:
        query = (
            select(DocumentChunk)
            .where(
                DocumentChunk.chapter_id == chapter_id,
                DocumentChunk.is_active.is_(True),
            )
            .order_by(
                DocumentChunk.page_start.asc(),
                DocumentChunk.chunk_index.asc(),
            )
        )

        if language:
            query = query.where(DocumentChunk.language == language)

        return list(db.scalars(query).all())

    @staticmethod
    def list_search_candidates(
        db: Session,
        chapter_id: uuid.UUID,
        language: str,
    ) -> list[DocumentChunk]:
        return list(
            db.scalars(
                select(DocumentChunk)
                .where(
                    DocumentChunk.chapter_id == chapter_id,
                    DocumentChunk.language == language,
                    DocumentChunk.is_active.is_(True),
                )
                .order_by(
                    DocumentChunk.page_start.asc(),
                    DocumentChunk.chunk_index.asc(),
                )
            ).all()
        )

    @staticmethod
    def delete_chunk(
        db: Session,
        chunk: DocumentChunk,
    ) -> None:
        db.delete(chunk)
        db.commit()

    @staticmethod
    def delete_chapter_chunks(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> int:
        chunks = RagRepository.list_chapter_chunks(
            db,
            chapter_id,
        )

        deleted_count = len(chunks)

        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.chapter_id == chapter_id,
            )
        )
        db.commit()

        return deleted_count

    @staticmethod
    def delete_document_chapter_chunks(
        db: Session,
        document_id: uuid.UUID,
        chapter_id: uuid.UUID,
    ) -> int:
        chunks = RagRepository.list_document_chapter_chunks(
            db,
            document_id,
            chapter_id,
        )

        deleted_count = len(chunks)

        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chapter_id == chapter_id,
            )
        )
        db.commit()

        return deleted_count