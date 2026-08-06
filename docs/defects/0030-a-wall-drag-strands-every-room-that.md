---
# permanent key, independent of GitHub
id: 30
title: "A wall drag strands every room that holds the moved corner but owns no wall in the dragged run"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 21
related: [23]
state_source: row
github_issue: null
---

# D30 — A wall drag strands every room that holds the moved corner but owns no wall in the dragged run

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 86) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**A wall drag strands every room that holds the moved corner but owns no wall in the dragged run — its walls partly follow and its region does not.** Found by the P3.8 exit survey's own row, with a REAL viewport-driven drag rather than an emulation. **Measured on `symmetricP1` at the 4-way corner (582, 714), held by Dining, Foyer, Great Room and Kitchen:** a body drag of the 198″ Dining/Kitchen wall moved the corner **(0, −24)**; Dining and Kitchen followed; **Foyer and Great Room were left behind**, each ending with **one wall end at the new corner and one at the old** while its outline stayed wholly at the old. No I11 in that geometry — the rooms simply stop meeting their own walls. **Mechanism:** `WallItem.mousePressEvent` step 4 gathers outline edges from the rooms of the walls in the **collinear run**, which is not the set of rooms **holding the corner**. Both app corner-movers that get this right collect holders from the geometry (`GroupItem._corner_records`; and the same fix applied to the defect-28 test). **Distinct from defect 23** (a group move stranding a room it does not fully own) and from the **endpoint** drag, where leaving the outline behind is the designed open-side behaviour — this is a *body* drag, where the corner is meant to carry everything on it. Pinned `xfail` by `test_wall_move.py::test_a_dragged_corner_carries_every_room_that_holds_it`, whose two preconditions (4 holders; the corner actually moved) are asserted before its verdict — the first draft xfailed on the PRECONDITION, which is exactly the vacuity the defect-28 lesson warns about.

## Site

`walls.py` (`mousePressEvent` step 4)

## Milestone

~~**unassigned — argue P4.2**~~ **FIXED at P4.2, as a BUG, not a semantics ruling — the read-back's dissolution of the deform framing was ratified:** the room follows because *its corner moved* (Phase 3's identity rule); the gather is now holders of the corner via vertex identity, scene-wide, exactly how the two correct corner-movers already gather (`_DragVertex.ends`, `GroupItem._corner_records`); identity makes a floor filter redundant (I2). **The 23-vs-30 boundary, stated for P4.5 to inherit clean:** 23 is group *membership* under a clipped band — the room's walls were duplicated into a group it never joined, and no widening of any gather reaches it; 30 was vertex *identity*. Nothing in the fix touches `duplicate_wall`, `GroupItem.bake` or the band gather; deform-vs-stay-put for non-holding rooms stays reserved at P4.5. Receipt: the pinned test's xfail flipped to a hard pass on exactly the gather change, its two preconditions asserted before the verdict. **CORRECTED AT THE MINI-GATE (2026‑08‑01), and the first cut's own claim is withdrawn:** blanket follow-the-moved-vertex was wrong — Patrick's screenshot (`symmetricP3`, Dining/Kitchen wall dragged down) caught it tearing a **diagonal** across Foyer and Great Room, whose boundary at that corner is the *continuation* the anti-shear split deliberately holds still. The corrected rule: the split makes the old corner **two** corners, and each room's corner goes with **its own boundary** — run-bordered rooms follow the moved vertex, continuation-bordered rooms re-point to the stationary twin the split minted (recorded in step 1). Receipt, fail-first: the revised pin `test_a_dragged_corner_splits_by_each_rooms_own_boundary` fails against the first cut ("borders the continuation but was dragged off it") and passes on the correction, with a no-diagonal assertion so the tear cannot return; measured on `symmetricP1` — Foyer and Great Room outlines byte-identical through the drag, Dining/Kitchen resize, zero new off-axis edges. **THIRD FINDING at the mini-gate (2026‑08‑01): the MIXED corner.** A run can cover only *part* of a neighbour's side (Master Suite's south side slides; Hall's top side runs on under Clst) — that room's corner is run-backed on one adjacent edge and continuation-backed on the other, and one corner cannot serve two stretches now on different lines: follow tears one, stay tears the other. Fix: the mixed corner becomes **two corners joined by an OPEN step edge** (`wall: null`, drawn dashed — outline surgery at drag start, the same moment the anti-shear split runs), plus hygiene: `collapse_degenerate_outline_edges` drops zero-length edges (a closed gap's welded corner pair; a step whose drag ended where it began). Receipts, fail-first: `test_a_partial_side_slide_steps_the_neighbours_outline` red against the pre-fix tree, green on the fix; end-to-end on `symmetricP1` — clean gaps, drag the Master Suite/M Bath wall 24″ down: zero diagonals, zero stranded corners, Hall the correct stepped polygon, Clst untouched.
