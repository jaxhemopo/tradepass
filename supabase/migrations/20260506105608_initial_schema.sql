-- Initial schema for TradePass / SparkyPass.
-- Engine tables (topics, questions, attempts, sm2_state, sessions, streaks,
-- flags, bookmarks) are trade-agnostic. Content (NZ EWRB regulations etc.)
-- lives in topics.brand_scope + topics.regulation_refs and the question rows
-- themselves — never in column or table names.

set check_function_bodies = off;

-- ---------------------------------------------------------------------------
-- Helper: bump updated_at on row update.
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- user_profiles — one row per auth user.
-- ---------------------------------------------------------------------------
create table public.user_profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  display_name  text,
  exam_booked   boolean not null default false,
  exam_date     date,
  daily_goal    integer not null default 20 check (daily_goal between 1 and 500),
  brand         text not null default 'sparkypass',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create trigger user_profiles_set_updated_at
  before update on public.user_profiles
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- topics — one row per topic, scoped by brand (e.g. 'nz-sparky').
-- ---------------------------------------------------------------------------
create table public.topics (
  id                uuid primary key default gen_random_uuid(),
  slug              text not null,
  name              text not null,
  brand_scope       text not null,
  regulation_refs   jsonb not null default '[]'::jsonb,
  created_at        timestamptz not null default now(),
  unique (brand_scope, slug)
);

create index topics_brand_scope_idx on public.topics (brand_scope);

-- ---------------------------------------------------------------------------
-- questions — multi-choice questions tied to a topic.
-- options is jsonb array: [{"id":"a","text":"..."}, ...]
-- correct_answer matches one of the option ids.
-- variants_of self-refs the canonical question for variant families.
-- ---------------------------------------------------------------------------
create table public.questions (
  id                  uuid primary key default gen_random_uuid(),
  topic_id            uuid not null references public.topics(id) on delete cascade,
  body                text not null,
  options             jsonb not null,
  correct_answer      text not null,
  explanation         text,
  regulation_clause   text,
  difficulty          smallint check (difficulty between 1 and 5),
  variants_of         uuid references public.questions(id) on delete set null,
  created_at          timestamptz not null default now()
);

create index questions_topic_id_idx on public.questions (topic_id);
create index questions_variants_of_idx on public.questions (variants_of)
  where variants_of is not null;

-- ---------------------------------------------------------------------------
-- attempts — every answer the user gives. Drives SM-2 and analytics.
-- rated_knew_it is the explicit "Knew it ✓ / Didn't know ✗" binary;
-- the engine combines it with timing/streak signals to derive SM-2 quality.
-- ---------------------------------------------------------------------------
create table public.attempts (
  id                    uuid primary key default gen_random_uuid(),
  user_id               uuid not null references auth.users(id) on delete cascade,
  question_id           uuid not null references public.questions(id) on delete cascade,
  answered_correct      boolean not null,
  time_taken_seconds    integer not null check (time_taken_seconds >= 0),
  rated_knew_it         boolean not null,
  created_at            timestamptz not null default now()
);

create index attempts_user_created_idx on public.attempts (user_id, created_at desc);
create index attempts_user_question_idx on public.attempts (user_id, question_id);

-- ---------------------------------------------------------------------------
-- sm2_state — SM-2 spaced repetition state per (user, question).
-- One row per pair; updated after each attempt.
-- ---------------------------------------------------------------------------
create table public.sm2_state (
  user_id           uuid not null references auth.users(id) on delete cascade,
  question_id       uuid not null references public.questions(id) on delete cascade,
  easiness          real not null default 2.5 check (easiness >= 1.3),
  interval_days     integer not null default 0 check (interval_days >= 0),
  repetitions       integer not null default 0 check (repetitions >= 0),
  due_date          timestamptz not null default now(),
  last_reviewed_at  timestamptz,
  updated_at        timestamptz not null default now(),
  primary key (user_id, question_id)
);

create index sm2_state_user_due_idx on public.sm2_state (user_id, due_date);

create trigger sm2_state_set_updated_at
  before update on public.sm2_state
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- sessions — a study/mock-exam/diagnostic session.
-- ---------------------------------------------------------------------------
create table public.sessions (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  mode        text not null check (mode in ('study', 'mock_exam', 'diagnostic')),
  started_at  timestamptz not null default now(),
  ended_at    timestamptz,
  score       real check (score is null or (score >= 0 and score <= 1))
);

