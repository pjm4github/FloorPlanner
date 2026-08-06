---
# permanent key, independent of GitHub
id: 12a
title: "WallItem._attached is one of defect 12's unfiltered paths, and P3.3 raises its stakes"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P3.3

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 13
related: [12]
state_source: row
github_issue: null
---

# D12a — WallItem._attached is one of defect 12's unfiltered paths, and P3.3 raises its stakes

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 78) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**`WallItem._attached` is one of defect 12's unfiltered paths, and P3.3 raises its stakes.**~~ **FIXED at P3.3.** A cross-floor coincident end wrongly dragged by the scan was a *transient* bug that ended with the drag; promoting that discovery into real vertex sharing would have made it permanent, because a vertex carries exactly one level — so unfiltered promotion would either violate **I2** outright or silently rewrite a wall's level. Fix: `w.floor != self.floor` at the **loop head** of the scan, so cross-level sharing is impossible by construction rather than filtered afterwards. Two tests pin it, both built on geometrically identical walls on two floors (what a leaking scan cannot tell apart): the other floor is neither shared with nor dragged, and is never even scanned.

## Site

`walls.py` (`mousePressEvent`, the `_attached` scan)

## Milestone

**P3.3 (done)**
