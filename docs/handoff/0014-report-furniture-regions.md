# 0014 — report: the furniture half, and the one fact the decision turns on

**MEASUREMENT ONLY. Nothing is built, nothing is decided, and the vehicle half
was not re-measured** — it is settled by inspection, below.

Probe: [`../evidence/furniture_internal_regions.py`](../evidence/furniture_internal_regions.py).
Parses the 18 `seat` / `bed` / `basin` / `enclosure` symbols with the **viewer's
own** ring reader, so it cannot report a shape the extruder would not see.

---

## 0. THE VEHICLE HALF — confirmed by eye, and this is its receipt

> **Patrick, 2026‑08‑13, on prism-live code on a real plan: tractor, lawn mower
> and snowblower have visibly changed shape, while the sofa and the bed in the
> same view are still slabs.**

**That is the vehicle form gaining real geometry and the furniture forms gaining
nothing** — the split the read-back predicted, confirmed by inspection rather
than by count. **`garden_tractor`, `lawnmower` and `snowblower` are the three
named**, and no re-measurement of the vehicle half was run or is owed.

**It also explains the "no change" report** that opened this: on a real plan the
furniture is what you see first, and the furniture is exactly what did not
change. Section 1 says why in numbers.

---

## 1. THE OUTER OUTLINE IS A PLAIN RECTANGLE FOR 17 OF 18

**A 4-vertex prism is a box.** After simplification (duplicate and collinear
points removed), the outer outline of every furniture symbol but one is a
**rectangle**:

> `kitchen_sink, bed_full, bed_king, bed_queen, bed_twin, bathtub, glass_shower,
> sauna, shower, swim_spa, walk_in_shower, whirlpool, armchair, dining_chair,
> lounge_chair, loveseat, sofa`

**The one exception is `office_chair` — 24 vertices**, because it is drawn as a
circle.

**This is the honest replacement for 28 → 1.** That figure counted items that
*extrude*; it could not distinguish *extrudes something* from *extrudes a
rectangle*. Prism gave the vehicles real outlines and gave the furniture **a box
by a different route** — same solid, arrived at from the artwork instead of from
the footprint. Patrick saw exactly that.

---

## 2. THE ANSWER TO THE DECIDING QUESTION: **CLOSED PATHS EXIST, BUT NOT WHERE IT MATTERS MOST**

