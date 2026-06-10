import hashlib
import uuid
from pathlib import Path

import pymupdf
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.catalog.repository import CatalogRepository
from app.modules.custom_tutor.repository import CustomTutorRepository
from app.modules.rag.service import RagService
from app.modules.study_tools.model import AiNote, Flashcard, FlashcardDeck, StudyDocument

from app.modules.study_tools.prompts import (
    flashcard_generation_messages,
    formula_extraction_messages,
    glossary_messages,
    important_questions_messages,
    key_points_messages,
    mind_map_generation_messages,
    mnemonic_messages,
    note_generation_messages,
    pdf_summary_messages,
    revision_checklist_messages,
    study_plan_messages,
    worksheet_generation_messages,
)

from app.modules.study_tools.repository import StudyToolsRepository

from app.modules.study_tools.schema import (
    AiNoteGenerateRequest,
    AiNoteUpdateRequest,
    FlashcardDeckUpdateRequest,
    FlashcardGenerateRequest,
    PdfSummarizeRequest,
    StudyArtifactGenerateRequest,
    StudyArtifactUpdateRequest,
    
)

from app.modules.tutor.deepseek_provider import DeepSeekProvider

from app.modules.study_tools.model import (
    AiNote,
    Flashcard,
    FlashcardDeck,
    StudyArtifact,
    StudyDocument,
)

import pymupdf
from fastapi import UploadFile



MAX_SOURCE_CHARS = 18000


