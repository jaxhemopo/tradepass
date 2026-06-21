-- Strip hallucinated AS/NZS 3000 table references from question bodies.
--
-- CONTEXT: Initial Gemini batch import fabricated plausible-sounding table
-- references ("Table 3.2 (Load Group A)" for max demand etc.) that do not
-- exist in either the 2007 or 2018 edition of AS/NZS 3000. The math/concept
-- of each question is correct; only the citation is wrong. We replace the
-- bogus citation with a generic topic-area phrase so candidates use their
-- copy of the Standard's index instead of hunting for a non-existent table.
--
-- VERIFICATION: cross-checked against AS/NZS 3000:2007 (full text) and the
-- AS/NZS 3000:2018 TOC. See docs/standards-references.md for the authoritative
-- table titles and edition differences.
--
-- SCOPE: 20 questions. The following 6 matched the broader scan but were
-- left UNCHANGED because their references are valid:
--   843914fb — Table 3.4 (conductor colours)             — correct
--   39645464 — Table 5.2 (acceptable earth electrodes)   — correct
--   d403bf6f — "Section 4" clearance (generic, valid)
--   ca7fa498 — "Section 4" clearance (generic, valid)
--   0e147256 — "Section 6" IP rating (generic, valid)
--   4ad7d5a3 — Electricity Act 1992 s.79 + ECP 51        — real legal refs
--
-- HOW TO RUN: review diffs below, then execute against the Tradepass DB.
--   psql "$DATABASE_URL" -f pipeline/fixes/2026-05-24-strip-hallucinated-table-refs.sql

BEGIN;

-- 1/20 — "Table 3" doesn't exist (no decimal); voltage drop is Clause 3.6.
-- OLD: ...Using AS/NZS 3000 Table 3, the maximum voltage drop permitted...
UPDATE questions SET body =
  'A 230V single-phase lighting circuit is 45 metres long and supplies a load of 6 amps. Per AS/NZS 3000 voltage drop requirements, the maximum voltage drop permitted for this circuit is:'
WHERE id = 'aa2fd6cc-5329-5f57-a484-15404a05c31d';

-- 2/20 — Table 5.1 is "Min Copper Earthing Conductor Size" (not CPC sizing in cable).
UPDATE questions SET body =
  'A 32A circuit protected by an MCB uses 6mm² active conductors. Per AS/NZS 3000 earthing requirements, the minimum protective conductor (CPC) size is:'
WHERE id = '71045793-7ed9-507b-98fd-c2d0b0e34ea9';

-- 3/20 — Zs values live in Table 8.1, not 5.1. Keep stated value (0.27Ω) — verify separately.
UPDATE questions SET body =
  'A circuit is protected by a Type C 32A MCB. AS/NZS 3000 specifies maximum earth fault loop impedance (Zs) for this device as 0.27Ω. The actual Zs measured is 0.31Ω. The installation:'
WHERE id = '81ef9903-1c73-5e4b-be61-c5bc82f0054a';

-- 4/20 — Table 3.2 is "Limiting Temperatures for Insulated Cables", not max demand.
UPDATE questions SET body =
  'A domestic installation has 8 identical 5A lighting circuits. Per AS/NZS 3000 maximum demand rules, the maximum demand contribution of all 8 circuits is:'
WHERE id = '22c49a8f-f5c3-5624-9a1d-e82532be9e78';

-- 5/20 — Table 3.2 (Load Group B) — same hallucination as above.
UPDATE questions SET body =
  'A domestic installation includes 25 standard 10A socket-outlets. Utilizing the standard maximum demand rules from AS/NZS 3000 (socket-outlets load group), what is the calculated maximum demand for these socket-outlets?'
WHERE id = 'd9634a0a-5bdc-545d-b8ea-26562076b79d';

-- 6/20 — Table 3.2 (Load Group F).
UPDATE questions SET body =
  'A domestic installation includes a 4.8kW electric storage hot water cylinder. Using the AS/NZS 3000 standard maximum demand method (water heater load group), calculate the maximum demand in Amperes for this water heater on a standard 230V single-phase supply. Provide your answer to one decimal place.'
