-- topics.weight powers the Exam Readiness % calculation:
-- the weighted average of per-topic mastery, where weight reflects how heavily
-- the EWRB exam tests each topic.
alter table public.topics
  add column weight smallint not null default 1 check (weight between 1 and 10);
