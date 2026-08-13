# 0012 — read-back: how many fallback symbols have an outline `prism` can use?

**MEASUREMENT ONLY. Nothing is built, nothing is decided.** This is the
read-back [`0010-ruling.md`](0010-ruling.md) item ONE opens with:

> **MEASURE FIRST: how many of the 28 fallback items have an outline `prism`
> could actually use?** Not every symbol is a single closed path — some are line
> art, some are several disjoint shapes. **That number sizes the win before
> anything is built.**

Probe: [`../evidence/prism_outline_census.py`](../evidence/prism_outline_census.py).
Run it to reproduce every number here.

**Unblocked by the Phase 6 park (2026‑08‑12)**, which was the answer ruling 0010
was waiting on.

---

## THE NUMBER — 19 of 28, and the answer has three tiers rather than two

| tier | items | what a prism would produce |
|---|---:|---|
| **BODY** | **19** | a filled shape carries the item's body; the extrusion is recognisably the thing |
| **PARTIAL** | **6** | a real filled body, but structure drawn in **strokes** is lost (a mower's handle, a bicycle's frame). Better than a box; not the whole item |
| **NONE** | **3** | no filled shape is a body — only accents (a fender, a light) or pure line art. **A prism would extrude fragments floating in space, which is WORSE than the box.** |

**The two-way question in the ruling has a three-way answer**, and the middle
tier is the one worth having: those six are not failures, they are items where
prism improves the solid without completing it.

---

## THE FINDING THAT MATTERS MORE THAN THE COUNT — it is split by FORM, starkly

| form | items | BODY | PARTIAL | NONE |
|---|---:|---:|---:|---:|
| `basin` | 1 | **1** | 0 | 0 |
| `bed` | 4 | **4** | 0 | 0 |
| `enclosure` | 7 | **6** | 0 | 1 |
| `seat` | 6 | **5** | 1 | 0 |
| **`vehicle`** | **10** | **3** | **5** | **2** |

**The four furniture forms are 16 BODY of 18. `vehicle` is 3 BODY of 10.**

### This RE-ORDERS ruling TWO, and strengthens its answer while changing its reason

Ruling TWO says: after prism, build the remaining generators **in descending item
count** — `vehicle` (10), `enclosure` (7), `seat` (6), `bed` (4), `basin` (1).

**Vehicle-first survives, but not because it has the most items.** It is because
**`vehicle` is the only form prism does not largely fix.** And the corollary is
the part that changes the work:

> **PRISM MAY RETIRE FOUR OF THE FIVE PENDING GENERATORS.** With prism as the
> fallback, `seat`, `bed`, `basin` and `enclosure` reach 16 of 18 items with a
> real extruded body and no new code per form. What remains is **one generator,
> `vehicle`** — plus a decision about whether the other four are still wanted at
> all, which is Patrick's and not code's.

**Stated as a question rather than assumed:** a dedicated `seat` generator would
model a seat back and arms, which an extrusion of the plan symbol cannot — a
prism gives a sofa-shaped block. **Whether that is enough** is exactly the kind
of judgement the 3D view exists to inform, and it should be looked at after
prism ships rather than argued now.

## The three NONE items, and why they are an AUTHORING fix, not a code one

`glass_shower`, `bicycle`, `boat_trailer`. Inspected individually rather than
inferred from the totals:

* **`glass_shower`** — every element is `<line>` or `fill="none"`. There is no
  filled shape at all.
* **`boat_trailer`** — the frame, bed rails and tongue are all `<line>`. The only
  fills are two fenders, a coupler and two lights. **A prism would extrude two
  fenders and a coupler floating in space.**
* **`bicycle`** — filled wheels and a saddle; frame and handlebars in strokes.

**None of these needs viewer code.** Each needs a filled body added to the symbol
in `_gen_assets.py` — the generated-asset rule, one edit and one command, which
[`0010-census-furnishings.md`](0010-census-furnishings.md) measured as the cost
of a furnishing change. **Whether the symbols should change is an artwork
decision** and is flagged, not taken.

## Two forms in `KNOWN_FORMS` have ZERO items

`planting` and `prism` are recognised and **used by nothing** — the catalog's
95 items are `box` 56, `slab` 11, `vehicle` 10, `enclosure` 7, `seat` 6, `bed` 4,
`basin` 1. So `prism` is not only unbuilt, **nothing currently asks for it**, and
adopting it means either re-pointing items at it or making it the fallback in
place of `box`. **The second is what item ONE is actually proposing**, and it is
worth saying out loud because it is a change to what an unbuilt form *means*.

---

## THE INSTRUMENT'S FIRST CUT WAS WRONG, AND HOW IT WAS CAUGHT IS THE REUSABLE PART

**The first cut used one threshold at 25% of the viewBox** and reported **21 of
28 usable**. That number is withdrawn. It called `lawnmower` usable at 36.7% and
`snowblower` unusable at 20.8% — and those two symbols are **structurally
identical**: a filled body rect, filled wheels, and a handle drawn in lines. The
only difference between them is how much of each viewBox the handle occupies.

> **A criterion that splits two symbols of the same kind is measuring the wrong
> thing.** Coverage-of-viewBox is a *proxy* for "is the body filled", and the
> proxy fails wherever an item's envelope is mostly empty air — which is exactly
> what a vehicle's envelope is.

**It was caught by inspecting the items either side of the line, not by reading
the totals.** A threshold's own error is invisible in its aggregate: 21 of 28
looked like a perfectly good answer, and the two counter-examples were adjacent
rows in the table it printed. This is the same shape as the census-source rule
already in [`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md) — the
instrument's assumption is the blind spot — applied to a threshold rather than
to an enumeration.

## What the instrument does NOT measure — stated because the ruling depends on it

* **Curve anchors only.** A path's control points are not sampled, so a rounded
  shape's area is slightly **understated**. Coverage is therefore a **lower
  bound**, which is the safe direction for a *"can we use it"* question.
* **`transform` is not applied.** Every generated symbol is authored in viewBox
  units, and the census **reports** any transform it meets rather than silently
  mis-measuring it. **None was found** in the 28.
* **It does not check that a body is a SINGLE ring.** A prism generator will have
  to decide what to do with holes and with multiple disjoint fills.
  `build_solid` already returns a **list** of parts, so multiple prisms per item
  are free architecturally — that is an observation, not a design.
* **It does not measure 3D correctness.** A filled plan symbol says nothing about
  whether a straight vertical extrusion is the right solid — a bathtub is not a
  prism, whatever its outline. **Prism is a better fallback, not a model.**

---

## What this read-back does NOT propose

**No implementation, and no ruling.** Item ONE said measure first; this is the
measurement. The decisions it now enables — make prism the fallback in place of
`box`; build `vehicle` and reconsider the other four; whether to re-author three
line-art symbols — are Patrick's.
