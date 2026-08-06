---
# permanent key, independent of GitHub
id: 23
title: "A group move strands the region of a room it does not fully own"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:groups
milestone: P4.5

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 19
related: [22]
state_source: status-table
github_issue: null
---

# D23 — A group move strands the region of a room it does not fully own

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 84) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**A group move strands the region of a room it does not fully own.** A rubber band selects only items FULLY inside it, so a wall poking out is left behind; `group_selected` then DUPLICATES the rest of that room's walls into the group, `room_owns_walls` is correctly false, and the room is not carried. Its region stays put while the member walls walk out from under it — the "detached, dashed outline at the original position" presentation. **Measured on `symmetricP1`, band clipping 8% of the plan: 3 of 20 rooms stranded — region-centroid to own-walls-centroid drift Garage 46.7", PKT Off 40.0", Util 23.3"; Garage moved 6 of its 9 walls against 0 of its 9 corners.** **PREDATES P3.5, and the branch improves it: the same drift measured on the pre-P3.5 tree is Garage 148.3".** An earlier claim that re-detection had been *hiding* this is withdrawn — it was landing the room somewhere worse. *Metric caveat, because the two eras do not measure alike:* "a corner matches no wall endpoint" is **not** comparable across P3.5, since before it a longer wall could span an outline edge and a corner legitimately sat mid-wall. The cross-boundary number is the basis-free centroid drift quoted above; the corner columns are within-era only. Distinct from defect 22, which is the identity tear underneath a room that *does* get carried and looks correct. **The fix is a semantics decision, not a repair**, so it is P4.5's: should a room whose walls partly moved DEFORM to follow the corners that moved, or stay put? **Provisional lean, decision reserved: DEFORM-TO-FOLLOW** — once `duplicate_wall` dies and vertex identity carries the geometry, a clipped room following its moved vertices is the *same mechanism* as a party-wall resize, whereas stay-put would need fresh special-casing to hold a room back from corners it holds. The separate gesture-level question — should grouping PROMOTE a clipped room to whole membership? — is UI policy and is decidable independently at P4.5. Characterized by `test_groups.py::test_a_clipped_band_leaves_every_room_coherent`, asserted against the invariant BOTH readings satisfy (per-room walls-moved and outline-moved must agree), `xfail(strict=False)` so it flips whichever way the ruling goes.

## Site

`mainwindow.py` (`group_selected`), `items.py` (`bake`)

## Milestone

**P4.5**