WHERE id = '71db532f-0c42-5d69-b467-025d8476f565';

-- 7/20 — Table 3.2 (Load Group C).
UPDATE questions SET body =
  'A domestic installation includes a 6.4kW electric cooktop and a 3.6kW separate wall oven. Using the AS/NZS 3000 standard maximum demand method (cooking appliances load group), calculate the maximum demand in Amperes for these cooking appliances. Assume a 230V single-phase supply and provide your answer to one decimal place.'
WHERE id = '6e5f32de-3894-5b4f-b1e0-0ad97d572ecb';

-- 8/20 — Table 3.2 (Load Group C).
UPDATE questions SET body =
  'A domestic installation includes a 7.2kW electric wall oven and a 5.6kW induction cooktop wired on separate subcircuits. Using the AS/NZS 3000 standard maximum demand method (cooking appliances load group), calculate the combined maximum demand in Amperes for these cooking appliances on a 230V single-phase supply. Provide your answer to one decimal place.'
WHERE id = 'fc7a6786-1398-5a14-be51-2a5f5d046049';

-- 9/20 — "Clause 4.2 (Table 4.2)" — Table 4.2 is "Min Distance Between Lamp and Flammable Materials".
UPDATE questions SET body =
  'A domestic kitchen installation has two separate dedicated circuits: a 3.0kW 230V wall oven and a 5.8kW 230V cooktop. According to AS/NZS 3000 maximum demand rules for cooking appliances, what is the combined maximum demand contribution of both appliances?'
WHERE id = '77a2ebff-879d-591f-a773-561600a8489f';

-- 10/20 — Table 3.2 (Load Group B).
UPDATE questions SET body =
  'A new domestic installation features exactly 45 standard 10A socket-outlets. Using the standard maximum demand rules from AS/NZS 3000 (socket-outlets load group), calculate the total maximum demand in Amperes for these socket-outlets.'
WHERE id = '22027be3-cd3a-53cd-9f9f-21a2b7c4c7d6';

-- 11/20 — Table 3.2 for max demand.
UPDATE questions SET body =
  'A single domestic installation contains 15 general lighting points. Using AS/NZS 3000 maximum demand rules, what is the calculated demand for this lighting load?'
WHERE id = 'a01bec26-39f5-576a-8e5b-c5d2f3ceb341';

-- 12/20 — Table 5.1 stated as containing Zs values — Zs is in Table 8.1. Keep 1.83Ω value.
UPDATE questions SET body =
  'A Type B 16A MCB protects a socket outlet circuit. AS/NZS 3000 specifies maximum Zs of 1.83Ω for this device. A measured Zs of 1.90Ω at the furthest socket means:'
WHERE id = 'd01eeec6-6c77-5814-8caa-b19ad4e22d7e';

-- 13/20 — Table 3.2 (Domestic installations).
UPDATE questions SET body =
  'According to AS/NZS 3000 maximum demand rules (domestic installations), what is the calculated maximum demand for a single 32A hard-wired cooktop?'
WHERE id = '2bc13ab9-dc6f-56e5-be37-69a70391864f';

-- 14/20 — Table 3.3 (Non-domestic installations).
UPDATE questions SET body =
  'According to AS/NZS 3000 maximum demand rules (non-domestic installations), how many Amperes of maximum demand must be allocated for a commercial factory lighting circuit if the total connected load of the LED luminaires is exactly 4,600 Watts on a 230V single-phase supply? Provide your exact answer.'
WHERE id = 'ae911a06-df19-5bb9-9fcd-0f60bfe4ba78';

-- 15/20 — Table 5.1 stated as Zs source — Zs is Table 8.1.
UPDATE questions SET body =
  'AS/NZS 3000 gives different Zs limits for Type B, C, and D MCBs of the same current rating because:'
WHERE id = '1e492167-9288-5ee5-a619-5d639a598da9';

-- 16/20 — Table 3.2 (Domestic installations).
UPDATE questions SET body =
  'Under AS/NZS 3000 maximum demand rules (domestic installations), how is the maximum demand calculated for a single, thermostatically controlled storage water heater on a dedicated final sub-circuit?'
