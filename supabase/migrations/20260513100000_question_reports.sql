-- User-submitted content quality reports. Surfaces LLM-generation issues
-- (explanation contradicts answer, factually wrong, unclear wording) so the
-- content team can fix them. Founder queries via Supabase dashboard / MCP;
-- no admin UI built yet.

create table public.question_reports (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  reason      text not null check (reason in ('contradiction', 'incorrect', 'unclear', 'other')),
  details     text,
  resolved    boolean not null default false,
  created_at  timestamptz not null default now()
);

create index question_reports_open_idx
  on public.question_reports (created_at desc) where resolved = false;
create index question_reports_user_idx
  on public.question_reports (user_id, created_at desc);

alter table public.question_reports enable row level security;

create policy question_reports_self_insert on public.question_reports
  for insert to authenticated with check (auth.uid() = user_id);

create policy question_reports_self_select on public.question_reports
  for select to authenticated using (auth.uid() = user_id);
