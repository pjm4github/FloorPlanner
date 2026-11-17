# 0352 — ruling: the dormer-as-furnishing refactor is ORDERED. Patrick's six decisions; phase 1 is built (reviewer lane, un-gated); phases 2-5 are Code's

**Reviewer (Cowork), 2026-11-16.** Supersedes [`0351`](0351-ruling.md) §2.1
(RED) — Patrick has answered. The plan, with his decisions in its section 9:
[`docs/furnishing-spec/DORMER_FURNISHING_PLAN.md`](../furnishing-spec/DORMER_FURNISHING_PLAN.md).

## 1. His decisions, verbatim in substance

1. A furnishing record, in a **Structure** category. He will migrate old
   plans by hand where needed.
2. Exterior walls rise to the gable face's peak.
3. Knobs C and D stay as guides; they draw no wall.
4. Convert on load if possible; **never abort** — a warning dialog.
5. Schema stays at 6.
6. The Wiscaway loop carries on and switches when the furnishing exists.

## 2. Phase 1 — built, in the tree, un-gated. GREEN

- `floorplanner/parametric/dormer_geometry.py` — pure, loadable by path. The
  state (`STATE_DEFAULTS`, `normalize_state`), heights and slopes,
  `ridge_depth` / `valley_lines` / `knee_lines` / `full_height_width` against
  a host plane, `footprint`, `guides`, `plan`, the local-to-plan transform,
  and the two adapters phases 2-4 stand on: **`to_roof_record`** (a dormer
  furnishing as the `roof` record `roofclip.RoofGeom.from_record` and `fp3d`
  already read) and **`from_roof_record`** (an old hosted roof record as a
  dormer state — the conversion on load).
- `floorplanner/parametric/dormers.py` — `DormerKind`, built as `DORMER` and
  **deliberately not registered**: nothing offers a dormer furnishing until
  phase 2 can draw one.
- `tests/test_dormer_geometry.py` — 23 test functions (30 cases as the stand-in counts them); the last one loads
  `roofclip.py` and checks its surface against this module's, point for point.
- Schema: `$defs/dormer_state`, declared, not enforced.

Stand-in runner: 30 of 30 pass. **Not run:** ruff, the real pytest. Gate it and
commit by path; failures verbatim.

## 3. Phases 2-5 — Code's. Each its own branch, AMBER on Patrick's check

**Phase 2 — the item.** `DormerItem(FurnishingItem)`, modelled on
`StairItem`. A catalog entry `dormer` and a new palette group **Structure**
(`_gen_assets.py`; whether `stairs` / `elevator` / `post` move there from
"Framing" is Patrick's to say — ask, do not assume). Drag-drop places it;
`register(DORMER)`; double-click opens the generic dialog. Knobs A-G move
from `RoofGripItem`; C and D drag the GUIDES. The host is found by absolute
height under `pos` each time — nothing stored. It draws ridge, eaves, rake,
valleys, guides and knee lines from `dormer_geometry.plan`, and NO wall.
`param_context` supplies `ceiling_in`, `host_z_face_in`, `host_slope`,
`host_ridge_in`.
- **C1 — measure the drag.** Knee lines must follow the pointer. Report the
  per-move time on `wiscaway2026-11-15R1.json`; hold the settle walk while a
  knob is down (`hold_roof_clips`). If it is under 15 frames a second, say so
  before building further.
- **C2 — one geometry.** The item's host cut, its knee lines and the 3D roof
  all go through `to_roof_record`. No second formula in `items.py`.

**Phase 3 — 3D and the wall rule.** `fp3d` reads dormer furnishings through
`to_roof_record` (it loads `dormer_geometry.py` by path, as it does the
stair's). An EXTERIOR wall under a dormer rises to the roof surface, above
the ceiling line if need be; an INTERIOR wall stops at the lower of roof and
ceiling. `_dormer_face` and `_dormer_cheeks` produce nothing for a furnishing
dormer.
- **C3 — say what is open.** A dormer with no wall under its face or a side
  gets an advisory in its dialog and a line in `model.notes`.
- **C4 — 0350 §1 first.** The clipper that does not return must be measured
  before this phase leans on it.

**Phase 4 — conversion and retirement.** On load, a `roofs[]` record with a
`host` becomes a dormer furnishing (`from_roof_record`); a `dormer`-type wall
becomes an `exterior` wall on its own vertices; an opening on the dormer
record becomes a window in the converted face wall.
- **C5 — never abort.** Anything that cannot be converted is collected and
  shown in ONE warning dialog after the plan opens; `interactive=False`
  callers get the same list on `_import_errors`. A test loads all 23 fixture
  files that hold dormers and asserts each opens.
- **C6 — before and after.** For each of those fixtures, `build_model`
  before and after: report triangle counts and bounds, and name every one
  that changed shape.
- Then delete: `sync_dormer_walls` and what serves it, `bound_to` writing,
  the weld, `DormerWindowItem`, the End-On dialog's window list,
  `legal_dormer_levels` / `move_dormer_to_level` / `MOVEDORMER`, the H tool's
  dormer mode. The schema keeps READING the old keys, marked deprecated.
- The ~165 dormer tests: keep those that pin rules 8 and 9, rewrite or
  delete those that pin minted walls and face windows. List which, per file.

**Phase 5 — documents.** `DORMER_CONROLS.md`, `COMMANDS.md`, schema text,
gallery. GREEN.

## 4. Model

Phases 2, 3 and 4 are not mechanical: they cross `roofs.py` (3,800 lines),
`fp3d.py`, `bridge.py` and the undo path, and phase 4 deletes behaviour
Patrick once asked for. **Opus** for those. **Sonnet** for phase 5 and for
the test census in phase 4's last bullet.

## 5. Order of work for Code

1. Now: gate and land phase 1 (§2). Take 0351 §2.4's two measurements.
2. Then phase 2, on a branch. Stop for Patrick's check.
3. Phases 3, 4, 5 in turn, each stopped for his check.

Still owed from earlier and not replaced by this: 0349 §2 (3D panel
framing), 0350 §1 (clipper record + measurement), §3 (blank 3D panel), §4
(heartbeat). 0350 §2 is recorded only — phase 4 deletes its code.
