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
| [`0033-report.md`](0033-report.md) | Report — the three redraws built, AMBER, one honest limit. **Cherry-picked onto `main` at `0040`'s §4 remedial** (was branch-only on `shower-identity-redraws`/PR #32 until then) |
| [`0034-ruling.md`](0034-ruling.md) | Ruling — the check is ready, the camera is the open question, `0030` §4 withdrawn. **Cherry-picked onto `main` at `0040`'s §4 remedial** |
| [`0035-ruling.md`](0035-ruling.md) | Ruling — Patrick's own report: cross-floor snapping (a census must test BOTH a missing filter and mis-tagged floor data, since the obvious query paths already filter correctly) and a per-floor totals feature, blocked on open D55 (totals double-count overlaps) — GREEN measurement can start now, neither displaces `0033`'s check or grid snap |
| [`0036-report.md`](0036-report.md) | Report — `0034`'s four action items, built. **Number collision** with this file's own `0036-ruling.md`; both legitimately committed on their own branches, neither renamed; see `0038`. **Cherry-picked onto `main` at `0040`'s §4 remedial** |
| [`0036-ruling.md`](0036-ruling.md) | **Number collision** — this file and `shower-identity-redraws`'s `0036-report.md` share a number; both legitimately committed on their own branches, neither renamed; see `0038`. Ruling — snap vs. bleed-through are different faults with no shared code; the discriminator is whether the saved document changes across the gesture, and it must run before `0035`'s census |
| [`0037-ruling.md`](0037-ruling.md) | Ruling — light gray IS the ghost paint, so `show_others` was true; names a suspect (the load path setting only `active`) and revises the census to Qt-reachability paths, not `.floor`-filtered ones |
| [`0038-report.md`](0038-report.md) | Report — `0037` §2's suspect does not hold: `apply_design_to_scene` already calls `_sync_floor_state()` on load (`bridge.py:1265`, since 2026‑07‑26), measured correct on Patrick's own submitted plan both with and without `show_others` pre-set. Reopens `0036`'s document-diff discriminator, still unanswered |
| [`0038-ruling.md`](0038-ruling.md) | **Number collision** — this file and this session's own `0038-report.md` (unrelated, about the floor investigation) share a number; neither renamed; see `0039`. Ruling — `fp2dxf` (a v5→DXF exporter built outside the repo) accepted in principle; its thickness table is D73/D74's disease again (one column carrying both a real quantity and a Chief-type mapping); three library-hygiene faults named; AMBER, ordered behind `0033`'s check and the floor work |
| [`0039-report.md`](0039-report.md) | Report — blocked: `fp2dxf.py`, its README, sample input/output and screenshots are not anywhere in this repository (checked exhaustively). Nothing in `0038` can start until it is dropped somewhere readable |
| [`0040-ruling.md`](0040-ruling.md) | Ruling — the package landed (`0038-fp2dxf-handoff.zip`, verified CRC); `0037` §2's suspect withdrawn (the v5 load path already recomputes floor visibility, since 2026‑07‑26); the "report and ruling share a number" convention retired — a ruling names the report it answers instead; the mailbox is a record and lives on `main` only, never a feature branch; `0033`–`0036-report.md` cherry-pick onto `main` still owed and gates the next number |
| [`0041-ruling.md`](0041-ruling.md) | Ruling — Code hit its context limit before a checkpoint; recovery recorded from the artifact alone: gate GREEN, `fp2dxf.py`/`__init__.py` on disk with the by-path decision written into the docstring, zip still packed. Recovery owed: re-run the gate, commit as a recovery (not a checkpoint), a short report |
| [`0042-ruling.md`](0042-ruling.md) | Ruling — answering Patrick's "is CI overkill" question: no, `Docs-Snapshot` is the only check ever at fault and it is miscategorised, not excessive — a git-topology check wearing a CI job's clothes; moved out of the `pull_request` lane, kept on push-to-`main` and the local gate, which already prevents the fault before a commit exists |
| [`0043-report.md`](0043-report.md) | Report — recovery closed: gate re-run found one new `ruff` finding (`B905`, fixed), committed at `5d61f1f`; measured against `0038`'s owed list, all three library-hygiene fixes and the `STD_T` thickness rewiring are already done, not merely started; zip still packed, no sample/README/golden test yet. **Numbered `0043` not `0042`**: `0042-ruling.md` landed mid-session and took the number first. `0040`'s cherry-pick remains owed and still gates the next number |
| [`0043-ruling.md`](0043-ruling.md) | **Number collision** — this file and Code's own `0043-report.md` share a number, a third time; see `0044`. Ruling — answering Patrick's "is the gate too rigorous" question: the friction is that only full-mode gate output unlocks a commit, not the gate's rigour itself; moves the bar from every commit (`--quick`) to every push (full mode), unchanged strength at what reaches `main`/origin/CI; also owes a flap receipt — run the gate twice on one unchanged tree before trusting a "flapping" claim |
| [`0044-ruling.md`](0044-ruling.md) | Ruling — `0043`'s collision was a genuine race (two writers, no lock), not the branch split; retires nothing further, but adds a protocol refinement: name the suffix when flagging a shared number (`"0043-ruling is up"`, not `"0043 is up"`). Names the order of everything owed: push `main`, cherry-pick `0033`-`0036-report.md` (this commit), the flap receipt, `0042`'s CI-lane move, `0043`'s hook split, then the DXF integration last, on a fresh context |
| [`0045-ruling.md`](0045-ruling.md) | Ruling — Patrick's shower check was run against `main`, which never had the redraws; they and the after-render exist only on `shower-identity-redraws`. Third instance of one root cause (work needed for a check living on an unnamed branch); adds "name the BRANCH" as the third check-request clause alongside "name the PLAN" and "name the CAMERA". Tier NONE — corrects how the check is run, changes nothing; `0044` §3's order stands |
| [`0046-report.md`](0046-report.md) | Report — `0044` §3 items 2 (mailbox cherry-pick) and 3 (flap receipt: gate run twice on one unchanged tree, identical both times, no flap) done, doc-only/measurement-only. Items 1 (push), 4 (CI-lane move) and 5 (hook split) held — push and infrastructure edits, CLAUDE.md's own etiquette says push only when explicitly asked, held to the same standard here despite `0044`'s GREEN tier. Item 6 (DXF) untouched per `0044`'s own instruction to start it fresh |
| [`0047-ruling.md`](0047-ruling.md) | Ruling — all three held items authorised: push needed no asking (the autonomy policy already covers it, verbatim), the CI-lane move authorised as ruled at `0042`, the hook split authorised but `0043` §7's one control is not enough — needs FOUR (no-result/quick-GREEN/full-GREEN/any-RED, each at both commit and push), in its own commit, revertible alone. The line: autonomy covers work the gate judges, not changes to the judge |
| [`0048-report.md`](0048-report.md) | Report — item 4 done: `Docs-Snapshot` skipped in the `pull_request` lane via a new `_snapshot_check()` wrapper at the two call sites (`main()`/`_docs()`), not inside `_snapshot_head()` itself, so every existing `HEAD^2`/merge-ref test keeps exercising the real logic unchanged. Two new controls (skip-when-stale positive, skip-scoped-to-PR negative), 13/13 green, end-to-end CLI check under a simulated PR env. One pre-existing, unrelated `Docs-Verdict: RED` (30 unresolved doc refs) flagged, not fixed |
| [`0049-report.md`](0049-report.md) | Report — item 5 done: the commit hook now matches `git push` too, requiring `mode == "full"` in `.gate-result.json` (a new field `--quick` now also writes); `git commit` still accepts either mode. `tests/test_verify_gate_hook.py`, 18 tests against an isolated fixture repo, driving all 8 cells of `0047`'s table plus distinct-message and freshness controls — caught a real `"pushs"` pluralisation bug before it shipped. 31/31 green (with `0048`'s 13), full gate GREEN |
| [`0050-ruling.md`](0050-ruling.md) | Ruling — Patrick's check on `shower-identity-redraws` passes (the three enclosures read as different things); the branch is 9 behind `main` and must not merge as checked — bring `main` in, full gate on the combined tree, re-run the extrudability census and report the three redrawn symbols, retake the after-shot only if the render changed, then PR/green CI/merge. AMBER condition already met, subject to stating which camera Patrick used and the re-gate |
| [`0050-report.md`](0050-report.md) | **Number collision** — this file (the worktree agent's own, landed autonomously) and `0050-ruling.md` share a number; the collision `0051-ruling.md` §2 predicted before it happened. Neither renamed, per `0040` §4's judgement. Report — `0044` §3's last item (the `fp2dxf` DXF integration) built end to end on branch `fp2dxf-integration`: zip unpacked/deleted, golden DXF pair regenerated against `STD_T` (diff stated: only `exterior`/`railing` moved), README split (workflow section transcribed verbatim), the File ▸ Export ▸ Chief Architect (DXF)… menu action + completion dialog wired, 7-test golden-file receipt, gate GREEN, ruff clean. [PR #33](https://github.com/pjm4github/FloorPlanner/pull/33) open. AMBER — Patrick's Chief Architect manual check is the merge condition and is out of Code's reach |
| [`0051-ruling.md`](0051-ruling.md) | Ruling — the DXF worktree agent is the right call, but structurally guaranteed to collide on a handoff number (it forked before `0050` existed) and to write its report on its own branch, not `main`. New rule: a worktree agent does not take a number or land a mailbox file; the parent reserves the number and lands the report on `main` itself. Retrofit for the run in flight: let it finish, then the parent renumbers and lands it |
| [`0052-ruling.md`](0052-ruling.md) | Ruling — the export guide lands at `docs/guides/chief-architect-export.md`, a new category (first user-facing doc in the repo); §1 of the zip's README is deleted as a spent handoff spec, §§2/3/5 become the guide, screenshots stay at `docs/evidence/chief-export/` with paths rewritten to `../evidence/chief-export/...`, and the guide must carry the current `STD_T`-derived thickness numbers, not the zip's stale ones. GREEN, separable from the AMBER menu item |
| [`0053-ruling.md`](0053-ruling.md) | Ruling — reads the git widget for Patrick: the DXF agent finished (`fb054e3`, took `0050` exactly as `0051` predicted), the worktree/branch are spent and owed deletion. Order: `git pull` main, merge PR #32 (ready, only the census statement was owed), leave PR #33 for Patrick's Chief check (on the regenerated DXF, not the original sample), delete five spent branches. Confirms the numbering-fix rule is now owed, not optional, since the collision happened while the agent was already in flight |
| [`0054-report.md`](0054-report.md) | Report — Patrick's Chief Architect check PASSED, quoted verbatim: the regenerated `L1.dxf`/`L2.dxf` exported from `fp2dxf-integration` and imported into Chief Architect X17, closing `0038-ruling.md` §8's merge condition. Branch brought current with `main` (8 behind, one real conflict in `fixtures/README.md`), re-gated GREEN. One review-checklist gap flagged for the record: the menu item only exists on the unmerged branch, and its label is a flat File-menu entry, not a nested submenu |
| [`0055-ruling.md`](0055-ruling.md) | Ruling — grid snap will not fix the off-axis walls Chief flagged on Patrick's own export; the exporter itself is clean (0 off-axis in the committed sample); Patrick's document shows two populations, `L1`'s large angles likely real architecture, `L2`'s 75 sub-2° deviations measured as drift from move/join/weld/coalesce relocating a vertex, which snap (cursor input only) cannot touch. Orders an orthogonality REPORT first (GREEN, cheap), a REPAIR is RED and unauthorised pending its own tolerance ruling, grid snap unchanged but its read-back owes one more clause |
| [`0056-report.md`](0056-report.md) | Report — item B built, item B ONLY per instruction: `wall_orthogonality()`/`orthogonality_bands()` in `validate.py`, wired into both surfaces `0055` asked for (`tools/validate_design.py`'s corpus census, Edit ▸ "Wall orthogonality report…"). Cross-checked against `0055`'s own corpus numbers (6/2 off-axis walls on `planc1.v5.json`/`symmetricP1.json`) rather than assumed. 17 new tests, both controls, gate GREEN. Item C (the repair) and grid snap (item A) untouched, as instructed |
| [`0057-ruling.md`](0057-ruling.md) | Ruling — the instrument is accepted (four things done right unprompted: cross-checked numbers, named the DXF-line/wall-count mismatch, the positive-control-for-zero, ASCII labels) but the census itself — B's whole justification — was never run. Orders it: every file in `examples/`+`fixtures/`, per-plan band table, the corpus total within 1° of orthogonal. Also owes one guide line (check the report before exporting) and notes the export-warning question (not ruled) and an Edit-menu placement gap (not worth its own fix) |
| [`0058-report.md`](0058-report.md) | Report — the census run: 948 walls across 16 v5 plans (8 skipped, each named why), 63 within 1° of orthogonal without being on it — `0055`'s own input to item C's tolerance argument. Two more of `0055`'s own numbers independently reproduced (both wiscaway files, exact match). One outlier named, not triaged (a live cross-floor-snapping intake file, different thread). Guide line added to `README.md` where the guide actually lives (not `docs/guides/`, which `0052` specified but `0054` found superseded). Export-warning question left open, as scoped |
| [`0059-ruling.md`](0059-ruling.md) | Ruling — the census stands, but its printed table cannot produce its own 63 headline: the bottom band merges "exactly on axis" with "off by up to 0.01°", so 51 of the 63 are visible and 12 are not. Orders the bucket split (`0.01-0.1`, `0 < dev < 0.01`, `on axis` as its own row), then a re-run. `0052`'s guide-location ruling withdrawn, superseded by where the branch had already put it. Names the crossfloor-snap outlier as a question for `0037`'s thread, not this one, with a cheap separating measurement suggested (its off-axis rate vs `wiscaway2026-08-09R`'s) |
| [`0060-report.md`](0060-report.md) | Report — the band split built and re-run: the table now sums to 63 exactly. Found and fixed a latent column-width bug in both printers, exposed by the new longer label. Ran `0059`'s suggested comparison: it does not separate the two hypotheses, and where it points, it points away from the bug — `wiscaway2026-08-09R` (no reported cross-floor symptom) has MORE walls over 5° (53) than the crossfloor plan (36), correcting `0058`'s own "highest in the corpus" framing. Also ran `0037` §3's reachability census: every mouse/macro hit-test and selection path shares one root (`items.py`'s `hit_candidates()`) and none filter by `.floor`, versus 100% of `walls.py`'s geometry hot paths, which do — currently masked by `apply_floor_visibility` running at load, not a reproduced bug, no fix built (AMBER territory per `0037` §6). GREEN, measurement only |
| [`0061-ruling.md`](0061-ruling.md) | Ruling — withdraws both of `0059` §4's own claims (crossfloor is not the worst on the flagged band; the rates are not the same) and accepts `0060`'s correction verbatim. The census found the fault: `view.py:244` `_align_to_wall` scans `sc.items()`, not `items(pos)`, so it is not masked by `apply_floor_visibility` the way the other reachability sites are — a real, live cross-floor snap on the wall-drawing path, matching Patrick's report clause for clause. Orders a fail-first test first (GREEN), then the fix (AMBER, Patrick's manual check as the merge condition), then names `fixtures/incoming/crossfloor-snap-2026-08-17.json`'s exit as owed |
| [`0062-report.md`](0062-report.md) | Report — the fail-first test built (RED before the fix: `500.0` where `505.0` was drawn), the fix applied (`_align_to_wall` and `wall_endpoint_open` both gained the `.floor` filter every other geometry hot path already had), full regression pass green, gate GREEN. The four other unfiltered sites `0061` §4 named are scoped out with a stated reason (they use `items(pos)`/`items(area)`, which `0061`'s own §2 found masked, unlike the bare `sc.items()` that was the live bug) and left as named follow-on hardening. `fixtures/incoming/`'s exit taken: the defect is covered by the synthetic test, the file itself promoted to `fixtures/` (kept as independent corpus evidence, not deleted). AMBER — branch `cross-floor-align-fix`, PR open, stopped for Patrick's manual check |
