import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LanguageCode = Literal["en", "bn"]

SkillLabel = Literal[
    "force_concept",
    "mass_concept",
    "acceleration_concept",
    "force_mass_relationship",
    "mass_acceleration_relationship",
    "formula_understanding",
    "formula_rearrangement",
    "unit_conversion",
    "numerical_substitution",
    "graph_interpretation",
    "word_problem_understanding",
    "real_life_application",
]

QuestionType = Literal["mcq", "short_answer"]
ConfidenceLabel = Literal["low", "medium", "high"]


class DiagnosticGenerateRequest(BaseModel):
    language: LanguageCode = "en"
    conversation_id: uuid.UUID | None = None


class GeneratedQuestion(BaseModel):
    question_type: QuestionType
    question_text: str = Field(min_length=3, max_length=1000)
    options: dict[str, str] | None = None
    correct_answer: str = Field(min_length=1, max_length=1000)
    evaluation_rubric: str | None = Field(default=None, max_length=2000)
    skill_label: SkillLabel
    explanation: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_question_shape(self):
        if self.question_type == "mcq":
            if not self.options:
                raise ValueError("MCQ must include options")

            required_options = {"A", "B", "C", "D"}

            if set(self.options.keys()) != required_options:
                raise ValueError("MCQ options must contain exactly A, B, C and D")

            if self.correct_answer.strip().upper() not in required_options:
                raise ValueError("MCQ correct_answer must be A, B, C or D")

        if self.question_type == "short_answer":
            if self.options is not None:
                raise ValueError("Short-answer question must not include options")

            if not self.evaluation_rubric:
                raise ValueError("Short-answer question must include evaluation_rubric")

        return self


class GeneratedQuestionSet(BaseModel):
    questions: list[GeneratedQuestion]


class ShortAnswerEvaluation(BaseModel):
    is_correct: bool
    score: float = Field(ge=0, le=1)
    feedback: str = Field(min_length=2, max_length=1000)
    detected_weakness: SkillLabel | None = None
    confidence: ConfidenceLabel

    @model_validator(mode="after")
    def validate_weakness(self):
        if self.is_correct:
            self.detected_weakness = None

        return self


class DiagnosticSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: uuid.UUID
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


class SafeQuestionResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    question_type: str
    question_text: str
    options: dict[str, str] | None
    skill_label: str
    display_order: int
    max_score: float

    model_config = ConfigDict(from_attributes=True)


class GeneratedAssessmentResponse(BaseModel):
    session: DiagnosticSessionResponse
    questions: list[SafeQuestionResponse]
    note: str = "Questions were generated from approved retrieved topic content."


class SubmittedAnswerRequest(BaseModel):
    question_id: uuid.UUID
    student_answer: str = Field(min_length=1, max_length=2000)


class SessionSubmitRequest(BaseModel):
    answers: list[SubmittedAnswerRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def prevent_duplicate_answers(self):
        ids = [answer.question_id for answer in self.answers]

        if len(ids) != len(set(ids)):
            raise ValueError("Each question may be answered only once")

        return self


class EvaluatedAnswerResponse(BaseModel):
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
    explanation: str


class DiagnosticResultResponse(BaseModel):
    session: DiagnosticSessionResponse
    answers: list[EvaluatedAnswerResponse]
    strengths: list[str]
    weaknesses: list[str]
    completion_status: str | None
    show_checkmark: bool


class TopicStatusResponse(BaseModel):
    topic_id: uuid.UUID
    completion_status: str
    latest_score: float | None
    best_score: float | None
    strength_labels: list[str]
    weakness_labels: list[str]
    show_checkmark: bool
    completed_at: datetime | None


class SubjectSummaryResponse(BaseModel):
    subject_id: uuid.UUID
    total_topics: int
    completed_topics: int
    is_completed: bool
    strength_labels: list[str]
    weakness_labels: list[str]