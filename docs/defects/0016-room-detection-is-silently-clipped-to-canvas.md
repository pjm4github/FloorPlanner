---
# permanent key, independent of GitHub
id: 16
title: "Room detection is silently clipped to canvas_rect() - a plan larger than the canvas loses its edge"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P3.5

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 18
related: []
state_source: row
github_issue: null
---

# D16 — Room detection is silently clipped to canvas_rect() - a plan larger than the canvas loses its edge

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 83) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**Room detection is silently clipped to `canvas_rect()`** — a plan larger than the canvas loses its edge rooms with no warning. Found by the P0.3 harness, not by any test.~~ **CLOSED STRUCTURALLY at P3.5.** `_RoomGrid` rasterised onto a grid sized by `canvas_rect()` and treated any flood reaching the grid edge as unenclosed, so the clip was inseparable from the method. The replacement is a walk over the wall graph, which has no canvas in it at all — closed by deletion rather than by a bounds check, which is the only kind of fix that cannot regress. Pinned by `test_detection_is_not_clipped_to_the_canvas` (a room built well past the canvas edge detects and reports its true area).

## Site

`rooms.py:29` (`_RoomGrid`, deleted)

## Milestone

**P3.5 (done)**
