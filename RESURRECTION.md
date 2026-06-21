# Resurrection guide

This project was retired on 2026-06-21. Vercel, Railway, and Supabase resources were torn down. Everything needed to bring it back from zero lives in this repo.

If you're reading this in the future and want to revive SparkyPass / TradePass, this is the playbook.

## Stack at retirement

| Layer | Service | Project name | What it ran |
| --- | --- | --- | --- |
| Web | Vercel | `sparkypass` | Next.js app in `apps/web` |
| Engine | Railway | `tradepass` | FastAPI in `apps/api` (Dockerfile + Procfile + railway.json in that dir) |
| DB | Supabase | `Tradepass` (Sydney, `ap-southeast-2`) | Postgres 17 + Auth (magic-link) |
| Content source-of-truth | Local SQLite | `~/Desktop/tradepass.db` | Importer ran SQLite → Supabase |

Project IDs at retirement (no longer valid, just for reference):
- Vercel: `prj_ZiX37nbkVwswfhfJjv9VRRinVylc` (team `team_lKnvr48kPj2u1xrKGa3BtWq3`)
- Supabase: `jhqgbqckuvadnqdyhzyb`

## Step-by-step reboot

### 1. Clone

```sh
git clone https://github.com/jaxhemopo/tradepass.git
cd tradepass
pnpm install
```

Python side (engine):
```sh
cd apps/api
uv sync
```

### 2. Recreate Supabase

1. New Supabase project (any region; Sydney was original). Postgres 17 recommended to match dumps.
2. Restore schema + content seed — see `supabase/dumps/README.md`.
3. Enable Auth → Email magic-link provider.
4. Note `Project URL`, `anon key`, `publishable key`, `service role key`, and the connection-pooled `DATABASE_URL`.

### 3. Recreate Railway engine

1. New Railway project. Connect this GitHub repo, set root to `apps/api`.
2. Railway auto-detects `Dockerfile` (or `railway.json`).
3. Env vars on Railway: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` (from Supabase → Settings → API → JWT secret).
4. Deploy. Note the public URL — that becomes `NEXT_PUBLIC_API_URL` for the web app.

### 4. Recreate Vercel web app

1. New Vercel project pointing at this repo, root `apps/web`.
2. Framework preset: Next.js. `vercel.json` in that dir handles install/build.
3. Env vars on Vercel (Production + Preview):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `NEXT_PUBLIC_API_URL` (the Railway URL from step 3)
4. Deploy.

### 5. Local dev

Copy `.env.example` to `.env.local` in repo root and fill in the values from steps 2 + 3. Then:

```sh
pnpm --filter web dev          # web on http://localhost:3000
cd apps/api && uv run uvicorn app.main:app --reload   # engine on http://localhost:8000
```

### 6. Content updates

The desktop SQLite (`~/Desktop/tradepass.db`) was the source of truth. If you no longer have it:
- The 200 questions + 16 topics are preserved in `supabase/dumps/content_seed.sql`.
- To extend content without the desktop DB, edit Supabase directly and re-export the seed.
- To regenerate the desktop DB from the seed, see `pipeline/importers/` — the reverse path was never built but is straightforward.

## What was NOT preserved

- **User accounts** (`user_profiles`, 2 rows) — founder + brother, deliberately excluded.
- **Study history** (`attempts`, `sm2_state`, `sessions`, `readiness_snapshots`) — per-user, useless without the users.
- **Supabase Auth users** — recreate by signing up again.
- **`.env.local` secrets** — stored outside git. Founder should have backed these up to a password manager.
- **Live database after teardown** — Supabase project was deleted; only the dumps survive.

## Key context files

- `ONBOARDING.md` — what the product is, who it's for, state of the build at retirement
- `PROJECT_BRIEF.md` — original product brief
- `docs/adr/` — architecture decision records
- `docs/standards-references.md` — NZ/AU electrical standards the content is based on
- `pipeline/SCHEMA_CONVENTIONS.md` — content authoring rules
