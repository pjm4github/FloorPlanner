---
# permanent key, independent of GitHub
id: 20
title: "Merging a collinear run can REVERSE the survivor without swapping left/right, silently flipping"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 35
related: []
state_source: row
github_issue: null
---

# D20 — Merging a collinear run can REVERSE the survivor without swapping left/right, silently flipping

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 100) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Merging a collinear run can REVERSE the survivor without swapping `left`/`right`, silently flipping every side on that wall.** `merge_collinear` wrote `w1.v1, w1.v2 = far1, far2`, and `far1` is the survivor's *far* end — so whenever the run extends behind the survivor's `v1`, the merged wall comes out pointing the other way while its `left`/`right` stay as written. Every side on that wall is then on the wrong side. **Found by single-sourcing at P3.4(i)** — not by a test, not by review: it only became visible when the same decision logic had to serve a scene that *renders* sides. **Fixed in the pure op at P3.4(i)** (the survivor keeps its own direction; every other end projects onto its axis), with its own test. **Still live scene-side** in `_coalesce_wall_impl`, which is why this is a defect and not a footnote: coalesce runs on wall draw/move release, on load/import, on ungroup and from Edit ▸ Coalesce all walls now, so the flip is reachable in shipping code paths **today**. It **dies at P3.4(iv)**, when the scene-side callers are retired.<br><br>**The instructive part is why nothing caught it.** A reversal slips straight past **I6**, because I6 checks that a wall's sides *agree with the rooms that name it* as a **set** — not **which** side is which. That is precisely the blind spot the P1.3 winding-pin test was built for ("without this, a flipped winding swaps every left/right and I6 still passes"), and this is the **first wild specimen proving the blind spot is real** rather than theoretical. If a cheap side-orientation invariant ever joins the deep three, this defect is its justification — *noted, not scoped.*

## Site

`design/topology.py` (`merge_collinear`, fixed); `walls.py` (`_coalesce_wall_impl`, still live)

## Milestone

**P3.4** — *pure op fixed at (i); scene-side dies at (iv)*
