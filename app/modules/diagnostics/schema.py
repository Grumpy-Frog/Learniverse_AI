import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LanguageCode = Literal["en", "bn"]
QuestionType = Literal["mcq", "short_answer"]


class DiagnosticGenerateRequest(BaseModel):
    language: LanguageCode = "en"
    conversation_id: uuid.UUID | None = None


class GeneratedQuestion(BaseModel):
    question_type: QuestionType
    question_text: str = Field(min_length=5)
    options: dict[str, str] | None = None
    correct_answer: str = Field(min_length=1)
    evaluation_rubric: str | None = None

    # Generic now. Not hard-coded to force/motion.
    skill_label: str = Field(min_length=2, max_length=120)

    explanation: str | None = None

    @model_validator(mode="after")
    def validate_question_shape(self):
        if self.question_type == "mcq":
            if not self.options:
                raise ValueError("MCQ questions must include options")

            expected_keys = {"A", "B", "C", "D"}

            if set(self.options.keys()) != expected_keys:
                raise ValueError("MCQ options must contain A, B, C and D")

            if self.correct_answer not in expected_keys:
                raise ValueError("MCQ correct_answer must be A, B, C or D")

        if self.question_type == "short_answer":
            if self.options is not None:
                raise ValueError("Short-answer options must be null")

            if not self.evaluation_rubric:
                raise ValueError("Short-answer questions need evaluation_rubric")

        return self


class GeneratedQuestionSet(BaseModel):
    questions: list[GeneratedQuestion]


class DiagnosticQuestionResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    question_type: str
    question_text: str
    options: dict | None
    correct_answer: str
    evaluation_rubric: str | None
    skill_label: str
    explanation: str | None
    display_order: int
    max_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicDiagnosticQuestionResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    question_type: str
    question_text: str
    options: dict | None
    skill_label: str
    display_order: int
    max_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiagnosticSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    chapter_id: uuid.UUID
    conversation_id: uuid.UUID | None
    language: str
    assessment_type: str
    status: str
    question_count: int
    score: float | None
    percentage: float | None
    outcome: str | None
    created_at: datetime
    submitted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SubmittedAnswer(BaseModel):
    question_id: uuid.UUID
    student_answer: str = Field(min_length=1, max_length=2000)


class SessionSubmitRequest(BaseModel):
    answers: list[SubmittedAnswer] = Field(min_length=1)


class DiagnosticAnswerResult(BaseModel):
    question_id: uuid.UUID
    question_type: str
    question_text: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    score: float
    feedback: str
    skill_label: str
    detected_weakness: str | None
    confidence: str | None
    explanation: str | None


class DiagnosticResultResponse(BaseModel):
    session: DiagnosticSessionResponse
    answers: list[DiagnosticAnswerResult]
    strengths: list[str]
    weaknesses: list[str]
    completion_status: str | None
    show_checkmark: bool


class ShortAnswerEvaluation(BaseModel):
    is_correct: bool
    score: float = Field(ge=0.0, le=1.0)
    feedback: str
    detected_weakness: str | None = None
    confidence: Literal["low", "medium", "high"]


class ChapterStatusResponse(BaseModel):
    chapter_id: uuid.UUID
    completion_status: str
    latest_score: float | None
    best_score: float | None
    strength_labels: list[str]
    weakness_labels: list[str]
    show_checkmark: bool
    completed_at: datetime | None


class SubjectSummaryResponse(BaseModel):
    subject_id: uuid.UUID
    total_chapters: int
    completed_chapters: int
    is_completed: bool
    strength_labels: list[str]
    weakness_labels: list[str]


class DeleteDiagnosticResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str