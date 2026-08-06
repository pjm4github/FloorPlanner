---
# permanent key, independent of GitHub
id: 48
title: "The invariants have never checked the scene the user edits - design_from_scene WELDS on the way"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-05
closed: null
closed_by: null
rank: 48
related: [41, 44]
state_source: row
github_issue: null
---

# D48 — The invariants have never checked the scene the user edits - design_from_scene WELDS on the way

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 113) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The invariants have never checked the scene the user edits — `design_from_scene` WELDS on the way out, so a scene-level identity fault emits a clean document.** Row 44's sibling, and the same shape one layer lower: 44 is *consistency, not history*; this is *the document, not the scene*. Filed 2026‑08‑05 at the fragment ruling, **not P4.5's to fix.** Worked example, measured: the fragment product holds **20 distinct `Vertex` objects on 10 geometric points**, with four corners carrying 3–4 duplicates each — and the walk collapses them (**20 → 10 vertices, 16 → 12 walls, `merged=4`, `unwelded_ends=0`**), so `check(doc, deep=True)` returns **CLEAN** on a scene whose corners are not shared at all. Every one of the fifteen is therefore blind, by construction, to the exact class P3.1's vertex table exists to prevent: two wall ends at the same point that are not the same corner. It also means a green `check()` cannot be read as "the scene is sound" — only as "the *welded projection* of the scene is sound", which is the instrument-boundary rule again (the corollary table in the plan's Working agreement). **Proposed instrument, to be scoped separately: a SCENE-level check that geometric coincidence implies identity** — for every pair of wall ends within `vertex_weld_in`, assert they are the same `Vertex` object — run where `--verify-design` already runs, so it costs nothing by default. Not designed here; the corpus consequences (legacy loads arrive unwelded by design, P2.1) are exactly what scoping it has to answer.

## Site

`design/bridge.py` (`design_from_scene`, the weld); `design/validate.py` (the fifteen)

## Milestone

**unassigned — argue at the invariant's own read-back, with row 41**
