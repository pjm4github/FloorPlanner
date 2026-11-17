# 0356 — ruling: control D has its field; the dormer dialog shows the GABLE END and BOTH SIDES, with the openings in the walls under them

**Reviewer (Cowork), 2026-11-17.** Answers [`0355`](0355-report.md) and
records a requirement Patrick added today. Read with [`0352`](0352-ruling.md)
and [`0353`](0353-ruling.md). The code below is in the tree on `dormer-item`,
un-gated; Code gates it and commits by path.

## 1. 0355 — control D. Granted, as asked

- `STATE_DEFAULTS["guide_face_in"] = 0.0` — the face guide's set-back from
  the face INTO the dormer (local +Y), 0 = on the face. Clamped `>= 0` in
  `normalize_state`; `plan()` clamps it to the ridge's length (only a caller
  that knows the host can), and the two side guides now START on it.
- `guides(st)` still returns three values; the third is that field.
- `to_roof_record` writes `face_guide_in` when it is not 0; `from_roof_record`
  reads it. Schema `$defs/dormer_state` has the key. Dialog field added.
- **Code:** add knob D to `_grip_kinds`, dragging along the ridge, and its
  test. Nothing else of yours changes.

**The ridge sliding off-centre (0355's nuance): no new field.** With
`symmetric` off, `span_left_in` and `span_right_in` already differ. Knob A
dragged ACROSS the ridge trades one span for the other, total width held,
and switches `symmetric` off; with `symmetric` on it does nothing across.
`box_*` stays what it was.

## 2. New — the gable end in the dialog (Patrick, 2026-11-17)

> "Windows on the dormer gable end should be visible on the dialog box when
> the dormer is opened - when the wall under it [is] defined. … a window (or
> door) that is on the gable end of the dormer may have height above the
> floor that is above the ceiling which is OK because the height of the
> dormer gable might be higher than the ceiling on that floor. In addition
> there may be windows that are stacked on each other (maybe a decorative
> octagonal window at the peak of the gable end and a window under it …)"

Built, pure, in `dormer_geometry.py`:

- `face_profile(st)` — the gable in elevation, seen from outside.
- `project_wall(pos, rot, p1, p2, guide_face, tol=6)` — is this wall a FACE
  wall (square to the ridge, within 6 in of the face guide), and its extent.
- `project_openings(x1, x2, wall_length, openings)` — that wall's openings in
  face coordinates.
- `face_openings(st, openings, ceiling_in, wall_span)` — each opening judged
  against the gable: `above_ceiling` (**reported, not a fault**),
  `through_roof`, `off_wall`, `overlaps`. Two openings stacked one above the
  other do not overlap. An opening may carry `shape`: `rect` | `octagon` |
  `round`; the cut corners are honoured, so a small octagon fits higher.

And in the kind / dialog:

- `DormerKind.evaluate` reads two new context keys, `face_wall` and
  `face_openings`, and adds `dormer.face_open` (ADVISORY — this is 0352 C3
  for the face), `dormer.opening_through_roof` and `dormer.openings_overlap`
  (WARNING). None blocks.
- `floorplanner/parametric/dormer_view.py` — `DormerFaceView`, the dialog's
  preview: roof line, floor, ceiling line, the wall, each opening at its own
  sill and head, red where the roof cuts it. **Written blind: this shell has
  no PyQt6. It compiles; nobody has seen it paint.**
- 11 new test functions in `tests/test_dormer_geometry.py`; stand-in runner
  41 of 41. **Not run:** ruff, the real pytest.

### What Code builds (phase 2, same branch, same AMBER check)

- **F1 — the context.** `DormerItem.param_context` finds the wall(s) on its
  own level that `dg.project_wall` accepts and passes `face_wall` (their
  joined extent, or `None` when it looked and found none) and
  `face_openings` (`s0`/`s1` from the wall's first end, `sill_in`, `head_in`
  above this level, `id`, `kind`, `code`).
  No geometry in `items.py`: gather, call `dg`.
- **F2 — see it.** Open the dialog headless on a dormer with a face wall
  holding two windows and a side wall holding one, grab the preview to a PNG under
  `docs/evidence/0356-dormer-face/`, and LOOK at it. Report what is wrong
  with my widget; fix what is plainly a paint bug, list what is a judgment.
- **F3 — measure, do not assume: can the app stack openings today?** Place a
  window on a wall, then a second at the same position along it with a
  higher sill. Report what happens in the plan, on save/reopen, and in
  `build_model` (does the 3D wall cut two holes, one above the other?). If
  any of the three refuses or merges them, say which and stop — that is a
  change to walls, and it needs its own ruling.
- **F4 — measure: an opening whose head is above the room ceiling**, in a
  wall under a dormer. Does the opening sheet accept the sill? Does
  `build_model` cut it in the part of the wall that climbs (rule 8)? Phase 3
  owns the fix if not; I need the answer now.

## 3. Patrick's answers (asked and answered today)

1. **Window shape: not now.** No `shape` key on openings — not in the
   schema, the opening sheet or the 3D cut. `dg` and the preview accept one
   and nothing feeds it; leave that dormant. The octagon is a later ruling.
2. **The preview is look-only.** Openings are edited on the wall in the plan.
3. **Gable end AND both sides.** Built: `side_x`, `side_top`,
   `side_profile` (the wall from the face guide back to where the host
   climbs to its top, with the host's line across it), `project_side_wall`,
   `side_openings` (adds `behind_host`: the sill is under the main roof's
   line there). The kind reads `side_walls` / `side_openings`
   (`{"left": …, "right": …}`) and adds `dormer.side_open.left|right` and
   `dormer.opening_behind_roof` (ADVISORY). The preview draws three panels.
   **F1 covers the sides too**: gather with `dg.project_side_wall(…,
   dg.side_x(st, side))`. Stand-in runner: 46 of 46.

## 4. Tier

§1 and the `dg` / kind changes: no behaviour until F1 feeds them — GREEN.
The preview in the dialog and knob D: AMBER, folded into the phase-2 check.
Patrick's batch for that check, now five items: drag a dormer from Framing
onto a roof; move knobs B, C, D, E, F and A across; release and see the
orange knee lines settle; open the dialog and see the gable end and both sides; draw a
wall on the face guide with a window and see it appear there.
