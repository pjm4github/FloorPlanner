# 0260 — report: the compose cost built on his word, from the parked patch and past it — the arrangement built from one set of disjoint cells, a neighbour graph for the walk; 15 roofs 32 s → 8 s; the clip pinned as a function of the roofs alone — on `roofclip-cost`, AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0259`](0259-report.md). His word:

> *"Go ahead with the cost tranche from the patch. Also make sure that
> when editing and moving roof sections that all walls, doors and
> windows as well as interior furnishings are all excluded from the
> intersection calculation."*

Built on `roofclip-cost`, ONE commit on `main`'s tip, pushed, PR open.
The checkout is on it.

## 0. WHAT THE PATCH GAVE, measured again first

[`0237`](0237-report.md) §0's probe (`docs/evidence/roof_compose_cost_probe.py`,
his `wiscaway2026-10-07R1.json` plus eight ridges dropped across the
existing ones), re-run on this machine with the parked adjacency memo
applied and nothing else: 12 roofs 4.8 s, 15 roofs **23 s** (against 5.2
and 32 without it). Profiled at 12 roofs: the walk (`_reach`) still 40 %
of the time, 2.2 million memo lookups for 83 walks over some 600 pieces;
`_shared_segment` another 25 %; the rest in the envelope rounds. The
memo answered the same question faster; it did not stop the question
being asked of every allowed pair from every frontier piece, and it did
nothing about the piece count the question is asked over.

## 1. WHAT IS BUILT

**The arrangement, from one set of disjoint cells.** Every line (each
roof's ridge and hips, and the infinite line through each edge of each
roof's domain polygon) used to cut EVERY cell of the whole arrangement
— a roof's end-edge line sliced the cells of roofs it never touched,
and the piece count grew with the product of roofs and lines, not with
the junctions. Now each roof's domain polygons are laid down in turn:
the new polygon is cut by the edges of the cells already there that it
meets; the cells it meets are cut by its own edges (so no cell straddles
a domain boundary — the one invariant the construction needs, coverers
constant within a cell); and the pieces of it already covered are
dropped (their centroid lies in a cell already placed). Then each roof's
own plane-change lines cut only the cells that meet its domain's
bounding box. Same ground, fewer pieces.

Measured on the way: the FIRST cut of this (each roof's domain laid down
as its own cells, bounding-box gated cuts, the vertex-set dedup left to
merge the copies) was wrong, and the fixture that showed it is the test
now. Two roofs' copies of the same ground were cut by different lines —
an end-edge line of a roof far away reached one copy, whose piece was
still large when that roof's turn came, and not the other — so the dedup
could not merge them, a region's cells overlapped each other, and
`region.area()` on his stacked-floor fixture read 307,955 for a roof of
233,861 (74,000 sq in of double counting; the ground itself, sampled on
a grid against the upper envelope, was unchanged). Building from one
disjoint set is what closed it; the cells are now pinned pairwise
disjoint on every promoted roof fixture.

**The neighbour graph, once per piece list.** `_neighbours(pieces)`:
every piece's neighbours (a shared boundary of positive length, the same
`_adjacent`), found by one sweep over the pieces' bounding boxes sorted
on x — `_adjacent` asked only of pairs whose boxes meet, once. `_reach`
follows the lists: each step considers a piece's actual neighbours, not
every allowed piece. The memo and its per-pair question are gone.

**The timings**, the probe's own shape, this machine:

| roofs | 0237 | memo alone | now |
|---|---|---|---|
| 9 | 0.75 s | 0.66 s | 0.25 s |
| 12 | 5.2 s | 4.8 s | 1.7 s |
| 13 | 10.7 s | 10.0 s | 3.3 s |
| 15 | 32 s | 23 s | **8.3 s** |

Four times faster at 15, three at 12; the curve still rises (the
envelope rounds and the per-cell local-maximum clips are the next term),
but a release on a 12-roof level is under two seconds where it was five.

**The clip is a function of the roofs alone — pinned.** It always was:
`sync_roof_clips` hands `compose_building` the scene's `RoofItem`s and
nothing else, and the clip never reads a wall, an opening, a room or a
furnishing. His second sentence is now a test: two crossing roofs, then
the same two with 200 walls carrying 100 openings, 40 furnishings and a
room added around them — the clip is the same geometry, and a spy on
the composer sees only `RoofItem`. For the record, the settle after a
roof gesture (the undo snapshot and the shadow-mode check) walks the
whole document, measured at 0.08 s on his plan: not where the time
went.

**Tests** (`tests/test_roofclip_cost.py`, 11): the roofs-alone pin;
every promoted roof fixture's region area and seam lines against a
record taken under the full-cut arrangement before this change
(`tests/data/roofclip_ground_0260.json`), with the constructed cells
pairwise disjoint; and the scaling, eight ridges over the promoted
two-level fixture, bounded. `test_roof_overhang_3d.py`'s positive
control on R2 counts 12 riser segments of the same boundaries where the
finer partition gave 15.

## 2. THE RECEIPT

`--quick` passed; ruff clean; the full gate GREEN on the branch commit.

## 3. TIER

**AMBER** — the clipper's arrangement is rebuilt. The visible regions
and seams are pinned unchanged on every promoted fixture, but his own
plans are the check: the roof editor on `wiscaway2026-10-07R1.json` and
the house, moving roof edges, the releases quicker and nothing of the
roofscape different.

## 4. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 12), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
  It is the probe's input; promoting it would let the scaling test run
  on it.
* `README.md`.

## 5. WHAT HAPPENS NEXT

His check of the PR. `docs/evidence/roofclip-adjacency-memo.patch` is
superseded by this and can be deleted on his word. Behind it: nothing
ordered — 0248's items 8 and 9 named.

**Carried:** unchanged from [`0259`](0259-report.md).
