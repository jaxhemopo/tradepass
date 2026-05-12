#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "psycopg[binary]>=3.2",
# ]
# ///
"""
Import topics + questions from the legacy SparkyPass SQLite DB into Supabase.

Run from repo root:
    uv run pipeline/importers/import_legacy_sqlite.py

- Reads pipeline/seed/tradepass-legacy.db
- Connects to Supabase via DATABASE_URL in .env.local at repo root
- Generates deterministic uuid5 IDs so re-runs are idempotent (upsert)
- All topics imported under brand_scope='nz-sparky'

Handles three question_types per pipeline/SCHEMA_CONVENTIONS.md:
  single_choice    options=[{id,text}], correct_answer=["a"]
  multiple_select  options=[{id,text}], correct_answer=["a","c"]
  exact_value      options=NULL,        correct_answer={answers,unit,tolerance}
"""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DB = REPO_ROOT / "pipeline" / "seed" / "tradepass-legacy.db"
ENV_FILE = REPO_ROOT / ".env.local"

LEGACY_NS = uuid.UUID("a3c5b8e9-0001-5678-90ab-cdef12345678")
BRAND_SCOPE = "nz-sparky"

DIFFICULTY_MAP = {"easy": 2, "medium": 3, "hard": 4}
OPTION_IDS = ["a", "b", "c", "d", "e", "f"]
ALLOWED_TYPES = {"single_choice", "multiple_select", "exact_value"}


def load_database_url() -> str:
    if not ENV_FILE.exists():
        sys.exit(f"missing {ENV_FILE} — need DATABASE_URL")
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            value = line.split("=", 1)[1]
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value
    sys.exit("DATABASE_URL not found in .env.local")


def topic_uuid(slug: str) -> uuid.UUID:
    return uuid.uuid5(LEGACY_NS, f"topic:{BRAND_SCOPE}:{slug}")


def question_uuid(legacy_id: str) -> uuid.UUID:
    return uuid.uuid5(LEGACY_NS, f"question:{legacy_id}")


def parse_options_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        items = json.loads(raw.replace('\\\\"', '\\"'))
    out: list[str] = []
    for item in items:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and "text" in item:
            out.append(str(item["text"]))
        else:
            raise ValueError(f"unrecognised option shape: {item!r}")
    return out


def to_option_objects(texts: list[str]) -> list[dict[str, str]]:
    return [{"id": OPTION_IDS[i], "text": t} for i, t in enumerate(texts)]


def parse_correct_answer(
    raw: str | None,
    legacy_index: int | None,
    qtype: str,
    n_options: int,
    answer_text: str,
    option_texts: list[str],
) -> dict | list[str] | None:
    """Translate the SQLite-stored correct_answer into Supabase's jsonb format."""
    if qtype == "exact_value":
        if not raw:
            return None
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or "answers" not in parsed:
            return None
        return parsed

    indices: list[int] | None = None
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list) and all(isinstance(x, int) for x in parsed):
            indices = parsed
        elif isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            # Already id-form (e.g. ["a","c"]); accept as-is.
            return parsed

    if indices is None and legacy_index is not None and isinstance(legacy_index, int):
        indices = [legacy_index]

    if indices is None:
        # Final fallback: match answer_text against options[0].
        stripped = (answer_text or "").strip()
        for i, t in enumerate(option_texts):
            if t.strip() == stripped:
                indices = [i]
                break

    if indices is None:
        return None

    ids: list[str] = []
    for i in indices:
        if 0 <= i < n_options:
            ids.append(OPTION_IDS[i])
        else:
            return None
    return ids


