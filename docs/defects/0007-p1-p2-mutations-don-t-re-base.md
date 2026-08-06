---
# permanent key, independent of GitHub
id: 7
title: "p1/p2 mutations don't re-base op.s"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P3.6

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 7
related: []
state_source: status-table
github_issue: null
---

# D7 — p1/p2 mutations don't re-base op.s

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 72) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**`p1`/`p2` mutations don't re-base `op.s`.**~~ **CLOSED at P3.6 (R4b + R2b), and by the CONDITION rather than by the sites.** The four cited lines were stale and re-surveying them would have pinned a moving target; what was verified tree-wide is that *nothing re-bases `op.s`*. **`s` is now DERIVED** — an opening holds the `Vertex` it is dimensioned off plus an offset, and `s` is read through from those — so there is no stored `s` for a mutation to leave stale and nothing to re-base. It closes structurally, not site by site. Guarded by R1(a)/(b)/(c): a stretch at the far end, a reversal, and a split each leave the opening exactly where it was. **Site list SUPERSEDED BY THE CONDITION at the P3.6 read-back:** the four cited lines are stale (the mutation surface was rebuilt at P3.3's vertex move and P3.5's corner records), and re-surveying them would pin a moving target. What is verified, and what actually closes the defect, is the CONDITION — **nothing anywhere in the tree re-bases `op.s`**: no `op.s +=`, no rebase helper. An anchor from a named end has nothing to re-base, so this closes structurally rather than site by site, and the guard is R1(a)/(b) rather than a count.

## Site

condition verified tree-wide; former sites stale

## Milestone

**P3.6**
