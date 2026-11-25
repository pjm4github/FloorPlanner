# 0367 — C2 read-back: the pyramid weld, before stage 3

**Code → reviewer (Cowork).** The ruling (`docs/handoff/0367-ruling.md`, §6 C2)
withholds stage 3 until this read-back is ruled on: *where the weld is computed
(an extension of `roofclip.py`, or its own pass) and why; its cost on
`wiscaway-c03-roofA-garage.json`; and proof that it RETURNS — 0350 §1's
three-roof case with a pyramid added, timed.* Prototype and measurements:
`c2_weld_probe.py`, `C2-weld-timing.json` (this folder).

## 1. What the weld is (ruling §4, restated)

Where a pyramid and a roof overlap **in plan** — a `roofs[]` record or a dormer
furnishing, any level, compared by **absolute** height — each is drawn only
where it is the **higher** surface. The boundary is the **equal-height line**,
exact: both surfaces are planar by pieces, so within a region where each is a
single plane the height difference is affine and its zero set is a **line**,
found by interpolation, never sampled. The lower surface is **cut** there, in
plan and in 3D, not merely hidden. `weld: off` ignores every roof and is ignored
by every roof. This is deliberately **not** `roofclip.py`'s anchor rule.

## 2. Where it is computed, and why

**Its own pass, built from `roofclip.py`'s convex toolkit — not an extension of
`compute_roof_clips`.** Concretely:

- a new pure function in `roofclip.py` (working name `weld_pieces(pyramid,
  roofs)`) that returns, per `(pyramid, roof)` couple, the plan polygons where
  the pyramid is higher and where the roof is higher, plus the seam segments;
- called from a **dedicated `fp3d` pass** that runs after the roofs and the
  pyramid faces are known, replacing each welded surface's whole-slab pieces
  with the kept pieces. The pyramid enters it through its own surface
  (`pyramid_geometry.plane_height`, the one height formula — C1), exactly as the
  stage-2 wall-climb already consults it via `_PyramidSurface`.

**Why here, and not `compute_roof_clips`.** `compute_roof_clips` is the
roof-to-roof pass — an adjacency graph (`_adjacent` / `_neighbours` / `_reach`)
walked by `_components` / `_walk`. That walk is **0350 §1's non-returning
pass**: three mutually-overlapping roofs ran past 100 s. The weld must never
join that walk. It reuses only the **leaf-level convex tools**, which are each
O(vertices) and loop-free:

| tool | use in the weld |
|---|---|
| `_convex_intersection(a, b)` | the overlap: pyramid eave polygon ∩ roof footprint |
| `_split_by_line` | cut the overlap by the pyramid's hips and the roof's `_cut_lines` |
| `_clip_by_values` | the equal-height boundary: the exact zero set of the affine height difference on a cell |
| `surface_height` / `plane_height` | the two surfaces' heights |

## 3. The algorithm — pairwise, finite, exact

For each `(pyramid, roof)` couple:

1. **overlap** `= _convex_intersection(eave_polygon, roof_footprint)`. Both are
   convex (a regular n-gon; a roof's eave rectangle), so the overlap is one
   convex polygon. No overlap → the couple contributes nothing.
2. **cells** — split the overlap by the pyramid's `n` hip lines **and** the
   roof's `_cut_lines` (ridge, hips). On every resulting cell **both** surfaces
   are a single plane, so the height difference `hP − hR` is **affine**.
3. **boundary** — `_clip_by_values(cell, [hP(v) − hR(v) for v in cell])` keeps
   the part where the pyramid is higher; the negated values keep the roof's
   part. The crossing is the affine zero — **one straight seam per cell**,
   interpolated exactly (ruling §4's "a line, never sampled").

The pyramid is pairwise against each roof; roofs are **never** coupled to each
other here (that is `compute_roof_clips`'s job, unchanged). A dormer furnishing
counts as a roof to weld against (§4), through its existing roof record.

## 4. Proof it returns

**Structural.** The pass is three nested finite loops and no more: over roofs
(finite), over cells of one overlap (at most `n + k` split lines ⇒ O(n·k) convex
cells, `n` = pyramid sides ≤ 12, `k` = the roof's cut lines ≤ 3), over a cell's
vertices (finite). Every step is a single convex-polygon operation; there is
**no recursion, no graph walk, and no iterate-to-converge** (contrast
`meet_along`'s bisection and `compute_roof_clips`'s `_walk`). A finite sequence
of exact linear clips cannot fail to terminate.

**Measured** (`c2_weld_probe.py`, 2000 iterations each, this machine):

| case | couples that overlap | cells | seams | **ms / weld** | returns |
|---|--:|--:|--:|--:|:--:|
| one gable + pyramid | 1 | 10 | 8 | **0.41** | yes |
| **0350 §1 three-roof junction + pyramid** | 3 | 22 | 16 | **0.94** | yes |

The three-roof junction is the case whose **roof-to-roof** clip did not return
(0350 §1, >100 s). Adding a pyramid and welding it against all three completes
in **under a millisecond**, because the weld never enters that walk — it is
pairwise pyramid-vs-surface. (The probe builds the three roofs as `RoofGeom`s
and welds the pyramid against them directly; it does not call
`compute_roof_clips`, so it is unaffected by that defect's status.)

## 5. Cost

Linear in **(roofs the pyramid overlaps) × (cells per overlap)** — ~0.4 ms per
overlapped roof above. A build pays it only for pyramids present and only
against roofs they actually overlap (an overlap test is one convex∩convex);
**a plan with no pyramid pays nothing**, as stage 2's C3 receipt already shows
for the walls.

**On `wiscaway-c03-roofA-garage.json`:** that file is **not in the repository**
— it is one of Patrick's working plans under `fixtures/incoming/` (gitignored),
and it is not present here. By the model above, its NOOK pyramid (E3: `sides` 8
over ~3 main-roof facets) is **one pyramid × ~3 overlaps ≈ 1 ms**, the same
shape as the three-roof row. I will run the probe on the actual file and record
the real number the moment it is dropped into `fixtures/incoming/`.

## 6. What stage 3 then builds (scope, for the ruling)

- The kept **pyramid** pieces triangulate at the pyramid surface; the kept
  **roof** pieces replace that roof's whole-slab triangles — the roof is cut, in
  plan and 3D (§4). `weld: off` bypasses the pass entirely.
- **C3** differential: every fixture with no pyramid builds identically
  before/after (as stage 2's already does); and a pyramid with `weld: off`
  builds exactly the stage-2 whole-pyramid.
- **C4** fail-first: a weld test that goes red with the cut removed.
- **C5** never abort: an unbuildable or `weld:off` pyramid still loads.

## 7. For the ruling — three things to confirm

1. **Home:** a new `roofclip.weld_pieces` + a dedicated `fp3d` pass, reusing the
   convex leaf tools, **never** `compute_roof_clips`. (§2)
2. **Scope:** pairwise pyramid-vs-surface only; roofs are not re-clipped against
   each other, and two pyramids draw whole against each other with an advisory
   `pyramid.overlap` (ruling §8 "not ordered"). Confirm that boundary.
3. **The garage number** is owed on Patrick's file; the termination proof
   (three-roof + pyramid, 0.94 ms) stands without it. OK to proceed to stage 3
   on that basis?
