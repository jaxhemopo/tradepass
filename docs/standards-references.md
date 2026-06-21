# NZ Sparky — Authoritative Standards References

Use these when generating, importing, or verifying question content. **Do not invent table or clause references** — verify against the actual Standard before writing them into a question body.

## AS/NZS 3000 — Electrical Installations (Wiring Rules)

The Wiring Rules. Primary reference for the NZ EWRB Registration exam and AU equivalents.

| Edition | URL | Notes |
|---|---|---|
| 2018 (current) | https://www.powerandcables.com/wp-content/uploads/2019/07/AS-NZ-3000-2018-Australian-New-Zealand-Wiring-Rules.pdf | Front matter / TOC only — full content is behind Standards Australia paywall. Use TOC to verify clause/section numbering. |
| 2007 (superseded) | https://iqytechnicalcollege.com/AS3000-2007.pdf | Full text. Useful for verifying table contents — but **note that 2018 reorganized max demand into Appendix C** (see below). |

### Critical edition differences

- **Maximum demand:**
  - 2007 → Tables in Section 2 / Section 3 (e.g. former references like "Table 2.1", "Table C2" in older versions)
  - 2018 → **Appendix C**:
    - `C1` — Single and multiple domestic
    - `C2` — Non-domestic
    - `C3` — Energy demand method
    - `C5` — Domestic cooking appliances
- **Voltage drop:**
  - 2018 → `Clause 3.6` (the 5% rule lives in clause text, not a table)
  - 2018 → `Appendix C8` — voltage drop simplified method
  - mV/A/m values live in **AS/NZS 3008**, not AS/NZS 3000
- **Max earth fault loop impedance (Zs):** `Table 8.1` in both editions (NOT Table 5.1 — Table 5.1 is "Minimum Copper Earthing Conductor Size")

### Verified 2007 table titles (cross-check when writing references)

| Table | Title |
|---|---|
| 3.1 | Cable Types and Their Application in Wiring Systems |
| 3.2 | **Limiting Temperatures for Insulated Cables** *(not max demand)* |
| 3.3 | **Nominal Minimum Cross-Sectional Area of Conductors** *(not max demand)* |
| 3.4 | Conductor Colours for Installation Wiring |
| 3.5 | Underground Wiring System Categories |
| 3.6 | Underground Wiring Systems — Minimum Depth of Cover |
| 4.1 | Temperature Limits in Normal Service for Parts of Electrical Equipment |
| 4.2 | **Minimum Distance Between Lamp and Illuminated Flammable Materials** *(not max demand)* |
| 5.1 | **Minimum Copper Earthing Conductor Size** *(not Zs)* |
| 5.2 | Acceptable Earth Electrodes |
| 8.1 | **Maximum Values of Earth Fault-Loop Impedance (Zs at 230 V)** ← Zs lives here |
| 8.2 | Maximum Values of Resistance |

## Other relevant standards

- **AS/NZS 3008** — Cable selection (mV/A/m voltage drop values live here)
- **NZ Electricity (Safety) Regulations 2010** — statutory framework
- **Electricity Act 1992** — Section 79 owner-occupier exemption etc.
- **ECP 51** — Electrical Code of Practice for homeowner electrical work

## Guidance for generators / importers

1. **Never include a table number in a generated question unless verified against the actual Standard.** Generic phrasing like "Per AS/NZS 3000 maximum demand rules…" is safer than a hallucinated reference.
2. **Edition-pin your references.** If you cite a table, say `AS/NZS 3000:2018 Appendix C1` not just `Table C1` — table numbering shifted between editions.
3. **The candidate brings their hard copy to the exam.** They are expected to look things up. Question precision matters; reproducing tables in-app is a copyright violation.
4. **Verify any numeric value pulled from a Standard** (Zs limits, cable sizes, max demand percentages) — these change between editions and are common hallucination targets.