create index sessions_user_started_idx on public.sessions (user_id, started_at desc);

-- ---------------------------------------------------------------------------
-- streaks — one row per user. Created on first activity.
-- ---------------------------------------------------------------------------
create table public.streaks (
  user_id          uuid primary key references auth.users(id) on delete cascade,
  current_streak   integer not null default 0 check (current_streak >= 0),
  longest_streak   integer not null default 0 check (longest_streak >= 0),
  freeze_tokens    integer not null default 0 check (freeze_tokens >= 0),
  last_active      date,
  updated_at       timestamptz not null default now()
);

create trigger streaks_set_updated_at
  before update on public.streaks
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- flags — user has flagged a question for exam-prep review (⭐).
-- ---------------------------------------------------------------------------
create table public.flags (
  user_id      uuid not null references auth.users(id) on delete cascade,
  question_id  uuid not null references public.questions(id) on delete cascade,
  created_at   timestamptz not null default now(),
  primary key (user_id, question_id)
);

-- ---------------------------------------------------------------------------
-- bookmarks — user has saved a question.
-- ---------------------------------------------------------------------------
create table public.bookmarks (
  user_id      uuid not null references auth.users(id) on delete cascade,
  question_id  uuid not null references public.questions(id) on delete cascade,
  created_at   timestamptz not null default now(),
  primary key (user_id, question_id)
);

-- ===========================================================================
-- Row Level Security
-- ===========================================================================

alter table public.user_profiles enable row level security;
alter table public.topics        enable row level security;
alter table public.questions     enable row level security;
alter table public.attempts      enable row level security;
alter table public.sm2_state     enable row level security;
alter table public.sessions      enable row level security;
alter table public.streaks       enable row level security;
alter table public.flags         enable row level security;
alter table public.bookmarks     enable row level security;

-- Content (topics, questions): readable by any authenticated user.
-- Writes are restricted to the service role (used by pipeline importer);
-- no policy granted means non-service-role writes are denied.
create policy topics_read_authenticated on public.topics
  for select to authenticated using (true);

create policy questions_read_authenticated on public.questions
  for select to authenticated using (true);

-- user_profiles: own row only.
create policy user_profiles_self_select on public.user_profiles
  for select to authenticated using (auth.uid() = id);
create policy user_profiles_self_insert on public.user_profiles
  for insert to authenticated with check (auth.uid() = id);
create policy user_profiles_self_update on public.user_profiles
  for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);

-- attempts: own rows only.
create policy attempts_self_select on public.attempts
  for select to authenticated using (auth.uid() = user_id);
create policy attempts_self_insert on public.attempts
  for insert to authenticated with check (auth.uid() = user_id);

-- sm2_state: own rows only.
create policy sm2_state_self_select on public.sm2_state
  for select to authenticated using (auth.uid() = user_id);
create policy sm2_state_self_insert on public.sm2_state
  for insert to authenticated with check (auth.uid() = user_id);
create policy sm2_state_self_update on public.sm2_state
  for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- sessions: own rows only.
create policy sessions_self_select on public.sessions
  for select to authenticated using (auth.uid() = user_id);
create policy sessions_self_insert on public.sessions
  for insert to authenticated with check (auth.uid() = user_id);
create policy sessions_self_update on public.sessions
  for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- streaks: own row only.
create policy streaks_self_select on public.streaks
  for select to authenticated using (auth.uid() = user_id);
create policy streaks_self_insert on public.streaks
  for insert to authenticated with check (auth.uid() = user_id);
create policy streaks_self_update on public.streaks
  for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- flags: own rows only.
create policy flags_self_select on public.flags
  for select to authenticated using (auth.uid() = user_id);
create policy flags_self_insert on public.flags
  for insert to authenticated with check (auth.uid() = user_id);
create policy flags_self_delete on public.flags
  for delete to authenticated using (auth.uid() = user_id);

-- bookmarks: own rows only.
create policy bookmarks_self_select on public.bookmarks
  for select to authenticated using (auth.uid() = user_id);
create policy bookmarks_self_insert on public.bookmarks
  for insert to authenticated with check (auth.uid() = user_id);
create policy bookmarks_self_delete on public.bookmarks
  for delete to authenticated using (auth.uid() = user_id);
