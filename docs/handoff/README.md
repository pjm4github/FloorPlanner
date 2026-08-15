# The handoff mailbox — protocol

**Two agents work on this repository: one writes code, one rules on it. This
directory is where they hand things to each other.** The rule that makes it
worth having is short:

> **Chat is not the record. A report is complete when it is on disk; a ruling is
> authoritative only from its file.**

That is not a new rule. It is the Working agreement's *"a checkpoint is not
complete until its handoff spec is committed"*, given a place to live.

---

## The protocol

1. **Code writes `NNNN-report.md` and commits it.** A read-back, a census, a
   measurement, a question — anything that needs an answer before work can
   continue. Reporting it in a terminal is not reporting it.
2. **The reviewer writes `NNNN-ruling.md` and commits it.** Decisions, with
   their reasons. A ruling that exists only in a conversation cannot be quoted
   later, cannot be found by the next session, and cannot be disagreed with on
   the record.
3. **The numbering is sequential and shared.** A report and its ruling take the
   same number. Next free number = highest here plus one, archive included.
4. **A closed pair moves to [`archive/`](archive/) when its task ticks.** The
   mailbox shows what is live; the archive keeps what was decided.

## THE CHANNEL CONTRACT — Patrick's standing change, 2026‑08‑14

**This directory is the channel, not a record kept alongside one.** Patrick's
Cowork session reads this repository directly; he no longer relays reports by
hand. So a report written *for a terminal to carry to him* is written for a
reader who no longer exists, and the protocol above is now stricter than its
first sentence suggested — this is what it means in full:

* **The terminal gets one short paragraph**: what was done, what is needed, and
  the file number. **Nothing else.** The report, census, read-back or receipt
  itself goes to `docs/handoff/NNNN-<kind>.md`, committed, in full.
* **Code does not write `-ruling.md` files, ever.** The reviewer writes
  `docs/handoff/NNNN-ruling.md` directly, on disk. Code's job is to **read it,
  act on it, and cite it** — not to transcribe it into a file of its own.
  "Record this ruling" means *cite the file the reviewer wrote*, not *author a
  copy of it*.
* **Never edit a file the other side wrote. Never expect the other side to edit
  one of yours.** Each side only *creates new numbered files*. A correction is
  the **next number**, in the open — not a silent edit to an earlier one.

**THE SUFFIX SPLIT (`-report.md` vs. `-ruling.md`) IS NOT A NAMING CONVENTION —
IT IS THE MECHANISM THAT MAKES THE COLLISION IMPOSSIBLE.** Two writers touching
the same file, even at different times, is exactly the shape that has already
cost sessions here: the append-only `side-tasks.md` conflict this project
measured and fixed by moving to per-file logs, and the case where a reviewer's
correction very nearly got written into the wrong party's words on the strength
of a premise the implementer had already disproved. **If each side owns its
suffix absolutely, there is no file either side is ever tempted to open in
place of the other's** — the split removes the failure mode rather than asking
either party to remember not to trigger it.

**Auto-commit is permitted for GREEN-tier work** — Code commits, pushes and
merges without asking, per the autonomy policy. **The pre-commit hook (a fresh
green gate, newer than every tracked file) is the only bar**, unchanged by this
rule. **AMBER still stops for Patrick's manual check before merge**; nothing
merges on a red gate or a failed check. This rule changes *reporting*, not
*authority*.

## How the rest of the record refers to a pair

**A progress entry CITES its handoff — one line, `handoff: 0042` — and does not
restate it.** Ruled 2026-08-06, and the reasoning is worth keeping: the progress
log is *curated* (what happened, why, what proved it) and a handoff file is *raw*
(the exchange itself). Different genres, different readers. Collapsing them would
make the log inherit the exchange's verbosity, and the log is already 4,351
lines. Same relationship the log already has with `docs/evidence/`: cite the
artifact, do not inline it.

## Every handoff lists `fixtures/incoming/`, with the age of each file

**Ruled 2026‑08‑09.** The intake directory
([`../../fixtures/incoming/README.md`](../../fixtures/incoming/README.md)) is
where Patrick drops plans that break or look wrong, uncharacterised and
unreferenced by any test. It is invisible to the gate **by design**, which means
nothing else will ever mention it.

So a report **names every file in it and how old each one is**. And **a file
that has sat there across two handoffs without triage is itself a finding** —
evidence arriving faster than it is being read — and it is stated out loud
rather than left to accumulate. The three exits (promote with a fail-first test,
delete as a duplicate naming its cover, delete as no-defect-found naming what
was checked) are in that README.

## What belongs here, and what does not

