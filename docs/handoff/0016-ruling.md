# 0016 — ruling: the enclosure check, and three boxes wearing three names

**Patrick's check, 2026‑08‑15.** Arrived by terminal and screenshot; recorded
here because a check that is not on disk did not happen. **No `0016-report`
exists** — see §6.

---

## 1. THE FIRST RENDER CONTAINED NO BOAT TRAILER, AND THE VERDICT ON IT IS WITHDRAWN

Patrick's first check read:

> **The shower looks fine but the boat trailer is chunky looking.**

**Measured, and the subject was not in the scene.** `boat_trailer` appears in
exactly one plan in the repository — [`../../fixtures/prism-check.json`](../../fixtures/prism-check.json)
(1 room, 4 walls, 0 openings, 28 furnishings). The render carried
`23 rooms · 106 walls · 49 openings`. A grep across every `.json` in the tree
returns `boat_trailer` in that fixture and in the generated `manifest.json` /
`groups.json`, nowhere else.

**So "chunky" was said about some other dark form in that garage, and it is
withdrawn — not overruled.** `boat_trailer` is still unchecked, and the second
render does not contain it either.

**The class, because it is one this project already names:** a verdict about a
state the instrument never reached is **vacuous by precondition**, and a manual
check is as exposed to it as a test is. **A check request states which plan to
load and which items are in it** — the AMBER tier's whole value is a person
looking at the right thing.

## 2. THE THREE SHOWERS ARE ONE BOX WEARING THREE NAMES — the finding that outlives the feature

The second render is the right instrument: five items, one scene, nothing else
in frame. What it shows, confirmed against the catalog:

| symbol | height | footprint | closed filled shapes | `data-h` regions |
|---|---:|---|---|---:|
| `shower` | 78″ | 36 × 36 | outer rect only | **0** |
| `walk_in_shower` | 78″ | 60 × 42 | outer rect + bench | 1 (`18`) |
| `glass_shower` | 78″ | 60 × 48 | **none — every element is `fill="none"` or a bare line** | 0 |
| `sauna` | 84″ | 72 × 72 | outer rect + heater | 1 (`30`) |
| `whirlpool` | 36″ | 84 × 84 | outer rect + well | 1 (`30`) |

**Three enclosures at the same height and near-identical footprint (60×42 against
60×48) cannot be told apart, and no amount of correctness in the extruder will
change that.** Their identity is carried by **size** — a scalar.

> **THIS IS THE THIRD INSTANCE OF THE D74 RULE AND THE FIRST IN 3D:** *identity
> needs a categorical channel, not a scalar one.* Thickness failed it, fineness
> failed it inside the fix, and now footprint fails it in the viewer. **A scalar
> holds in a side-by-side comparison and fails at a glance** — and the second
> render is a side-by-side, which is exactly why the three read as a set rather
> than as three kinds.

**The channel that is available and categorical is the internal region**: a
glass enclosure has a door panel and a curb, a walk-in has a bench, a plain
shower has neither. Those are different **kinds of mark**, not points on an axis.

## 3. `glass_shower` — CONFIRMED as the last true box fallback, and the redraw brief is now specific

`glass_shower.svg` carries **no filled closed shape at all**: the outer boundary
is four separate `<line>` elements rather than a rect, and every other element is
`fill="none"`. So the extruder has nothing to extrude and the item falls back to
a box **and is named in the model's report**, exactly as
[`0013-ruling.md`](0013-ruling.md) recorded.

**It stays on the authoring list, and the redraw now has a brief rather than a
label:** a closed floor pan, a closed door panel, and a closed curb or bench —
each a region, so the enclosure reads as its kind and not as its dimensions.

## 4. `shower` AND `walk_in_shower` JOIN THE AUTHORING LIST — and the model's report cannot find them

`shower.svg` is a filled rect, two diagonals and a drain circle. It **extrudes
successfully** to a featureless box, so **the report does not name it** — the
report names only symbols with nothing closed to extrude.

