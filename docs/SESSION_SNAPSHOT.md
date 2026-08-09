# Session snapshot — read this first

**Re-cut 2026‑08‑09 on `main` @ `eae9b77`, immediately after PR #18 merged.** **PHASE 4 IS COMPLETE; the GREEN batch merged; A1 AND A1b ARE BOTH DONE, each having passed its manual check. THE NEXT ITEM IS A2 — D11's runtime z collapse — and its FIRST DELIVERABLE IS A MEASUREMENT, NOT A FIX.** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

> **[`README.md`](README.md) is the map** — what each document is, which decide things, which are history. **[`ROADMAP.md`](ROADMAP.md) is the autonomy charter** — which items may proceed without Patrick and which may not. Read §4 below for the short version, and the map for the whole.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | none open. `a1-d47-fragment-extract` and `a1b-d53-readback` are both merged and deleted, local and remote. |
| **`main`** | **`eae9b77`** — PR #18 (A1b). CI green on all six jobs. `origin/main` is the same commit. |
| **Merged since the last re-cut** | **PR #17** (A1 / D47 — a fragment is a floating room) and **PR #18** (A1b / D53 — type priority, not z-order; carrying D57's crash fix, the fixture freeze, the `View` and `Edit` reach routes, and four filed records). Both as **merge commits, not squashes**: the sequence is the record. |
| **The two manual checks** | **A1**: three floating pieces, no group boxes, each carrying its region, no dashed edge, undo restoring both rooms — and totals 505 → 424 sq ft holding at 424, which is independent evidence the pieces are disjoint. **A1b**: every item, **including drag-a-room's-label-then-right-click-a-wall-inside-it** — the gesture that broke A1b's first cut through the *left*-click virtual, so passing it through the *right*-click virtual is the evidence one resolver governs both. |
| **Census** (full mode, `main`, 2026‑08‑09) | `collected=663 ruff=clean vacuous=0 end_assign=0`; OFF / ON / DEEP each **656 passed, 7 deselected**, every sum reconciling; **`Gate-Verdict: GREEN`**. **Zero xfails.** |
| **Records** | **61 records — 19 open, 42 closed.** `python tools/gate.py --docs` **GREEN**. `Ref-Audit: unresolved=10` — dangling *links and paths*, reported and never enforced; dangling *keys* would fail. |
| **Working tree** | clean, including untracked. **`fixtures/`** holds manual-check plans, deliberately outside `examples/` so the corpus glob never sees them (see §6 and D51) — and one of them is **load-bearing and frozen**: `wiscaway2026-08-08.json` is retained *because* it fails I7. |

**A commit gate is enforced, not merely available.** `tools/gate.py` writes `.gate-result.json`; a `PreToolUse` hook blocks any `git commit` unless that file exists, reads GREEN, and is **newer than every tracked file** — every tracked file, `.md` included, so a document edit made after the gate ran makes it stale. See §6.

---

## 2. THE OPEN QUEUE, in order

**The tiers are [`ROADMAP.md`](ROADMAP.md)'s and are also recorded in the plan (§ "the work, tiered").** Code does not self-classify. GREEN merges on green CI; **AMBER stops at the PR and Patrick's manual check is the merge condition**; RED does not start.

**The GREEN batch is done and merged.** What remains is AMBER and RED.

**A1 (D47) and A1b (D53) are DONE** — merged at PRs #17 and #18, each with its manual check passed and recorded verbatim on the PR. The queue now starts at A2.

