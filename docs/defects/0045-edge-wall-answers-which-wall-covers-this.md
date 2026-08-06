---
# permanent key, independent of GitHub
id: 45
title: "_edge_wall answers \"which wall covers this edge?\" BY GEOMETRY - the last survivor of the"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 45
related: [44]
state_source: row
github_issue: null
---

# D45 — _edge_wall answers "which wall covers this edge?" BY GEOMETRY - the last survivor of the

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 110) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**`_edge_wall` answers "which wall covers this edge?" BY GEOMETRY — the last survivor of the detection-from-geometry family this migration exists to cure.** Named at P4.5 (2026‑08‑04) when its group exemption was retired, recorded as a **known survivor with a stated justification** rather than left to be rediscovered as an oversight. It scans the scene for walls collinear with the edge, measures coverage, and picks by a heuristic. That is `bounding_walls()`'s shape — proximity answering a question the model should answer outright — and `bounding_walls()`'s workflow uses died at P4.4 (the clipboard) and P4.5(2) (grouping). **Why it survives — CORRECTED 2026‑08‑04 by measurement, because the first version of this justification was wrong on its main clause.** It said the search exists for "an outline that arrived **from a file** with edges naming nothing". **It does not: neither file path calls the binder at all.** The v5 apply reads the binding straight out of the document (`wmap.get(e["wall"])`), and a legacy file is converted to v5 first and then goes through that same apply — so on the file path **the document carries the binding and the loader reads it**, which is F3's *cure*, not F3's disease surviving. Measured consumers of `bind_room_walls`, which is what actually reaches `_edge_wall`: **CSV import** (`csvio.py`), the **macro `room` token**, the **Room tool** (`view.py`), **room_boolean**, the **explicit join** (`extract.py`), **undo restore**, and the legacy `Project` apply (`planio.py`) — i.e. paths that mint a room from geometry with no bindings to read, plus the two repair paths for an edge whose wall died or stopped spanning it. That is still a real reason; it is a different one. **AND THE TWO NULLS ARE SAFE, measured:** `wall: null` means "deliberately open, draw it dashed" (P3.7) and would mean "unknown, go find it" to a binder. Constructed where they actually diverge — the walk emits null when no chain **spans** the edge, while `_edge_wall` accepts **partial** cover — a half-covered edge round-trips with its null intact through both the v5 and the legacy path (`test_a_deliberately_open_edge_survives_a_round_trip`). The distinction holds because the loader never asks the question. **THE DIVERGENCE IS DEFINITIONAL, AND IT IS ONLY LATENT — say so plainly for whoever wires the next caller.** Two answers to one question live in the tree: the walk (`_rooms_of` → `_walk`) calls an edge covered only when a **chain of walls spans it end to end**; `_edge_wall` calls it covered on **partial** cover of at least `MIN_WALL_LEN`. On a half-covered edge those disagree by construction — one says open, the other says found. They never collide **today** only because no document path reaches the finder: the v5 apply reads the stored binding and the legacy path converts first. **That is protection by CALL GRAPH, not by semantics.** So: **adding any document-side caller of `_edge_wall` — a loader that re-derives, a validator that repairs, an importer that "fills in" nulls — converts this latent divergence into a live defect that silently closes deliberate openings.** Whoever wires one must reconcile the two definitions first, or scope the new caller to spanning cover only. **Not P4.5's to remove** — the task is group semantics, and removing this needs the load path to carry the binding in the document instead of re-deriving it, which is a format question. **The soft part, named: the TIE-BREAK heuristic** — ends-match, then coverage, then geometrically-smallest. It is now pinned as a contract (`test_the_edge_wall_tie_break_is_a_contract`) rather than left as an observation, because row 44 proved two overlapping-but-not-identical candidates are a **legal** document state, so the ambiguity is reachable in a valid plan rather than a corner case. **Argued Phase 6**, with the command layer, where "the document states the binding" is the natural replacement.

## Site

`rooms.py` (`_edge_wall`), 3 callers: `bind_room_walls`, `repair_edge_bindings`, `split_partially_covered_edges`

## Milestone

**argued Phase 6**
