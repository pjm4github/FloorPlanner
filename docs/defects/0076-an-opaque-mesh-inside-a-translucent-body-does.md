---
# permanent key, independent of GitHub
id: 76
title: "An opaque mesh inside a translucent body does not composite in the 3D viewer"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-15
closed: null
closed_by: null
rank: 76
related: [69, 75, 77]
state_source: row
github_issue: null
---

# D76 — An opaque mesh inside a translucent body does not composite in the 3D viewer

**Filed as its own record, per [`handoff/0022-ruling.md`](../handoff/0022-ruling.md)
§4 — not folded into [D69](0069-an-auxiliary-control-panel-on-the-3d-view.md),
which is a feature request for a components panel and would bury a rendering
limitation as one line inside it.**

## The finding

**An opaque mesh placed inside a translucent one does not visibly composite
through it, in `fp3d.py`'s `GLViewWidget`-based viewer, at any glass alpha
tested.** Found while checking the vessel/enclosure split
([`handoff/0021-report.md`](../handoff/0021-report.md) §6):
`walk_in_shower`'s bench is built correctly — the right position, size and
material bucket, confirmed by dumping the mesh's own bounding box directly
(`furnishings:stone  z[0.0, 18.0]`, standing on the floor, inside
`furnishings:glass  z[0.0, 78.0]`) — and it is not visible in the render.
Alpha 0.35 (the shipped body material) and 0.12 (a synthetic test value,
restored afterward) both show the same plain glass box, so it is not a matter
of the body being *too* opaque.

> **AN OPAQUE MESH INSIDE A TRANSLUCENT BODY DOES NOT COMPOSITE, AT ANY ALPHA
> TESTED.** That is the general statement, not "the bench is hard to see" —
> it reaches every future item of this shape: a cabinet interior, a fixture
> within a glass enclosure, anything nested inside a translucent envelope.

## Why it is not merely `walk_in_shower`'s problem

`sauna`'s interior is unobservable too, but for a *different and unavoidable*
reason — its body is opaque wood, closed and capped, so there is structurally
nothing to see regardless of the renderer (named at
[`handoff/0018-ruling.md`](../handoff/0018-ruling.md) §7). `walk_in_shower`
is the sharper case: its body is deliberately translucent glass **so that**
the interior would be visible, and it still is not. That is a **renderer**
limit, not a **material-choice** limit — the distinction [D75](0075-a-recessed-floor-feature-is-not-representable.md)'s
neighbouring record draws between a limit and a gap applies here too.

## Why it silently defeats manual checks

**It is how the finding was made at all.** A check that asks a person to look
at the render and confirm an interior feature is present will read as *absent*
whether the feature is genuinely missing or merely uncomposited — the picture
looks identical either way. Any future AMBER check of this shape (an interior
part, inside a translucent body) inherits the same blind spot unless the check
is answered from the mesh directly, as [`0022-ruling.md`](../handoff/0022-ruling.md)
§3 requires for row 1 of the enclosure-form check.

## Relationship to D69

[D69](0069-an-auxiliary-control-panel-on-the-3d-view.md) is the REQUIREMENT
for a components panel (floors, furnishings, openings toggled on/off) and
already carries a note citing this same instance as evidence the panel is
needed. This record is the **rendering limitation itself** — compositing, not
visibility toggling — and would remain true even if D69's panel existed and
simply hid the body outright rather than seeing through it. Cross-referenced,
not merged: a toggle that removes the body is a workaround for this limit, not
a fix of it.

## Ruling

*(Open — filed 2026‑08‑15, on [`handoff/0022-ruling.md`](../handoff/0022-ruling.md)
§4's instruction.)* Not built here, not scope for the vessel/enclosure split.
Recorded as its own defect so it is discoverable independent of D69's design
pass, and so the next item of this shape is checked from the mesh rather than
re-discovering the same blind spot by trial.
