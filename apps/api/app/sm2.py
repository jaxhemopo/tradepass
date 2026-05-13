"""SM-2 spaced repetition algorithm.

Quality scale (SuperMemo classic):
    5 - perfect response
    4 - correct after hesitation
    3 - correct with serious difficulty
    2 - wrong, but on reflection the answer felt familiar
    1 - wrong, full recall failure
    0 - blackout

We derive the quality from the user's binary "Knew it / Didn't" plus timing,
because forcing apprentices to grade themselves on a 6-point scale degrades
the experience without improving accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MIN_EASINESS = 1.3
DEFAULT_EASINESS = 2.5

# A question counts as mastered when correctly answered this many times in a
# spaced succession. Used by readiness mastery and the "X / Y mastered" count.
TARGET_REPETITIONS = 3

# Wall-clock budget (seconds) we use to judge "fast" vs "slow" recall.
FAST_THRESHOLD_S = 10
SLOW_THRESHOLD_S = 30


def derive_quality(
    *,
    answered_correct: bool,
    rated_knew_it: bool,
    time_taken_seconds: int,
) -> int:
    """Map the user's signals onto the SM-2 0-5 scale."""
    if not answered_correct:
        # Wrong answer always trips the SM-2 reset, regardless of rating.
        return 1 if rated_knew_it else 0
    if not rated_knew_it:
        # Got it right but second-guessed themselves — treat as "with difficulty".
        return 3
    if time_taken_seconds <= FAST_THRESHOLD_S:
        return 5
    if time_taken_seconds <= SLOW_THRESHOLD_S:
        return 4
    return 4 if time_taken_seconds <= SLOW_THRESHOLD_S * 2 else 3


@dataclass(frozen=True)
class Sm2State:
    easiness: float
    interval_days: int
    repetitions: int
    due_date: datetime
    last_reviewed_at: datetime


def initial_state(now: datetime | None = None) -> Sm2State:
    now = now or datetime.now(timezone.utc)
    return Sm2State(
        easiness=DEFAULT_EASINESS,
        interval_days=0,
        repetitions=0,
        due_date=now,
        last_reviewed_at=now,
    )


def apply_review(prev: Sm2State, quality: int, now: datetime | None = None) -> Sm2State:
    """Return the next SM-2 state after a review of the given quality."""
    if quality < 0 or quality > 5:
        raise ValueError(f"quality must be 0..5, got {quality}")
    now = now or datetime.now(timezone.utc)

    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        repetitions = prev.repetitions + 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = max(1, round(prev.interval_days * prev.easiness))

    new_easiness = prev.easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    easiness = max(MIN_EASINESS, new_easiness)

    return Sm2State(
        easiness=easiness,
        interval_days=interval_days,
        repetitions=repetitions,
        due_date=now + timedelta(days=interval_days),
        last_reviewed_at=now,
    )


def topic_mastery(repetitions_per_question: list[int], target_repetitions: int = TARGET_REPETITIONS) -> float:
    """Per-topic mastery in [0, 1].

    A question is fully mastered once the learner has answered it correctly
    `target_repetitions` times in spaced succession. Partial credit scales
    linearly. Topics with no studied questions return 0.
    """
    if not repetitions_per_question:
        return 0.0
    capped = [min(r, target_repetitions) / target_repetitions for r in repetitions_per_question]
    return sum(capped) / len(capped)


def readiness_percent(
    topics: list[tuple[int, list[int]]],
) -> float:
    """Weighted readiness across all topics.

    Args:
        topics: list of (weight, repetitions_per_question_in_topic) tuples.
                Topics with zero questions studied still pull the average down,
                because the learner hasn't proven mastery there.

    Returns:
        Readiness in [0, 100].
    """
    if not topics:
        return 0.0
    total_weight = sum(w for w, _ in topics) or 1
    weighted_mastery = sum(w * topic_mastery(reps) for w, reps in topics)
    return round(100 * weighted_mastery / total_weight, 1)
