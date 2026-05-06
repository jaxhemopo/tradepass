-- Pin search_path on the set_updated_at trigger function.
-- Resolves Supabase advisor warning 0011 (function_search_path_mutable):
-- a function with a mutable search_path can be hijacked by a malicious user
-- creating shadowing objects in a writable schema.

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog, pg_temp
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
