# Source DB Conventions — `tradepass.db`

The desktop SQLite file is the source of truth that the content agent populates.
The Supabase importer reads from it via `pipeline/importers/import_legacy_sqlite.py`.

## `questions` columns (as of 2026-05-12)

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT | `tp-NNN`, zero-padded so sort order matches insertion order |
| `topic_id` | INTEGER | FK to `topics.id` |
| `question_text` | TEXT | The question body |
| `answer_text` | TEXT | Human-readable canonical answer (for explanation, not used by engine) |
| `options` | TEXT (JSON) | JSON array of strings; **null** for `exact_value` |
| `correct_answer_index` | INTEGER | Legacy: index into `options` for `single_choice` only. Leave NULL for new types. |
| `correct_answer` | TEXT (JSON) | **Authoritative.** See "Encoding by question_type" below. |
| `explanation` | TEXT | Per-option reasoning |
| `reference_clause` | TEXT | e.g. `AS/NZS 3000:2018 Clause 3.6.2(a)` |
| `difficulty` | TEXT | `easy` / `medium` / `hard` |
| `question_type` | TEXT | `single_choice` / `multiple_select` / `exact_value` |
| `is_active` | INTEGER | 1 to include in seed import |

## Encoding `correct_answer` by `question_type`

### `single_choice`
- `options`: 4 strings.
- `correct_answer`: JSON array containing one zero-based index, e.g. `[0]`, `[2]`.
- (Optional) set `correct_answer_index` to the same int for legacy compatibility.

```json
options          = ["11.5V (5%)", "16.1V (7%)", "9.2V (4%)", "23V (10%)"]
correct_answer   = [0]
```

### `multiple_select`
- `options`: 4–6 strings.
- `correct_answer`: JSON array of 2–3 zero-based indices, e.g. `[0, 2]`.
- Order within the array doesn't matter — engine compares as a set.

```json
options          = ["Cable must be sized for fault current", "Trip time must be ≤ 0.4s for socket outlets", "Cable insulation must be PVC", "Earthing must be effective"]
correct_answer   = [0, 1, 3]
```

### `exact_value`
- `options`: **null**.
- `correct_answer`: JSON object with `answers`, `unit`, `tolerance`.
  - `answers`: array of accepted string values (handles synonyms like `"11.5"` and `"11.50"`).
  - `unit`: display unit, e.g. `"V"`, `"A"`, `"%"`. Engine strips this from user input before comparing.
  - `tolerance`: fractional tolerance (e.g. `0.05` = ±5%) for numeric matching.

```json
options          = null
correct_answer   = {"answers": ["11.5"], "unit": "V", "tolerance": 0.05}
```

## Authoring rules

1. **For new `single_choice` questions, don't always put the correct answer at index 0.** Mix it up. The Supabase importer translates to id-based references so option order is shuffled at runtime regardless, but starting with varied positions makes the source data more honest.
2. **`correct_answer` is authoritative.** New importer logic will read it first, fall back to `correct_answer_index` only if absent.
3. **Topic IDs**: existing 16 topics 1–16. Add new topics only when a question genuinely doesn't fit — don't shoehorn.
4. **JSON escaping**: strings inside the `options` array MUST escape inner quotes as `\"` (single backslash + quote), never `\\"` (we hit that bug once on `tp-103`).

## Session composition rule (founder requirement, locked-in)

When the engine builds a 10-question study session, it must include **≥2 advanced-type questions** (multi-select or exact-value) when any are available. Engine implementation is pending.
