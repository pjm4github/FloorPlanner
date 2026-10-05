<!-- SNAPSHOT-HEAD: eef0ef5 -->

# Session snapshot — read this first

**Re-cut 2026‑08‑12 for the gate condition below, and kept current by the gate
ever since.** **Trimmed to its stated job 2026‑08‑16, Patrick's ruling —
[`handoff/0028-ruling.md`](handoff/0028-ruling.md).** The file had grown to 621
lines by accumulating narrative that already lives in `handoff/`, `defects/`
and `WORKING_AGREEMENT.md` — the ruling's own measure: *"an index that
summarises the thing it indexes has stopped being an index."* Only §1 (state)
and §5 (traps) stay dense by design; everything else is now a pointer.

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
>
> **On a PR's merge-ref checkout** (`refs/pull/N/merge`), `HEAD` has two
> parents and the check reads `HEAD^2` instead — [D78](defects/0078-the-snapshot-staleness-gate-cannot-pass-on.md),
> gated on `GITHUB_EVENT_NAME == "pull_request"` so a genuine merge commit on
> `main` is never misread the same way. `tools/gate.py`'s own docstring on
> `_snapshot_checkout_base` carries the full reasoning.

> **[`README.md`](README.md) is the map** — what each document is, which decide
> things, which are history. **[`ROADMAP.md`](ROADMAP.md) is the autonomy
> charter** — which items may proceed without Patrick and which may not, and
> **§3 is the full tiered work queue** this file no longer restates.

---

## 0. WHERE THE WORK IS

> **Trimmed again 2026‑10‑03, on Patrick's word — [`handoff/0203-report.md`](handoff/0203-report.md).**
> This section had regrown to 18,600 characters of closed-tranche narrative
> and §1's `main` row to 13,000. Both now say **where the work is and where
> to read the rest**. Nothing was moved anywhere new: every sentence removed
> restated a numbered report. The text as it stood is at
> `git show 52a2870:docs/SESSION_SNAPSHOT.md`. **Keep it this size:** when a
> tranche closes, REPLACE its entry with one line and a link; do not append.

