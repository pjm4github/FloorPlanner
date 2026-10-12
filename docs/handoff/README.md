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

<!-- PAIRS:BEGIN -- generated by tools/status_index.py; do not hand-edit -->

| pair | subject |
|---|---|
| [`0000-landings.md`](./0000-landings.md) | landings no report records: every merge before the mailbox, and the green-CI merges after it |
| [`0001-report.md`](./0001-report.md) | report: docs refactor, read-back |
| [`0001-ruling.md`](./0001-ruling.md) | ruling: docs refactor |
| [`0002-report.md`](./0002-report.md) | report: repository state at 2026‑08‑09, for a fresh session |
| [`0003-report.md`](./0003-report.md) | report: D61's three owed items, measured |
| [`0004-report.md`](./0004-report.md) | report: the four ordered measurements, and what they decide |
| [`0005-report.md`](./0005-report.md) | report: reboot state, 2026‑08‑10 |
| [`0005-ruling.md`](./0005-ruling.md) | ruling: the plan-file placement conflict |
| [`0006-readback-outline-invariants.md`](./0006-readback-outline-invariants.md) | read-back: the two outline invariants |
| [`0007-readback-phase-6.md`](./0007-readback-phase-6.md) | read-back: Phase 6, command undo |
| [`0008-readback-phase-6-deep.md`](./0008-readback-phase-6-deep.md) | read-back: Phase 6, the four questions |
| [`0009-readback-p6d-cutover.md`](./0009-readback-p6d-cutover.md) | read-back: P6.d, the cutover |
| [`0010-census-furnishings.md`](./0010-census-furnishings.md) | census: furnishings |
| [`0010-ruling.md`](./0010-ruling.md) | ruling: furnishings |
| [`0011-census-wall-types-and-railings.md`](./0011-census-wall-types-and-railings.md) | census: settable wall types and porch railings |
| [`0012-readback-prism-outlines.md`](./0012-readback-prism-outlines.md) | read-back: how many fallback symbols have an outline `prism` can use? |
| [`0012-ruling.md`](./0012-ruling.md) | ruling: prism order, and two rules the read-back earned |
| [`0013-report-prism-receipt.md`](./0013-report-prism-receipt.md) | report: prism is built, and here is its receipt |
| [`0013-ruling.md`](./0013-ruling.md) | ruling: prism's tier, and the two small calls |
| [`0014-report-furniture-regions.md`](./0014-report-furniture-regions.md) | report: the furniture half, and the one fact the decision turns on |
| [`0014-ruling.md`](./0014-ruling.md) | ruling: build the region extrusion; the three seats are artwork |
| [`0015-ruling.md`](./0015-ruling.md) | ruling: the four furniture generators are RETIRED |
| [`0016-ruling.md`](./0016-ruling.md) | ruling: the enclosure check, and three boxes wearing three names |
| [`0017-report.md`](./0017-report.md) | report: the owed measurement from 0016 §5 |
| [`0018-ruling.md`](./0018-ruling.md) | ruling: the form splits, and 0017's control was pointed the wrong way |
| [`0019-ruling.md`](./0019-ruling.md) | ruling: the status table is generated, or it lies |
| [`0020-ruling.md`](./0020-ruling.md) | ruling: the three things Patrick ever says |
| [`0021-report.md`](./0021-report.md) | report: the vessel/enclosure split, built — and one thing the render cannot show |
| [`0022-ruling.md`](./0022-ruling.md) | ruling: the control is accepted, and row 1 is not discharged by a number |
| [`0023-ruling.md`](./0023-ruling.md) | ruling: session continuity, and the reviewer's checkpoint is a QUESTION |
| [`0024-report.md`](./0024-report.md) | report: 0022's four remedies, built |
| [`0025-ruling.md`](./0025-ruling.md) | ruling: the check PASSES, the merge needs a PR, and what follows |
| [`0026-report.md`](./0026-report.md) | report: pushed, PR #31 open, CI is red — and it is a finding, not a re-run |
| [`0027-ruling.md`](./0027-ruling.md) | ruling: my own §2 was never measured, and D78's remedy |
| [`0028-ruling.md`](./0028-ruling.md) | ruling: do NOT fragment the snapshot. Enforce its own contract instead. |
| [`0029-ruling.md`](./0029-ruling.md) | ruling: the next tranche — the predicate FIRST, and it re-decides the redraw list |
| [`0030-ruling.md`](./0030-ruling.md) | ruling: the glance test FAILS today, and one thing in the render contradicts D76 |
| [`0031-ruling.md`](./0031-ruling.md) | ruling: the glance fixture is placed, and one gap named for later |
| [`0032-report.md`](./0032-report.md) | report: the predicate built, the census run, D76 reconciled — the redraw brief changes |
| [`0033-report.md`](./0033-report.md) | report: the three redraws, built — AMBER, and one honest limit |
| [`0034-ruling.md`](./0034-ruling.md) | ruling: the check is ready, the camera is the open question, and I withdraw 0030 §4 |
| [`0035-ruling.md`](./0035-ruling.md) | ruling: cross-floor snapping, and per-floor totals that must not inherit D55 |
| [`0036-report.md`](./0036-report.md) | report: 0034's four action items, built |
| [`0036-ruling.md`](./0036-ruling.md) | ruling: two faults in one sentence, and the one test that separates them |
| [`0037-ruling.md`](./0037-ruling.md) | ruling: a hidden floor that paints is a measurement, and it names a suspect |
| [`0038-report.md`](./0038-report.md) | report: §2's diagnosis does not hold — `_sync_floor_state()` already runs on load |
| [`0038-ruling.md`](./0038-ruling.md) | ruling: the DXF export is ACCEPTED, and its thickness table is D73 arriving again |
| [`0039-report.md`](./0039-report.md) | report: `fp2dxf` is not in this repository — blocked before it can start |
| [`0040-ruling.md`](./0040-ruling.md) | ruling: the package is placed, my 0037 suspect was wrong, and the numbering convention is retired |
| [`0041-ruling.md`](./0041-ruling.md) | ruling: the recovery, and what actually survived |
| [`0042-ruling.md`](./0042-ruling.md) | ruling: the CI is not overkill; ONE check in it is in the wrong lane |
| [`0043-report.md`](./0043-report.md) | report: recovery closed out, measured against 0041 §3 and 0038's owed list |
| [`0043-ruling.md`](./0043-ruling.md) | ruling: the gate is not too rigorous; the BAR IS ON THE WRONG EVENT |
| [`0044-ruling.md`](./0044-ruling.md) | ruling: 0040 §4 was half right, and the order of work |
| [`0045-ruling.md`](./0045-ruling.md) | ruling: the check was run against the wrong tree, and a check request must name its BRANCH |
| [`0046-report.md`](./0046-report.md) | report: 0044 §3 items 2 and 3 done; items 1/4/5 held for Patrick's say-so |
| [`0047-ruling.md`](./0047-ruling.md) | ruling: all three authorised, and the hook split needs FOUR controls, not one |
| [`0048-report.md`](./0048-report.md) | report: `Docs-Snapshot` out of the `pull_request` lane, item 4 done |
| [`0049-report.md`](./0049-report.md) | report: the commit hook split, four controls, item 5 done |
| [`0050-report.md`](./0050-report.md) | report: `fp2dxf` integration built end to end, PR #33 open, AMBER |
| [`0050-ruling.md`](./0050-ruling.md) | ruling: the redraw check PASSES; the branch is 9 behind and must not merge as-is |
| [`0051-ruling.md`](./0051-ruling.md) | ruling: the worktree agent is the right call, and it will reproduce two problems we fixed today |
| [`0052-ruling.md`](./0052-ruling.md) | ruling: the export README lands at `docs/guides/`, the first user-facing doc in this project |
| [`0053-ruling.md`](./0053-ruling.md) | ruling: what the git widget is showing, and the order to clear it |
| [`0054-report.md`](./0054-report.md) | report: Patrick's Chief Architect check passed, PR #33 merging |
| [`0055-ruling.md`](./0055-ruling.md) | ruling: grid snap will NOT fix the off-axis walls, and the measurement says why |
| [`0056-report.md`](./0056-report.md) | report: the orthogonality report (item B), built — item C untouched |
| [`0057-ruling.md`](./0057-ruling.md) | ruling: the instrument is accepted; its READING has not been reported |
| [`0058-report.md`](./0058-report.md) | report: the census, run — and the guide line, added |
| [`0059-ruling.md`](./0059-ruling.md) | ruling: the census stands, its bottom band hides the number item C needs |
| [`0060-report.md`](./0060-report.md) | report: the band split, re-run; and 0037 §3's census, folded in |
| [`0061-ruling.md`](./0061-ruling.md) | ruling: `_align_to_wall` is the cross-floor snap, and it is NOT masked |
| [`0062-report.md`](./0062-report.md) | report: `_align_to_wall`'s cross-floor snap, fixed — AMBER, PR open |
| [`0063-ruling.md`](./0063-ruling.md) | ruling: the fix is right, the receipt for it is not in the suite |
| [`0064-report.md`](./0064-report.md) | report: `0063`'s three GREEN items done; two out-of-band features landed |
| [`0065-ruling.md`](./0065-ruling.md) | ruling: the label that exists to show drift rounds the drift away |
| [`0066-ruling.md`](./0066-ruling.md) | ruling: item C, the orthogonality repair — bounded by DISPLACEMENT, not by angle |
| [`0067-report.md`](./0067-report.md) | report: `0065`'s items done; PR #35 open, batched with #34 |
| [`0068-ruling.md`](./0068-ruling.md) | ruling: the fix is sound; its receipt passes against the unfixed code |
| [`0069-report.md`](./0069-report.md) | report: `0068`'s GREEN items done; PR #35 carries a real receipt now |
| [`0070-ruling.md`](./0070-ruling.md) | ruling: the code snaps the MOVE, not the DESTINATION — Patrick's off-grid walls |
| [`0071-report.md`](./0071-report.md) | report: D80 bisected, root-caused, fixed — PR #36 open, batched |
| [`0072-ruling.md`](./0072-ruling.md) | ruling: the export menu, and `fp2pdf.py` arrives with four faults `fp2dxf.py` was fixed for five days ago |
| [`0073-ruling.md`](./0073-ruling.md) | ruling: settings precedence for `fp2pdf` — and there is no settings FILE to add them to |
| [`0074-ruling.md`](./0074-ruling.md) | ruling: the settings file already exists — and `0073` §1 was wrong to say it did not |
| [`0075-ruling.md`](./0075-ruling.md) | ruling: JSON, not `configparser` — and `configparser` would have kept the bug |
| [`0076-report.md`](./0076-report.md) | report: every GREEN-tier settings/`fp2pdf` item built |
| [`0077-ruling.md`](./0077-ruling.md) | ruling: accepted — and the type-safe coercer is not type-safe for the input it was built for |
| [`0078-ruling.md`](./0078-ruling.md) | ruling: materialise the settings — and the `version` key now has to do real work |
| [`0079-report.md`](./0079-report.md) | report: `0066` item 1 built; the read-back for item 2 |
| [`0080-report.md`](./0080-report.md) | report: every GREEN item across `0077`/`0078` built |
| [`0081-report.md`](./0081-report.md) | report: current state, consolidated — three AMBER PRs, item C's read-back, every GREEN settings/`fp2pdf` item |
| [`0082-ruling.md`](./0082-ruling.md) | ruling: the read-back is accepted with three amendments, and two of them make the repair run at all |
| [`0083-report.md`](./0083-report.md) | report: item C (the orthogonality repair) built, gated GREEN, and two findings neither ruling anticipated |
| [`0084-ruling.md`](./0084-ruling.md) | ruling: `T` was dropped, and the interlock guards the wrong quantity |
| [`0085-ruling.md`](./0085-ruling.md) | ruling: shorter exchanges, and `CLAUDE.md` down to the traps |
| [`0086-ruling.md`](./0086-ruling.md) | ruling: prepare the check session — Patrick checks out branches in the main tree |
| [`0087-report.md`](./0087-report.md) | report: the ready report — three branches current, gated, waiting on Patrick |
| [`0088-ruling.md`](./0088-ruling.md) | ruling: PR #36's check PASSED — D80 closes, merge authorised |
| [`0089-ruling.md`](./0089-ruling.md) | ruling: PR #34's check PASSED — and the grid symptom beside it is expected, measured |
| [`0090-ruling.md`](./0090-ruling.md) | ruling: PR #35 PASSED — all three merge, and the AMBER queue is empty |
| [`0091-ruling.md`](./0091-ruling.md) | ruling: the status-bar label is confirmed in Patrick's own words |
| [`0092-ruling.md`](./0092-ruling.md) | ruling: the angle clause shows both — heading and deviation |
| [`0093-ruling.md`](./0093-ruling.md) | ruling: off-axis is measured from the nearest INTENDED angle, not the nearest cardinal |
| [`0094-ruling.md`](./0094-ruling.md) | ruling: walls DO have an angle snap — and it breaks [`0093`](0093-ruling.md)'s exactness test |
| [`0095-report.md`](./0095-report.md) | report: `0084-ruling.md` §6 items 1–3 built — `T` restored, the post-condition added, the census re-run |
| [`0096-report.md`](./0096-report.md) | report: the status-bar angle clause built — `0092`/`0093`/`0094` |
| [`0097-report.md`](./0097-report.md) | report: `CLAUDE.md` trimmed to traps only — `0085-ruling.md` |
| [`0098-ruling.md`](./0098-ruling.md) | ruling: the report names walls the user cannot find — two id namespaces, one label shape |
| [`0099-ruling.md`](./0099-ruling.md) | ruling: the session id is not reproducible, and the check was aimed at a plan with nothing to repair |
| [`0100-ruling.md`](./0100-ruling.md) | ruling: one visible wall number, and click-a-row-to-find-it |
| [`0101-report.md`](./0101-report.md) | report: the read-back for `0100-ruling.md` §5 — no code built |
| [`0101-ruling.md`](./0101-ruling.md) | ruling: the map is not built, it is discarded — and the seam already exists |
| [`0102-report.md`](./0102-report.md) | report: `0100-ruling.md` §1 built — the report names walls Patrick can find |
| [`0103-ruling.md`](./0103-ruling.md) | ruling: the read-back answered, and [`0100`](0100-ruling.md) §2 was wrong about the gaps dialog |
| [`0104-ruling.md`](./0104-ruling.md) | ruling: the fast lane already exists and is already running; the 3× is the real cost |
| [`0105-ruling.md`](./0105-ruling.md) | ruling: both reasons for cutting CI are false — and there is a better reason that survives |
| [`0106-report.md`](./0106-report.md) | report: the ON/DEEP-vs-OFF measurement `0104` ordered, and `0105`'s CI cuts built |
| [`0107-ruling.md`](./0107-ruling.md) | ruling: I cut a check that was working, on a claim I did not verify |
| [`0108-ruling.md`](./0108-ruling.md) | ruling: "Snap wall to grid" — a per-wall manual action, and it is NOT the orthogonality repair |
| [`0109-ruling.md`](./0109-ruling.md) | ruling: the walkthrough confirms the arithmetic and CHANGES one of [`0108`](0108-ruling.md)'s refusals |
| [`0110-ruling.md`](./0110-ruling.md) | ruling: "Snap to Grid Orthogonal" — and it corrects a hazard in the plain version |
| [`0111-ruling.md`](./0111-ruling.md) | ruling: closing out the open PRs — three, not two, and one check session |
| [`0112-ruling.md`](./0112-ruling.md) | ruling: gitignore `plans.pdf` — and [`0111`](0111-ruling.md) §2's second half is withdrawn |
| [`0113-report.md`](./0113-report.md) | report: `0111`/`0112`'s close-out, then `0108`-`0110`'s three snap-to-grid features — all four PRs checked and merged |
| [`0114-ruling.md`](./0114-ruling.md) | ruling: accepted — and "nothing is currently owed" is wrong by one receipt |
| [`0115-ruling.md`](./0115-ruling.md) | ruling: the check quotes are confirmed; the four merges are final |
| [`0116-ruling.md`](./0116-ruling.md) | ruling: the Export menu — [`0072`](0072-ruling.md) §4–§5 unblocked, with every prerequisite now measured DONE |
| [`0117-report.md`](./0117-report.md) | report: [`0116`](0116-ruling.md)'s manual check came back — menu passes, two PDF-content defects filed, PR #42 merges as-is |
| [`0118-ruling.md`](./0118-ruling.md) | ruling: the PDF tranche — the dimension mess is `round(p, 3)`, and stations are the fix for both D82 and the pile-up |
| [`0119-ruling.md`](./0119-ruling.md) | ruling: aligned dimensions for angled walls — tranche 2, on tranche 1's machinery |
| [`0120-ruling.md`](./0120-ruling.md) | ruling: Patrick's room-driven scheme replaces [`0119`](0119-ruling.md) §2's wall classifier — and it is measured to be document-backed |
| [`0121-report.md`](./0121-report.md) | report: [`0118`](0118-ruling.md) built — station clustering, telescoping |
| [`0122-report.md`](./0122-report.md) | report: [PR #43](https://github.com/pjm4github/FloorPlanner/pull/43) merged — D81/D82 closed; the 45° labeling gap confirmed as [`0119`](0119-ruling.md)/[`0120`](0120-ruling.md)'s own scope, next as its own effort |
| [`0123-ruling.md`](./0123-ruling.md) | ruling: `0121`/`0122` accepted clean — tranche 2 is authorised to start |
| [`0124-report.md`](./0124-report.md) | report: tranche 2 starting — [`dim_row_along`](0119-ruling.md) refactor first (own branch, GREEN), the angled lane (`0120-ruling.md`) after, on top of it |
| [`0125-report.md`](./0125-report.md) | report: [`0120`](0120-ruling.md)'s angled dimension lane built, AMBER, PR pending on `angled-dimension-lanes` |
| [`0126-report.md`](./0126-report.md) | report: [`0127`](0127-ruling.md)/[`0128`](0128-ruling.md)'s three check findings fixed on `angled-dimension-lanes`, plus the global opening-station drop and footer note |
| [`0127-ruling.md`](./0127-ruling.md) | ruling: Patrick's three check findings on the 45° lanes — [`0120`](0120-ruling.md) amended, one receipt reversed |
| [`0128-ruling.md`](./0128-ruling.md) | ruling: opening stations leave EVERY dimension row — and the intent behind it is now on the record |
| [`0129-ruling.md`](./0129-ruling.md) | ruling: PR #45 passes and merges; the four branches are one live and three ghosts; the cleanup tranche specified |
| [`0130-ruling.md`](./0130-ruling.md) | ruling: family exclusivity — each lane dimensions only its own walls |
| [`0131-ruling.md`](./0131-ruling.md) | ruling: `R2f` screenshot read — every visible defect maps to an item already in flight; nothing new is ordered |
| [`0132-ruling.md`](./0132-ruling.md) | ruling: `R2` pair adopted as the tranche's "before" baseline; the re-check re-points at it |
| [`0133-report.md`](./0133-report.md) | report: [PR #45](https://github.com/pjm4github/FloorPlanner/pull/45) merged, three ghost branches deleted; the cleanup tranche (0129/0130/0132) starting next |
| [`0134-report.md`](./0134-report.md) | report: the cleanup tranche built — [`0129`](0129-ruling.md) §3(a)-(c) and [`0130`](0130-ruling.md)'s family exclusivity, on `dimension-cleanup-tranche` |
| [`0135-ruling.md`](./0135-ruling.md) | ruling: door symbols by type, windows made real — the Chief import tranche |
| [`0136-report.md`](./0136-report.md) | report: [`0135`](0135-ruling.md)'s DXF door-symbol-by-type + real windows built — and the golden fixture itself carried the defect |
| [`0137-ruling.md`](./0137-ruling.md) | ruling: the DXF check passes in his words; PR #47 merged clean — and item C's number is one sentence away |
| [`0138-report.md`](./0138-report.md) | report: item C closed — zero walls flagged, [`0066`](0066-ruling.md)'s count received |
| [`0139-ruling.md`](./0139-ruling.md) | ruling: the roofline plan — five gated tranches, one buildable at a time |
| [`0140-ruling.md`](./0140-ruling.md) | ruling: the End‑On dialog IS the drawing — R2b spec sharpened by Patrick's sketch |
| [`0141-report.md`](./0141-report.md) | report: a second numbering collision recovered; R1 built |
| [`0142-report.md`](./0142-report.md) | report: R2 — roof menu, ridge sketch, eaves pick, minimal heights dialog |
| [`0143-report.md`](./0143-report.md) | report: R2 closed — Patrick's own check passed, PR #49 merged |
| [`0144-report.md`](./0144-report.md) | report: R2b — the End-On marker, its dialog, the three-way recompute |
| [`0145-ruling.md`](./0145-ruling.md) | ruling: roof visibility/editability ruled as R2c; clip display as R3b; the macro notes on the record |
| [`0146-ruling.md`](./0146-ruling.md) | ruling: R2b's check passes — PR #50 merges |
| [`0147-report.md`](./0147-report.md) | report: R2b merged, D84 reclassified, R2c starting |
| [`0148-report.md`](./0148-report.md) | report: R2c — Show roof / Edit roof |
| [`0149-report.md`](./0149-report.md) | report: R2c closed — the disappearing-roof bug found and fixed, PR #51 merged |
| [`0150-report.md`](./0150-report.md) | report: R3 — roof planes + gable ends in `fp3d.build_model` |
| [`0151-report.md`](./0151-report.md) | report: R3 closed — his own check passed, PR #52 merged |
| [`0152-report.md`](./0152-report.md) | report: R3b — the roof-clip dotted line |
| [`0153-report.md`](./0153-report.md) | report: R3b closed — the crash investigated, D85 found and fixed, PR #53 merged |
| [`0154-ruling.md`](./0154-ruling.md) | ruling: R4 re-planned around Patrick's five requirements — the footprint enters the schema |
| [`0155-report.md`](./0155-report.md) | report: R4a — the roof footprint enters the schema |
| [`0156-report.md`](./0156-report.md) | report: R4a closed — PR #54 merged on green CI |
| [`0157-report.md`](./0157-report.md) | report: R4b — the roof parameters dialog: overhang, hip ends, eaves bound to the room top |
| [`0158-report.md`](./0158-report.md) | report: R4b's check found three things — per-side eaves pick, editable spans, and the span measured to the ridge LINE |
| [`0159-report.md`](./0159-report.md) | report: R4b's re-check passed; the selection outline now hugs the roof |
| [`0160-ruling.md`](./0160-ruling.md) | ruling: 0158/0159 verified — R4b hangs on one look, the outline |
| [`0161-report.md`](./0161-report.md) | report: R4b closed — PR #55 merged on Patrick's word |
| [`0162-report.md`](./0162-report.md) | report: R4c — five grips on a selected roof |
| [`0163-report.md`](./0163-report.md) | report: R4c closed — PR #56 merged on Patrick's word |
| [`0164-ruling.md`](./0164-ruling.md) | ruling: roof intersection clipping — the valley item comes due as R4d |
| [`0165-report.md`](./0165-report.md) | report: R4d — roof intersection clipping, the valley seam |
| [`0166-report.md`](./0166-report.md) | report: R4d's check — a joining roof stops at the seam, whichever surface is higher |
| [`0167-report.md`](./0167-report.md) | report: R4d closed — PR #57 merged on Patrick's word; mesh clipping ordered as R4e |
| [`0168-report.md`](./0168-report.md) | report: R4e — mesh clipping: the 3D roofs are built from the plan's own clip |
| [`0169-report.md`](./0169-report.md) | report: R4e closed — PR #58 merged on Patrick's word; one item named for later |
| [`0170-ruling.md`](./0170-ruling.md) | ruling: the three-ridge case arrives — the clip becomes the upper envelope, computed globally |
| [`0171-report.md`](./0171-report.md) | report: R4f built — the three-ridge clip, a seam real only where no third roof is higher |
| [`0172-report.md`](./0172-report.md) | report: R4f's own check — a real hole in 3D, fixed on the branch |
| [`0173-report.md`](./0173-report.md) | report: R4f's second check — a stray fin, traced to two artifacts, both fixed |
| [`0174-report.md`](./0174-report.md) | report: R4f rebuilt from a single global arrangement, per the researched standard technique |
| [`0175-report.md`](./0175-report.md) | report: R4f, his fourth check — a real hole, closed with a cross-roof riser |
| [`0176-ruling.md`](./0176-ruling.md) | ruling: the notch is the `_strip` residual, not a mystery — candidacy becomes the footprint, and phantom boundaries become illegal |
| [`0177-ruling.md`](./0177-ruling.md) | ruling: Patrick's correction adopted — a point is not a connection, and the anchor is the roof's own ground |
| [`0178-report.md`](./0178-report.md) | report: R4g built — candidacy becomes the footprint, reachability anchors at single-coverage ground, a real fallback bug found and fixed; two of the ruling's own receipts not fully met, honestly measured |
| [`0179-ruling.md`](./0179-ruling.md) | ruling: 0178's fallback-bug fix stands; the 27% blank does not — prune-and-re-envelope is the criterion the pass was missing |
| [`0180-report.md`](./0180-report.md) | report: prune-and-re-envelope built; a real reach bug found closing it; gap cut from 27% to 15%, not to 0 — the remaining cause is diagnosed, not guessed at |
| [`0181-ruling.md`](./0181-ruling.md) | ruling: the criterion §4 asked for — a roof passes UNDER, it never passes ABOVE |
| [`0182-report.md`](./0182-report.md) | report: the under-pass network built; the partition is whole — 0% blank on the three-ridge fixture, D85's corner the L's one legal blank; two facts the rule needed that the ruling did not name, each measured |
| [`0183-report.md`](./0183-report.md) | report: his check of 0182 — the 3D view passed, the plan was missing a joint; seams are now read off the final pieces |
| [`0184-report.md`](./0184-report.md) | report: his second fixture — a ridge cut short over another roof needs a gable end, not an extension; built, the pinch unchanged |
| [`0185-report.md`](./0185-report.md) | report: R4g closed and merged on his word; where the roofline plan stands for the next session |
| [`0186-ruling.md`](./0186-ruling.md) | ruling: R4g ratified closed; the next arc — clip trace on the roof, dormers, multifloor |
| [`0187-report.md`](./0187-report.md) | report: R5a — the clip trace on the roof, built; AMBER, stopped for his check |
| [`0188-report.md`](./0188-report.md) | report: R5a merged on his word; the 3D wall clip, built; AMBER, stopped for his look |
| [`0189-report.md`](./0189-report.md) | report: his first look at the 3D wall clip — one thing, fixed on the branch; stopped for his second |
| [`0190-report.md`](./0190-report.md) | report: R5b dormers — the design read-back ([`0186`](0186-ruling.md) §3), no code |
| [`0191-ruling.md`](./0191-ruling.md) | ruling: the dormer read-back is adopted nearly whole — one gesture correction, and the build is ordered |
| [`0192-report.md`](./0192-report.md) | report: R5b dormers — built as ruled; AMBER, stopped for his check |
| [`0193-report.md`](./0193-report.md) | report: R5b merged on his word; the undo (already there, and 0192 corrected) and the macro's DORMER token; AMBER, stopped for his check |
| [`0194-report.md`](./0194-report.md) | report: his look at the merged dormer — the back-end grip returns, the dormer's own walls go; fixed on PR #64's branch, stopped for his check |
| [`0195-ruling.md`](./0195-ruling.md) | ruling: 0194 adopted on measurement, with one overclaim corrected — the dormer's back-end grip is not the inverse of the derivation, and one demand before R6 |
| [`0196-report.md`](./0196-report.md) | report: PR #64 merged on his word (the record 0194 owed); 0195's clamp built and its closure demand answered; AMBER, stopped for his check |
| [`0197-ruling.md`](./0197-ruling.md) | ruling: R6 opens, and D50 is its gate — no multifloor plan in the corpus has a roof, and every level in every one says elevation 0.0 |
| [`0198-report.md`](./0198-report.md) | report: PR #65 merged on his word (the record 0197 §7 owed); R6.0 — D50 measured, closed, and its receipt across all five multifloor plans; AMBER, stopped for his check |
| [`0199-report.md`](./0199-report.md) | report: PR #66 merged on his word; his R6 fixture, promoted; R6.a built — the plan view's multifloor roof rule and the whole-building 3D default; AMBER, stopped for his check |
| [`0200-report.md`](./0200-report.md) | report: PR #67 merged on his word; R6.b — the building's one roofscape, composed in absolute height; its cost measured and fixed; AMBER, stopped for his check |
| [`0201-report.md`](./0201-report.md) | report: PR #68 merged on his word; D67 REPRODUCED (a fourth site, undo complete); the roof paths and the level's elevation, measured on his fixture — measurements only, nothing fixed |
| [`0202-report.md`](./0202-report.md) | report: R6.c — the roof tool across levels; measured on his fixture, three faults found and fixed; AMBER, stopped for his check |
| [`0203-report.md`](./0203-report.md) | report: `SESSION_SNAPSHOT.md` trimmed on his word, 67,936 → 40,657 characters; uncommitted work found on the R6.c branch and left alone; one file in `incoming/` |
| [`0204-report.md`](./0204-report.md) | report: `SESSION_SNAPSHOT.md`'s QUEUE trimmed on his word, 17,976 → 5,131 characters; the file is now 27,882, down from 67,936 this morning |
| [`0205-report.md`](./0205-report.md) | report: the open list brought to his word of 2026‑10‑03 — PR #69 did not crash; grid snap by default goes first, angled walls excepted; the incoming plan is a test design, not a defect |
| [`0206-report.md`](./0206-report.md) | report: PR #69 merged on his word — R6.c is closed; the check fixture kept with its row corrected |
| [`0207-report.md`](./0207-report.md) | READ-BACK: grid snap by default (A6) — what snaps today, clause by clause; four decisions before the build |
| [`0208-report.md`](./0208-report.md) | report: grid snap by default (A6) built on his four answers; three things the build had to decide beyond them; AMBER, stopped for his check |
| [`0209-report.md`](./0209-report.md) | report: PR #70 merged on his word — grid snap by default is closed |
| [`0210-report.md`](./0210-report.md) | report: the 3‑inch reach — his report against grid snap reproduced, 0208 §2(a)'s 9″ rule withdrawn, two more over-reaches found by the check plan; AMBER, stopped for his check |
| [`0211-report.md`](./0211-report.md) | report: PR #71 merged on his word — the 3‑inch reach is closed, and grid snap by default with it |
| [`0212-report.md`](./0212-report.md) | READ-BACK: macro language v2 — the existing macro feature surveyed, ten conflicts with the v2 grammar, his three answers, and the plan in three tranches |
| [`0213-report.md`](./0213-report.md) | report: macro language v2, T1 — the language is built, no Qt delivery; ANTLR 4.11.1 stands (my doubt about it was wrong); his question on carrying v1's features into v2, answered as a proposal |
| [`0214-report.md`](./0214-report.md) | report: PR #72 merged (GREEN, on green CI); macro language v2, T2 — the player; the modifier leak measured exactly and guarded; AMBER, stopped for his check |
| [`0215-report.md`](./0215-report.md) | report: application commands, `@NAME arg …` — v1's high-level commands carried into v2 on his word; his grammar and spec extended; built stacked on the player, no PR until #73 merges; his question on the check macro's step 3 |
| [`0216-report.md`](./0216-report.md) | report: the v2 recorder, built on his report that Shift is not captured; the commands check ran on his screen; three branches stacked, one PR open |
| [`0217-report.md`](./0217-report.md) | report: PR #73 merged on his word, three tranches folded into it — macro language v2 runs, takes application commands and is recorded |
| [`0218-report.md`](./0218-report.md) | report: the legacy converter and the v2 docs built, with two things he asked for mid-session — replay takes whole lines top down, and the recorder window numbers its lines |
| [`0219-report.md`](./0219-report.md) | report: PR #74 merged on his word — the legacy converter, the v2 docs, whole-line replay and the recorder window's line numbers; the macro spec's six tasks are done |
| [`0220-report.md`](./0220-report.md) | report: the error indicator in the recorder window's gutter, built on his word; both languages mark the failing line |
| [`0221-report.md`](./0221-report.md) | report: his ruling on a v2 error — the lines before it run, it stops there, the error stays on show; §8.3 of his spec amended; folded into PR #75 |
| [`0222-report.md`](./0222-report.md) | report: PR #75 merged on his word, after his check — the error indicator in the recorder window's gutter, and the stop-at-the-error rule |
| [`0223-report.md`](./0223-report.md) | report: the D67 pair fixed on `d67-floor-scope`, one predicate each; his gable-end plan promoted as the check fixture; the gable-end tranche read back before it is built |
| [`0224-report.md`](./0224-report.md) | report: the gable-end tranche built on `gable-end-walls`, stacked on `d67-floor-scope`; the read-back of 0223 §3 answered by his own words, not by him |
| [`0225-report.md`](./0225-report.md) | report: PR #76 merged on his word with the gable-end tranche folded in — the D67 pair and the open gable ends; D67 CLOSED |
| [`0226-report.md`](./0226-report.md) | report: the four-way crossing fault — NOT REPRODUCED in 96 runs across seven configurations and two commits, one of them the commit 0208 measured on; no defect filed; the instrument kept |
| [`0227-report.md`](./0227-report.md) | report: the four-way crossing fault CLOSED as not reproduced, no defect, on his word |
| [`0228-report.md`](./0228-report.md) | report: two parallel walls one grid step apart stay two walls — a gesture merges at A6's 3″, built on `parallel-walls-6in` for his check |
| [`0229-report.md`](./0229-report.md) | report: the "Malformed design file" report takes you there — a list of every violation, each one zooming the view to the place it names; built on `design-problems`, stacked on `parallel-walls-6in` |
| [`0230-report.md`](./0230-report.md) | report: the wall-properties dialog — double-click a wall, edit its name, type and end points corner by corner; names are document fields; built on `wall-properties`, stacked on `design-problems` |
| [`0231-report.md`](./0231-report.md) | report: PR #77 merged on his word with three tranches folded in — the parallel-walls merge rule, the violations report that zooms to each problem, the wall-properties dialog |
| [`0232-report.md`](./0232-report.md) | READ-BACK: the status board — what the record can and cannot say about a completed unit today, measured; the four answers 0019 §4 asked for; a recommendation, nothing built |
| [`0233-report.md`](./0233-report.md) | report: the status board built — `docs/STATUS.md` generated from one `**Landed:**` line per merge, gate-checked; 77 PRs on the board from #1; the migration table frozen; the pair table generated; the mailbox is the record |
| [`0234-report.md`](./0234-report.md) | report: PR #78 merged on green CI — the status board is on `main`, and this is the first landing recorded by its own line |
| [`0235-report.md`](./0235-report.md) | report: the PDF (and DXF) exporters refused every plan with a roof — a version‑6 document read as "not v5"; fixed on `pdf-v6`, D87 filed and closed with it |
| [`0236-report.md`](./0236-report.md) | report: PR #79 merged on green CI — the PDF and DXF exporters accept a plan with a roof; D87 closed |
| [`0237-report.md`](./0237-report.md) | report: his `short-angle-roof.json` — a joined end's extension given ground in every roof's footprint, drawn across roofs it never reached; fixed on `roof-joined-domain`, D88; and what the lock-up measurement found before he redirected it |
| [`0238-report.md`](./0238-report.md) | report: PR #80 merged on his word — the joined end's extension grounded in its hosts' footprints; D88 closed; his next rule, the gable end that projects UP, read back before anything is built |
| [`0239-report.md`](./0239-report.md) | READ-BACK: the gable end that projects UP — what his design shows at the west junction, the mechanism, and the rule as I read it; nothing built |
| [`0240-report.md`](./0240-report.md) | report: his word on 0239 — "the wall loop test is right", the build ordered; the state saved for a fresh session |
| [`0241-report.md`](./0241-report.md) | report: the lower roof runs under the overhang — 0240 §1 built on `roof-overhang-build`, AMBER; measured on his design and on every roof fixture, including two the order expected unchanged and the rule reaches |
| [`0242-report.md`](./0242-report.md) | report: his 3D view of the gable ends — the brown wrap is the cross-roof riser on the higher roof's gable-end line; gone, on `roof-overhang-build` with 0241's build, PR #81; his `short-angle-roofR2.json` (a dormer added) promoted |
| [`0243-report.md`](./0243-report.md) | report: his second 3D look — the dormer's cheek spill and the step under the overhang; no riser on any edge of the higher roof, and the hidden strip is its roof's territory for the wall cap; PR #81 updated, one commit |
| [`0244-report.md`](./0244-report.md) | report: the dormer's sides, projected up to the dormer — generated cheeks standing on the host roof; PR #81 updated, one commit |
| [`0245-report.md`](./0245-report.md) | report: the set-back dormer's face climbs from the roof itself — `_dormer_face`; his `short-angle-roofR3.json` promoted; PR #81 updated, one commit |
| [`0246-report.md`](./0246-report.md) | report: PR #81 merged on his word — the lower roof under the overhang, nothing of roof hanging from a roof's edge, the dormer's sides and face projected up from the roof; the roof-wrap bug closed |
| [`0247-report.md`](./0247-report.md) | report: his word on 0241 §2 — the overhang rule stays as it is on the three-ridge and two-level fixtures; nothing built |
| [`0248-report.md`](./0248-report.md) | report: his house picture built as a design — `fixtures/incoming/house_cutout.json`, four iterations with renders; where the roof and dormer tools fell short, and the plan proposed |
| [`0249-report.md`](./0249-report.md) | report: 0248's plans A and C built on `roof-shed-form` — the `shed` roof form, and a dormer's generated side or face yielding to a house wall; the house model regenerated with both; AMBER, for his check |
| [`0250-report.md`](./0250-report.md) | report: the house regenerated from the first-floor plan (iteration 6); a shed's ends are never joined — found on it, fixed on `roof-shed-form`; PR #82 updated, one commit |
| [`0251-report.md`](./0251-report.md) | report: PR #82 merged on his word — the `shed` roof form, a shed's ends never joined, a dormer's generated side or face yielding to a house wall; 0248's plans A and C closed |
| [`0252-report.md`](./0252-report.md) | report: 0248's plans B and D built on `roof-openings-ridge-meet` — openings on a dormer record, cut into its generated face; the equal-height ridge meeting in the clip; the viewer's `--shot` given a viewpoint; AMBER, for his check |
| [`0253-report.md`](./0253-report.md) | report: PR #83 merged on his word — openings on a dormer record, the equal-height ridge meeting, the app's 3D view taking a shot; 0248's plans B and D closed; iteration 10 of the house ordered |
| [`0254-report.md`](./0254-report.md) | report: iteration 10 of the house — the dormers' windows; a first-floor gable wall climbed through the second storey, fixed on `roof-gable-climb-level`; AMBER, for his check |
| [`0255-report.md`](./0255-report.md) | report: his four fixes — the End-On dialog no longer takes the app down on the porch's shed roof; the window's elevation is a property on its sheet with a plan default; the schema audited against everything the app writes; iteration 11 of the house — on `window-sill-endon`, stacked on `roof-gable-climb-level`; AMBER, for his check |
| [`0256-report.md`](./0256-report.md) | report: his two reports on iteration 11's shed dormer — the End-On dialog refused it ("never meets the host roof") and OK did nothing, and its ridge grip shrank it on every move; a shed's ridge is its high edge, on the host; both fixed, folded into `window-sill-endon`'s one commit; AMBER |
| [`0257-report.md`](./0257-report.md) | report: PR #84 merged on his word, the stack folded in — the gable climb's level check, his four fixes, the shed dormer's dialog and grip; iteration 11 of the house stands |
| [`0258-report.md`](./0258-report.md) | report: 0248's plan E and its item 6 built on his word — the hip run settable per end; a `post` furnishing that rises to the roof over it; the porch floor as an exterior room; iteration 12 of the house — on `porch-posts-hip-run`, AMBER, for his check |
| [`0259-report.md`](./0259-report.md) | report: PR #85 merged on his word — the hip run per end, the post that rises to the roof over it, the porch floor; 0248's plan E and item 6 closed; iteration 12 of the house stands |
| [`0260-report.md`](./0260-report.md) | report: the compose cost built on his word, from the parked patch and past it — the arrangement built from one set of disjoint cells, a neighbour graph for the walk; 15 roofs 32 s → 8 s; the clip pinned as a function of the roofs alone — on `roofclip-cost`, AMBER, for his check |
| [`0261-report.md`](./0261-report.md) | report: PR #86 merged on his word — the compose cost: the arrangement from one set of disjoint cells and the neighbour graph, 15 roofs 32 s → 8 s; the clip pinned a function of the roofs alone; the parked patch deleted |
| [`0262-report.md`](./0262-report.md) | report: his `wiscaway2026-10-11R2.json` given the shed dormer between the front gables and the porch roof, as the house model's iteration 11 has them — a new file beside his, nothing of the tools changed |
| [`0263-report.md`](./0263-report.md) | report: his four features built on his word — annotations (text) on the plan, measurements that snap to items with a datum, the items' callouts in a settable colour, and a Show menu that switches each on its own; 0248's items 8 and 9 backlogged — on `annotations-measure`, AMBER, for his check |
| [`0264-report.md`](./0264-report.md) | report: his review of 0263 — the item callouts are the items' document ids, on when a plan opens; the measure gets its four knobs (move, rotate about the other, slide the end, slide the label); folded into PR #87's one commit; AMBER |
| [`0265-report.md`](./0265-report.md) | report: his word on the callouts — the SESSION LABELS, always (W7, V12), adopted from the file's ids when a plan opens so the two match; the Malformed-design report translated to them; folded into PR #87's one commit; AMBER |
| [`0266-report.md`](./0266-report.md) | report: PR #87 merged on his word — annotations, measurements with their four knobs and a datum, the session-label callouts, the Show menu; the knobs made small and black on his screen before the merge; his annotation-display clean-up next |

<!-- PAIRS:END -->