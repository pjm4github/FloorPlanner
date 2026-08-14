# 0014 — ruling: build the region extrusion; the three seats are artwork

**Patrick's, 2026‑08‑14**, on
[`0014-report-furniture-regions.md`](0014-report-furniture-regions.md). Quoted
rather than summarised.

---

## 1. BUILD IT — one generator, not four

> **BUILD THE REGION EXTRUSION. One generator, not four, and your costing
> decides it: 17 annotations beside artwork that already exists, plus one loop
> in `build_prism`, which already returns a list of parts and already extrudes a
> ring between two heights. That covers 13 of 18 items and generalises to every
> form.**

## 2. The three seats are an ARTWORK fix, and the counter-examples are the point

> **THE THREE SEATS ARE AN ARTWORK FIX, NOT A CODE PROBLEM — and that is the
> whole point of the counter-examples you found. `dining_chair` and
> `office_chair` draw their backs as closed rects IN THE SAME FORM. So `sofa`,
> `armchair` and `loveseat` are not a limit of the approach; they are three
> symbols drawn inconsistently with their own neighbours. Redraw the back as a
> closed rect and they flow through the same generator with no new mechanism.**
>
> **It also makes the PLAN symbol more correct, which is the tell that it is the
> right fix rather than a workaround: a sofa back has thickness, and a line says
> it does not.**

**That test was applied and passed before the redraw shipped**: the plan symbols
are at `evidence/seat-plan-symbols.png`, and the back and arms now read as
regions with thickness rather than as zero-width lines.

## 3. Annotation beside the artwork — ACCEPTED, and the reasoning is the ruling

> **ANNOTATION BESIDE THE ARTWORK IS ACCEPTED, and your reasoning is the ruling:
> the artwork says WHERE a region is and never WHAT it is, no parser
> distinguishes a pillow from a drain, an ordinal rule breaks silently when
> artwork is re-ordered, and a geometric heuristic invents a number the document
> does not contain — which is the objection that already refused `--stack`.
> Quote that last line in the record; it is the same principle twice and it
> should be visibly so.**

**Quoted, as instructed** — the `--stack` refusal, from `VIEWER_NOTES.md` §8 and
D50's ruling:

> **A rendering flag that invents a number the document does not contain is a
> decision about the MODEL wearing a renderer's clothes**; it would make the
> picture stop being evidence; and the moment elevations are real the flag
> becomes a way to disagree with them.

**The same principle, twice:** there it refused a flag that would have invented
level elevations; here it refuses a heuristic that would have invented region
heights. **In both cases the alternative is to state the number in the document
that owns the fact** — `level.elevation_in` there, `data-h` beside the artwork
here.

## 4. THE BOUNDARY — height only, never coordinates

> **ONE BOUNDARY TO HOLD WHILE BUILDING IT. The region's POSITION comes from the
> artwork; only its HEIGHT is annotated. Do not let the annotation acquire
> coordinates — the moment it does, there are two sources of truth about where a
> pillow is, and they will disagree. Same discipline as the thickness table: one
> normative source per fact.**

**Held, and asserted rather than trusted.**
`test_the_annotation_carries_A_HEIGHT_AND_NOTHING_ELSE` walks every SVG in the
asset tree and fails if any `data-` attribute is not `data-h`, or if any value is
not a single number. **A future annotation that acquired an `x` would turn the
suite red.**

**One clarification the build produced:** `data-h` is measured **from the item's
base**, the same datum as `height_in` — so a counter-mounted sink's `data-h="2"`
is 2″ above the counter, not above the floor. **An annotation measured from the
floor would have to know where the counter is, which is a coordinate**, which is
this boundary. Found because a test asserted world z and went red on
`kitchen_sink`: the test was wrong and the extruder right.

## 5. Order, tier and the check

> **ORDER: the generator and the 17 annotations first, since the three artwork
> fixes have nothing to flow through until it exists. Then the seats.**
>
> **Tier AMBER. Patrick's check is one question: does a sofa read as a sofa.**

Built in that order, as two commits on one branch — the check needs the seats, so
both are in the same PR. Renders for the check: `evidence/seat-check.png` (3D)
and `evidence/seat-plan-symbols.png` (plan).

## 6. The authoring list, now FIVE

> **Add them to the authoring list, which now stands at five — `glass_shower`,
> `boat_trailer`, `sofa`, `armchair`, `loveseat`. Note against the three seats
> that they are the seats a room is fullest of, so they carry more visible
> weight than their count suggests.**

**Three of the five are done in this branch** — `sofa`, `armchair` and
`loveseat`, whose backs and arms are now closed regions. **Two remain:
`glass_shower`** (no fill at all, still a box) and **`boat_trailer`** (fills, but
no body — five disconnected slabs). Both stay artwork tasks, separate from the
generators.

## 7. The `dining_chair` correction is the FOURTH instance of the enumeration rule

> **Your criterion counted only NESTED shapes, and `dining_chair`'s back is a
> sibling rect — so the criterion was shaped by an assumption about how a region
> would be drawn, and returned exactly what that assumption admitted. Same
> failure as the menu-shaped, predicate-shaped and container-shaped censuses. It
> is the strongest version yet, because the shaping assumption was invisible
> even to the person who wrote it — which is the case the rule exists for.**

Filed as row 4 in [`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md), with that
reasoning. **The first three were containers a reader could name** — a spelling,
a predicate, `MainWindow`. **This one was geometric, embedded in a `_pip` call,
and nothing in the code or the question said "nested".**