WHERE id = '2ecf32cd-9215-5839-b040-5cb865cdde6d';

-- 17/20 — Table 3.2 (Domestic installations).
UPDATE questions SET body =
  'Under AS/NZS 3000 maximum demand rules (domestic installations), how is the maximum demand calculated for the indoor lighting load?'
WHERE id = '4f73dcf2-8984-5326-84f8-65b69a611e2d';

-- 18/20 — Table 3.2 (Load Group A).
UPDATE questions SET body =
  'Using the AS/NZS 3000 standard maximum demand method (domestic lighting load group), calculate the maximum demand in Amperes for a single-phase house containing exactly 35 standard lighting points.'
WHERE id = '6d9848d2-2a27-5eee-ad51-273c800095a9';

-- 19/20 — Table 3.3 (Non-domestic).
UPDATE questions SET body =
  'When calculating the maximum demand for a commercial office building (lighting load group, non-domestic), how is the interior lighting load assessed according to the standard method in AS/NZS 3000?'
WHERE id = '8be57a8f-8448-53e2-9114-2c53c8e1c897';

-- 20/20 — Table 8.1 is "Maximum Values of Earth Fault-Loop Impedance", not insulation resistance.
UPDATE questions SET body =
  'When testing the insulation resistance of a complete low-voltage installation (isolated from the supply), what is the minimum acceptable resistance value specified in AS/NZS 3000 when using a 500V DC tester?'
WHERE id = 'cf5c7f32-bd35-5cda-8ed6-5e84634597b8';

-- ------------------------------------------------------------------
-- Option-text fixes: two questions had answer options that *also*
-- referenced the now-stripped Table 5.1. Replacing the whole options
-- array so the candidate never sees the bogus citation.
-- ------------------------------------------------------------------

-- Q12 above (d01eeec6) — option (a) referenced "Table 5.1 value".
UPDATE questions SET options = '[
  {"id":"a","text":"Non-compliant — measured Zs must not exceed the maximum Zs value specified in AS/NZS 3000 under any circumstances"},
  {"id":"b","text":"Compliant because the MCB would eventually clear the fault"},
  {"id":"c","text":"Non-compliant but acceptable if Ze is subtracted from the measured Zs"},
  {"id":"d","text":"Compliant because the fault current is still sufficient to operate the MCB"}
]'::jsonb
WHERE id = 'd01eeec6-6c77-5814-8caa-b19ad4e22d7e';

-- Q15 above (1e492167) — distractor (c) said "Table 5.1 only applies to Type B devices".
UPDATE questions SET options = '[
  {"id":"a","text":"Type B devices have lower magnetic trip thresholds (3-5× In), meaning they require less fault current to trip instantaneously, thereby tolerating higher circuit impedance"},
  {"id":"b","text":"Type C devices are more sensitive and need higher Zs limits"},
  {"id":"c","text":"The Zs requirements only apply to Type B devices"},
  {"id":"d","text":"The difference is due to thermal overload characteristics only"}
]'::jsonb
WHERE id = '1e492167-9288-5ee5-a619-5d639a598da9';

-- Sanity check: must touch exactly 20 rows in body + 2 in options, and
-- NO rewritten row may still contain a bogus table reference (body OR option).
DO $$
DECLARE
  expected_ids uuid[] := ARRAY[
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
  ];
  bad_body integer;
  bad_options integer;
BEGIN
  SELECT COUNT(*) INTO bad_body
  FROM questions
  WHERE id = ANY(expected_ids)
    AND (body ~* '\mtable\s*[0-9]' OR body ~* 'clause\s*4\.2');
  IF bad_body <> 0 THEN
    RAISE EXCEPTION 'Sanity check failed: % rewritten question body(ies) still contain a Table N reference', bad_body;
  END IF;

  SELECT COUNT(*) INTO bad_options
  FROM questions
  WHERE id = ANY(expected_ids)
    AND options::text ~* '\mtable\s*[0-9]';
  IF bad_options <> 0 THEN
    RAISE EXCEPTION 'Sanity check failed: % rewritten question(s) still contain a Table N reference in options', bad_options;
  END IF;
END $$;

COMMIT;
