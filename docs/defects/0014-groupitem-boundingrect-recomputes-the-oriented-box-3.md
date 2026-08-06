---
# permanent key, independent of GitHub
id: 14
title: "GroupItem.boundingRect recomputes the oriented box 3× per paint"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:perf
milestone: P0.6

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 15
related: []
state_source: status-table
github_issue: null
---

# D14 — GroupItem.boundingRect recomputes the oriented box 3× per paint

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 80) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

`GroupItem.boundingRect` recomputes the oriented box 3× per paint

## Site

`items.py:509‑528`

## Milestone

**P0.6**
