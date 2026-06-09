import uuid

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.catalog.repository import CatalogRepository
from app.modules.diagnostics.repository import DiagnosticsRepository
from app.modules.remediation.model import (
    RemediationContent,
    RemediationRecheck,
    RemediationSession,
)
from app.modules.remediation.prompts import (
    recheck_evaluation_messages,
    remediation_generation_messages,
)
from app.modules.remediation.repository import RemediationRepository
from app.modules.remediation.schema import (
    RemediationGenerateRequest,
    RemediationGeneratedContent,
    RemediationRecheckEvaluation,
    RemediationRecheckRequest,
)
from app.modules.rag.service import RagService
from app.modules.tutor.deepseek_provider import DeepSeekProvider


class RemediationService:
    @staticmethod
    def _get_session_detail(
        db: Session,
        remediation_session_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        session = RemediationRepository.get_session_for_user(
            db,
            remediation_session_id,
            current_user.id,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remediation session not found",
            )

        content = RemediationRepository.get_content(
            db,
            session.id,
        )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remediation content not found",
            )

        rechecks = RemediationRepository.list_rechecks(
            db,
            session.id,
        )

        return {
            "session": session,
            "content": content,
            "rechecks": rechecks,
        }

    @staticmethod
    def _build_evidence_text(
        db: Session,
        diagnostic_session_id: uuid.UUID,
        weakness_label: str,
    ) -> str:
        questions = DiagnosticsRepository.list_questions(
            db,
            diagnostic_session_id,
        )
        answers = DiagnosticsRepository.list_answers(
            db,
            diagnostic_session_id,
        )

        question_by_id = {
            question.id: question
            for question in questions
        }

        evidence_lines = []

        for answer in answers:
            if answer.detected_weakness != weakness_label:
                continue

            question = question_by_id.get(answer.question_id)

            if not question:
                continue

            evidence_lines.append(
                f"- Question: {question.question_text}\n"
                f"  Student answer: {answer.student_answer}\n"
                f"  Correct answer: {question.correct_answer}\n"
                f"  Feedback: {answer.feedback}"
            )

        if not evidence_lines:
            return (
                "No detailed evidence was found, but this weakness was selected "
                "from the chapter quiz result."
            )

        return "\n".join(evidence_lines)

    @staticmethod
    async def generate_from_diagnostic(
        db: Session,
        diagnostic_session_id: uuid.UUID,
        payload: RemediationGenerateRequest,
        current_user: User,
    ) -> dict:
        diagnostic_session = DiagnosticsRepository.get_session_for_user(
            db,
            diagnostic_session_id,
            current_user.id,
        )

        if not diagnostic_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnostic session not found",
            )

        if diagnostic_session.status != "evaluated":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diagnostic session must be evaluated before remediation",
            )

        if diagnostic_session.assessment_type == "understanding_check":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Generate remediation from a chapter quiz, not an understanding check",
            )

        answers = DiagnosticsRepository.list_answers(
            db,
            diagnostic_session.id,
        )

        detected_weaknesses = list(
            dict.fromkeys(
                answer.detected_weakness
                for answer in answers
                if answer.detected_weakness
            )
        )

        if not detected_weaknesses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No weakness was detected in this diagnostic session",
            )

        selected_weakness = (
            payload.weakness_label
            if payload.weakness_label
            else detected_weaknesses[0]
        )

        if selected_weakness not in detected_weaknesses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected weakness was not found in this diagnostic session",
            )

        chapter = CatalogRepository.get_chapter_by_id(
            db,
            diagnostic_session.chapter_id,
        )

        if not chapter or not chapter.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        chunks = RagService.get_story_context_for_tutor(
            db=db,
            chapter_id=diagnostic_session.chapter_id,
            language=payload.language,
            limit=8,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No RAG chunks are available for remediation generation",
            )

        evidence = RemediationService._build_evidence_text(
            db,
            diagnostic_session.id,
            selected_weakness,
        )

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=remediation_generation_messages(
                chapter=chapter,
                language=payload.language,
                weakness_label=selected_weakness,
                evidence=evidence,
                chunks=chunks,
            ),
            max_tokens=settings.remediation_generation_output_tokens,
            temperature=0.2,
        )

        try:
            generated_content = RemediationGeneratedContent.model_validate(
                completion.data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned invalid remediation content",
            ) from exc

        session = RemediationSession(
            user_id=current_user.id,
            chapter_id=diagnostic_session.chapter_id,
            diagnostic_session_id=diagnostic_session.id,
            weakness_label=selected_weakness,
            language=payload.language,
            status="generated",
            is_source_grounded=True,
        )

        content = RemediationContent(
            weakness_statement=generated_content.weakness_statement,
            micro_lesson=generated_content.micro_lesson,
            guided_example=generated_content.guided_example,
            partially_solved_problem=generated_content.partially_solved_problem,
            recheck_question=generated_content.recheck_question,
            expected_answer=generated_content.expected_answer,
            next_action=generated_content.next_action,
        )

        created_session = RemediationRepository.create_session_with_content(
            db,
            session,
            content,
        )

        return RemediationService._get_session_detail(
            db,
            created_session.id,
            current_user,
        )

    @staticmethod
    def get_session(
        db: Session,
        remediation_session_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        return RemediationService._get_session_detail(
            db,
            remediation_session_id,
            current_user,
        )

    @staticmethod
    async def submit_recheck(
        db: Session,
        remediation_session_id: uuid.UUID,
        payload: RemediationRecheckRequest,
        current_user: User,
    ) -> dict:
        detail = RemediationService._get_session_detail(
            db,
            remediation_session_id,
            current_user,
        )

        session = detail["session"]
        content = detail["content"]

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=recheck_evaluation_messages(
                language=session.language,
                weakness_label=session.weakness_label,
                recheck_question=content.recheck_question,
                expected_answer=content.expected_answer,
                student_answer=payload.student_answer,
            ),
            max_tokens=settings.remediation_evaluation_output_tokens,
            temperature=0.1,
        )

        try:
            evaluation = RemediationRecheckEvaluation.model_validate(
                completion.data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned invalid recheck evaluation",
            ) from exc

        is_passed = evaluation.score >= settings.remediation_pass_score

        new_status = (
            "completed"
            if is_passed
            else "needs_retry"
        )

        recheck = RemediationRecheck(
            remediation_session_id=session.id,
            student_answer=payload.student_answer,
            is_correct=is_passed,
            score=evaluation.score,
            feedback=evaluation.feedback,
            next_action=evaluation.next_action,
        )

        RemediationRepository.add_recheck(
            db,
            session,
            recheck,
            new_status,
        )

        return RemediationService._get_session_detail(
            db,
            session.id,
            current_user,
        )

    @staticmethod
    def list_my_chapter_sessions(
        db: Session,
        chapter_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        chapter = CatalogRepository.get_chapter_by_id(
            db,
            chapter_id,
        )

        if not chapter or not chapter.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        sessions = RemediationRepository.list_user_chapter_sessions(
            db,
            current_user.id,
            chapter_id,
        )

        return {
            "sessions": sessions,
        }

    @staticmethod
    def delete_session(
        db: Session,
        remediation_session_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        session = RemediationRepository.get_session_for_user(
            db,
            remediation_session_id,
            current_user.id,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remediation session not found",
            )

        deleted_id = session.id

        RemediationRepository.delete_session(
            db,
            session,
        )

        return {
            "deleted_id": deleted_id,
            "message": "Remediation session deleted successfully",
        }