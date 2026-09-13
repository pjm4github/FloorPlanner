# 0175 — report: R4f, his fourth check — a real hole, closed with a cross-roof riser

**His fourth check of [PR #59](https://github.com/pjm4github/FloorPlanner/pull/59)**
(after 0174-report.md's global-arrangement rebuild): a screenshot
showing a visible hole/gap at the ridge junction — "the ridge lines
have holes in them."

## 1. Confirmed real, not a lighting artefact

Disabling floors (`--no-floors`) showed the DARK BACKGROUND straight
through the gap, not the ceiling plane — a genuine absence of mesh
coverage from that viewing angle, not a shading quirk.

## 2. Root cause — and why 0174's own "0 gaps" measurement was still true

0174-report.md measured **zero gaps** in an exhaustive 400×400 grid
over the footprint union, straight down. That measurement was correct
and remains correct — the 2D partition genuinely has no gap. The
visible hole is a **3D lift** problem, not a 2D ownership problem:

0174's own disclosed, honestly-measured residual (the joining-end
candidacy shape's own width-limited edge, `_strip`, can seat a
joining roof's eaves height directly next to a host's unrelated
height at a boundary that is not a real seam) means two **different**
roofs' adjacent 2D cells can have **mismatched heights** at their
shared boundary. Each roof's own extrusion (`_prism_slab`) gives its
surface a short skirt — a constant `ROOF_T` (4 inches) drop below its
own top. Where two adjacent, different-owner cells disagree in height
by more than a few inches (measured: up to ~30 inches on his
fixture), each side's own 4-inch skirt stops **far short** of the
other's, leaving an **open vertical slot** between them.

Looking straight down, both roofs' TOP surfaces still cover that
(x, y) — hence zero gap in the top-down grid. Looking from an oblique
angle, the camera can see directly into the slot — his screenshot.

## 3. The fix — additive only, never touches 2D ownership

`_cross_roof_risers` (new, `fp3d.py`): for every pair of **different**
live roofs on a level, finds every boundary segment where their final
clip regions touch, and — where the two roofs' own heights there do
**not** already agree (i.e. it is not a real, drawn seam) — returns
the (plan segment, height range) needed to close the gap.
`_riser_quad` (new): builds a flat, double-sided vertical(-ish) quad
spanning generously past both sides' own skirts, closing the slot.

This is a **pure addition** to the mesh, computed once per level from
the clip results already being built. It never changes which roof
owns which 2D territory, so it **cannot** reopen the D85 regression
that two wider candidacy shapes already caused during 0174's own
rebuild — the fix for this report carries no risk to that
already-hard-won two-roof regression.

Where two roofs' heights already agree at a boundary (a real seam),
`_cross_roof_risers` finds nothing to add there — verified directly
on the T fixture (`clip_pair`'s own two-roof reference): zero risers.

## 4. Verified

- The hole is gone in both a plain and a `--edges` render, at the
  original screenshot's angle and at several zoom levels — what
  remains is a correctly shadowed roof valley (architecturally
  expected at a complex multi-ridge junction), not a defect.
- `tests/test_viewer_model.py`, two new tests:
  - **Positive control**: the fixture must produce at least one riser
    (else the coverage test below would pass for the wrong reason —
    no mismatched boundaries to fail on).
  - **Negative control**: the T fixture's own exact seam produces
    zero risers.
  - **The main receipt**: every riser's own height range, sampled
    along the interior of its edge (never at an endpoint — an
    endpoint is a vertex, often shared with a third roof that one
    pairwise riser cannot fully resolve alone, but a vertex is a
    single zero-width point that can never itself be a visible 2D
    hole), must be covered by some mesh triangle.
- **A real trap, caught before it shipped a test that could not have
  failed**: the first draft of the coverage check used a 2D
  barycentric XY lookup — which cannot see a near-vertical riser wall
  at all, since its own XY projection is degenerate (the exact same
  class of bug as the gable-triangle trap named in 0174-report.md).
  Rewritten as a genuine 3D point-in-triangle test before commit.
- Full suite: 1270 passed (2 new), `ruff` clean, gate GREEN.

## His fifth look

Does the render now look right at the junction — no hole, no visible
crack — and do the existing two-roof cases (T, L) still look
unaffected (they are, by construction: risers never fire where a real
seam already exists).

**Carried, unchanged from 0174 §6/§7:** the joining-end candidacy
shape's own width-limited edge is still the underlying reason a riser
is needed at all (not eliminated, just visually closed) — a future
pass using the reachability mechanism itself to arbitrate the width
could remove the need for risers entirely, but was not attempted here
given the two prior regressions that approach already caused.
`fp3d.py`'s gable-end-triangle overhang (0174 §5) is unrelated and
still open. D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard
items; the End-On marker at a clipped ridge end
([`0166`](0166-report.md) §3).
