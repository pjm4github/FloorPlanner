---
# permanent key, independent of GitHub
id: 21
title: "relocated_to silently renames a corner that was never named"

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
rank: 50
related: []
state_source: row
github_issue: null
---

# D21 — relocated_to silently renames a corner that was never named

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 115) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**`relocated_to` silently renames a corner that was never named.**~~ **FIXED at P3.5.** P3.3's rule is "a moved corner is the SAME corner, so it keeps its uid" — but `relocated_to` copied `self._uid`, and uids are minted **lazily on first read**. On a vertex nobody had yet named, that `None` crossed the move and the "same corner" got a fresh identity the first time anything asked. **Nothing observably broke** while only the document walk read uids — which is exactly why it survived P3.1, P3.3 and P3.4 — and it becomes a live bug at **P4.5**, which serializes groups by member id: a group whose member corner had never been walked, then dragged, comes back naming a vertex that no longer exists.<br><br>**Found by P3.5's by-construction test**, not by review, and the near-miss is the instructive part: `test_relocation_carries_the_vertex_identity` has pinned this rule since P3.3 and **passes for a reason it does not state** — it reads `v.uid` before relocating, forcing the mint. A test that establishes the precondition it is meant to be testing cannot see the bug. Fix: read `self.uid`, forcing the mint at relocation. Deliberately *not* the per-READ allocation P3.1 removed — a relocation is a genuine move, orders of magnitude rarer than the reads on the paint path. Pinned by `test_relocation_carries_identity_even_when_never_named`, which constructs the unnamed case the original could not.

## Site

`floorplanner/vertex.py` (`Vertex.relocated_to`)

## Milestone

**P3.5 (done)**
