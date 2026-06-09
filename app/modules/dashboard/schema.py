import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProgressStatsResponse(BaseModel):
    total_chapters: int
    completed_chapters: int
    needs_practice_chapters: int
    not_started_chapters: int
    completion_percentage: float


class ChapterProgressResponse(BaseModel):
    chapter_id: uuid.UUID
    chapter_no: int
    title: str
    slug: str
    completion_status: str
    latest_score: float | None
    best_score: float | None
    strength_labels: list[str]
    weakness_labels: list[str]
    show_checkmark: bool
    completed_at: datetime | None


class SubjectProgressResponse(BaseModel):
    subject_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    display_order: int
    stats: ProgressStatsResponse
    chapters: list[ChapterProgressResponse] = Field(default_factory=list)


class GradeProgressResponse(BaseModel):
    grade_id: uuid.UUID
    name: str
    slug: str
    display_order: int
    stats: ProgressStatsResponse
    subjects: list[SubjectProgressResponse] = Field(default_factory=list)


class ContinueLearningResponse(BaseModel):
    grade_id: uuid.UUID
    grade_name: str
    subject_id: uuid.UUID
    subject_name: str
    chapter_id: uuid.UUID
    chapter_no: int
    chapter_title: str
    completion_status: str


class RecentDiagnosticSessionResponse(BaseModel):
    session_id: uuid.UUID
    chapter_id: uuid.UUID
    assessment_type: str
    status: str
    score: float | None
    percentage: float | None
    outcome: str | None
    created_at: datetime
    submitted_at: datetime | None


class DashboardOverviewResponse(BaseModel):
    stats: ProgressStatsResponse
    continue_learning: ContinueLearningResponse | None
    recent_diagnostic_sessions: list[RecentDiagnosticSessionResponse]
    grades: list[GradeProgressResponse]