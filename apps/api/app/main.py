"""TradePass / SparkyPass engine — FastAPI app.

Endpoints (all under /v1):
    POST /sessions/start     — pick N due cards, return session id + questions
    POST /reviews            — record an attempt, apply SM-2, return next due
    GET  /readiness          — weighted exam readiness % across all topics

All endpoints require an Authorization: Bearer <supabase-jwt> header.

Handles three question_types:
    single_choice    correct_answer=["a"],         options=[{id,text}]
    multiple_select  correct_answer=["a","c"],     options=[{id,text}]
    exact_value      correct_answer={answers,...}, options=NULL
"""

from __future__ import annotations

import logging
import secrets
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import answers, sm2
from .config import get_settings
from .deps import AuthedUser, authed_user
from .schemas import (
    Option,
    ReadinessResponse,
    ReviewRequest,
    ReviewResponse,
    StartSessionRequest,
    StartSessionResponse,
    StudyQuestion,
    TopicReadiness,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tradepass.engine")

ADVANCED_TYPES = {"multiple_select", "exact_value"}
ADVANCED_FLOOR_BY_MODE = {"study": 2, "mock_exam": 6, "diagnostic": 1}

app = FastAPI(title="TradePass Engine", version="0.2.0")
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_origin_regex=_settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled %s on %s %s\n%s",
        type(exc).__name__,
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": f"server error: {type(exc).__name__}: {exc}"},
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
QUESTION_SELECT = "id, body, options, difficulty, question_type, correct_answer, topics(slug)"


def _shuffled(opts: list[dict]) -> list[dict]:
    out = list(opts)
    for i in range(len(out) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def _to_study_question(q: dict[str, Any]) -> StudyQuestion:
    qtype = q.get("question_type") or "single_choice"
    raw_options = q.get("options") if qtype != "exact_value" else None
    options_payload: list[Option] | None = None
    if raw_options:
        options_payload = [Option(**o) for o in _shuffled(raw_options)]
    unit = None
    if qtype == "exact_value":
        correct = q.get("correct_answer") or {}
        if isinstance(correct, dict):
            unit = correct.get("unit")
    return StudyQuestion(
        id=q["id"],
        topic_slug=(q.get("topics") or {}).get("slug", ""),
        question_type=qtype,
        body=q["body"],
        options=options_payload,
        difficulty=q.get("difficulty"),
        unit=unit,
    )


# ---------------------------------------------------------------------------
# Session start
# ---------------------------------------------------------------------------
@app.post("/v1/sessions/start", response_model=StartSessionResponse)
def start_session(
    body: StartSessionRequest,
    user: AuthedUser = Depends(authed_user),
) -> StartSessionResponse:
    sb = user.client
    now_iso = datetime.now(timezone.utc).isoformat()
    limit = body.limit
    floor = ADVANCED_FLOOR_BY_MODE.get(body.mode, 0)

    due_state = (
        sb.table("sm2_state")
        .select("question_id, due_date")
        .eq("user_id", user.id)
        .lte("due_date", now_iso)
        .order("due_date")
        .limit(limit)
        .execute()
    )
    due_question_ids = [row["question_id"] for row in (due_state.data or [])]

    picked_ids: list[str] = []
    picked_rows: list[dict] = []
    if due_question_ids:
        q_resp = (
            sb.table("questions")
            .select(QUESTION_SELECT)
            .in_("id", due_question_ids)
            .execute()
        )
        for row in q_resp.data or []:
            picked_rows.append(row)
            picked_ids.append(row["id"])

    seen_resp = (
        sb.table("sm2_state")
        .select("question_id")
        .eq("user_id", user.id)
        .execute()
    )
    seen_ids = {r["question_id"] for r in (seen_resp.data or [])}

    def in_session(qid: str) -> bool:
        return qid in picked_ids

    advanced_count = sum(1 for r in picked_rows if r.get("question_type") in ADVANCED_TYPES)
    if advanced_count < floor and len(picked_rows) < limit:
        gap = min(floor - advanced_count, limit - len(picked_rows))
        adv_resp = (
            sb.table("questions")
            .select(QUESTION_SELECT)
            .in_("question_type", list(ADVANCED_TYPES))
            .limit(max(gap * 4, gap))
            .execute()
        )
        # Prefer cards the user hasn't seen yet, then any.
        unseen = [r for r in (adv_resp.data or []) if r["id"] not in seen_ids and not in_session(r["id"])]
        fallback = [r for r in (adv_resp.data or []) if r["id"] in seen_ids and not in_session(r["id"])]
        for row in unseen + fallback:
            picked_rows.append(row)
            picked_ids.append(row["id"])
            if len(picked_rows) >= limit:
                break
            advanced_count += 1
            if advanced_count >= floor:
                break

    if len(picked_rows) < limit:
        gap = limit - len(picked_rows)
        new_resp = (
            sb.table("questions")
            .select(QUESTION_SELECT)
            .limit(gap * 4)
            .execute()
        )
        for row in new_resp.data or []:
            if row["id"] in seen_ids or in_session(row["id"]):
                continue
            picked_rows.append(row)
            picked_ids.append(row["id"])
            if len(picked_rows) >= limit:
                break

    if not picked_rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no questions available")

    session_resp = (
        sb.table("sessions")
        .insert({"user_id": user.id, "mode": body.mode})
        .execute()
    )
    session_id = session_resp.data[0]["id"]

    return StartSessionResponse(
        session_id=session_id,
        questions=[_to_study_question(q) for q in picked_rows],
    )


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------
@app.post("/v1/reviews", response_model=ReviewResponse)
def post_review(
    body: ReviewRequest,
    user: AuthedUser = Depends(authed_user),
) -> ReviewResponse:
    sb = user.client

    q_resp = (
        sb.table("questions")
        .select("id, question_type, correct_answer")
        .eq("id", body.question_id)
        .single()
        .execute()
    )
    if not q_resp.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "question not found")
    qtype = q_resp.data["question_type"]
    correct = q_resp.data["correct_answer"]

    answered_correct = answers.is_correct(qtype, body.picked_answer, correct)
    quality = sm2.derive_quality(
        answered_correct=answered_correct,
        rated_knew_it=body.rated_knew_it,
        time_taken_seconds=body.time_taken_seconds,
    )

    sb.table("attempts").insert({
        "user_id": user.id,
        "question_id": body.question_id,
        "answered_correct": answered_correct,
        "time_taken_seconds": body.time_taken_seconds,
        "rated_knew_it": body.rated_knew_it,
        "picked_answer": body.picked_answer,
    }).execute()

    prev_resp = (
        sb.table("sm2_state")
        .select("easiness, interval_days, repetitions, due_date, last_reviewed_at")
        .eq("user_id", user.id)
        .eq("question_id", body.question_id)
        .maybe_single()
        .execute()
    )
    if prev_resp and prev_resp.data:
        prev = sm2.Sm2State(
            easiness=float(prev_resp.data["easiness"]),
            interval_days=int(prev_resp.data["interval_days"]),
            repetitions=int(prev_resp.data["repetitions"]),
            due_date=datetime.fromisoformat(prev_resp.data["due_date"].replace("Z", "+00:00")),
            last_reviewed_at=datetime.fromisoformat(
                (prev_resp.data["last_reviewed_at"] or prev_resp.data["due_date"]).replace("Z", "+00:00")
            ),
        )
    else:
        prev = sm2.initial_state()

    nxt = sm2.apply_review(prev, quality)

    sb.table("sm2_state").upsert({
        "user_id": user.id,
        "question_id": body.question_id,
        "easiness": nxt.easiness,
        "interval_days": nxt.interval_days,
        "repetitions": nxt.repetitions,
        "due_date": nxt.due_date.isoformat(),
        "last_reviewed_at": nxt.last_reviewed_at.isoformat(),
    }).execute()

    return ReviewResponse(
        correct_answer=correct,
        answered_correct=answered_correct,
        quality=quality,
        repetitions=nxt.repetitions,
        interval_days=nxt.interval_days,
        due_date=nxt.due_date,
    )


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------
@app.get("/v1/readiness", response_model=ReadinessResponse)
def get_readiness(user: AuthedUser = Depends(authed_user)) -> ReadinessResponse:
    sb = user.client

    topics_resp = (
        sb.table("topics")
        .select("id, slug, name, weight")
        .eq("brand_scope", "nz-sparky")
        .execute()
    )
    topics = topics_resp.data or []
    if not topics:
        return ReadinessResponse(readiness_percent=0.0, questions_due_now=0, topics=[])

    topic_id_to_meta = {t["id"]: t for t in topics}

    questions_resp = (
        sb.table("questions")
        .select("id, topic_id")
        .in_("topic_id", list(topic_id_to_meta.keys()))
        .execute()
    )
    question_to_topic = {q["id"]: q["topic_id"] for q in (questions_resp.data or [])}

    state_resp = (
        sb.table("sm2_state")
        .select("question_id, repetitions, due_date")
        .eq("user_id", user.id)
        .execute()
    )

    now = datetime.now(timezone.utc)
    reps_by_topic: dict[str, list[int]] = {tid: [] for tid in topic_id_to_meta}
    questions_due_now = 0
    for row in state_resp.data or []:
        topic_id = question_to_topic.get(row["question_id"])
        if topic_id is None:
            continue
        reps_by_topic[topic_id].append(int(row["repetitions"]))
        due = datetime.fromisoformat(row["due_date"].replace("Z", "+00:00"))
        if due <= now:
            questions_due_now += 1

    weighted_input = [(int(t["weight"]), reps_by_topic[t["id"]]) for t in topics]
    readiness = sm2.readiness_percent(weighted_input)

    topic_readiness = [
        TopicReadiness(
            slug=t["slug"],
            name=t["name"],
            weight=int(t["weight"]),
            questions_seen=len(reps_by_topic[t["id"]]),
            mastery_percent=round(100 * sm2.topic_mastery(reps_by_topic[t["id"]]), 1),
        )
        for t in sorted(topics, key=lambda t: (-int(t["weight"]), t["slug"]))
    ]

    return ReadinessResponse(
        readiness_percent=readiness,
        questions_due_now=questions_due_now,
        topics=topic_readiness,
    )
