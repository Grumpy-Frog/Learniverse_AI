import re
import unicodedata
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.catalog.repository import CatalogRepository
from app.modules.documents.repository import DocumentRepository
from app.modules.rag.model import DocumentChunk
from app.modules.rag.repository import RagRepository
from app.modules.rag.schema import (
    ChunkBuildRequest,
    ChunkResponse,
    RagSearchRequest,
)


class RagService:
    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text)
        return " ".join(normalized.casefold().split())

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        normalized_query = RagService._normalize_text(query)

        terms = re.split(r"\s+", normalized_query)

        cleaned_terms = [
            term.strip(".,!?;:()[]{}\"'`~।")
            for term in terms
        ]

        return list(
            dict.fromkeys(
                term
                for term in cleaned_terms
                if len(term) >= 2
            )
        )

    @staticmethod
    def build_chunks(
        db: Session,
        document_id: uuid.UUID,
        payload: ChunkBuildRequest,
    ) -> list[DocumentChunk]:
        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if not document.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document must be approved before building RAG chunks",
            )

        topic = CatalogRepository.get_topic_by_id(
            db,
            payload.topic_id,
        )

        if not topic or not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        if topic.chapter_id != document.chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic does not belong to the document chapter",
            )

        if payload.page_end > document.page_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_end exceeds document page count",
            )

        pages = DocumentRepository.list_pages(
            db,
            document_id,
        )

        selected_pages = [
            page
            for page in pages
            if payload.page_start <= page.page_number <= payload.page_end
            and page.has_text
            and page.extracted_text.strip()
        ]

        if not selected_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No extracted text exists in the selected page range",
            )

        words_with_page_numbers: list[tuple[str, int]] = []

        for page in selected_pages:
            words_with_page_numbers.extend(
                (word, page.page_number)
                for word in page.extracted_text.split()
            )

        if not words_with_page_numbers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No words found in the selected page range",
            )

        step_size = payload.chunk_size_words - payload.overlap_words
        generated_chunks: list[DocumentChunk] = []

        start_index = 0
        chunk_index = 1

        while start_index < len(words_with_page_numbers):
            window = words_with_page_numbers[
                start_index : start_index + payload.chunk_size_words
            ]

            if not window:
                break

            content = " ".join(
                word for word, _ in window
            ).strip()

            if content:
                generated_chunks.append(
                    DocumentChunk(
                        document_id=document.id,
                        chapter_id=document.chapter_id,
                        topic_id=payload.topic_id,
                        language=document.language,
                        chunk_index=chunk_index,
                        content=content,
                        page_start=window[0][1],
                        page_end=window[-1][1],
                        word_count=len(window),
                        is_active=True,
                    )
                )
                chunk_index += 1

            start_index += step_size

        if not generated_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create any chunks from selected pages",
            )

        return RagRepository.replace_topic_chunks(
            db,
            document_id,
            payload.topic_id,
            generated_chunks,
        )

    @staticmethod
    def list_chunks(
        db: Session,
        document_id: uuid.UUID,
        topic_id: uuid.UUID,
    ) -> list[DocumentChunk]:
        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        topic = CatalogRepository.get_topic_by_id(
            db,
            topic_id,
        )

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        return RagRepository.list_document_topic_chunks(
            db,
            document_id,
            topic_id,
        )

    @staticmethod
    def search(
        db: Session,
        payload: RagSearchRequest,
    ) -> dict:
        topic = CatalogRepository.get_topic_by_id(
            db,
            payload.topic_id,
        )

        if not topic or not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        candidates = RagRepository.list_search_candidates(
            db,
            payload.topic_id,
            payload.language,
        )

        normalized_query = RagService._normalize_text(
            payload.query
        )
        query_terms = RagService._query_terms(
            payload.query
        )

        if not query_terms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query does not contain usable keywords",
            )

        scored_chunks: list[tuple[int, DocumentChunk]] = []

        for chunk in candidates:
            normalized_content = RagService._normalize_text(
                chunk.content
            )

            score = sum(
                normalized_content.count(term)
                for term in query_terms
            )

            if normalized_query in normalized_content:
                score += 10

            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(
            key=lambda item: (
                -item[0],
                item[1].page_start,
                item[1].chunk_index,
            )
        )

        result_items = []

        for score, chunk in scored_chunks[: payload.limit]:
            chunk_data = ChunkResponse.model_validate(
                chunk
            ).model_dump()
            chunk_data["score"] = score
            result_items.append(chunk_data)

        return {
            "query": payload.query,
            "retrieval_method": "keyword",
            "results": result_items,
        }

    @staticmethod
    def get_story_context_for_tutor(
        db: Session,
        topic_id: uuid.UUID,
        language: str,
        limit: int = 4,
    ) -> list[DocumentChunk]:
        """
        Used when generating the first story lesson.
        There is no student search question yet, so return the first
        approved chunks already assigned to the selected topic/language.
        """
        candidates = RagRepository.list_search_candidates(
            db,
            topic_id,
            language,
        )

        return candidates[:limit]

    @staticmethod
    def retrieve_context_for_tutor(
        db: Session,
        topic_id: uuid.UUID,
        language: str,
        query: str,
        limit: int = 4,
    ) -> list[DocumentChunk]:
        """
        Used for follow-up chat questions.
        Returns relevant chunks in ranked search order.
        """
        search_result = RagService.search(
            db,
            RagSearchRequest(
                topic_id=topic_id,
                language=language,
                query=query,
                limit=limit,
            ),
        )

        result_ids = [
            item["id"]
            for item in search_result["results"]
        ]

        candidates = RagRepository.list_search_candidates(
            db,
            topic_id,
            language,
        )

        chunk_map = {
            chunk.id: chunk
            for chunk in candidates
        }

        return [
            chunk_map[chunk_id]
            for chunk_id in result_ids
            if chunk_id in chunk_map
        ]