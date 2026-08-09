---
# permanent key, independent of GitHub
id: 55
title: "Area totals DOUBLE-COUNT overlapping regions - the totals bar sums rooms independently"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 56
related: [52, 47]
state_source: report
github_issue: null
---

# D55 — Area totals DOUBLE-COUNT overlapping regions

## Symptom

The toolbar Totals figure is the **sum of the rooms' areas**. Where two rooms
overlap, the shared region is counted **twice**, and nothing says so.

Measured on `fixtures/fragment2room.json`:

| | |
|---|---:|
| `A` | 255.8 sf |
| `B` | 249.8 sf |
| **reported total** | **505.5 sf** |
| true union | **424.5 sf** |
| intersection, counted twice | **81.0 sf** |

## Mechanism

`MainWindow._update_totals` (`mainwindow.py:400‑410`) is a bare sum:

    sqft = sum(it.area_sqft for it in self.scene.items()
               if isinstance(it, RoomItem)
               and it.properties.get("include_sqft", True))

Each `RoomItem.area_sqft` derives correctly from its own outline. **There is no
concept of shared area anywhere in the expression** — no union, no pairwise
subtraction, no check that the rooms are disjoint. The figure is right for every
plan whose rooms do not overlap, which is nearly all of them, and silently wrong
for the ones that do.

*(Two further properties of the same expression, recorded because they bear on
the ruling the fix needs and not as separate defects: it does not filter by
**floor**, so a multi-storey plan reports the whole building rather than the
active level; and it does not filter by **placement state**, so a floating room
counts. Both may well be intended — that is the question below.)*

## Evidence

**Pre-existing. NOT caused by A1** — `_update_totals` is untouched by that
branch, and the double-count is a property of any plan with overlapping rooms,
which the app has always allowed.

**A1 is the first operation that made it VISIBLE**, and the mechanism is worth
stating because it is the whole reason this was found: `fragment` replaces two
overlapping rooms with three **disjoint** pieces covering the same ground, so
the reported figure collapses to the true union. Observed at A1's manual check:

    505 sq ft  ->  424 sq ft on fragment, and held at 424 through the drags

The 81 sq ft "drop" is not area being lost. **It is the double-count ending.**

That is also why the number was useful as a check on A1 itself: the six scripted
items confirm each piece is right on its own, and all six would pass with two
pieces still sharing area. The totals holding at 424 is independent evidence the
pieces are **disjoint** — a correct measurement taken with a broken instrument,
which is only possible because the instrument's bias is exactly known.

Reproduce: `python docs/evidence/d49_overlap_area_probe.py` measures the same
intersection for the sibling case; the numbers above come from the ring
shoelaces and `QPolygonF.intersected` on `fixtures/fragment2room.json`.

## Ruling

**REPORT-ONLY for now. No fix without a ruling on what the totals bar is FOR**,
because the three plausible answers give three different numbers and the code
cannot choose between them:

1. **Gross floor area** — sum of rooms as drawn. What it does today. Defensible
   for costing, where two overlapping rooms are a *drawing error* and the
   inflated figure is a symptom worth seeing.
2. **Net footprint** — the union. What "Sq. Feet" reads as to a person looking
   at a plan, and what `fragment` incidentally produces.
3. **Gross, with the overlap declared** — today's number plus an explicit
   "(81 sq ft counted twice)". Loses nothing and hides nothing.

**This is not a decision a tool should take**, for the same reason D49's *check
yes, fix no* was ruled that way: any of the three silently changes a number the
user costs a building from.

**It composes with [D49](0049-i11-overlapping-placed-rooms-the-corruption-this.md)
and [D52](0052-a-room-inside-a-room-cannot-be.md)**, and the three should be
read together. D49 will report overlaps at save with their area; D52 says
overlap is an **unmodelled state**, not a feature — and this record is the
concrete harm that framing exists to protect: if overlapping rooms were "a
feature", a double-counted total would read as intended output rather than as an
artefact nobody chose.

## Receipt

*(Open, report-only.)* Acceptance, once the ruling exists: on
`fixtures/fragment2room.json` the reported total either equals the true union
(424.5) or states the double-counted 81.0 explicitly — and **fragmenting the
plan no longer changes the reported figure**, because a gesture that only
redraws the same ground must not move a number that claims to measure it.
