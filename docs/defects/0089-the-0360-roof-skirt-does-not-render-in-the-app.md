---
# permanent key, independent of GitHub
id: 89
title: "The 0360 roof-skirt does not render in the app"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-11-22
closed: null
closed_by: null
rank: 89
related: []
state_source: report
github_issue: null
---

# D89 — The 0360 roof-skirt does not render in the app

## The report

**Patrick, 2026‑11‑22,** checking the merged 0360 stage‑3 work: *"The
roof-skirt doesnt seem to work yet."* The S° roof-skirt — the sloped roof
surface that is meant to ramp from the host fascia up to the attic floor on a
cantilever dormer whose face stands past the fascia (A < C) with the host eave
below the dormer floor, replacing the flat §8.4 cantilever floor
(`DORMER_EDGE_ORDERINGS.md` notes 7b/7c) — does not appear in his live app
view.

## What IS verified (so the gap is narrow)

The skirt mesh *is built* by the headless model:

- Mesh enumeration over the committed evidence JSONs (`fp3d.build_model`,
  `furnishings=True`) shows the two A < C cantilevers **W09 and W31** return
  **`roofs` × 2 and no `dormer_floor`** (the skirt stands in for the flat
  floor), while the flat-floor rows keep `dormer_floor` and `skirt_mode` off
  restores it. Regression `test_a_cantilever_roof_skirt_replaces_the_flat_floor`
  holds on the committed W09 fixture.
- The ramp height is correct: an instrumented build reported the W09 skirt
  spanning **84 → 108** (host fascia up to the attic floor), the right
  direction, non-inverted.

So the geometry layer produces a skirt. What Patrick does not get is the skirt
**on screen** in the running app.

## Not yet diagnosed

The break is somewhere between the built mesh and what the live viewer draws —
candidates not yet ruled out: the skirt `roofs` mesh is produced but culled /
occluded / z-fought by the host roof or the (removed) flat floor at that
location; the live app feeds the dormer a state where `skirt_mode` resolves to
off or the A < C / host-eave-below condition is not met for his real dormers
(the evidence cases are a synthetic base design, not his plan); or the real 3D
view path differs from `build_model` (e.g. `fp3dq`/`scene.qml`). The standard
catalog render angle (yaw 25) also tucks the eave-side skirt under the dormer
body, so a first step is to confirm whether it is truly absent or merely hidden
at his camera.

## Status

**OPEN.** Filed on Patrick's word while landing 0360 stage 3 (PR #110) so the
work merges without losing the observation. Landing recorded in
[`handoff/0364-report.md`](../handoff/0364-report.md).
