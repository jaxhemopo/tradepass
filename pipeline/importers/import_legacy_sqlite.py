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
- Skips legacy users / progress / sessions / etc — content only
- All topics imported under brand_scope='nz-sparky'
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DB = REPO_ROOT / "pipeline" / "seed" / "tradepass-legacy.db"
ENV_FILE = REPO_ROOT / ".env.local"

# Stable namespace so uuid5(legacy_id) is reproducible across runs.
LEGACY_NS = uuid.UUID("a3c5b8e9-0001-5678-90ab-cdef12345678")
BRAND_SCOPE = "nz-sparky"

DIFFICULTY_MAP = {"easy": 2, "medium": 3, "hard": 4}
OPTION_IDS = ["a", "b", "c", "d", "e", "f"]


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


def transform_options(raw: str | None) -> list[dict[str, str]]:
    if not raw:
        return []
    items = json.loads(raw)
    return [{"id": OPTION_IDS[i], "text": str(text)} for i, text in enumerate(items)]


def correct_answer_letter(idx: int | None) -> str | None:
    if idx is None or idx < 0 or idx >= len(OPTION_IDS):
        return None
    return OPTION_IDS[idx]


def main() -> None:
    if not LEGACY_DB.exists():
        sys.exit(f"missing legacy DB at {LEGACY_DB}")

    db_url = load_database_url()
    src = sqlite3.connect(LEGACY_DB)
    src.row_factory = sqlite3.Row

    legacy_topics = src.execute(
        "select id, name, slug, weight from topics order by id"
    ).fetchall()
    legacy_questions = src.execute(
        """
        select id, topic_id, question_text, answer_text, options, correct_answer_index,
               explanation, reference_clause, difficulty
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
        options = transform_options(row["options"])
        if not options:
            skipped.append((row["id"], "no options"))
            continue
        idx = row["correct_answer_index"]
        if idx is None or (isinstance(idx, str) and idx.strip() == ""):
            answer_text = (row["answer_text"] or "").strip()
            for i, opt in enumerate(options):
                if opt["text"].strip() == answer_text:
                    idx = i
                    break
        correct = correct_answer_letter(idx if isinstance(idx, int) else None)
        if correct is None or correct not in {o["id"] for o in options}:
            skipped.append((row["id"], f"could not resolve correct answer (idx={row['correct_answer_index']!r})"))
            continue
        difficulty = DIFFICULTY_MAP.get((row["difficulty"] or "medium").lower(), 3)
        question_rows.append((
            str(question_uuid(row["id"])),
            str(topic_uuid(slug)),
            row["question_text"],
            json.dumps(options),
            correct,
            row["explanation"],
            row["reference_clause"],
            difficulty,
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
                (id, topic_id, body, options, correct_answer, explanation, regulation_clause, difficulty)
            values (%s, %s, %s, %s::jsonb, %s, %s, %s, %s)
            on conflict (id) do update set
                topic_id = excluded.topic_id,
                body = excluded.body,
                options = excluded.options,
                correct_answer = excluded.correct_answer,
                explanation = excluded.explanation,
                regulation_clause = excluded.regulation_clause,
                difficulty = excluded.difficulty
            """,
            question_rows,
        )
        conn.commit()

    print(f"imported: {len(topic_rows)} topics, {len(question_rows)} questions")
    if skipped:
        print(f"skipped {len(skipped)} questions:")
        for qid, reason in skipped:
            print(f"  {qid}: {reason}")


if __name__ == "__main__":
    main()