| | |
|---|---|
| **here** | read-backs, pre-work censuses, rulings, findings that need a decision, disagreements and how they resolved |
| **`../progress/`** | what was done, in the order it was done, with its gate |
| **`../defects/`** | a fault, gap, limit or task that outlives the exchange |
| **`../evidence/`** | the measurement itself, and the probe that produced it |

A report that turns out to describe a defect gets a record in `../defects/`; the
report is not the register, and the register is not a conversation.

## Two conventions that keep the pair readable

**Quote the ruling, do not summarise it.** A ruling file carries the reviewer's
words. A summary of a decision is a second version of it, and this project has
measured what second versions do.

**A report states what it measured and what it could not.** The instrument's
boundary belongs in the report, because the ruling depends on it — several
rulings in `0001` turned on exactly that.

---

| pair | subject |
|---|---|
| [`0001-report.md`](0001-report.md) · [`0001-ruling.md`](0001-ruling.md) | The docs refactor: read-back, eleven findings, and the rulings that settled them |
| [`0002-report.md`](0002-report.md) | Repository state at 2026‑08‑09: `main` @ `a604d40`, the vertex-accumulation programme, and what is owed before 2b |
| [`0003-report.md`](0003-report.md) | D61's three owed items measured — the arrow points up by +2, none of the 69; 28 = 40 slots, residue 0; `normalize_walls` has one caller. **D62 filed** |
| [`0004-report.md`](0004-report.md) | The leave path does not weld, D62 is runtime-only, the pair is already a fixpoint, 28 of the 29 are a neighbour's corner — **and 2a's fix partly evaporates on save** |
| [`0005-report.md`](0005-report.md) · [`0005-ruling.md`](0005-ruling.md) | **Reboot state 2026‑08‑10.** `main` @ `175c474` pushed; branch `d62-weld-and-fixture-layout` @ `5f5cd3e` in **PR #19**, unreviewed. The rebound's two producers, the weld repair, the 0.005 sq ft area bound, the `fixtures/incoming/` contract, and the queue |
| [`0006-readback-outline-invariants.md`](0006-readback-outline-invariants.md) | **Read-back, measurement only.** The two OUTLINE invariants: which corpus files fail each (**completeness: `08‑09R` only; simple ring: five files incl. `symmetricP1`**), the cost that puts completeness in the **cheap twelve — but only indexed** (0.917 ms against 36 ms naive), the **declared 0.05″ perpendicular** tolerance on a three-decade plateau, and **land them SEPARATELY** |
| [`0007-readback-phase-6.md`](0007-readback-phase-6.md) | **Read-back, measurement only.** Phase 6: **retiring snapshot undo does not retire `snapshot()`** (4 of 8 callers die; 3 are dirty tracking, 1 diagnostics), the command surface is **14 public mutators** against P6.1's nine Phase-0 classes **and the drag is in neither**, and the subsumption claim is **two records, not "several"**. Three rulings move it RED -> AMBER |
| [`0008-readback-phase-6-deep.md`](0008-readback-phase-6-deep.md) | **Read-back, measurement only — the four questions.** `_commit_if_changed` is **the per-mutation shadow-mode hook wearing undo's clothes**; the boundary must be the **settled gesture** (a label-drag crosses six sub-operations whose intermediates are not documents); Phase 6 is a **CUTOVER** because the stack is driven by `scene.changed`, not by operations; and **2b survives** — the growth is forward-path, so undo makes debris removable, not absent |
| [`0009-readback-p6d-cutover.md`](0009-readback-p6d-cutover.md) | **Read-back, measurement only — P6.d's three questions.** **Q1 ENTITIES: undo restores EVERY floor**, measured on `roundedMultifloor`, so **D67 does not block the cutover**. **Q2 NO: commands cannot yet be the sole dirty source** — and the re-cut command list has its own gap, missing `EditRoomProps`/`EditOpening`/`ChangeSettings`/level ops because it was derived from `MainWindow` methods. **Q3 determinism carried forward.** |
| [`0010-census-furnishings.md`](0010-census-furnishings.md) · [`0010-ruling.md`](0010-ruling.md) | **Census, measurement only.** **The cost of one new furnishing is TWO EDITS IN ONE FILE plus one command**, measured by adding one. `CLAUDE.md`'s "no app-code change" claim **tested and TRUE**. The 3D form is **not one box per item** — **2 of 9 forms built, 67 of 95 items covered, 28 falling back with a report**, so the work is BUILDING seven generators, not authoring. No parameterisation: each size is its own entry. The AI menu is **one action**, prices only. **[D70](../defects/0070-the-asset-generator-writes-a-corrupt-svg.md) found while measuring.** **RULING:** prism first, then the generators by item count, then parameterisation (read-back), then AI drafting — **authoring time only, never plan time**. |
| [`0011-census-wall-types-and-railings.md`](0011-census-wall-types-and-railings.md) | **Census, measurement only.** **The feature is mostly already built**: `wall.type` already has `railing`, and the viewer already has its thickness, height (36") and colour. **The gap is the SCENE and the UI** — `WallItem.t` is binary, the menu offers two types, and the editor cannot create a `gate` at all. **Contradicts four of six provisional rulings**, mostly by being done already: no schema change is needed, and I7 already restricts landscape walls to gates. **[D73](../defects/0073-two-wall-thickness-tables-disagree-and-one.md)** filed. |
| [`0012-readback-prism-outlines.md`](0012-readback-prism-outlines.md) · [`0012-ruling.md`](0012-ruling.md) | **Read-back, measurement only — ruling 0010 item ONE's opening question.** Of the 28 fallback items, **19 have a filled BODY prism can extrude, 6 give a PARTIAL solid, 3 have NONE** (prism would be worse than the box). **The split is by FORM and it is stark**: the four furniture forms are **16 BODY of 18**, `vehicle` is **3 of 10** — so **prism may retire four of the five pending generators** and vehicle-first survives for a stronger reason than item count. **The instrument's first cut was wrong and is withdrawn**: one 25% threshold split `lawnmower` from `snowblower`, two structurally identical symbols, and it was caught by inspecting either side of the line rather than by reading the totals. **RULING:** build prism, **then RE-MEASURE, then decide** whether the four furniture generators are still wanted — building them first guarantees work prism would have made redundant. Vehicle-first survives for the better reason. The three NONE items are **authoring work, kept separate so a code task does not acquire an artwork dependency**. Two rules recorded (categorical channel; a criterion that splits identical cases), and **the snapshot's staleness is now a gate condition**. |
| [`0013-report-prism-receipt.md`](0013-report-prism-receipt.md) · [`0013-ruling.md`](0013-ruling.md) | **Prism is built, and this is its receipt — a re-measurement through `build_model` itself, on one of every catalog kind.** **The box fallback goes 28 → 1**: only `glass_shower` is left, the one symbol drawn entirely in strokes. `vehicle` 10 of 10, `seat` 6 of 6, `bed` 4 of 4, `basin` 1 of 1, `enclosure` 6 of 7. **But 27-of-28 overstates it, and the picture says where:** `boat_trailer` extrudes five disconnected slabs and no trailer, exactly as the read-back predicted; `bicycle` does not (thin, but a bicycle is thin). **No threshold was added to catch it** — that is the instrument whose failure is already recorded. Authoring list is now **two**, not three. **RULING:** prism is **AMBER and landed on `main` without its check** — backed out and re-applied at a PR; a strong number was allowed to stand in for a tier decision, and *a green gate and a strong number are evidence about the code, not about the tier*. `boat_trailer` stays extruding (artwork fix, not a threshold); `bicycle` stays as it is; **the reserved decision stays reserved until Patrick has looked.** |
| [`0014-report-furniture-regions.md`](0014-report-furniture-regions.md) · [`0014-ruling.md`](0014-ruling.md) | **Report, measurement only — the furniture half, narrowed.** **The vehicle half is settled by EYE** (Patrick: tractor, lawn mower and snowblower visibly changed; sofa and bed in the same view still slabs) and was not re-measured. **THE OUTER OUTLINE IS A PLAIN RECTANGLE FOR 17 OF 18** — a 4-vertex prism is a box, and that is the honest replacement for 28 → 1. **Closed internal paths EXIST but not where it matters most:** beds have pillows, `bathtub` has its well, `kitchen_sink` its bowls — but **`sofa`, `armchair` and `loveseat` draw the back as ONE LINE**, so the cheap answer is shut for the three seats a room is fullest of. `dining_chair` and `office_chair` are counter-examples in the same form. **Cost of the cheap answer: 17 filled regions to annotate, in `_gen_assets.py`, plus one loop in `build_prism`.** **RULING: BUILD IT** — one generator, not four. **The three seats are an ARTWORK fix**, not a limit of the approach: `dining_chair` and `office_chair` draw their backs as closed rects *in the same form*, and redrawing makes the PLAN symbol more correct too, which is the tell. **Annotation beside the artwork accepted**, with the boundary that it carries a HEIGHT AND NOTHING ELSE — a heuristic would *invent a number the document does not contain*, the same objection that refused `--stack`. Authoring list now **five**. |
| [`0015-ruling.md`](0015-ruling.md) | **Ruling only — no report.** **THE FOUR FURNITURE GENERATORS ARE RETIRED**: `seat`, `bed`, `basin`, `enclosure` — not deferred, not pending, and never written. `vehicle` is NOT retired with them (the loft design stands). **The reusable part is the SEQUENCE, not the outcome: build the cheap general mechanism, re-measure, then decide whether the specific ones are still wanted — four functions unwritten is the receipt.** Two conditions on it, and the correction it needed (28 → 1 overstated the win; 17-of-18 was the honest number). Also: *"not needed" is a measurement and "retired" is a decision, and the register should not blur them.* |
| [`0016-ruling.md`](0016-ruling.md) | **Ruling only — no report** (§6 names why that is itself a failure). **The "chunky boat trailer" verdict is WITHDRAWN**: the item was not in the checked frame — *vacuous by precondition*, arriving at a person rather than at code. **Three enclosures at near-identical footprint are ONE BOX WEARING THREE NAMES** — the categorical-channel rule's third instance, the first in 3D. **`form="enclosure"` conflates a VESSEL and a ROOM**, inferred from a picture and explicitly **not ruled** — Code owes a three-line measurement first. **Authoring list grows to four** (`shower`, `walk_in_shower` join it — both extrude to a *featureless* box, which the model's report structurally cannot name). **`boat_trailer` is reclassified as probably NOT artwork** — its form is `vehicle`, the one generator 0015 didn't retire; its fix is plausibly the loft, not a redraw. **Standing addition: a check request names the plan and lists its items.** |
| [`0017-report.md`](0017-report.md) | **Report, measurement only — the SS5 measurement owed from 0016, no ruling.** For `walk_in_shower`, `sauna`, `whirlpool`: black-box probe on unmodified `build_model` (is there a face at the body's full height over the region's centre?), positive-controlled against `bathtub`. **All three came out as a WELL** — correct for `whirlpool` (a vessel), and it **confirms** the vessel/room conflation for the other two by measurement rather than inference. No fix, no ruling — Patrick's to decide. |
| [`0018-ruling.md`](0018-ruling.md) | **Ruling only.** **0017's control was pointed the WRONG WAY** — every case, control included, expected and got WELL, so the instrument was never shown it could say anything else; a third member of the positive-control family, catching an instrument that can report only ONE of its two answers. The finding survives on a second instrument (the render's own notch), so the ruling proceeds. **`enclosure` SPLITS**: a new `vessel` form keeps the above/below well rule; `enclosure` becomes a room where a region is always a solid on the floor — **categorical, not a threshold**. **A second defect found on the render**: materials attach to PARTS, not items — a vessel's region is its declared contents (translucent), an enclosure's region is solid. **The check is corrected before being run**: a check must name something the CORRECT state makes visible, not the fault's signature. |
| [`0019-ruling.md`](0019-ruling.md) | **Ruling only.** `V5_MIGRATION_PLAN.md`'s Status table is the **third instance** of "a status board drifts unless generated" — P5.2 shipped complete and the table said unchecked for two days. **Freeze the closed migration's table as history; move forward status to a generated `docs/STATUS.md` with its own `--check`.** A read-back comes first: what identifies a completed unit when most recent work has no phase number at all. **Explicitly ordered behind 0018.** |
| [`0020-ruling.md`](0020-ruling.md) | **Ruling only — the coordination protocol, on disk for the first time.** Three utterances only: `NNNN is up` (read the ruling), `NNNN check passed: <what you saw>` (to Code), `NNNN check failed / unsure` (to the reviewer — a failure opens a record, it does not invite Code to guess). **A PR is never asked for** — AMBER already stops there by construction. Patrick's check words are quoted verbatim, not rounded to pass/fail, because the reasoning outlives the feature. |
| [`0021-report.md`](0021-report.md) | **Report — the vessel/enclosure split, BUILT.** `KNOWN_FORMS` gains `vessel`; `build_prism` takes the real catalog form and asks one categorical question. **A second bug found by dumping the mesh, not by the probe**: the first cut reused "sits on the body" for an enclosure's region, building `walk_in_shower`'s bench spanning 18″–78″ (near the ceiling) instead of 0″–18″ (on the floor) — the roof-over control had nothing to say about it, since it only ever asked about the cap. **Materials split alongside it** (`region_material`, falling back to body's). **One thing the render cannot show**: the bench is geometrically correct but invisible through the translucent body at any alpha tested — a renderer limit, noted against D69, not fixed here. **[D75](../defects/0075-a-recessed-floor-feature-is-not-representable.md) filed** as the accepted limit the split leaves open. AMBER, PR opens, check row 1 adjusted to the mesh numbers since the render cannot carry it. |
