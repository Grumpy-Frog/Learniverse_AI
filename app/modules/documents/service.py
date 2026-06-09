import hashlib
import uuid
from pathlib import Path

import pymupdf
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.catalog.repository import CatalogRepository
from app.modules.documents.model import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.rag.repository import RagRepository


class DocumentService:
    @staticmethod
    def upload_textbook_pdf(
        db: Session,
        chapter_id: uuid.UUID,
        title: str,
        language: str,
        file: UploadFile,
        admin_user: User,
    ) -> Document:
        chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        if language not in {"en", "bn"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language must be 'en' or 'bn'",
            )

        existing_document = DocumentRepository.get_textbook_by_chapter_and_language(
            db,
            chapter_id,
            language,
        )

        if existing_document:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A textbook PDF already exists for this chapter and language. "
                    "Delete the existing document before uploading a new one."
                ),
            )

        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed",
            )

        accepted_content_types = {
            "application/pdf",
            "application/octet-stream",
        }

        if file.content_type not in accepted_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be a PDF",
            )

        target_directory = (
            Path(settings.storage_dir)
            / str(chapter_id)
            / language
        )
        target_directory.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid.uuid4()}.pdf"
        stored_path = target_directory / stored_filename

        sha256_hash = hashlib.sha256()
        file_size = 0

        try:
            with stored_path.open("wb") as saved_file:
                while True:
                    chunk = file.file.read(1024 * 1024)

                    if not chunk:
                        break

                    saved_file.write(chunk)
                    sha256_hash.update(chunk)
                    file_size += len(chunk)

            extracted_pages: list[dict] = []
            text_page_count = 0

            with pymupdf.open(str(stored_path)) as pdf:
                page_count = pdf.page_count

                for page_index, page in enumerate(pdf, start=1):
                    extracted_text = page.get_text("text").strip()
                    has_text = bool(extracted_text)

                    if has_text:
                        text_page_count += 1

                    extracted_pages.append(
                        {
                            "page_number": page_index,
                            "extracted_text": extracted_text,
                            "has_text": has_text,
                        }
                    )

            if page_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The PDF has no pages",
                )

            processing_status = (
                "processed"
                if text_page_count > 0
                else "needs_ocr"
            )

            document = Document(
                chapter_id=chapter_id,
                title=title.strip(),
                language=language,
                source_type="textbook",
                original_filename=file.filename,
                storage_path=stored_path.as_posix(),
                file_hash=sha256_hash.hexdigest(),
                file_size_bytes=file_size,
                page_count=page_count,
                processing_status=processing_status,
                is_approved=False,
                uploaded_by=admin_user.id,
            )

            return DocumentRepository.create_with_pages(
                db,
                document,
                extracted_pages,
            )

        except HTTPException:
            stored_path.unlink(missing_ok=True)
            raise

        except Exception as exc:
            stored_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process the uploaded PDF",
            ) from exc

        finally:
            file.file.close()

    @staticmethod
    def list_chapter_documents(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> list[Document]:
        chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        return DocumentRepository.list_by_chapter(
            db,
            chapter_id,
        )

    @staticmethod
    def get_document(
        db: Session,
        document_id: uuid.UUID,
    ) -> Document:
        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        return document

    @staticmethod
    def list_document_pages(
        db: Session,
        document_id: uuid.UUID,
    ):
        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        return DocumentRepository.list_pages(
            db,
            document_id,
        )

    @staticmethod
    def approve_document(
        db: Session,
        document_id: uuid.UUID,
    ) -> Document:
        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if document.processing_status == "needs_ocr":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This PDF has no extracted text and cannot be approved until OCR is implemented",
            )

        return DocumentRepository.approve(
            db,
            document,
        )

    @staticmethod
    def delete_document(
        db: Session,
        document_id: uuid.UUID,
    ) -> dict:
        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        deleted_id = document.id
        storage_path = document.storage_path
        chapter_id = document.chapter_id

        # Delete chunks created from this document first.
        # This avoids stale RAG chunks after replacing a chapter PDF.
        RagRepository.delete_document_chapter_chunks(
            db,
            document_id=deleted_id,
            chapter_id=chapter_id,
        )

        DocumentRepository.delete(
            db,
            document,
        )

        # Remove local PDF file if it still exists.
        # Do not fail the API only because the file is already missing.
        if storage_path:
            try:
                Path(storage_path).unlink(missing_ok=True)
            except OSError:
                pass

        return {
            "deleted_id": deleted_id,
            "message": "Document deleted successfully",
        }