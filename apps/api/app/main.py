"""TradePass / SparkyPass engine — FastAPI app.

Endpoints (all under /v1, JWT-protected):
    POST /sessions/start     — pick N due cards
    POST /reviews            — record an attempt, apply SM-2
    GET  /readiness          — weighted exam readiness + history + today progress
    GET  /profile            — return user_profiles row (auto-creates if absent)
    PATCH /profile           — update daily_goal / display_name
"""

from __future__ import annotations

import logging
import secrets
import traceback
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import answers, sm2
from .config import get_settings
from .deps import AuthedUser, authed_user
from .schemas import (
    Option,
    Profile,
    ProfileUpdate,
    ReadinessHistoryPoint,
    ReadinessResponse,
    ReportRequest,
    ReportResponse,
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
NZ_TZ = ZoneInfo("Pacific/Auckland")
HISTORY_DAYS = 30
DEFAULT_DAILY_GOAL = 20

app = FastAPI(title="TradePass Engine", version="0.3.0")
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


def _ensure_profile_row(sb: Any, user_id: str) -> dict:
    existing = (
        sb.table("user_profiles")
        .select("id, display_name, daily_goal")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if existing and existing.data:
        return existing.data
    inserted = (
        sb.table("user_profiles")
        .insert({"id": user_id, "daily_goal": DEFAULT_DAILY_GOAL})
        .execute()
    )
    return inserted.data[0]


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

    # Fetch a wider pool of due cards so we can reserve slots by type.
    due_state = (
        sb.table("sm2_state")
        .select("question_id, due_date")
        .eq("user_id", user.id)
        .lte("due_date", now_iso)
        .order("due_date")
        .limit(limit * 3)
        .execute()
    )
    due_question_ids = [row["question_id"] for row in (due_state.data or [])]

    due_questions: list[dict] = []
    if due_question_ids:
        q_resp = (
            sb.table("questions")
            .select(QUESTION_SELECT)
            .in_("id", due_question_ids)
            .execute()
        )
        due_order = {qid: i for i, qid in enumerate(due_question_ids)}
        due_questions = sorted(q_resp.data or [], key=lambda q: due_order.get(q["id"], 0))

    seen_resp = (
        sb.table("sm2_state")
        .select("question_id")
        .eq("user_id", user.id)
        .execute()
    )
    seen_ids = {r["question_id"] for r in (seen_resp.data or [])}

    # Compose the session with the advanced-types quota reserved up front.
    advanced_due = [q for q in due_questions if q.get("question_type") in ADVANCED_TYPES]
    basic_due = [q for q in due_questions if q.get("question_type") not in ADVANCED_TYPES]

    picked_rows: list[dict] = []
    picked_ids: list[str] = []

    for q in advanced_due[:floor]:
        picked_rows.append(q)
        picked_ids.append(q["id"])

    for q in basic_due:
        if len(picked_rows) >= limit:
            break
        picked_rows.append(q)
        picked_ids.append(q["id"])

    for q in advanced_due[floor:]:
        if len(picked_rows) >= limit:
            break
        picked_rows.append(q)
        picked_ids.append(q["id"])

    def advanced_in_session() -> int:
        return sum(1 for r in picked_rows if r.get("question_type") in ADVANCED_TYPES)

    # Top up with unseen advanced cards if we still haven't hit the floor.
    if advanced_in_session() < floor:
        adv_resp = (
            sb.table("questions")
            .select(QUESTION_SELECT)
            .in_("question_type", list(ADVANCED_TYPES))
            .limit(floor * 6)
            .execute()
        )
        existing = set(picked_ids)
        unseen_adv = [
            r for r in (adv_resp.data or []) if r["id"] not in seen_ids and r["id"] not in existing
        ]
        for q in unseen_adv:
            if advanced_in_session() >= floor:
                break
            if len(picked_rows) >= limit:
                # Drop the last basic card to make room for the advanced one.
                for i in range(len(picked_rows) - 1, -1, -1):
                    if picked_rows[i].get("question_type") not in ADVANCED_TYPES:
                        removed = picked_rows.pop(i)
                        picked_ids.remove(removed["id"])
                        break
                else:
                    break  # nothing to displace
            picked_rows.append(q)
            picked_ids.append(q["id"])

    if len(picked_rows) < limit:
        gap = limit - len(picked_rows)
        new_resp = (
            sb.table("questions")
            .select(QUESTION_SELECT)
            .limit(gap * 4)
            .execute()
        )
        existing = set(picked_ids)
        for row in new_resp.data or []:
            if row["id"] in seen_ids or row["id"] in existing:
                continue
            picked_rows.append(row)
            picked_ids.append(row["id"])
            existing.add(row["id"])
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
        .select("id, question_type, correct_answer, explanation, regulation_clause")
        .eq("id", body.question_id)
        .single()
        .execute()
    )
    if not q_resp.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "question not found")
    qtype = q_resp.data["question_type"]
    correct = q_resp.data["correct_answer"]
    explanation = q_resp.data.get("explanation")
    regulation_clause = q_resp.data.get("regulation_clause")

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
        explanation=explanation,
        regulation_clause=regulation_clause,
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

    profile_row = _ensure_profile_row(sb, user.id)
    daily_goal = int(profile_row.get("daily_goal") or DEFAULT_DAILY_GOAL)

    nz_today = datetime.now(NZ_TZ).date()
    nz_today_start_utc = datetime.combine(nz_today, datetime.min.time(), NZ_TZ).astimezone(timezone.utc)
    attempts_resp = (
        sb.table("attempts")
        .select("id", count="exact")
        .eq("user_id", user.id)
        .gte("created_at", nz_today_start_utc.isoformat())
        .execute()
    )
    reviewed_today = attempts_resp.count if attempts_resp.count is not None else len(attempts_resp.data or [])

    history_start = (nz_today - timedelta(days=HISTORY_DAYS - 1)).isoformat()
    history_resp = (
        sb.table("readiness_snapshots")
        .select("date, readiness_percent")
        .eq("user_id", user.id)
        .gte("date", history_start)
        .order("date")
        .execute()
    )
    history_rows = history_resp.data or []

    total_q_resp = (
        sb.table("questions")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )
    total_questions = total_q_resp.count or 0

    mastered_resp = (
        sb.table("sm2_state")
        .select("question_id", count="exact")
        .eq("user_id", user.id)
        .gte("repetitions", sm2.TARGET_REPETITIONS)
        .limit(1)
        .execute()
    )
    mastered_count = mastered_resp.count or 0

    if not topics:
        return ReadinessResponse(
            readiness_percent=0.0,
            questions_due_now=0,
            reviewed_today=reviewed_today,
            daily_goal=daily_goal,
            mastered_count=mastered_count,
            total_questions=total_questions,
            change_7d=None,
            history=[],
            topics=[],
        )

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
    questions_seen = 0
    for row in state_resp.data or []:
        topic_id = question_to_topic.get(row["question_id"])
        if topic_id is None:
            continue
        reps_by_topic[topic_id].append(int(row["repetitions"]))
        questions_seen += 1
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

    # Lazy snapshot for today (idempotent — overwrites if we already wrote one).
    sb.table("readiness_snapshots").upsert({
        "user_id": user.id,
        "date": nz_today.isoformat(),
        "readiness_percent": readiness,
        "questions_seen": questions_seen,
    }).execute()

    history_map: dict[str, float] = {r["date"]: float(r["readiness_percent"]) for r in history_rows}
    history_map[nz_today.isoformat()] = readiness
    history_points = [
        ReadinessHistoryPoint(date=date.fromisoformat(d), readiness_percent=v)
        for d, v in sorted(history_map.items())
    ]

    change_7d: float | None = None
    target_date = (nz_today - timedelta(days=7)).isoformat()
    if target_date in history_map:
        change_7d = round(readiness - history_map[target_date], 1)

    return ReadinessResponse(
        readiness_percent=readiness,
        questions_due_now=questions_due_now,
        reviewed_today=reviewed_today,
        daily_goal=daily_goal,
        mastered_count=mastered_count,
        total_questions=total_questions,
        change_7d=change_7d,
        history=history_points,
        topics=topic_readiness,
    )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.get("/v1/profile", response_model=Profile)
