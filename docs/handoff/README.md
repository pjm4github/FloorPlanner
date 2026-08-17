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

**The diagram: [`channel-commands.svg`](channel-commands.svg)** — the five
phrases (four to an agent, one to your own terminal), the AMBER stop, and both
recovery paths: Code's `checkpoint` before a `/clear` and `resume from NNNN —
and MMMM is up`, Cowork's context-free `where do things stand?` reboot (it
holds nothing that needs recovering, since every decision was written to disk
in the turn it was made).

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

**ONE LINE PER PAIR, per [`0028-ruling.md`](0028-ruling.md) §5** — the number
and a single clause naming the subject. The reasoning is in the file linked;
this table is not a second copy of it.

| pair | subject |
|---|---|
| [`0001`](0001-report.md) · [`0001-ruling.md`](0001-ruling.md) | The docs refactor read-back and its rulings |
| [`0002-report.md`](0002-report.md) | Repo state 2026‑08‑09 — the vertex-accumulation programme |
| [`0003-report.md`](0003-report.md) | D61's three owed items measured; D62 filed |
| [`0004-report.md`](0004-report.md) | The leave path does not weld; 2a's fix partly evaporates on save |
| [`0005-report.md`](0005-report.md) · [`0005-ruling.md`](0005-ruling.md) | Reboot state 2026‑08‑10 — PR #19 unreviewed |
| [`0006-readback-outline-invariants.md`](0006-readback-outline-invariants.md) | Read-back — the two OUTLINE invariants, which corpus files fail each |
| [`0007-readback-phase-6.md`](0007-readback-phase-6.md) | Read-back — Phase 6 does not retire `snapshot()` |
| [`0008-readback-phase-6-deep.md`](0008-readback-phase-6-deep.md) | Read-back — Phase 6 is a CUTOVER, not a retirement; 2b survives |
| [`0009-readback-p6d-cutover.md`](0009-readback-p6d-cutover.md) | Read-back — P6.d's three questions; D67 does not block the cutover |
| [`0010-census-furnishings.md`](0010-census-furnishings.md) · [`0010-ruling.md`](0010-ruling.md) | Census — furnishings; 28 of 95 fall back to a box; D70 filed |
| [`0011-census-wall-types-and-railings.md`](0011-census-wall-types-and-railings.md) | Census — wall types/railings mostly already built; D73 filed |
| [`0012-readback-prism-outlines.md`](0012-readback-prism-outlines.md) · [`0012-ruling.md`](0012-ruling.md) | Read-back — prism outlines; build prism, re-measure, then decide |
| [`0013-report-prism-receipt.md`](0013-report-prism-receipt.md) · [`0013-ruling.md`](0013-ruling.md) | Prism's receipt — 28→1 corrected to 27-of-28; AMBER, backed out and re-applied |
| [`0014-report-furniture-regions.md`](0014-report-furniture-regions.md) · [`0014-ruling.md`](0014-ruling.md) | Report — furniture regions; 17-of-18 outlines are a plain rectangle |
| [`0015-ruling.md`](0015-ruling.md) | Ruling only — `seat`/`bed`/`basin`/`enclosure` retired, `vehicle` not |
| [`0016-ruling.md`](0016-ruling.md) | Ruling only — "chunky boat trailer" withdrawn; `enclosure` conflates vessel and room |
| [`0017-report.md`](0017-report.md) | Report — the SS5 measurement; all three items read WELL |
| [`0018-ruling.md`](0018-ruling.md) | Ruling — 0017's control pointed the wrong way; `enclosure` splits into `vessel`/`enclosure` |
| [`0019-ruling.md`](0019-ruling.md) | Ruling — a generated status board replaces the frozen migration table |
| [`0020-ruling.md`](0020-ruling.md) | Ruling — the coordination protocol, on disk for the first time |
| [`0021-report.md`](0021-report.md) | Report — the vessel/enclosure split, built; D75 filed |
| [`0022-ruling.md`](0022-ruling.md) | Ruling — the control accepted; row 1 not discharged by the mesh numbers alone |
| [`0023-ruling.md`](0023-ruling.md) | Ruling, GREEN — session continuity; the checkpoint/resume protocol recorded |
| [`0024-report.md`](0024-report.md) | Report — 0022's remedies built; D76 and D77 filed |
| [`0025-ruling.md`](0025-ruling.md) | Ruling — the check passes, verbatim; push, open the PR, merge on green CI |
| [`0026-report.md`](0026-report.md) | Report — PR #31 pushed, CI red on a structural finding; D78 filed |
| [`0027-ruling.md`](0027-ruling.md) | Ruling — a self-correction, then D78's remedy (b), adopted and receipted |
| [`0028-ruling.md`](0028-ruling.md) | Ruling, GREEN — trim this file and `SESSION_SNAPSHOT.md` to their stated job |
| [`0029-ruling.md`](0029-ruling.md) | Ruling — the extrudability predicate goes first, GREEN; then the redraws, AMBER |
| [`0030-ruling.md`](0030-ruling.md) | Ruling — the glance test fails today (baseline render); a mark in the render contradicts D76, reconciliation ordered |
| [`0031-ruling.md`](0031-ruling.md) | Ruling, GREEN — the glance fixture placed (`shower-glance-check.json`), a Cowork status view recorded, four untested check fixtures named as a deferred gap |
| [`0032-report.md`](0032-report.md) | Report — predicate built (with a correction to predicate 2), census run (6 more fragmented items found), D76 reconciled (stands, unamended); the redraw brief changes to `beside`-shaped marks, not regions |
| [`0033-report.md`](0033-report.md) | Report — the three redraws built as `beside` shapes, AMBER, PR opens; an honest limit named — the marks are clear up close, subtler at the check's own room-scale camera |
| [`0034-ruling.md`](0034-ruling.md) | Ruling — `0030`'s D76-contradiction claim withdrawn (measurement stands); the check is really two questions (glance test + is the camera working distance), a working-distance camera is owed; the 3% tolerance owes its raw values; one record for the six fragmented items, not six |
| [`0035-ruling.md`](0035-ruling.md) | Ruling — Patrick's own report: cross-floor snapping (a census must test BOTH a missing filter and mis-tagged floor data, since the obvious query paths already filter correctly) and a per-floor totals feature, blocked on open D55 (totals double-count overlaps) — GREEN measurement can start now, neither displaces `0033`'s check or grid snap |
| [`0036-report.md`](0036-report.md) | Report — `0034`'s four action items built: the working-distance camera (both before/after), the 3% tolerance's raw values (nothing between 1% and 3%), D79 filed for the six fragmented items |
