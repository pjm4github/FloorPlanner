---
# permanent key, independent of GitHub
id: 69
title: "An auxiliary control panel on the 3D view, toggling which components appear"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
closed_by: null
rank: 70
related: [68, 50]
state_source: row
github_issue: null
---

# D69 — An auxiliary control panel on the 3D view

## The requirement, not a design

**A panel on the 3D view toggling which components appear:** floors,
furnishings, openings, and **later roof and foundation**.

**Patrick has deferred the detail.** This record is the **requirement**; it
deliberately does not propose a layout, a widget set or a place on screen.

## WHERE IT LIVES, AND WHAT IT MAY NOT DO

**The panel is PRESENTATION and lives in the shell. It sets `build_model`'s
parameters and RE-BUILDS; it does not reach into meshes.**

That follows from the boundary recorded at
[`VIEWER_NOTES.md`](../../floorplanner/viewer/VIEWER_NOTES.md) §1:

> **A toggle that changes WHICH GEOMETRY EXISTS is a `build_model` parameter. A
> toggle that changes what is DRAWN from geometry already built is view-side.**

**Building it as a mesh filter is the obvious wrong turn**, and it is wrong for a
reason that is already on disk: **two renderers import `build_model` unchanged**
(the pyqtgraph shell and the Qt Quick 3D spike), so a filter in either shell
would scope one and not the other. `furnishings=False` is the existing precedent
— the pattern is established rather than invented.

Which toggles fall on which side is a per-toggle question the design pass
answers: **floors and furnishings are geometry** (both are already
`build_model` parameters); **openings are probably geometry too**, since they cut
wall meshes; a future *wireframe* or *palette* switch would be view-side.

## A MANUAL CHECK HAS NOW WANTED IT — noted 2026‑08‑15, handoff 0018 §7

**The instance is `walk_in_shower`'s bench.** [`handoff/0018-ruling.md`](../handoff/0018-ruling.md)'s
check named it as the row that carries the verdict — *"its body is translucent
glass, so the interior is visible from outside… the only one of the three where
the correct state can be seen."* **Measured, and it is not**: the bench's
geometry is correct (confirmed by dumping the mesh directly — the right
position, the right size, the right material bucket), but the `fp3d.py` CLI
viewer does not visibly composite an opaque interior mesh through a translucent
body, at any glass alpha tested (0.35 and 0.12 both tried; the bench is equally
invisible at both).

**`sauna`'s interior was already named as unobservable** at the ruling's own
§7 — an OPAQUE enclosure hides its interior structurally, by design, which is
a different and unavoidable limit. `walk_in_shower`'s case is sharper: its body
is deliberately translucent *so that* the interior would be visible, and it
still is not — a **renderer** limit, not a **material-choice** limit.

**Not built here — still not scope for this task.** Recorded because two
manual checks in one ruling have now individually reached for exactly this
requirement, which is worth knowing when this record's design pass is finally
taken: **"reveal an opaque interior mesh behind/inside a translucent body" is
not a hypothetical use case invented for the panel — it is the second real
check that needed it.**

## Ruling

*(Open — filed 2026‑08‑11.)* **Requirement filed, design deferred.** The
`build_model`-parameter boundary is the one thing ruled now, because it is free
today and expensive after the panel exists.
