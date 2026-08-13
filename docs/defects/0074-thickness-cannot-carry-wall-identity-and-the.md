---
# permanent key, independent of GitHub
id: 74
title: "Thickness cannot carry wall identity, and the gate is invisible and unnamed"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-12
closed: null
closed_by: null
rank: 75
related: [73]
state_source: manual-check
github_issue: null
---

# D74 — Thickness cannot carry wall identity, and the gate is invisible and unnamed

**Filed as a NEW ITEM, not as a reopening of D73.** D73 was about three tables
disagreeing and one being dead; it is fixed and stays closed. This record is
about what the fixed table is being asked to *communicate*, which is a different
question and one D73 never touched.

**Found by Patrick's manual check on PR #26.** The AMBER gate worked exactly as
designed: the code was green, the census was right, the implementation matched
the ruling — and **the ruling was wrong**. That is what the manual check is for,
and it is the second time it has returned something no automated signal could
(the first was D53, at A1b).

---

## Part 1 — THE THICKNESS RULING IS REFUTED

**The ruling under PR #26 was that a wall's type reads from its drawn
thickness.** In plan: exterior 6.0″, interior 4.5″, partition 3.5″, railing 2.0″,
fence 2.0″, hedge 18.0″, retaining 8.0″.

**Patrick cannot tell a fence from a railing at working zoom, and never will.**

| type | `STD_T` | distinguishable in plan? |
|---|---:|---|
| railing | **2.0** | **NO — identical to fence** |
| fence | **2.0** | **NO — identical to railing** |
| hedge | 18.0 | yes |
| retaining | 8.0 | yes |

**The two that "work" are the tell, not the counter-example.** Hedge and
retaining are legible because they **genuinely are fatter** — that is the
quantity being read correctly, not identity being communicated. The two coincide
there by accident, and the accident is what made the ruling look sound.

### The general form, which outlives this feature

> **A CHANNEL COMMITTED TO REPRESENTING A REAL QUANTITY CANNOT ALSO CARRY
> IDENTITY.**

**Thickness is already spent.** It represents real thickness — that is a contract
the schema states (`wall.thickness_in`, *"Override; omitted = the standard for
`type`"*) and one D73 has just made single-sourced and normative. A channel
carrying a real measurement is not free to also mean *"this is a railing"*,
because whenever two types share a measurement the channel has nothing left to
say, and **it cannot be widened without lying about the measurement.**

This belongs with the project's other channel rulings rather than standing alone:
**dashed is already spoken for twice** (a floating room's boundary, and the P4.5
fault signature), and **colour is spoken for in 3D** (`WALL_C`, recorded as a
deliberate 2D/3D asymmetry in `VIEWER_NOTES` — a plan has line weight to spend
and a 3D scene does not).

## THE FIX — a second channel: DECORATION ALONG THE RUN

**Not colour, not dash, both of which are spoken for.** The channel is what is
drawn *along* the wall's run:

| type | decoration |
|---|---|
| **fence** | regular **perpendicular post ticks** |
| **railing** | **closer, lighter cross-ticks** — reading as *related but lighter* |
| **hedge** | a **scalloped edge** |
| **retaining** | **keeps thickness**, which already works |

**Railing reading as a lighter fence is correct, not a compromise** — they *are*
related, and the drawing should say so.

**These are drafting conventions, not a standard.** So **the exact form is
adjustable after Patrick sees it — the channel is not.** Tick spacing, weight and
scallop radius are all open to a second look; *"decoration along the run"* is the
ruling.

---

## Part 2 — THE GATE HAS NO SYMBOL, AND THE DIALOG NEVER NAMES THE KIND

**PR #26 made the gate derivable and then left it invisible.** A door placed in a
landscape wall *becomes* a gate — no mode, no tool, I7 true by construction —
which is right. But:

* **It paints exactly as a door**, inheriting only the railing's 2 inches through
  `self.wall.t`. Thinness was argued to carry the difference; by Part 1 it
  cannot, and here it does not even try to — a door in a railing and a gate are
  the same drawing.
* **The properties dialog offers size only.** It never says what the user made.

### The fix, both halves

**The gate gets its conventional symbol: a BREAK IN THE RUN plus a quarter-circle
SWING ARC, lighter than a door's.** It already paints as a door, so the work is
to **break the decoration either side** — which Part 1's channel now makes
possible — and **keep the arc thin**.

**The dialog shows the kind as READ-ONLY TEXT, with its reason.** Not an editable
field: the kind is derived, and offering it as a choice would re-introduce
exactly the mode the derivation removed (someone putting a gate in a bedroom
wall, then being told off for it by I7).

> **DERIVING A PROPERTY IS NOT A LICENCE TO HIDE IT.**

A derived value the user cannot see is indistinguishable, from where they sit,
from a value that was ignored.

---

## Tier and the manual check

**AMBER.** Patrick's check is judgement, and it is two questions:

1. **At working zoom, tell a fence from a railing without clicking.**
2. **Find the gate in a run of rail.**

## Ruling

*(Opened 2026‑08‑12 — Patrick's, from the PR #26 manual check.)* Filed as a new
item rather than a reopening: D73's tables were genuinely wrong and are genuinely
fixed. What is refuted is a **design ruling made on top of them**, and conflating
the two would make a closed measurement look unsafe when it is not.
