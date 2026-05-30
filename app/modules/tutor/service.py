import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.catalog.model import Topic
from app.modules.catalog.repository import CatalogRepository
from app.modules.rag.model import DocumentChunk
from app.modules.rag.service import RagService
from app.modules.tutor.deepseek_provider import DeepSeekProvider
from app.modules.tutor.model import TutorConversation, TutorMessage
from app.modules.tutor.prompts import (
    chat_system_prompt,
    format_rag_context,
    get_topic_context,
    no_rag_context_reply,
    out_of_scope_reply,
    scope_check_messages,
    story_messages,
)
from app.modules.tutor.repository import TutorRepository
from app.modules.tutor.schema import (
    ChatMessageRequest,
    ConversationCreateRequest,
    ConversationSettingsUpdateRequest,
    StoryGenerateRequest,
)


class TutorService:
    @staticmethod
    def _get_active_topic(db: Session, topic_id: uuid.UUID) -> Topic:
        topic = CatalogRepository.get_topic_by_id(db, topic_id)

        if not topic or not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        return topic

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
                "content_preview": (
                    chunk.content[:180] + "..."
                    if len(chunk.content) > 180
                    else chunk.content
                ),
            }
            for chunk in chunks
        ]

    @staticmethod
    def create_conversation(
        db: Session,
        payload: ConversationCreateRequest,
        current_user: User,
    ) -> TutorConversation:
        topic = TutorService._get_active_topic(db, payload.topic_id)
        _, subject_name, chapter_title, topic_title = get_topic_context(topic)

        conversation = TutorConversation(
            user_id=current_user.id,
            topic_id=topic.id,
            language=payload.language,
            title=f"{subject_name} — {chapter_title} — {topic_title}",
            provider="deepseek",
            model_name=settings.deepseek_model,
            use_rag=payload.use_rag,
        )

        return TutorRepository.create_conversation(db, conversation)

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
    def update_conversation_settings(
        db: Session,
        conversation_id: uuid.UUID,
        payload: ConversationSettingsUpdateRequest,
        current_user: User,
    ) -> TutorConversation:
        conversation = TutorService._get_user_conversation(
            db,
            conversation_id,
            current_user,
        )

        return TutorRepository.update_settings(
            db,
            conversation,
            payload.use_rag,
        )

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

        topic = TutorService._get_active_topic(
            db,
            conversation.topic_id,
        )

        retrieved_chunks: list[DocumentChunk] = []
        rag_context: str | None = None

        if conversation.use_rag:
            retrieved_chunks = RagService.get_story_context_for_tutor(
                db=db,
                topic_id=conversation.topic_id,
                language=conversation.language,
                limit=4,
            )

            if not retrieved_chunks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "No RAG chunks are available for this topic and language. "
                        "Build chunks or turn off RAG."
                    ),
                )

            rag_context = format_rag_context(retrieved_chunks)

        await DeepSeekProvider.ensure_credit_available()

        result = await DeepSeekProvider.complete(
            messages=story_messages(
                topic=topic,
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
            is_source_grounded=conversation.use_rag,
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

        topic = TutorService._get_active_topic(
            db,
            conversation.topic_id,
        )

        _, _, chapter_title, _ = get_topic_context(topic)

        previous_messages = TutorRepository.list_recent_messages(
            db,
            conversation.id,
            limit=12,
        )

        await DeepSeekProvider.ensure_credit_available()

        if TutorService._is_obviously_out_of_scope(payload.message):
            is_in_scope = False
            scope_result = None
        else:
            scope_result = await DeepSeekProvider.complete(
                messages=scope_check_messages(
                    topic=topic,
                    student_message=payload.message,
                ),
                max_tokens=settings.tutor_scope_check_max_tokens,
                temperature=0.0,
            )

            is_in_scope = scope_result.content.strip().upper() == "YES"

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
                    chapter_title=chapter_title,
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

        retrieved_chunks: list[DocumentChunk] = []
        rag_context: str | None = None

        if conversation.use_rag:
            retrieved_chunks = RagService.retrieve_context_for_tutor(
                db=db,
                topic_id=conversation.topic_id,
                language=conversation.language,
                query=payload.message,
                limit=4,
            )

            if not retrieved_chunks:
                TutorRepository.add_message(
                    db,
                    conversation,
                    user_message,
                )

                no_context_message = TutorMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    message_type="refusal",
                    content=no_rag_context_reply(
                        conversation.language,
                    ),
                    is_in_scope=True,
                    is_source_grounded=False,
                    prompt_tokens=scope_result.prompt_tokens,
                    completion_tokens=scope_result.completion_tokens,
                    finish_reason=scope_result.finish_reason,
                )

                no_context_message = TutorRepository.add_message(
                    db,
                    conversation,
                    no_context_message,
                )

                return conversation, no_context_message, []

            rag_context = format_rag_context(retrieved_chunks)

        api_messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": chat_system_prompt(
                    topic=topic,
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
            is_source_grounded=conversation.use_rag,
            prompt_tokens=TutorService._add_token_values(
                scope_result.prompt_tokens,
                answer_result.prompt_tokens,
            ),
            completion_tokens=TutorService._add_token_values(
                scope_result.completion_tokens,
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