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

## A2's FIRST MEASUREMENT — 2026‑08‑09, and it is a NEGATIVE RESULT

**Ruled: instrument the hang with a bounded event counter, find the consumer of
the z step, and do not choose constants that make the symptom go away. The
measurement was the deliverable, not a fix.** It is done, and it did not find a
consumer — because on this tree there does not appear to be one, and the hang
does not reproduce.

`docs/evidence/d11-a2-z-step-measurement.txt`, probe at
`docs/evidence/d11_a2_z_step_counter.py`.

**The reconstruction is a READING, and is labelled as one.** The work was
reverted, so `Z_STACK_BAND` exists nowhere in the tree. Two things answer to
"the z step" and **both** were parametrised rather than guessing:
`bring_to_front`'s `+ 1.0` and `raise_to_front`'s `* 10`.

| step | stack | TOTAL events | max abs z | completed |
|---:|---:|---:|---:|---|
| 1.0 | 10 | **545** | 67.0 | yes |
| 100000.0 | 10 | **545** | 200056.0 | yes |
| 1.0 | 100000 | **545** | 6007.0 | yes |

**The per-consumer breakdown is identical in all three runs.** Five orders of
magnitude on either term changes nothing but the z values. And the named test —
`test_drag_split_macro_keeps_every_room_rectilinear` — **passes in ~0.3 s at all
four combinations**, including both terms at 100 000 together.

**So the record's stated trigger — magnitude — is not confirmed on today's tree
and cannot be acted on as written.** What that does *not* establish is set out
in the evidence: the reverted change is not on disk, ruling 4's type term and
the death of `bring_to_front`'s full-scene scan are not reconstructed, and the
tree has moved through all of P4.5, A1 and A1b since.

### The parasitic-reach question needs a distinction before it can be answered

Carried into A2: *what currently works because all floors collapse to one
height?* **There are two different z's here and the question lands on the other
one.**

* **Scene stacking order — this record's subject.** `_apply_floor_stacking`
  bands items by `-depth * FLOOR_Z_BAND` (100 000) and ghosts do paint behind
  the active floor. **It works.** Not a never-worked capability, so not a
  parasitic-reach precondition.
* **Document elevation — [D50](0050-a-level-s-elevation-is-destroyed-by.md)'s
  subject.** Every `elevation_in` is the literal `0.0`. *That* is what has never
  worked, and its consumers are enumerable: **`fp3d.py:448`** (the viewer stacks
  levels by it) and **`fp3d.py:228`** (a wall-hung item sits at the level's
  floor plus its catalog elevation). **Nothing in the editor reads it at all.**

So the parasitic surface for the collapse is the viewer, which D50 has already
ruled correct and not to be changed — and **A2 touches neither quantity**.

### PARKED AS NOT REPRODUCIBLE — ruled 2026‑08‑09

**The HANG is parked. The record is not closed.**

What is parked is the specific symptom: *"it hangs
`test_drag_split_macro_keeps_every_room_rectilinear` at the first drag, and the
trigger is the magnitude of the z step."* That does not reproduce on this tree,
by the measurement above, and chasing it further would have meant changing
things until something hung — which is the same error as choosing constants to
make a symptom go away, pointed the other way.

**What survives the parking, and is still open:**

* **the four competing z-order systems**, which is what this record is actually
  named for and which the measurement did not touch;
* **ruling 4's scheme** — z = `floor_term + stack_term + type_term`, the
  backdrop's −1e9 becoming a **type term** rather than a magic number,
  `bring_to_front`'s full-scene max scan dying with it, and the band arithmetic
  becoming named constants with `max(type_term) < STACK_BAND` and
  `max(stack_term) < FLOOR_BAND` pinned by a test;
* **the serialization half**, unblocked by R‑B and queued separately as A3.

**If the hang returns**, the instrument is on disk and takes one command:
`docs/evidence/d11_a2_z_step_counter.py`, which parametrises both z steps and
bounds the run so a hang yields tallies rather than a wedged process. **Do not
re-derive it.**
