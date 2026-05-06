# SparkyPass / TradePass — Project Brief

> Read this first. This document captures all architectural and product decisions
> made during planning. Future Claude Code sessions should treat this as
> source-of-truth context.

## What this is

A spaced-repetition study app for trades certification exams.

- **Launch product:** SparkyPass — for NZ apprentice electricians sitting
  the EWRB (Electrical Workers Registration Board) exam.
- **Parent brand:** TradePass — the company / platform underneath.
- **Future products:** AU sparky, then plumbers, builders, gasfitters across
  NZ + AU. Architecture must support this from day one.

## The thesis

- Apprentices avoid sitting their exam because they're scared of failing,
  not because they don't know the material.
- A confidence-building study tool that tells them objectively when they're
  ready to book solves the real bottleneck.
- AI is pushing more people into trades — under-served software market.
- Build for one real user (founder's brother) → validate → templatize.

## The killer feature

**Exam Readiness %** — a single number on the home screen that reflects
the user's true readiness to pass, computed from SM-2 state across all topics.
Plus a traffic-light topic grid showing weak/strong areas. The framing is
"book your exam when you hit 75%" — removes the deadline pressure for users
who haven't booked yet (founder's brother is one of these).

## Stack (locked)

- **Monorepo:** pnpm workspaces
- **Frontend:** Next.js 15 + TypeScript + Tailwind + shadcn/ui
- **Backend:** FastAPI (Python 3.11+) + uv for deps
- **Database + auth:** Supabase (Postgres, Sydney region)
- **Hosting:** Vercel (web) + Railway (API) — free tiers
- **Linter/formatter:** Biome (replaces ESLint + Prettier)
- **Repo:** github.com/jaxhemopo/tradepass (private)

## Repo structure

tradepass/
├── apps/
│ ├── web/ # Next.js — currently SparkyPass branded
│ │ └── brand.config.ts # SparkyPass / PlumbPass / etc.
│ └── api/ # FastAPI — SRS engine, trade-agnostic
│ └── srs/ # SM-2 logic
├── packages/
│ ├── shared-types/ # zod + pydantic types
│ ├── ui/ # shadcn components
│ └── content-schema/ # JSON schema for questions
├── content/
│ ├── nz-sparky/ # NZ EWRB content (launch)
│ ├── au-sparky/ # later
│ └── nz-plumber/ # later
├── pipeline/ # Question scrape/generate/review/import
│ ├── scrapers/
│ ├── generators/
│ ├── reviewers/
│ └── importers/
├── supabase/
│ └── migrations/
├── pnpm-workspace.yaml
└── PROJECT_BRIEF.md # this file


**Key principle:** content layer (`content/`) is separated from engine (`apps/api/srs/`).
Adding a new trade or country means adding a `content/` folder, not changing engine code.

## Database schema (high level)

- `users` (Supabase auth)
- `user_profiles` — display name, exam booked y/n, exam date (nullable),
  daily goal, brand (sparkypass / plumbpass / etc.)
- `topics` — id, slug, name, brand_scope, regulation_refs
- `questions` — id, topic_id, body, options, correct_answer, explanation,
  regulation_clause, difficulty, variants_of (FK self-ref)
- `attempts` — user_id, question_id, answered_correct, time_taken_seconds,
  rated_knew_it, created_at
- `sm2_state` — user_id, question_id, easiness, interval_days,
  due_date, repetitions
- `sessions` — user_id, mode, started_at, ended_at, score
- `streaks` — user_id, current, longest, freeze_tokens, last_active
- `flags` — user_id, question_id (for ⭐ exam-prep flagging)
- `bookmarks` — user_id, question_id

## SM-2 design choices

- **2-rating UI** ("Knew it ✓" / "Didn't know ✗") — lower friction than
  Anki's 4-rating. Apprentices want to study fast.
- **4 internal signals** augment the rating:
  - Time taken to answer (fast = treat as Easy, slow = treat as Hard)
  - Consecutive correct streak per question
  - First-try vs hesitation (changed answer)
  - Plus the explicit rating
- **Algorithm maps these to SM-2's standard 0–5 quality score internally.**
- Show user "Next review: 3 days" after each card so they feel the system.

## Readiness % design

- Computed from SM-2 state across all topics for the user.
- Topic accuracy weighted by recency (recent attempts count more).
- Overdue cards decay linearly: 1 day overdue = full credit,
  7 days = 70%, 30+ days = 30%. Encourages return without punishing absences.
- Initial readiness from a 15-question diagnostic during onboarding (1–2 per topic).
- Dashboard shows: big % number + "you'll hit 75% in ~3 weeks at this pace".
- Below 75% = "not ready to book yet". 75%+ = "you'd likely pass today".

## Brand config

`apps/web/brand.config.ts` — single source of truth for current brand:
- name: "SparkyPass"
- tagline: "Pass your sparky exam with confidence"
- colors: primary, accent (TBD)
- copy tokens: "sparky", "tradie", "EWRB"
- regulations: ["AS/NZS 3000", "ESR 2010"]

Future brands swap this file. Engine code never references "sparky" or "EWRB".

## Question pipeline (separate concern)

Standalone Python tooling in `pipeline/`. Run by founder + OpenClaw agents.
Output → Supabase. Not part of the app runtime.

- Scrapers: ewrb.govt.nz, worksafe.govt.nz, legislation.govt.nz, reddit, master electricians NZ
- Generators: Claude prompts that produce 5–10 variants per regulation clause
  (numeric variation, scenario variation, framing variation, distractor quality)
- Reviewers: automated checks (citation present? answer matches body?
  difficulty calibrated?)
- Human review step (electrician advisor) before bulk import
- Importers: validated JSON → Supabase

## Pricing (planned)

- Free for first 50 users (founder's brother + beta cohort)
- Then **$49 NZD one-time, valid until you pass** (refund if you fail)
- Aligns incentive with user outcome, no subscription anxiety

## Distribution (planned)

- v1: brother's group chat + Reddit (r/electricians, r/newzealand) +
  NZ Facebook trade groups + one TikTok video
- After first testimonial: FB/IG ads ($300–500 budget to learn)
- After validation: trade school partnerships (Etco, Skills, MITO)

## Build order

- **Pass 1:** Monorepo skeleton, push to GitHub
- **Pass 2:** Supabase schema + migrations + generated types
- **Pass 3:** Auth + protected dashboard + brand config + Vercel deploy
- **Pass 4:** Port SM-2 engine + tests + Railway deploy
- **Pass 5:** Question pipeline scaffold + README for OpenClaw agents
- **Then:** onboarding flow (incl. diagnostic quiz), study screen,
  readiness dashboard, topic grid, milestones, streaks
- **Then:** brother daily-tests for 2 weeks, iterate
- **Then:** mock exam mode, notifications, beta users

## Founder context

- Solo dev, NZ-based
- Backend: Go + Python (boot.dev)
- Vibe-coded TS + Flutter previously
- Has OpenClaw agents for parallel autonomous work
- Brother is target user — sitting EWRB but hasn't booked due to fear of failing

## Working style

- Web first, mobile-responsive (no native app yet — wait for product-market fit)
- Ship in passes, founder reviews after each pass
- No premature abstractions — build for SparkyPass NZ now,
  templatize only when adding the second brand
- Keep config-driven separation between engine and content from day one
  (cheap insurance for the multi-brand future)
