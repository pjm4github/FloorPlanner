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
