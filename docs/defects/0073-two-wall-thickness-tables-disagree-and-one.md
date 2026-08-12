---
# permanent key, independent of GitHub
id: 73
title: "Two wall-thickness tables disagree, and the one in validate.py is never read"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
closed_by: null
rank: 74
related: [45]
state_source: measurement
github_issue: null
---

# D73 — Two wall-thickness tables disagree, and one is dead

## The fault

**Two type→thickness tables exist and they do not agree:**

| type | `validate.py:17` `STD_T` | `viewer/fp3d.py:51` `WALL_T` |
|---|---:|---:|
| exterior | 6.0 | 6.0 |
| interior | 4.5 | 4.5 |
| partition | 3.5 | 3.5 |
| railing | 2.0 | 2.0 |
| fence | 2.0 | 2.0 |
| **hedge** | **18.0** | **12.0** |
| retaining | 8.0 | 8.0 |

**`STD_T` is never read.** It is defined at module level in `validate.py` and
referenced nowhere in `floorplanner/` — measured while taking the wall-types
census (handoff 0011).

**And a third definition exists in the scene**, in a different shape:
`WallItem.t` is a two-branch conditional over `EXTERIOR_T` / `INTERIOR_T`
(`config.py:43-44`) that knows nothing of the other five types.

## Why it matters more than a dead constant usually would

**The schema says the thickness table is normative.** `wall.thickness_in` is
documented as *"Override; omitted = the standard for `type`"* — so *"the standard
for `type`"* is a real contract, and **three different answers to it live in the
tree**, one of them dead and one of them disagreeing.

**A dead table is also a trap in the direction of looking authoritative.**
`STD_T` sits at the top of `validate.py`, the file that owns the invariants — the
most plausible place a reader would look for the normative table, and the one
place whose copy has no effect at all.

## What is NOT claimed

**No plan is known to be wrong because of this.** `hedge` is a landscape type; no
corpus plan uses one, and the viewer's value is the one that renders. This is
recorded as a **divergence and a dead definition**, not as a rendering fault.

## The fix, not taken

**One table, in the layer both can import.** `validate.py` is deliberately
dependency-free and the viewer already imports from the repo, so the direction is
not obvious and is a ruling rather than a mechanical move — which is why this is
filed rather than done inside a census.

**Whichever survives, `hedge` needs a decided value**, not a merge.

## Ruling

*(Open — filed 2026‑08‑11.)* Found while taking the wall-types census, not by a
failure. **Filed, not fixed.**
