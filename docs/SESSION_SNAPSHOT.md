<!-- SNAPSHOT-HEAD: ad73b21 -->

# Session snapshot — read this first

**Re-cut 2026‑08‑12, and kept current by the gate ever since — see the box
below.** The cut before it sat **eight commits stale**: it pinned `main` at
`4e08191`, and its §0 named the furnishings census as the next task when that
census was done, ruled and committed. **That is the last time this file was
allowed to drift.**

This file exists so a fresh session can start from disk instead of from a chat
summary. It is an **index and a state marker, not a second copy of the record** —
where it points at another document, that document is authoritative and this one
must not be trusted over it.

> ### THIS FILE'S STALENESS IS NOW A GATE CONDITION — 2026‑08‑12, Patrick's ruling
>
> **`tools/gate.py` fails if the `SNAPSHOT-HEAD` marker above is not the current
> tip**, in **full mode** as well as `--docs` — full mode, because that is the
> only one that writes `.gate-result.json`, which is the only thing the commit
> hook reads. A check living only in the docs lane would be one more thing
> nobody runs, which is the exact failure it exists to close.
>
> **Why it took a gate.** The previous cut carried, in bold at its line 9, a
> note saying a stale §1 had once sent a reader down the wrong queue and that
> *"the cost is paid at every reset."* **It then went stale itself, in the same
> section, in the same way, and the warning did nothing** — eight commits, and
> an archaeology pass to establish what was true. **A warning is a note to a
> reader; staleness is a property of the file.** The only two things that have
> ever fixed this class here are **generation** (`defects/INDEX.md`, `--check`)
> and **a gate that fails**. This is now the second.
>
> **The semantics, which are not the obvious ones.** The marker records the
> commit this file was cut **against** — the tip at gate time, which is what the
> pending work is built on, not the commit about to be made (which has no hash
> yet). **The marker may name HEAD or its parent**, and that one commit of slack
> is not leniency: the gate runs *before* a commit, so the instant that commit
> lands the marker is one behind. **An exact-match rule would leave the
> repository RED AT REST** — red after every correct commit, red for CI on every
> push (CI calls this tool with `--deep`, which runs the check), red for the next
> session before it had done anything wrong. **A gate that is red in its resting
> state trains people to ignore it**, which would rebuild this very problem in a
> louder form. Worst-case drift is **two** commits, against the **eight** it
> reached.
>
> **What it does not do:** it cannot check that anyone re-read the content. It
> makes this file impossible to ignore, not impossible to update carelessly —
> which is why the gate asserts the marker and the `main` row in §1 carry the
> **same** hash, so the marker cannot be bumped while the prose beside it goes
> on lying.

> **[`README.md`](README.md) is the map** — what each document is, which decide
> things, which are history. **[`ROADMAP.md`](ROADMAP.md) is the autonomy
> charter** — which items may proceed without Patrick and which may not. Read §4
> below for the short version, and the map for the whole.

---

## 0. WHERE THE WORK IS

**THE ENCLOSURE QUESTION IS THE LIVE ITEM, and it is Patrick's to rule on —
Code's part (the measurement) is done.** [`handoff/0016-ruling.md`](handoff/0016-ruling.md)
found, from an actual render, that three enclosure symbols at near-identical
footprint and the **same height** are indistinguishable in 3D, and that
`form="enclosure"` may be conflating a **vessel** (recess-into-top, correct) and
a **room** (a tall hollow volume, where a low internal feature should stand on
the floor, not recess into the ceiling). **[`handoff/0017-report.md`](handoff/0017-report.md)
is the owed measurement, confirming the mechanism** — `walk_in_shower`, `sauna`
and `whirlpool` **all** produce a WELL (an opened cap); correct for `whirlpool`,
wrong for the other two, by the same reasoning the ruling inferred from a
picture. **No fix and no ruling yet — Patrick's, explicitly, per his own
instruction not to rule from an inference.**

