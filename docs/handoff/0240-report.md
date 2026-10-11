# 0240 — report: his word on 0239 — "the wall loop test is right", the build ordered; the state saved for a fresh session

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). His word to [`0239`](0239-report.md):

> *"first, save the plan so that a /clear can be done and then I will
> commence with the build - the wall loop test is right"*

So: the read-back's §3 is ordered as written, §4's first question is
answered — **"under an overhang" means outside the covering level's wall
loops** — and its other two answers stand unless he says otherwise
(build to the seam; plan view unchanged). Nothing is built in this
commit; this is the state a fresh session starts from.

## 1. THE BUILD, exactly as ordered — the next session's first task

Branch `roof-overhang-build` (AMBER). In `floorplanner/viewer/fp3d.py`'s
roof builder, for a clipped roof:

1. After its visible cells, mesh **the cells of its own nominal footprint
   that the clip hid**, at the roof's own surface, **when the cell's
   centroid lies outside every wall loop of the covering roof's level**
   (the level whose roof hides it). The covering roof is found from the
   clip's final assignment (`diag["final"]`'s `owner_of` / `coverer_rank`,
   or recomputed from the cells' top coverer); the level's wall loops
   are the rooms' outlines or the exterior walls' closed loops of that
   level, in plan.
2. Where the lower roof's surface would rise above the covering roof's
   inside such a cell, cut at the seam (the clip already names it);
   build to the seam, not through it.
3. `_wall_under_roofs` unchanged: the gable wall climbs already.
4. Tests on `fixtures/short-angle-roof.json`: `rf1`'s roof mesh reaches
   x=120 (not 108); nothing of `rf1` east of 120; `rf2` the mirror
   (reaches 354, nothing west of it); `rf4`'s overhang slab still above
   both; the gable-end fixture, the three-ridge fixtures and the dormer
   fixture build unchanged (compare mesh vertex sets before/after).
5. Re-render the three evidence pictures with
   `python docs/evidence/render3d.py fixtures/short-angle-roof.json <out.png> -90 18 20 220 100 380`
   (the west junction) and the slice at `100 130 100 380`.

Then the report, PR, his check of the 3D view.

## 2. SAVED WITH THIS COMMIT, so nothing lives only in a session

* [`docs/evidence/roofclip-adjacency-memo.patch`](../evidence/roofclip-adjacency-memo.patch)
  — the parked compose-cost memo ([`0237`](0237-report.md) §0);
  `git apply --check` clean against this tree.
* [`docs/evidence/roof_compose_cost_probe.py`](../evidence/roof_compose_cost_probe.py)
  and [`roof_grip_drag_probe.py`](../evidence/roof_grip_drag_probe.py)
  — the instruments behind 0237 §0's numbers (they read
  `fixtures/incoming/wiscaway2026-10-07R1.json`, his, still in
  `incoming/`).
* [`docs/evidence/render3d.py`](../evidence/render3d.py) — the headless
  3D renderer (0239 §0), already landed.

## 3. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 4. WHAT HAPPENS NEXT

A fresh session reads the snapshot, then this file, and builds §1.
Behind it: the compose cost, as its own tranche, starting from the
patch.

**Carried:** unchanged from [`0239`](0239-report.md).
