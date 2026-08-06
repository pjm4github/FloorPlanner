---
# permanent key, independent of GitHub
id: 31
title: "The group selection box stretched as the group was dragged - leading edge at ~2× the mouse"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:groups
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 22
related: []
state_source: row
github_issue: null
---

# D31 — The group selection box stretched as the group was dragged - leading edge at ~2× the mouse

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 87) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The group selection box stretched as the group was dragged — leading edge at ~2× the mouse, trailing edge static.** Found at **Gate 3** (every file, clean included). **TWO MECHANISMS AT ONE SITE, both measured before either was touched.** (a) `GroupItem._content_points` **mixed frames**: wall children contribute `ch.p1`/`ch.p2`, already in the group's frame, while furnishings contributed `ch.mapToScene(...)` — SCENE. The two agree only while the group sits at the origin, so a move shifted the furnishing points and `boundingRect()`, read in the item's own frame, applied that translation a **second** time. (b) the cache was dropped in `ItemPositionChange`, which fires **before** the move commits, so any rebuild during it stored the box for the position being *left* — **measured: the reported box lagged the group by exactly one drag step** (move to (48,0) → box grew by the *previous* delta, 24). **Receipt:** a walls-only group is stable and a group with one furnishing **at the edge** stretches — the discriminating prediction held; after the fix all growth is 0.0 at every offset. The first draft of that repro put the furnishing at the **centre**, where it never determines an extreme, and reported a clean box for a reason unrelated to the mechanism. Fix: `mapToParent` (the same query asked in the frame the answer is used in), and stop dropping the cache on move — the box no longer depends on where the group sits. `_invalidate_box()` was already dead code; every site assigns `_obox = None` directly.

## Site

`items.py` (`_content_points`, `itemChange`) — **defect 14's site**

## Milestone

**Gate 3 (fixed, pre-merge)**
