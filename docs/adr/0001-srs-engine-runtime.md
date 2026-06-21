# ADR-0001: SM-2 SRS engine runs on Supabase Edge Functions, not Railway/FastAPI

**Status:** Accepted
**Date:** 2026-05-07
**Deciders:** Jax Hemopo (solo)

## Context

`PROJECT_BRIEF.md` originally locked in FastAPI on Railway as the home for the
SM-2 spaced-repetition engine, with the web app on Vercel calling it over HTTP.
That brief was written before any of Pass 4 was built. With Pass 1–3a now
shipped and Pass 4 (SM-2 engine) up next, we need to commit to where the engine
actually runs before writing it.

Constraints driving the call:

- Solo dev, free-tier hosting only until there's revenue.
- Brother (target user 0) is on mobile data — every extra round-trip hurts.
- Mobile apps are planned (one per brand) and will need to consume the same
  engine. The web app cannot be the only client.
- The engine is grading cards on a study screen. It's on the user's request
  path. Cold starts are unacceptable.
- SM-2 itself is ~100 lines of pure logic. It is not ML, not heavy numerics.

## Decision

The SM-2 engine runs as **Supabase Edge Functions** (Deno/TypeScript),
co-located with Postgres in the Sydney region. FastAPI on Railway is demoted
from "request path" to "offline batch worker" — pipeline runs, Claude question
generation, reviewer scoring. None of those block a user.

The web app and (future) mobile apps both call the same edge functions. Auth
handoff is automatic via the Supabase JWT already issued at sign-in.

## Options considered

### Option A: FastAPI on Railway (the original plan)

| Dimension          | Assessment                                |
|--------------------|-------------------------------------------|
| Complexity         | Medium — two deploy targets, CORS, JWT verify in API |
| Cost               | Free tier limited; Railway sleeps free dynos |
| Latency            | High — cold starts ~5–10s, extra network hop |
| Team familiarity   | High — Python is in user's stack          |
| Mobile-readiness   | Same API works for mobile                 |

**Pros:** Engine in Python, familiar to the dev. Easy to add ML/numpy later if
the algorithm gets fancy.

**Cons:** Cold starts on free Railway are ~5–10 seconds — fatal for a study
screen. CORS and JWT verification are extra work the dev would own. Two deploy
targets to keep working. Engine isn't co-located with the DB, so every grade
operation is a network hop to FastAPI then a network hop to Supabase.

### Option B: Supabase Edge Functions for hot path, FastAPI for batch *(chosen)*

| Dimension          | Assessment                                |
|--------------------|-------------------------------------------|
| Complexity         | Low — one user-facing runtime             |
| Cost               | Generous Supabase free tier               |
| Latency            | Low — co-located with Postgres            |
| Team familiarity   | Medium — TS is in the stack already; SM-2 ports trivially |
| Mobile-readiness   | Same API works for mobile                 |

**Pros:** Single runtime for everything user-facing (Supabase). No cold starts
worth caring about. Auth is automatic — edge function receives the verified JWT
from Supabase. Engine and DB are in the same region, same network — `fetch
state → compute → write state` is one effective round-trip. Railway/FastAPI
becomes an offline worker; if it goes down, the app keeps working.

**Cons:** SM-2 lives in TS instead of Python (one-time port, ~100 lines, fully
testable). Engine code is split across two languages — but they're different
concerns (real-time grading vs batch generation), so the split is natural.
Anyone running SM-2 locally needs Deno; offset by `pnpm` already being the
team-of-one's tool.

### Option C: Server Actions in Next.js → Supabase direct

| Dimension          | Assessment                                |
|--------------------|-------------------------------------------|
| Complexity         | Lowest — no separate engine deploy        |
| Cost               | Free                                      |
| Latency            | Lowest — no extra hop                     |
| Team familiarity   | High — TS, Next.js                        |
| Mobile-readiness   | Bad — engine is locked inside the web app |

**Pros:** The simplest possible thing. No second deploy to manage.

**Cons:** SM-2 lives inside `apps/web` and is therefore reachable only via
Next.js. Mobile apps would either re-implement the algorithm (drift risk —
inevitable bugs) or call internal Next.js routes (architectural smell, web app
becomes an API for mobile). Couples the engine to a web framework it has no
business knowing about.

## Trade-off analysis

Option C is the simplest thing today but breaks the moment a second client
exists. Mobile apps are explicitly planned, so this is a known-future-pain
choice — rejected.

Option A is the "real engineer" answer and the original brief locked it in.
But Railway free-tier cold starts make the user-facing latency unacceptable on
a study screen, and the operational cost (two deploys, CORS, manual JWT
verify) buys nothing the dev needs.

Option B threads the needle. The engine lives independently of any client,
runs co-located with the data it's tightly coupled to (SM-2 is just reads and
writes against `sm2_state`), and uses the auth system already in place. The TS
port is trivial — SM-2 is pure math, no library dependencies. Python doesn't
disappear; it just stops being on the request path and continues to handle the
batch work it's actually good at.

## Consequences

**Becomes easier**

- Adding mobile apps — they call the same edge functions as the web app, no
  parallel implementation.
- Auth — JWT is validated by Supabase before the function runs.
- Free-tier hosting for MVP — no Railway hours to budget on the request path.
- Iterating on SM-2 — engine sits next to the data it reads/writes.

**Becomes harder**

- Engine code is split across two languages (TS for hot path, Python for
  batch). New devs (if any are added) need to know both.
- Local SM-2 work needs Deno installed.
- If SM-2 ever needs heavy ML/numpy work, this needs to be rethought.

**Worth revisiting if**

- A single user's card count grows past ~5,000 and edge function execution
  hits CPU/time limits.
- We want offline-first mobile (would need on-device SM-2 anyway).
- Supabase pricing changes materially against us.

## Action items

1. [ ] Port SM-2 from `apps/api/srs/` to `supabase/functions/grade-card/`
       (TypeScript / Deno).
2. [ ] Define the edge function API surface: `grade-card`, `get-readiness`,
       `get-due-cards`. Document request/response shapes in
       `packages/shared-types/`.
3. [ ] Wire the study screen and dashboard in `apps/web` to call those
       functions via the Supabase client (auth is automatic).
4. [ ] Add a thin `tests/` harness for the SM-2 logic in TS — same test cases
       that were planned for Python, just ported.
5. [ ] Deploy edge functions to the Sydney project (`jhqgbqckuvadnqdyhzyb`).
6. [ ] Update `PROJECT_BRIEF.md` "Stack" section: FastAPI + Railway move to
       "batch / pipeline only".
7. [ ] Keep `apps/api/` for the pipeline + Claude question generation. Don't
       delete it; it's getting smaller, not gone.
