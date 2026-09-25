# 0197 — ruling: R6 opens, and D50 is its gate — no multifloor plan in the corpus has a roof, and every level in every one says elevation 0.0

**On his instruction, 2026‑09‑25:** *"lets work on the multifloor 3d
rendering and roof tool."* That is authority to open R6, which
[`0186`](0186-ruling.md) §4 left waiting on two things owed by him. Both
are settled below — and a measurement moves where R6 starts.

## 1. THE MEASUREMENT — five multifloor plans, no roofs, no elevations

Read off the corpus and the fixtures, not off the record:

| plan | levels | walls | **roofs** |
|---|---|---|---|
| `examples/farmplaceBIGmultifloor.json` | L1 0.0/96, L2 0.0/96 | 79 / 30 | **0** |
| `examples/roundedMultifloor.json` | L1 0.0/96, L2 0.0/96 | 81 / 41 | **0** |
| `fixtures/crossfloor-snap-2026-08-17.json` | L1 0.0/96, L2 0.0/96 | 106 / 45 | **0** |
| `fixtures/wiscaway2026-08-30R1.json` | L1 0.0/96, L2 0.0/96 | 109 / 39 | **0** |
| `fixtures/wiscaway2026-08-30R2.json` | L1 0.0/96, L2 0.0/96 | 106 / 40 | **0** |

Three consequences, and they reorder the arc:

* **He does not owe a multifloor fixture.** Five exist; **two are his own
  wiscaway**, R1 and R2. [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md)'s
  line that `roundedMultifloor.json` is the only multifloor plan in the
  corpus is **out of date** — that was true of `examples/`, and the
  fixtures have since overtaken it. Correct it when D67 is next touched.
* **But not one multifloor plan carries a single roof record.** There is
  no multifloor roofscape anywhere on disk to compose. The fixture R6
  actually needs does not exist, and cannot be drawn until the next point.
* **Every level of every one says `elevation_in 0.0`.** That is
  [D50](../defects/0050-a-level-s-elevation-is-destroyed-by.md), live —
  and the two wiscaway files were written by the app on **2026‑08‑30,
  three weeks after D50 was filed**. The destruction is still happening,
  on his own drawings.

## 2. D50 IS THE GATE — R6.0, and R6 stays shut until it closes

[`0186`](0186-ruling.md) §4 ruled composition in **absolute height** —
the level's `elevation_in` plus the roof's own heights. On documents
where every elevation is 0.0, that composes **every storey's roofscape at
one height**: a pile. This is not a risk, it is arithmetic, and it is
precisely the image [D68](../defects/0068-the-3d-view-renders-every-level-not-the.md)
deleted on purpose — *"what is removed is a misleading view, not a
working one."* Build R6 first and we rebuild the view D68 removed, this
time with the envelope machinery pruning roofs against each other at a
height none of them has.

**RULED: R6.0 is closing D50, and it is the whole first tranche. AMBER.**
Its acceptance is already written, in D50's own Receipt — the
`--list-levels` round trip. As ordered:

1. **`model.Floor` gains `elevation_in` and `height_in`.** D50's
   mechanism is exact and saves the census: `Floor` has only `name` and
   `reference`, so all three writers emit literals —
   `bridge.py:796` (scene walk), `bridge.py:976` (detect),
   `importer.py:184` (legacy import). Fields first, then those three read
   them.
2. **MEASURE THE LOADER FIRST — D50 does not.** Its evidence is a
   round trip, which cannot tell a lossy writer from a lossy loader. Does
   `load_data` put a document's `elevation_in` / `height_in` onto the
   `Floor`, or drop them on the way in? **Report the measurement before
   writing a line.** A writer fixed over a loader that discards still
   round-trips to 0.0, and the round-trip test would pass on a plan whose
   levels were 0.0 to begin with — which is every plan we have.
3. **Stored, not derived.** A new level's elevation **defaults** to the
   level below's elevation plus its height, is **written**, and is
   editable. Deriving it on read is refused for D50's own stated reason:
   it refused a `--stack` flag that invents a number the document does
   not contain, and a derived elevation is that flag moved into the model.
