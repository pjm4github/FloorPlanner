# Session snapshot — read this first

**Re-cut 2026‑08‑06, on `main` @ `ac93afc`, immediately after the docs-refactor merge (PR #11).** **PHASE 4 IS COMPLETE.** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

> **The record moved on 2026‑08‑06 and this file's old reading order is dead.** The Working agreement, the progress log and the defect register left the two documents that had absorbed them. **[`README.md`](README.md) is the map** — what each document is, which decide things, which are history. Read §4 below for the short version, and the map for the whole.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` @ `ac93afc` — no work branch open; `docs-refactor` merged and pruned, local and remote. |
| **`main`** | P4.1, P4.1b, P4.2, P4.3, P4.4 and **P4.5** all merged and ticked (PRs #2, #3, #4, #5, #6, **#10**); the 3D viewer packaged and its popup merged (PRs #4–#8); the **docs refactor** merged (**PR #11**, merge commit `ac93afc`, 14 sub-commits). |
| **Census** | **633 collected** (625 passed, 7 deselected, 1 xfailed), ruff clean, `vacuous=0`, **`end_assign=0`**, every sum reconciling in all three modes. |
| **Records** | **50 defect records** — 11 open, 39 closed. `python tools/gate.py --docs` GREEN. |
| **CI on `main`** | green — ruff, records, py3.10, py3.13, deep invariants (run `31132161605`). |
| **Working tree** | clean. |

**A commit gate is now enforced, not merely available.** `tools/gate.py` writes `.gate-result.json`; a `PreToolUse` hook in `.claude/settings.json` blocks any `git commit` unless that file exists, reads GREEN, and is **newer than every tracked file**. See §6.

---

## 2. THE OPEN QUEUE, in order

Everything here was carried out of Phase 4 **deliberately and with a record**, not dropped. Each is now a file: `docs/defects/NNNN-*.md`, indexed at [`defects/INDEX.md`](defects/INDEX.md).

1. **D47 — `fragment` must produce floating rooms via `extract`. THE FIRST TASK, ahead of grid snap.** `room_boolean` (`mainwindow.py:982‑996`) builds a complete wall loop per region with no dedup, then groups it; nothing welds them. **This is a SECOND duplication site that `duplicate_wall`'s death never reached, so P4.5's retirement of copy-on-group is incomplete and the record states by how much.** Measured (`docs/evidence/defect23-fragment.json`, reproduce with the probe beside it): 20 distinct `Vertex` objects on 10 geometric points; `room_owns_walls` **false for all nine (group, room) pairs**; dragging a fragment clear moves **4 of 4 walls and 0 of 16 outline corners**; four dashed edges each with a real wall on them; `check(deep)` CLEAN throughout and **the save succeeds**. Pinned by `test_fragment_groups_each_piece_with_its_own_walls`, the suite's only remaining `xfail`, which flips when this lands.
2. **D11's RUNTIME z-order collapse — in P4.5's charter and it did NOT land.** Only 11a did. It hangs `test_drag_split_macro_keeps_every_room_rectilinear` at the first drag, bisected to `geometry.py`, and the trigger is the **magnitude** of the z step (`×1.0` completes, `×Z_STACK_BAND` hangs); the work was reverted, so nothing of it is in the tree and it is **not reproducible from disk**. **Next step: instrument the drag with a bounded event counter to find the consumer — do not choose constants to avoid a symptom.** **The agreed rule (ruling 4) carries forward whole:** z = `floor_term + stack_term + type_term`; the backdrop's −1e9 becomes a **type term**, not a magic number; `bring_to_front`'s full-scene max scan dies with it; and the band arithmetic becomes **named constants** with `max(type_term) < STACK_BAND` and `max(stack_term) < FLOOR_BAND` written beside them and **pinned by a test**. **The SERIALIZATION half is separately blocked** on a schema ruling with version implications (v5 has no stacking-index field on room, wall, furnishing or group, and all four set `additionalProperties: false`), and returns to Patrick as its own decision.
3. **D48 — the invariants have never checked the scene the user edits.** `design_from_scene` **welds on the way out**, so a scene whose corners are not shared at all emits a document that passes all fifteen (measured: 20 → 10 vertices, 16 → 12 walls, `merged=4`, `check(deep)` CLEAN). D44's sibling one layer down. Proposed instrument, to be scoped: a **scene-level** check that geometric coincidence implies identity.
4. **D49 — I11 speaks nowhere in the shipped app.** Deep-only *plus* shadow mode off by default compose into a hole neither has alone, and I11 is the invariant that caught the real `planc1.json` corruption this migration was started for. Measured on one corrupt scene: `FP_VERIFY_DESIGN` unset → **the save wrote the file** with I5b ×1 and I11 ×3; `=1` → refused; `=deep` → refused. Proposed fix: run the deep set at **document boundaries** (load, save) regardless of shadow mode, keeping the cheap twelve for editing.
5. **Grid snap.**
6. **Phase 5 — Landscape** (P5.1 site levels/categories/area accounting, P5.2 landscape wall types + gates, P5.3 site schedule fields + reports).

**The other open records**, not queued as tasks but live: **D27** (the Windows CI half), **D41**, **D42**, **D43**, **D44** (an accepted limit), **D45**, **D46**. Eleven open in total: **D11, D27, D41–D49**.

**D40 and D3 closed at the docs refactor's step 10**, each in its own commit with a receipt — D40's condition had been met on 2026‑08‑03 and never ticked; D3's cell still said "is still open" after P4.5 closed it.

**Patrick will ask separately for the consolidated feature-and-phase document. Do not start it unprompted.**

---

## 3. What Phase 4 settled, in one place

- **Rooms are movable units** (P4.2): `extract_room` lifts a room out of the network (I12 by construction), `join_room` welds it back; a placed room's label-drag *is* extract → move → join.
- **Groups move the real items** (P4.5): `duplicate_wall` is dead, all four `group() is None` guards retired (**visibility before permission**, one sub-commit each), `merge_all`-on-ungroup gone, the `rigid` carve-out retired with its expired justification kept verbatim. Group the whole 20-room plan, move, ungroup → **189 → 189 scene items, zero new objects**, against the review's ≥106 duplicate walls and ≥149 duplicate openings on that gesture.
- **Deform-to-follow** (D23, ruled §2a): a room the band only partly took follows the corners that moved — *because the corner moved*, not because anything holds it back. Clipped band: Garage **0 of 9 → 7 of 9** corners, PKT Off 0 → 5, Util 0 → 3.
- **One gather, three gestures**: `rooms_holding` (in `rooms.py`) is the single definition used by the group bake, Align to grid and Distribute, and it widens to every room **and every wall** holding a moved corner.
- **The P3.1 split-on-write shim is gone**: `p1`/`p2` setters, `_carry_anchors`, `Vertex.moved_to`, `split_count`, `split_sites`, `note_vertex_splits` — 178 lines. The operation survives as **`WallItem.detach_end`**, named for which of the two things it is (`Vertex.at` = a new corner; `relocated_to` = the same corner moved). **The guarantee moved to the gate: `end_assign=0`.**
- **Defects closed in Phase 4:** D17, D25, D30, D34, D35, D13 (drag half), D36, D37, D3, D11a, D23. **Filed not fixed:** D47, D48, D49, plus D41, D42, D43, D44, D45.

---

## 4. How to read this repo's record

**The structure changed on 2026‑08‑06 under anyone who knew the old one.** Which document answers which question:

| the question | the document |
|---|---|
| *What is the architecture? What are the house rules?* | **`CLAUDE.md`** |
| *What is every document, and which are authoritative?* | **[`README.md`](README.md)** — the map. Start here when unsure. |
| *What rules bind the work?* — census doctrine, gate discipline, what a receipt is, how vacuity is detected | **[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)**. Extracted from the plan because the rules outlive the migration. |
| *What is planned, and what is done?* | **[`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md)** — now 586 lines: Status table, phase specs, risk register, sequencing rationale. |
| *What happened, and what proved it?* | **[`progress/`](progress/)** — the log, split by phase, verbatim and contemporaneous. Index at [`progress/README.md`](progress/README.md). |
| *What is broken, and what was decided about it?* | **[`defects/`](defects/)** — one record per file, `D23` is the permanent key. Index at [`defects/INDEX.md`](defects/INDEX.md); the field rules and the taxonomy at [`defects/README.md`](defects/README.md). |
| *What did an agent report, and what was ruled?* | **[`handoff/`](handoff/)** — the mailbox. Chat is not the record. |
| *What was measured, and how do I reproduce it?* | **[`evidence/`](evidence/)** — cited by records, never inlined. |
| *What was the plan before this one?* | **[`superseded/`](superseded/)** — kept because it holds material found nowhere else, **not** because it is safe to skip. |

**Reading order for a fresh session:** `CLAUDE.md` → this file → [`README.md`](README.md) → then whichever row above the task needs. The four documents this file used to send you to still exist; two of them are now a tenth of their old size because the record left them.

**`docs/CODE_REVIEW_v2.md` is still worth reading** for §1 (module verdicts) and §2 (the five structural findings). Its §3 is now a pointer into `defects/`.

---

## 5. The rules that bind the work

Unchanged, and all in [`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md): **a green signal is only evidence about what it measures** (with the artifact→check table); **retire visibility before permission**, and enumerate a view's consumers first — those that scope themselves by it are permission grants in disguise; **a task that changes what an operation does owes a differential receipt** alongside the green gate; **vacuity has three shapes**, only tautology is machine-detectable; **negative assertions are where vacuity concentrates**, so preconditions are mandatory there; **verify a probe — and a record edit — actually landed**; **measure survival justifications** like any other claim; **in a test, call the production predicate rather than restating it**; and **a tidy-up pass that outlives its mess only touches things nobody asked it to**.

**Added by the docs refactor, and they generalise:**

- **A content correction discovered during a structural move is NEVER folded into the move** — it is the next commit, with its own receipt. Keeps the move's verbatim receipt intact and makes the correction visible. (`defects/README.md` states it; D40 and D3 are the worked examples.)
- **A lint that fails on correctly-recorded history is a lint that gets disabled.** A register that names deleted code is doing its job. Hence: dangling *keys* fail the gate, dangling *links and paths* are reported and never enforced.
- **A boundary belongs at the instrument.** `ref_audit.py` had a hole its docstring did not admit, so a second dangling pointer was found by eye. The pattern set is now versioned and `--compare` refuses a cross-version baseline.
- **Annotate, do not rewrite** — applied to documents, not just code.

---

## 6. Things that will waste your time if you don't know them

- **A `git commit` is now BLOCKED unless a fresh green gate result exists on disk.** `tools/gate.py` writes `.gate-result.json` (gitignored) at the end of a full-mode run; `.claude/hooks/verify_gate.py` checks it exists, reads GREEN, and is **newer than every tracked file**. Run `python tools/gate.py` *after* your last edit and *before* committing. The hook reads the RESULT FILE, never the commit message — three of the four incidents behind it were a claim about a gate rather than a gate.
- **A running app keeps the code it imported** — the status-bar version label shows the launch identity; restart before re-testing.
- **`gh` is not on `PATH` in PowerShell**: `& "C:\Program Files\GitHub CLI\gh.exe"`. It *is* on PATH under the bash tool.
- **`.gitattributes` forces LF**, so the CRLF phantom-diff class is closed structurally — but the working tree still checks out CRLF, so multi-line `\n` patterns in ad-hoc scripts still match nothing. Use `tools/record.py`, which handles it once and verifies.
- **`git commit` after `git add` commits the WHOLE index** — use `git commit <paths>` when anything else is staged.
- **Macro replay geometry matters**: a `.fpm` replays correctly only at the window geometry it was recorded at; each pinned test states which.
- **The suite's console is cp1252** — no non-ASCII in test output. Tools that print corpus text transliterate on the way out (`ref_audit.py`) or reconfigure stdout to UTF-8 when the output is a command rather than a report (`defects_to_github.py`).
- **Migrating the records to GitHub Issues has a precondition**: none of the 15 labels or 20 milestones exist yet. `tools/defects_to_github.py --create-labels --yes` first; `--execute` refuses without them.
