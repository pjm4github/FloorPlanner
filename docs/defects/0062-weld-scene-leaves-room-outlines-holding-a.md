---
# permanent key, independent of GitHub
id: 62
title: "weld_scene leaves room outlines holding a Vertex no wall holds, and D48's report cannot see it"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-09
closed: null
closed_by: null
rank: 63
related: [48, 61]
state_source: measurement
github_issue: null
---

# D62 — `weld_scene` divorces a room outline from the walls at its corner

## Symptom

Found while validating an instrument for [D61](0061-a-room-move-permanently-adds-two-walls.md)'s
item 2, not by looking for it.

**Edit ▸ Coalesce all walls now leaves the majority of a plan's outline corners
holding a `Vertex` object that no wall at that coordinate holds any more.**
Measured on five plans, counting only PLACED rooms and scoping by floor:

| plan | divorced corners, as loaded | after `normalize_walls` |
|---|---:|---:|
| `wiscaway2026-08-08` (Patrick's) | **0** | **49** |
| `planc1.v5` | 0 | 56 |
| `farmplaceBIGmultifloor` | 0 | 24 |
| `roundedMultifloor` | 0 | 78 |
| `symmetricP1` | 0 | 57 |

Zero on every plan as loaded; large on every plan afterwards.

**This state should not exist.** The Phase 3 model is that *a corner is one
`Vertex` that the walls and the room outlines both hold*, which is why a wall
move carries the rooms with nothing to recompute (`OutlineEdge`'s own
docstring, `rooms.py:75`).

## Mechanism

Attributed by running each of `normalize_walls`'s three sub-passes alone:

    merge_collinear_scene   divorced +0   (it orphans corners instead: +22)
    weld_scene              divorced +49
    split_body_landings     divorced +0

`weld_scene`'s share step folds coincident wall ends onto one surviving
`Vertex` and **does not rebind the room outlines holding the loser**. Nothing
moves — `moved: 0` on `wiscaway` — so this is purely a rebinding of identity.

Distinguish it from the *other* thing the same pass does, which is not this
defect: `merge_collinear_scene` dissolves a wall junction and the outline goes
on naming a corner where **no wall end lies at all** (`wiscaway` 7 → 29).
That is D61's territory. This record is about the corner where a wall **is**
present and is no longer the same object.

## What it is NOT known to do

**The consequence is open, and is deliberately not claimed here.** `WallItem`
gathers the outline edges a corner drag must carry with `by_id.get(id(e.v))`
(`walls.py:1979`) — **by identity** — so a divorced edge is skipped. Read from
the source that is stranding.

**Measured, one sample does not settle it.** A real body drag on a wall at a
divorced corner (`Lounge`, `(456, 768)`) moved the wall, left that corner where
it was, and changed the room's area by nothing. That is consistent with
stranding **and** with the designed step-insertion at `walls.py:1999-2014`,
which exists precisely to leave a jog where a run moves and its neighbour does
not. Separating them needs more than one sample and it has not been done.

So: **the STATE is measured, the HARM is not.** `evidence/d61_divorce_behaviour.py`
is the probe, and its arm A is a positive control that had to be fixed twice
before its arm B meant anything.

## Why nothing caught it

**`scene_identity_report` (D48/G2) reports `extra_vertices` 0 on four of the
five plans after `normalize_walls`** (6 on `planc1`). It is not broken. It
compares **wall ends to wall ends** — its own docstring says so — and an
outline corner holding a vertex no wall holds is outside the question it asks.

*A census inherits the blindness of the predicate that scopes it*, and this is
that rule landing on the newest instrument in the tree rather than an old one.
D48's report answers *"do two wall ends at one point share a vertex?"*
completely and correctly. Nobody has ever asked *"does the room's corner share
the wall's vertex?"*, and the two questions look the same from the outside.

**Would `check(deep=True)` have fired? No** — and the reason is D48's own
finding: `design_from_scene` **welds on the way out**, so the emitted document
has one vertex per point whatever the scene holds. The invariants have never
seen this and structurally cannot. That is a gap, not a limit: the question is
answerable at scene level, and D48 already built the layer to answer it.

## Evidence

`docs/evidence/d61-normalize-outline-arrow.txt` ·
`docs/evidence/d61-normalize-outline-arrow.json` ·
`docs/evidence/d61_normalize_outline_arrow.py` ·
`docs/evidence/d61_divorce_behaviour.py`

**Three instrument faults were found by controls before any of the above was
believed**, and they are recorded in the evidence file rather than here: a drag
that pressed a door instead of a wall; a divorce counter blind to a
half-carried corner; and a by-point test with no floor filter and no floating
exemption, which read 62 where the scoped answer is 49.

## Ruling

*(None yet. Reported, not directed.)* What is owed before anything is built:
whether a divorced corner strands in practice, on more than one sample and on
both readings; and whether the fix belongs in `share_coincident_ends` (rebind
the outlines as the ends fold) or in a widening of `scene_identity_report` to
ask the outline question too. **Both are Patrick's to direct.**