**Per item, closed shapes beyond the outer outline.** `nested` = centroid inside
the outline (a tub's well, a pillow); `beside` = a separate closed region
adjacent to it (a chair back beside its seat).

| kind | form | outer v | nested | beside | strokes | what the closed shapes are |
|---|---|---:|---:|---:|---:|---|
| `kitchen_sink` | basin | 4 | 3 | 0 | 0 | two bowls (filled), drain (unfilled) |
| `bed_full` | bed | 4 | 2 | 0 | 1 | two pillows (filled) |
| `bed_king` | bed | 4 | 2 | 0 | 1 | two pillows (filled) |
| `bed_queen` | bed | 4 | 2 | 0 | 1 | two pillows (filled) |
| `bed_twin` | bed | 4 | 1 | 0 | 1 | one pillow (filled) |
| `bathtub` | enclosure | 4 | 2 | 0 | 0 | **the well (filled)** + drain |
| `glass_shower` | enclosure | 4 | 4 | 0 | 14 | all unfilled — tray, door, fittings |
| `sauna` | enclosure | 4 | 4 | 0 | 1 | bench (filled) + 3 unfilled |
| `shower` | enclosure | 4 | 2 | 0 | 2 | both unfilled |
| `swim_spa` | enclosure | 4 | 5 | 0 | 1 | well (filled) + 4 unfilled |
| `walk_in_shower` | enclosure | 4 | 6 | 0 | 9 | tray (filled) + 5 unfilled |
| `whirlpool` | enclosure | 4 | 8 | 0 | 0 | well (filled) + **7 jets** (unfilled) |
| **`armchair`** | seat | 4 | **0** | **0** | 3 | **nothing — strokes only** |
| `dining_chair` | seat | 4 | 0 | 1 | 0 | **back panel, a closed rect beside the seat** |
| `lounge_chair` | seat | 4 | 1 | 0 | 2 | headrest (filled) |
| **`loveseat`** | seat | 4 | **0** | **0** | 4 | **nothing — strokes only** |
| `office_chair` | seat | **24** | 1 | 1 | 0 | back (filled, beside) + hub (unfilled) |
| **`sofa`** | seat | 4 | **0** | **0** | 5 | **nothing — strokes only** |

### The answer, split the way the artwork splits

**BEDS, BASIN AND MOST ENCLOSURES: the cheap answer is OPEN.** A bathtub's inner
well is a filled rectangle inside its rim; a bed's pillows are filled rectangles;
a sink's bowls are filled rectangles. **These are exactly the regions Patrick
described**, present as closed paths, on disk, today.

**THE THREE UPHOLSTERED SEATS: the cheap answer is SHUT.** `sofa`, `armchair`
and `loveseat` share one pattern, and it is the pattern the question named:

```
<rect .../>                                  the outer body
<line x1="0.75" y1="7" x2="83.25" y2="7"/>   THE BACK — a single line
<line x1="7"    y1="7" ... y2="35.25"/>      an arm — a line
<line x1="77"   y1="7" ... y2="35.25"/>      an arm — a line
```

> **A sofa's back panel is drawn as ONE LINE, not as a closed rectangle.** So is
> each arm. There is no region to extrude and nothing to give a height to.

**`dining_chair` and `office_chair` are the counter-examples inside the same
form** — both draw the back as a real `<rect>` — which is why this is reported
per item rather than per form. **3 of 6 seats have a closed back or headrest; 3
have nothing at all.**

### One correction, made by reading rather than by parsing

**The first cut of this census reported `dining_chair` as having no internal
closed paths.** It has a back panel drawn as a closed rectangle — the exact case
the question is about — sitting *beside* the seat rather than nested inside it,
and the criterion only counted nested shapes. **Caught by opening the four
files**, which is the third time on this feature that looking has overturned
counting.

---

## 3. THE COST, IF THE CHEAP ANSWER IS TAKEN — costed, not built

**What exists to annotate, counted rather than estimated:**

| | |
|---|---:|
| closed shapes beyond the outline, all | **45** |
| …of which **filled** (a region, not a mark) | **17** |
| items carrying at least one filled region | **13 of 18** |

**The 28 unfilled remainder are drains, jets, door swings and fittings** —
marks, not regions. Whether any earns a height is a judgement; the two counts are
separate so it stays one.

### Where the height would come from, and why it is DATA

**The artwork says where a region is. It does not say what the region IS** — the
parser cannot tell a pillow from a drain, and the difference is a height. So the
region needs a name, and there are three places it could come from:

| | how | cost | what it costs later |
|---|---|---|---|
| **(a) authored beside the artwork** | `_gen_assets.py` emits `data-h="6"` (or a role name) on each region it draws | **17 attribute additions**, in the file that already draws them, plus a viewer change to read one attribute and extrude per region | nothing — a new symbol states its own regions as it is drawn, which is the same "two edits and a command" the 0010 census measured |
| (b) a rule by ordinal | "the second-largest ring is the well" | almost none | **fragile**: it breaks silently whenever artwork is re-ordered, and nothing would report it |
| (c) a geometric heuristic | "nested + filled → raise 40%" | none | **it invents a number the document does not contain** — the same objection that refused `--stack` for the viewer |

**(a) is the only one that is data.** It puts the statement where the artwork is
authored, generalises across every form without a function per kind, and is a
**per-region height rule** exactly as described.

**The viewer side is one generator, not four:** `build_prism` already returns a
list of parts and already extrudes a ring between two heights. Per-region heights
are the same loop with a per-ring `z0`/`z1` instead of one pair.

**What it would NOT fix:** `sofa`, `armchair` and `loveseat` — 3 of 6 seats, and
the three a room is most likely to be full of. **No annotation can name a region
that is not drawn.** For those, either the artwork gains a closed back panel (an
authoring change, in the same file, of the same kind) or a bespoke generator
invents the structure.

---

## 4. WHAT IS NOT CLAIMED

* **That the filled regions are all worth a height.** `whirlpool`'s eight
  circles are jets; `walk_in_shower`'s nine strokes are fittings. Counted, not
  judged.
* **That a per-region extrusion looks right.** It has not been built or
  rendered. The last three predictions on this feature were settled by looking,
  and two of them went against what had been written down first.
* **Anything about `vehicle`.** Not re-measured, by instruction; §0 is its
  receipt.
