---
# permanent key, independent of GitHub
id: 64
title: "The save writes an outline corner at a recomputed coordinate, and only on angled geometry"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-10
closed: null
closed_by: null
rank: 65
related: [63, 61]
state_source: measurement
github_issue: null
---

# D64 — The save writes an outline corner at a recomputed coordinate

## Why this is a defect and not a curiosity — the sentence, and its correction

> **A save that moves a corner by more than the weld distance can land it inside
> welding range of a DIFFERENT neighbour, or out of range of the one it belongs
> to — which turns a projection error into an IDENTITY change, and identity is
> the one thing this model cannot afford to get wrong.**

That is the reasoning this record exists for, and it stands. **The number it was
issued on does not.** The ruling was made on a measured **1.5290″** move against
a `vertex_weld_in` of **0.6″**. Re-measured, **that 1.5290″ is not a move at
all** — it is a producer-2 *insertion*, and the figure was an artifact of the
census that found it.

**The largest genuine corner move is 0.3802″, which is below the weld radius.**

## What the save actually does

| plan | genuine moves | largest | new corners misread as moves |
|---|---:|---:|---:|
| `wiscaway2026-08-09R` (angled) | **2** | **0.3802″** | 0 |
| `planc1.v5` | 0 | — | 2 (at 1.5290″) |
| `roundedMultifloor` | 0 | — | 0 |
| `wiscaway2026-08-08` | 0 | — | 0 |
| `symmetricP1` | 0 | — | 0 |

**Zero on every axis-aligned plan; non-zero only on the angled one.** That points
at `split_params`' projection, and it is a **prediction for the grid-snap work to
check**: if snap-by-default removes off-lattice geometry, this should vanish with
it.

### The misclassification, named so it is not repeated

A proximity threshold alone cannot tell two things apart:

* **a MOVED corner** — the same corner, recomputed. **No wall end is at it**, and
  it lies inside no outline edge.
* **a NEW corner** — a [D63](0063-a-coalesced-outline-partly-rebounds-on-save.md)
  producer-2 insertion that merely happens to be near an existing corner. **3–6
  wall ends are at it**, and it sits strictly inside an outline edge.

`planc1`'s pair is at `(248.43, 654.0)`, which `d63-producer-two.json`
independently identifies as that plan's producer-2 insertion — 3 wall ends,
inside an edge at fraction 0.562, in `Hall` / `M Bath` / `Master Suite`. The
1.5290″ was its distance to an unrelated neighbour, not a displacement.

## The consequence, measured — ACCURACY, not data integrity

**No genuine move can reach a neighbour.** Measured on the pre-save scene, so no
reload and no re-split can contaminate it:

| corner | move | nearest **other** wall end | reachable at 0.6″ + move? |
|---|---:|---:|---|
| `OFFICE` | 0.0778″ | **5.998″** | **no** |
| `PWDR` | 0.3802″ | **12.000″** | **no** |

So no corner changes which neighbour it welds to, and **identity is not at
risk on any plan measured.** It **queues normally as an accuracy defect.**

**The bound is a property of these plans, not of the operation** — the same
mistake this project has already recorded once, at the area bound. A 0.38″ move
on a plan with a corner 0.3″ away *could* cross. What is measured is that no such
spacing exists in the corpus.

## The instrument error, recorded because it nearly shipped a false alarm

**The literal test — "does the weld set differ across a save and reload" — is
confounded, and the first run of it reported `DATA INTEGRITY` on all five
plans.** It was wrong.

**The save legitimately re-splits walls** at every junction and room corner, so
the reloaded scene has more wall ends and therefore more vertex groups whether or
not anything moved. The tell was in the output: **three plans where the save
moved ZERO corners still "changed"** — `symmetricP1` 58 → 60, `wiscaway2026-08-08`
71 → 93. A move cannot be the cause where there is no move, so the comparison was
measuring the re-split.

That accidental control is the only reason the false verdict was caught before it
was reported. **A whole-partition comparison across a save cannot be used for
anything**, and the local question — *did this corner's weld neighbourhood
change?* — has to be asked on the pre-save scene alone.

## Evidence

`docs/evidence/d64_corner_move_weld_boundary.py` →
`d64-corner-move-weld-boundary.json` · the move census in
`d63-tolerance-and-drift.json` (Q3), whose 2.0″ threshold is the one that
misclassified `planc1`.

**Controls:** the weld-partition reader is validated against a constructed
change — a third wall's end moved onto an existing shared corner with
`detach_end` and re-welded must alter the partition, and it does (**5 → 4
groups**, PASS). Without that, "identical" would be the report of an instrument
that cannot see a difference at all.

## Ruling

*(Open — filed 2026‑08‑10.)* **Accuracy defect, queued normally.** The
data-integrity escalation is withdrawn on measurement: no genuine move exceeds
the weld radius, and none can reach a neighbour on any plan in the corpus.

**It is NOT the same mechanism as D63's producer 2, and the plans say so.**
`roundedMultifloor` carries 6 producer-2 insertions and **0** corner moves;
`wiscaway2026-08-09R` carries 2 corner moves and **1** producer-2 insertion.
They appear on **disjoint plans**, so the *"one mechanism read twice"* caution
was raised correctly and does not apply here — these are two findings, and the
counting is honest.

**Re-measure after grid snap**, per the prediction above.