**Prism (PR #28) and region extrusion (PR #29) are still merged, and the four
furniture generators — `seat`, `bed`, `basin`, `enclosure` — are still RETIRED**
([`handoff/0015-ruling.md`](handoff/0015-ruling.md)) — **but `0016` reopened
*whether region extrusion covers the enclosures*, one of the four**, without
reopening the retirement itself. `seat`, `bed` and `basin` are untouched.

> **THE REUSABLE PART IS THE SEQUENCE, NOT THE OUTCOME:** build the cheap
> general mechanism, **re-measure**, then decide whether the specific ones are
> still wanted. **Four functions unwritten is the receipt.** Full form, with its
> two conditions and the correction it needed, in
> [`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md) — which now also carries a
> sibling finding: **"extrudes a body" is not "reads as its kind"**, the same
> substitution `0016` found in the `enclosure 6 of 7` number that helped retire
> the four generators in the first place.

**How a furnishing gets its 3D form now**, in one place:

| | |
|---|---|
| `box`, `slab` | their own generators, as before |
| everything else | **the plan symbol, extruded** — and where a closed shape carries `data-h`, its own height: **above** the body a raised region (pillow, bench, chair back), **below** it a well with the body's cap opened (tub, sink bowl), **not nested** a column of its own |
| a symbol with nothing closed to extrude | still a box, and **named** in the model's report |
| a symbol that extrudes to a **featureless** box | still not named — **the report's blind spot**, found by `0016` (`shower`, `walk_in_shower`) |

**`data-h` CARRIES A HEIGHT AND NOTHING ELSE** — position comes from the
artwork, and a test walks every SVG and fails on any other `data-` attribute. It
is measured **from the item's base**, the same datum as `height_in`.

**A CHECK REQUEST NOW NAMES THE PLAN AND LISTS ITS ITEMS**, standing rule as of
`0016`: a first verdict was withdrawn (not overruled) after the checked render
turned out not to contain the item being judged — *vacuous by precondition*,
arriving at a person instead of at code. Full form in
[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md).

---

## THE QUEUE: THE ENCLOSURE RULING, THEN THE REST OF THE BATCH, THEN GRID SNAP

1. ~~**[D72](defects/0072-gen-assets-writes-the-asset-tree-at-import.md) — the
   import-time asset write.**~~ **DONE, 2026‑08‑15.** Module-level write moved
   behind a main guard; `import _gen_assets` is now inert. **The obvious
   receipt (hash the tree before/after) was the wrong one** — it reported 13
   files differing, every one a pre-existing CRLF phantom-diff, reproduced
   identically against the unmodified generator. The controlled receipt —
   diff the *outputs* of the old and new code, not a checked-out blob against
   an output — showed **no content difference**.
2. ~~**[D71](defects/0071-renderability-is-checkable-in-a-test-where-qt.md) — the
   `QSvgRenderer` check in a test.**~~ **DONE, 2026‑08‑15, WITH A CORRECTION TO
   THE FILED METHOD.** `isValid()`, the record's proposed instrument, does
   **not** catch a symbol that parses and draws nothing — measured: it returns
   `True` for an `<svg>` with no children at all. The actual check is
   **render to a buffer and look for a painted pixel**. Its own positive
   control then caught a second bug in its own first draft: `sip.voidptr[i]`
   is a truthy `bytes` regardless of value, so the first cut reported every
   pixel painted. `tests/test_furnishings.py`, three tests, fail-first checked.
3. **AWAITING PATRICK: does `0017`'s measurement confirm a second form
   (vessel vs. room)?** If it does, **the fix is a second form, not a
   threshold** — the split is a height gap (20/36/40 vs. 78/78/78/84), and a
   threshold there would repeat the exact mistake already recorded at
   [`0012-ruling.md`](handoff/0012-ruling.md) (one 25% line split two
   structurally identical vehicle symbols). **Nothing is built until this is
   ruled.**
4. **THE AUTHORING LIST — four items, one of them provisional.**
   **`glass_shower`** (no fill at all) and **`boat_trailer`** carry forward;
   **`shower`** and **`walk_in_shower`** join (they extrude to a *featureless*
   box, invisible to the model's report). **`boat_trailer` is reclassified**:
   its form is `vehicle`, the one generator [`0015`](handoff/0015-ruling.md)
   did **not** retire, and its failure — five disconnected filled fragments —
   is what an open-frame plan symbol gives you. **Its likely fix is the loft
   design, not a redraw; it is held out of the redraw batch until that is
   decided.** So the redraw batch is really **three**: `glass_shower`,
   `shower`, `walk_in_shower` — and it **waits on item 3**, since redrawing a
   bench the extruder would still punch into a floor is work done twice.

**THEN GRID SNAP — the inversion.** The largest daily-use improvement left on
the board, and **fully specified**: snap-by-default; **shift means
unconstrained** across both gestures; the angled-wall rule **quantising length
along the ray**; intersection joins with their two refusals; and the live
length-and-angle readout showing **snapped values rather than cursor position**.

> **ITS READ-BACK IS STILL OWED AND UNCHANGED**, and it comes before any code:
> the **clause-by-clause reconciliation** marking each **EXISTS / PARTIAL /
> ABSENT**; the **thresholds with their reasons**; the **modifier audit** for
> shift; the **angle convention already in the geometry code**; and **Ctrl's
> disposition** once snapping is the default.

**Not in this queue, and where they were left:** the **vehicle loft**
(`VIEWER_NOTES` §5 — the design stands, only its urgency changed, and it may now
also be `boat_trailer`'s fix), then **parameterisation** and **AI symbol
drafting**, third and fourth, **both behind a read-back**.

**SETTABLE WALL TYPES AND PORCH RAILINGS ARE COMPLETE — 2026‑08‑13, PR #27
(`3864f38`).** D73 and **D74 both closed**; Patrick's manual check passed and is
recorded verbatim in [D74](defects/0074-thickness-cannot-carry-wall-identity-and-the.md)
and [`progress/phase-5.md`](progress/phase-5.md). Types settable, thicknesses
from **one** normative table, identity carried by **decoration along the run**,
gates **derived** rather than chosen, and the opening sheet naming what it made.
**Phase 5 still owes P5.1 and P5.3.**

> **THE AMBER GATE RETURNED A FINDING TWICE ON THIS ONE FEATURE, IN OPPOSITE
> DIRECTIONS**, and that is the argument for the tier rather than a complaint
> about it: it **refuted** the thickness ruling at PR #26 while every automated
> signal was green, and it **confirmed** the decoration channel at PR #27 where
> no automated signal could have.

*(The two parts of D74's ruling are kept below — the reasoning outlives the
feature, and §5 carries the general form.)* Settable wall types shipped at PR #26
and **Patrick's manual check refuted part of it.** Two parts, both his judgement:

1. **THICKNESS CANNOT CARRY IDENTITY.** He cannot tell a fence from a railing at
   working zoom and never will — both are physically ~2 inches, and thickness is
   already spent representing real thickness. Hedge and retaining only *appear*
   to work because those genuinely are fatter. **The general form, which outlives
   the feature: A CHANNEL COMMITTED TO REPRESENTING A REAL QUANTITY CANNOT ALSO
   CARRY IDENTITY.** The second channel is **decoration along the run** — not
   colour, not dash, both spoken for. Fence: perpendicular post ticks. Railing:
   closer, lighter cross-ticks. Hedge: scalloped edge. Retaining: keeps
   thickness. **Drafting conventions, so the exact form is adjustable — the
   channel is not.** **The fence's FILLED POST is ruled IN** (2026‑08‑12): it is
   not beyond the ruling, it completes it — see §5's categorical-channel rule.
2. **THE GATE NEEDS A SYMBOL AND THE DIALOG MUST NAME THE KIND.** Break in the
   run plus a thin quarter-circle swing arc; the properties dialog shows the kind
   as **read-only text with its reason**. **Deriving a property is not a licence
   to hide it.**

**AND ONE THING THE BUILD FOUND, which is worth more than the feature:** the
first cut of the channel **passed every test and would still have failed the
check.** Fence and railing rendered at working zoom as *the same ladder*,
differing only in how fine it was — a distinction you make by comparing, not one
you make at a glance. **No test was going to say so.** It took a render at the
zoom a person actually works at. See D74's *"the form was already adjusted once,
by looking"*.

**FURNISHINGS — THE LIVE WORK**, unblocked by the Phase 6 park below, which was
the answer [`handoff/0010-ruling.md`](handoff/0010-ruling.md) was waiting on.
The census that opened it found **a third of the catalog rendering as a box — 28
of 95**; **that is now 1 of 95** (see the top of this section). Ruled order:
**(1) the `prism` generator, and it OPENS WITH A MEASUREMENT — ✅ DONE** ·
**(2) the remaining generators by item count — now a DECISION, not a task** ·
**(3) parameterisation — a READ-BACK first** · **(4) AI symbol drafting, last,
and AUTHORING TIME ONLY.**

> **ITEM (1)'s MEASUREMENT IS DONE AND RULED — [`handoff/0012-readback-prism-outlines.md`](handoff/0012-readback-prism-outlines.md) · [`0012-ruling.md`](handoff/0012-ruling.md).**
> Of the 28: **19 BODY** (prism extrudes something recognisable), **6 PARTIAL**
> (body kept, line-drawn structure lost), **3 NONE** (fragments floating in
> space — worse than the box). **The split is by form and it is stark:** the four
> furniture forms are **16 BODY of 18**; `vehicle` is **3 of 10**.
>
> **THE RULING: BUILD PRISM, THEN RE-MEASURE, THEN DECIDE.** Do **not** build the
> four furniture generators first — if prism covers 16 of 18 on those forms, most
> may never need writing, and building them first **guarantees work prism would
> have made redundant**. `vehicle` does not wait on that decision: 3 of 10 is
> already its answer, and that is a better reason than item count ever was. **The
> three NONE items are AUTHORING work and stay separate, so a code task does not
> acquire an artwork dependency.**
>
> **PRISM'S RECEIPT IS A RE-MEASUREMENT, NOT A CLAIM** (Patrick, 2026‑08‑13):
> after it lands, **how many of the 28 box-fallback items still fall back, and
> which.** That number decides whether any further generator is written, and
> ***"a third of the catalog renders as a box"*** is the sentence it either
> falsifies or does not.

**STILL OPEN AND NOT STARTED: WIDEN THE COMMAND ROSTER, DERIVED FROM THE
PROPERTY.** Pre-committed at `2557e32` and never done. Enumerate every code path
that **WRITES TO THE DOCUMENT**, by parsing writes to the model — **not**
`MainWindow`'s methods, not the menu, not any class's public surface. Those are
containers, and *a container census can only return its own contents*. Seed set
at [`handoff/0009-readback-p6d-cutover.md`](handoff/0009-readback-p6d-cutover.md)
§Q2. **Its urgency dropped with the Phase 6 park** — it was the cutover's
prerequisite and the cutover is not happening — but **the census itself is still
worth having**, because it is the only enumeration of the document's write
surface anyone has asked for.

> **THE RE-CUT RULE, added at this cut:** a task that changes `main`'s head, the
> queue, the record count or the gate line **re-cuts §0 and §1 in its own
> commit.** Not "before the next session" — in the commit. This file went stale
> because eight commits each left it for the next one.

---

## 1. Where the work stands

| | |
|---|---|
| **`main`** | **`ad73b21`** — `0016-ruling.md` landed, on `e1eeb3a` (snapshot re-cut), on `c214619` (PR #30, D72+D71). PRs #19–#30 all merged. |
| **Branches** | **none open.** |
| **Gate** | `collected=727 ruff=clean vacuous=0 end_assign=0 snapshot=current`; OFF / ON / DEEP each **720 passed, 7 deselected**, every sum reconciling; **`Gate-Verdict: GREEN`**. **Zero xfails.** The **7 deselected are the PERF LANE** (standing P3.8 flap-class ruling). |
| **Records** | **75 records**, **27 open**. **D71 and D72 both closed**, 2026‑08‑15. `python tools/gate.py --docs` GREEN. |
| **Working tree** | see §6 — check `git status --untracked-files=all` before believing a census disagreement. |
| **THE MIGRATION** | **CLOSED 2026‑08‑11** — closing statement with its evidence in [`ROADMAP.md`](ROADMAP.md). Everything after it is features or cleanup. |
| **PHASE 6** | **PARKED 2026‑08‑12, Patrick's ruling** — see §2. |
| **PHASE 5** | **P5.2 (settable wall types + porch railings) COMPLETE**, PR #26 then PR #27, D73 and D74 closed. Progress entry at [`progress/phase-5.md`](progress/phase-5.md). **P5.1 and P5.3 not started**; the Yard catalog stays RED on artwork scope, and D46 closes with it. |

**A commit gate is enforced, not merely available.** `tools/gate.py` writes
`.gate-result.json`; a `PreToolUse` hook blocks any `git commit` unless that file
exists, reads GREEN, and is **newer than every tracked file** — every tracked
file, `.md` included, so a document edit made after the gate ran makes it stale.
See §6.

---

## 2. PHASE 6 IS PARKED — 2026‑08‑12

**Patrick's ruling. P6.a and P6.b stay MERGED AND DORMANT; P6.c and P6.d are NOT
WIRED.** The full record with its reasoning is in [`ROADMAP.md`](ROADMAP.md); the
short form:

**The subsumption case was refuted by measurement.** Phase 6 does **not** retire
`snapshot()` (4 of 8 callers die; the rest are dirty tracking and diagnostics),
**D42 does not die with it** (the re-cut has no `MoveVertices`; the drag is one
memento *wrapping* three appliers, so applier consolidation is independent), and
**D45 does not die with it** (a load-path/format change; a memento stack stores
documents and does not make the loader carry a binding). **So what remains buys a
better undo and closes no records.**

**What would reopen it, stated so the park has an exit that is not a mood:** an
**undo defect the memento stack cannot fix**, or a **feature needing semantic
replay rather than whole-document restore** (collaborative edit, scripted redo, a
diff-based audit trail).

---

## 3. THE REST OF THE QUEUE, in order

**The tiers are [`ROADMAP.md`](ROADMAP.md)'s and are also recorded in the plan
(§ "the work, tiered"). Code does not self-classify.** GREEN merges on green CI;
**AMBER stops at the PR and Patrick's manual check is the merge condition**; RED
does not start. **The GREEN batch is done and merged. A1 (D47) and A1b (D53) are
DONE**, merged at PRs #17 and #18.

> ### THE VERTEX-ACCUMULATION FAMILY IS CLOSED OR PARKED (2026‑08‑11)
>
> **Six measurement passes ended here, on Patrick's ruling. Nothing in this block
> is live work; all of it is register state.**
>
> * **[D61](defects/0061-a-room-move-permanently-adds-two-walls.md) — ACCEPTED LIMITATION**, `type:limit` on D44's precedent. `Edit ▸ Coalesce all walls now` is the documented mitigation and the accumulation is **obvious in the scene**. **Reopens if it becomes invisible, or if the mitigation stops sufficing on a larger plan.**
> * **2b — CLOSED as NOT ISOLATED, not as fixed.** The stashed implementation targeted a shape the three-state baseline disproved, and was deleted.
> * **[D66](defects/0066-a-departing-room-carries-its-neighbours-walls.md) — the one real finding** six passes produced. Parked.
> * **PARKED, register entries only:** [D63](defects/0063-a-coalesced-outline-partly-rebounds-on-save.md)'s producer 2, [D64](defects/0064-the-save-writes-an-outline-corner-at-a.md), [D65](defects/0065-weld-scene-is-implicated-in-three-separate.md). **Not to be reopened without a new instruction.**
> * **D63 producer 1 stays CLOSED** — rebound 0 on five plans, robust across four pairing tolerances.

1. **AWAITING PATRICK: the enclosure form split.** `0016`/`0017` — see §0. The
   measurement is done and confirms the mechanism; whether `enclosure` splits
   into a vessel form and a room form is his to rule on, and **nothing builds
   until it is**.
2. **THE REST OF THE SMALL BATCH — D72 and D71 done; three artwork redraws
   (`glass_shower`, `shower`, `walk_in_shower`) wait on item 1**, since
   redrawing a bench the extruder would still punch into a floor is work done
   twice. `boat_trailer` is held out of this batch entirely — see §0, its
   likely fix is the vehicle loft, not a redraw.
3. **GRID SNAP — the inversion. THE READ-BACK COMES FIRST.** Fully specified;
   §0 carries the five things the read-back owes. Was A6; it moves up because
   the furnishings work is (mostly) done and this is the largest daily-use
   improvement left.
4. **Furnishings — 3D FORMS MOSTLY DONE, three of four generators RETIRED for
   good.** Prism and region extrusion merged (PRs #28, #29). Trail:
   [`handoff/0012`](handoff/0012-readback-prism-outlines.md) ·
   [`0012-ruling`](handoff/0012-ruling.md) ·
   [`0013`](handoff/0013-report-prism-receipt.md) ·
   [`0013-ruling`](handoff/0013-ruling.md) ·
   [`0014`](handoff/0014-report-furniture-regions.md) ·
   [`0014-ruling`](handoff/0014-ruling.md) ·
   [`0015-ruling`](handoff/0015-ruling.md) ·
   [`0016-ruling`](handoff/0016-ruling.md) ·
   [`0017`](handoff/0017-report.md); log at
   [`progress/furnishings.md`](progress/furnishings.md). **What remains: the
   enclosure ruling (item 1), the vehicle loft (possibly `boat_trailer`'s fix
   too now), then parameterisation and AI drafting — both behind a read-back.**
5. **The command-roster census, derived from the property.** See §0.
6. **A2 — D11's runtime z collapse. ⏸ PARKED, twice over.** The hang is **not
   reproducible** (2026‑08‑09): five orders of magnitude on either z step leaves
   the event breakdown identical at 545, `docs/evidence/d11-a2-z-step-measurement.txt`.
   And it was **DROPPED BEHIND D68** (2026‑08‑11) — the viewer now renders the
   active floor, which makes the z collapse stop mattering for the common case.
   The instrument is kept at `evidence/d11_a2_z_step_counter.py`; **do not
   re-derive it.**
7. **A3 — D11's SERIALIZATION half.** Unblocked by **ruling R‑B**: an *additive
   optional* field or enum value does not bump the document version, so a
   stacking index can be added at `schema_revision` without a v6. AMBER.
8. **D59 — the CHEAP TWELVE at document boundaries.** A real plan was saved
   carrying an `I7`, nothing reported it, and the user met it later as a silent
   crash (D57). P1.2's O(n²)-per-edit cost objection does not touch this half.
   **AMBER, and it moves up on evidence rather than preference.**
9. **A4 — D49, the deep checks at document boundaries. AMENDED 2026‑08‑07 — read
   the amendment, not the proposal it supersedes.** The ruling: **CHECK YES, FIX
   NO**; **SAVE ASKS, IT DOES NOT REFUSE**; the report must be **ACTIONABLE**
   (rooms *and overlap area*, plus select-and-zoom). Acceptance case is `planc1`;
   `farmplace` is the silence case once D52's half 1 lands.
10. **A5 — D41, the new simple-ring invariant.** Ruled at **R‑A**. **A read-back
    is required before starting.**
11. ~~**A6 — Grid snap.**~~ **MOVED TO #3 and no longer RED** — the sub-rulings are answered and the feature is fully specified (2026‑08‑14). Kept as a row so `A6` still resolves where it is referenced.
12. **Phase 5 — the rest:** P5.1 site levels/categories/area accounting, P5.3
    site schedule fields + reports. **P5.2 is what shipped.** The Yard catalog is
    RED on artwork scope; **D46** closes with it.

**Other open records, not queued as tasks but live: D44** (an accepted limit),
**D45**, **D50** (a level's elevation is destroyed by a load/save round trip —
blocks Phase 7's Build Floor), **D52** (room-inside-a-room has no representation
and I11 misreports the workaround), **D51** (the census depends on the working
tree), **D67**, **D69**, **D71**, **D72**.
[`defects/INDEX.md`](defects/INDEX.md) is generated and is authoritative over
this paragraph.

**Patrick will ask separately for the consolidated feature-and-phase document. Do
not start it unprompted.**

### `examples/farmplaceBIGmultifloor.json` — read this before touching `examples/`

**It still fails I11, and it is TRACKED.** `check(deep=True)` →
`["I11 rooms 'Lounge' and 'Toi' overlap"]`; `check(deep=False)` → `[]`. It was
committed at **`83a3ccc`** together with the `KNOWN_UNCLEAN` exemption, which is
documented as being for **REAL PLANS carrying a known, recorded fault** — as
distinct from `planc1.v5.json`, *a fixture built to be dirty*. The entry names
**D52** as the record that owns the fault.
`test_known_unclean_still_fails` asserts each listed file is schema-valid and
**still carries its named fault**, so the list cannot become a place where
failures go to be forgotten — `roundedMultifloor.json` was on it one morning and
came off it the same afternoon.

---

## 4. How to read this repo's record

Which document answers which question:

| the question | the document |
|---|---|
| *What is the architecture? What are the house rules?* | **`CLAUDE.md`** |
| *What is every document, and which are authoritative?* | **[`README.md`](README.md)** — the map. Start here when unsure. |
| *What may proceed without Patrick, and what may not?* | **[`ROADMAP.md`](ROADMAP.md)** — the tier charter (GREEN / AMBER / RED), the autonomy policy, rulings **R‑A** and **R‑B**, and the **Phase 6 park**. |
| *What rules bind the work?* — census doctrine, gate discipline, what a receipt is, how vacuity is detected | **[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)**. Extracted from the plan because the rules outlive the migration. |
| *What is planned, and what is done?* | **[`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md)** — Status table, phase specs, risk register, sequencing rationale. |
| *What happened, and what proved it?* | **[`progress/`](progress/)** — the log, split by phase, verbatim and contemporaneous. Index at [`progress/README.md`](progress/README.md). |
| *What is broken, and what was decided about it?* | **[`defects/`](defects/)** — one record per file, `D23` is the permanent key. Index at [`defects/INDEX.md`](defects/INDEX.md); field rules at [`defects/README.md`](defects/README.md). |
| *What did an agent report, and what was ruled?* | **[`handoff/`](handoff/)** — the mailbox. Chat is not the record. |
| *What was measured, and how do I reproduce it?* | **[`evidence/`](evidence/)** — cited by records, never inlined. |
| *What was the plan before this one?* | **[`superseded/`](superseded/)** — kept because it holds material found nowhere else, **not** because it is safe to skip. |

**Reading order for a fresh session:** `CLAUDE.md` → this file →
[`README.md`](README.md) → [`ROADMAP.md`](ROADMAP.md) → then whichever row above
the task needs.

**`docs/CODE_REVIEW_v2.md` is still worth reading** for §1 (module verdicts) and
§2 (the five structural findings). Its §3 is now a pointer into `defects/`.

---

## 5. The rules that bind the work

All in [`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md): **a green signal is only
evidence about what it measures**; **retire visibility before permission**, and
enumerate a view's consumers first; **a task that changes what an operation does
owes a differential receipt**; **vacuity has three shapes** (plus UNSATISFIABLE,
its mirror); **negative assertions are where vacuity concentrates**, so
preconditions are mandatory there; **verify a probe — and a record edit —
actually landed**; **measure survival justifications** like any other claim;
**grep for identifiers, parse for shapes**; **in a test, call the production
predicate rather than restating it**; and **a tidy-up pass that outlives its mess
only touches things nobody asked it to**.

**Added since the docs refactor:**

- **EVERY CENSUS IS SHAPED BY ITS ENUMERATION SOURCE, AND THE SOURCE IS THE BLIND
  SPOT — enumerate from the PROPERTY, not from a place things are kept.** Three
  instances: the split-on-write survey enumerated a **spelling** and missed five
  `setattr` writers through two censuses; A1b's hit census enumerated a
  **predicate** and missed a 68-line `contextMenuEvent`; P6.b's roster enumerated
  a **container** (`MainWindow`'s public surface) and missed the drag, then four
  more after the trap had just been named. **The tell is the preposition** —
  *"every mutator IN MainWindow"* and *"every path that WRITES TO the document"*
  sound like one census and are not.
- **IDENTITY NEEDS A CATEGORICAL CHANNEL, NOT A SCALAR ONE — added 2026‑08‑12,
  and it has TWO INSTANCES one level apart.** **Thickness** failed because two
  types share a real thickness (*a channel committed to representing a real
  quantity cannot also carry identity* — the narrower form, which came first).
  **Fineness** then failed the same way inside the fix: tick spacing and weight
  are scalars too, and the render showed one ladder at two pitches. What worked
  was **categorical** — the fence's ticks carry a filled post, the railing's do
  not. **Ask of any identity channel: are its values points on an axis, or
  different kinds of mark?** A scalar holds in a side-by-side comparison and
  fails at a glance, and a glance is what the user gives it. Sits with the
  project's other channel rulings: dashed is spoken for twice, colour in 3D.
- **A CRITERION THAT SPLITS TWO STRUCTURALLY IDENTICAL CASES IS MEASURING THE
  WRONG THING, AND THE AGGREGATE NEVER SHOWS IT — added 2026‑08‑12, beside the
  positive control; same family, different failure.** The positive control
  catches an instrument reporting **nothing**; this catches one reporting a
  **plausible something**. One 25% line called `lawnmower` usable and
  `snowblower` not — identical symbols — while **21-of-28 looked perfectly
  respectable from above**. **The practice: inspect the items either side of the
  line, not the count**, and print every raw value so a different cut needs no
  re-run.
- **AN ACCEPTANCE STATED AS A COUNT IS SATISFIED BY REPLACEMENT.** *"40 of 40
  survive a save"* cannot distinguish forty survivors from forty removals and
  forty fresh insertions. When the question is whether a specific thing
  **persisted**, the measure must be an **identity**, not a total — the cheap
  form is a **set equality in both directions**.
- **A content correction discovered during a structural move is NEVER folded into
  the move** — it is the next commit, with its own receipt.
- **A lint that fails on correctly-recorded history is a lint that gets
  disabled.** Dangling *keys* fail the gate; dangling *links and paths* are
  reported and never enforced.
- **A boundary belongs at the instrument. Annotate, do not rewrite** — applied to
  documents, not just code.
- **TRUNCATION INVITES FABRICATION** — `| tail` has caused two different
  failures. Never truncate a gate, a census or any output you are about to quote.
  **`tools/gate.py --trailer` reprints the stored block** so the numbers never
  pass through a human. `--quick` and `--deep` deliberately do not write that
  block.
- **The GREEN criterion was amended 2026‑08‑07, and the amendment is Patrick's.**
  It reads *"no new semantics, and nothing the user must learn"* rather than *"no
  user-visible behaviour change"*. A report that fires **only when something is
  already wrong**, reusing an existing message, adds nothing to learn. A new
  mode, a new gesture, a changed default, or a message that can fire on
  **correct** work all still fail the test.
- **An append-only shared file serialises parallel branches.** Before two agents
  run at once, progress entries move to per-task files. **A precondition on
  concurrency, not a debt.**

---

## 6. Things that will waste your time if you don't know them

- **A `git commit` is BLOCKED unless a fresh green gate result exists on disk.**
  `tools/gate.py` writes `.gate-result.json` (gitignored) at the end of a
  full-mode run; `.claude/hooks/verify_gate.py` checks it exists, reads GREEN,
  and is **newer than every tracked file** — **including `.md` files**, so *edit
  the documents first, then gate, then commit*. The hook reads the RESULT FILE,
  never the commit message.
- **ONE CALL CANNOT BOTH RUN THE GATE AND COMMIT**, and the hook blocks that
  shape outright. **`--trailer` is exempt** — it runs nothing and writes nothing,
  and it is exactly the command that belongs beside a commit.
- **A `NameError` inside a Qt virtual override PRESENTS AS A SEGFAULT.** PyQt6
  aborts the process on an unhandled Python exception in an override, so the run
  dies with **no traceback and no pytest summary**. **`config.py` has an
  `__all__`**, so a constant added there is invisible to the star-importing
  modules until it is *listed*. If a headless run dies silently, wrap the handler
  and re-raise before suspecting Qt.
- **Importing `floorplanner.design.validate` DRAGS IN THE QT BINDINGS** —
  measured at P5.2 — because `floorplanner/__init__.py` star-imports the editor.
  `viewer/fp3d.py` is deliberately Qt-free and loads that module **by path**. A
  **source-text grep** guards it, so prose that merely names the bindings trips
  it; reword the prose rather than weakening the guard.
- **`QRubberBand.show()` on an offscreen viewport kills the process** —
  pre-existing, reproducible on `main`, and why no headless test covers the
  Ctrl+drag band.
- **A running app keeps the code it imported** — the status-bar version label
  shows the launch identity; restart before re-testing.
- **`gh` is not on `PATH` in PowerShell**: `& "C:\Program Files\GitHub CLI\gh.exe"`.
  It *is* on PATH under the bash tool.
- **`.gitattributes` forces LF**, so the CRLF phantom-diff class is closed
  structurally — but the working tree still checks out CRLF, so multi-line `\n`
  patterns in ad-hoc scripts still match nothing. Use `tools/record.py`, which
  handles it once and verifies.
- **`git commit` after `git add` commits the WHOLE index** — use
  `git commit <paths>` when anything else is staged.
- **The census reads the WORKING TREE (D51).** A stray `.json` in `examples/`
  changes `collected=` and can turn the gate red, which — with the commit hook —
  **blocks every commit in the repository**. Check
  `git status --untracked-files=all` before believing a census disagreement is
  real.
- **A plan for a MANUAL CHECK goes in `fixtures/`, never `examples/`.**
  `examples/` is the corpus: schema-validated, frozen, and a change there needs a
  declared justification. See [`../fixtures/README.md`](../fixtures/README.md).
- **Macro replay geometry matters**: a `.fpm` replays correctly only at the
  window geometry it was recorded at; each pinned test states which.
- **The suite's console is cp1252** — no non-ASCII in test output.
- **Migrating the records to GitHub Issues has a precondition**: none of the 15
  labels or 20 milestones exist yet. `tools/defects_to_github.py --create-labels
  --yes` first; `--execute` refuses without them.
