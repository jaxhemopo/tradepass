from datetime import datetime, timezone

from app import sm2


def test_quality_correct_fast_is_easy():
    assert sm2.derive_quality(answered_correct=True, rated_knew_it=True, time_taken_seconds=5) == 5


def test_quality_correct_normal_is_good():
    assert sm2.derive_quality(answered_correct=True, rated_knew_it=True, time_taken_seconds=20) == 4


def test_quality_correct_slow_drops_to_3():
    assert sm2.derive_quality(answered_correct=True, rated_knew_it=True, time_taken_seconds=120) == 3


def test_quality_correct_unsure_is_3():
    assert sm2.derive_quality(answered_correct=True, rated_knew_it=False, time_taken_seconds=20) == 3


def test_quality_wrong_resets():
    assert sm2.derive_quality(answered_correct=False, rated_knew_it=True, time_taken_seconds=10) == 1
    assert sm2.derive_quality(answered_correct=False, rated_knew_it=False, time_taken_seconds=10) == 0


def test_first_correct_review_sets_interval_1():
    state = sm2.apply_review(sm2.initial_state(), quality=5)
    assert state.repetitions == 1
    assert state.interval_days == 1


def test_second_correct_review_sets_interval_6():
    s1 = sm2.apply_review(sm2.initial_state(), quality=4)
    s2 = sm2.apply_review(s1, quality=4)
    assert s2.repetitions == 2
    assert s2.interval_days == 6


def test_third_correct_review_uses_easiness():
    s1 = sm2.apply_review(sm2.initial_state(), quality=5)
    s2 = sm2.apply_review(s1, quality=5)
    s3 = sm2.apply_review(s2, quality=5)
    # 6 days * easiness (~2.6) ≈ 15-16 days
    assert s3.repetitions == 3
    assert s3.interval_days >= 15


def test_failure_resets_repetitions_and_interval():
    s1 = sm2.apply_review(sm2.initial_state(), quality=5)
    s2 = sm2.apply_review(s1, quality=5)
    fail = sm2.apply_review(s2, quality=1)
    assert fail.repetitions == 0
    assert fail.interval_days == 1


def test_easiness_floor_is_1_3():
    state = sm2.initial_state()
    for _ in range(10):
        state = sm2.apply_review(state, quality=0)
    assert state.easiness == sm2.MIN_EASINESS


def test_topic_mastery_empty_is_zero():
    assert sm2.topic_mastery([]) == 0.0


def test_topic_mastery_caps_at_target_repetitions():
    # 3 questions all at 3+ reps -> fully mastered
    assert sm2.topic_mastery([3, 5, 10]) == 1.0
    # mix
    assert sm2.topic_mastery([0, 3, 3]) == (0 + 1 + 1) / 3


def test_readiness_weighted_average():
    # topic A weight 5, fully mastered. topic B weight 2, untouched.
    # readiness = (5*1 + 2*0) / (5+2) = 5/7 ≈ 71.4
    pct = sm2.readiness_percent([(5, [3, 3, 3]), (2, [])])
    assert 71.0 <= pct <= 72.0


def test_readiness_zero_when_nothing_studied():
    pct = sm2.readiness_percent([(5, []), (3, []), (2, [])])
    assert pct == 0.0
