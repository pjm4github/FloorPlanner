# 0189 — report: his first look at the 3D wall clip — one thing, fixed on the branch; stopped for his second

**Code, 2026‑09‑13, on [`0188`](0188-report.md).** Patrick's look at PR #62,
his words in full: *"that looks pretty good. The dashed lines look good
… We need to move the walls down just a little so that the wall doesnt
poke through the roof in 3D view at some angles."* With it, two pictures:
the plan with the R5a trace on a hip-ended roof over a loft (right), and
the 3D view from above — a wall showing through the roof at the junction
of a wing and the main.

## 1. WHAT IT WAS

[`0188`](0188-report.md) §1 capped each wall piece **on the roof's top
surface** and §3 named the underside as "one constant if he wants it".
His look is why that was the wrong side: the wall's top face and the
roof's top face are then **the same plane** wherever the roof is lower
than the wall, and a depth test cannot order two coplanar faces — at
grazing angles the wall's face wins some pixels and shows through. The
viewer culls no back faces (`fp3d.py` sets none), so the same fight
would recur on the underside if the cap sat exactly there.

## 2. WHAT IT IS NOW — fixed on `roofs-3d-wall-clip`, PR #62 updated

One constant, `WALL_CAP_BELOW_ROOF_IN = ROOF_T + 0.5` (4½″): every cap
sits the slab's own thickness under the top surface — the roof's
underside — **plus half an inch of clearance**, so no wall face ever
coincides with a roof face from either side. His "just a little" is that
half inch on top of the 4″ the slab already draws. Nothing else in the
clip changes: the same territories, the same exact splits and level sets,
the same byte-identical fall-through when no roof intrudes (the
clearing-roof test now clears by the underside, at 102½″ eaves over 96″
walls).

## 3. THE CHECK — receipts

`tests/test_viewer_wall_clip.py` re-derived to the underside: the drop
pinned to `ROOF_T + 0.5` in the first test; the gable wall's corners at
75½″ (eaves 80″ less the drop), its crossings at 60.58″ off the ridge
(`(132 − 4.5 − 96) / 0.52`), flat at 96″ under the ridge; the
zero-overhang eaves wall within half a thickness of 75½″; the wing's eave
at 75½″ under the L; his three-ridge fixture at 120″ walls — **0**
vertices above the owning roof's underside, the roofless control above
it. Full suite **1308 passed**, `ruff` clean, gate GREEN on the branch.

## 4. `fixtures/incoming/`, with ages

Unchanged from [`0187`](0187-report.md) §4 (the two promoted `w7`
duplicates, 23 days). Exit 2 on his word.

## 5. WHAT HAPPENS NEXT

His second look at the same view. On his word PR #62 merges, branch
deleted in the merge step; then [`0186`](0186-ruling.md) §3's R5b dormer
read-back. **Carried:** unchanged from [`0188`](0188-report.md).
