---
# permanent key, independent of GitHub
id: 11
title: "Four competing z-order systems, two of which run on every wall click"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:ui
  - status:partial
  - status:carried
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 11
related: [11a, 47]
state_source: row
github_issue: null
---

# D11 — Four competing z-order systems, two of which run on every wall click

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 76) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Four competing z-order systems, two of which run on every wall click.** Re-censused at P4.5 (2026‑08‑05): **20 `setZValue` sites**, not 14 — (i) `geometry.bring_to_front`/`send_to_back`, a whole-scene max/min scan with no floor filter, assigning relative to the scene's current max; (ii) `RoomItem.raise_to_front`, a running counter `win._z_top × 10`, assigned absolutely; (iii) `levels.py`'s `FLOOR_Z_BAND` (100,000) applied as a **delta**; (iv) the static layer constants. **HALF CLOSED at P4.5 as defect 11a** — (ii) and (iii) fought, and `raise_to_front` won by dropping the band: a room raised on a ghost floor measured **z −99996 → +10 against an active floor at 4**, i.e. the ghost painted OVER the floor being edited. **The serious half is that it COMPOUNDS rather than being wrong once:** `_floor_band` was left recording −100000 while the z had escaped to +10, so the next re-band computed `10 − (−100000) + new` and added the band a second time on top of an already-wrong value. **A band and its own record disagreeing is the same shape as a flag that reads fine and does nothing** — the state is not merely wrong, it is wrong in a way that reports itself as right. Fixed by re-basing the raise into the item's own band; **openings are deliberately exempt** because an `OpeningItem` is a CHILD of its wall, so its z is relative to that wall and banding it would sink the opening behind the wall it is cut into (the reason is recorded AT THE SITE, not only in the commit, so the next blanket fix does not reintroduce it). Receipt, fail-first: `test_raising_a_ghost_room_keeps_it_inside_its_floor_band`, red on its verdict (`assert 10.0 < 4.0`) past three preconditions. **STILL OPEN, AND IT LEFT P4.5 UNLANDED — the phase ticked with an explicit carve-out rather than over it (2026‑08‑06):** the runtime collapse/hang, and whether (i) and (iv) unify. `Z_STACK_BAND` exists nowhere in the tree, so the hang is not reproducible from disk and instrumenting it comes first — a bounded event counter on the drag to find the consumer, rather than choosing constants to avoid a symptom. **The agreed rule is unchanged and carries forward whole:** z = `floor_term + stack_term + type_term`; the backdrop's −1e9 becomes a TYPE TERM; `bring_to_front`'s full-scene max scan dies with it; the band arithmetic becomes NAMED CONSTANTS with `max(type_term) < STACK_BAND` and `max(stack_term) < FLOOR_BAND` written beside them and **pinned by a test**, because without that it is three schemes again the first time someone raises a type constant. **The SERIALIZATION half is separately blocked** on a schema ruling with version implications — v5 has no stacking-index field on room, wall, furnishing or group, and all four set `additionalProperties: false` — so z stays OUT of the document until that is ruled, and this row closes only its runtime half when it closes.

## Site

`rooms.py` (`raise_to_front`, fixed); `geometry.py`, `levels.py`, the constants

## Milestone

**P4.5 (11a done) · runtime half CARRIED OUT of Phase 4, queued second after row 47**
