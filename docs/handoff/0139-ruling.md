# 0139 — ruling: the roofline plan — five gated tranches, one buildable at a time

**Numbering note: authored and dated as `0138`, renumbered `0139` on landing
— `0138` had already been taken by Code's own report before this file
reached disk. Neither renamed after commit; this is the one-time fix
before either existed in the shared record (the `0127`/`0128` precedent).**

**Patrick, 2026‑08‑31:** ridge + pitch + gable ends, sketched with the wall
tool's own Ctrl/Shift modifiers; pick a ridge line, pick an eaves line, set
ridge height and eaves height; a separate Roof menu; 3D visualization; then a
parameters dialog; dormers after that. The 45° wing carries **its own ridge**.
*"Lets build the feature in an incremental fashion that I can test and gate
one feature at a time."*

**Also on the record: yard items (trees, shrubs, gardens) — wanted, deferred
by his word. Not lost, not started.**

---

## 1. WHAT THE TREE ALREADY PROVIDES — measured, reused, not rebuilt

* **3D exists and is in the app.** `viewer/fp3d.py` (1619 lines): headless
  numpy geometry (`build_model`), OBJ export, offscreen PNG; wired as a popup
  at `mainwindow.py:619` via `fp3dq.Plan3DQuickWidget`, optional deps guarded.
  **Roofs in 3D = new meshes in `build_model`; the popup and CLIs get them free.**
* **The sketch modifiers live in the wall tool** (`walls.py:1899/1974`). The
  ridge tool **calls that machinery** — reuse, not transcription
  ([`0072`](0072-ruling.md) §4's lesson), which also keeps it clear of the
  delta-snap defect class ([`0070`](0070-ruling.md) §3).
* **Levels carry `elevation_in` + `height_in`** — the default eaves height is
  the wall top of the roof's own level; the dialog overrides it.
* **Schema is v5** (`bridge.py:926`). Roofs are an **additive `roofs` block,
  version → 6**, loader accepting 5 (no roofs) — same migration discipline the
  settings file used ([`0078`](0078-ruling.md)).

## 2. THE MODEL — heights are the inputs, pitch is derived

A roof object: `{id, level, ridge: [p1, p2], eaves_h_in, ridge_h_in,
overhang_in, gable: [end1, end2]}`. **Pitch = rise over the ridge→eaves
horizontal run, derived** — the dialog shows it live and accepts a typed pitch
by recomputing `eaves_h` (or `ridge_h`, whichever is unlocked), so "draw the
ridge and the pitch" and "set the two heights" are the same dialog. A gable
roof is two planes off the ridge plus vertical gable-end triangles. **The 45°
wing is simply a second roof object with a rotated ridge — no special case.**
Where two roofs meet, **v1 lets the planes interpenetrate** (correct from
outside in 3D); computed valley/hip lines are named for later, not ordered.

## 3. THE TRANCHES — one branch, one PR, one of Patrick's gates each

| # | tranche | tier | his check |
|---|---|---|---|
| R1 | `roofs` in the document: model + round-trip + v5→6 migration. **No UI.** | **GREEN** — merge on green CI | none (receipts: round-trip, v5 loads, version-pin test) |
| R2 | **Roof menu** + ridge sketch (wall-tool modifiers) + eaves pick + heights dialog with live pitch; 2D overlay (ridge heavy, eaves/gables dashed) | **AMBER** | sketch the main ridge and the 45° wing ridge on wiscaway; modifiers feel like the wall tool |
| R3 | Roof planes + gable ends in `fp3d.build_model` (+ overhang) | **AMBER** | orbit wiscaway: both roofs, right pitch, gables closed (headless receipts: plane slope = derived pitch; `--shot` PNG as evidence) |
| R4 | Roof parameters dialog on an existing roof: heights/pitch, overhang, gable↔hip per end, edits round-trip and re-render | **AMBER** | change a pitch, see 2D + 3D follow |
| R5 | **Dormers** — rooms poking through the roof | **RED — own ruling when R1–R4 stand** | — |

**Named, not ordered:** valley/hip intersection lines in 2D; a roof-plan sheet
in the PDF/DXF exports (the architect handoff will want it eventually); yard
items.

## 4. ORDER

**Code starts with R1 alone and stops.** No tranche starts before the previous
one's gate is passed — that is the instruction, in his words, and it is the
merge condition too. Each report names its tranche number.

**Carried:** item C's Chief off-axis count ([`0137`](0137-ruling.md) §2 — one
line, if the import is still on screen); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family.
