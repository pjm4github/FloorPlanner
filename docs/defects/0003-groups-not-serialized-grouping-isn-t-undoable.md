---
# permanent key, independent of GitHub
id: 3
title: "Groups not serialized; grouping isn't undoable; undo dissolves groups"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:groups
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 3
related: [4]
state_source: row
github_issue: null
---

# D3 — Groups not serialized; grouping isn't undoable; undo dissolves groups

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 68) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

Groups not serialized; grouping isn't undoable; undo dissolves groups

## Site

`mainwindow.py:1042‑1083`

## Milestone

**P4.5** — *partly closed early: defect 4's fix made group→move→undo restore the plan correctly. The remaining half (the group itself surviving save/load and redo) is still open and is held by characterization test 3.*
