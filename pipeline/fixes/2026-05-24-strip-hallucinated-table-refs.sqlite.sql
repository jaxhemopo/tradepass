-- SQLite-compatible version of 2026-05-24-strip-hallucinated-table-refs.sql
-- Apply to the local tradepass.db SQLite mirror to keep it in sync with the
-- Supabase production DB.
--
-- Notes on the port:
--   - SQLite has no `DO $$ ... $$` PL/pgSQL blocks, so the post-run sanity
--     check is expressed as a SELECT you eyeball at the end (should return 0).
--   - The `options` column is TEXT in SQLite (not jsonb), so we set raw JSON
--     strings without a `::jsonb` cast.
--   - `BEGIN; ... COMMIT;` works in SQLite — the whole thing is atomic.
--
-- How to run:
--   sqlite3 ~/Desktop/tradepass.db < pipeline/fixes/2026-05-24-strip-hallucinated-table-refs.sqlite.sql

BEGIN;

UPDATE questions SET body =
  'A 230V single-phase lighting circuit is 45 metres long and supplies a load of 6 amps. Per AS/NZS 3000 voltage drop requirements, the maximum voltage drop permitted for this circuit is:'
WHERE id = 'aa2fd6cc-5329-5f57-a484-15404a05c31d';

UPDATE questions SET body =
  'A 32A circuit protected by an MCB uses 6mm² active conductors. Per AS/NZS 3000 earthing requirements, the minimum protective conductor (CPC) size is:'
WHERE id = '71045793-7ed9-507b-98fd-c2d0b0e34ea9';

UPDATE questions SET body =
  'A circuit is protected by a Type C 32A MCB. AS/NZS 3000 specifies maximum earth fault loop impedance (Zs) for this device as 0.27Ω. The actual Zs measured is 0.31Ω. The installation:'
WHERE id = '81ef9903-1c73-5e4b-be61-c5bc82f0054a';

UPDATE questions SET body =
  'A domestic installation has 8 identical 5A lighting circuits. Per AS/NZS 3000 maximum demand rules, the maximum demand contribution of all 8 circuits is:'
WHERE id = '22c49a8f-f5c3-5624-9a1d-e82532be9e78';

UPDATE questions SET body =
  'A domestic installation includes 25 standard 10A socket-outlets. Utilizing the standard maximum demand rules from AS/NZS 3000 (socket-outlets load group), what is the calculated maximum demand for these socket-outlets?'
WHERE id = 'd9634a0a-5bdc-545d-b8ea-26562076b79d';

UPDATE questions SET body =
  'A domestic installation includes a 4.8kW electric storage hot water cylinder. Using the AS/NZS 3000 standard maximum demand method (water heater load group), calculate the maximum demand in Amperes for this water heater on a standard 230V single-phase supply. Provide your answer to one decimal place.'
WHERE id = '71db532f-0c42-5d69-b467-025d8476f565';

UPDATE questions SET body =
  'A domestic installation includes a 6.4kW electric cooktop and a 3.6kW separate wall oven. Using the AS/NZS 3000 standard maximum demand method (cooking appliances load group), calculate the maximum demand in Amperes for these cooking appliances. Assume a 230V single-phase supply and provide your answer to one decimal place.'
WHERE id = '6e5f32de-3894-5b4f-b1e0-0ad97d572ecb';

UPDATE questions SET body =
  'A domestic installation includes a 7.2kW electric wall oven and a 5.6kW induction cooktop wired on separate subcircuits. Using the AS/NZS 3000 standard maximum demand method (cooking appliances load group), calculate the combined maximum demand in Amperes for these cooking appliances on a 230V single-phase supply. Provide your answer to one decimal place.'
WHERE id = 'fc7a6786-1398-5a14-be51-2a5f5d046049';

UPDATE questions SET body =
  'A domestic kitchen installation has two separate dedicated circuits: a 3.0kW 230V wall oven and a 5.8kW 230V cooktop. According to AS/NZS 3000 maximum demand rules for cooking appliances, what is the combined maximum demand contribution of both appliances?'
WHERE id = '77a2ebff-879d-591f-a773-561600a8489f';

UPDATE questions SET body =
  'A new domestic installation features exactly 45 standard 10A socket-outlets. Using the standard maximum demand rules from AS/NZS 3000 (socket-outlets load group), calculate the total maximum demand in Amperes for these socket-outlets.'
WHERE id = '22027be3-cd3a-53cd-9f9f-21a2b7c4c7d6';

UPDATE questions SET body =
  'A single domestic installation contains 15 general lighting points. Using AS/NZS 3000 maximum demand rules, what is the calculated demand for this lighting load?'
WHERE id = 'a01bec26-39f5-576a-8e5b-c5d2f3ceb341';

UPDATE questions SET body =
  'A Type B 16A MCB protects a socket outlet circuit. AS/NZS 3000 specifies maximum Zs of 1.83Ω for this device. A measured Zs of 1.90Ω at the furthest socket means:'
WHERE id = 'd01eeec6-6c77-5814-8caa-b19ad4e22d7e';

UPDATE questions SET body =
  'According to AS/NZS 3000 maximum demand rules (domestic installations), what is the calculated maximum demand for a single 32A hard-wired cooktop?'
WHERE id = '2bc13ab9-dc6f-56e5-be37-69a70391864f';

