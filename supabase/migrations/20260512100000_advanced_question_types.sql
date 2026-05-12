-- Extend questions schema for Aspeq-style mixed question formats.
--
-- New format:
--   single_choice    options=[{id,text}], correct_answer=["a"]
--   multiple_select  options=[{id,text}], correct_answer=["a","c"]
--   exact_value      options=NULL,        correct_answer={answers,unit,tolerance}

alter table public.questions
  add column question_type text not null default 'single_choice'
  check (question_type in ('single_choice', 'multiple_select', 'exact_value'));

-- Existing correct_answer was a single option id like 'a'. Convert to a JSONB
-- array so the same column can hold single_choice (["a"]), multiple_select
-- (["a","c"]), or exact_value ({answers, unit, tolerance}).
alter table public.questions
  alter column correct_answer type jsonb
  using to_jsonb(array[correct_answer]);

-- exact_value questions have no multiple-choice options.
alter table public.questions
  alter column options drop not null;

-- For analytics + replay: store the raw user submission.
alter table public.attempts
  add column picked_answer jsonb;
