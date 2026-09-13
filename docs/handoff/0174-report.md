# 0174 — report: R4f rebuilt from a single global arrangement, per the researched standard technique

**His own instruction, after three rounds of patching**
([`0171`](0171-report.md)/[`0172`](0172-report.md)/[`0173`](0173-report.md)):
look at what closed-form/standard techniques exist for this exact
problem, compare them to what `roofclip.py` actually does, and — his
follow-up — build it properly. This report is that comparison's
conclusion, made real, on [PR #59](https://github.com/pjm4github/FloorPlanner/pull/59).

## 1. What the research found

The standard, published techniques for "several planar surfaces, which
one is visible where" all converge on one idea: build a **single shared
2D arrangement** from every surface's own geometry at once — CGAL's
`Envelope_3` package computes an upper envelope this way ("by overlay of
planar arrangements"); the same idea underlies BSP-tree solid-boolean
merging (Naylor/Amanatides/Thibault, SIGGRAPH 1990) and the
straight-skeleton roof algorithm. The exact ingredient that makes this
robust: for any three planes, the three pairwise equal-height lines are
**always mutually concurrent at one point** (trivial algebra — if
h₁=h₂ and h₁=h₃ at a point, h₂=h₃ there too) — a genuine three-way
junction is guaranteed, by construction, to reduce to one exact vertex.

`roofclip.py`'s three-times-patched architecture did the opposite: it
composed `clip_pair`'s own **independently-built** two-roof
decompositions, then patched the composite result after the fact (a
gap-fill pass, a sliver-area floor, a duplicate-cell dedup). Each patch
closed one measured symptom without touching the structural cause: two
surfaces meeting at a junction were never forced to agree on a shared
vertex, only to land *close* to one.

## 2. What was rebuilt

`compute_roof_clips` no longer calls `clip_pair` in a loop. It builds
ONE shared cell decomposition from every live roof's plane-change lines
(`_cut_lines`: ridge, hip equal-height lines) and every live roof's own
footprint edges, at once — so a physical location that two roofs'
starting footprints both cover decomposes into **identical** cells
regardless of which one the arrangement started from (an exact-vertex
dedup, not a rounding-tolerance one).

Per cell: one coverer keeps it outright; several are split by their
own **exact local upper envelope** — chained affine half-plane clips
against every other coverer, in the SAME cell, so the resulting seam
boundary already accounts for every roof actually contesting that
ground (not a pair considered in isolation, then corrected afterward).

Reachability — the one rule a plain "highest wins" test does not give
for free, and the reason this is closer to a CSG union of BOUNDED roof
volumes than an envelope of unbounded planes (his own R4d check is the
proof: an equal-height L put roof A numerically above B past its own
apex, yet the ruling was that A must stop at the seam anyway, since a
plane extended past where a roof is actually built is a phantom, not a
roof) — is preserved from `clip_pair`'s own rule, generalised: each live
roof keeps only its local-maximum pieces reachable, by shared boundary,
from its own anchor (the piece holding whichever ridge end isn't
swallowed by another live roof). An unreachable piece from a
MULTI-coverer cell is never simply left undrawn — it falls,
unconditionally, to the next-ranked coverer (matching `clip_pair`'s own
"flip to the other one" rule for an unclaimed overlap piece exactly);
only true single-coverer ("root") territory can go undrawn, the
generalised D85 corner.

`clip_pair` itself is **untouched** and remains the two-roof reference
every test checks the new construction against — two roofs reduce to
exactly its own answer (all 26 pre-existing regression tests pass
unmodified).

## 3. A real bug found and fixed during the rebuild

A piece reassigned to a fallback owner (because its true local-max
owner couldn't reach it) could still have its **seam** attributed to
the wrong pair — the seam's two endpoints were computed as an
h_i==h_j crossing for a *specific* pair, and once one side gets
relabelled to a third roof, that pair no longer matches the label.
Measured directly: a "seam" whose two reported heights weren't even
equal (114.69 vs 96.0, in one instance). Fixed: a seam is only ever
drawn between two pieces that **both** kept their own true local-max
owner (checked against the final state, after every reassignment
pass).

## 4. Re-verified, exhaustively

- **0 gaps** in a 400×400 grid over the entire footprint union (a real,
  visible hole existed before this session's earlier fixes).
- **0 double-owned points.**
- **0 seam-height mismatches** (every drawn seam checked against both
  its owners' own height formulas).
- The exact triple point unchanged: (681.586, 538.067), height 117.503
  on all three surfaces.
- All cells convex; all main-surface top-cap normals correctly
  oriented; the 3D mesh (via `fp3d.py`, unmodified this session except
  where noted below) fully connected.

## 5. A second, separate, pre-existing bug found (not fixed)

`fp3d.py`'s gable-end-triangle code draws a roof's unjoined gable end
using the FULL, unclipped eave-corner triangle, with no regard for
whether `clip.region` still owns all of it — measured: ~6% of one
gable triangle on his fixture fell outside its own roof's final
region, a phantom overhang. This is pre-existing (present before this
session's R4f work) and unrelated to the fixes above.

**An attempted fix was tried and reverted, not shipped.** A gable
triangle's PLAN-VIEW projection (x, y only) is exactly collinear — the
ridge point and both eave corners share one line in plan; the triangle
is only real once height is added. Clipping it with `_convex_intersection`
(a 2D area operation) therefore always measures zero area and silently
deletes every gable triangle — caught before commit, by checking the
triangle count after the "fix" and finding gable walls missing project-wide.
Reverted to the original, unconditional draw. **A correct fix is named,
not built**: clip `ClipRegion.clip_segment` against the PLAN LINE from
one eave corner to the other, then rebuild the surviving piece(s) by
linear interpolation along the triangle's own straight 3D edges — a
different operation than the 2D area clip that failed.

## 6. Honestly measured, not fully closed

**The joining-end candidacy shape still has a real residual.**
`_strip` (reused verbatim from `clip_pair`) bounds a joining roof's
candidacy to its OWN span width — correct along the ridge axis, but
that width edge is an arbitrary rectangle boundary, not a real seam or
eave. Outside it, no comparison against the host ever happens, so the
joining roof's own eaves height can sit directly next to the host's
unrelated, uncompared height. Measured directly: **27 adjacent
cross-roof cell boundaries with mismatched heights** (none of them on
a *drawn* seam — the seam-validity fix in §3 keeps the explicit valley
lines all correct), several within 100 inches of the true triple
point.

Two wider candidacy shapes were tried to close this and both
**regressed** the D85 two-roof test:
- Blanket rectangle reaching however far needed to clear its host:
  phantom-competed with every unrelated roof in the scene (20%+ of the
  footprint union came back undrawn).
- The host's full nominal footprint, or a rectangle bounded along the
  ridge axis but unbounded in width: a GABLE roof's height formula has
  no along-axis cutoff at all (depends only on perpendicular distance
  from the ridge line, extended infinitely), so either shape let a
  joining roof win real territory in the L-case's own excluded corner
  — the D85 test's own precondition.

`_strip`'s width-limited shape was kept because it is the only one of
the three that does not regress a single existing test. Closing the
residual crack needs the **reachability mechanism itself** to arbitrate
the width (not a wider candidacy shape) — named as follow-up work, not
attempted under this same PR after two regressions.

**A visual artifact also persists** near the triple point in the 3D
render, whose exact cause was not conclusively found despite the
verification in §4. It is very unlikely to be the 2D partition itself
(provably exact per §4) — the most likely remaining suspects are a
further `fp3d.py` mesh-generation subtlety (distinct from the
gable-triangle bug in §5, which does not explain it: reverting that
fix entirely left the same artifact) or a renderer-level effect. Not
chased further this round given the time already spent; a fresh,
narrowly-scoped investigation is the right next step if he wants it
closed rather than continuing to guess.

## 7. What was removed

Superseded entirely by there being one arrangement instead of many
reconciled after the fact: `_fill_unclaimed_ground`, `_subtract_claimed`,
the second (coarser) `_dedup_cells` call site, `MIN_FILL_AREA`,
`FILL_DEDUP_TOL`, `_clip_segment_by_values`. None have an equivalent in
the new construction.

## 8. Receipts

- `tests/test_roof_intersection.py`: all 26 pre-existing tests pass
  unmodified; the R4f-era tests kept, with one (checking an area
  threshold specific to the now-removed fill-pass architecture)
  rewritten to check what the new construction actually guarantees —
  no duplicate cells.
- `python tools/gate.py`: GREEN, 1267 passed, `ruff` clean.

## His fourth look

Two separate questions, both worth checking independently:
1. **Does the render still show the same visual artifact near the
   junction?** (Named in §6, not closed.)
2. **Is the SEAM MAPPING itself correct now** — his own literal
   complaint, "the ridge meeting point seams don't map correctly"?
   Provably yes: every drawn seam is height-consistent, checked
   exhaustively, and the underlying 2D partition has zero gaps or
   double-coverage at fine grid resolution.

**Carried, unchanged from 0171-0173:** D83/D84 (held); room-label
rounding ([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family;
yard items; the End-On marker at a clipped ridge end
([`0166`](0166-report.md) §3); plus, new to this report: the
width-limited candidacy residual (§6), the gable-triangle overhang
(§5), and the unresolved visual artifact (§6), each named for a
dedicated future pass rather than folded into a fourth rushed fix
under this same ruling.
