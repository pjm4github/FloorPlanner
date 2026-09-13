# 0173 — report: R4f's second check — a stray fin, traced to two artifacts, both fixed

**His second check of [PR #59](https://github.com/pjm4github/FloorPlanner/pull/59)**
(after 0172-report.md's hole-fix): a small, badly-angled flap of roof
still visible near the junction — smaller than the original hole, but a
real defect, not a rendering quirk.

## 1. Two distinct artifacts, both measured directly

**Artifact A — a razor-thin sliver from the pairwise fold itself.**
`compute_roof_clips`'s region fold intersects `clip_pair(rf1,rf2)`'s
kept-region-for-rf3-partner against `clip_pair(rf2,rf3)`'s, cell by cell
(`_convex_intersection`). Near a complex junction where several seam
lines converge at close angles, this can produce an exact but razor-thin
sliver — measured on his fixture, before any fix: two cells in rf3's
region at (756.0, 552.9)-(756.0, 553.3)-(756.5, 553.0) and its neighbour,
areas **0.1094 and 0.3694 square inches**. `_prism_slab` still extrudes
each as its own tiny prism — a sub-square-inch scrap of roof, at
whatever angle its razor-thin triangle happens to lift to, reads as a
stray fin next to the real surface around it.

**Artifact B — a duplicated gap-fill cell.** `_fill_unclaimed_ground`
builds its own, independent cell arrangement, then subtracts every
already-claimed region from each candidate cell (`_subtract_claimed`)
before assigning what remains. Two DIFFERENT starting candidate cells
can, after subtraction, converge on the exact same leftover geometry —
the pre-subtraction dedup pass (`_dedup_cells`, tight rounding
tolerance) doesn't catch this, since the duplication only emerges after
subtraction runs. Measured: two pairs of exact-duplicate cells in rf2's
region (areas 272.1972 and 343.1525, each appearing twice, vertices
identical up to rotation).

## 2. The fix

- A roof's region (for 3-or-more-touched roofs only) has every cell
  under **`MIN_FILL_AREA`** (1 square inch — deliberately much larger
  than `MIN_CELL_AREA`'s 1e-3, which is float-noise tolerance for the
  EXACT pairwise clip, not a threshold for what counts as real,
  manufactured roof) dropped, before the fill pass runs. That ground
  becomes unclaimed and the fill pass picks it back up, this time
  merged into whichever real neighbour is highest there — no tiny
  isolated cell survives on its own.
- `_fill_unclaimed_ground` now dedups what it manufactures (at a looser
  tolerance, `FILL_DEDUP_TOL`, than the arrangement-stage dedup) before
  merging it into a roof's region — so a leftover produced twice from
  two different starting cells is only added once.

Both changes are scoped to live (3-or-more-touched) roofs, same as the
gap-fill pass itself, so the two-roof regression (`clip_pair`'s own
tight area-equality test, `abs=1e-3`) is untouched by construction.

## 3. Re-verified on his fixture

- Every remaining cell, on every roof, is well over 1 sq in (smallest:
  rf1 133.6, rf2 146.1, rf3 38.5).
- No duplicate cells (checked by rounded vertex-set key) on any roof.
- Still 0 double-owned points, 0 seam-crosses-a-higher-third-roof
  violations, 0 undrawn points in the footprint union.
- The exact triple point is unchanged: (681.586, 538.067), height
  117.503 on all three surfaces.
- **New receipt**: the 3D roof mesh is confirmed to be ONE connected
  surface — union-find over every pair of triangles sharing an edge
  finds a single component (708 faces, all reachable from any other). A
  stray sliver would show up as either a second, disconnected component
  or a needle-thin one still attached at one edge; neither exists.
- A re-render (`fp3d.py --shot`, and again with `--edges` to see the
  triangulation directly) shows a clean, continuous surface at the
  junction.

## 4. Receipts

- `tests/test_roof_intersection.py::test_r4f_no_stray_slivers_or_duplicate_cells_near_the_junction`
  — new, asserts every cell area on his fixture exceeds 1 sq in and no
  duplicate cells exist.
- `tests/test_roof_intersection.py::test_r4f_the_3d_mesh_is_one_connected_surface`
  — new, the mesh-connectivity receipt from §3.
- All previously-passing tests (the 26 two-roof regression tests, plus
  the 8 tests from 0171/0172) still pass unchanged.
- `python tools/gate.py`: GREEN, 1267 passed, `ruff` clean.

## 5. His third look

Open `fixtures/threeRidgeFloorplan.json` again. No hole, no stray fin;
the roof should read as one clean, continuous surface at the junction,
the three valleys still meeting at one point. The two-roof T/L cases are
unaffected by construction (this session's third change in a row scoped
away from them) but cost nothing to glance at again.

**Carried, unchanged from 0171 §6 / 0172 §6:** D83/D84 (held); room-label
rounding ([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family;
yard items; the End-On marker at a clipped ridge end
([`0166`](0166-report.md) §3); a genuinely global (non-pairwise)
construction, should a future case call for it.