**NOTHING IS OPEN ON A BRANCH. THE 3‑INCH REACH IS CLOSED AND MERGED** —
[PR #71](https://github.com/pjm4github/FloorPlanner/pull/71) landed on `main`
by this merge commit on Patrick's word (2026‑10‑04: "OK that fix is good. commit and push # 71."),
the branch deleted in the merge step; recorded at
[`0211-report.md`](handoff/0211-report.md). Grid snap by default is closed with it: a wall
gesture lands on the grid; within 3″ of another wall's end or line it goes
to that instead; Shift turns both off. **MACRO LANGUAGE v2 IS IN — his spec,
[`docs/macro-spec/MACRO_SPEC.md`](macro-spec/MACRO_SPEC.md); the read-back and his
three answers, [`0212`](handoff/0212-report.md).** A macro whose first line is
`; fpmacro 2` runs on `floorplanner/macro2/`; anything else runs on
`MacroRunner`, untouched. Merged: the language (PR #72,
[`0213`](handoff/0213-report.md)), and — folded into ONE PR on his word and
merged by this commit ("fold all three into #73 and merge"), [PR #73](https://github.com/pjm4github/FloorPlanner/pull/73) —
the player ([`0214`](handoff/0214-report.md)), application commands
`@NAME arg …` ([`0215`](handoff/0215-report.md)) and the v2 recorder
([`0216`](handoff/0216-report.md)). The merge is recorded in the report that
follows it. **STILL OWED: the legacy converter (`fp_macro.py --convert`) and
the v2 section of `docs/macro_language.md`** — the rest of the spec's Task 5
and the plan's T3. `MacroRunner` and the committed `.fpm` files are not
touched. Everything else waiting is in THE QUEUE and
[`0211`](handoff/0211-report.md) §4.

**`fixtures/incoming/single-floor-90-roof-gable-end-check.json` — his own,
2026‑10‑03, and no defect comes with it.** His words: *"a smaller, easier
to test work design."* One level, 19 walls all on axis, no rooms, two
roofs at 90° (rf1 along x; rf2 along y, 36″ overhang, the higher ridge).
Its exit from `incoming/` is not yet named (0205 §3).

**OPEN FOR HIS RULING, none built:**

* [D67](defects/0067-selection-is-not-scoped-to-the-active-floor.md) —
  reproduced, mechanism `RoomItem.interior_walls()` with no floor predicate,
  undo complete; the fix is one predicate ([`0201`](handoff/0201-report.md) §1).
* The Door/Window tool places an opening on another level's ghosted wall —
  D67's class, measured 56 → 57 ([`0202`](handoff/0202-report.md) §4).
* A dormer on a roof of another level, and the R3b wall dash / R5a trace
  across levels — one decision (0202 §6; [`0200`](handoff/0200-report.md) §6).
* The crossed-arm rule reads the plan, not the height; L2's storey height in
  his fixture is 196″ (0200 §5–6).
* The End-On dialog's level line was built from a finding, not a fault — his
  to reverse (0202 §2).

**THE ROOFLINE ARC, CLOSED TRANCHES — one line each; the report is the record.**

| tranche | what | PR | report |
|---|---|---|---|
| R1–R3b | model, ridge sketch, end-on marker, show/edit, planes and gables, the wall clip line | #48–#53 | [`0139`](handoff/0139-ruling.md)–[`0153`](handoff/0153-report.md) |
| R4a–R4c | schema, parameters dialog, five grips | #54–#56 | [`0155`](handoff/0155-report.md)–[`0163`](handoff/0163-report.md) |
| R4d–R4g | intersection clip, mesh clip, the three-ridge envelope, the full footprint | #57, #58, #60 (#59 closed, superseded by #60) | [`0164`](handoff/0164-ruling.md)–[`0185`](handoff/0185-report.md) |
| R5a | the clip trace on the roof | #61 | [`0187`](handoff/0187-report.md) |
| 3D wall clip | walls capped under roofs | #62 | [`0188`](handoff/0188-report.md), [`0189`](handoff/0189-report.md) |
| R5b | dormers; then undo, the `DORMER` macro token, the grip clamp | #63–#65 | [`0190`](handoff/0190-report.md)–[`0196`](handoff/0196-report.md) |
| R6.0 | D50 closed: a level's elevation and height survive | #66 | [`0198`](handoff/0198-report.md) |
| R6.a | plan-view roof rule; 3D builds the whole building | #67 | [`0199`](handoff/0199-report.md) |
| R6.b | one roofscape, composed in absolute height | #68 | [`0200`](handoff/0200-report.md) |
| (measurements) | D67 reproduced; roof paths and the level's elevation | — | [`0201`](handoff/0201-report.md) |
| R6.c | the roof tool across levels; `fixtures/r6c-two-level-tool-check.json` its manual check | #69 | [`0202`](handoff/0202-report.md) |
| A6 | grid snap by default (not roofline; listed here as the arc's last merged tranche): walls land on the grid, Shift unconstrained, 3″ gesture weld | #70 | [`0207`](handoff/0207-report.md), [`0208`](handoff/0208-report.md) |
| the 3‑inch reach | his report against A6 fixed: every gesture pull reaches 3″; `fixtures/grid-snap-3in-check.json` its manual check | #71 | [`0210`](handoff/0210-report.md) |

Everything before the roofline arc — the vessel/enclosure split, the three
redraws, the wall orthogonality repair, the wall id fix, the snap-to-grid
features — is merged and closed; `handoff/README.md`'s pair table is its
trail.

**Named, not ordered:** valley/hip lines; a roof-plan export sheet; yard
items. **Carried, undated:** room-label rounding
([`0131`](handoff/0131-ruling.md) §2); delta-snap sites; the D61 family.
**Numbering collisions on the record:** `0036`, `0043`, `0050`, `0101`,
`0138`, `0139` — neither renamed after commit.

**Traps for whoever touches `roofclip.py` next:** the fixed point's
three classes (phantom / root limb / orphan) and the ORDER they prune in
are load-bearing — measured alternatives that fail are recorded in the
in-code comments and in 0182 §2–3 (judge-with-others-removed deadlocks;
poke-height ordering fails the saddle in isolation; whole-component
limbs re-open D85; root-only limbs strand rf3's rake). `_reach`'s
`no_step` veto is the strip rule; `_under_pieces(..., exclude=)` keeps
phantoms out of the network. `diag=` is the testing hook: cells,
original coverers, blank cells, limb cells, and every round. Seams are
read off the FINAL pieces (`_shared_segment`, 0183), never off the
in-round crossing bookkeeping. A swallowed end's `ext` is zero when the
end is open (0184: short of every host's ridge and above the host) --
the item and `fp3d` both key the end line and fascia on it. The mailbox
lands on `main` only (the commit hook enforces it); branch deletions
count as pushes to the hook -- delete a merged ref through `gh api`. R5a's
trace (`roof_clip_trace`) is computed at PAINT time like the wall dash
(rooms change without the roof hearing), and the join extension it
carries while clipped is R4d's raw reach -- hundreds of inches -- only
ever seen through `_drawn_trace`'s region clip; never draw the
unclipped locus of a clipped roof. **Since R6.b** composition is the
whole building's (`compose_building`, absolute height), and
`hold_roof_clips` holds it during a load and a drag; **since R6.c** a roof
of a level not being edited has an empty hit shape (`_roof_hittable`).

---

## THE QUEUE

> **Trimmed 2026‑10‑03, on Patrick's word — [`handoff/0204-report.md`](handoff/0204-report.md).**
> Six of this section's eight numbered items were DONE and still carried
> their whole build narrative. What is open is stated; what is closed is
> one line and its report. The text as it stood is at
> `git show 0f833f4:docs/SESSION_SNAPSHOT.md`. The roofline arc — the
> work actually in flight — is §0, not here.

**OPEN — one item, not started.** (Grid snap by default, A6, which stood
first here, is CLOSED AND MERGED — PR #70, [`0207`](handoff/0207-report.md),
[`0208`](handoff/0208-report.md). **Left open by his word, not dropped from
the spec: the angled-wall rule**, quantising length along the ray; and
snapping what an OPERATION produces, which A6 never covered.)

1. **The status board — GREEN, read-back first.**
   [`handoff/0019-ruling.md`](handoff/0019-ruling.md), priority lowered by
   [`0029`](handoff/0029-ruling.md) §6 (Patrick's Cowork skill renders the
   same state on demand — a view, not the artifact). Freeze the closed
   migration's Status table as history; move forward status to a generated
   `docs/STATUS.md`, which does not exist yet. Read-back owed: what
   identifies a completed unit when recent work has no phase number.

**Full tiered queue (A2–A5, the command-roster census, Phase 5's
remainder):** [`ROADMAP.md`](ROADMAP.md) §3.

**NAMED, NOT BUILT — each waits on its own ruling:**

* [D79](defects/0079-six-catalog-symbols-extrude-as-disconnected.md) — six
  catalog symbols with a fragmented body, exempted by name from the
  extrudability predicate; `boat_trailer` with them.
* `boat_trailer` and the vehicle loft — behind a read-back; design at
  [`floorplanner/viewer/VIEWER_NOTES.md`](../floorplanner/viewer/VIEWER_NOTES.md) §5.
* The four masked reachability sites, and `wall_endpoint_open`'s
  `floor=None` default, which should invert but changes two callers
  ([`0063-ruling.md`](handoff/0063-ruling.md)). Every mouse/macro hit path
  trusts Qt's visible/enabled state where `walls.py`'s geometry paths check
  `.floor` — the structural gap [`0037`](handoff/0037-ruling.md) §5 names.
  **D67's class: its two measured sites are in §0.**
* The orthogonality repair's clause (f): a wall the repair REFUSES can
  still move, through a vertex it shares with one the repair does move
  ([`0083-report.md`](handoff/0083-report.md) §§4–5). And its item 3 — a
  user-settable `T`, the graph solve — stays RED.

**CLOSED — one line each; the report is the record.**

| item | outcome | record |
|---|---|---|
| The extrudability predicate | built, merged. D76 stands unamended; **a mark nested in a translucent body is invisible — a redraw adds `beside` shapes, never regions** | [`0029`](handoff/0029-ruling.md) §2 · [`0032`](handoff/0032-report.md) · [`0036-report`](handoff/0036-report.md) |
| The artwork redraws (`shower`, `glass_shower`, `walk_in_shower`) | built, his check passed, merged | [`0016`](handoff/0016-ruling.md) · [`0033`](handoff/0033-report.md) · [`0050-ruling`](handoff/0050-ruling.md) |
| `Docs-Snapshot` out of the `pull_request` CI lane | done | [`0042`](handoff/0042-ruling.md) · [`0048`](handoff/0048-report.md) |
| The commit hook: quick for commit, full for push | done | [`0043-ruling`](handoff/0043-ruling.md) · [`0047`](handoff/0047-ruling.md) · [`0049`](handoff/0049-report.md) |
| The orthogonality report and its corpus census (63 near-axis walls of 948) | done | [`0055`](handoff/0055-ruling.md)–[`0060`](handoff/0060-report.md) |
| The cross-floor align fix (`_align_to_wall`, `wall_endpoint_open(floor=)`), with its positive control | merged, PR #34 | [`0061`](handoff/0061-ruling.md)–[`0063`](handoff/0063-ruling.md) |
| The wall orthogonality repair | merged, PR #37. Corpus: 22 moved, 4 refused, 37 withheld by one file's rollback | [`0066`](handoff/0066-ruling.md) · [`0079`](handoff/0079-report.md) · [`0082`](handoff/0082-ruling.md) · [`0083`](handoff/0083-report.md) |
| `fp2dxf`, the v5 → Chief Architect DXF exporter | merged, PR #33, his Chief import check passed | [`0038-ruling`](handoff/0038-ruling.md) · [`0043-report`](handoff/0043-report.md) · [`0050-report`](handoff/0050-report.md) |

**Confirmed by Patrick, 2026‑10‑03:** *"PR #37 and PR #34 are complete. The cheif architect import is completed and it works."*

**Patrick's cross-floor report of 2026‑08‑17**
([`0035`](handoff/0035-ruling.md)–[`0037`](handoff/0037-ruling.md);
[`0038-report`](handoff/0038-report.md) refuted the load-path suspect):
its snapping half is the align fix above; its selection half is D67,
reproduced at [`0201`](handoff/0201-report.md).

**Numbering collisions in this range, neither renamed:** `0036` and `0038`
each name a ruling and an unrelated report (§0 lists the later ones).

---

## 1. Where the work stands

| | |
|---|---|
| **`main`** | **`eef0ef5`** at this file's cut — the `macro2-player` tip (player, application commands and recorder, folded), landed on `main` by the merge commit this file rides in: **macro v2 MERGED on Patrick's word** ("fold all three into #73 and merge"); `main`'s `1cf2c66` ([`0216`](handoff/0216-report.md) landed) is its other parent. **Owed next: the report recording this merge; then the legacy converter and docs.** Every PR through #73 is merged (#59 was closed, superseded by #60). |
| **Branches** | **None open.** Only `main` on the remote: `macro2-player`, `macro2-commands` and `macro2-recorder` were deleted in this merge step, local and remote, like every merged branch before them. |
| **Gate** | full mode, re-run for this commit. GREEN — see this commit's own gate run. The **7 deselected are the PERF LANE** (standing P3.8 flap-class ruling). |
| **Records** | **86 records, 32 open** (D50 CLOSED 2026‑09‑25, R6.0, `closed_by b8475b7`). D75 an accepted limit, D44's precedent; D76 the non-compositing renderer limit, cross-referenced to D69; D77 a tooling gap in `fp3d.py --shot`. D78 CLOSED (fixed 2026‑08‑16, `handoff/0027-ruling.md`). D80 CLOSED (fixed 2026‑08‑22, closed 2026‑08‑23 on Patrick's own check, `handoff/0088-ruling.md`, merged `main` at `ac6d763`). **D81/D82 CLOSED 2026‑08‑30** — `fp2pdf.py`'s door symbols and dimension-fraction formatting, fixed and merged, `handoff/0122-report.md`. **D83/D84 OPEN, filed 2026‑09‑02** — two macro-recorder gaps Patrick found, held for later, not scheduled. **D85 CLOSED 2026‑09‑05** — a very short roof ridge (or a thin-span one) was unselectable because its shape only covered the ridge, not the dashed eave/gable lines; fixed and confirmed on his own check, merged with R3b. `python tools/gate.py --docs` GREEN. |
| **Working tree** | see §5 — check `git status --untracked-files=all` before believing a census disagreement. |
| **THE MIGRATION** | **CLOSED 2026‑08‑11** — closing statement with its evidence in [`ROADMAP.md`](ROADMAP.md). Everything after it is features or cleanup. |
| **PHASE 6** | **PARKED 2026‑08‑12, Patrick's ruling** — see §2. |
| **PHASE 5** | **P5.2 (settable wall types + porch railings) COMPLETE**, PR #26 then PR #27, D73 and D74 closed. Progress entry at [`progress/phase-5.md`](progress/phase-5.md). **P5.1 and P5.3 not started**; the Yard catalog stays RED on artwork scope, and D46 closes with it. |

**A commit gate is enforced, not merely available.** `tools/gate.py` writes
`.gate-result.json`; a `PreToolUse` hook blocks any `git commit` unless that file
exists, reads GREEN, and is **newer than every tracked file** — every tracked
file, `.md` included, so a document edit made after the gate ran makes it stale.
See §5.

---

## 2. PHASE 6 IS PARKED — 2026‑08‑12

**P6.a and P6.b stay MERGED AND DORMANT; P6.c and P6.d are NOT WIRED.**
Refuted by measurement: Phase 6 does not retire `snapshot()`, and neither
D42's applier consolidation nor D45's `_edge_wall` folds in here. **Full
record, reasoning and the two named reopening conditions:**
[`ROADMAP.md`](ROADMAP.md) § "PHASE 6 IS PARKED".

---

## 3. How to read this repo's record

Which document answers which question:

| the question | the document |
|---|---|
| *What is the architecture? What are the house rules?* | **`CLAUDE.md`** |
| *What is every document, and which are authoritative?* | **[`README.md`](README.md)** — the map. Start here when unsure. |
| *What may proceed without Patrick, and what may not?* | **[`ROADMAP.md`](ROADMAP.md)** — the tier charter (GREEN / AMBER / RED), the autonomy policy, rulings **R‑A** and **R‑B**, the full work queue, and the **Phase 6 park**. |
| *What rules bind the work?* — census doctrine, gate discipline, what a receipt is, how vacuity is detected | **[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)**. Extracted from the plan because the rules outlive the migration. |
| *What is planned, and what is done?* | **[`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md)** — Status table, phase specs, risk register, sequencing rationale. |
| *What happened, and what proved it?* | **[`progress/`](progress/)** — the log, split by phase, verbatim and contemporaneous. Index at [`progress/README.md`](progress/README.md). |
| *What is broken, and what was decided about it?* | **[`defects/`](defects/)** — one record per file, `D23` is the permanent key. Index at [`defects/INDEX.md`](defects/INDEX.md); field rules at [`defects/README.md`](defects/README.md). |
| *What did an agent report, and what was ruled?* | **[`handoff/`](handoff/)** — the mailbox. Chat is not the record. |
| *What was measured, and how do I reproduce it?* | **[`evidence/`](evidence/)** — cited by records, never inlined. |
| *What was the plan before this one?* | **[`superseded/`](superseded/)** — kept because it holds material found nowhere else, **not** because it is safe to skip. |

**Reading order for a fresh session:** `CLAUDE.md` → this file →
[`handoff/`](handoff/) (highest number first) → [`README.md`](README.md) →
[`ROADMAP.md`](ROADMAP.md) → then whichever row above the task needs.

**`docs/CODE_REVIEW_v2.md` is still worth reading** for §1 (module verdicts) and
§2 (the five structural findings). Its §3 is now a pointer into `defects/`.

---

## 4. The rules that bind the work

**Full text and reasoning for every rule below is
[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md).** This is names only — enough
to know a rule exists and where to read it, per
[`handoff/0028-ruling.md`](handoff/0028-ruling.md)'s own instruction that this
section stop carrying the reasoning WORKING_AGREEMENT.md already carries.

- a green signal is only evidence about what it measures
- retire visibility before permission; enumerate a view's consumers first
- a task that changes what an operation does owes a differential receipt
- vacuity has three shapes, plus UNSATISFIABLE, its mirror
- negative assertions are where vacuity concentrates — preconditions are mandatory there
- verify a probe — and a record edit — actually landed
- measure survival justifications like any other claim
- grep for identifiers, parse for shapes
- in a test, call the production predicate rather than restating it
- a tidy-up pass that outlives its mess only touches things nobody asked it to
- every census is shaped by its enumeration source — enumerate from the PROPERTY, not a container
- identity needs a categorical channel, not a scalar one
- a criterion that splits two structurally identical cases is measuring the wrong thing, and the aggregate never shows it
- an acceptance stated as a count is satisfied by replacement — measure identity, not a total
- a content correction discovered during a structural move is never folded into the move
- a lint that fails on correctly-recorded history is a lint that gets disabled
- a boundary belongs at the instrument — annotate, do not rewrite
- truncation invites fabrication
- the GREEN criterion: "no new semantics, and nothing the user must learn"
- an append-only shared file serialises parallel branches
- **every instrument is validated against a case known to be non-zero before its zero is believed** — the positive-control family, four members, all in `WORKING_AGREEMENT.md`: an instrument reporting nothing; one reporting a plausible something; one that can report only one of its two answers; and **a control proves the question it was built to answer, and no more** (added 2026‑08‑16)

---

## 5. Things that will waste your time if you don't know them

- **A task that changes `main`'s head, the queue, the record count or the gate
  line RE-CUTS §0/§1 IN ITS OWN COMMIT** — not "before the next session." This
  file went stale for eight commits, once, because each one left it for the
  next.
- **A `git commit` is BLOCKED unless a fresh green gate result exists on disk.**
  `tools/gate.py` writes `.gate-result.json` (gitignored) at the end of a
  full-mode run; `.claude/hooks/verify_gate.py` checks it exists, reads GREEN,
  and is **newer than every tracked file** — **including `.md` files**, so *edit
  the documents first, then gate, then commit*. The hook reads the RESULT FILE,
  never the commit message.
- **A NEW `docs/handoff/NNNN-*.md` ONLY COMMITS ON `main`** (0084-ruling.md
  §4) — `.claude/hooks/verify_gate.py` refuses a `git commit` that ADDS one on
  any other branch, merge commits exempt. Write the report or ruling, commit
  it on `main`, then branch for the code that answers it.
- **ONE CALL CANNOT BOTH RUN THE GATE AND COMMIT**, and the hook blocks that
  shape outright. **`--trailer` is exempt** — it runs nothing and writes nothing,
  and it is exactly the command that belongs beside a commit. **The hook's match
  is a plain substring on `tools/gate.py`**, so it also fires on a `git add`
  that merely names that path (or `tests/test_gate.py`) in the same command as
  a commit, and on a commit MESSAGE that quotes the string — stage in one call,
  commit (ideally via `-F <file>`, not an inline message) in the next.
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
- **`fp3d.py`'s GL rendering (`--shot`, `make_view`) needs a REAL display, not
  `QT_QPA_PLATFORM=offscreen`.** Measured 2026‑08‑16 (D77, D78's investigation):
  under `offscreen`, this project's Qt cannot create a GL context at all —
  `grabFramebuffer()` returns a null image, `.save()` returns `False` (its
  return value is unchecked), and `--shot` prints `wrote <path>` and writes
  nothing, reproducibly. The real platform, an actual window, works. Headless
  2D work (`QGraphicsScene`, `export_canvas`) is unaffected — this is GL-specific.
- **A SHALLOW git checkout (`fetch-depth: 1`, `actions/checkout`'s default)
  hides ALL parent-relative revisions at the boundary commit** — not just a
  merge commit's second parent; `HEAD^1` fails too. Measured on CI building
  D78. `git cat-file -p HEAD` still shows the true `parent` lines (raw object
  content, unaffected); `git rev-parse HEAD^N` / `HEAD~N` do not. Jobs that
  need real ancestry (this file's own staleness check, `closed_by` validation)
  need `fetch-depth: 0`.
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
