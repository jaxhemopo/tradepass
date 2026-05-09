from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Option(BaseModel):
    id: str
    text: str


class StudyQuestion(BaseModel):
    id: str
    topic_slug: str
    body: str
    options: list[Option]
    difficulty: int | None = None


class StartSessionRequest(BaseModel):
    mode: str = Field(default="study", pattern="^(study|mock_exam|diagnostic)$")
    limit: int = Field(default=10, ge=1, le=50)


class StartSessionResponse(BaseModel):
    session_id: str
    questions: list[StudyQuestion]


class ReviewRequest(BaseModel):
    question_id: str
    session_id: str | None = None
    picked_option_id: str
    rated_knew_it: bool
    time_taken_seconds: int = Field(ge=0, le=3600)


class ReviewResponse(BaseModel):
    correct_answer: str
    answered_correct: bool
    quality: int
    repetitions: int
    interval_days: int
    due_date: datetime


class TopicReadiness(BaseModel):
    slug: str
    name: str
    weight: int
    questions_seen: int
    mastery_percent: float


class ReadinessResponse(BaseModel):
    readiness_percent: float
    questions_due_now: int
    topics: list[TopicReadiness]
