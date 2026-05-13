# Onboarding — SparkyPass / TradePass

> Where things stand. Updated end-of-session for anyone (including you, or a future Claude) reading cold.

## What this is

A spaced-repetition study app for NZ apprentice electricians sitting the EWRB exam. The founder's brother is target user 0.

- **SparkyPass NZ** = the launch product, kept **free** as a data-acquisition play
- **SparkyPass AU + future trades/countries** = the paid products. Same engine, different content. Brand-engine separation already in the codebase.

## Live

- **Web**: https://sparkypass-nine.vercel.app (Vercel, project `kaji-hemopo-projects/sparkypass`)
- **Engine**: https://tradepass-production-0860.up.railway.app (Railway, FastAPI)
- **DB**: Supabase project `jhqgbqckuvadnqdyhzyb` (Sydney region)
- **Repo**: `github.com/jaxhemopo/tradepass`, branch `main`
- **Identity for third-party services**: `kaji.hemopo@gmail.com` (Vercel, Railway, Supabase)

Custom domain `sparkypass.nz` deliberately not set up — `*.vercel.app` is fine for the NZ test build.

## State of the build

### Content
- **200 verified questions** in Supabase: 165 single_choice / 16 multiple_select / 19 exact_value
- **16 topics** with weights 2–5 driving the readiness % calculation
- **Source of truth**: `~/Desktop/tradepass.db` (SQLite). Importer at `pipeline/importers/import_legacy_sqlite.py` syncs SQLite → Supabase.

### Engine (v0.3.x, Railway)
- `POST /v1/sessions/start` — picks ≤10 due cards, enforces ≥2 advanced-types per study session, shuffles option order per session
- `POST /v1/reviews` — accepts `picked_answer` (str | list[str]), applies SM-2, returns correctness + the **explanation + clause** (only after answer submitted)
- `GET /v1/readiness` — weighted % + history + change_7d + reviewed_today + mastered/total + daily_goal. Lazy-writes a daily snapshot to `readiness_snapshots`.
- `GET/PATCH /v1/profile` — daily_goal management (5–50)
- `POST /v1/reports` — user-submitted content quality flags
- All endpoints JWT-protected via Supabase Auth passthrough; RLS enforces row isolation.

### Web (Vercel)
- `/login` — magic-link auth via Supabase
- `/dashboard` — readiness % + sparkline + weekly delta + "Today X / goal" + "Mastered X / 200" progress + ? popovers explaining SRS and mastery
- `/study` — three question-type layouts: radio-style single, checkbox + submit multi, text-input exact-value. End-of-session recap shows explanations **only for misses, one-shot, never persisted**.
- `/settings` — daily review goal slider with educational copy about spaced repetition + sweet-spot guidance
- Brand chrome lives in `apps/web/brand.config.ts`. Multi-brand-ready.

### Content-QA workflow
- 🚩 Report button on each recap card → writes to `question_reports` table
- To triage: SQL query in `~/.claude/projects/-Users-jacksonhemopo-workspace-sparkypass/memory/project_content_qa_workflow.md`
- Discipline: when fixing a question, edit **both** Supabase and the desktop SQLite (otherwise the next importer run silently overwrites the Supabase fix)

## What I'd build next (in priority order, none urgent)

1. **Question variants for anti-memorization** — ask Gemini for 3–5 number-variants of each math/calculation question. Without variants, even SM-2 + the recap-once design can be gamed by a determined memorizer.
2. **AI audit pass** — once Gemini batch is sized up, validate every question's explanation aligns with its marked correct answer (catch contradictions like tp-018 had).
3. **Mock exam mode** — 70-question timed session matching the real Aspeq blueprint, no per-question reveal. Engine + UI both need a new mode.
4. **Streak / achievement features** — `streaks` table already exists in the schema, never written to. Daily-use motivation.
5. **AU launch** — new `topics.brand_scope='au-sparky'`, AU-specific legislation questions, Gemini content batch, separate Vercel project.

## Key files / where stuff lives

- `apps/web/app/dashboard/page.tsx` — dashboard
- `apps/web/app/study/study-client.tsx` — study + recap UI
- `apps/web/app/settings/` — settings page
- `apps/web/components/{help-popover,progress-metric,sparkline}.tsx` — reusable bits
- `apps/api/app/main.py` — engine endpoints
- `apps/api/app/answers.py` — correctness check per question type
- `apps/api/app/sm2.py` — SM-2 algorithm + mastery thresholds
- `pipeline/importers/import_legacy_sqlite.py` — desktop → Supabase sync
- `pipeline/importers/insert_gemini_batch.py` — Gemini JSON → desktop SQLite
- `pipeline/SCHEMA_CONVENTIONS.md` — content authoring rules for Gemini
- `supabase/migrations/` — every schema change

## Rollback safety

- Tag `pre-advanced-questions-2026-05-12` is on origin if we ever need to roll back the advanced-question types migration.
- Earlier desktop SQLite backups in `pipeline/seed/.archive/` (gitignored).

## Founder context

Solo NZ dev, Go/Python backgrounds, picking up Next.js as we go. Working style: confirm at decision points, ship the minimum useful thing, iterate. The brother is the real target user — he's afraid to book the EWRB exam, and the "Exam Readiness %" is the headline feature that's meant to tell him objectively when he's ready.
