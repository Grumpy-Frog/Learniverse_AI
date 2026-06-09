import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.catalog.model import Chapter, Subject, Topic
from app.modules.catalog.repository import CatalogRepository
from app.modules.rag.model import DocumentChunk
from app.modules.rag.service import RagService
from app.modules.tutor.deepseek_provider import DeepSeekProvider
from app.modules.tutor.model import TutorConversation, TutorGroup, TutorMessage
from app.modules.tutor.prompts import (
    chat_system_prompt,
    format_rag_context,
    out_of_scope_reply,
    scope_check_messages,
    story_messages,
)
from app.modules.tutor.repository import TutorRepository
from app.modules.tutor.schema import (
    ChatMessageRequest,
    ConversationCreateRequest,
    StoryGenerateRequest,
    TutorGroupCreateRequest,
)


class TutorService:
    @staticmethod
    def _get_active_subject(
        db: Session,
        subject_id: uuid.UUID,
    ) -> Subject:
        subject = CatalogRepository.get_subject_by_id(
            db,
            subject_id,
        )

        if not subject or not subject.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        return subject

    @staticmethod
    def _get_active_chapter(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> Chapter:
        chapter = CatalogRepository.get_chapter_by_id(
            db,
            chapter_id,
        )

        if not chapter or not chapter.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        return chapter

    @staticmethod
    def _get_chapter_topics(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> list[Topic]:
        return CatalogRepository.list_topics(
            db,
            chapter_id,
        )

    @staticmethod
    def _get_user_conversation(
        db: Session,
        conversation_id: uuid.UUID,
        current_user: User,
    ) -> TutorConversation:
        conversation = TutorRepository.get_conversation_for_user(
            db,
            conversation_id,
            current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return conversation

    @staticmethod
    def _get_user_group(
        db: Session,
        group_id: uuid.UUID,
        current_user: User,
    ) -> TutorGroup:
        group = TutorRepository.get_group_for_user(
            db,
            group_id,
            current_user.id,
        )

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor group not found",
            )

        return group

    @staticmethod
    def _get_or_create_default_group(
        db: Session,
        current_user: User,
        subject: Subject,
    ) -> TutorGroup:
        existing_group = TutorRepository.get_first_group_for_subject(
            db,
            current_user.id,
            subject.id,
        )

        if existing_group:
            return existing_group

        group = TutorGroup(
            user_id=current_user.id,
            subject_id=subject.id,
            title=subject.name,
        )

        return TutorRepository.create_group(
            db,
            group,
        )

    @staticmethod
    def _add_token_values(
        first: int | None,
        second: int | None,
    ) -> int | None:
        if first is None and second is None:
            return None

        return (first or 0) + (second or 0)

    @staticmethod
    def _sources_from_chunks(
        chunks: list[DocumentChunk],
    ) -> list[dict]:
        return [
            {
                "document_id": chunk.document_id,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "section_title": chunk.section_title,
                "content_preview": (
                    chunk.content[:180] + "..."
                    if len(chunk.content) > 180
                    else chunk.content
                ),
            }
            for chunk in chunks
        ]

    @staticmethod
    def create_group(
        db: Session,
        payload: TutorGroupCreateRequest,
        current_user: User,
    ) -> TutorGroup:
        subject = TutorService._get_active_subject(
            db,
            payload.subject_id,
        )

        group = TutorGroup(
            user_id=current_user.id,
            subject_id=subject.id,
            title=(payload.title or subject.name).strip(),
        )

        return TutorRepository.create_group(
            db,
            group,
        )

    @staticmethod
    def list_groups(
        db: Session,
        current_user: User,
    ) -> list[TutorGroup]:
        return TutorRepository.list_user_groups(
            db,
            current_user.id,
        )

    @staticmethod
    def delete_group(
        db: Session,
        group_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        group = TutorService._get_user_group(
            db,
            group_id,
            current_user,
        )

        deleted_id = group.id

        TutorRepository.delete_group(
            db,
            group,
        )

        return {
            "deleted_id": deleted_id,
            "message": "Tutor group deleted successfully",
        }

    @staticmethod
    def create_conversation(
        db: Session,
        payload: ConversationCreateRequest,
        current_user: User,
    ) -> TutorConversation:
        chapter = TutorService._get_active_chapter(
            db,
            payload.chapter_id,
        )
        subject = chapter.subject

        if payload.group_id:
            group = TutorService._get_user_group(
                db,
                payload.group_id,
                current_user,
            )

            if group.subject_id != subject.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tutor group subject does not match chapter subject",
                )
        else:
            group = TutorService._get_or_create_default_group(
                db,
                current_user,
                subject,
            )

        conversation = TutorConversation(
            group_id=group.id,
            user_id=current_user.id,
            subject_id=subject.id,
            chapter_id=chapter.id,
            language=payload.language,
            title=f"{subject.name} — {chapter.title}",
            provider="deepseek",
            model_name=settings.deepseek_model,
            rag_mode="auto",
        )

        return TutorRepository.create_conversation(
            db,
            conversation,
        )

    @staticmethod
    def list_conversations(
        db: Session,
        current_user: User,
    ) -> list[TutorConversation]:
        return TutorRepository.list_user_conversations(
            db,
            current_user.id,
        )

    @staticmethod
    def list_subject_conversations(
        db: Session,
        subject_id: uuid.UUID,
        current_user: User,
    ) -> list[TutorConversation]:
        TutorService._get_active_subject(
            db,
            subject_id,
        )

        return TutorRepository.list_subject_conversations(
            db,
            current_user.id,
            subject_id,
        )

    @staticmethod
    def list_chapter_conversations(
        db: Session,
        chapter_id: uuid.UUID,
        current_user: User,
    ) -> list[TutorConversation]:
        TutorService._get_active_chapter(
            db,
            chapter_id,
        )

        return TutorRepository.list_chapter_conversations(
            db,
            current_user.id,
            chapter_id,
        )

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        conversation = TutorService._get_user_conversation(
            db,
            conversation_id,
            current_user,
        )

        deleted_id = conversation.id

        TutorRepository.delete_conversation(
            db,
            conversation,
        )

        return {
            "deleted_id": deleted_id,
            "message": "Conversation deleted successfully",
        }

    @staticmethod
    async def generate_story(
        db: Session,
        conversation_id: uuid.UUID,
        payload: StoryGenerateRequest,
        current_user: User,
    ) -> tuple[TutorConversation, TutorMessage, list[dict]]:
        conversation = TutorService._get_user_conversation(
            db,
            conversation_id,
            current_user,
        )

        chapter = TutorService._get_active_chapter(
            db,
            conversation.chapter_id,
        )
        topics = TutorService._get_chapter_topics(
            db,
            chapter.id,
        )

        retrieved_chunks = RagService.get_story_context_for_tutor(
            db=db,
            chapter_id=conversation.chapter_id,
            language=conversation.language,
            limit=4,
        )

        rag_context = (
            format_rag_context(retrieved_chunks)
            if retrieved_chunks
            else None
        )

        await DeepSeekProvider.ensure_credit_available()

        result = await DeepSeekProvider.complete(
            messages=story_messages(
                chapter=chapter,
                topics=topics,
                language=conversation.language,
                student_preference=payload.student_preference,
                rag_context=rag_context,
            ),
            max_tokens=settings.tutor_max_output_tokens,
            temperature=0.7,
        )

        reply = TutorMessage(
            conversation_id=conversation.id,
            role="assistant",
            message_type="story",
            content=result.content,
            is_in_scope=True,
            is_source_grounded=bool(retrieved_chunks),
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            finish_reason=result.finish_reason,
        )

        reply = TutorRepository.add_message(
            db,
            conversation,
            reply,
        )

        return (
            conversation,
            reply,
            TutorService._sources_from_chunks(retrieved_chunks),
        )

    @staticmethod
    async def send_chat_message(
        db: Session,
        conversation_id: uuid.UUID,
        payload: ChatMessageRequest,
        current_user: User,
    ) -> tuple[TutorConversation, TutorMessage, list[dict]]:
        conversation = TutorService._get_user_conversation(
            db,
            conversation_id,
            current_user,
        )

        chapter = TutorService._get_active_chapter(
            db,
            conversation.chapter_id,
        )
        topics = TutorService._get_chapter_topics(
            db,
            chapter.id,
        )

        previous_messages = TutorRepository.list_recent_messages(
            db,
            conversation.id,
            limit=12,
        )

        await DeepSeekProvider.ensure_credit_available()

        if TutorService._is_obviously_out_of_scope(payload.message):
            scope_result = None
            is_in_scope = False
        else:
            scope_result = await DeepSeekProvider.complete(
                messages=scope_check_messages(
                    chapter=chapter,
                    topics=topics,
                    student_message=payload.message,
                ),
                max_tokens=settings.tutor_scope_check_max_tokens,
                temperature=0.0,
            )

            is_in_scope = scope_result.content.strip().upper().startswith("YES")

        user_message = TutorMessage(
            conversation_id=conversation.id,
            role="user",
            message_type="chat",
            content=payload.message,
            is_in_scope=is_in_scope,
            is_source_grounded=False,
        )

        if not is_in_scope:
            TutorRepository.add_message(
                db,
                conversation,
                user_message,
            )

            refusal = TutorMessage(
                conversation_id=conversation.id,
                role="assistant",
                message_type="refusal",
                content=out_of_scope_reply(
                    chapter_title=chapter.title,
                    language=conversation.language,
                ),
                is_in_scope=False,
                is_source_grounded=False,
                prompt_tokens=scope_result.prompt_tokens if scope_result else None,
                completion_tokens=scope_result.completion_tokens if scope_result else None,
                finish_reason=scope_result.finish_reason if scope_result else "blocked",
            )

            refusal = TutorRepository.add_message(
                db,
                conversation,
                refusal,
            )

            return conversation, refusal, []

        retrieved_chunks = RagService.retrieve_context_for_tutor(
            db=db,
            chapter_id=conversation.chapter_id,
            language=conversation.language,
            query=payload.message,
            limit=4,
        )

        rag_context = (
            format_rag_context(retrieved_chunks)
            if retrieved_chunks
            else None
        )

        api_messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": chat_system_prompt(
                    chapter=chapter,
                    topics=topics,
                    language=conversation.language,
                    rag_context=rag_context,
                ),
            }
        ]

        api_messages.extend(
            {
                "role": message.role,
                "content": message.content,
            }
            for message in previous_messages
        )

        api_messages.append(
            {
                "role": "user",
                "content": payload.message,
            }
        )

        answer_result = await DeepSeekProvider.complete(
            messages=api_messages,
            max_tokens=settings.tutor_max_output_tokens,
            temperature=0.7,
        )

        TutorRepository.add_message(
            db,
            conversation,
            user_message,
        )

        reply = TutorMessage(
            conversation_id=conversation.id,
            role="assistant",
            message_type="chat",
            content=answer_result.content,
            is_in_scope=True,
            is_source_grounded=bool(retrieved_chunks),
            prompt_tokens=TutorService._add_token_values(
                scope_result.prompt_tokens if scope_result else None,
                answer_result.prompt_tokens,
            ),
            completion_tokens=TutorService._add_token_values(
                scope_result.completion_tokens if scope_result else None,
                answer_result.completion_tokens,
            ),
            finish_reason=answer_result.finish_reason,
        )

        reply = TutorRepository.add_message(
            db,
            conversation,
            reply,
        )

        return (
            conversation,
            reply,
            TutorService._sources_from_chunks(retrieved_chunks),
        )

    @staticmethod
    def list_messages(
        db: Session,
        conversation_id: uuid.UUID,
        current_user: User,
    ) -> list[TutorMessage]:
        conversation = TutorService._get_user_conversation(
            db,
            conversation_id,
            current_user,
        )

        return TutorRepository.list_messages(
            db,
            conversation.id,
        )

    @staticmethod
    def _is_obviously_out_of_scope(message: str) -> bool:
        text = message.lower()

        blocked_keywords = [
            "c++",
            "java",
            "python",
            "javascript",
            "html",
            "css",
            "react",
            "next.js",
            "programming",
            "coding",
            "football",
            "cricket",
            "messi",
            "ronaldo",
            "movie",
            "song",
            "politics",
            "election",
            "president",
            "game cheat",
        ]

        return any(keyword in text for keyword in blocked_keywords)