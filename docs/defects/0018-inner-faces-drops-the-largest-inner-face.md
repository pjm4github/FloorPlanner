---
# permanent key, independent of GitHub
id: 18
title: "inner_faces drops the largest INNER face as the \"outer boundary\" - discarding a real room"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P1.3b

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 34
related: []
state_source: row
github_issue: null
---

# D18 — inner_faces drops the largest INNER face as the "outer boundary" - discarding a real room

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 99) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**`inner_faces` drops the largest INNER face as the "outer boundary" — discarding a real room.**~~ **FIXED at P1.3b.** The true outer boundary is opposite-wound and already excluded by the majority-sign filter, so `inner[1:]` threw away the biggest *room* (symmetricP1's Garage, 868.5 sf). Fix: keep the majority winding, drop *all* opposite-wound faces (one per component), never by size — in both `design/topology.py` and `tools/migrate_to_design_v5.py`. Retargeted P3.5 → **P1.3b** because P2.1's import traces outlines, so the bug would silently fall back to stored corners for the largest room of every imported plan.

## Site

`design/topology.py`, `tools/migrate_to_design_v5.py` (`inner_faces`)

## Milestone

**P1.3b (done)**