UPDATE questions SET body =
  'According to AS/NZS 3000 maximum demand rules (non-domestic installations), how many Amperes of maximum demand must be allocated for a commercial factory lighting circuit if the total connected load of the LED luminaires is exactly 4,600 Watts on a 230V single-phase supply? Provide your exact answer.'
WHERE id = 'ae911a06-df19-5bb9-9fcd-0f60bfe4ba78';

UPDATE questions SET body =
  'AS/NZS 3000 gives different Zs limits for Type B, C, and D MCBs of the same current rating because:'
WHERE id = '1e492167-9288-5ee5-a619-5d639a598da9';

UPDATE questions SET body =
  'Under AS/NZS 3000 maximum demand rules (domestic installations), how is the maximum demand calculated for a single, thermostatically controlled storage water heater on a dedicated final sub-circuit?'
WHERE id = '2ecf32cd-9215-5839-b040-5cb865cdde6d';

UPDATE questions SET body =
  'Under AS/NZS 3000 maximum demand rules (domestic installations), how is the maximum demand calculated for the indoor lighting load?'
WHERE id = '4f73dcf2-8984-5326-84f8-65b69a611e2d';

UPDATE questions SET body =
  'Using the AS/NZS 3000 standard maximum demand method (domestic lighting load group), calculate the maximum demand in Amperes for a single-phase house containing exactly 35 standard lighting points.'
WHERE id = '6d9848d2-2a27-5eee-ad51-273c800095a9';

UPDATE questions SET body =
  'When calculating the maximum demand for a commercial office building (lighting load group, non-domestic), how is the interior lighting load assessed according to the standard method in AS/NZS 3000?'
WHERE id = '8be57a8f-8448-53e2-9114-2c53c8e1c897';

UPDATE questions SET body =
  'When testing the insulation resistance of a complete low-voltage installation (isolated from the supply), what is the minimum acceptable resistance value specified in AS/NZS 3000 when using a 500V DC tester?'
WHERE id = 'cf5c7f32-bd35-5cda-8ed6-5e84634597b8';

UPDATE questions SET options =
  '[{"id":"a","text":"Non-compliant — measured Zs must not exceed the maximum Zs value specified in AS/NZS 3000 under any circumstances"},{"id":"b","text":"Compliant because the MCB would eventually clear the fault"},{"id":"c","text":"Non-compliant but acceptable if Ze is subtracted from the measured Zs"},{"id":"d","text":"Compliant because the fault current is still sufficient to operate the MCB"}]'
WHERE id = 'd01eeec6-6c77-5814-8caa-b19ad4e22d7e';

UPDATE questions SET options =
  '[{"id":"a","text":"Type B devices have lower magnetic trip thresholds (3-5× In), meaning they require less fault current to trip instantaneously, thereby tolerating higher circuit impedance"},{"id":"b","text":"Type C devices are more sensitive and need higher Zs limits"},{"id":"c","text":"The Zs requirements only apply to Type B devices"},{"id":"d","text":"The difference is due to thermal overload characteristics only"}]'
WHERE id = '1e492167-9288-5ee5-a619-5d639a598da9';

COMMIT;

-- Post-run sanity check. Both of these SELECTs should return 0.
-- (No DO block in SQLite, so eyeball the output.)
SELECT 'bad_bodies' AS check_name, COUNT(*) AS hits
FROM questions
WHERE id IN (
  'aa2fd6cc-5329-5f57-a484-15404a05c31d','71045793-7ed9-507b-98fd-c2d0b0e34ea9',
  '81ef9903-1c73-5e4b-be61-c5bc82f0054a','22c49a8f-f5c3-5624-9a1d-e82532be9e78',
  'd9634a0a-5bdc-545d-b8ea-26562076b79d','71db532f-0c42-5d69-b467-025d8476f565',
  '6e5f32de-3894-5b4f-b1e0-0ad97d572ecb','fc7a6786-1398-5a14-be51-2a5f5d046049',
  '77a2ebff-879d-591f-a773-561600a8489f','22027be3-cd3a-53cd-9f9f-21a2b7c4c7d6',
  'a01bec26-39f5-576a-8e5b-c5d2f3ceb341','d01eeec6-6c77-5814-8caa-b19ad4e22d7e',
  '2bc13ab9-dc6f-56e5-be37-69a70391864f','ae911a06-df19-5bb9-9fcd-0f60bfe4ba78',
  '1e492167-9288-5ee5-a619-5d639a598da9','2ecf32cd-9215-5839-b040-5cb865cdde6d',
  '4f73dcf2-8984-5326-84f8-65b69a611e2d','6d9848d2-2a27-5eee-ad51-273c800095a9',
  '8be57a8f-8448-53e2-9114-2c53c8e1c897','cf5c7f32-bd35-5cda-8ed6-5e84634597b8'
) AND (body LIKE '%Table %' OR body LIKE '%table %' OR body LIKE '%Clause 4.2%');

SELECT 'bad_options' AS check_name, COUNT(*) AS hits
FROM questions
WHERE id IN (
  'd01eeec6-6c77-5814-8caa-b19ad4e22d7e','1e492167-9288-5ee5-a619-5d639a598da9'
) AND (options LIKE '%Table %' OR options LIKE '%table %');
