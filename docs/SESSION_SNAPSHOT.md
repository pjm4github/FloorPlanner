<!-- SNAPSHOT-HEAD: db09acf -->

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

**THE VESSEL/ENCLOSURE SPLIT IS MERGED — PR #31 → `main`, 2026‑08‑16 — AND
D78 (a CI-only gate bug the merge itself surfaced) IS CLOSED.** Full trail,
one line per exchange: [`handoff/README.md`](handoff/README.md)'s pair table,
`0018` through `0028`. Live records: [D75](defects/0075-a-recessed-floor-feature-is-not-representable.md)
(accepted limit), [D76](defects/0076-an-opaque-mesh-inside-a-translucent-body-does.md)
(renderer limit, open), [D77](defects/0077-fp3d-py-shot-reports-success-on-a-failed.md)
(tooling gap, open), D78 (closed).

**Next: the three artwork redraws, below.**

---

## THE QUEUE

1. **The three artwork redraws — AMBER, one check for all three.**
   `glass_shower`, `shower`, `walk_in_shower` — indistinguishable because
   identity is carried by footprint, a scalar; the fix is an internal region
   that differs in KIND. Unblocked now that the extruder they flow into
   (PR #31) is merged. Brief: [`handoff/0016-ruling.md`](handoff/0016-ruling.md)
   §2–3; ordered here by [`handoff/0025-ruling.md`](handoff/0025-ruling.md) §4.
2. **[`handoff/0019-ruling.md`](handoff/0019-ruling.md)'s status board — GREEN,
   read-back first.** Freeze the closed migration's Status table as history;
   move forward status to a generated `docs/STATUS.md`. Read-back owed: what
   identifies a completed unit when recent work has no phase number at all.
3. **Grid snap — the largest daily-use improvement left, fully specified, read-back
   owed before any code.** Snap-by-default; shift means unconstrained; the
   angled-wall rule quantises length along the ray; intersection joins with
   their two refusals; the live readout shows snapped values. The read-back:
   clause-by-clause EXISTS/PARTIAL/ABSENT, thresholds with reasons, the shift
   modifier audit, the angle convention already in the geometry code, and
   Ctrl's disposition. Spec: [`ROADMAP.md`](ROADMAP.md) A6.

**Full tiered queue (A2–A5, the command-roster census, Phase 5's remainder,
etc.):** [`ROADMAP.md`](ROADMAP.md) §3. **`boat_trailer` and the vehicle
loft** are not in this queue — both behind a read-back, design at
[`floorplanner/viewer/VIEWER_NOTES.md`](../floorplanner/viewer/VIEWER_NOTES.md)
§5.

---

## 1. Where the work stands

| | |
|---|---|
| **`main`** | **`db09acf`** — PR #31 merged at `b813343` (`gh pr merge --merge`; real two-parent commit, this repo's standing strategy), then D78's third round direct on `main`. Carries the vessel/enclosure split, the check's pass (`0025`), and D78's fix in full (`0027` — see §0). |
| **Branches** | **`d74-vessel-enclosure-split`** — merged, kept (not deleted). No other branch live. |
| **Gate** | local at `db09acf`: `collected=731 ruff=clean vacuous=0 end_assign=0 snapshot=current`; OFF / ON / DEEP each **724 passed, 7 deselected**, every sum reconciling; **`Gate-Verdict: GREEN`**. **Zero xfails.** CI on this same commit's predecessor confirmed green with the correct `Docs-Snapshot-Shape: linear` label on `main`'s real merge commit. The **7 deselected are the PERF LANE** (standing P3.8 flap-class ruling). |
| **Records** | **79 records**, **30 open**. D75 an accepted limit, D44's precedent; D76 the non-compositing renderer limit, cross-referenced to D69; D77 a tooling gap in `fp3d.py --shot`. D78 CLOSED (fixed 2026‑08‑16, `handoff/0027-ruling.md`, receipted by four `tests/test_gate.py` merge-ref tests). `python tools/gate.py --docs` GREEN. |
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
