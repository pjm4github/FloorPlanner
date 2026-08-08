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

## Evidence

**The instrument exists as of 2026-08-07 (G2): `design.bridge.scene_identity_report`.
REPORT-ONLY — it gates nothing, raises nothing, and no operation calls it.**

It asks the question `WallItem.end_vertex` already states: *two ends are the same
corner iff this returns the same object for both (`is`, never `==`)*. For every
pair of wall ends within `WELD_TOL`, are they the same `Vertex`?

**It reproduces this record's measurement independently**, from the live scene
rather than from the walk — `docs/evidence/d48-scene-identity.json`:

| | this record said | measured by the instrument |
|---|---|---|
| distinct `Vertex` objects | 20 | **20** |
| geometric points | 10 | **10** |
| corners carrying duplicates | 3, 4, 4, 3 | **4, 4, 3, 3** |
| walk collapse | 20 → 10 vertices, 16 → 12 walls | **20 → 10, 16 → 12** |
| `merged` | 4 | **4** |
| `unwelded_ends` | 0 | **0** |
| `check(doc, deep=True)` | CLEAN | **`[]`** |

The last two rows are the point: the scene's corners are not shared at all, the
weld hides it, and every one of the fifteen accepts the result.

**Scoped the way the walk is scoped, which is what keeps it quiet on correct
scenes.** Per floor, then per vertex namespace. A floating room has deliberately
broken its sharing with the plan (I12, P4.2), so its coincidences with plan walls
are correct rather than faults — a checker that did not know this would report
every parked float as broken. The partition rule was **extracted from
`design_from_scene` into `_partitions()` and is now called by both**, so the walk
and the check cannot disagree about which ends may be compared.

**Differential receipt** — same two walls, one corner shared and not:

    two walls meeting at (120, 0), ends NOT shared   extra_vertices = 1
    after `w2.set_end_vertex("p1", w1.end_vertex("p2"))`  extra_vertices = 0

**STILL OPEN, and deliberately.** This record proposed running the check *where
`--verify-design` already runs*. That is **not** done here: wiring it would change
what an operation produces, which is an AMBER decision, and the corpus
consequence this record already names — legacy loads arrive unwelded **by
design** (P2.1) — is exactly the scoping question that has to be answered first.
G2 delivers the instrument; where it runs is a separate ruling.

### Residual measured at A1 (2026-08-07), and it is this record's family

A freshly fragmented product leaves **18 distinct `Vertex` objects on 16
geometric points** — three corners inside a single floating room's own namespace
that are coincident but not identical. Per room: `Room 1` 6 walls / 8
wall-vertices, `Room 2` 6 / 7, `Overlap` 4 / 4.

It is not caused by the fragment op. Traced: each region's loop is built with
one vertex per corner (12 → 6 on a six-wall loop, measured), and the split
reappears between `rebuild_all_walls` and the room being claimed — i.e. inside
`bind_room_walls` / `share_outline_vertices`, which re-points some wall ends
onto the detected outline's vertices and not others.

It costs nothing today: `check(deep=True)` is clean, `room_owns_walls` holds,
the drag carries the region, and no edge reads as open. It is recorded because
it is exactly what this record exists to make visible — a coincidence the
document walk welds away, so no invariant will ever report it.
