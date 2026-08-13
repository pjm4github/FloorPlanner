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

### The form was already adjusted once, BY LOOKING — and that is the finding

**The first cut passed every test and would still have failed the check.**
Fence 12″/4.0, railing 6″/2.5: both rendered at working zoom as **the same
ladder**, differing only in how *fine* it was. That is a distinction you make by
comparing two walls, not one you make at a glance — and *"tell a fence from a
railing without clicking"* is a glance.

**No test was going to say so**, which is the point worth keeping: every
assertion about the channel was true, and the drawing was still wrong. It took a
render at the zoom a person actually works at
(`evidence/d74-decoration-working-zoom.png`, produced by
`evidence/d74_decoration_render.py`).

**What changed:** both axes the ruling names were pushed — fence to 16″/5.0 and
darker, railing to 4″/2.0 and lighter — and **the fence gained a filled POST at
each tick**, which is what a post *is* in plan.

### THE POST IS RULED IN — it does not go beyond the ruling, it COMPLETES it

*(Patrick, 2026‑08‑12. It was submitted as the strikeable part; the ruling
rejects that framing, and the reason generalises well past this feature.)*

> **My ruling named decoration as the channel but said nothing about decoration
> having AXES, and your first cut showed why that mattered: fence and railing as
> the same ladder differing only in FINENESS. Fineness is a scalar, and a scalar
> cannot carry identity between two similar things — which is exactly the reason
> thickness failed one level up. Fill versus stroke is CATEGORICAL, and
> categorical distinctions survive at working zoom while scalar ones dissolve
> into it.**

> **IDENTITY NEEDS A CATEGORICAL CHANNEL, NOT A SCALAR ONE.**

**Two instances, one level apart.** **Thickness** failed because two types share
a real thickness. **Fineness** then failed *inside the fix*: tick spacing and
weight are scalars too, so the channel had changed and the **kind** of channel
had not. A scalar has no gaps in it, and a viewer's eye normalises a continuum
away; fill-versus-stroke has no intermediate values and survives a glance.

**So the tick spacing, the weights and the scallop radius remain adjustable — the
post is not one of them.** It is the categorical half of the channel, and
striking it would put the drawing back exactly where the render found it. The
general form is in [`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md) with both
instances, and in [`../handoff/0012-ruling.md`](../handoff/0012-ruling.md).

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

**The plan to check it on is `fixtures/d74-wall-decoration.json`** — five runs
side by side (an ordinary wall for reference, then railing with a gate, fence,
hedge, retaining), rebuilt by `evidence/d74_decoration_render.py`. It is in
`fixtures/`, not `examples/`: a check plan is edited freely and may be as dirty
as the check needs, and the corpus is frozen.

## What landed

| | |
|---|---|
| `WALL_DECOR` in `walls.py` | the table — form, pitch, reach, grey, post — with `retaining` deliberately absent |
| `WallItem._build_decor` | builds the path in `rebuild`, **not** in `paint`: the view repaints every item on every change, so path work per repaint stalls a big plan. An ordinary wall returns before the first loop and pays nothing |
| `WallItem._opening_spans` | **one definition** of where the run is cut, feeding both the body's holes and the decoration's break — so a gate's break cannot drift away from the gap in the wall |
| `GATE_INK` | the lighter arc |
| `OpeningPropertiesDialog` | the sheet that names the kind, replacing a bare `QInputDialog`; the menu item is now **Properties…** rather than *Set size (WWHH)…*, since the sheet does more than size |

**Six tests**, and three of them exist to stop the others being vacuous: the
fence/railing test asserts **first** that the two thicknesses are equal (without
it, "the two differ" is satisfied by the thickness that was already there, and
the test passes on the code it was written to reject); the gate-break test
measures the **same wall without the gate first**, because *"no tick inside the
span"* is also true of a wall with no ticks anywhere; and the dialog test asserts
a **door gets no reason line**, because a reason invented for a chosen kind is
noise. Both mechanisms were **fail-first checked** by breaking them —
`open_at → False` and railing's spec set equal to fence's — and both tests went
red.

## Ruling

*(Opened 2026‑08‑12 — Patrick's, from the PR #26 manual check.)* Filed as a new
item rather than a reopening: D73's tables were genuinely wrong and are genuinely
fixed. What is refuted is a **design ruling made on top of them**, and conflating
the two would make a closed measurement look unsafe when it is not.
