import uuid

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.catalog.model import Topic
from app.modules.catalog.repository import CatalogRepository
from app.modules.diagnostics.model import (
    DiagnosticAnswer,
    DiagnosticQuestion,
    DiagnosticSession,
)
from app.modules.diagnostics.prompts import (
    diagnostic_quiz_messages,
    short_answer_evaluation_messages,
    understanding_check_messages,
)
from app.modules.diagnostics.repository import DiagnosticsRepository
from app.modules.diagnostics.schema import (
    DiagnosticGenerateRequest,
    GeneratedQuestion,
    GeneratedQuestionSet,
    SessionSubmitRequest,
    ShortAnswerEvaluation,
)
from app.modules.rag.model import DocumentChunk
from app.modules.rag.service import RagService
from app.modules.tutor.deepseek_provider import DeepSeekProvider


class DiagnosticsService:
    @staticmethod
    def _get_active_topic(
        db: Session,
        topic_id: uuid.UUID,
    ) -> Topic:
        topic = CatalogRepository.get_topic_by_id(
            db,
            topic_id,
        )

        if not topic or not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        return topic

    @staticmethod
    def _get_source_chunks(
        db: Session,
        topic_id: uuid.UUID,
        language: str,
    ) -> list[DocumentChunk]:
        chunks = RagService.get_story_context_for_tutor(
            db=db,
            topic_id=topic_id,
            language=language,
            limit=6,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No approved source chunks are available for diagnostic generation. "
                    "Build RAG chunks for this topic and language first."
                ),
            )

        return chunks

    @staticmethod
    def _get_session_for_user(
        db: Session,
        session_id: uuid.UUID,
        current_user: User,
    ) -> DiagnosticSession:
        session = DiagnosticsRepository.get_session_for_user(
            db,
            session_id,
            current_user.id,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnostic session not found",
            )

        return session

    @staticmethod
    def _question_models(
        generated_questions: list[GeneratedQuestion],
    ) -> list[DiagnosticQuestion]:
        return [
            DiagnosticQuestion(
                question_type=item.question_type,
                question_text=item.question_text,
                options=item.options,
                correct_answer=item.correct_answer.strip(),
                evaluation_rubric=item.evaluation_rubric,
                skill_label=item.skill_label,
                explanation=item.explanation,
                display_order=index,
                max_score=1.0,
            )
            for index, item in enumerate(generated_questions, start=1)
        ]

    @staticmethod
    async def generate_understanding_check(
        db: Session,
        topic_id: uuid.UUID,
        payload: DiagnosticGenerateRequest,
        current_user: User,
    ) -> DiagnosticSession:
        topic = DiagnosticsService._get_active_topic(
            db,
            topic_id,
        )

        chunks = DiagnosticsService._get_source_chunks(
            db,
            topic_id,
            payload.language,
        )

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=understanding_check_messages(
                topic=topic,
                language=payload.language,
                chunks=chunks,
            ),
            max_tokens=700,
            temperature=0.2,
        )

        try:
            generated_set = GeneratedQuestionSet.model_validate(
                completion.data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned an invalid understanding-check question shape",
            ) from exc

        if len(generated_set.questions) != 1:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Understanding check must contain exactly one question",
            )

        if generated_set.questions[0].question_type != "short_answer":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Understanding check must be a short-answer question",
            )

        session = DiagnosticSession(
            user_id=current_user.id,
            topic_id=topic_id,
            conversation_id=payload.conversation_id,
            language=payload.language,
            assessment_type="understanding_check",
            status="generated",
            question_count=1,
        )

        return DiagnosticsRepository.create_session_with_questions(
            db,
            session,
            DiagnosticsService._question_models(
                generated_set.questions
            ),
        )

    @staticmethod
    async def generate_diagnostic_quiz(
        db: Session,
        topic_id: uuid.UUID,
        payload: DiagnosticGenerateRequest,
        current_user: User,
    ) -> DiagnosticSession:
        topic = DiagnosticsService._get_active_topic(
            db,
            topic_id,
        )

        chunks = DiagnosticsService._get_source_chunks(
            db,
            topic_id,
            payload.language,
        )

        await DeepSeekProvider.ensure_credit_available()

        completion = await DeepSeekProvider.complete_json(
            messages=diagnostic_quiz_messages(
                topic=topic,
                language=payload.language,
                chunks=chunks,
            ),
            max_tokens=settings.diagnostic_quiz_output_tokens,
            temperature=0.2,
        )

        try:
            generated_set = GeneratedQuestionSet.model_validate(
                completion.data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned an invalid diagnostic quiz shape",
            ) from exc

        questions = generated_set.questions

        if len(questions) != 5:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Diagnostic quiz must contain exactly five questions",
            )

        mcq_count = sum(
            1 for question in questions
            if question.question_type == "mcq"
        )

        short_answer_count = sum(
            1 for question in questions
            if question.question_type == "short_answer"
        )

        if mcq_count != 3 or short_answer_count != 2:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Diagnostic quiz must contain exactly 3 MCQ and 2 short-answer questions",
            )

        session = DiagnosticSession(
            user_id=current_user.id,
            topic_id=topic_id,
            conversation_id=payload.conversation_id,
            language=payload.language,
            assessment_type="diagnostic_quiz",
            status="generated",
            question_count=5,
        )

        return DiagnosticsRepository.create_session_with_questions(
            db,
            session,
            DiagnosticsService._question_models(questions),
        )

    @staticmethod
    def get_questions(
        db: Session,
        session_id: uuid.UUID,
        current_user: User,
    ) -> list[DiagnosticQuestion]:
        session = DiagnosticsService._get_session_for_user(
            db,
            session_id,
            current_user,
        )

        return DiagnosticsRepository.list_questions(
            db,
            session.id,
        )

    @staticmethod
    async def submit_session(
        db: Session,
        session_id: uuid.UUID,
        payload: SessionSubmitRequest,
        current_user: User,
    ) -> DiagnosticSession:
        session = DiagnosticsService._get_session_for_user(
            db,
            session_id,
            current_user,
        )

        if session.status == "evaluated":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This diagnostic session has already been submitted",
            )

        questions = DiagnosticsRepository.list_questions(
            db,
            session.id,
        )

        answer_map = {
            answer.question_id: answer.student_answer.strip()
            for answer in payload.answers
        }

        expected_question_ids = {
            question.id
            for question in questions
        }

        if set(answer_map.keys()) != expected_question_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submit exactly one answer for every question in the session",
            )

        evaluated_answers: list[DiagnosticAnswer] = []

        for question in questions:
            student_answer = answer_map[question.id]

            if question.question_type == "mcq":
                is_correct = (
                    student_answer.upper()
                    == question.correct_answer.upper()
                )

                evaluated_answers.append(
                    DiagnosticAnswer(
                        session_id=session.id,
                        question_id=question.id,
                        student_answer=student_answer,
                        is_correct=is_correct,
                        score=1.0 if is_correct else 0.0,
                        feedback=(
                            "Correct."
                            if is_correct
                            else question.explanation
                        ),
                        detected_weakness=(
                            None
                            if is_correct
                            else question.skill_label
                        ),
                        confidence="high",
                        evaluation_method="automatic",
                    )
                )

                continue

            await DeepSeekProvider.ensure_credit_available()

            completion = await DeepSeekProvider.complete_json(
                messages=short_answer_evaluation_messages(
                    question_text=question.question_text,
                    expected_answer=question.correct_answer,
                    rubric=question.evaluation_rubric or question.correct_answer,
                    student_answer=student_answer,
                    skill_label=question.skill_label,
                    language=session.language,
                ),
                max_tokens=settings.diagnostic_evaluation_output_tokens,
                temperature=0.1,
            )

            try:
                evaluation = ShortAnswerEvaluation.model_validate(
                    completion.data
                )
            except ValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="DeepSeek returned an invalid short-answer evaluation shape",
                ) from exc

            evaluated_answers.append(
                DiagnosticAnswer(
                    session_id=session.id,
                    question_id=question.id,
                    student_answer=student_answer,
                    is_correct=evaluation.is_correct,
                    score=evaluation.score,
                    feedback=evaluation.feedback,
                    detected_weakness=evaluation.detected_weakness,
                    confidence=evaluation.confidence,
                    evaluation_method="deepseek",
                )
            )

        total_score = round(
            sum(answer.score for answer in evaluated_answers),
            2,
        )

        maximum_score = sum(
            question.max_score for question in questions
        )

        percentage = round(
            (total_score / maximum_score) * 100,
            2,
        )

        strengths = list(
            dict.fromkeys(
                question.skill_label
                for question, answer in zip(questions, evaluated_answers)
                if answer.is_correct
            )
        )

        weaknesses = list(
            dict.fromkeys(
                answer.detected_weakness
                for answer in evaluated_answers
                if answer.detected_weakness
            )
        )

        if session.assessment_type == "understanding_check":
            outcome = (
                "understood"
                if percentage >= settings.diagnostic_pass_percentage
                else "needs_diagnostic"
            )

            update_topic_status = False
        else:
            outcome = (
                "strong"
                if percentage >= settings.diagnostic_pass_percentage
                else "needs_practice"
            )

            update_topic_status = True

        return DiagnosticsRepository.save_evaluation(
            db=db,
            session=session,
            answers=evaluated_answers,
            score=total_score,
            percentage=percentage,
            outcome=outcome,
            strengths=strengths,
            weaknesses=weaknesses,
            update_topic_status=update_topic_status,
            pass_percentage=settings.diagnostic_pass_percentage,
        )

    @staticmethod
    def get_result(
        db: Session,
        session_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        session = DiagnosticsService._get_session_for_user(
            db,
            session_id,
            current_user,
        )

        if session.status != "evaluated":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submit the session before requesting the result",
            )

        questions = DiagnosticsRepository.list_questions(
            db,
            session.id,
        )

        answers = DiagnosticsRepository.list_answers(
            db,
            session.id,
        )

        answer_by_question = {
            answer.question_id: answer
            for answer in answers
        }

        result_answers = []

        strengths = []
        weaknesses = []

        for question in questions:
            answer = answer_by_question[question.id]

            if answer.is_correct:
                strengths.append(question.skill_label)

            if answer.detected_weakness:
                weaknesses.append(answer.detected_weakness)

            result_answers.append(
                {
                    "question_id": question.id,
                    "question_type": question.question_type,
                    "question_text": question.question_text,
                    "student_answer": answer.student_answer,
                    "correct_answer": question.correct_answer,
                    "is_correct": answer.is_correct,
                    "score": answer.score,
                    "feedback": answer.feedback,
                    "skill_label": question.skill_label,
                    "detected_weakness": answer.detected_weakness,
                    "confidence": answer.confidence,
                    "explanation": question.explanation,
                }
            )

        strengths = list(dict.fromkeys(strengths))
        weaknesses = list(dict.fromkeys(weaknesses))

        topic_status = DiagnosticsRepository.get_topic_status(
            db,
            current_user.id,
            session.topic_id,
        )

        completion_status = (
            topic_status.completion_status
            if topic_status
            else None
        )

        return {
            "session": session,
            "answers": result_answers,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "completion_status": completion_status,
            "show_checkmark": completion_status == "completed",
        }

    @staticmethod
    def get_topic_status(
        db: Session,
        topic_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        DiagnosticsService._get_active_topic(
            db,
            topic_id,
        )

        status_record = DiagnosticsRepository.get_topic_status(
            db,
            current_user.id,
            topic_id,
        )

        if not status_record:
            return {
                "topic_id": topic_id,
                "completion_status": "not_started",
                "latest_score": None,
                "best_score": None,
                "strength_labels": [],
                "weakness_labels": [],
                "show_checkmark": False,
                "completed_at": None,
            }

        return {
            "topic_id": topic_id,
            "completion_status": status_record.completion_status,
            "latest_score": status_record.latest_score,
            "best_score": status_record.best_score,
            "strength_labels": status_record.strength_labels,
            "weakness_labels": status_record.weakness_labels,
            "show_checkmark": status_record.completion_status == "completed",
            "completed_at": status_record.completed_at,
        }

    @staticmethod
    def get_subject_summary(
        db: Session,
        subject_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        subject = CatalogRepository.get_subject_by_id(
            db,
            subject_id,
        )

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        topic_ids = DiagnosticsRepository.list_active_topic_ids_for_subject(
            db,
            subject_id,
        )

        statuses = DiagnosticsRepository.list_statuses_for_topics(
            db,
            current_user.id,
            topic_ids,
        )

        completed_topics = sum(
            1
            for status_record in statuses
            if status_record.completion_status == "completed"
        )

        strength_labels = list(
            dict.fromkeys(
                label
                for status_record in statuses
                for label in status_record.strength_labels
            )
        )

        weakness_labels = list(
            dict.fromkeys(
                label
                for status_record in statuses
                for label in status_record.weakness_labels
            )
        )

        total_topics = len(topic_ids)

        return {
            "subject_id": subject_id,
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "is_completed": (
                total_topics > 0
                and completed_topics == total_topics
            ),
            "strength_labels": strength_labels,
            "weakness_labels": weakness_labels,
        }