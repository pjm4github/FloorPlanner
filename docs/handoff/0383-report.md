# 0383 — report on 0382. The census is corrected and reconciled: 22 top-reductions (my 0380 grid was too coarse and saw 3), 8 below-base by the column instrument (a min-vertex read over-counts). The 22 PNGs are regenerated with class+fall in the INDEX, and the lean-to test now runs on a committed reduction of the BR3 plan, RED on 0379, GREEN now. Patrick's word is given; merging.

2026-11-27, Code. Branch `dormer-climb-floor-0372` on `c2b4c33` (A + B's corner,
0380). No `fp3d.py` change here — §2 and §3 are evidence and a test only, so
Patrick's look stands. PR #115.

## 1. The census missed 19 of 22 because its grid was too coarse (§2, tops)

You are right. My 0380 census sampled **28 linspace points** across each wall's
bbox — about 13 in apart on a 360 in plan — and the class-1 fin sits in a narrow
eave strip beside the cheek; a 13 in step walks over it, so those cases read
"0 changed". Re-measured on a **2-inch grid** by barycentric z at the column (and
re-checked at 1 in / 0.1 in — same sets), against `2f39c90`:

| Class | n | Δtop (max column fall) | cases |
|---|---|---|---|
| 2: LV1 wall in front of the face, under the rake | 6 | 70–74 in | W02 W08 W26 W38 W41 W62 |
| 1: LV1 wall under the eave overhang beside a cheek | 16 | 8.7–13.7 in | W01 W07 W09 W25 W31 W37 W40 W49 W52 W53 W61 W65 W68 W71 W72 W75 |

**22 cases, your 22 exactly**, and **0 tops raised anywhere**. Every change is a
reduction: the old territory-only `dormer_over` let the fin climb; the
box+territory gate removes it. (My Δtop for class 2 clusters at 70–74, not your
28; the difference is that I report the max column fall — the full fin height —
not a per-point spread. The case set and the class split are the same.)

## 2. Below-base is 8, by the column instrument; a min-vertex read over-counts (§2, base)

Measured the same way — barycentric z at the column, lowest wall surface, cur vs
`2f39c90` — the base-drop adds material below a face/cheek base in **8 cases**:
W01 W07 W25 (26 in), W09 W31 W40 W61 (24 in), W37 (23 in). The result is sharp:
each is 23–26 in, and the next case is 0.00 — nothing between. It holds at a 1 in
grid and a 0.1 in threshold, so this is not the coarse-grid undercount of §1; 8
is exact.

Your 15 comes from a min-vertex read, and that instrument misreads this scene.
Run globally, "lowest wall z dropped while the top held" finds **0** (the LV1
walls sit at z = 0 and own the minimum, which no pier can lower). Run per wall
mesh, still **0** (a mesh aggregates its level's walls, so its min is pinned at
the floor). Any min-vertex variant either sees nothing or, keyed on a whole
wall's extent, counts the vertex and triangulation changes the fin removal leaves
behind — every one of the 8 below-base cases is also a top-fall case, so an
instrument that asks only "did this wall's lowest z move" cannot separate new
base material from the fin's departure. The right instrument is the one you set
for A in 0380 — barycentric z at the column — and it gives 8. INDEX carries the
per-case class, Δtop and below-base.

## 3. The 22 PNGs, regenerated (§2, evidence)

`make_cases.py` re-run for the 22 at `c2b4c33`; each reproduces its ordering. The
generator rewrites the case JSON too, but only the session-label `uid`s change
(V12→V6, …) — the geometry is byte-identical — so I reverted the JSONs and kept
only the PNGs. INDEX gains a `0382 §2 census` section: ID, class, Δtop, and
below-base for all 22, the 4 unchanged (W05 W29 W51 W67) named. W02's PNG now
shows the wall in front of the face gone (your §5 check 3).

## 4. The lean-to test now runs on a committed reduction, not the frozen file (§3)

`tests/data/dormer_lean_to_face_base_0383.json`: the BR3 case cut down to the
**29 walls** of its cluster, the **two roofs** it turns on, and the dormer
`f135`. Rooms, the other 140 furnishings, annotations, cameras and the
provenance (it named the plan and Patrick) are stripped; the kept items carry the
plan's own geometry, untouched. It reproduces the frozen numbers exactly — lean-to
134 at x 803/810/942, the cheek at (799,640) = 211.2, hipped `rf4` 124.0 / 128.7 /
123.7 — and is **RED on 0379's `roof_beneath` (112.9)**, GREEN now.

Both roofs are load-bearing for the case, and dropping either answers "why a small
scene does not":
- **without `rf2` (the host)** the dormer anchors to nothing and builds no piers —
  the face column reads empty;
- **without `rf4` (the skirt)** there is nothing over the base to close it, so it
  drops to the host strip at 112.9 — the 0379 symptom itself.

So the irreducible scene is walls + those two roofs + the dormer, exactly your
list. `test_a_face_wall_over_a_lean_to_keeps_its_base` loads it and drops the
`skipif`; `test_a_cheek_wall_...` (W01, committed) is unchanged.

## 5. B2, the gate, and the merge

B2 (the two floor tabs hanging at the hipped front corners, outside the hips) is
the §8.4 floor under the dormer's overhang where there is no attic to close —
recorded for C/D/E as you ruled, not touched here.

`tools/gate.py` GREEN (ruff + OFF + ON). §2 and §3 add a fixture, a test, the 22
PNGs and the INDEX section; no code moved, so your look holds. Patrick's word is
given ("passes my review"), so with §2 and §3 done and the gate green on the tip,
PR #115 meets all three of your merge conditions. Merging, then the furnishings
lane (0378), then C/D/E.
