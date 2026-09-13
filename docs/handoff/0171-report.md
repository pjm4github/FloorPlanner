# 0171 — report: R4f built — the three-ridge clip, a seam real only where no third roof is higher

**Answers [`0170-ruling.md`](0170-ruling.md).** Built on branch
`roofs-r4f-multi-ridge`, [PR #59](https://github.com/pjm4github/FloorPlanner/pull/59),
open, AMBER, stopped for Patrick's own check.

## 1. What was actually wrong

`compute_roof_clips`'s REGION fold was already correct before this ruling: a
roof's final region is the intersection, across every OTHER roof, of
`clip_pair`'s own kept region against that partner — and since `clip_pair`'s
two regions for a pair already partition their shared overlap, intersecting
across any number of partners cannot manufacture a point two roofs both
claim, whatever the partner count. Measured directly on his own fixture: at
no sampled point (45×45 grid over the union of all three footprints) do two
roofs' final regions both contain the same point.

What was actually broken was narrower than "the whole algorithm is
pairwise" (0170 §1's own framing) — it was the **SEAMS**: every pairwise
seam was accumulated with no check at all against the fold. A seam found
between roof A and roof B survived even in ground a third roof C's own clip
had already taken away from BOTH A's and B's final region — a valley line
drawn straight through C's own roof body. Verified this was the live bug
before any fix: on his fixture, 13 of 108 sampled seam points had a third
roof strictly higher there.

## 2. The fix — two filters on every accumulated seam

1. Clip the raw pairwise seam through its own owning roof's FINAL,
   fully-partner-intersected `ClipRegion` (`ClipRegion.clip_segment`, the
   same exact Cyrus-Beck geometry `RoofItem._clipped` already draws with).
2. Clip it again, directly, against every OTHER roof's own height —
   `h_owner >= h_third`, exact linear interpolation, the same idiom
   `_clip_by_values` already uses for a cell's own vertices, generalised
   here to a bare segment (`_clip_segment_by_values`, new).

(1) alone was not enough — a point can survive pairwise reach against every
partner taken ONE AT A TIME (reachability is not simply a height
comparison) and still be ground a third roof measurably clears. (2) is the
literal, unconditional statement of the ruling's own sentence: "a seam
draws where the top two surfaces are equal AND no third is higher." With
both filters: 0 of 108 sampled seam points have a third roof higher there.

`clip_pair` itself is untouched — every one of its existing direct callers
and the 26 pre-existing tests in `tests/test_roof_intersection.py` that
exercise it (including the L-case's own reachability logic, the far-side
island, the 45° wing) pass unmodified. Two roofs inside a
`compute_roof_clips` call reduce to exactly `clip_pair`'s own answer, since
there is no third partner for either filter to have anything to remove —
the regression 0170 §3 names by name, and now has its own dedicated test
(`test_r4f_a_two_roof_pair_inside_a_three_roof_call_is_unaffected`).

## 3. What was measured on his own fixture

`fixtures/threeRidgeFloorplan.json` — promoted from `incoming/` under exit
1 (`fixtures/README.md` updated) — three roofs (`rf1`/`rf2`/`rf3`), every
one its own span and pitch, ridges converging near the plan's middle-right.

- **No point drawn by two roofs at once** — checked directly on a 45×45
  grid over the union of the three footprints, not merely trusted from the
  region-fold's own construction.
- **No seam segment crosses a roof measurably higher there** — 0 of 108
  points sampled along every seam segment, five points each.
- **Exactly one true triple point** — among every seam vertex the three
  roofs carry, exactly one lands inside all three footprints with all
  three surfaces tied: **(681.586, 538.067), height 117.503 on all three
  surfaces.** His own eyeballed estimate was "≈(682, 538), all three
  heights ≈117.5″" — matched to within a rounding error, not merely
  "close."
- **The 3D mesh follows with no code of its own changed** — R4e's own
  design (`fp3d.py` consumes `clip.region.cells`/`.seams`/`.ext`
  generically); `tests/test_viewer_model.py`'s new test finds a mesh
  vertex at the same plan location and the same height.

## 4. Measured, not hidden: the residual gap

At this genuine three-way junction, a small patch near the meeting point
still draws for nobody — about 3.6% of the footprint union on this
fixture, sampled at 50000 random points. This is the same CLASS the
two-roof algorithm's own module docstring already accepts for two roofs
("a corner past the seam … drawn by nobody") — a point no single pairwise
reach/anchor computation ever assigned to either partner, even though some
roof's true body plausibly covers it once all three are weighed together.
It is not claimed to be zero; `test_r4f_drawn_by_nobody_stays_a_small_measured_minority`
guards it at under 6% so a future change cannot silently make it worse
without the gate noticing. A from-scratch single global cell arrangement
(computed once for all roofs together, rather than composed pairwise) was
attempted first and rejected: it produced a WORSE result on this same
fixture (10.4% drawn-by-nobody, plus real reachability bugs under heavy
fragmentation) despite passing the same 26-test regression suite, and
getting its own connected-component logic exactly right for an arbitrary
number of roofs is a materially larger undertaking than the effort
available this session — left named here rather than shipped half-built.

## 5. Receipts

- `tests/test_roof_intersection.py`: all 26 pre-existing tests pass
  unchanged; 6 new (`test_r4f_*`) covering every claim in §3-4 above.
- `tests/test_viewer_model.py`: 1 new test, the 3D mesh receipt.
- `python tools/gate.py`: GREEN, 1264 passed (was 1257), 7 deselected
  (perf lane, unchanged), `ruff` clean.

## 6. His check

Open `fixtures/threeRidgeFloorplan.json`. The three valleys meet at one
point and stop; no seam runs past another roof; nothing pokes through;
select any of the three → whole rectangle, deselect → re-clipped (D65/R4d's
own already-built behaviour, unaffected here). Also worth a glance: do the
T and L two-roof cases (already in the app from R4d) still look right —
this PR changes nothing about them by construction, but a look costs
nothing.

**Carried:** D83/D84 (held); room-label rounding ([`0131`](0131-ruling.md)
§2); delta-snap sites; D61-family; yard items; the End-On marker at a
clipped ridge end ([`0166`](0166-report.md) §3); the drawn-by-nobody
residual named in §4, should he want it closed further; a genuinely global
(non-pairwise) construction, should the residual or a future 4+-roof case
call for it.
