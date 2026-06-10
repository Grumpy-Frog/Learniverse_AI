import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.study_tools.model import AiNote, FlashcardDeck, StudyDocument, StudyArtifact

from app.modules.study_tools.schema import (
    AiNoteGenerateRequest,
    AiNoteResponse,
    AiNoteUpdateRequest,
    DeleteStudyToolResponse,
    FlashcardDeckDetailResponse,
    FlashcardDeckResponse,
    FlashcardDeckUpdateRequest,
    FlashcardGenerateRequest,
    PdfSummarizeRequest,
    StudyDocumentDetailResponse,
    StudyDocumentResponse,
    StudyArtifactGenerateRequest,
    StudyArtifactResponse,
    StudyArtifactUpdateRequest,
)

from app.modules.study_tools.service import StudyToolsService


router = APIRouter(
    prefix="/study-tools",
    tags=["Study Tools"],
)


@router.post(
    "/pdfs/upload",
    response_model=StudyDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_pdf(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    title: str = Form(...),
    language: str = Form("en"),
    grade_id: uuid.UUID | None = Form(None),
    subject_id: uuid.UUID | None = Form(None),
    chapter_id: uuid.UUID | None = Form(None),
) -> StudyDocument:
    return StudyToolsService.upload_pdf(
        db=db,
        title=title,
        language=language,
        grade_id=grade_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        file=file,
        current_user=current_user,
    )


@router.get(
    "/pdfs",
    response_model=list[StudyDocumentResponse],
)
def list_pdfs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[StudyDocument]:
    return StudyToolsService.list_documents(db, current_user)


@router.get(
    "/pdfs/{document_id}",
    response_model=StudyDocumentDetailResponse,
)
def get_pdf(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyDocument:
    return StudyToolsService.get_document(db, document_id, current_user)


@router.post(
    "/pdfs/{document_id}/summarize",
    response_model=StudyDocumentResponse,
)
async def summarize_pdf(
    document_id: uuid.UUID,
    payload: PdfSummarizeRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyDocument:
    return await StudyToolsService.summarize_pdf(
        db,
        document_id,
        payload,
        current_user,
    )


@router.delete(
    "/pdfs/{document_id}",
    response_model=DeleteStudyToolResponse,
)
def delete_pdf(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return StudyToolsService.delete_document(db, document_id, current_user)


@router.post(
    "/notes/generate",
    response_model=AiNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_note(
    payload: AiNoteGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AiNote:
    return await StudyToolsService.generate_note(
        db,
        payload,
        current_user,
    )


@router.get(
    "/notes",
    response_model=list[AiNoteResponse],
)
def list_notes(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AiNote]:
    return StudyToolsService.list_notes(db, current_user)


@router.get(
    "/notes/{note_id}",
    response_model=AiNoteResponse,
)
def get_note(
    note_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AiNote:
    return StudyToolsService.get_note(db, note_id, current_user)


@router.patch(
    "/notes/{note_id}",
    response_model=AiNoteResponse,
)
def update_note(
    note_id: uuid.UUID,
    payload: AiNoteUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AiNote:
    return StudyToolsService.update_note(db, note_id, payload, current_user)


@router.delete(
    "/notes/{note_id}",
    response_model=DeleteStudyToolResponse,
)
def delete_note(
    note_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return StudyToolsService.delete_note(db, note_id, current_user)


@router.post(
    "/flashcards/generate",
    response_model=FlashcardDeckDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_flashcards(
    payload: FlashcardGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return await StudyToolsService.generate_flashcards(
        db,
        payload,
        current_user,
    )


@router.get(
    "/flashcards/decks",
    response_model=list[FlashcardDeckResponse],
)
def list_flashcard_decks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[FlashcardDeck]:
    return StudyToolsService.list_decks(db, current_user)


@router.get(
    "/flashcards/decks/{deck_id}",
    response_model=FlashcardDeckDetailResponse,
)
def get_flashcard_deck(
    deck_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return StudyToolsService.get_deck_detail(db, deck_id, current_user)


@router.patch(
    "/flashcards/decks/{deck_id}",
    response_model=FlashcardDeckResponse,
)
def update_flashcard_deck(
    deck_id: uuid.UUID,
    payload: FlashcardDeckUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FlashcardDeck:
    return StudyToolsService.update_deck(db, deck_id, payload, current_user)


@router.delete(
    "/flashcards/decks/{deck_id}",
    response_model=DeleteStudyToolResponse,
)
def delete_flashcard_deck(
    deck_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return StudyToolsService.delete_deck(db, deck_id, current_user)


@router.post(
    "/mind-maps/generate",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_mind_map(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.generate_mind_map(
        db,
        payload,
        current_user,
    )


@router.post(
    "/worksheets/generate",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_worksheet(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.generate_worksheet(
        db,
        payload,
        current_user,
    )


@router.post(
    "/formulas/extract",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def extract_formulas(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.extract_formulas(
        db,
        payload,
        current_user,
    )


@router.post(
    "/important-questions/generate",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_important_questions(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.generate_important_questions(
        db,
        payload,
        current_user,
    )


@router.get(
    "/artifacts",
    response_model=list[StudyArtifactResponse],
)
def list_artifacts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    artifact_type: str | None = None,
) -> list[StudyArtifact]:
    return StudyToolsService.list_artifacts(
        db,
        current_user,
        artifact_type,
    )


@router.get(
    "/artifacts/{artifact_id}",
    response_model=StudyArtifactResponse,
)
def get_artifact(
    artifact_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return StudyToolsService.get_artifact(
        db,
        artifact_id,
        current_user,
    )


@router.patch(
    "/artifacts/{artifact_id}",
    response_model=StudyArtifactResponse,
)
def update_artifact(
    artifact_id: uuid.UUID,
    payload: StudyArtifactUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return StudyToolsService.update_artifact(
        db,
        artifact_id,
        payload,
        current_user,
    )


@router.delete(
    "/artifacts/{artifact_id}",
    response_model=DeleteStudyToolResponse,
)
def delete_artifact(
    artifact_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return StudyToolsService.delete_artifact(
        db,
        artifact_id,
        current_user,
    )


@router.post(
    "/mind-maps/generate",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_mind_map(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.generate_mind_map(
        db,
        payload,
        current_user,
    )


@router.post(
    "/worksheets/generate",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_worksheet(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.generate_worksheet(
        db,
        payload,
        current_user,
    )


@router.post(
    "/formulas/extract",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def extract_formulas(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.extract_formulas(
        db,
        payload,
        current_user,
    )


@router.post(
    "/important-questions/generate",
    response_model=StudyArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_important_questions(
    payload: StudyArtifactGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return await StudyToolsService.generate_important_questions(
        db,
        payload,
        current_user,
    )


@router.get(
    "/artifacts",
    response_model=list[StudyArtifactResponse],
)
def list_artifacts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    artifact_type: str | None = None,
) -> list[StudyArtifact]:
    return StudyToolsService.list_artifacts(
        db,
        current_user,
        artifact_type,
    )


@router.get(
    "/artifacts/{artifact_id}",
    response_model=StudyArtifactResponse,
)
def get_artifact(
    artifact_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return StudyToolsService.get_artifact(
        db,
        artifact_id,
        current_user,
    )


@router.patch(
    "/artifacts/{artifact_id}",
    response_model=StudyArtifactResponse,
)
def update_artifact(
    artifact_id: uuid.UUID,
    payload: StudyArtifactUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudyArtifact:
    return StudyToolsService.update_artifact(
        db,
        artifact_id,
        payload,
        current_user,
    )


@router.delete(
    "/artifacts/{artifact_id}",
    response_model=DeleteStudyToolResponse,
)
def delete_artifact(
    artifact_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return StudyToolsService.delete_artifact(
        db,
        artifact_id,
        current_user,
    )