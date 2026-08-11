---
# permanent key, independent of GitHub
id: 65
title: "weld_scene creates I15 violations -- the third finding on one function"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-10
closed: null
closed_by: null
rank: 66
related: [62, 63, 61]
state_source: measurement
github_issue: null
---

# D65 — `weld_scene` creates I15 violations, and it is the third finding on one function

## The finding

**`weld_scene` writes outline-completeness violations into saved files.** Measured
across four lanes on six plans:

| plan | on disk | load + save | **+ `normalize_walls`** | + coalesce |
|---|---:|---:|---:|---:|
| `roundedMultifloor` | 0 | **0** | **3** | 3 |
| `farmplaceBIGmultifloor` | 0 | **0** | **4** | 4 |
| `wiscaway2026-08-09R` | 2 | 2 | 1 | 1 |
| `wiscaway2026-08-08`, `symmetricP1`, `planc1.v5` | 0 | 0 | 0 | 0 |

**A plain round trip produces zero on every plan** — the negative control — so
the writer alone is innocent. Sub-pass attribution puts the seven on **`weld_scene`**:

| plan | loaded | + `merge_collinear_scene` | **+ `weld_scene`** | + `split_body_landings` |
|---|---:|---:|---:|---:|
| `roundedMultifloor` | 0 | 0 | **2** | 3 |
| `farmplaceBIGmultifloor` | 0 | 0 | **4** | 4 |
| `wiscaway2026-08-09R` | 2 | 2 | **1** | 1 |

Merge produces none; `split_body_landings` adds one more on `rounded`; and on
`08‑09R` the weld actually *repairs* one, 2 → 1.

**The user-facing route is `Edit ▸ Coalesce all walls now`, then save.** The
outline coalesce is not the producer — measured, it creates **zero** scene-level
violations on all five plans, exactly as its predicate promises.

## Why this record exists at all: THREE FINDINGS ON ONE FUNCTION

`weld_scene` has now been implicated three times, and the third is what makes it
worth naming the function rather than the faults:

| # | finding | record |
|---|---|---|
| 1 | leaves room outlines holding a `Vertex` no wall holds — **divorced corners, 49/56/78/57** | [D62](0062-weld-scene-leaves-room-outlines-holding-a.md) |
| 2 | its repair changes nothing about the rebound; producer 2 survives it | [D63](0063-a-coalesced-outline-partly-rebounds-on-save.md) |
| 3 | **creates I15 violations** — 7 across two plans | *this record* |

**THESE ARE NOT THREE INDEPENDENT SUPPORTS, and the register must not read as
though they were.** They are three consequences of **one operation**: folding two
coincident wall ends onto a single `Vertex` while the room outlines that named
them are updated by a *different* mechanism, or not at all. D62 is that gap seen
as identity; this record is the same gap seen as geometry — a wall end lands on a
corner that some room's outline edge now runs straight through without naming.
**Counting them as three pieces of evidence for "weld_scene is broken" would be
one mechanism read three times**, the error the working agreement names at D62.

**What three findings DO license is a statement about the function rather than
about each fault:** `weld_scene` mutates the wall graph without a complete
account of what the room outlines holding those corners must become. P4.2
established the repair at **one** call site (`join_room`); `close_gap` has it;
`weld_scene` got it at D62 for identity and still has nothing for geometry.

## Status

**Reported, not fixed.** I15 now names the state at both document boundaries
(load reports, save asks) — so the fault is visible where it was silent, which is
the precondition for fixing it rather than the fix.

**The repair is NOT obvious and must not be guessed at.** The candidate — after
welding, re-split any outline edge that now runs through a wall end — is
`split_partially_covered_edges`' family, and running it plan-wide from
`weld_scene` is exactly the shape the *"a tidy-up pass that outlives its mess"*
rule warns about. **Measure the producer at the vertex before choosing a pass.**

## Evidence

`docs/evidence/i15_coalesce_can_it_produce_one.py` →
`i15-coalesce-can-it-produce-one.json` · the four-lane and sub-pass attributions
are quoted above from the runs recorded in PR #20's description.

**Controls:** the plain round trip must produce 0 (**PASS**, six plans); the
outline coalesce must produce 0 at scene level (**PASS**, five plans); and the
I15 predicate is validated against the fixture known to carry exactly 2
(**PASS**) before any zero here is believed.

## Ruling

*(Open — filed 2026‑08‑10.)* **Filed separately from D62 and D63 on the
reviewer's ruling**, because three findings on one function is a statement about
the function. **Cross-referenced rather than merged**, and explicitly marked as
one mechanism seen three ways so the register cannot be read as three
independent confirmations.
