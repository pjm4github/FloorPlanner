---
# permanent key, independent of GitHub
id: 66
title: "A departing room CARRIES its neighbours' walls -- extract does not undo what join welded"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
closed_by: null
rank: 67
related: [61, 62, 63, 65]
state_source: measurement
github_issue: null
---

# D66 — A departing room carries its neighbours' walls

## The measurement

Three states on `fixtures/wiscaway2026-08-08.json`, room `WIC`, moved 24″ by
`_translate` (production's own float mover) — **pristine** (before the room ever
landed at that site), **after-join**, **after-leave** with the room taken right
out of the plan:

| state | walls at the site |
|---|---:|
| pristine | 2 |
| after-join | 4 |
| after-leave | **2** |

**The count returns. The geometry does not:**

```
pristine      (534, 546)-(630, 546)    (534, 636)-(630, 636)
after-leave   (558, 546)-(654, 546)    (558, 636)-(654, 636)
```

**Same length, shifted exactly 24″ — the room's own displacement.**

## The cause, stated as a hypothesis about BINDING, not geometry

**Those neighbour walls did not decay. THEY FOLLOWED THE ROOM.**

`join_room` welds via `share_coincident_ends`, folding the arriving room's ends
onto the plan's vertices. **In v5 a shared vertex IS identity** (Phase 3), so a
neighbour wall now ends on a `Vertex` the room also holds. When the room is
extracted and translated, `_translate` moves the vertices the room holds — and
the neighbour's end goes with them.

**That is deform-to-follow working exactly as designed, on the way out, where
nobody intended it.**

So the fault is not at the vacated site and it is not about extents:

> **LEAVING DOES NOT UNDO WHAT JOINING DID.** `join_room` welds; `extract_room`
> privatises via `_private`; and the privatisation evidently does not sever the
> *neighbour's* binding to the vertex the room is about to carry away. Whoever
> takes this starts at **the binding**, not at the geometry.

**Restoring the extents afterwards would be symptom repair** and is explicitly
not the fix — it would paper over a live identity error with a geometry
correction, and the next gesture would reproduce it.

**It is the fourth instance of one asymmetry in this family:** the join does
something and no gesture un-does it. [D61](0061-a-room-move-permanently-adds-two-walls.md)
(the split), [D62](0062-weld-scene-leaves-room-outlines-holding-a.md) (the weld's
divorced corners), [D65](0065-weld-scene-is-implicated-in-three-separate.md)
(the weld's I15 violations), and now the weld's *shared identity* surviving the
departure. **Related, and not four independent supports** — one design gap seen
four ways.

## What this does NOT explain

**It does not explain the redundant collinear corners D61 was filed for.** A
neighbour wall carried 24″ is not a degree-2 collinear vertex on a straight run.
The two are different faults and this record does not close D61's.

## Evidence

`docs/evidence/d61_2b_three_state_baseline.py` — the three-state baseline, with
the open-space run kept and **labelled degenerate**: with no neighbours there is
nothing to split on arrival and nothing to re-fuse on departure, so its zero says
nothing.

**Controls:** the site must contain neighbours (the open-space run is the
negative case and reports 0 → 4 → 0); the room must be taken right out of the
plan in state 3, so a rejoin elsewhere cannot add that site's splits to the
count; and `SEPARABLE` — an earlier attribution at 24″ measured the two polygons
0.00″ apart and correctly reported two walls **AMBIGUOUS** rather than forcing
them, which is what kept a wrong "2 vacated" out of the record.

**Boundary of the evidence, recorded so the next reader knows where it stops:**
a **short move**, whose before and after footprints overlap, cannot be attributed
by separating the sites geometrically. That case is unreached by this method.

## Ruling

*(Open — filed 2026‑08‑11.)* **Filed as its own defect on the reviewer's ruling**,
with the cause stated as a binding question rather than a geometry one.
**Parked** with [D63](0063-a-coalesced-outline-partly-rebounds-on-save.md)'s
remaining halves, [D64](0064-the-save-writes-an-outline-corner-at-a.md) and
[D65](0065-weld-scene-is-implicated-in-three-separate.md): register entry, no work, and
not to be reopened without a new instruction.
