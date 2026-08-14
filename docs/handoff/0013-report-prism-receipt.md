# 0013 — report: prism is built, and here is its receipt

**The receipt the ruling asked for, and it is a re-measurement rather than a
claim:**

> **Prism's receipt is a RE-MEASUREMENT, not a claim: after it lands, how many
> of the 28 box-fallback items still fall back, and which. That number is what
> decides whether any further generator gets written, and *"a third of the
> catalog renders as a box"* is the sentence it either falsifies or does not.**

Probe: [`../evidence/prism_remeasure.py`](../evidence/prism_remeasure.py)
(`--look` for the picture). Measured **through `build_model` itself** — the
production path — on a document holding **one of every catalog kind**, so the
answer is what the viewer actually draws and covers the whole catalog rather
than a sample.

---

## THE SENTENCE IS FALSIFIED

| | before | after |
|---|---:|---:|
| catalog | 95 | 95 |
| falling back to a box | **28** | **1** |
| extruded from the plan symbol | 0 | **27** |

**`glass_shower` is the only item left**, and it is the one symbol drawn
entirely in strokes — there is nothing to extrude, and a prism would have to
invent a boundary.

| form | extruded | of |
|---|---:|---:|
| `basin` | 1 | 1 |
| `bed` | 4 | 4 |
| `enclosure` | 6 | 7 |
| `seat` | 6 | 6 |
| `vehicle` | **10** | **10** |

**The counts come from `model.stats`, which the viewer now emits** — `prism_kinds`
and `box_fallback_kinds`, as **lists, not totals**. A count cannot be argued
with or acted on; the claim only stays checkable if the survivors are named. A
test asserts the two lists **partition** the fallback set, so an item cannot
quietly vanish from both.

---

## AND THE CAVEAT THE COUNT DOES NOT CARRY — the picture supplies it

**27-of-28 overstates the win, and the read-back predicted exactly where.**
`build_model` extrudes whatever filled rings a symbol has; it does not judge
whether those rings are a **body** or a handful of **accents**. The read-back's
NONE tier named three items where they are accents, and two of them now extrude:

* **`boat_trailer` — the prediction is borne out.** Its frame, bed rails and
  tongue are all `<line>`; the only fills are two fenders, a coupler and two
  lights. The extrusion is **five disconnected slabs and no trailer** — visible
  in `evidence/prism-extrusion-look.png`, second row, second cell. The
  read-back's words were *"fragments floating in space, which is WORSE than the
  box"*, and looking at it, they are right.
* **`bicycle` — the prediction is NOT borne out.** Two wheels and a saddle, in
  line. It is thin, but **a bicycle is thin**, and a 24″×68″ box is a much worse
  statement about the object than three narrow shapes in the right places.

**Everything else looked at is a real improvement**, including the four the
read-back put in PARTIAL: `lawnmower` extrudes its deck and leaves the handle
open, which is what a mower *is*; `motorcycle` and `snowblower` read correctly
from above.

### No threshold was added to force `boat_trailer` back to a box, and that is deliberate

**It would have to be a coverage threshold — and this is the exact instrument
whose failure is already recorded** in `WORKING_AGREEMENT.md`: one such line put
`lawnmower` and `snowblower` on opposite sides while they are structurally
identical. Reintroducing it to catch one item would re-create a fault that has
already cost a withdrawn number, in order to fix something an authoring change
fixes properly.

**So `boat_trailer` is reported and left extruding.** The decision is Patrick's,
and the options are: leave it, add a filled bed to its symbol (the authoring
fix, which is the same two edits and a command as the other two), or rule that
prism should refuse an item whose rings are all accents — which needs a
criterion that is not a coverage threshold, and none is currently proposed.

## The authoring list is now TWO, not three

`glass_shower` (no fill at all) and `boat_trailer` (fills, but no body).
`bicycle` comes off it. **Still authoring work, still separate from the
generators**, per the ruling that a code task must not acquire an artwork
dependency.

---

## What this means for the four furniture generators

**The ruling was: build prism, re-measure, then decide. This is the
re-measurement, and it is the strongest possible case for not writing them.**

`seat`, `bed`, `basin` and `enclosure` are **17 of 18 extruded from real
outlines**. What a dedicated generator would add over that is **structure the
plan symbol does not contain** — a seat back, arms, a tub's inner well — which
is a genuinely different question from *"is the footprint right"*, and one best
answered by looking at the 3D view now that it shows real shapes.

**No recommendation is made here beyond that.** `vehicle` is 10 of 10 extruded,
which is a bigger change than its read-back number predicted (3 BODY of 10) and
weakens the case for a `vehicle` generator too — but *"extruded"* and *"looks
right"* are different claims, and only two of those ten have been looked at.

## What is NOT claimed

* **That a prism is the right SOLID.** A filled plan symbol says nothing about
  whether a straight vertical extrusion is correct — a bathtub is not a prism,
  whatever its outline. **Prism is a better fallback, not a model.**
* **That every extrusion has been seen.** Eight were rendered and looked at; the
  other nineteen are counted, not inspected.
* **That the solids are watertight.** They are closed prisms over simple rings
  by construction, and nothing has measured them as meshes.
