# 0183 — report: his check of 0182 — the 3D view passed, the plan was missing a joint; seams are now read off the final pieces

**Patrick, 2026‑09‑13, on [`0182`](0182-report.md):** *"That looks
fantastic!"* (the 3D view of `threeRidgeFloorplan.json`) — *"The overhead
view is not correct yet … only a few of the joints are missing"* (marked
in red and blue on the plan: the rf2/rf3 seam beside rf2's ridge end).
Same branch, `roofs-r4g-full-footprint`, PR #60. AMBER continues.

## 1. What was missing, and why

The rf2/rf3 seam had the pieces (825, 369)–(788, 468)–(773, 509) and
(756, 553)–(737, 549), and nothing between (773, 509) and (756, 553) —
the stretch beside rf2's ridge end, where rf2's south arm is wrapped by
rf3. The regions were right (the 3D view draws from the same clip and
was right); only the seam list was short.

Cause, measured on the round trace: 0182's per-piece prune splits a
cell ALONG an equal-height line so a roof loses only the piece it lost.
From then on that line is a boundary between two single-owner cells and
is never again a crossing found inside one cell — and seams were
collected from exactly that crossing bookkeeping. The joint he marked is
the one that formed that way (rf2's south arm re-enveloped after rf1's
overshoot pruned).

## 2. Fixed: the seam is defined by what it is

`compute_roof_clips` now reads seams off the FINAL pieces: every shared
edge of positive length between two roofs' pieces along which both
surfaces agree at both ends (new `_shared_segment`; a point contact is
not a shared edge). The crossing bookkeeping inside a round still exists
for what it is needed for — the seam-blocked reach walk — and no longer
decides what is drawn. A shared edge where the surfaces do not agree is a
real step, the class `fp3d`'s riser pass already treats by the same test.

## 3. Receipts

* New `test_0182_every_equal_height_boundary_between_two_roofs_is_a_drawn_seam`:
  the definition asserted globally on the fixture — every equal-height
  shared edge between two roofs' final cells is covered by a seam of BOTH
  roofs — and the joint he marked is present for rf2 and rf3 (it bends
  once at rf3's ridge line, so it is two segments).
* The plan re-rendered headlessly: the rf2/rf3 seam is continuous from
  (825, 369) to rf2's ridge end; everything else unchanged.
* All prior receipts stand unmodified (0% blank, the pinch, D85, the L,
  the triple point, the riser refinement); `ruff` clean; gate GREEN — the
  census is in the landing commit.

## His check

The plan view again, at the junction — the marked joints — and, since
the seam list changed for every clipped roof, the L and T fixtures'
plans once more.

**Carried:** unchanged from [`0182`](0182-report.md).
