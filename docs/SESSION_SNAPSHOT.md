<!-- SNAPSHOT-HEAD: 92a8813 -->

# Session snapshot — read this first

**Re-cut 2026‑08‑12, and kept current by the gate ever since — see the box
below.** The cut before it sat **eight commits stale**: it pinned `main` at
`4e08191`, and its §0 named the furnishings census as the next task when that
census was done, ruled and committed. **That is the last time this file was
allowed to drift.** This file
exists so a fresh session can start from disk instead of from a chat summary. It
is an **index and a state marker, not a second copy of the record** — where it
points at another document, that document is authoritative and this one must not
be trusted over it.

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

**[D74](defects/0074-thickness-cannot-carry-wall-identity-and-the.md) — the PR #26 follow-up — IS BUILT AND WAITING ON PATRICK'S CHECK, at [PR #27](https://github.com/pjm4github/FloorPlanner/pull/27). AMBER.**
**His check: at working zoom, tell a fence from a railing without clicking, and
find the gate in a run of rail.** The plan is `fixtures/d74-wall-decoration.json`;
the renders are `evidence/d74-decoration-working-zoom.png` (and `-zoomed`).
**Nothing else starts on that surface until he has looked.**

Settable wall types shipped (PR #26) and **Patrick's manual check refuted part of
it.** Two parts, both his judgement:

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

**THEN FURNISHINGS — UNBLOCKED as of 2026‑08‑12** by the Phase 6 park below,
which was the answer [`handoff/0010-ruling.md`](handoff/0010-ruling.md) was
waiting on. **A third of the catalog renders as a box — 28 of 95.** Ruled order:
**(1) the `prism` generator, and it OPENS WITH A MEASUREMENT** · **(2) the
remaining generators by item count** · **(3) parameterisation — a READ-BACK
first** · **(4) AI symbol drafting, last, and AUTHORING TIME ONLY.**

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
| **`main`** | **`cb3e6e6`** — the snapshot gate condition and its red-at-rest fix, on `9bddf21` (the prism read-back), on `be2cb95` (the Phase 6 park, the documentation debt, D74 filed), on `b4d8ea4` (PR #26). PRs #19–#26 all merged. **This branch is cut against `92a8813`**, its own tip, with `main` merged in. |
| **Branches** | **`d74-decoration-channel` — [PR #27](https://github.com/pjm4github/FloorPlanner/pull/27), AMBER, waiting on Patrick's check.** `i15-outline-completeness` was a stale local branch (PR #20, merged, 0 ahead) and was deleted 2026‑08‑12. |
| **Gate** | on this branch (`main` merged in): `collected=711 ruff=clean vacuous=0 end_assign=0 snapshot=current`; OFF / ON / DEEP each **704 passed, 7 deselected**, every sum reconciling; **`Gate-Verdict: GREEN`**. **Zero xfails.** The **7 deselected are the PERF LANE** (standing P3.8 flap-class ruling). |
| **Records** | **75 records**, 30 open. **D74 is new** — the PR #26 follow-up. **D73 closed** with the wall-types work. `python tools/gate.py --docs` GREEN. |
| **Working tree** | see §6 — check `git status --untracked-files=all` before believing a census disagreement. |
| **THE MIGRATION** | **CLOSED 2026‑08‑11** — closing statement with its evidence in [`ROADMAP.md`](ROADMAP.md). Everything after it is features or cleanup. |
| **PHASE 6** | **PARKED 2026‑08‑12, Patrick's ruling** — see §2. |
| **PHASE 5** | **P5.2 (settable wall types) DONE**, merged at PR #26, with D74 outstanding against it. Progress entry at [`progress/phase-5.md`](progress/phase-5.md). **P5.1 and P5.3 not started.** |

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

1. **D74 — the PR #26 follow-up. BUILT, at [PR #27](https://github.com/pjm4github/FloorPlanner/pull/27), AMBER — waiting on the check.** See §0.
2. **Furnishings — BUILD `prism`, THEN RE-MEASURE, THEN DECIDE.** Measured and
   ruled ([`handoff/0012`](handoff/0012-readback-prism-outlines.md) ·
   [`0012-ruling.md`](handoff/0012-ruling.md)); **the build has not started, and
   it is the next code task.** The four furniture generators are **not**
   scheduled work — they are a question to re-ask after prism, against a
   re-measurement. `vehicle` does not wait on it. The three NONE items are
   **authoring**, filed separately.
3. **The command-roster census, derived from the property.** See §0.
4. **A2 — D11's runtime z collapse. ⏸ PARKED, twice over.** The hang is **not
   reproducible** (2026‑08‑09): five orders of magnitude on either z step leaves
   the event breakdown identical at 545, `docs/evidence/d11-a2-z-step-measurement.txt`.
   And it was **DROPPED BEHIND D68** (2026‑08‑11) — the viewer now renders the
   active floor, which makes the z collapse stop mattering for the common case.
   The instrument is kept at `evidence/d11_a2_z_step_counter.py`; **do not
   re-derive it.**
5. **A3 — D11's SERIALIZATION half.** Unblocked by **ruling R‑B**: an *additive
   optional* field or enum value does not bump the document version, so a
   stacking index can be added at `schema_revision` without a v6. AMBER.
6. **D59 — the CHEAP TWELVE at document boundaries.** A real plan was saved
   carrying an `I7`, nothing reported it, and the user met it later as a silent
   crash (D57). P1.2's O(n²)-per-edit cost objection does not touch this half.
   **AMBER, and it moves up on evidence rather than preference.**
7. **A4 — D49, the deep checks at document boundaries. AMENDED 2026‑08‑07 — read
   the amendment, not the proposal it supersedes.** The ruling: **CHECK YES, FIX
   NO**; **SAVE ASKS, IT DOES NOT REFUSE**; the report must be **ACTIONABLE**
   (rooms *and overlap area*, plus select-and-zoom). Acceptance case is `planc1`;
   `farmplace` is the silence case once D52's half 1 lands.
8. **A5 — D41, the new simple-ring invariant.** Ruled at **R‑A**. **A read-back
   is required before starting.**
9. **A6 — Grid snap.** Three sub-rulings still RED.
10. **Phase 5 — the rest:** P5.1 site levels/categories/area accounting, P5.3
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
