# 0332 — report: the furnishings lane (VEHICLES 0325 fleet + CABINETS/room-style 0329) gated GREEN with the dormer fix in the tree; committed by path on `furnishings-lane`, AMBER. 0330's "anything else red" answered.

**Code, 2026-11-14.** Answers 0329 §6, 0328 §5 and 0330. The reviewer built two
furnishing deliverables un-gated (no PyQt6/pytest on the device): the eight
remaining vehicle side elevations (0325 follow-on) and parametric CABINETS + a
room STYLE (0329). Plus 0330 fixed one cabinet TEST assertion in place. This is
their first real run under Qt/pytest, gated together with Code's dormer ceiling
fix (0331) in the same tree.

## 1. THE GATE — FULL, ON THE COMBINED TREE

```
Gate-Census: collected=2280 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2273 passed, 7 deselected, 3 warnings  -> sum 2280  OK
Gate-ON:  2273 passed, 7 deselected, 11 warnings -> sum 2280  OK
Gate-Verdict: GREEN (every sum reconciles against --collect-only)
```

**Collected 2227 → 2280**: the cabinet suites (`test_cabinet_geometry`,
`test_cabinet_item`, `test_cabinet_viewer`) and the vehicle-fleet additions.
`Gate-ON` runs `FP_VERIFY_DESIGN=1`.

## 2. 0330's QUESTION — "anything else red, verbatim"

Before the pair table was regenerated for this landing, the only reds were two
DOC-index tests, not product code:

```
FAILED tests/test_status_index.py::test_the_board_and_the_pair_table_match_a_regeneration
FAILED tests/test_status_index.py::test_the_pair_table_lists_every_mailbox_file
```

Both are the mailbox pair table being stale against the new handoff files
(0328–0332) — fixed by `python tools/status_index.py`, part of this commit. **No
product test is red.** 0330's cabinet fix (the drawer-number assertion) is green.

## 3. THE COMMIT, BY PATH

On `furnishings-lane` (off `main`), one commit, the lane's files only (0329 §6):
`_gen_assets.py`, `assets/furnishings/` (regenerated — the eight new
`*.side.svg`, manifest/materials/README), `floorplanner/design/design-schema.v6.json`,
`floorplanner/dialogs.py`, `floorplanner/items.py`, `floorplanner/parametric/`
(cabinet calculator/view + registry), `floorplanner/viewer/fp3d.py` (the
`build_vehicle`/`load_side_profile` and cabinet `_load_parametric`/`CABGEO`
hunks — NOT the dormer ceiling hunks, which landed on `main` with 0331),
`tests/test_vehicle_profile.py`, `tests/test_viewer_model.py`, the three
`tests/test_cabinet_*.py`, `docs/furnishing-spec/CABINETS_AND_ROOM_STYLE_PLAN.md`,
`docs/evidence/0325-vehicles/fleet_*.png`, `docs/evidence/0329-cabinets/`.

**`fp3d.py` note:** the working file carried three lanes' hunks (dormer, vehicles,
cabinets). The dormer hunks were staged to `main` alone (by patch); the
furnishings commit carries the vehicle + cabinet hunks, committed once — said so
here.

## 4. LEFT OUT (0328 §5)

`assets/icons/*` show modified but are LF-only (autocrlf, content identical) —
not committed. `docs/gallery/21-cars-suv-3d.png` is not this session's — left.

## 5. NOT RULED ON / AMBER

The gate tests behaviour, not design. 0329's KNOWN GAPS and Patrick's checks
stand; the camera-elevation step (0329 phase 5) is held behind camera Phase 2,
and the one `fp3dq._pbr` sheen line (0329 §4.1) is Code's, for when Phase 2 is
in. Nothing merged — the vehicles and cabinets are AMBER on `furnishings-lane`,
his look is the merge condition.

## 6. OWED

- **Code:** this report; the two commits (dormer on `main` with 0331; furnishings
  on `furnishings-lane`). Hold for his checks.
- **Reviewer:** fixes from his checks, in the next ruling; no git.
