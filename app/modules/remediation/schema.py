import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LanguageCode = Literal["en", "bn"]
NextAction = Literal["continue", "retry", "practice_more", "move_back"]


class RemediationGenerateRequest(BaseModel):
    language: LanguageCode = "en"
    weakness_label: str | None = Field(default=None, min_length=2, max_length=120)


class RemediationGeneratedContent(BaseModel):
    weakness_statement: str = Field(min_length=5, max_length=1500)
    micro_lesson: str = Field(min_length=10, max_length=3000)
    guided_example: str = Field(min_length=10, max_length=3000)
    partially_solved_problem: str = Field(min_length=10, max_length=3000)
    recheck_question: str = Field(min_length=5, max_length=1500)
    expected_answer: str = Field(min_length=2, max_length=1500)
    next_action: NextAction


class RemediationRecheckRequest(BaseModel):
    student_answer: str = Field(min_length=1, max_length=2000)


class RemediationRecheckEvaluation(BaseModel):
    is_correct: bool
    score: float = Field(ge=0, le=1)
    feedback: str = Field(min_length=2, max_length=1500)
    next_action: NextAction

    @model_validator(mode="after")
    def normalize_next_action(self):
        if self.is_correct:
            self.next_action = "continue"
        elif self.next_action == "continue":
            self.next_action = "retry"

        return self


class RemediationSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    chapter_id: uuid.UUID
    diagnostic_session_id: uuid.UUID
    weakness_label: str
    language: str
    status: str
    is_source_grounded: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RemediationContentResponse(BaseModel):
    id: uuid.UUID
    remediation_session_id: uuid.UUID
    weakness_statement: str
    micro_lesson: str
    guided_example: str
    partially_solved_problem: str
    recheck_question: str
    expected_answer: str
    next_action: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RemediationRecheckResponse(BaseModel):
    id: uuid.UUID
    remediation_session_id: uuid.UUID
    student_answer: str
    is_correct: bool
    score: float
    feedback: str
    next_action: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RemediationDetailResponse(BaseModel):
    session: RemediationSessionResponse
    content: RemediationContentResponse
    rechecks: list[RemediationRecheckResponse] = Field(default_factory=list)


class RemediationListResponse(BaseModel):
    sessions: list[RemediationSessionResponse]


class DeleteRemediationResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str