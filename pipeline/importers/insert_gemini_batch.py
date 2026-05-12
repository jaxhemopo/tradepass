#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# ///
"""
Import a Gemini-authored question batch into the desktop tradepass.db source.

Usage:
    uv run pipeline/importers/insert_gemini_batch.py path/to/batch.json

Reads a JSON array of question objects (see pipeline/SCHEMA_CONVENTIONS.md for
field-level rules) and upserts into ~/Desktop/tradepass.db. Idempotent —
re-running the same batch produces the same result.

Gemini's payload uses `correct_answer: ["a","c"]` (option ids) and
`options: [{id,text},...]`. This script normalises to the existing SQLite
storage format: `options` as a plain string array, `correct_answer` as an
array of indices. No information is lost — the importer at the Supabase
boundary will re-mint stable ids.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

DB_PATH = Path.home() / "Desktop" / "tradepass.db"
ALLOWED_TYPES = {"single_choice", "multiple_select", "exact_value"}


class ValidationError(Exception):
    pass


def id_to_index(opt_id: str, options: list[dict]) -> int:
    for i, opt in enumerate(options):
        if opt.get("id") == opt_id:
            return i
    raise ValidationError(f"correct_answer references unknown option id {opt_id!r}")


def normalise(q: dict[str, Any], existing_topic_ids: set[int]) -> dict[str, Any]:
    qid = q.get("id")
    if not qid or not isinstance(qid, str):
        raise ValidationError(f"missing or invalid id: {qid!r}")

    qtype = q.get("question_type")
    if qtype not in ALLOWED_TYPES:
        raise ValidationError(f"{qid}: question_type {qtype!r} not in {ALLOWED_TYPES}")

    try:
        topic_id = int(q["topic_id"])
    except (KeyError, TypeError, ValueError) as e:
        raise ValidationError(f"{qid}: topic_id must be int-coercible") from e
    if topic_id not in existing_topic_ids:
        raise ValidationError(f"{qid}: topic_id {topic_id} not in topics table")

    question_text = q.get("question")
    if not question_text:
        raise ValidationError(f"{qid}: missing question text")

    rationale = q.get("rationale", "") or q.get("explanation", "")
    raw_options = q.get("options") or []
    raw_answer = q.get("correct_answer")

    if qtype in ("single_choice", "multiple_select"):
        if not raw_options or len(raw_options) < 2:
            raise ValidationError(f"{qid}: choice question needs at least 2 options")
        normalised_options: list[str] = []
        option_objects: list[dict] = []
        for opt in raw_options:
            if isinstance(opt, str):
                option_objects.append({"id": chr(ord("a") + len(option_objects)), "text": opt})
                normalised_options.append(opt)
            elif isinstance(opt, dict) and "text" in opt:
                option_objects.append({"id": opt.get("id", chr(ord("a") + len(option_objects))), "text": opt["text"]})
                normalised_options.append(opt["text"])
            else:
                raise ValidationError(f"{qid}: option must be string or {{id,text}} dict, got {opt!r}")

        if not isinstance(raw_answer, list) or not raw_answer:
            raise ValidationError(f"{qid}: correct_answer must be a non-empty list for {qtype}")

        if qtype == "single_choice" and len(raw_answer) != 1:
            raise ValidationError(f"{qid}: single_choice needs exactly 1 correct answer, got {len(raw_answer)}")
        if qtype == "multiple_select" and len(raw_answer) < 2:
            raise ValidationError(f"{qid}: multiple_select needs at least 2 correct answers, got {len(raw_answer)}")

        indices: list[int] = []
        for entry in raw_answer:
            if isinstance(entry, int):
                if entry < 0 or entry >= len(normalised_options):
                    raise ValidationError(f"{qid}: correct_answer index {entry} out of range")
                indices.append(entry)
            elif isinstance(entry, str):
                indices.append(id_to_index(entry, option_objects))
            else:
                raise ValidationError(f"{qid}: correct_answer entry must be int or str, got {entry!r}")
        indices.sort()

        correct_answer_json = json.dumps(indices)
        options_json = json.dumps(normalised_options, ensure_ascii=False)
        first_correct_idx = indices[0]
        answer_text = (
            normalised_options[first_correct_idx]
            if qtype == "single_choice"
            else "; ".join(normalised_options[i] for i in indices)
        )
        return {
            "id": qid,
            "topic_id": topic_id,
            "question_text": question_text,
            "answer_text": answer_text,
            "explanation": rationale,
            "options": options_json,
            "correct_answer_index": first_correct_idx,
            "correct_answer": correct_answer_json,
            "question_type": qtype,
        }

    if not isinstance(raw_answer, dict) or "answers" not in raw_answer:
        raise ValidationError(f"{qid}: exact_value correct_answer must be {{answers, unit, tolerance}}")
    answers = raw_answer["answers"]
    if not isinstance(answers, list) or not answers:
        raise ValidationError(f"{qid}: exact_value answers must be a non-empty list")
    if "tolerance" not in raw_answer:
        raise ValidationError(f"{qid}: exact_value missing tolerance")

    correct_answer_json = json.dumps(raw_answer, ensure_ascii=False)
    primary = str(answers[0])
    unit = raw_answer.get("unit", "")
    answer_text = f"{primary} {unit}".strip()
    return {
        "id": qid,
        "topic_id": topic_id,
        "question_text": question_text,
        "answer_text": answer_text,
        "explanation": rationale,
        "options": None,
        "correct_answer_index": None,
        "correct_answer": correct_answer_json,
        "question_type": qtype,
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: insert_gemini_batch.py path/to/batch.json")
    batch_path = Path(sys.argv[1])
    if not batch_path.exists():
        sys.exit(f"missing: {batch_path}")
    if not DB_PATH.exists():
        sys.exit(f"missing source db: {DB_PATH}")

    payload = json.loads(batch_path.read_text())
    if not isinstance(payload, list):
        sys.exit("batch must be a JSON array")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    topic_ids = {row["id"] for row in conn.execute("select id from topics")}

    normalised: list[dict] = []
    errors: list[str] = []
    for raw in payload:
        try:
            normalised.append(normalise(raw, topic_ids))
        except ValidationError as e:
            errors.append(str(e))

    print(f"input: {len(payload)} | valid: {len(normalised)} | invalid: {len(errors)}")
    for e in errors:
        print(f"  X {e}")
    if errors:
        sys.exit(1)

    inserted = 0
    updated = 0
    for row in normalised:
        existing = conn.execute("select id from questions where id = ?", (row["id"],)).fetchone()
        if existing:
            conn.execute(
                """
                update questions set
                    topic_id = :topic_id,
                    question_text = :question_text,
                    answer_text = :answer_text,
                    explanation = :explanation,
                    options = :options,
                    correct_answer_index = :correct_answer_index,
                    correct_answer = :correct_answer,
                    question_type = :question_type,
                    updated_at = datetime('now'),
                    is_active = 1
                where id = :id
                """,
                row,
            )
            updated += 1
        else:
            conn.execute(
                """
                insert into questions
                    (id, topic_id, question_text, answer_text, explanation,
                     options, correct_answer_index, correct_answer, question_type, is_active)
                values
                    (:id, :topic_id, :question_text, :answer_text, :explanation,
                     :options, :correct_answer_index, :correct_answer, :question_type, 1)
                """,
                row,
            )
            inserted += 1

    conn.commit()
    print(f"db: inserted {inserted}, updated {updated}, total now {conn.execute('select count(*) from questions where is_active=1').fetchone()[0]}")
    by_type = conn.execute("select question_type, count(*) as n from questions where is_active=1 group by question_type").fetchall()
    print("by type:", ", ".join(f"{r['question_type']}={r['n']}" for r in by_type))
    conn.close()


if __name__ == "__main__":
    main()
