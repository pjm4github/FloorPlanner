---
# permanent key, independent of GitHub
id: 42
title: "The party-wall drag has the same self-intersection exposure as the group bake, and it is"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 43
related: [30]
state_source: row
github_issue: null
---

# D42 — The party-wall drag has the same self-intersection exposure as the group bake, and it is

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 108) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The party-wall drag has the same self-intersection exposure as the group bake, and it is unaddressed.** Recorded at P4.5 §2a on Patrick's explicit condition: *"check whether the same exposure exists on the party-wall drag… If there's a shared vertex-translation applier, attach the check there and both callers get it. If there isn't, implement at bake and record a row."* **Measured: there is no shared applier.** Three structurally identical ones exist — `walls._DragVertex.apply` (the drag), `items.GroupItem._apply_corner_records` (bake and rotation), and `rooms.RoomItem._translate` (the label-drag / float move). Each relocates a vertex and rebinds the wall ends and outline edges holding it; there is no single seam to attach a check to. **The exposure is precisely NON-UNIFORM corner movement**, which is a sharper statement than "the drag": `RoomItem._translate` moves every corner of its room by one delta, so it is rigid and **cannot** self-intersect; a bake of a fully-owned room is likewise rigid. What can deform is the drag (moves one or two corners of a room that keeps the rest) and a clipped bake once no-copy lands. So the check went in at bake per the ruling, and **the drag path is knowingly uncovered**. The obvious fix — unify the three appliers behind one seam and check there — is itself the right shape (three implementations of one concept is F2's disease) but is deliberately out of P4.5's scope, per *"do not expand P4.5 into auditing every mover"*. **ADJACENT FINDING, recorded not acted on:** those three structurally identical appliers are themselves a **consolidation candidate** — one concept with three implementations is F2's shape, and the reason this row exists at all is that there was no single seam to attach a check to. **SHAPE CHANGED AT P4.5(24), and in the direction that helps: three appliers, one more CALLER, and a demonstrated pattern for how two gestures should differ.** Retiring the P3.1 shim's fourth writer — the endpoint drag, which split identity on every mouse-move event — could have minted a fourth applier. It did not: the endpoint drag now runs on `walls._DragVertex.apply`, the BODY drag's own applier, and the two differ only in **what they gather** — one deliberately detached end, versus every end on the corner. **That is defect 30's lesson applied before the fact** (there, the gather was wrong and the applier was not), and it is evidence the consolidation is the right shape rather than a tidy-up: the seam this row asks for is exactly where the gathers would meet. Pinned by `test_the_endpoint_drag_runs_on_the_same_applier_as_the_body_drag`, which fails the day a fourth applier appears. **Argued Phase 6**, with the command layer (`MoveVertices` is exactly that seam); explicitly **not P4.5's**, and not to be acted on now.

## Site

`walls.py` (`_DragVertex.apply`); the three appliers named above

## Milestone

**unassigned — the applier-unification task, argued Phase 6**