> **THE RECEIPT HAS A BLIND SPOT, AND IT IS THE SAME ONE 0014 ALREADY FOUND
> ONCE.** *"The box fallback is 1 of 95"* is true and does not mean *"one item
> renders as a box"*; **the outer outline is a plain rectangle for 17 of 18** was
> the honest correction, and this is that correction meeting a second receipt.
> **A count of fallbacks measures the extruder, not the picture.** The measure
> that would have caught these three is *how many items render with no internal
> feature* — which is a different census and nobody has run it.

Authoring list is therefore **four**: `glass_shower`, `boat_trailer`, `shower`,
`walk_in_shower`. All artwork, none code.

## 5. `form="enclosure"` COVERS TWO PHYSICALLY DIFFERENT THINGS — the whole form, censused

The documented rule is **above the body → a raised region; below it → a well with
the body's cap opened**. Every `enclosure` item in the catalog, read from the
artwork and the height table:

| item | height | filled shapes | regions | what the rule gives it |
|---|---:|---:|---:|---|
| `bathtub` | 20″ | 2 | 1 | well — **correct** |
| `whirlpool` | 36″ | 2 | 1 | well — **correct** |
| `swim_spa` | 40″ | 2 | 1 | well — **correct** |
| `walk_in_shower` | 78″ | 2 | 1 (`18`) | **well — a bench becomes a slot** |
| `sauna` | 84″ | 2 | 1 (`30`) | **well — a stove becomes a hole** |
| `shower` | 78″ | 1 | 0 | plain box |
| `glass_shower` | 78″ | **0** | 0 | box fallback |

> **ONE LABEL IS CARRYING A VESSEL YOU LOOK DOWN INTO AND A ROOM YOU WALK INTO.**
> A tub at 20–40″ is a body with a recess cut in it, and the rule is right about
> it. A shower or sauna at 78–84″ is a **tall hollow volume, and everything
> inside it is below its height without being a recess in it** — so the rule
> cannot be right about it, and the render agrees: the sauna shows a dark square
> notch in its top face where a heater should stand.

**I am not ruling the defect, because I inferred it from a rule and a picture
and this project distinguishes a correct inference from a taken reading.** Code
owes the measurement: **for `walk_in_shower`, `sauna` and `whirlpool`, dump each
part and state whether it produced a raised solid or an opened cap.** Three
lines of output.

**IF IT CONFIRMS, THE FIX IS A SECOND FORM, NOT A THRESHOLD.** The split is
visible as a height gap — 20/36/40 against 78/78/78/84 — and **a threshold there
would be the mistake this project already recorded at
[`0012-ruling.md`](0012-ruling.md)**: one 25% line split `lawnmower` from
`snowblower`, two structurally identical symbols. **A vessel and a room are
different KINDS, not points on an axis**, which is §2's rule again at the level
of the catalog rather than the picture. `data-h` is untouched and still carries a
height and nothing else, so [`0014-ruling.md`](0014-ruling.md) §4's boundary
holds.

## 5b. THE ENCLOSURE RETIREMENT'S PREMISE IS THE THING UNDER TEST

[`0015-ruling.md`](0015-ruling.md) retired `enclosure` among the four, on the
grounds that **region extrusion covers what those generators were wanted for**.
**Three of the four items now on the authoring list are that form**, and
[`0013`](0013-report-prism-receipt.md)'s supporting number was *"enclosure 6 of
7"* — a count of items that **extruded a body**.

> **"EXTRUDES A BODY" IS NOT "READS AS ITS KIND", AND THIS IS THE THIRD TIME
> THAT GAP HAS BEEN MEASURED.** 28 → 1 overstated it; *the outer outline is a
> plain rectangle for 17 of 18* was the honest correction; **nobody re-applied
> that correction to the enclosures**, and 6-of-7 is the same sentence about a
> different form.

