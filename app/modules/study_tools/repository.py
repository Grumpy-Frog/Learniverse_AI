import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.study_tools.model import (
    AiNote,
    Flashcard,
    FlashcardDeck,
    StudyDocument,
    StudyArtifact
)




class StudyToolsRepository:
    @staticmethod
    def create_document(db: Session, document: StudyDocument) -> StudyDocument:
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def get_document_for_user(db: Session, document_id: uuid.UUID, user_id: uuid.UUID) -> StudyDocument | None:
        return db.scalar(
            select(StudyDocument).where(
                StudyDocument.id == document_id,
                StudyDocument.user_id == user_id,
                StudyDocument.is_deleted.is_(False),
            )
        )

    @staticmethod
    def list_documents(db: Session, user_id: uuid.UUID) -> list[StudyDocument]:
        return list(
            db.scalars(
                select(StudyDocument)
                .where(StudyDocument.user_id == user_id, StudyDocument.is_deleted.is_(False))
                .order_by(StudyDocument.updated_at.desc())
            ).all()
        )

    @staticmethod
    def update_document(db: Session, document: StudyDocument) -> StudyDocument:
        document.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def create_note(db: Session, note: AiNote) -> AiNote:
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def get_note_for_user(db: Session, note_id: uuid.UUID, user_id: uuid.UUID) -> AiNote | None:
        return db.scalar(
            select(AiNote).where(
                AiNote.id == note_id,
                AiNote.user_id == user_id,
                AiNote.is_deleted.is_(False),
            )
        )

    @staticmethod
    def list_notes(db: Session, user_id: uuid.UUID) -> list[AiNote]:
        return list(
            db.scalars(
                select(AiNote)
                .where(AiNote.user_id == user_id, AiNote.is_deleted.is_(False))
                .order_by(AiNote.updated_at.desc())
            ).all()
        )

    @staticmethod
    def update_note(db: Session, note: AiNote) -> AiNote:
        note.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def create_deck_with_cards(
        db: Session,
        deck: FlashcardDeck,
        cards: list[Flashcard],
    ) -> FlashcardDeck:
        db.add(deck)
        db.flush()

        for card in cards:
            card.deck_id = deck.id
            db.add(card)

        db.commit()
        db.refresh(deck)
        return deck

    @staticmethod
    def get_deck_for_user(db: Session, deck_id: uuid.UUID, user_id: uuid.UUID) -> FlashcardDeck | None:
        return db.scalar(
            select(FlashcardDeck).where(
                FlashcardDeck.id == deck_id,
                FlashcardDeck.user_id == user_id,
                FlashcardDeck.is_deleted.is_(False),
            )
        )

    @staticmethod
    def list_decks(db: Session, user_id: uuid.UUID) -> list[FlashcardDeck]:
        return list(
            db.scalars(
                select(FlashcardDeck)
                .where(FlashcardDeck.user_id == user_id, FlashcardDeck.is_deleted.is_(False))
                .order_by(FlashcardDeck.updated_at.desc())
            ).all()
        )

    @staticmethod
    def list_cards(db: Session, deck_id: uuid.UUID) -> list[Flashcard]:
        return list(
            db.scalars(
                select(Flashcard)
                .where(Flashcard.deck_id == deck_id)
                .order_by(Flashcard.display_order.asc())
            ).all()
        )

    @staticmethod
    def update_deck(db: Session, deck: FlashcardDeck) -> FlashcardDeck:
        deck.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(deck)
        return deck
    
        @staticmethod
        def create_artifact(
            db: Session,
            artifact: StudyArtifact,
        ) -> StudyArtifact:
            db.add(artifact)
            db.commit()
            db.refresh(artifact)

            return artifact

        @staticmethod
        def get_artifact_for_user(
            db: Session,
            artifact_id: uuid.UUID,
            user_id: uuid.UUID,
        ) -> StudyArtifact | None:
            return db.scalar(
                select(StudyArtifact).where(
                    StudyArtifact.id == artifact_id,
                    StudyArtifact.user_id == user_id,
                    StudyArtifact.is_deleted.is_(False),
                )
            )

        @staticmethod
        def list_artifacts(
            db: Session,
            user_id: uuid.UUID,
            artifact_type: str | None = None,
        ) -> list[StudyArtifact]:
            statement = select(StudyArtifact).where(
                StudyArtifact.user_id == user_id,
                StudyArtifact.is_deleted.is_(False),
            )

            if artifact_type:
                statement = statement.where(
                    StudyArtifact.artifact_type == artifact_type,
                )

            return list(
                db.scalars(
                    statement.order_by(StudyArtifact.updated_at.desc())
                ).all()
            )

        @staticmethod
        def update_artifact(
            db: Session,
            artifact: StudyArtifact,
        ) -> StudyArtifact:
            artifact.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(artifact)

            return artifact