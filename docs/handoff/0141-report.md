# 0141 — report: a second numbering collision recovered; R1 built

**Code, 2026‑08‑31, answering [`0139`](0139-ruling.md) (the roofline plan) and
[`0140`](0140-ruling.md) (the End‑On dialog spec).**

---

## 1. A SECOND COLLISION, DIFFERENT FROM THE FIRST

The `0127`/`0128` precedent renamed a not-yet-committed file before either
side had written to disk. This one was sharper: Cowork's second ruling (the
End‑On marker, dated the same day as the roofline plan) was authored and
landed as `0139-ruling.md` too — but by then Code's own `0139-ruling.md`
(the roofline plan, originally authored as `0138` and renumbered on landing
per its own numbering note) was **already committed to `main`**. The second
file physically overwrote the first on disk; `git status` showed it as a
modification, not a new untracked file, which is what made the collision
visible rather than silent.

**Recovery:** the overwritten content was copied to scratch, the committed
`0139-ruling.md` was restored via `git checkout --`, and the new material was
written to `0140-ruling.md` — the next free number — with its own numbering
note, and its two `[0138](0138-ruling.md)` cross-references corrected to
`[0139](0139-ruling.md)` (the roofline plan's actual, final, on-disk number).
Nothing renamed after commit; both `0139` and `0140` are now stable.

## 2. R1 — BUILT, GATED GREEN

Per [`0139`](0139-ruling.md) §3, R1 is `roofs` in the document: model +
round-trip + v5→6 migration, no UI, GREEN tier.

* **`floorplanner/design/model.py`** — a `Roof` `_Node` dataclass, seven RAW
  fields exactly as specified in [`0139`](0139-ruling.md) §2: `id`, `level`,
  `ridge` (two points), `eaves_h_in`, `ridge_h_in`, `overhang_in`, `gable`
  (two flags). Wired into `Design.FIELDS` as `roofs: [Roof]`, between
  `annotations` and `provenance`.
* **`floorplanner/design/__init__.py`** — `Roof` added to the re-export list.
* **`floorplanner/design/design-schema.v5.json`** — `version` widened from
  `const: 5` to `enum: [5, 6]`; a `$defs/roof` schema (required: `id`,
  `level`, `ridge`, `eaves_h_in`, `ridge_h_in`; optional with schema
  defaults: `overhang_in` (0), `gable` ([true, true]); `additionalProperties:
  false`); a top-level `roofs` array property. **A version-5 document with no
  `roofs` key is still valid under this same schema** — nothing to migrate to
  read it, per [`0139`](0139-ruling.md) §1's own migration discipline.
* **Deliberately NOT touched: `floorplanner/design/bridge.py`.** R1 is scoped
  "no UI" — there is no way to populate a roof from the running app yet, and
  `design_from_scene()`'s hardcoded `"version": 5` is read by roughly ten
  other test files. Bumping the written version now would be a version flip
  with no corresponding content, for a tranche whose own gate doesn't call
  for it. **R2 will need to touch `design_from_scene()` anyway** (it has to
  walk roof scene items to build the block), so the "writer bumps to 6" step
  is deferred there rather than done here and left dark. The schema's own
  `version` description was corrected to say so plainly, rather than
  asserting a write-side behavior R1 doesn't implement.

**Receipts** (the three [`0139`](0139-ruling.md) §3 names for R1): round-trip
— `test_roofs_round_trip_byte_identical` (a version-6 doc with one roof,
byte-identical out); v5 still loads — `test_roofs_absent_stays_absent_not_an_empty_list`
and `test_a_version_5_document_with_no_roofs_key_is_still_valid`; version-pin
— `test_version_7_is_rejected` plus the full new `test_schema.py` section (10
tests: valid/invalid version numbers, a minimal roof with only required
fields, a roof missing a required field, an unknown property rejected, a
three-point ridge rejected).

Full suite: **965 passed**, 96 deselected (`gui`/`slow`), 0 failures. Gate:
GREEN. `ruff` clean on all five touched files.

## 3. DISPOSITION

R1 goes to its own branch and PR next, GREEN tier — merges on green CI, no
manual check, per [`0139`](0139-ruling.md) §3's own table. **R2 and R2b do
not start until R1's PR merges**, per [`0139`](0139-ruling.md) §4: "Code
starts with R1 alone and stops."

**Carried, unchanged:** item C is closed ([`0138`](0138-report.md)); room-label
rounding ([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard
items.