4. **Say which height the existing code reads.** `height_in` is the
   **storey** height and is not the same thing as a wall's height. Name,
   measured, what the wall and roof paths read today, before changing
   either. A storey height that silently becomes a wall height is a
   worse defect than the one being closed.
5. **No schema change.** `level` has carried both fields since v5 was
   vendored at P0.7 — D50's own *"THE SCHEMA IS NOT AT FAULT"*.
6. **Acceptance:** D50's Receipt verbatim, extended across all five
   plans of §1 — set L2's elevation and height, open, save, read back,
   values unchanged. D50 closes with `closed_by` that report.

## 3. THEN THE FIXTURE — and it is one gesture of his

Once R6.0 lands, his part is small and specific: **open
`fixtures/wiscaway2026-08-30R2.json`, set L2's elevation to the real
storey height, draw a roof on L2 over the upper walls, save.** That file
is the R6 fixture. Nothing else is owed by him. Until it exists, §5's
composition work has synthetic cases only — and every arc in this record
has been carried by one of his drawings, not by a scene someone invented.

## 4. HIS TWO ANSWERS, RULED IN

* **Plan view — which roofs draw.** His answer: **this level's roofs
  solid; a roof on any other level that covers this level's rooms draws
  ghosted.** Adopted. It reuses `roof_clip_spans`, which already answers
  *which roof covers this room*, so the display rule follows the
  machinery instead of adding a predicate that could disagree with it.
  The corollary is what earns it: **an R3b wall dash never appears on a
  plan with no roof drawn above it.** Ghosting style is one line in the
  report, not a design exercise.
* **3D default — the whole building.** Adopted, and D68's own reasoning
  licenses the flip: it scoped the view to one floor because *"what
  rested on this one was an image that lied"*, and closing D50 is what
  stops it lying. D68's boundary rule still governs — **geometry scope is
  a `build_model` parameter, not a view filter** — and `levels=` already
  exists, so this is **one call site**, `MainWindow.show_3d_view`,
  ceasing to narrow. [D69](../defects/0069-an-auxiliary-control-panel-on-the-3d-view.md)'s
  panel is how a user asks for one floor again; **it is not a
  precondition** and does not gate this.

## 5. THE ORDER, AND ONE MEASUREMENT BEFORE THE ROOF TOOL

**R6.0 (D50) → his fixture → R6.a (§4's two answers) → R6.b (composition
over all live roofs in absolute height, 0186 §4's principle) → R6.c (the
roof tool across levels).** Never two open AMBER tranches at once, as
0186 §5 has it.

**Before R6.c is written, reproduce or refute D67.** It is testimony, not
measurement, unreproduced since 2026‑08‑11, and it is exactly the roof
tool's hazard — a ridge sketched on L2 picking up L1's vertices. D67
names its own fixture, says the suite's silence is *"about nobody having
asked"*, and marks its three candidate sites **explicitly unmeasured**.
One headless run on `roundedMultifloor.json`: drag across floors, undo,
compare floor 1 to pristine. **If that undo comes back partial, D67 says
it blocks the cutover and the consequence is pre-committed** — so the
answer is wanted before the roof tool gains a level dimension, not after.

**And one more measurement in the same report:** does any roof path read
the level's elevation today? Every roof height is measured from the
level-base datum (0186 §4, citing [`0140`](0140-ruling.md) §3). When the
level base stops being zero, say whether the dialog's seeded heights —
R3b's governing ceiling — are still right, measured on his fixture, not
reasoned about.

## 6. WHAT IS NOT IN R6

[D11](../defects/0011-four-competing-z-order-systems-two-of.md)'s z
collapse and D69's panel are separate open records and are **not this
arc**. If closing D50 does not by itself put each storey at its own
height in 3D, say so in the R6.0 report and D11 gets its own ruling —
do not absorb it quietly.

## 7. RECORD — the same gap, twice

`299576a` merged PR #65 on his word — *"that fixed it, merge PR #65"* —
and **no numbered report records it**, the same gap 0195 §4 corrected one
tranche ago. **The R6.0 report opens by recording it.** Twice running
makes it the pattern rather than a slip: the merge belongs in the report
that follows it, every time, with his words and the commit.

**Carried:** unchanged from [`0196`](0196-report.md).
