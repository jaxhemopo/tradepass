-- Daily readiness snapshots power the dashboard sparkline + "Up X this week"
-- delta. Engine writes one row per user per day on /v1/readiness reads — no
-- cron needed, snapshots accumulate organically as users hit the dashboard.

create table public.readiness_snapshots (
  user_id            uuid not null references auth.users(id) on delete cascade,
  date               date not null,
  readiness_percent  double precision not null,
  questions_seen     integer not null,
  created_at         timestamptz not null default now(),
  primary key (user_id, date)
);

create index readiness_snapshots_user_date_idx
  on public.readiness_snapshots (user_id, date desc);

alter table public.readiness_snapshots enable row level security;

create policy readiness_snapshots_self_select on public.readiness_snapshots
  for select to authenticated using (auth.uid() = user_id);
create policy readiness_snapshots_self_insert on public.readiness_snapshots
  for insert to authenticated with check (auth.uid() = user_id);
create policy readiness_snapshots_self_update on public.readiness_snapshots
  for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