def get_profile(user: AuthedUser = Depends(authed_user)) -> Profile:
    sb = user.client
    row = _ensure_profile_row(sb, user.id)
    return Profile(
        user_id=user.id,
        email=user.email,
        display_name=row.get("display_name"),
        daily_goal=int(row.get("daily_goal") or DEFAULT_DAILY_GOAL),
    )


@app.post("/v1/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def post_report(
    body: ReportRequest,
    user: AuthedUser = Depends(authed_user),
) -> ReportResponse:
    """User-submitted content quality flag for a specific question."""
    sb = user.client
    resp = (
        sb.table("question_reports")
        .insert({
            "user_id": user.id,
            "question_id": body.question_id,
            "reason": body.reason,
            "details": (body.details or "").strip() or None,
        })
        .execute()
    )
    row = resp.data[0] if resp.data else {}
    return ReportResponse(id=str(row.get("id", "")))


@app.patch("/v1/profile", response_model=Profile)
def patch_profile(
    body: ProfileUpdate,
    user: AuthedUser = Depends(authed_user),
) -> Profile:
    sb = user.client
    _ensure_profile_row(sb, user.id)

    updates: dict[str, Any] = {}
    if body.daily_goal is not None:
        updates["daily_goal"] = body.daily_goal
    if body.display_name is not None:
        updates["display_name"] = body.display_name.strip() or None
    if not updates:
        return get_profile(user)

    resp = (
        sb.table("user_profiles")
        .update(updates)
        .eq("id", user.id)
        .execute()
    )
    row = resp.data[0] if resp.data else {}
    return Profile(
        user_id=user.id,
        email=user.email,
        display_name=row.get("display_name"),
        daily_goal=int(row.get("daily_goal") or DEFAULT_DAILY_GOAL),
    )