1. **A2 — D11's RUNTIME z-order collapse. THE CURRENT ITEM, AND ITS FIRST DELIVERABLE IS THE MEASUREMENT, NOT A FIX.** It hangs `test_drag_split_macro_keeps_every_room_rectilinear` at the first drag, bisected to `geometry.py`, and the trigger is the **magnitude** of the z step (`×1.0` completes, `×Z_STACK_BAND` hangs); the work was reverted, so nothing of it is in the tree and it is **not reproducible from disk**. **The roadmap's instruction is explicit and is the first step: INSTRUMENT THE HANG WITH A BOUNDED EVENT COUNTER TO FIND THE CONSUMER OF THE z STEP. Do not choose constants that make the symptom go away.** The agreed rule (ruling 4) carries forward whole: z = `floor_term + stack_term + type_term`; the backdrop's −1e9 becomes a **type term**, not a magic number; `bring_to_front`'s full-scene max scan dies with it; the band arithmetic becomes **named constants** with `max(type_term) < STACK_BAND` and `max(stack_term) < FLOOR_BAND` written beside them and **pinned by a test**. Manual check: bring-to-front sticks; ghost floors stay behind the active floor; multi-floor banding unchanged.
   **CARRIED INTO A2 FROM A1b, AND IT IS A PRECONDITION ON THE READ-BACK.**
   **Multi-floor z is a capability that has never visibly worked** — every floor
   renders at one height (D50: every level reports `elevation_in 0.0`). That is
   the exact precondition for **PARASITIC REACH**
   ([`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)), which now has five instances
   behind it. So before anything changes, ask the question the pattern tells you
   to ask: **what currently works BECAUSE all floors collapse to one height?**
   Anything that does will present as a regression the moment z starts working,
   and it is to be found in the read-back rather than in Patrick's hands.

2. **A3 — D11's SERIALIZATION half.** No longer blocked: **ruling R‑B** (roadmap §2) decided that an *additive optional* field or enum value does not bump the document version, so a stacking index can be added at `schema_revision` without a v6. Still AMBER.
3. **D59 — the CHEAP TWELVE at document boundaries. SPLIT OUT OF D49 on 2026‑08‑09, on measured grounds.** A real plan was saved carrying an `I7`, nothing reported it, and the user met it later as a silent crash (D57). **I7 is one of the cheap twelve**, so a boundary check would have caught it *without* the deep set — and P1.2's O(n²)-per-edit cost objection, which has kept D49 unscheduled, does not touch this half at all: the cheap twelve are already deemed affordable per mutation under shadow mode. Its only open question is what the app does with the result, and D49's amendment already answers that for overlap in reasoning that carries. **AMBER, and it moves up the queue on evidence rather than preference.**
4. **A4 — D49, the deep checks at document boundaries. AMENDED 2026‑08‑07 — read the amendment, not the 2026‑08‑05 proposal it supersedes.** I11 speaks nowhere in the shipped app: deep-only *plus* shadow mode off by default compose into a hole neither has alone. Measured on one corrupt scene: `FP_VERIFY_DESIGN` unset → **the save wrote the file** with I5b ×1 and I11 ×3; `=1` → refused; `=deep` → refused. The ruling: **CHECK YES, FIX NO** (overlap's causes vary and every auto-repair silently changes drawn geometry; the one repairable cause is already fixed by welding on load — same reasoning as **D34**); **SAVE ASKS, IT DOES NOT REFUSE** (a deform-to-follow drag can transiently overlap, and a hard refusal traps the user with unsaveable work); and **the report must be ACTIONABLE** — rooms *and overlap area*, plus select-and-zoom. **Sequencing, measured:** the area does not exist in I11 today (a boolean from three terms, no number), computing it honestly **is D52's half 1**, and on the amendment's own driving case the true intersection is **0.0 sf** — so `planc1` is the acceptance case and `farmplace` is the silence case. Real behaviour change; will be felt.
5. **A5 — D41, the new simple-ring invariant.** Ruled at **R‑A**: a ring that visits a vertex twice is a *degeneracy*, not a crossing, so it gets its own invariant rather than widening I5b. **A read-back is required before starting** — which files in `examples/` fail it, deep-only or one of the cheap twelve, and the corpus-freeze diff for `symmetricP1.json`.
6. **A6 — Grid snap.** Three sub-rulings still RED (see §4 of the roadmap).
7. **Phase 5 — Landscape** (P5.1 site levels/categories/area accounting, P5.2 landscape wall types + gates, P5.3 site schedule fields + reports).

### The three records filed since the last re-cut — all on disk, none merely discussed

* **D50 — a level's elevation is DESTROYED by a load/save round trip.** `model.Floor` has only `name` and `reference`, so all three writers emit literals (`bridge.py:796`, `bridge.py:976`, `importer.py:184`). **The SCHEMA is not at fault** — `level` has carried `elevation_in` and `height_in` since P0.7. **The fault is destruction, not absence**, which is what makes it a defect rather than an unbuilt feature: `IN [('default',0.0,96.0), ('second',108.0,108.0)]` → `OUT [('default',0.0,96.0), ('second',0.0,96.0)]`. Nothing reports the loss; `check()` is clean either way. **Blocks Phase 7's Build Floor**, which must produce exactly this field. AMBER.
* **D51 — the census depends on the WORKING TREE, not the repository.** `tests/test_schema.py` globs `examples/*.json` off the filesystem and parametrizes `test_clean_design_validates` over what it finds, so an untracked or merely staged file changes `collected=`. Measured: 638 / RED with an uncommitted file present, 637 / green without. **Sharper form: with the commit hook in place, a file that is in no commit can block every commit in the repository** — which it did, for several hours. Committing the two plans closed that instance; **the hole itself remains open**, and three fixes are proposed with none implemented.
* **The `--stack` refusal for the 3D viewer, with its reasoning.** Ruled 2026‑08‑07 and recorded in **two** places: `floorplanner/viewer/VIEWER_NOTES.md` **§8** (the full argument) and **D50's Ruling** (the one-paragraph form). A rendering flag that invents a number the document does not contain is **a decision about the MODEL wearing a renderer's clothes**; it would make the picture stop being evidence (§4's whole argument for `--dump`); and the moment elevations are real the flag becomes a way to disagree with them. **`--explode` is not refused — it waits**, having nothing to space out until D50 closes. It is a ruling in the notes and the record, **not a defect record of its own**.

### `examples/farmplaceBIGmultifloor.json` — read this before touching `examples/`

**It still fails I11, and it is TRACKED.** Measured 2026‑08‑08: `check(deep=True)` → `["I11 rooms 'Lounge' and 'Toi' overlap"]`; `check(deep=False)` → `[]`. It was committed at **`83a3ccc`**, together with the `KNOWN_UNCLEAN` exemption; the working tree is clean and nothing is staged.

**The classification is on disk and is committed**: `KNOWN_UNCLEAN` in `tests/test_schema.py` is documented as being for **REAL PLANS carrying a known, recorded fault**, explicitly distinct from `planc1.v5.json`, which is *a fixture built to be dirty*. The entry names **D52** as the record that owns the fault, and D52's ruling reads *"Deferred as a FEATURE, 2026‑08‑07"*. `test_known_unclean_still_fails` asserts each listed file is schema-valid and **still carries its named fault**, so the list cannot become a place where failures go to be forgotten — `roundedMultifloor.json` was on it in the morning and came off it the same afternoon, after Patrick reshaped the two rooms so they no longer nest.

**What is worth confirming rather than assuming:** the record does not name who made that classification, so if the real-plan-vs-second-fixture question is still considered open, the answer currently in the repository is *real plan*, and it is load-bearing for the census, the corpus test and the exemption list.

* **D52 — room-inside-a-room has no representation, and I11 misreports the workaround.** `Toi` is a WC fully enclosed by `Lounge`; a single-ring outline cannot express a hole, so the drawing carves it out with a **zero-width slit**, and I11's **vertex-average** centroid then lands inside the closet — `_pip(Toi centre, Lounge)` False, edge crossings none, `_pip(Lounge "centre", Toi)` **True**, which is the entire failure. Two independent halves: **I11's centroid is wrong regardless of this plan** (same family as D41 — an invariant meeting a non-simple ring and reporting the wrong thing), and **room-in-room has no representation** (`holes` exists in the schema and is implemented nowhere). Five repairs were attempted and measured; each changes what the plan *means*, which is the author's call.

**The other open records**, not queued as tasks but live: **D44** (an accepted limit), **D45**, **D46**. **Thirteen open in total: D11, D41–D52** *(D43, D48 and D42 have shipped their first steps and remain open for the rest; D27 closed with the Windows CI leg)*.

**Patrick will ask separately for the consolidated feature-and-phase document. Do not start it unprompted.**

---

## 3. What Phase 4 settled, in one place

- **Rooms are movable units** (P4.2): `extract_room` lifts a room out of the network (I12 by construction), `join_room` welds it back; a placed room's label-drag *is* extract → move → join.
- **Groups move the real items** (P4.5): `duplicate_wall` is dead, all four `group() is None` guards retired (**visibility before permission**, one sub-commit each), `merge_all`-on-ungroup gone, the `rigid` carve-out retired with its expired justification kept verbatim. Group the whole 20-room plan, move, ungroup → **189 → 189 scene items, zero new objects**.
- **Deform-to-follow** (D23, ruled §2a): a room the band only partly took follows the corners that moved — *because the corner moved*, not because anything holds it back.
- **One gather, three gestures**: `rooms_holding` (in `rooms.py`) is the single definition used by the group bake, Align to grid and Distribute.
- **The P3.1 split-on-write shim is gone** — 178 lines. The operation survives as **`WallItem.detach_end`**. **The guarantee moved to the gate: `end_assign=0`.**
- **Defects closed in Phase 4:** D17, D25, D30, D34, D35, D13 (drag half), D36, D37, D3, D11a, D23. **Filed not fixed:** D47, D48, D49, plus D41, D42, D43, D44, D45.

---

## 4. How to read this repo's record

Which document answers which question:

| the question | the document |
|---|---|
| *What is the architecture? What are the house rules?* | **`CLAUDE.md`** |
| *What is every document, and which are authoritative?* | **[`README.md`](README.md)** — the map. Start here when unsure. |
| *What may proceed without Patrick, and what may not?* | **[`ROADMAP.md`](ROADMAP.md)** — the tier charter (GREEN / AMBER / RED), the autonomy policy, and rulings **R‑A** and **R‑B**. |
| *What rules bind the work?* — census doctrine, gate discipline, what a receipt is, how vacuity is detected | **[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)**. Extracted from the plan because the rules outlive the migration. |
| *What is planned, and what is done?* | **[`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md)** — Status table, phase specs, risk register, sequencing rationale, and the roadmap's tiers recorded on disk. |
| *What happened, and what proved it?* | **[`progress/`](progress/)** — the log, split by phase, verbatim and contemporaneous. Index at [`progress/README.md`](progress/README.md). |
| *What is broken, and what was decided about it?* | **[`defects/`](defects/)** — one record per file, `D23` is the permanent key. Index at [`defects/INDEX.md`](defects/INDEX.md); field rules and taxonomy at [`defects/README.md`](defects/README.md). |
| *What did an agent report, and what was ruled?* | **[`handoff/`](handoff/)** — the mailbox. Chat is not the record. |
| *What was measured, and how do I reproduce it?* | **[`evidence/`](evidence/)** — cited by records, never inlined. |
| *What was the plan before this one?* | **[`superseded/`](superseded/)** — kept because it holds material found nowhere else, **not** because it is safe to skip. |

**Reading order for a fresh session:** `CLAUDE.md` → this file → [`README.md`](README.md) → [`ROADMAP.md`](ROADMAP.md) → then whichever row above the task needs.

**`docs/CODE_REVIEW_v2.md` is still worth reading** for §1 (module verdicts) and §2 (the five structural findings). Its §3 is now a pointer into `defects/`.

---

## 5. The rules that bind the work

Unchanged, and all in [`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md): **a green signal is only evidence about what it measures** (with the artifact→check table); **retire visibility before permission**, and enumerate a view's consumers first; **a task that changes what an operation does owes a differential receipt** alongside the green gate; **vacuity has three shapes** (plus UNSATISFIABLE, its mirror), only tautology is machine-detectable; **negative assertions are where vacuity concentrates**, so preconditions are mandatory there; **verify a probe — and a record edit — actually landed**; **measure survival justifications** like any other claim; **grep for identifiers, parse for shapes**; **in a test, call the production predicate rather than restating it**; and **a tidy-up pass that outlives its mess only touches things nobody asked it to**.

**Added since the docs refactor:**

- **A content correction discovered during a structural move is NEVER folded into the move** — it is the next commit, with its own receipt.
- **A lint that fails on correctly-recorded history is a lint that gets disabled.** Dangling *keys* fail the gate; dangling *links and paths* are reported and never enforced.
- **A boundary belongs at the instrument.** **Annotate, do not rewrite** — applied to documents, not just code.
- **TRUNCATION INVITES FABRICATION** — `| tail` has caused two different failures. Never truncate a gate, a census or any output you are about to quote: read it whole, or have the tool hand you the text. **`tools/gate.py --trailer` reprints the stored block** so the numbers never pass through a human. `--quick` and `--deep` deliberately do not write that block, so neither can be quoted as a full-mode run.
- **The GREEN criterion was amended 2026‑08‑07, and the amendment is Patrick's.** It now reads *"no new semantics, and nothing the user must learn"* rather than *"no user-visible behaviour change"* — because the old wording contradicted the roadmap's own G4 acceptance. A report that fires **only when something is already wrong**, reusing an existing message, adds nothing to learn. A new mode, a new gesture, a changed default, or a message that can fire on **correct** work all still fail the test.
- **An append-only shared file serialises parallel branches.** The GREEN batch's only merge conflicts were in `docs/progress/side-tasks.md`; the source files never collided. **Before two agents run at once, progress entries move to per-task files** (`progress/tasks/<task>.md`, index generated, mirroring `defects/INDEX.md`). Deliberately not done yet — **a precondition on concurrency, not a debt**.

---

## 6. Things that will waste your time if you don't know them

- **A `git commit` is BLOCKED unless a fresh green gate result exists on disk.** `tools/gate.py` writes `.gate-result.json` (gitignored) at the end of a full-mode run; `.claude/hooks/verify_gate.py` checks it exists, reads GREEN, and is **newer than every tracked file** — **including `.md` files**, so *edit the documents first, then gate, then commit*. The hook reads the RESULT FILE, never the commit message.
- **ONE CALL CANNOT BOTH RUN THE GATE AND COMMIT**, and the hook blocks that shape outright: `PreToolUse` fires *before* the command, so the verdict it checks is the previous run's. **`--trailer` is exempt** — it runs nothing and writes nothing, and it is exactly the command that belongs beside a commit. Run the gate in its own call, read the verdict, then commit in a separate one.
- **A `NameError` inside a Qt virtual override PRESENTS AS A SEGFAULT.** PyQt6 aborts the process on an unhandled Python exception in an override, so the run dies with **no traceback and no pytest summary** — it just stops mid-line. Cost several runs at A1b, where the missing name was a new constant. **`config.py` has an `__all__`**, so a constant added there is invisible to the star-importing modules until it is *listed*. If a headless run dies silently, wrap the handler and re-raise before suspecting Qt.
- **`QRubberBand.show()` on an offscreen viewport kills the process** — pre-existing, reproducible on `main`, and why no headless test has ever covered the Ctrl+drag band. A1b works around it by creating the band on the first *move* rather than on the press.
- **A running app keeps the code it imported** — the status-bar version label shows the launch identity; restart before re-testing.
- **`gh` is not on `PATH` in PowerShell**: `& "C:\Program Files\GitHub CLI\gh.exe"`. It *is* on PATH under the bash tool.
- **`.gitattributes` forces LF**, so the CRLF phantom-diff class is closed structurally — but the working tree still checks out CRLF, so multi-line `\n` patterns in ad-hoc scripts still match nothing. Use `tools/record.py`, which handles it once and verifies.
- **`git commit` after `git add` commits the WHOLE index** — use `git commit <paths>` when anything else is staged.
- **The census reads the WORKING TREE (D51), and it BIT AGAIN on 2026‑08‑08.** A stray `.json` in `examples/` changes `collected=` and can turn the gate red, which — with the commit hook — **blocks every commit in the repository**. It happened to `fragment2room.json`: saved into `examples/` as a manual-check plan, it took the census 639 → 640, tripped I11 (its two rooms overlap **by design** — that is the fixture), and held the gate RED until it was moved. Check `git status --untracked-files=all` before believing a census disagreement is real.
- **A plan for a MANUAL CHECK goes in `fixtures/`, never `examples/`.** `examples/` is the corpus: schema-validated, frozen, and a change there needs a declared justification. `fixtures/` is outside both corpus tests by construction, so a check plan may be edited freely and can be as dirty as the check needs. See [`../fixtures/README.md`](../fixtures/README.md).
- **Macro replay geometry matters**: a `.fpm` replays correctly only at the window geometry it was recorded at; each pinned test states which.
- **The suite's console is cp1252** — no non-ASCII in test output.
- **Migrating the records to GitHub Issues has a precondition**: none of the 15 labels or 20 milestones exist yet. `tools/defects_to_github.py --create-labels --yes` first; `--execute` refuses without them.
