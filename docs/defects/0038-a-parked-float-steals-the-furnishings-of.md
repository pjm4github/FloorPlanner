---
# permanent key, independent of GitHub
id: 38
title: "A parked float steals the furnishings of the room beneath it"

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
rank: 39
related: []
state_source: row
github_issue: null
---

# D38 — A parked float steals the furnishings of the room beneath it

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 104) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**A parked float steals the furnishings of the room beneath it.** Patrick's field report (2026‑08‑03, shuffle testing): an extracted room moved over an existing room "picks up and holds onto" that room's furnishings. **Mechanism, measured:** `RoomItem.__init__` set `_floating_furnishings = []` — the same value as *captured-but-empty* — and the lazy-capture guard was a **falsy** check, so a floating room whose capture came up empty re-captured **at every drag press, by whatever geometry it was parked over**, and the next `_translate` carried the underlying room's furnishings away. **FIXED with the full assignment contract, ruled by Patrick:** **(a)** floating a room captures the furnishings inside it, shuffle or not (the explicit Extract's existing trait, now stated); **(b)** under shuffle **every** dragged room — label-drag or float-drag — keeps its furnishings (the non-shuffle plain drag still leaves them, P4.2's trait preserved); **(c)** once floating, a room **never** picks up additional furnishings; the one re-baseline event is the **shuffle-ON toggle**, where each floating room re-captures — what it already **carried stays its own** (even parked over a placed room) and what is inside-and-unclaimed becomes assigned; a furnishing **claimed by a placed room is never the float's to take**. Implementation: the sentinel (`None` = never captured vs `[]` = captured empty), the press guard `is None`, `capture_floating_furnishings` grown prev-aware with the claimed-exclusion, the re-baseline in `_set_shuffle(on=True)`. **Receipts, fail-first (worktree at `c192ff6`):** four flips red — the steal pin, the shuffle-carry pin, the re-baseline pin, and the P4.3 acceptance test's furnishing assert (**changed by this ruling, declared**: the mover's furnishing now rides the shuffle drag instead of staying plan-side); three preservation pins pass both eras (plain-drag leaves furnishings; extract captures in any mode; the re-baseline's two edges). One wiring lesson pinned in the tests themselves: the re-baseline fires only through the toggle — tests that set `SETTINGS["shuffle"]` directly bypass it.

## Site

`rooms.py` (`__init__`, `mousePressEvent`), `extract.py` (`capture_floating_furnishings`, `join_room`), `mainwindow.py` (`_set_shuffle`)

## Milestone

**P4.3+ (done)**
