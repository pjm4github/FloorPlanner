# 0367 pyramid-roof — evidence INDEX (stage 2)

The pyramid-roof furnishing ordered in `docs/handoff/0367-ruling.md`. Stage 2
(the item, the plan symbol, the 3D faces, and §3's walls/posts rising) owes
**E1** (ruling §7); E2–E5 come with stage 3's weld. `Patrick's check` is left
empty for him.

| ID | Case | sides | Plan | Image (3D) | Patrick's check |
| -- | ---- | ----- | ----- | ---------- | --------------- |
| E1 | free-standing hexagon gazebo — an exterior room 12 ft across the flats, a 6×6 post at each corner, a six-sided pyramid roof whose wall line sits on the posts (eaves 96, pitch 10, apex 156) | 6 | [E1…json](E1-free-standing-hexagon.json) | [E1…png](E1-free-standing-hexagon.png) | |

The posts rise to the roof's underside; the roof is drawn whole (no weld at
stage 2). Patrick's stage-2 check (ruling §7): E1 by eye, plus drag, rotate and
the dialog in the app.

## Conditions

- **C1 — one geometry.** The plan symbol, the dialog, the 3D faces and the
  walls/posts all read `floorplanner/parametric/pyramid_geometry.py`
  (`plane_height` / `surface_height`); no second height formula in `items.py`
  or `fp3d.py`.
- **C3 — differential receipt.** `C3-differential.json` (from
  `c3_differential.py`): every no-pyramid document builds **identically** before
  (branch base `24601ac`, fp3d with no pyramid code) and after — per-mesh
  triangle count and bounds — for a gable, a gable+dormer, a cross-gable and a
  walls-only plan. The only new behaviour is gated on a pyramid being present.
- **C4 — fail-first.** `tests/test_pyramid_3d.py` holds the wall-climb test and
  its contrast: take the pyramid away and the same exterior wall stays at its
  own 96 in (`test_without_the_pyramid_the_same_wall_stays_at_its_own_height`).
- **C5 — never abort.** A pyramid with a flat pitch still loads: it draws RED in
  plan and in 3D, says why in the dialog and in `model.notes`, and holds up no
  wall or post.

## Reproduce

- `make_e1.py` — writes the E1 plan (validated against the packaged v6 schema)
  and renders the 3D shot.
- `c3_differential.py` — regenerates `C3-differential.json`.
