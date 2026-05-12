-- easiness was 'real' (4-byte float). Python's 1.3 round-trips through
-- single precision as 1.299999952..., which fails check (easiness >= 1.3).
-- Switching to double precision matches Python's native float exactly.
alter table public.sm2_state alter column easiness type double precision;