**The retirement is not reopened by this ruling** — `seat`, `bed` and `basin`
are untouched and the sequence that produced it stands. What is reopened is
**whether region extrusion covers the enclosures**, which is a question the §5
measurement answers directly. **`vehicle` was already kept out of that
retirement**, and §5c is why that now matters.

## 5c. THE BOAT TRAILER IS PROBABLY NOT AN ARTWORK TASK AT ALL

Its catalog form is **`vehicle`** — the one generator [`0015`](0015-ruling.md)
deliberately did **not** retire, whose case is the loft design in
[`../../floorplanner/viewer/VIEWER_NOTES.md`](../../floorplanner/viewer/VIEWER_NOTES.md)
§5. Its failure is **five disconnected filled fragments**, which is what a plan
symbol of an **open frame** gives you — and no redraw makes an open frame into a
closed body without drawing a trailer that is not there.

**So the trailer's fix is plausibly the loft, not artwork**, and it should not be
sent for a redraw until that is decided. Kept distinct from the three showers,
whose failure is a different one with a different remedy.

## 5d. THE AUTHORING INSTRUCTION IS THE COMMON CAUSE, AND A PREDICATE IS THE ONLY FORM THAT HOLDS

Three of the four failures are one cause: **the artwork was commissioned to look
right in 2D, and nothing in the brief said it would be extruded.** `glass_shower`
is all strokes, `shower` is a bare filled rect, `boat_trailer` is five
fragments — three drawing outcomes, one instruction.

**The existing guards stop exactly one layer short.** `svg_error` (D70) checks
well-formedness; `test_every_catalog_symbol_renders_something` (D71) checks that
a symbol draws ink. **`glass_shower` draws plenty of ink and extrudes to
nothing** — nothing in the suite asks whether artwork is EXTRUDABLE.

> **A BETTER PROMPT IS AN INSTRUCTION, AND THIS PROJECT HAS RECORDED WHAT
> INSTRUCTIONS ARE WORTH: the only two things that have ever fixed a class here
> are GENERATION and A GATE THAT FAILS.** A sharper brief is worth writing and
> will not hold on its own — the next symbol is drawn by a different hand, or the
> same one on a different day.

The contract stated as source-only predicates, cheap and checkable:

1. **A symbol has at least one closed FILLED shape.** Catches `glass_shower`.
2. **The body is one connected region, not N fragments.** Catches `boat_trailer`.
3. **A census, reported not enforced: how many items have a body but NO internal
   region** — the number that would have caught `shower` and `walk_in_shower`,
   and the one no receipt has ever produced. Reported, because `box` and `slab`
   forms are legitimately featureless and a hard failure there would be wrong.

**And the receipt for a sharpened brief is not a nicer render:** re-run the new
instruction on a symbol that already failed and check the result against the
predicate. Otherwise *"I added specificity to the prompt"* is a claim of the
same shape as a green gate standing in for a tier decision.

## 6. TIER, AND WHAT IS OWED

**AMBER, all of it** — redraws and any extruder change both alter what an
operation produces. Nothing merges without Patrick's check.

**Order:** the §5 measurement first, since it decides whether the redraws are
drawn against a working extruder or a broken one. Redrawing a bench that the
extruder will punch into the floor is work done twice.

**Three record failures to close, all in how this check arrived:**

1. **No `0016-report`.** Both renders reached the reviewer as terminal
   screenshots one day after [`README.md`](README.md)'s channel contract retired
   exactly that. **A check request is a report.**
2. **No evidence PNG committed.** Every prior check shipped one — `prism-check-before/after.png`,
   `seat-check.png`, `seat-plan-symbols.png`. `docs/evidence/` has nothing since
   2026‑08‑14.
3. **The check named no plan.** Which is how §1 happened.

**And a standing addition to the check protocol, which is the reusable part:**

> ### A CHECK REQUEST NAMES THE PLAN AND LISTS THE ITEMS IT CONTAINS.
>
> The reviewer can then verify the subject was in frame **before** reading the
> verdict — which is a precondition, asserted, in the one place this project had
> not yet been asserting one.
