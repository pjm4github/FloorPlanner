---
# permanent key, independent of GitHub
id: 5
title: "RoomItem has no itemChange → dangling WallItem.rooms at 5 sites"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P0.5

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 5
related: []
state_source: status-table
github_issue: null
---

# D5 — RoomItem has no itemChange → dangling WallItem.rooms at 5 sites

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 70) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

`RoomItem` has no `itemChange` → dangling `WallItem.rooms` at 5 sites

## Site

`rooms.py`, `mainwindow.py:472,592,677,1234,1287`

## Milestone

**P0.5**
