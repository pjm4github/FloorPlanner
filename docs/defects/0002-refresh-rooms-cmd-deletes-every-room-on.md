---
# permanent key, independent of GitHub
id: 2
title: "refresh_rooms_cmd deletes every room on non-active floors"

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
rank: 2
related: []
state_source: status-table
github_issue: null
---

# D2 — refresh_rooms_cmd deletes every room on non-active floors

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 67) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

`refresh_rooms_cmd` deletes every room on non-active floors

## Site

`mainwindow.py:589‑593`

## Milestone

**P0.5**