def main() -> None:
    if not LEGACY_DB.exists():
        sys.exit(f"missing legacy DB at {LEGACY_DB}")

    db_url = load_database_url()
    src = sqlite3.connect(LEGACY_DB)
    src.row_factory = sqlite3.Row

    has_qtype = any(r["name"] == "question_type" for r in src.execute("pragma table_info(questions)"))
    has_ca = any(r["name"] == "correct_answer" for r in src.execute("pragma table_info(questions)"))
    if not (has_qtype and has_ca):
        sys.exit("SQLite source missing question_type / correct_answer columns — run schema upgrade first")

    legacy_topics = src.execute(
        "select id, name, slug, weight from topics order by id"
    ).fetchall()
    legacy_questions = src.execute(
        """
        select id, topic_id, question_text, answer_text, options, correct_answer_index,
               correct_answer, question_type, explanation, reference_clause, difficulty
        from questions
        where is_active = 1
        order by id
        """
    ).fetchall()

    legacy_topic_id_to_slug = {row["id"]: row["slug"] for row in legacy_topics}

    print(f"legacy: {len(legacy_topics)} topics, {len(legacy_questions)} active questions")

    skipped: list[tuple[str, str]] = []
    topic_rows: list[tuple] = []
    for row in legacy_topics:
        topic_rows.append((
            str(topic_uuid(row["slug"])),
            row["slug"],
            row["name"],
            BRAND_SCOPE,
            "[]",
            int(row["weight"]) if row["weight"] is not None else 1,
        ))

    question_rows: list[tuple] = []
    for row in legacy_questions:
        slug = legacy_topic_id_to_slug.get(row["topic_id"])
        if slug is None:
            skipped.append((row["id"], f"unknown topic_id={row['topic_id']}"))
            continue

        qtype = (row["question_type"] or "single_choice").strip()
        if qtype not in ALLOWED_TYPES:
            skipped.append((row["id"], f"unknown question_type={qtype!r}"))
            continue

        option_texts = parse_options_json(row["options"])

        if qtype == "exact_value":
            options_payload = None
            correct = parse_correct_answer(
                row["correct_answer"], None, qtype, 0, "", []
            )
            if not isinstance(correct, dict) or "answers" not in correct:
                skipped.append((row["id"], "exact_value missing answers object"))
                continue
        else:
            if not option_texts:
                skipped.append((row["id"], "choice question has no options"))
                continue
            options_payload = to_option_objects(option_texts)
            correct = parse_correct_answer(
                row["correct_answer"],
                row["correct_answer_index"] if isinstance(row["correct_answer_index"], int) else None,
                qtype,
                len(option_texts),
                row["answer_text"] or "",
                option_texts,
            )
            if not isinstance(correct, list) or not correct:
                skipped.append((row["id"], "could not resolve correct option(s)"))
                continue
            if qtype == "single_choice" and len(correct) != 1:
                skipped.append((row["id"], f"single_choice needs exactly 1 correct, got {len(correct)}"))
                continue
            if qtype == "multiple_select" and len(correct) < 2:
                skipped.append((row["id"], f"multiple_select needs ≥2 correct, got {len(correct)}"))
                continue

        difficulty = DIFFICULTY_MAP.get((row["difficulty"] or "medium").lower(), 3)
        question_rows.append((
            str(question_uuid(row["id"])),
            str(topic_uuid(slug)),
            row["question_text"],
            json.dumps(options_payload) if options_payload is not None else None,
            json.dumps(correct, ensure_ascii=False),
            row["explanation"],
            row["reference_clause"],
            difficulty,
            qtype,
        ))

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.executemany(
            """
            insert into public.topics (id, slug, name, brand_scope, regulation_refs, weight)
            values (%s, %s, %s, %s, %s::jsonb, %s)
            on conflict (brand_scope, slug) do update set
                name = excluded.name,
                weight = excluded.weight
            """,
            topic_rows,
        )
        cur.executemany(
            """
            insert into public.questions
                (id, topic_id, body, options, correct_answer, explanation,
                 regulation_clause, difficulty, question_type)
            values (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
            on conflict (id) do update set
                topic_id = excluded.topic_id,
                body = excluded.body,
                options = excluded.options,
                correct_answer = excluded.correct_answer,
                explanation = excluded.explanation,
                regulation_clause = excluded.regulation_clause,
                difficulty = excluded.difficulty,
                question_type = excluded.question_type
            """,
            question_rows,
        )
        conn.commit()

    by_type: dict[str, int] = {}
    for r in question_rows:
        by_type[r[8]] = by_type.get(r[8], 0) + 1

    print(f"imported: {len(topic_rows)} topics, {len(question_rows)} questions")
    print(f"  by type: {', '.join(f'{k}={v}' for k, v in sorted(by_type.items()))}")
    if skipped:
        print(f"skipped {len(skipped)} questions:")
        for qid, reason in skipped:
            print(f"  {qid}: {reason}")


if __name__ == "__main__":
    main()
