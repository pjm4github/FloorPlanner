# 0172 — report: R4f's own check — a real hole in 3D, fixed on the branch

**His check of [PR #59](https://github.com/pjm4github/FloorPlanner/pull/59)
(0171-report.md's build)** found a genuine defect, not a false alarm: a
3D screenshot showing a visible hole through the roof where the three
ridges should meet, plus a small flap of roof reading as disconnected.

## 1. What his screenshot showed, and what it actually was

0171-report.md §4 had already measured and named a residual: at this
three-way junction, roughly 3.6% of the footprint union was left "drawn
by nobody," the same CLASS the two-roof algorithm's own module docstring
already accepts for a corner past a seam. Framed as a flat area
percentage, that reads as a minor, cosmetic gap. **It is not, in 3D**: a
patch of roof surface that draws for nobody is a patch with no mesh at
all there, which reads as a literal hole through to whatever the camera
sees behind it — exactly his screenshot, reproduced locally with
`python floorplanner/viewer/fp3d.py fixtures/threeRidgeFloorplan.json --shot`.
The lesson, stated once so it does not need re-learning: a "drawn by
nobody" residual measured as a percentage of plan-space area is not the
same claim as "this looks fine" — the two-roof case's own sliver is
tiny and always sits OUTSIDE the ground two roofs actually fight over
(D85's own corner); this one sat squarely inside the contested ground
three roofs all reach.

## 2. The fix — `_fill_unclaimed_ground`

Added to `compute_roof_clips`, after the region fold and both seam
filters, as a last-resort pass: for three or more TOUCHED roofs (roofs
that overlap at least one other), any ground still contested after
everything above is subtracted, cell by cell, against every already-
decided region (`_subtract_claimed`, exact convex difference), and
whatever remains genuinely unclaimed is given to whichever covering roof
is measurably HIGHEST there.

**Scoped to three-or-more roofs on purpose.** The two-roof "corner past
the seam ... drawn by nobody" behaviour is a DELIBERATE, tested design
(D85, `test_a_s_corner_past_the_seam_draws_no_line_of_a`), and
0170-ruling.md's own regression clause requires the two-roof cases to
come out identical. `_fill_unclaimed_ground` checks the touched-roof
count before doing anything, so a plain two-roof pair is completely
untouched by this pass — locked in by a new dedicated test.

**Why this cannot create a new fault of its own**: it only ever
considers ground that (a) some roof's footprint actually covers and
(b) no region above already claims — the subtraction step guarantees
(b) exactly, so it can neither contradict an already-decided seam (which
only exists on the shared boundary of two regions that already exist)
nor manufacture a second owner for a point some region already contains.

## 3. Re-measured, on the same fixture

- **No point drawn by two roofs at once** — still 0 (unaffected by
  construction, per §2).
- **No seam crosses a roof measurably higher there** — still 0/108
  sampled (unaffected).
- **No point within the footprint union left undrawn** — **0/25,893
  sampled**, was a real, visible gap before this pass.
- **The exact triple point** — unchanged: (681.586, 538.067), height
  117.503 on all three surfaces.
- **A re-render confirms it visually**: `fp3d.py --shot` (default
  camera) and again with `--edges` (mesh triangulation visible) both
  show a fully continuous surface at the junction, no gap, no
  disconnected flap.

## 4. Receipts

- `tests/test_roof_intersection.py::test_r4f_a_genuine_three_way_junction_leaves_nothing_drawn_by_nobody`
  — was a bounded-and-measured test (`< 0.06`), now asserts exactly zero.
- `tests/test_roof_intersection.py::test_r4f_the_fill_pass_never_touches_a_two_roof_corner`
  — new, locks the D85 corner's own behaviour against this pass.
- All 26 pre-existing roof-intersection tests, and the 7 other R4f
  tests from 0171, still pass unchanged.
- `python tools/gate.py`: GREEN, 1265 passed, `ruff` clean.

## 5. His re-check

Open `fixtures/threeRidgeFloorplan.json` again (or pull the branch and
re-run whatever produced the screenshot). The hole should be gone and
the roof should read as one continuous surface at the junction; the
three valleys still meet at one point and stop, and the two-roof T/L
cases should still look exactly as they did before this branch existed.

**Carried, unchanged from 0171 §6:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the End-On marker at a clipped ridge end ([`0166`](0166-report.md) §3);
a genuinely global (non-pairwise) construction, should a future case
call for it.