class StudyToolsService:
    @staticmethod
    def _trim_text(text: str) -> str:
        clean = " ".join(text.split())
        return clean[:MAX_SOURCE_CHARS]

    @staticmethod
    def _validate_context(db: Session, grade_id, subject_id, chapter_id):
        grade = None
        subject = None
        chapter = None

        if chapter_id:
            chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)
            if not chapter or not chapter.is_active:
                raise HTTPException(status_code=404, detail="Chapter not found")

            subject = chapter.subject
            grade = subject.grade_level

            if subject_id and subject_id != subject.id:
                raise HTTPException(status_code=400, detail="Chapter does not belong to selected subject")

            if grade_id and grade_id != grade.id:
                raise HTTPException(status_code=400, detail="Chapter does not belong to selected grade")

            return grade, subject, chapter

        if subject_id:
            subject = CatalogRepository.get_subject_by_id(db, subject_id)
            if not subject or not subject.is_active:
                raise HTTPException(status_code=404, detail="Subject not found")

            grade = subject.grade_level

            if grade_id and grade_id != grade.id:
                raise HTTPException(status_code=400, detail="Subject does not belong to selected grade")

            return grade, subject, None

        if grade_id:
            grade = CatalogRepository.get_grade_by_id(db, grade_id)
            if not grade or not grade.is_active:
                raise HTTPException(status_code=404, detail="Grade not found")

        return grade, None, None

    @staticmethod
    def _source_context_ids(grade, subject, chapter):
        return {
            "grade_id": grade.id if grade else None,
            "subject_id": subject.id if subject else None,
            "chapter_id": chapter.id if chapter else None,
        }

    @staticmethod
    def _get_source_text(
        db: Session,
        current_user: User,
        source_type: str,
        source_id: uuid.UUID | None,
        raw_text: str | None,
        language: str,
    ) -> tuple[str, dict]:
        if source_type == "raw_text":
            if not raw_text or not raw_text.strip():
                raise HTTPException(status_code=400, detail="raw_text is required")
            return raw_text, {"grade_id": None, "subject_id": None, "chapter_id": None}

        if source_type == "pdf":
            if not source_id:
                raise HTTPException(status_code=400, detail="source_id is required for PDF source")

            document = StudyToolsRepository.get_document_for_user(db, source_id, current_user.id)
            if not document:
                raise HTTPException(status_code=404, detail="Study PDF not found")

            source_text = document.summary or document.extracted_text
            if not source_text:
                raise HTTPException(status_code=400, detail="PDF has no extracted text")

            return source_text, {
                "grade_id": document.grade_id,
                "subject_id": document.subject_id,
                "chapter_id": document.chapter_id,
            }

        if source_type == "note":
            if not source_id:
                raise HTTPException(status_code=400, detail="source_id is required for note source")

            note = StudyToolsRepository.get_note_for_user(db, source_id, current_user.id)
            if not note:
                raise HTTPException(status_code=404, detail="AI note not found")

            return note.content, {
                "grade_id": note.grade_id,
                "subject_id": note.subject_id,
                "chapter_id": note.chapter_id,
            }

        if source_type == "custom_tutor_chat":
            if not source_id:
                raise HTTPException(status_code=400, detail="source_id is required for custom tutor chat source")

            chat = CustomTutorRepository.get_chat_for_user(db, source_id, current_user.id)
            if not chat:
                raise HTTPException(status_code=404, detail="Custom tutor chat not found")

            messages = CustomTutorRepository.list_messages(db, chat.id)
            text = "\n".join(f"{message.role}: {message.content}" for message in messages)

            return text, {
                "grade_id": chat.grade_id,
                "subject_id": chat.subject_id,
                "chapter_id": chat.chapter_id,
            }

        if source_type == "chapter":
            if not source_id:
                raise HTTPException(status_code=400, detail="source_id must be chapter_id for chapter source")

            chapter = CatalogRepository.get_chapter_by_id(db, source_id)
            if not chapter or not chapter.is_active:
                raise HTTPException(status_code=404, detail="Chapter not found")

            chunks = RagService.get_story_context_for_tutor(
                db,
                chapter_id=chapter.id,
                language=language,
                limit=10,
            )

            source_text = "\n\n".join(chunk.content for chunk in chunks)

            if not source_text:
                source_text = f"Chapter: {chapter.title}"

            return source_text, {
                "grade_id": chapter.subject.grade_level.id,
                "subject_id": chapter.subject.id,
                "chapter_id": chapter.id,
            }

        raise HTTPException(status_code=400, detail="Invalid source_type")

    @staticmethod
    def upload_pdf(
        db: Session,
        title: str,
        language: str,
        grade_id: uuid.UUID | None,
        subject_id: uuid.UUID | None,
        chapter_id: uuid.UUID | None,
        file: UploadFile,
        current_user: User,
    ) -> StudyDocument:
        if language not in {"en", "bn"}:
            raise HTTPException(status_code=400, detail="Language must be 'en' or 'bn'")

        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        grade, subject, chapter = StudyToolsService._validate_context(
            db,
            grade_id,
            subject_id,
            chapter_id,
        )

        target_directory = Path(settings.storage_dir) / "study_tools" / str(current_user.id)
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

            extracted_pages = []
            text_page_count = 0

            with pymupdf.open(str(stored_path)) as pdf:
                page_count = pdf.page_count

                for page in pdf:
                    text = page.get_text("text").strip()
                    if text:
                        text_page_count += 1
                        extracted_pages.append(text)

            if page_count == 0:
                raise HTTPException(status_code=400, detail="The PDF has no pages")

            extracted_text = "\n\n".join(extracted_pages).strip()
            processing_status = "processed" if text_page_count > 0 else "needs_ocr"

            document = StudyDocument(
                user_id=current_user.id,
                grade_id=grade.id if grade else None,
                subject_id=subject.id if subject else None,
                chapter_id=chapter.id if chapter else None,
                title=title.strip(),
                language=language,
                original_filename=file.filename,
                storage_path=stored_path.as_posix(),
                file_hash=sha256_hash.hexdigest(),
                file_size_bytes=file_size,
                page_count=page_count,
                extracted_text=extracted_text or None,
                processing_status=processing_status,
            )

            return StudyToolsRepository.create_document(db, document)

        except HTTPException:
            stored_path.unlink(missing_ok=True)
            raise

        except Exception as exc:
            stored_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Could not process uploaded PDF") from exc

        finally:
            file.file.close()

    @staticmethod
    async def summarize_pdf(
        db: Session,
        document_id: uuid.UUID,
        payload: PdfSummarizeRequest,
        current_user: User,
    ) -> StudyDocument:
        document = StudyToolsRepository.get_document_for_user(db, document_id, current_user.id)

        if not document:
            raise HTTPException(status_code=404, detail="Study PDF not found")

        if not document.extracted_text:
            raise HTTPException(status_code=400, detail="PDF has no extracted text")

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=pdf_summary_messages(
                source_text=StudyToolsService._trim_text(document.extracted_text),
                language=payload.language,
                instruction=payload.instruction,
            ),
            max_tokens=1400,
            temperature=0.2,
        )

        document.summary = str(completion.data.get("summary", "")).strip()

        if not document.summary:
            raise HTTPException(status_code=502, detail="AI did not return a summary")

        return StudyToolsRepository.update_document(db, document)

    @staticmethod
    async def generate_note(
        db: Session,
        payload: AiNoteGenerateRequest,
        current_user: User,
    ) -> AiNote:
        source_text, context_ids = StudyToolsService._get_source_text(
            db,
            current_user,
            payload.source_type,
            payload.source_id,
            payload.raw_text,
            payload.language,
        )

        if payload.grade_id or payload.subject_id or payload.chapter_id:
            grade, subject, chapter = StudyToolsService._validate_context(
                db,
                payload.grade_id,
                payload.subject_id,
                payload.chapter_id,
            )
            context_ids = StudyToolsService._source_context_ids(grade, subject, chapter)

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=note_generation_messages(
                source_text=StudyToolsService._trim_text(source_text),
                language=payload.language,
                ai_help_mode=payload.ai_help_mode,
                instruction=payload.instruction,
            ),
            max_tokens=1600,
            temperature=0.3,
        )

        title = payload.title or str(completion.data.get("title", "AI Notes")).strip()
        content = str(completion.data.get("content", "")).strip()

        if not content:
            raise HTTPException(status_code=502, detail="AI did not return note content")

        note = AiNote(
            user_id=current_user.id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            title=title[:200],
            content=content,
            ai_help_mode=payload.ai_help_mode,
            language=payload.language,
            **context_ids,
        )

        return StudyToolsRepository.create_note(db, note)

    @staticmethod
    async def generate_flashcards(
        db: Session,
        payload: FlashcardGenerateRequest,
        current_user: User,
    ) -> dict:
        source_text, context_ids = StudyToolsService._get_source_text(
            db,
            current_user,
            payload.source_type,
            payload.source_id,
            payload.raw_text,
            payload.language,
        )

        if payload.grade_id or payload.subject_id or payload.chapter_id:
            grade, subject, chapter = StudyToolsService._validate_context(
                db,
                payload.grade_id,
                payload.subject_id,
                payload.chapter_id,
            )
            context_ids = StudyToolsService._source_context_ids(grade, subject, chapter)

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=flashcard_generation_messages(
                source_text=StudyToolsService._trim_text(source_text),
                language=payload.language,
                card_count=payload.card_count,
            ),
            max_tokens=1800,
            temperature=0.2,
        )

        raw_cards = completion.data.get("cards", [])

        if not isinstance(raw_cards, list) or not raw_cards:
            raise HTTPException(status_code=502, detail="AI did not return flashcards")

        deck_title = payload.title or str(completion.data.get("deck_title", "AI Flashcards")).strip()

        deck = FlashcardDeck(
            user_id=current_user.id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            title=deck_title[:200],
            language=payload.language,
            **context_ids,
        )

        cards = [
            Flashcard(
                deck_id=deck.id,
                front=str(card.get("front", "")).strip(),
                back=str(card.get("back", "")).strip(),
                hint=str(card.get("hint", "")).strip() or None,
                display_order=index,
            )
            for index, card in enumerate(raw_cards, start=1)
            if str(card.get("front", "")).strip() and str(card.get("back", "")).strip()
        ]

        if not cards:
            raise HTTPException(status_code=502, detail="AI returned invalid flashcards")

        created_deck = StudyToolsRepository.create_deck_with_cards(db, deck, cards)

        return {
            "deck": created_deck,
            "cards": StudyToolsRepository.list_cards(db, created_deck.id),
        }

    @staticmethod
    def list_documents(db: Session, current_user: User) -> list[StudyDocument]:
        return StudyToolsRepository.list_documents(db, current_user.id)

    @staticmethod
    def get_document(db: Session, document_id: uuid.UUID, current_user: User) -> StudyDocument:
        document = StudyToolsRepository.get_document_for_user(db, document_id, current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Study PDF not found")
        return document

    @staticmethod
    def delete_document(db: Session, document_id: uuid.UUID, current_user: User) -> dict:
        document = StudyToolsService.get_document(db, document_id, current_user)
        document.is_deleted = True
        StudyToolsRepository.update_document(db, document)
        return {"deleted_id": document_id, "message": "Study PDF deleted successfully"}

    @staticmethod
    def list_notes(db: Session, current_user: User) -> list[AiNote]:
        return StudyToolsRepository.list_notes(db, current_user.id)

    @staticmethod
    def get_note(db: Session, note_id: uuid.UUID, current_user: User) -> AiNote:
        note = StudyToolsRepository.get_note_for_user(db, note_id, current_user.id)
        if not note:
            raise HTTPException(status_code=404, detail="AI note not found")
        return note

    @staticmethod
    def update_note(db: Session, note_id: uuid.UUID, payload: AiNoteUpdateRequest, current_user: User) -> AiNote:
        note = StudyToolsService.get_note(db, note_id, current_user)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)

        return StudyToolsRepository.update_note(db, note)

    @staticmethod
    def delete_note(db: Session, note_id: uuid.UUID, current_user: User) -> dict:
        note = StudyToolsService.get_note(db, note_id, current_user)
        note.is_deleted = True
        StudyToolsRepository.update_note(db, note)
        return {"deleted_id": note_id, "message": "AI note deleted successfully"}

    @staticmethod
    def list_decks(db: Session, current_user: User) -> list[FlashcardDeck]:
        return StudyToolsRepository.list_decks(db, current_user.id)

    @staticmethod
    def get_deck_detail(db: Session, deck_id: uuid.UUID, current_user: User) -> dict:
        deck = StudyToolsRepository.get_deck_for_user(db, deck_id, current_user.id)
        if not deck:
            raise HTTPException(status_code=404, detail="Flashcard deck not found")

        return {
            "deck": deck,
            "cards": StudyToolsRepository.list_cards(db, deck.id),
        }

    @staticmethod
    def update_deck(db: Session, deck_id: uuid.UUID, payload: FlashcardDeckUpdateRequest, current_user: User) -> FlashcardDeck:
        deck = StudyToolsRepository.get_deck_for_user(db, deck_id, current_user.id)
        if not deck:
            raise HTTPException(status_code=404, detail="Flashcard deck not found")

        deck.title = payload.title

        return StudyToolsRepository.update_deck(db, deck)

    @staticmethod
    def delete_deck(db: Session, deck_id: uuid.UUID, current_user: User) -> dict:
        deck = StudyToolsRepository.get_deck_for_user(db, deck_id, current_user.id)
        if not deck:
            raise HTTPException(status_code=404, detail="Flashcard deck not found")

        deck.is_deleted = True
        StudyToolsRepository.update_deck(db, deck)

        return {"deleted_id": deck_id, "message": "Flashcard deck deleted successfully"}
    
    @staticmethod
    async def _generate_artifact(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
        artifact_type: str,
    ) -> StudyArtifact:
        source_text, context_ids = StudyToolsService._get_source_text(
            db,
            current_user,
            payload.source_type,
            payload.source_id,
            payload.raw_text,
            payload.language,
        )

        if payload.grade_id or payload.subject_id or payload.chapter_id:
            grade, subject, chapter = StudyToolsService._validate_context(
                db,
                payload.grade_id,
                payload.subject_id,
                payload.chapter_id,
            )
            context_ids = StudyToolsService._source_context_ids(
                grade,
                subject,
                chapter,
            )

        trimmed_text = StudyToolsService._trim_text(source_text)

        if artifact_type == "mind_map":
            messages = mind_map_generation_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                instruction=payload.instruction,
            )
            max_tokens = 1600

        elif artifact_type == "worksheet":
            messages = worksheet_generation_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                difficulty=payload.difficulty,
                instruction=payload.instruction,
            )
            max_tokens = 2200

        elif artifact_type == "formula_sheet":
            messages = formula_extraction_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                instruction=payload.instruction,
            )
            max_tokens = 1800

        elif artifact_type == "important_questions":
            messages = important_questions_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                difficulty=payload.difficulty,
                instruction=payload.instruction,
            )
            max_tokens = 2200
        
        elif artifact_type == "key_points":
            messages = key_points_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                instruction=payload.instruction,
            )
            max_tokens = 1400

        elif artifact_type == "glossary":
            messages = glossary_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                instruction=payload.instruction,
            )
            max_tokens = 1600

        elif artifact_type == "revision_checklist":
            messages = revision_checklist_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                instruction=payload.instruction,
            )
            max_tokens = 1400

        elif artifact_type == "study_plan":
            messages = study_plan_messages(
                source_text=trimmed_text,
                language=payload.language,
                plan_days=payload.plan_days,
                instruction=payload.instruction,
            )
            max_tokens = 1800

        elif artifact_type == "mnemonic_set":
            messages = mnemonic_messages(
                source_text=trimmed_text,
                language=payload.language,
                item_count=payload.item_count,
                instruction=payload.instruction,
            )
            max_tokens = 1400
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid artifact type",
            )

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.25,
        )

        title = payload.title or str(
            completion.data.get("title", "AI Study Tool")
        ).strip()

        content_markdown = str(
            completion.data.get("markdown", "")
        ).strip()

        if not content_markdown:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI did not return artifact content",
            )

        artifact = StudyArtifact(
            user_id=current_user.id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            artifact_type=artifact_type,
            title=title[:200],
            content_markdown=content_markdown,
            content_json=completion.data,
            language=payload.language,
            **context_ids,
        )

        return StudyToolsRepository.create_artifact(
            db,
            artifact,
        )

    @staticmethod
    async def generate_mind_map(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="mind_map",
        )

    @staticmethod
    async def generate_worksheet(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="worksheet",
        )

    @staticmethod
    async def extract_formulas(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="formula_sheet",
        )

    @staticmethod
    async def generate_important_questions(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="important_questions",
        )

    @staticmethod
    def list_artifacts(
        db: Session,
        current_user: User,
        artifact_type: str | None = None,
    ) -> list[StudyArtifact]:
        return StudyToolsRepository.list_artifacts(
            db,
            current_user.id,
            artifact_type,
        )

    @staticmethod
    def get_artifact(
        db: Session,
        artifact_id: uuid.UUID,
        current_user: User,
    ) -> StudyArtifact:
        artifact = StudyToolsRepository.get_artifact_for_user(
            db,
            artifact_id,
            current_user.id,
        )

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study artifact not found",
            )

        return artifact

    @staticmethod
    def update_artifact(
        db: Session,
        artifact_id: uuid.UUID,
        payload: StudyArtifactUpdateRequest,
        current_user: User,
    ) -> StudyArtifact:
        artifact = StudyToolsService.get_artifact(
            db,
            artifact_id,
            current_user,
        )

        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(artifact, field, value)

        return StudyToolsRepository.update_artifact(
            db,
            artifact,
        )

    @staticmethod
    def delete_artifact(
        db: Session,
        artifact_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        artifact = StudyToolsService.get_artifact(
            db,
            artifact_id,
            current_user,
        )

        artifact.is_deleted = True

        StudyToolsRepository.update_artifact(
            db,
            artifact,
        )

        return {
            "deleted_id": artifact_id,
            "message": "Study artifact deleted successfully",
        }
    
    @staticmethod
    async def extract_key_points(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="key_points",
        )

    @staticmethod
    async def generate_glossary(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="glossary",
        )

    @staticmethod
    async def generate_revision_checklist(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="revision_checklist",
        )

    @staticmethod
    async def generate_study_plan(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="study_plan",
        )

    @staticmethod
    async def generate_mnemonics(
        db: Session,
        payload: StudyArtifactGenerateRequest,
        current_user: User,
    ) -> StudyArtifact:
        return await StudyToolsService._generate_artifact(
            db,
            payload,
            current_user,
            artifact_type="mnemonic_set",
        )
    
    @staticmethod
    def _extract_pdf_text_from_upload(file: UploadFile) -> str:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed",
            )

        try:
            file_bytes = file.file.read()

            if not file_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded PDF is empty",
                )

            extracted_pages: list[str] = []

            with pymupdf.open(stream=file_bytes, filetype="pdf") as pdf:
                if pdf.page_count == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The PDF has no pages",
                    )

                for page in pdf:
                    text = page.get_text("text").strip()

                    if text:
                        extracted_pages.append(text)

            extracted_text = "\n\n".join(extracted_pages).strip()

            if not extracted_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No selectable text found in this PDF",
                )

            return extracted_text

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process uploaded PDF",
            ) from exc

        finally:
            file.file.close()

    @staticmethod
    async def extract_key_points_from_pdf_upload(
        db: Session,
        file: UploadFile,
        title: str | None,
        language: str,
        item_count: int,
        instruction: str | None,
        current_user: User,
    ) -> StudyArtifact:
        if language not in {"en", "bn"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language must be 'en' or 'bn'",
            )

        extracted_text = StudyToolsService._extract_pdf_text_from_upload(file)

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=key_points_messages(
                source_text=StudyToolsService._trim_text(extracted_text),
                language=language,
                item_count=item_count,
                instruction=instruction,
            ),
            max_tokens=1400,
            temperature=0.2,
        )

        artifact_title = title or str(
            completion.data.get("title", "PDF Key Points")
        ).strip()

        content_markdown = str(
            completion.data.get("markdown", "")
        ).strip()

        if not content_markdown:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI did not return key points",
            )

        artifact = StudyArtifact(
            user_id=current_user.id,
            source_type="raw_text",
            source_id=None,
            artifact_type="key_points",
            title=artifact_title[:200],
            content_markdown=content_markdown,
            content_json=completion.data,
            language=language,
            grade_id=None,
            subject_id=None,
            chapter_id=None,
        )

        return StudyToolsRepository.create_artifact(
            db,
            artifact,
        )