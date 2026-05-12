"""TradePass / SparkyPass engine — FastAPI app.

Endpoints (all under /v1):
    POST /sessions/start     — pick N due cards, return session id + questions
    POST /reviews            — record an attempt, apply SM-2, return next due
    GET  /readiness          — weighted exam readiness % across all topics

All endpoints require an Authorization: Bearer <supabase-jwt> header.
"""

from __future__ import annotations

import logging
import secrets
import traceback
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import sm2
from .config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tradepass.engine")
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

app = FastAPI(title="TradePass Engine", version="0.1.0")
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
    # Without this, an unhandled exception bypasses CORSMiddleware in some
    # Starlette versions and the browser sees a CORS error instead of the
    # real 500. Logging the traceback also makes Railway logs actionable.
    logger.error("unhandled %s on %s %s\n%s", type(exc).__name__, request.method, request.url.path, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": f"server error: {type(exc).__name__}: {exc}"})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


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

    due_state = (
        sb.table("sm2_state")
        .select("question_id, due_date")
        .eq("user_id", user.id)
        .lte("due_date", now_iso)
        .order("due_date")
        .limit(body.limit)
        .execute()
    )
    due_question_ids = [row["question_id"] for row in (due_state.data or [])]

    questions: list[dict] = []
    if due_question_ids:
        q_resp = (
            sb.table("questions")
            .select("id, body, options, difficulty, topics(slug)")
            .in_("id", due_question_ids)
            .execute()
        )
        questions = q_resp.data or []

    if len(questions) < body.limit:
        seen_ids = (
            sb.table("sm2_state")
            .select("question_id")
            .eq("user_id", user.id)
            .execute()
        )
        seen_set = {r["question_id"] for r in (seen_ids.data or [])}
        gap = body.limit - len(questions)
        new_q_resp = (
            sb.table("questions")
            .select("id, body, options, difficulty, topics(slug)")
            .limit(gap * 4)
            .execute()
        )
        for row in new_q_resp.data or []:
            if row["id"] in seen_set or any(q["id"] == row["id"] for q in questions):
                continue
            questions.append(row)
            if len(questions) >= body.limit:
                break

    if not questions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no questions available")

    session_resp = (
        sb.table("sessions")
        .insert({"user_id": user.id, "mode": body.mode})
        .execute()
    )
    session_id = session_resp.data[0]["id"]

    def shuffled(opts: list[dict]) -> list[dict]:
        # Source data has the correct answer at position 0 every time; without
        # this, the UI would always show "A" as correct and the SRS becomes
        # useless. We preserve each option's original id (a/b/c/d) so the
        # review endpoint can still match picked_option_id to correct_answer —
        # the client renders the visible label from array index instead.
        shuffled_opts = list(opts)
        for i in range(len(shuffled_opts) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            shuffled_opts[i], shuffled_opts[j] = shuffled_opts[j], shuffled_opts[i]
        return shuffled_opts

    return StartSessionResponse(
        session_id=session_id,
        questions=[
            StudyQuestion(
                id=q["id"],
                topic_slug=(q.get("topics") or {}).get("slug", ""),
                body=q["body"],
                options=[Option(**o) for o in shuffled(q["options"])],
                difficulty=q.get("difficulty"),
            )
            for q in questions
        ],
    )


# ---------------------------------------------------------------------------
# Review (record attempt + advance SM-2)
# ---------------------------------------------------------------------------
@app.post("/v1/reviews", response_model=ReviewResponse)
def post_review(
    body: ReviewRequest,
    user: AuthedUser = Depends(authed_user),
) -> ReviewResponse:
    sb = user.client

    q_resp = (
        sb.table("questions")
        .select("id, correct_answer")
        .eq("id", body.question_id)
        .single()
        .execute()
    )
    if not q_resp.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "question not found")
    correct_answer = q_resp.data["correct_answer"]
    answered_correct = body.picked_option_id == correct_answer

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
        correct_answer=correct_answer,
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
