# Supabase dumps

Frozen snapshot taken at retirement. Use these to rebuild the database from scratch.

## Files

- `schema.sql` — full `public` schema DDL (tables, indexes, constraints, functions, triggers). Authoritative; supersedes `supabase/migrations/` if they ever drift.
- `content_seed.sql` — data-only `INSERT`s for `topics` (16 rows) and `questions` (200 rows). User-PII tables (`user_profiles`, `attempts`, `sm2_state`, `sessions`, `readiness_snapshots`) deliberately excluded.

## Restore (new Supabase project)

```sh
# 1. Get the DATABASE_URL of the new project from Supabase dashboard.
export DATABASE_URL='postgresql://postgres.<ref>:<password>@<host>:6543/postgres'

# 2. Apply schema.
psql "$DATABASE_URL" -f supabase/dumps/schema.sql

# 3. Seed content. --single-transaction handles the questions self-FK warning.
psql "$DATABASE_URL" --single-transaction -f supabase/dumps/content_seed.sql
```

If the seed fails on the self-referencing FK, wrap it manually:

```sql
BEGIN;
SET CONSTRAINTS ALL DEFERRED;
\i supabase/dumps/content_seed.sql
COMMIT;
```
