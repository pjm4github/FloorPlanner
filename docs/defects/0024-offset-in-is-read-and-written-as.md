---
# permanent key, independent of GitHub
id: 24
title: "offset_in is read and written as a CENTRE distance in topology.py and as a NEAR-EDGE distance"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:schema
milestone: P3.6

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 31
related: []
state_source: status-table
github_issue: null
---

# D24 — offset_in is read and written as a CENTRE distance in topology.py and as a NEAR-EDGE distance

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 96) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**`offset_in` is read and written as a CENTRE distance in `topology.py` and as a NEAR-EDGE distance everywhere else — an opening-width/2 disagreement inside one document format.** The schema says *"offset from that vertex to the opening's near edge"*; `bridge._walls_of` emits `(loc) - ow/2` and `bridge._opening_s` inverts with `off + ow/2`. But `topology.graph_from_design` builds its planner view with `s = off` (or `length - off`), and `topology._reanchor` writes `offset_in = s`, both omitting the half-width. **Measured on `symmetricP1` wall `w6`, a 36" door anchored 6.793" from v1: the schema puts its centre at 24.79", the planner thinks 6.79" — 18.00", exactly half the door.** Self-cancelling for a `v1` anchor on the kept segment (the same error on read and write), which is why nothing caught it; NOT self-cancelling for `v2` anchors, for the segment assignment, or for the straddle test `ov.s - half < s < ov.s + half` — which is precisely the value **R2's total-split semantics now rest on**. The scene feeder (`graph_from_scene`, off `OpeningItem.s`) is correct, so this is one planner with two feeders and only one of them mis-feeding it — the "one concept, two implementations" failure P3.4 was built to avoid, arrived on the feeder side. Found at the P3.6 read-back.

## Site

`design/topology.py` — **THREE sites, not the two first registered**: `graph_from_design` (read), `_reanchor` (write), and a fourth hand-written copy of the same arithmetic inline in `apply_merge_plan` (write), found only when the fix turned its test red. All three now route through `_reanchor`, so the conversion exists once — which is the actual cure for a defect whose shape was one concept with four implementations.

## Milestone

**P3.6**
