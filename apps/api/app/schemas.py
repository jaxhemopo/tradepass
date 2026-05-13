from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

QuestionType = str  # 'single_choice' | 'multiple_select' | 'exact_value'


class Option(BaseModel):
    id: str
    text: str


class StudyQuestion(BaseModel):
    id: str
    topic_slug: str
    question_type: QuestionType
    body: str
    options: list[Option] | None = None
    difficulty: int | None = None
    # exact_value only: surfaced as a display hint next to the input box.
    unit: str | None = None


class StartSessionRequest(BaseModel):
    mode: str = Field(default="study", pattern="^(study|mock_exam|diagnostic)$")
    limit: int = Field(default=10, ge=1, le=10)


class StartSessionResponse(BaseModel):
    session_id: str
    questions: list[StudyQuestion]


class ReviewRequest(BaseModel):
    question_id: str
    session_id: str | None = None
    picked_answer: str | list[str]
    rated_knew_it: bool
    time_taken_seconds: int = Field(ge=0, le=3600)


class ReviewResponse(BaseModel):
    correct_answer: Any
    answered_correct: bool
    quality: int
    repetitions: int
    interval_days: int
    due_date: datetime
    # End-of-session recap renders these for missed questions; in-session
    # reveal deliberately ignores them to keep testing free of spoilers.
    explanation: str | None = None
    regulation_clause: str | None = None


class TopicReadiness(BaseModel):
    slug: str
    name: str
    weight: int
    questions_seen: int
    mastery_percent: float


class ReadinessHistoryPoint(BaseModel):
    date: date
    readiness_percent: float


class ReadinessResponse(BaseModel):
    readiness_percent: float
    questions_due_now: int
    reviewed_today: int
    daily_goal: int
    mastered_count: int
    total_questions: int
    change_7d: float | None
    history: list[ReadinessHistoryPoint]
    topics: list[TopicReadiness]


class Profile(BaseModel):
    user_id: str
    email: str | None
    display_name: str | None
    daily_goal: int


class ProfileUpdate(BaseModel):
    daily_goal: int | None = Field(default=None, ge=5, le=50)
    display_name: str | None = None


class ReportRequest(BaseModel):
    question_id: str
    reason: str = Field(pattern="^(contradiction|incorrect|unclear|other)$")
    details: str | None = Field(default=None, max_length=2000)


class ReportResponse(BaseModel):
    id: str
