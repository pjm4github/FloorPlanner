---
# permanent key, independent of GitHub
id: 63
title: "A coalesced outline partly rebounds on save, and the two producers are separable"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-09
closed: null
closed_by: null
rank: 64
related: [61, 62]
state_source: measurement
github_issue: null
---

# D63 — A coalesced outline partly rebounds on save

## Symptom

Run `Edit ▸ Coalesce all walls now`, save, reopen: **some of the removed outline
corners are back.** Once, not repeatedly — the count then settles.

| plan | as loaded | after the command | after save + reopen | **durable** | rebound |
|---|---:|---:|---:|---:|---:|
| **`wiscaway2026-08-08`** | 159 | 119 | **126** | **33 of 40** | 7 |
| `roundedMultifloor` | 187 | 167 | **186** | **1 of 20** | 19 |
| `symmetricP1` | 140 | 136 | 136 | 4 of 4 | 0 |

`119 → 126 → 126 → 126`. **A pure round trip with no command is stable** — 159,
159, 159, 159 — so saving is not a producer on its own; it is the *coalesced*
state that does not survive one.

**This is the number that decides whether 2a helped.** On Patrick's plan the
durable benefit is **33 of the 69** corners he can see, not the 40 the command
reports. On `roundedMultifloor` it is **1 of 20** — near-total loss.

## Mechanism: TWO producers, separated by an exact identity

Measured on five plans, with the coalesce lane and a **wall-pass-only** lane run
separately:

| plan | 2a removed | inserted by the save | of which 2a's | inserted after the **wall pass alone** |
|---|---:|---:|---:|---:|
| `wiscaway` | 40 | 7 | **7** | 0 |
| `roundedMultifloor` | 20 | 19 | **13** | 6 |
| `farmplace` | 2 | 2 | **2** | 0 |
| `symmetricP1` | 4 | 0 | 0 | 0 |
| `planc1.v5` | 0 | 3 | 0 | 3 |

> **`inserted_after_the_pair − inserted_after_the_wall_pass == overlap`, exactly,
> on all five plans.**

So:

* **Producer 1 — THE COALESCE COMING UNDONE.** The save puts back corners the
  outline pass removed. 7 on `wiscaway`, 13 on `rounded`, 2 on `farmplace`.
* **Producer 2 — A WALL-PASS-SIDE INSERTION.** Corners 2a never touched, added
  after `normalize_walls` alone. 6 on `rounded`, 3 on `planc1` — where the
  outline pass removed **nothing at all**, so producer 1 cannot account for it.

**These are two investigations, not one**, and the identity above is what says
so rather than an impression.

Both need the wall pass to have run: the negative control — a pure round trip
with no command — inserts **0** on every plan.

## What has been RULED OUT

**It is not D62 seen from another side, and that hypothesis is recorded as
REFUTED rather than partially confirmed.** The proposal was that the save-side
weld in `design_from_scene` — already implicated in bounding D62's harm and in
hiding it from `check(deep=True)` — was also re-inserting these corners.

**The identity half came out that way; the causal half did not, and only the
second mattered.** With [D62](0062-weld-scene-leaves-room-outlines-holding-a.md)'s
repair applied (`weld_scene` now restores the P3.5 invariant, divorce 49 → 0),
durability is **unchanged**: `wiscaway` 33 of 40 becomes 33 of **37**, `rounded`
1 of 20 becomes 1 of **17**. Fixing D62 does not fix the rebound.

## Evidence

`docs/evidence/d61-save-reinserts.json` · `docs/evidence/d61_save_reinserts.py` ·
`docs/evidence/d61-divorce-persistence.json` ·
`docs/evidence/d61-what-2a-leaves.json` ·
`docs/evidence/d61-leave-path-and-persistence.txt`

**Controls, because a zero was a live outcome throughout:** a pure round trip
must insert 0 (PASS, five plans); the identification must match the count delta
(PASS, five plans); and the document reader must be READABLE — the first version
walked `levels[*].walls` on a **flat** v5 document, found nothing, and reported a
confident `0 orphan refs` off zero walls and zero rooms.

## PRODUCER 1 — FOUND, AND IT IS NOT THE SAVE

**The save was right and the coalesce was wrong.** `design/bridge._walk` emits
**one outline edge per wall** (invariant I5), so a room edge crossing a
T-junction is several edges however few corners the scene holds. The coalesce
was removing corners the *document model requires*, and the save put them back
correctly.

**Measured, and the predicate discriminates cleanly** — of the corners the save
re-inserted, **4/4** on `wiscaway`, **4/4** on `wiscaway…09R` and **16/16** on
`roundedMultifloor` had a **wall end** at them; of those that stayed removed,
**0/33**, **0/94** and **1/7** did.

Two terms were missing from `wall_ok`, both now measured into it:

1. **A wall ENDS here that does not hold this vertex** — a T-junction whose stem
   is off the run, invisible to a degree count.
2. **The two collinear walls CANNOT MERGE.** `merge_wall` is same-type only, so
   a 6″ `exterior` meeting a 4.5″ `interior` head-on stays two walls and needs
   an outline edge each. Found at `(1062, 774)`, `(852, 762)`, `(1476, 660)` on
   `wiscaway` — collinear at 90.0°, different types.

**Result, measured across a save:**

| plan | removed | durable | rebound |
|---|---:|---:|---:|
| `wiscaway2026-08-08` | 33 | **33** | **0** *(was 40 / 33 / 7)* |
| `wiscaway2026-08-09R` | 94 | **93** | 1 |
| `symmetricP1` | 4 | **4** | 0 |
| **`roundedMultifloor`** | 6 | **0** | **6 — UNRESOLVED** |

Pinned by `tests/test_rooms.py::test_a_coalesced_corner_stays_gone_across_a_save`.

**`roundedMultifloor` is still open and its cause is not known.** A floor-scoping
hypothesis was written and **refuted** — the result is byte-identical with and
without it, so the scoping stays on its own merits and explains nothing here.

## Ruling

*(Open — producer 1 largely closed, `roundedMultifloor` and producer 2 remain.)*
**Producer 1 first** — the coalesce coming undone — as ruled at handoff
0004's response. Producer 2 is separable and waits.

It bears directly on **D61 stage 2b**, whose acceptance is now *taken across a
save*: a six-move walk must end with the counts it started with **after save and
reload**, not in session. In-session-only would measure the wrong thing, and this
record is why.
