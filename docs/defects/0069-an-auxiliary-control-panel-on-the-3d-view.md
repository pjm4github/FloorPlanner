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

## Ruling

*(Open — filed 2026‑08‑11.)* **Requirement filed, design deferred.** The
`build_model`-parameter boundary is the one thing ruled now, because it is free
today and expensive after the panel exists.
