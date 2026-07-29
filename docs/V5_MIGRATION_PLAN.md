# v5 migration plan — staged, gated, executable

**Target:** `floorplanner/design/design-schema.v5.json` (vendored at P0.7; pointer at `docs/design-schema.v5.md`) · **Review:** `docs/CODE_REVIEW_v2.md` · **Model rationale:** `docs/DESIGN_MODEL_v5.md`

Seven phases. Every task is small enough to finish and verify in one sitting, and **every task ends on a green gate**: `python -m ruff check .` then `python -m pytest -ra`, both clean, before the next task starts. `main` stays shippable throughout except during Phase 3, which runs on a branch.

---

## Working agreement

This plan is written to be executed by Claude Code in the repo, one task at a time.

**The loop.** For each task: Claude Code reads the task below, implements it, runs the gate, and appends one line to the **Progress log** at the bottom of this file. Then paste the result back here — I verify it against the acceptance criteria, tick the box in the status table, and hand over the next task.

**What I need back from each run**, so I can mark it honestly rather than optimistically:

```
P0.3  <done|blocked>
ruff:    <clean | N findings>
pytest:  <N passed, M failed, K xfailed, S skipped in T.Ts>
files:   <added/changed>
notes:   <anything surprising — especially a test you had to change and why>
```

**A changed test is a red flag, not a detail.** If a task required editing an existing assertion, say so explicitly. Half this migration's risk lives in tests being quietly relaxed to match new behaviour.

**Prompt shape for Claude Code:**

> Read `docs/V5_MIGRATION_PLAN.md`. Do task **P0.3** exactly as specified — no adjacent refactoring, no drive-by cleanups. When done, run `python -m ruff check .` then `python -m pytest -ra`, and append your result line to the Progress log.

**P0.0 first** (below) adds a pointer in `CLAUDE.md` so Claude Code finds this plan without being told each time.

### The gate is `ruff check .` over the whole tree — settled 2026‑07‑26

P0.1 found the gate red at baseline: 23 findings, all in `tools/` and `docs/_superseded/` scaffolding committed during the design sessions, **0 in `floorplanner/` or `tests/`**. Four responses were on the table; the deciding fact is that **`.github/workflows/ci.yml:26` runs `python -m ruff check .` over the whole tree**. Narrowing the local gate to `floorplanner tests`, or excluding `tools/`, would make the local gate disagree with CI and leave CI red on the next push — a local gate that is greener than CI is worse than no gate.

So: the gate stands as written, and the 23 findings were **fixed at source** (mechanical: `l` → `lv`, unused loop vars prefixed `_`, `zip(..., strict=False)`, semicolons split, the `math` import hoisted). All three tools re-verified afterwards to produce byte-identical output. `docs/_superseded/` was moved to `_to_delete/` — dead drafts kept alive behind a lint exclusion is exactly how scaffolding rots.

**Standing rule for the rest of the migration:** scaffolding in `tools/` is held to the same lint bar as shipped code, because CI does not distinguish them.

**Corollary found at P0.2** — the divergence cuts both ways. `_to_delete/` was untracked, so the *local* gate went red while CI would have been green. Same principle: the two must agree. `_to_delete/` is now gitignored, which (because ruff respects `.gitignore` for discovery) removes it from both. That directory exists only because the Cowork device bridge cannot delete files on your machine; it is a transfer buffer that should always be empty, and Claude Code should empty it when it appears.

### Three more conventions, settled at P0.2

**Commit at every green gate.** One commit per task, message `P0.x — <task title>`. A 40-task migration with no commits has no rollback points; with one per task, every gate is a place to return to. Nothing is pushed unless asked.

**In a multi-part task, run the FULL gate before each commit, not just at the end.** Found at P0.5: fix 4 was committed after running only `test_selection.py` and turned out to break a test in a different file. Five sub-fixes means five full-suite runs. A targeted run tells you the fix works; only the full suite tells you what else it touched.

**`Touches` lists are hints, not contracts.** P0.2's list named `test_io.py` (which references none of the removed names) and missed `test_inventory.py` and `test_walls.py` (which do). Follow the code, do the task, and report the divergence in the log — that is what happened, and it is the correct behaviour. I write these lists from static analysis; the compiler is a better authority than I am.

**Annotating a doomed assertion means naming the *specific* task**, not "Phase 3". If no task actually retires it, say so rather than inventing one.

### Push policy — settled at P0.3

**Commit per task; push per phase.** With one exception: **push once now, at the end of Phase 0's safety net.**

The reason is that `.github/workflows/ci.yml` triggers on push and PR only, so **nothing in this migration has ever been validated by CI.** Local runs are py3.13 on Windows; CI is py3.10 *and* py3.13 on `ubuntu-latest`. Those differ in ways that matter — Qt offscreen font metrics, path handling, and py3.10 syntax support. Discovering a py3.10 break at P1.4 means bisecting a stack of commits instead of reading one failure.

Pushing per *task* is the wrong granularity: 40 pushes is noise, and a phase boundary is the natural "coherent, shippable state". Pushing per *phase* after this first one is the rule. Phase 3 runs on `v5-topology` and pushes there.

**Before the first push, the timing tests need a marker of their own** — see P0.3b step 3. Ratio assertions on shared CI runners flap; that is a well-known false-positive source and it would poison the signal we just built.

### Doc edits are Cowork's, committing is Claude Code's — settled at P0.6

The Cowork device bridge writes into the working tree but **cannot run git**. So every doc edit handed back (a re-ticked status table, a new rule, an amendment) sits **uncommitted** until Claude Code commits it — and any `git checkout` / `restore` / `stash` in between silently discards it. Root cause of the P0.3b/P0.4/P0.5 checkbox drift: the ticks were written to the working tree but never committed, then overwritten.

Two rules:

**Commit handed-back doc edits immediately, as a doc-only commit, before running any git that could discard them.** A doc edit you can see on disk but have not committed is one `checkout` away from gone.

**Verify the status table on disk, not from a summary — including your own.** `grep '☐\|☑' docs/V5_MIGRATION_PLAN.md` before claiming a task is ticked. A summary (yours or mine) is not the file. And if a Progress-log entry goes missing after a hand-back, that is a regeneration bug on my side — say so rather than committing the lossy version.

**Root cause of the three doc-loss incidents — identified at P0.6, and it is Cowork's.**
`device_stage_files` reports the device's true file size but can serve a *stale*
container-side copy from an earlier stage. Measured: the tool reported 46,942 bytes
while the copy it produced was 38,760 — a version several commits old. Editing that
stale copy and writing it back overwrites newer work with older content, which is
exactly the damage seen at P0.4, P0.5 and P0.6.

**Consequence: Cowork no longer edits this file, or CODE_REVIEW_v2.md.** Plan and
review changes are handed to Claude Code as explicit edit instructions; Claude Code
applies them, commits, and grep-verifies on disk. One extra round-trip, and the only
channel that has destroyed work in this project is closed.

### The gate must be checked, not printed — settled at P3.6

**`python -m pytest -q | tail -1 && git commit` does not gate anything.** A
pipeline's exit status is the LAST command's, so `&&` was testing `tail`, which
always succeeds. Every gate run in that shape reported its counts honestly and
enforced nothing — which is how P3.6(3) came to be committed with **two errors**
in the ON and DEEP runs, visible in the very output that was pasted into the
commit message.

The errors were real and were shadow mode doing its job (`I7: 0 -> 1`, an
opening pushed off its wall by a width change). They were found and fixed
minutes later, so nothing shipped broken — but they were found by *reading* the
output, which is exactly the manual step the gate exists to replace.

**Run the command, capture its status, then print.** A helper that stores the
output, keeps `$?`, echoes the tail and returns the status; or simply
`set -o pipefail`. Never `... | tail -N && <next step>`.

### Destructive experiments run in a worktree, or after a WIP commit — settled at P3.5

**Never against uncommitted work.** `git checkout <file>` has no undo. At P3.5 it
was used to revert a deliberate break-it-to-prove-the-test experiment (making
the two defect-8 regressions fail on purpose, to confirm they catch what they
name — which is the right thing to do) and it took that file's *uncommitted*
work with it.

The solution was already in use in the same task: the P3.5 perf comparison ran
the old code in a `git worktree`, which cannot touch the working tree at all.
So: **`git worktree add --detach <path> <ref>` for anything that needs the code
in another state, or commit first and experiment on top.** The P3.5-followup
verified its five new tests against pre-fix code exactly that way, and found
that one of them passes on both sides — which is a finding the experiment only
surfaces if it is safe enough to run.

The doc-edit rule below is the same rule for a different asset. Stated once
here so it does not have to be re-learned per file type.

### A checkpoint is not complete until its handoff spec is committed — settled at P3.3

**Session-end summaries and hand-off prompts are chat, and chat is not the record.**
The P3.3 boundary proved it: the "five settled points" that fully specified the task
existed **only in conversation**. The commit that was supposed to carry them
(`3d6d32e`) changed exactly two lines — the defect 12a row and the P2.3 regression
row — and the Progress log still ended at P3.2. Only the read-back verification
caught it.

**So: before ending a session mid-task, commit the spec** — into the Progress log or
the task text — **then summarize.** The summary describes what was committed; it is
never the thing itself.

And the read-back is the check that makes the rule enforceable, so it stays: **quote
what disk supports, name what it doesn't, proceed on the verified subset.** A number
that cannot be found on disk is not quoted back as though it were — at P3.3 the
"72 splits" figure appeared nowhere in the repo, and saying so is what surfaced the
gap rather than papering over it.

---

## Status

| | Task | Gate |
|---|---|---|
| ☑ | **P0.0** Point `CLAUDE.md` at this plan | ruff |
| ☑ | **P0.1** Record the green baseline | ruff + pytest |
| ☑ | **P0.2** Decouple tests from private names | ruff + pytest |
| ☑ | **P0.3** Scaling harness | + `pytest -m slow` |
| ☑ | **P0.3b** Add selection-building to the harness | + `pytest -m slow` |
| ☑ | **P0.4** Characterization tests (xfail where broken) | ruff + pytest |
| ☑ | **P0.5** Five free bug fixes | ruff + pytest |
| ☑ | **P0.6** Cheap render wins | + P0.3 ratios |
| ☑ | **P0.7** Vendor schema + validator; CI validates `examples/` | ruff + pytest |
| ☑ | **P1.1** `design/model.py` — dataclasses | ruff + pytest |
| ☑ | **P1.2** `design/validate.py` — I1–I14 | ruff + pytest |
| ☑ | **P1.3** `design/topology.py` — weld/planarize/trace | ruff + pytest |
| ☑ | **P1.3b** Fix defect 18 (`_inner_faces` winding) + corpus diff | ruff + pytest |
| ☑ | **P1.4** `design_from_scene()` | ruff + pytest |
| ☑ | **P1.5** `apply_design_to_scene()` | ruff + pytest |
| ☑ | **P1.6** `--verify-design` shadow mode; suite runs with it on | ruff + pytest ×2 |
| ☑ | **P2.1** Load path: v1–v4 migrate + dirty + report; v5 direct | ruff + pytest |
| ☑ | **P2.2** Save writes v5; legacy export | ruff + pytest |
| ☑ | **P2.3** Undo snapshots the v5 dict | ruff + pytest |
| ☑ | **P2.4** Convert the corpus and the tooling | ruff + pytest |
| ☑ | **P2.5** Split `MainWindow` IO/CSV/image/floors out | ruff + pytest |
| ☑ | **P3.1** Vertex table live; `WallItem` holds `v1`/`v2` | branch, ruff + pytest |
| ☑ | **P3.2** `RoomItem.outline`; drop `perimeter_corners` | ruff + pytest |
| ☑ | **P3.3** Wall move = move vertices + split rule | ruff + pytest |
| ☑ | **P3.4** Topology ops replace coalesce/weld/fracture | ruff + pytest |
| ☑ | **P3.5** Delete the detection engine | ruff + pytest |
| ☐ | **P3.6** Opening anchors — *code complete; tick blocked on **defect 28 → resolution pending corpse table + re-certification**. Defect 26 (the crash) is FIXED. Ticks when DEEP runs green 10/10 under the machine trailer.* | ruff + pytest |
| ☐ | **P3.7** Delete `OpenWall` | ruff + pytest |
| ☐ | **P3.8** Perf verification vs P0.3 · **+ split-on-write exit survey** | ratios recorded |
| ☐ | **P4.1** Delete-wall keeps the room | ruff + pytest |
| ☐ | **P4.2** Extract / join | ruff + pytest |
| ☐ | **P4.3** Shuffle mode | ruff + pytest |
| ☐ | **P4.4** Concept rooms, `nominal_size`, duplicate-as-template | ruff + pytest |
| ☐ | **P4.5** Group semantics + z-order collapse | ruff + pytest |
| ☐ | **P5.1** Site levels, categories, area accounting | ruff + pytest |
| ☐ | **P5.2** Landscape wall types + gates | ruff + pytest |
| ☐ | **P5.3** Site schedule fields + reports | ruff + pytest |
| ☐ | **P6.1** `QUndoStack` + commands | ruff + pytest |
| ☐ | **P6.2** Retire snapshot undo | ruff + pytest |
| ☐ | **P6.3** Scene index + viewport update final pass | ratios recorded |

---

# Phase 0 — Baseline, safety net, free wins

*No file-format change. No user-visible behaviour change except the bug fixes.*

### P0.0 — Point `CLAUDE.md` at this plan
**Do.** Add to `CLAUDE.md` after the Architecture section:

```markdown
## v5 migration (in progress)
The file format and domain model are moving to `floorplanner/design/design-schema.v5.json` (vendored at P0.7; pointer at `docs/design-schema.v5.md`).
Read `docs/V5_MIGRATION_PLAN.md` before changing walls/rooms/items/mainwindow —
it says which code is being deleted and in which phase. Do not add new callers of
`detect_room`, `refresh_rooms`, `bind_room_walls`, `coalesce_*`, `weld_all` or
`OpenWall`; they are all scheduled for removal in Phase 3.
```
**Acceptance.** `CLAUDE.md` mentions the plan; no code change.

### P0.1 — Record the green baseline
**Do.** Run `python -m ruff check .`, then `python -m pytest -ra --durations=15`, then `python -m pytest --quick`. Record in the Progress log: pass/fail/xfail/skip counts, wall-clock for the full run and the quick run, and the 15 slowest tests.
**Why.** Every later "still green" claim is meaningless without this number. The slowest-15 list also tells us which tests Phase 3 will speed up.
**Acceptance.** Numbers in the log. If anything is already failing, **stop and report** — do not fix it as part of this task.

### P0.2 — Decouple tests from private names
**Touches.** `FloorPlanner.py:155‑160`, `tests/test_coalesce.py`, `tests/test_view.py`, `tests/test_groups.py`, `tests/test_rooms.py`, `tests/test_io.py`, `tests/test_selection.py`.
**Do.** Remove the four private re-exports (`_money`, `_WallBBoxIndex`, `_coalesce_all_impl`, `_coalesce_wall_impl`) from the shim. Tests that need them import from the submodule directly (`from floorplanner.walls import _coalesce_all_impl`). Where a test asserts on a private attribute that Phase 3 deletes (`view._zoom_accum`, `g._angle`, `room._detect_sig`, `dup._path`, `win._sel_order`), add a comment naming the phase that will retire it — do **not** rewrite the assertion yet.
**Acceptance.** Suite green; `grep -n "^from floorplanner" FloorPlanner.py` shows no underscore names.
**Why now.** Phase 3 deletes `_coalesce_*` and `_WallBBoxIndex` outright. If the shim still advertises them, the deletion breaks the public API instead of an internal one.

### P0.3 — Scaling harness
**Touches.** `tests/test_scaling.py` (new).
**Do.** Build an *n*×*n* grid of walled, named rooms with a door and a window per room and two furnishings, at *n* and 2*n* (start n=4 → 8, i.e. 16 → 64 rooms). Time four operations: `group_selected`, group drag + `bake`, `ungroup_selected`, `rebuild_all_walls`. Mark `@pytest.mark.slow`. Assert each ratio `t(2n)/t(n) < 8` (sub-quadratic in room count; quadratic would be ~16). Print the raw milliseconds so the numbers are visible in `-ra` output.
**Acceptance.** Test runs and prints. **Record the current ratios in the log even if they fail the assertion** — if grouping is already quadratic, mark that test `xfail(strict=False)` with a comment pointing at P3.8 rather than weakening the threshold.
**Why.** This is the only number that will prove Phase 3 worked.

> **How to read the ratios.** The grid is *n*×*n*, so `n → 2n` multiplies the **room count by 4**, not 2. Therefore: **4 ≈ linear in rooms, 16 ≈ quadratic, and the threshold of 8 sits at rooms^1.5.** Anything under 4 is sub-linear.

**Result (2026‑07‑26, n=4 → n=8, i.e. 16 → 64 rooms):**

| op | n=4 | n=8 | ratio | reading |
|---|---|---|---|---|
| `rebuild_all_walls` | 1.2 ms | 3.2 ms | **2.7** | **sub-linear** — the memoized `refresh_rooms` genuinely works |
| `group_selected` | 22.5 ms | 262.6 ms | **11.7–13.7** | near-quadratic → xfail, P3.8 |
| `bake` | 29.8 ms | 143.0 ms | 4.4–4.8 | ~linear, passes |
| `ungroup_selected` | 53.1 ms | 436.2 ms | **8.2–8.5** | rooms^1.5 → xfail, P3.8 |

**`rebuild` at 2.7 is the surprise, and it is a constraint on Phase 3, not just good news.** The `_RoomGrid`/`_WallGraph`/`room_signature` machinery that P3.5 deletes is currently performing *better than linear*. Stored outlines should beat it outright — there is no detection left to do — but P3.8 must confirm that rather than assume it. If P3.8 shows `rebuild` regressing, that is a real finding, not noise.

### P0.3b — Add selection-building to the harness
**Why.** P0.3 measures `group_selected` *after* the selection exists. It does not measure **building** the selection, which is where the user's reported stall most likely lives: `scene.selectionChanged` → `_update_edit_actions` (`mainwindow.py:323`) → `_selected_room_shapes()` (`:598‑629`) calls `bounding_walls()` **per already-selected room**, so ctrl-clicking room *k* re-runs O(k·W) `QPainterPath` booleans. Selecting R rooms is therefore O(R²·W) path booleans *before Ctrl+G is ever pressed*. Nothing measures this.
**Touches.** `tests/test_scaling.py`.
**Do.** Add a fifth timed operation: select the rooms **one at a time** (`setSelected(True)` per room, which is what a ctrl-click does), measuring cumulative wall-clock. Same `n` / `2n` grid, same ratio assertion, same `xfail(strict=False)` → P3.8 if it fails.
**Acceptance.** Ratio recorded. Also record the **absolute** time to select all 64 rooms — that number is the one to compare against the felt symptom.
**Note.** The harness runs headless offscreen, so it measures none of the repaint cost (`FullViewportUpdate`, no `setCacheMode`). Real-world stalls will be worse than these numbers, not better.

**Amendment (P0.6) — split `select` into two ops.** The debounce landed in P0.6 item 1 makes the single `select` op measure the wrong thing, and the fix is not simply to pump events: **the two user paths have genuinely different costs and should be measured separately.**

- **`select_burst`** — no event pumping. Models Ctrl+A, rubber-band, and the macro runner, where selections arrive faster than the debounce interval. Here the **debounce** does the work.
- **`select_interactive`** — `processEvents()` after *each* `setSelected`. Models a human ctrl-clicking, whose clicks are far slower than the timer, so `_apply_edit_actions` fires **once per click** and the debounce buys nothing. Here the **cheap-count fix** does the work.

Both get ratio assertions. Measure `select_interactive` first, then promote to a hard pass if it clears the threshold; if it doesn't, keep it `xfail` naming the specific task that will.

**This is not a goalpost move, and the tell is the direction the number moves.** Pumping makes the measurement *worse* (1.0 ms → 1.7 ms for the coalesced case, and higher again once it fires per click) because it models the user more faithfully. A goalpost move makes the number look better; this one makes it look honest.

**Step 3 — give the timing tests their own marker, before the first push.**
Register a `perf` marker in `pytest.ini` and tag every test in `tests/test_scaling.py` with it (keep `slow` too, so `--quick` behaviour is unchanged). Then change the CI test step to `python -m pytest -ra -m "not perf"`.

Deliberately `perf` and **not** `slow`: excluding `slow` from CI would also drop `test_fp_extract_cli_end_to_end` and the macro CLI subprocess test, which are slow but *deterministic* and worth running there. Only the timing-ratio assertions are unsafe on shared runners.

The harness stays a **local gate**, invoked explicitly at P0.6 and P3.8 — the two moments its numbers decide something. A timing gate that flaps in CI gets muted within a week and then protects nothing.

### P0.4 — Characterization tests
**Touches.** `tests/test_characterization.py` (new).
**Do.** Write these against *current* behaviour, marking `xfail` the ones that fail today:
1. Group a named room with a door, a window and two furnishings; move it; assert every opening's `s` relative to its wall is unchanged. Repeat for a 90° group rotation.
2. Delete one wall of a 4-wall named room. **Split into two tests — the single test cannot distinguish today's behaviour from P4.1's.**
   - **2a `test_delete_wall_keeps_room`** — the room still exists with its name, area and furnishings. **Passes today** (verified at P0.4), and must never regress. Assert hard.
   - **2b `test_delete_wall_actually_removes_the_wall`** — after the delete, the room has **3 built walls and 1 open edge**, not 4 built walls. *(xfail — P4.1)*
   
   Why the split: the room survives today **because the wall is not actually deleted**. `fracture_delete_wall` (`walls.py:300‑354`) keeps every stretch that runs along a room perimeter and rebinds it, so deleting a room's own perimeter wall is silently a **no-op** — 4 walls in, 4 walls out, 0 open edges (measured at P0.4). Under P4.1 the wall genuinely goes and the edge becomes `wall: null`. A test that only asserts "the room survived" passes in both worlds and therefore proves nothing about the change. 2b is the assertion that actually holds P4.1 to its promise.
3. Group two rooms, `serialize()`, `load_data()`, assert the group survives. *(expected xfail — P4.5)*
4. Group, move, `undo()`; assert the plan returns to its pre-group state. *(expected xfail — P4.5)*
5. Assert grouped walls are exempt from `coalesce_all` (guards the `group() is None` gate that nothing currently covers).
6. Group a room, ungroup, repeat 4×; assert wall and opening counts reach a fixed point. *(This is the deleted `test_zzleak.py`, promoted.)*
**Acceptance.** Each test either passes or is `xfail` with a comment naming the phase that flips it. **No existing test modified.**

> **An xfail prediction that turns out wrong is a finding, not an error.** Record what actually happens and *why*, then decide whether the test needs splitting (as test 2 did) — an unexpected pass usually means the test is measuring something coarser than the behaviour under change.

### P0.5 — Five free bug fixes
**Do.** One commit each, each with a regression test.

> **Expected test breakage — authorised in advance.** Fix 4 (making `select_in_rect` read-only) removes the wall synthesis that `tests/test_selection.py:53, 83, 106` currently assert.
>
> **Blast radius was wider than that — resolved at P0.5.** It also breaks `test_groups.py::test_extracted_room_region_follows_move`, which is not a defect-asserting test. Root cause: the old `select_in_rect` synthesised a *private copy* of a longer party-wall edge, and the following `rebuild_all_walls` rebound the room to that copy — so the room **owned** the edge and `bake()`'s strict `room_owns_walls` check would carry the region. Read-only selection removes that accidental privatisation, the room stays bound to the shared wall, and `bake()` correctly declines to move it.
>
> **Decision: mark it `xfail` → P4.2**, and record it in Known regressions below. Rationale: selection silently mutating the document is the worse defect, the workflow it protected is exactly what P4.2 rebuilds as a real `extract` operation, and dragging a room by its label still works today (`_privatize_shared_walls`, `rooms.py:838‑865`), so no workflow is lost outright — only the rubber-band-then-group route to it. Those three tests assert the *defect*: that a rubber-band selection duplicates a party-wall edge. Rewrite them to assert the corrected behaviour — selection creates nothing — and say so explicitly in the log. This and P3.4 / P4.5 are the only places in Phase 0–4 where changing an existing assertion is expected rather than suspicious.
1. `RoomItem.itemChange` on `ItemSceneChange` unbinds its walls, mirroring `walls.py:496‑504` including the `sip.isdeleted` guard. *(defect 5)*
2. `mainwindow.py:1074` → `properties=dict(it.properties)`. *(defect 4)*
3. `refresh_rooms_cmd` (`mainwindow.py:589‑593`) iterates only active-floor rooms. *(defect 2)*
4. `view.py:445` — `select_in_rect` must not call `synthesize_room_edge`; selection is read-only. *(defect 10)*
5. `catalog.apply_furnishing_prices` writes to the user config dir, not `assets/furnishings/manifest.json`. *(review §1)*
**Acceptance.** Five tests added; suite green; #3's test creates two floors and asserts the inactive floor's rooms survive.

### Known regressions carried during the migration

Behaviour that is deliberately worse between the task that broke it and the task that restores it. Kept visible rather than buried in a log, because "main stays shippable" has to mean something.

| Broken at | Behaviour | Workaround today | Restored at |
|---|---|---|---|
| **P0.5** (fix 4) | Rubber-band-select a room whose edge is a longer party wall, then group + move it — the region no longer follows. The walls captured by the band move; the room does not. | Drag the room by its **label** instead: `_privatize_shared_walls` handles the party wall correctly on that path. | **P4.2** (`extract` replaces the accidental privatisation with a real operation) |
| **pre-dates the branch** (surfaced at P3.5, defect 23) | **A rubber band that clips a room's wall set strands that room.** The band takes only items fully inside it, so a wall poking out is left behind, that room's remaining walls are duplicated into the group, and the group moves those while the room's region stays where it was — it reads as a detached dashed outline at the original position. 3 of 20 rooms on a band covering 92% of `symmetricP1`. | **Band whole rooms** — include every wall of any room you mean to take — **or move the room individually** by dragging its label, which carries its walls and openings correctly. | **P4.5**, where "what a group is" is decided. Listed here rather than as a Phase-3 regression because the branch measurably IMPROVES it (148.3" of drift before P3.5, 46.65" now) — the Phase-3 gate is no-worse, not all-better. |
| **P3.5** | **An open side of a room is not drawn.** Detach a wall from its room and pull a corner away and the side opens — the room keeps its shape and area, and the document says `wall: null` exactly as before — but the vacated stretch renders as nothing rather than as a dashed line. The producer of the dashed `OpenWall` placeholder was `refresh_rooms` → `reloop_open_room` → `bind_room_walls`, all deleted here; the fact itself moved onto the outline (`RoomItem.open_edges()`), which is where the document had always kept it. | None needed for correctness — nothing is lost but the on-screen cue. The room's area, outline and saved file are unaffected. | **P3.7** (`OpenWall` is deleted and a `wall: null` edge renders dashed from the outline, which is the same cue drawn from the one representation instead of a second one) |
| **P2.3** | **After the first undo, a wall that crosses a junction comes back split** — and if it borders NO room, body-dragging it moves only that segment. Measured at P3.3: one 480″ wall with a mid-span T returns as two 240″ walls. **Narrower than first recorded**: `_collinear_run()` (`walls.py:888`) gathers the whole room *side*, so for a wall on a room perimeter — the common case, and the one a user would notice — both halves still move as one. Verified with a room: `_collinear_run()` gathers 2 of 2. The row applies only to room-less walls, where `self.rooms` is empty and the run short-circuits to `[self]`. | Bind the wall to a room, or drag the halves together. Nothing is lost either way: the **document is unchanged**, since `design_from_scene` planarises to the same canonical form. | ~~P3.4~~ → **retargeted at P3.4 (iv), and the predicted fix was wrong on its own terms.** Re-checked by hand: the 480″ wall still returns as two 240″ segments, `merge_all` does **not** re-merge them, and the body-drag still moves one segment. It must not — the mid-span T is a **degree-3 vertex**, load-bearing for the planar subdivision, and merging through it would destroy planarity. `merge_collinear` refuses for exactly the right reason, so this row was never merge's to close. The fix belongs in the **drag's run-gathering**: `_collinear_run()` (`walls.py`) short-circuits to `[self]` when the wall borders no room, which is precisely the case the row describes. Gathering the run over **vertex adjacency** instead would carry both segments. Unassigned rather than invented — it is one small change, and the honest place is whichever task next touches the drag (**P4.2** extract/join is the nearest) |

### P0.6 — Cheap render wins
**Touches.** `items.py`, `rooms.py`, `mainwindow.py`, `view.py`.
**Do.**
1. Cache `GroupItem._oriented_box()` per geometry change instead of recomputing 3× per paint (`items.py:509‑528`).
2. Debounce `_update_totals` behind the existing 180 ms dirty timer instead of firing on every `scene.changed` (`mainwindow.py:98`).
3. Cache the `QFontMetricsF` in `RoomItem._label_rect` (`rooms.py:678`) and the stroker in `_boundary_band` (`rooms.py:514`).
4. `setCacheMode(DeviceCoordinateCache)` on `FurnishingItem`.
5. **Measure** `NoIndex` vs `BspTreeIndex` (`mainwindow.py:78`) with the P0.3 harness. Report both numbers; change the default only if BSP wins.
**Acceptance.** P0.3 ratios and absolute times recorded before and after. No behaviour change.

### P0.7 — Vendor the schema and validator
**Touches.** `floorplanner/design/` (new package), `tools/`, `tests/test_schema.py` (new), `.github/workflows/ci.yml`.
**Do.** Move `docs/design-schema.v5.json` to `floorplanner/design/design-schema.v5.json` (packaged data, with `docs/` keeping a symlink or a pointer). Port `tools/validate_design.py` to `floorplanner/design/validate.py` as an importable `check(doc) -> list[str]`. Add `tests/test_schema.py` validating every `examples/*.json` that declares `floorplanner-design`, plus asserting `planc1.v5.json` still fails I6 (it is the "does not launder its input" fixture). Add `jsonschema` to `requirements-dev.txt`.
**Acceptance.** `pytest -m io` validates the corpus; CI green.

---

# Phase 1 — The v5 document, shadow mode

*Nothing user-visible. The `Design` exists alongside the scene and is continuously checked against it.*

### P1.1 — `design/model.py`
Qt-free dataclasses for `Level`, `Vertex`, `Wall`, `Opening`, `Room`, `OutlineEdge`, `Furnishing`, `Group`, `Provenance`, `Design`, with `to_dict`/`from_dict` and stable emit order. No behaviour, no callers yet.
**Acceptance.** `Design.from_dict(load("symmetricP1.json")).to_dict() == load("symmetricP1.json")` byte-identical. Zero Qt imports (assert it in the test).

### P1.2 — `design/validate.py` (deep flag + negative tests)
**Most of this landed early at P0.7.** `check(doc) -> list[str]` already ports all **15** named checks (I1–I14 plus I5b; pure Python, in `floorplanner/design/validate.py`), and the corpus acceptance below already holds (`test_schema.py`). What actually **remains** of P1.2:
- Split the three O(n²) invariants behind a `deep` flag: **deep-only (3)** `I5b` (outline self-intersection, O(edges²)/room), `I11` (room-vs-room overlap, O(rooms²)), `I14` (weld closure, O(walls²) — ~6,700 pairs on 82 walls); **always-on (12)** I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I12 I13. The docstring must state the call sites, since they are the reason for the split: the cheap twelve run **per mutation** under P1.6's `--verify-design` (an O(n²) sweep per edit would make the app unusable); the deep three run on **save, load and import** (paid once, stakes highest — I11 and I14 are the two that caught the real corruption in `planc1.json`).
- Two negative unit tests, each of which must **fail the check** (not merely not-crash): nudge a shared vertex 0.3″ → `I14` fires (and does *not* fire under `deep=False`); point a wall's `left` at a room that doesn't name it → `I6` fires.
**Acceptance.** `check(doc, deep=True)` (the default) runs all 15; `deep=False` runs only the 12 always-on and skips I5b/I11/I14; both negative tests pass. **`deep=True` is the default deliberately**: forgetting `deep=False` on the hot path is a loud slowdown, but forgetting `deep=True` on load/import is *silent* corruption — the failure mode should be loud. (The corpus acceptance — `[]` for `symmetricP1.json` and `site_demo.json`, non-empty for `planc1.v5.json` — already holds from P0.7.)

### P1.3 — `design/topology.py`
Port from `tools/migrate_to_design_v5.py`: `weld_endpoints`, `planarize`, `split_edge`, `merge_collinear`, `trace_faces`, `enclosing_face`. Pure functions over the `Design`; no Qt.
**Acceptance.** `trace_faces` on `symmetricP1` recovers every stored room area (**20**, after the P1.3b `_inner_faces` fix; it was 19 while defect 18 dropped the Garage), plus one extra face for a genuinely unclaimed region. `weld_endpoints` on the legacy `planc1.json` geometry welds exactly 31 ends.

### P1.4 — `design_from_scene()`
Walk the live scene into a `Design`. **This is where the ten unfiltered floor queries get fixed** — the walk is level-scoped **by construction** (iterate levels outer, items inner, so cross-level contamination is impossible, not merely filtered out). Build room outlines from the scene's own `RoomItem.corners`, **not** from `trace_faces`: `design_from_scene` must report what the scene *believes*, not what the geometry *should* be. Repairing while reading would make P1.6's shadow comparison diverge from the live scene; repair belongs at P2.1's import, once, and nowhere else. The scene is still `p1`/`p2`-based (pre-P3.1), so the walk uses `legacy.py`'s weld/planarise to reach a vertex table.
**Acceptance.** Corpus is **legacy files only** — `examples/planc1.json`, `examples/sample_plan.json`, and scenes built by the test fixtures — because `symmetricP1.json`/`site_demo.json` are v5 and have no loader until P2.1. For each: load into a scene the old way, `design_from_scene()`, then room areas match `project_from_scene()`'s to 0.1 sf. `check(deep=True)` returns `[]` on the clean scenes (planc1 may carry the same referential faults as its v5 fixture — assert what it actually reports, don't force `[]`).

### P1.5 — `apply_design_to_scene()`
Build the scene from a `Design`.
**Acceptance.** `scene → Design → scene → Design` is identical at the second `Design`. Existing IO and undo tests still green.

### P1.6 — `--verify-design` shadow mode
A debug flag (env var or `--verify-design`) that rebuilds the `Design` and runs the cheap invariants after every mutating operation, raising on failure.
**Acceptance.** **The entire suite passes twice: once normally, once with the flag on.** This is the gate that says the bridge is trustworthy. CI runs both. Any invariant that fires here is a real bug in the current code — log it, don't paper over it.

---

# Phase 2 — IO cutover

*The file format changes. This is the first user-visible phase.*

### P2.1 — Load path
v1–v4 `floorplanner-json`: parse → weld at `join_tol_in` → planarize → trace outlines → convert openings → assign furnishing owners → write `provenance` → **mark dirty** → show the conversion report (§7a of `DESIGN_MODEL_v5.md`). v5 `floorplanner-design`: load, validate, **never dirty**; a file failing I14 is reported as malformed, not silently re-welded.

**Two weld counters, with a 0.6″ noise floor** *(added after P1.4 measured them)*. Track both: `weld_ops`, operations performed (31 on `planc1.json`), and `ends_moved`, operations that displaced a coordinate by **more than `settings.vertex_weld_in` (0.6″)** — **4**. Only `ends_moved` reaches the user or `provenance.endpoints_welded`, whose schema description already says "wall ends *moved*"; `weld_ops` is for cross-checks. Anything at or below 0.6″ is not a geometry change by the document's own definition, so it must not be counted as one. **Regenerate `examples/symmetricP1.json`'s `provenance.endpoints_welded` (31 → the measured `ends_moved`) as part of this task**, once the real importer exists — not before, since P1.1/P1.4/P1.5/P1.6 all pin that fixture and a mid-phase regeneration is churn for a semantics fix this task implements properly anyway.

**Also close defect 19's in-app arm here.** Weld-on-load fixes the PNG extractor's *file* route for free (write a plan, open it, it welds). It does **not** fix `extract_from_reference` (`mainwindow.py:1644`), which injects detected walls straight into the live scene and never passes through a load — that arm needs its own explicit weld pass after the walls are written. Closing only the file arm would tick the defect while leaving the reported reproduction alive.

**Outlines come from the welded FILE geometry, never from the scene's re-detection.** P1.4 measured why: loading `planc1.json` collapses Hall and M Bath into **one identical 21-vertex region** (both 243.5 sf, same vertex set), where the file at least keeps them distinct (Hall 243.5 sf/18 corners, M Bath 591.6 sf/24 corners). The scene's belief about a corrupt file is **strictly worse than the file itself**, so importing through the scene would bake in damage the file does not contain. `tests/test_design_bridge.py::test_planc1_reports_its_real_faults` pins the shared vertex set and is the guard for this.
**Acceptance.** Opening `examples/planc1.json` yields M Bath 182.0 sf, Hall 61.5 sf, **`provenance.endpoints_welded` = 4** (`ends_moved`, the ends displaced by more than 0.6″ — *not* the 31 weld operations attempted; see the two-counter rule above), and a dirty document. Opening `examples/symmetricP1.json` is clean and not dirty. The legacy file on disk is never modified. **Opening a v5 file must not dirty it** — this depends on P1.1 round-trip fidelity (`Design.from_dict(x).to_dict() == x`); if a v5 file opens dirty, suspect a model normalisation that broke byte-identity, not the load path.

### P2.2 — Save writes v5
Plus **File ▸ Export legacy v4…** for one release, so nobody is stranded.
**Acceptance.** Save → reopen → `check()` clean, not dirty. Legacy export round-trips through the old loader.

### P2.3 — Undo snapshots the v5 dict
Still whole-document; only the payload changes.

> **Correction (2026‑07‑27): groups do NOT close here.** This task originally read "Groups now serialize, so defect 3 partially closes here", with an acceptance test "group, undo, redo — the group survives". That was written before P1.4 decided — correctly — that the bridge emits `groups: []` until **P4.5**: mapping a grouped wall onto its split segments is undefined while grouping still *copies* walls. So group survival stays at P4.5, held by characterization test 3 exactly as it is now, and **the group-survives test must not be written here** — it would pass for the wrong reason or fail for a reason P2.3 cannot fix. The behaviour P2.3 *must* preserve is narrower and already works: **undo after grouping restores the plan correctly** (via the P0.5 aliasing fix) even though the group itself dissolves.
**Compare canonical form, not raw bytes.** The dirty check and the undo comparison must both run `design.canonical.canonicalize` over each side before comparing. With the importer canonicalized (P2.2) this is belt-and-braces — but defining equality on canonical form is what survives any future producer that forgets to canonicalize, **including whichever way P3.1's uid decision goes**. Two documents describing the same plan must compare equal even when they were built by different code paths.
**Also here: backdrop / reference-image retention.** `apply_project_to_scene`'s `keep_backdrop` flag exists because undo must not delete the tracing image; `apply_design_to_scene` (P1.5) deliberately does **not** implement it, since it belongs with the undo-restore path rather than the bridge. Wire it here, or undo silently drops the backdrop.
**Acceptance.** `test_undo.py` green. Undo after grouping restores the plan (the group dissolving is expected until P4.5). Undo with a reference image loaded keeps the image. **Record undo latency on the P0.3 64-room grid** — the canonical walk now runs per settled edit, so P6.1's "undo cost is independent of plan size" needs a baseline to be measured against.

### P2.4 — Convert the corpus and the tooling
`examples/*.json`, `docs/make_gallery.py`, `examples/make_examples.py`, `tests/bench_rooms.py`, `fp_extract.py`'s writer, and the macro `open`/`save` tokens.
**Includes flipping `fp_extract.py` from `export_legacy_v4_path` back to `save_path` (v5)** — deferred here from P2.2, where `save_path` going v5 would have converted that one writer early and out of step with the rest of the tooling.
**Acceptance.** `python docs/make_gallery.py` and `python examples/make_examples.py` both run; gallery images regenerate.

### P2.5 — Split `MainWindow`
Extract `io.py` (open/save/export), `csvio.py` (`_import_rooms`/`_export_rooms`, 137 lines), `imageio.py` (PNG import/calibration), `levels.py` (floor roster). `MainWindow` keeps UI wiring.
**Acceptance.** `MainWindow` under ~55 methods. Suite green with no test changes.
**Why here.** After the IO seam is clean and before Phase 3 churns the same files.

---

# Phase 3 — Vertices own the geometry

> **Branch.** `git switch -c v5-topology`. This is the only phase where `main` should not track HEAD. Merge when P3.8 records its numbers.

### P3.1 — Vertex table live
`Design.vertices` becomes the live store. `WallItem` gains `v1`/`v2` ids; `p1`/`p2` become read-through properties resolving against the table, so **every existing caller keeps working**. Assignment to `p1`/`p2` moves the vertex and is logged under `--verify-design`.
**Assignment is SPLIT-ON-WRITE, not shared-move** *(ruled 2026‑07‑27)*. Assigning a new position to `p1`/`p2` **mints a fresh vertex for that wall's end** and leaves any sharer on the old one — today's independent-ends semantics, preserved exactly. That is what makes "suite green with no test changes" achievable at all: a shared move would drag a neighbour's end and break tests that have nothing to do with this task. Sharing is created **explicitly** (weld/join making two ends reference one vertex) and broken **explicitly** (split-on-write); shared movement arrives at **P3.3** as the wall-move *operation*, never as a side effect of assignment. Representation changes first, behaviour second, each observable separately. **Log every split-on-write under `--verify-design`** — the count of implicit splits per operation is exactly the data P3.3 needs to decide which call sites should become real vertex moves.

**Gate additions** *(the Gate 2 lesson, applied verbatim)*: the task's gate includes a round-trip through **both** apply paths — `load_data` (faithful) and `open_document` (converting) — plus the `--verify-design` run. Compositions, not just paths.

**Decide id policy here.** **Live items carry persistent uids, minted once; FILES stay canonical.** Persistence is an **in-memory** property; canonical form is the **interchange** property; P2.3's canonical comparison is the bridge that makes a persistent-uid document compare equal to its canonical form. Save canonicalizes at serialization exactly as P2.2 already built it, so **nothing on disk changes because of this decision** — fixtures, diffs and the equality definition are all untouched. Items should carry **persistent uids, minted once** — stable across edits, and therefore macro-addressable — with `canonicalize` (`design/canonical.py`) applied only at **snapshot/serialization time**, for equality. Content-derived ids recomputed per walk are almost certainly the wrong thing to *persist*: P1.5's canonical ids sort by geometry, so moving one wall renumbers its neighbours. That is harmless for round-trip and undo comparison, which is all it was built for, but P3.1 makes scene items id-carrying and **P4.5 serializes groups by member id** — a group whose members are renumbered by an unrelated wall move is a live bug. Settle it at this task rather than discovering it at P4.5.
**Acceptance.** Suite green with no test changes. The `--verify-design` run stays green.

### P3.2 — `RoomItem.outline`
`RoomItem` gains `outline: list[OutlineEdge]`. `corners` becomes a derived property. `properties["perimeter_corners"]` is dropped on save and ignored on load (the schema already forbids it).
**Acceptance.** Room areas unchanged across the corpus. `_sync_corner_props` and its six call sites deleted.

### P3.3 — Wall move = move vertices, plus the split rule
Dragging a wall moves its two vertices. Implement the split rule: a collinear continuation past an endpoint splits first; a vertex landing on another wall's body splits that wall.
**Acceptance.** Port `tools/demo_move_wall.py` to `tests/test_wall_move.py`: moving `w24` by +12 y changes exactly Lounge and Front Porch by ±17.5 sf, total unchanged, `check()` clean. Add a split-rule test with a T-junction continuation.

### P3.4 — Topology ops replace coalesce/weld/fracture
`coalesce_wall`, `coalesce_all`, `_coalesce_*_impl`, `weld_all`, `join_endpoints`, `fracture_delete_wall`, `_WallIndex`, `_WallBBoxIndex`, `_compute_wall_junctions` → `merge_collinear`, `split_edge`, vertex adjacency. **Defect 9 closes here** (merge dedups openings).
**Inherits the split rule's second half from P3.3: a vertex landing on another wall's body splits that wall.** P3.3 built only the first half (a collinear continuation past an endpoint splits first, so it can never be sheared); the body-landing half is `split_edge` applied scene-side, which is exactly this task, and building it twice would have meant building it wrong once. Until it lands, a body-landing has no vertex to be: P3.3 leaves those attachments on the old coordinate path (`kind == "tee"` in `WallItem.mousePressEvent`) with a comment naming this task. **Also remove `split_edge`'s `NotImplementedError` guard on walls carrying openings** (`design/topology.py`, added at P1.3-followup and pinned by `pytest.raises(match="P3.3")`) as the redistribution it names is built — the guard's message points at P3.3, so retarget or retire it rather than leaving it lying about which task owns the work.
**Settled before implementation** *(2026‑07‑27 — seven points; committed to this file first, per the handoff-spec rule above, so the implementing session reads them from disk rather than from a summary).*

**1. The crux — one pure planner, two thin appliers.** The ops in `design/topology.py` are pure `Design → Design`; this task needs them acting on a live scene of `WallItem`s carrying `OpeningItem` children, room bindings, groups, z-order and floors. Two obvious routes were considered and **both are rejected**:

- **(a) Lift the scene to a `Design`, run the pure op, apply back.** Disqualified *on measurement*, not on taste: it makes every wall edit a **full-plan rebuild**, which destroys item identity — selection, in-flight drag state, group membership, and the whole point of P3.1's persistent uids — and would regress precisely the numbers **P3.8** exists to improve.
- **(b) Scene-side siblings that share only the algorithm.** This is **F2's disease**: one concept, two implementations, drifting apart from the day they are written.

**The third way: the decision logic runs ONCE, pure; only the mutation is dual.** `plan_merge_collinear(...)` / `plan_split_edge(...)` compute a **delta** — which vertices merge, which walls die, which openings land where and with what anchors — and two **thin** appliers execute it: the `Design` applier (essentially what `topology.py` already is) and a new **scene** applier that touches **only the items named in the delta**. No full rebuild; the algorithm single-sourced.

**The drift risk that makes dual appliers frightening is already policed.** `--verify-design` re-derives the `Design` from the scene at every quiescent point, so **if the two appliers ever disagree, the shadow gate fires**. P1.6 was built for exactly this moment; this is the task that collects on it.

*Bonus, and it is not incidental:* **a delta plus an applier is a command in all but name.** **P6.1** (`QUndoStack` + `MoveVertices`/`EditOpening`/…) inherits this shape for free rather than inventing it later.

**2. The three unlisted helpers — let the call-site census decide, not the list.** The rule is: **a line dies when its last caller dies. Anything deleted must be uncalled; anything still called migrates.**

- `_merge_intervals` is `fracture_delete_wall`'s alone → **falls with it**.
- `coincident_walls` and `wall_endpoint_open` have callers in the **drawing / snap paths that survive Phase 3** → **they do not fall.** They are **reimplemented as thin queries over vertex adjacency** — a vertex's degree and its incident walls — which is precisely what the task line's "vertex adjacency" clause means. Census taken at P3.3, and it is **wider than "view.py"**: `wall_endpoint_open` at `view.py:248` (draw-release snapping); `coincident_walls` at `view.py:597` **and at `walls.py:656` and `walls.py:695`, inside `WallItem.rebuild` and `paint`** — those two are the party-wall opening cascade and the render path, neither of which Phase 3 removes. Only the `walls.py:201` caller (inside `_coalesce_wall_impl`) dies. Migrate on the census, not on the module a helper happens to live in.

**3. Junction rendering — the inputs change, the output must not.** `_compute_wall_junctions` found neighbours by **bbox search**; adjacency hands them over **by lookup** (the walls sharing a vertex). The `_outline_clip` cache is recomputed from adjacency. **Seam-free is an OUTPUT contract: if the junction test needs touching, the replacement is wrong.**

> **Correction, made at the read-back rather than discovered mid-task: the existing guard is NOT a pixel test.** `tests/test_walls.py:360` `test_junction_outline_is_clipped_so_walls_read_solid` asserts `w._outline_clip is not None` for crossing walls and `is None` for a lone one — **structural, not rendered**. It would pass against a replacement that populates the cache with the *wrong* clip, which is exactly the failure a bbox→adjacency swap can produce. So point 3 has two halves: keep that test green **unchanged** (it pins the cache's shape), **and add the pixel assertion it never had** — render a cross junction and assert no light seam pixel at the crossing. Per `CLAUDE.md`, antialiased 1-px assertions need a lenient threshold (`< 190`, not `< 100`). This is an **addition**, not a rewrite, so it does not count against the changed-test budget point 4 governs.

**4. Rewritten tests get one line each: old op → new op → why the assertion moved.** For **defect 9**, the closing test is **live-editing shaped**: merge two collinear walls carrying identical openings → one survivor, openings deduped. (`planc1`'s three stacked doors were cleaned at import; this guards **the path that created them**, which is the one still open.)

**5. Telemetry expectations, stated in advance so the numbers are predictions and not rationalisations.** The tee branch's **2** split-on-writes → **0** when the split rule's second half lands. `GroupItem.bake`'s **80 remain**: they are **P4.5's**, and the counter staying nonzero until then is **correct, not unfinished**. The split-on-write shim stays until its counter is owned entirely by P4.5's rebuild.

**6. Sub-commits, each at a FULL green gate** (the P0.5 per-fix precedent — and this task is the size that earns it: one task, several rollback points):

  1. planner/applier factoring + the scene applier for `merge_collinear`;
  2. `split_edge` scene-side + the split rule's second half + the guard retarget (with its **pre-authorized** `match=` change, named in the log rather than slipped through);
  3. call-site migration, **family by family**;
  4. deletion of the dead ~375 and the junction swap.

**7. On exit.** Re-check the **P2.3 Known-regressions row by hand** — the 480″ body-drag moving as one run again — and **flip it only if it genuinely closes**. Report the **measured** deletion count against the estimated 375.

**Acceptance.** `test_coalesce.py` and the coalesce half of `test_walls.py` rewritten against the new ops — **and this is the biggest "changed test" risk in the plan, so every rewritten assertion must be justified in the log.** ~330 lines deleted from `walls.py` — **measured at P3.3 as 375 across 13 functions (25% of the file), including the three helpers point 2 adjudicates**; report the real figure on exit.

### P3.5 — Delete the detection engine
`_RoomGrid`, `_WallGraph`, `detect_room`, `_detect_room`, `room_signature`, `refresh_rooms` memoization, `bind_room_walls`, `_wall_along_segment`, `_perimeter_span`, `room_owns_walls`, `walls_cover_room`, `duplicate_wall`, `_privatize_shared_walls`, `synthesize_room_edge`, `reloop_open_room`. "Detect room here" becomes `topology.enclosing_face`. **Defects 8 and 13 close here.**
**Acceptance.** ~550 lines deleted from `rooms.py`. `test_rooms.py` and `test_room_walls.py` pass against stored outlines. `room_boolean` rewritten as a polygon op on outlines that touches only its own walls.

**Settled before implementation** *(2026‑07‑27 — four riders on the read-back; committed to this file first, per the handoff-spec rule, so the implementing session reads them from disk).*

**1. The headline check — the acceptance's essence in one assertion.** After the flip a wall move must update room outlines **by construction, with zero recomputation**: the outline references the same `Vertex` the wall does, so `relocated_to` moves both, or the model is wrong. **The proof is the existing P3.3 demo test** — the Lounge / Front Porch party wall, +12 y, ±17.5 sf, total unchanged — **passing with `refresh_rooms` deleted.** That one test surviving the deletion of the machinery that used to make it pass is the whole phase in a single assertion.

**2. The tripwire disambiguation, made mechanical.** `test_a_corner_is_still_two_distinct_wall_vertices` can go red two ways: the designed outline flip, or a weld reaching the room-creation path (P3.4 built `share_coincident_ends`; `make_room` never calls it). **Sequence the sub-commits so the flip is unambiguous: retarget the docstrings → flip outlines to vertex identity (the guards flip HERE, for the designed reason) → then any path changes.** Red at any other point is a finding, not the flip.

**3. Defect 13 — do not tick it on the disappearance of its measuring instrument.** The read-back established that `detach_wall_from_room` contains no detection today, and the only zoom-dependent quantities on that path are the drag's (`mousePressEvent`'s `20.0 / _view_scale()` endpoint catch radius, `_project_to_orthogonal`'s `16.0 / view_scale` stick). *Archaeological note:* the original `test_zzprobe` evidence counted **OpenWalls after `detach_wall_from_room` at pinned zooms** — and `reloop_open_room` plus the bind machinery die here while `OpenWall` itself dies at **P3.7**, so the repro's substrate is being demolished across two tasks. If it cannot be reproduced at the P3.5 exit, write **"repro substrate removed, defect retargeted to the drag tolerances"** rather than ticking it. *A defect closed by the disappearance of its measuring instrument is not closed.*

**4. Census divergences, approved as tabled.** Realistic deletion **~470 from `rooms.py` + 34 from `walls.py`** against the ~550 estimate, with four names owned elsewhere: `_perimeter_span` (24) falls with `fracture_delete_wall` at **P4.1**; `duplicate_wall` (15) at **P4.5**; `room_owns_walls` (14) and `walls_cover_room` (20) are **rewritten as outline predicates, not deleted** (last caller is `GroupItem.bake`). `_privatize_shared_walls` (28) is assessed **in-task**, with the outlines already flipped, rather than guessed now. `synthesize_room_edge` (13) is already callerless — a free deletion. **`test_rooms.py` / `test_room_walls.py` rewrites are this task's authorized zone**, same discipline as P3.4: one line per rewritten assertion, old mechanism → stored outline → why.

### P3.6 — Opening anchors
`s` → `{from, offset_in}`. Delete the silent clamp in `WallItem.rebuild` (**`walls.py:1004`**, not `:568` — the line moved through P3.3–P3.5) — an out-of-range opening is an error surfaced to the user, not a slid door. Replace the **8 verified** `except ValueError: continue` sites that silently drop an opening with a collected, reported error list. **Defects 6 and 7 close here.**

**Read-back corrections, settled 2026‑07‑28** *(the numbers in the line above were quoted from the review and did not survive being checked; recorded here rather than carried).*

- **"13" was never the count of opening drops.** Measured at the migration baseline `841264e`: **13 is the count of *every* `except ValueError` in `floorplanner/`**, of which **7** wrapped an `OpeningItem(…)`. Today: 17 total, 9 wrapping `OpeningItem`, of which **8 are still silent** (`bridge.py` was converted to a reported list at P1.5 and its comment forecast this task). The other four at baseline are catalog price parsing ×2, `macro._is_num`, and dialog handlers that already report — feeding those into an opening-error list would be wrong. **The 8:** `planio.py:169` (the v4 load — defect 6's "incl. on load"), `mainwindow.py:1082` and `:1177` (paste), `rooms.py:749` (privatize), `rooms.py:1046` (`duplicate_wall`), `walls.py:333` (merge), `:587` (split), `:675` (fracture).
- **"P0.4 test 1 passes without xfail" pinned nothing** — it was never xfail. P0.4's own log says *"Passes: opening-s under group move AND rotate"*, and both still pass. Replaced by R1 below.
- **Defect 7's four cited sites are stale.** The *condition* is verified intact — nothing anywhere re-bases `op.s` — and that condition, not the site list, is what the anchor closes.

**Rulings, settled 2026‑07‑28 (R1–R5).**

**R1 — Acceptance.** The schema's own rationale, as three tests plus the report:
  (a) an opening anchored `from: "v2"` keeps its `offset_in` exactly when the wall is stretched **at v2** — *the discriminating case*, since absolute `s` holds position relative to v1 instead;
  (b) reversing a wall leaves the opening's physical position unchanged;
  (c) the split of R2;
  (d) loading a plan whose door no longer fits **reports** it.
  **Receipt standard:** (a) and (b) must be shown failing against `s`-based code in a worktree before the anchor lands.

**R2 — Straddle: the primitive becomes TOTAL, and both pins flip.** P3.4(ii)'s decline was a placeholder pending representability, and `match="P3.6"` was that test naming its own executioner. **Load-time planarize cannot decline** — a crossing that exists in the data has to split, and refusing there aborts or corrupts a load. Semantics: the opening anchors to the segment containing its **anchored end**; if its extent no longer fits that segment, it joins the collected report. **The scene op's decline dies with it** — a gesture that silently does nothing is defect 17's disease and we do not keep a second case on purpose. Both flipped assertions carry a one-line justification citing this ruling.

**R3 — The drag clamp LIVES,** and is annotated so a later census does not kill it as a survivor of this task. `rebuild`'s clamp silently repairs *stored data* (dies); `OpeningItem.mouseMoveEvent`'s (**`walls.py:1821`**) bounds a *gesture* (lives) — the same distinction that keeps `wall_endpoint_open` and `_WallBBoxIndex` in the "rightly spatial, permanently" category.

**R4 — `center`: consume, never produce.** Emitting `center` requires knowing the user *meant* centred, and inferring that from coordinates that happen to be the midpoint is detection-from-geometry — the disease v5 exists to kill. P3.6 emits `v1`/`v2` only, **nearer end, ties broken toward `v1`**, so canonicalization round-trips deterministically. **Production of `center` is deferred until a UI expresses the intent.**

**R5 — One vocabulary, two surfaces.** All 8 sites feed the `rep["openings_failed"]` structure, entries naming wall, opening type and anchor. Surfaced by context: **load-path** entries (`planio.py:169` included — that is defect 6's "incl. on load" closing, and it ends the v4-silent / v5-reported asymmetry) join the open/conversion report per P2.1; **edit-path** entries (paste ×2, merge, split, fracture, privatize, `duplicate_wall`) surface as a status-bar line naming the edit, **said once** — the `06c2145` wording standard applies.

**R4b — anchors: FIDELITY on round-trip, canonical at MINT only** *(settled 2026‑07‑28; overrules the canonicalize-on-emit shipped at P3.6(1))*. An anchor that already exists — loaded from a v5 file, or held by the live item — round-trips **verbatim**. The nearer-end / tie-to-`v1` rule of R4 applies **only when minting**: a legacy import, or an opening that has never had an anchor. *Why:* the anchor end changes behaviour under stretch, so re-basing it on save is **silent loss of intent — the same category as the clamp P3.6 deletes.** `_walls_of` reads the stored anchor when present and mints only when absent. Pinned by a round-trip test: a hand-authored FAR-end anchor survives load → save unchanged.

**R2b — the straddle rule, confirmed as read.** **Extent decides:** an opening wholly inside one segment lands there regardless of which end it is anchored to. The anchored-end rule is the tiebreak for the **true straddle only** — where the opening necessarily overhangs and is necessarily reported. When an opening lands on the segment that does *not* contain its anchor vertex, it **re-seats to the same-side end of its new segment** (the split vertex), exact position preserved, offset recomputed — **same-side, not nearer-end**, consistent with R4b.

**Also in scope, found during the read-back: defect 24.** `topology.graph_from_design` and `_reanchor` read and write `offset_in` as a **centre** distance where the schema, `bridge._walls_of` and `bridge._opening_s` all define it as a **near-edge** distance. This is the anchor arithmetic, so it is this task's; and R2's straddle test (`ov.s - half < s < ov.s + half`) rests on the value being right.

### P3.7 — Delete `OpenWall`
An outline edge with `wall: null` renders dashed.
**Acceptance.** `test_open_walls.py` rewritten against null edges; the class is gone.

### P3.8 — Perf verification
Re-run P0.3 and compare against the P0.6 numbers.
**Acceptance.** Ratios recorded in the log. Grouping 20 rooms creates **0** new walls — assert it.

**Also: the SPLIT-ON-WRITE EXIT SURVEY** *(added 2026‑07‑28)*. Assigning `p1`/`p2` mints a fresh vertex for that end, and three separate defects have now come from something downstream being left on the old one: the P3.1 shim's own telemetry, **defect 22** (bake orphaning room outlines) and **the anchor orphaning** found at P3.6(1) (12 of 41 openings mirrored on loading `planc1`). Three members is a pattern, not a coincidence. **Census at P3.6: 9 direct coordinate-assignment sites remain** — `mainwindow.py:568,569` (align to grid), `:578,579` (`_translate_shape`), `view.py:402` (the rubber-band wall being drawn), `walls.py:1511,1513` (the endpoint drag), `walls.py:1549,1551` (the `rigid` and `tee` branches, both P4.5's / P3.3's by ruling). P3.8 re-runs this grep, records the count, and for each survivor states what carries the things attached to that end — or names the task that will.

---

# Phase 4 — Rooms as durable movable units

### P4.1 — Delete-wall keeps the room
**Acceptance.** P0.4 test 2 flips to pass.

### P4.2 — Extract / join
Per §4 of `DESIGN_MODEL_v5.md`. Extract privatizes walls and vertices, sets `state: floating`, `extracted_from`. Join welds, merges coincident walls, splits, rebinds, sets `state: placed`, and coalesces only the touched degree-2 vertices.
**Acceptance.** Extract → move 500″ → join at a new location → `check()` clean at every step; furnishings and openings intact; I12 holds while floating.
**Also required:** flip `test_groups.py::test_extracted_room_region_follows_move` back from `xfail` to a hard pass — via a real `extract`, not via selection-time synthesis. That test is the receipt for the P0.5 regression in Known regressions above.

### P4.3 — Shuffle mode
`settings.editing.{shuffle,auto_coalesce,auto_weld,auto_bind}` + a toolbar toggle. Leaving shuffle joins nothing automatically.
**Acceptance.** With shuffle on, dragging a floating room across the plan leaves both unchanged; `check()` clean throughout (I11 exempts floating rooms).

### P4.4 — Concept rooms, `nominal_size`, duplicate-as-template
Create a room by typed dimension; duplicate a room as a floating unit; save/load a one-room design as a template.
**Acceptance.** A one-room file validates against the schema and loads into an existing design as a floating room.

### P4.5 — Group semantics + z-order
Groups move the real items — no `duplicate_wall`, no `coalesce_all` on ungroup. Groups serialize (`Design.groups`). Collapse the four z schemes into one that is serialized. **Defects 3 and 11 close here.**
**Retire or re-justify P3.3's `kind == "rigid"` carve-out here, explicitly.** A wall drag promotes coincident ends into shared vertices, but *excludes grouped neighbours* — they keep the old coordinate path, following the drag without becoming topology. The reason is this task's premise: grouping **duplicates** a room's walls onto the originals, so a grouped coincident end is the common case and not an exotic one, and sharing one would wire a group member to an outside wall permanently while what a group *is* topologically is still undefined. Exactly the reasoning behind the `group() is None` gate that keeps grouped walls out of coalesce — deliberately not topology. **When groups stop copying walls, that reason evaporates**, and a carve-out whose justification has gone is how a workaround becomes folklore. Decide it here: delete it, or write down the new reason.
**Acceptance.** P0.4 tests 3, 4 and 6 flip to pass. `test_groups.py` rewritten — the three tests encoding duplicate-on-group semantics (`:64`, `:133`, `:155`) are *intentionally* replaced; say so in the log.

---

# Phase 5 — Landscape

### P5.1 — Site levels, categories, area accounting
`level.kind`, `room.category`, `area_accounting` with the class-scoped I11.
**Acceptance.** `examples/site_demo.json` opens, edits and re-saves clean. Area totals report conditioned / unconditioned / site separately.

### P5.2 — Landscape wall types + gates
`fence`, `hedge`, `retaining`, `railing`; `kind: "gate"`; no finishes on landscape walls.
**Acceptance.** Drawing a fence and placing a gate round-trips; placing a *door* in a fence is refused.

### P5.3 — Site schedule fields + reports
`surface`, `plant_palette[]`, `irrigation`, `sun_exposure`, `slope_pct`, `drainage`, `edging` in the room properties dialog; inventory/schedule split by accounting class.
**Acceptance.** Site rooms schedule correctly; interior reports unchanged.

---

# Phase 6 — Command undo and final perf

### P6.1 — `QUndoStack` + commands
`AddItems`, `DeleteItems`, `MoveVertices`, `EditOpening`, `EditRoomProps`, `Group`/`Ungroup`, `Extract`/`Join`, `ChangeSettings`, level ops. Each references items by id and re-runs a scoped rebuild.
### P6.2 — Retire snapshot undo
### P6.3 — Scene index + viewport update final pass
Revisit `FullViewportUpdate` now that bounding rects are trustworthy.
**Acceptance.** P0.3 numbers improve again; undo cost is independent of plan size (assert: undo time on a 20-room plan ≈ undo time on an 80-room plan).

---

## Risk register

| Risk | Mitigation |
|---|---|
| **P3 is the whole refactor in one phase** | Branch; P3.1/P3.2 are compat shims that keep every caller working, so the suite stays green while the store changes underneath |
| **Tests quietly relaxed to match new behaviour** | Every changed assertion must be named and justified in the Progress log; P0.4 characterization tests are written *before* the behaviour changes |
| **P3.4 and P4.5 legitimately invalidate existing tests** | Called out in advance — those are the only two tasks where rewriting tests is expected rather than suspicious |
| **The perf win doesn't materialise** | P0.3 exists before any of it; P0.6 and P3.8 both record numbers, so a regression is visible at the task that caused it |
| **Legacy files silently change on open** | Never modified in place; conversion is reported and requires an explicit Save (P2.1) |
| **Macro/gallery/extract tooling drifts** | P2.4 converts them at the format cutover, not later |

## Sequencing rationale

Phase 0 before anything: without the scaling harness and the characterization tests, no later phase can be shown to have worked. Phase 1 before Phase 2 so the document is proven against the live scene before it owns the file. Phase 2 before Phase 3 so the format cutover is separately revertible from the geometry rewrite. Phase 3 before Phase 4 because extract/join/shuffle need vertices. Phase 5 is additive and could move earlier if landscape work becomes urgent. Phase 6 last because commands want stable ids and settled operations.

---

## Progress log

*Append one entry per task. Newest at the bottom.*

```
P0.0  done
ruff:    n/a (doc only)
pytest:  n/a
files:   CLAUDE.md
notes:   "## v5 migration (in progress)" block added verbatim after Architecture,
         before "## Generated assets". No code change.

P0.1  blocked -> resolved
ruff:    23 findings at first run — ALL in tools/ and docs/_superseded/,
         0 in floorplanner/ or tests/. Correctly reported rather than papered over.
         RESOLUTION: fixed at source (17 after dedup across the two copies),
         docs/_superseded moved to _to_delete/. ruff check . now clean.
pytest:  287 passed, 0 failed, 0 xfailed, 0 skipped in 7.59s
quick:   276 passed, 11 skipped in 6.18s
files:   tools/{validate_design,migrate_to_design_v5,make_site_demo}.py (lint only)
notes:   No test changed. Tools re-verified after the lint fixes: welds=31,
         rooms_traced=19, openings_deduped=2; symmetricP1 + site_demo PASS/PASS;
         planc1.v5 still 23 invariant errors (intended fixture).

BASELINE OF RECORD
  full   287 passed / 0 failed  in 7.59s
  quick  276 passed / 11 skipped in 6.18s
  ruff   clean over the whole tree
  15 slowest: test_extract::test_detect_walls_on_clean_plan 0.75s;
              test_extract::test_fp_extract_cli_end_to_end 0.30s;
              test_macro::test_fp_macro_cli_pup_resize 0.29s; rest <= 0.12s.
  Note: the suite is fast because nothing in it is large. No test exceeds ~5
  group members and none exceeds 36 rooms — which is precisely why P0.3 exists.

P0.2  done
ruff:    clean
pytest:  287 passed, 0 failed, 0 xfailed, 0 skipped in 6.67s
files:   FloorPlanner.py (4 private re-exports removed);
         test_inventory.py, test_coalesce.py, test_walls.py, test_rooms.py
         (direct submodule imports);
         test_rooms/test_view/test_groups/test_selection (phase comments only)
notes:   NO assertion changed — import source + comments only.
         Touches list was wrong in three ways and the code was followed instead:
         test_io.py listed but references none of the names (left alone);
         test_inventory.py (_money) and test_walls.py (_coalesce_wall_impl)
         not listed but did need the switch. Correct call.
         Phase annotations corrected after review:
           room._detect_sig  -> P3.5   (refresh_rooms memoization)   confirmed
           win._sel_order    -> P3.5   (room_boolean rewrite)        confirmed
           dup._path         -> P0.5   (NOT Phase 3 — see below)     corrected
           g._angle          -> P4.5   (group semantics)             confirmed
           view._zoom_accum  -> none   (NOT scheduled for removal)   corrected
         dup._path: test_selection's duplicate comes from select_in_rect ->
         synthesize_room_edge, which P0.5 fix 4 removes. Retired at P0.5, not
         Phase 3.
         view._zoom_accum: wheel coalescing is a deliberate, documented perf
         feature (CLAUDE.md, view.py:159-179) that the migration KEEPS and
         copies to drags. Nothing deletes it. The assertion is brittle (an exact
         accumulator value of 400) but that is a test-quality nit, not a
         migration hazard.

P0.3  done   (commit 12024f1; b00af84..12024f1 = four rollback points, unpushed)
ruff:    clean
pytest:  289 passed, 2 xfailed, 0 failed in 8.72s
         --quick: 276 passed, 15 skipped in 5.46s (harness behind `slow`, as intended)
files:   tests/test_scaling.py (new)
notes:   No existing test touched. Ratios recorded WITHOUT weakening the
         threshold, per acceptance — group and ungroup are xfail(strict=False)
         -> P3.8; rebuild and bake assert hard.
         Numbers surfaced via warnings.warn (visible under plain -ra) rather
         than print (captured and hidden unless -s). Adopted as the convention.
         FINDING: room detection is clipped to canvas_rect() (rooms.py:29), so
         the n=8 grid (960") overflowed the default 840" canvas and edge rooms
         went undetected until the canvas was enlarged. Logged as defect 16.

P0.3b  done   (commit 43e838b; step 3 landed separately, see below)
ruff:    clean
pytest:  289 passed, 3 xfailed in 9.19s
         --quick: 276 passed, 16 skipped (all 5 scaling tests skipped)
files:   tests/test_scaling.py (fifth timed op; no other test touched)
notes:   Selection-building is the worst-scaling op measured, and the one
         nothing was timing before Ctrl+G.
           select   2.7 ms (16 rooms) -> 71.8 ms (64 rooms)   ratio 27.07  XFAIL
         27 is ABOVE the quadratic reference of 16 -> confirmed O(R^2 * W): each
         setSelected fires _update_edit_actions -> _selected_room_shapes(), which
         reruns bounding_walls() (QPainterPath booleans) for every already-
         selected room. ACCEPTANCE FIGURE: selecting all 64 rooms one at a time =
         71.8 ms HEADLESS -- excludes ALL repaint cost (FullViewportUpdate, no
         setCacheMode), so the felt stall is this PLUS a full-scene repaint per
         click, i.e. strictly worse. xfail(strict=False) -> P3.8. Nuance: P3.5's
         stored outlines cut the per-room W constant, but the O(R^2) recompute
         STRUCTURE lives in _selected_room_shapes and may not clear until P4.5.

P0.3b-step3  done
ruff:    clean
files:   pytest.ini (register `perf` marker); tests/test_scaling.py (tag every
         test perf + slow); .github/workflows/ci.yml (test step -> -m "not perf")
notes:   Precondition for the first push. `perf` and NOT `slow`, deliberately:
         excluding `slow` from CI would also drop the deterministic slow tests
         (fp_extract CLI, macro CLI subprocess) worth running there. Only the
         timing-ratio assertions are unsafe on shared runners. --quick behaviour
         unchanged (scaling tests keep `slow`).

P0.4  done
ruff:    clean
pytest:  294 passed, 6 xfailed in 10.42s
files:   tests/test_characterization.py (new)
notes:   6 behaviours pinned; no existing test modified. Passes: opening-s under
         group move AND rotate; delete-wall keeps the room (2a); grouped walls
         exempt from coalesce_all; group/ungroup 4x fixed point. xfail: 2b
         delete-actually-removes-the-wall (P4.1), group survives roundtrip
         (P4.5), group+move+undo restores (P4.5).
         FINDING that reshaped the task: test 2 was predicted xfail->P4.1 but
         PASSED. Diagnosed: the room survives because the wall is never deleted
         -- fracture_delete_wall keeps the perimeter stretch and rebinds it
         (measured 4 walls in, 4 out, 0 open edges). A single "room survived"
         test passes in both today's and P4.1's world, so it proves nothing about
         the change. Split per the amended plan into 2a (invariant, asserts hard,
         must never regress) and 2b (wall actually gone: 3 built + 1 open edge,
         xfail->P4.1). Refused deletion with no message = defect 17.

P0.5  done   (5 fix commits 947ae4f..76c32ee + 1 gate-resolution commit)
ruff:    clean
pytest:  298 passed, 6 xfailed, 0 failed, 0 xpassed in 9.14s
files (source): rooms.py (fix1 RoomItem.itemChange + sip import),
         mainwindow.py (fix2 dict(it.properties); fix3 refresh_rooms_cmd active-
         floor scope), view.py (fix4 select_in_rect read-only),
         catalog.py (fix5 price overrides -> config_dir, merged on load).
TESTS ADDED (one per fix): test_rooms::test_removing_room_unbinds_its_walls;
         test_io::test_project_from_scene_copies_room_properties;
         test_floors::test_refresh_rooms_cmd_spares_inactive_floor_rooms (two
         floors, inactive-floor room survives -- per acceptance);
         test_ai_pricing::test_apply_prices_writes_config_not_manifest +
         test_price_override_reloads_from_config.
TESTS CHANGED (each a red flag, named per the working agreement):
       * fix 4 (authorised): test_selection.py's two defect-asserting tests
         rewritten to assert selection creates nothing --
         test_room_edge_on_party_wall_is_not_duplicated,
         test_party_wall_edge_selection_leaves_the_door_intact; module docstring
         updated; the P0.2 dup._path assertion retired here as scheduled.
       * fix 5 (necessary consequence): test_apply_prices_updates_manifest_and_
         catalog asserted the defect (a manifest write) -> replaced with
         test_apply_prices_writes_config_not_manifest; manifest_guard fixture
         (existed only to restore the mutated asset) -> price_sandbox (redirects
         override path to tmp); test_placed_item_picks_up_price and
         test_dialog_fetch_applies_without_network switched to it.
       * gate fallout from fix 4 (NOT anticipated in the 3 named tests):
         test_groups::test_extracted_room_region_follows_move failed -- its
         "extract via rubber-band" workflow stood on the synthesis fix 4 removed.
         Root cause: old select_in_rect synthesised the party edge AND the
         following rebuild rebound the room to that private copy, so bake's strict
         room_owns_walls could carry it. Decision (a): xfail -> P4.2, logged in
         Known regressions; label-drag (_privatize_shared_walls) is the workaround.
       * XPASS resolved: test_characterization::test_group_move_undo_restores
         (was xfail->P4.5) PROMOTED to a hard pass -- fix 2 closed it (snapshot no
         longer aliases live properties). Verified first that test 3
         (group_survives_roundtrip) is STILL xfail, so P4.5's remaining half is
         still held; comment points at test 3 as the holder.
notes:   PROCESS: after this, run the FULL gate before each commit in a multi-part
         task, not just at the end -- fix 4 committed green on test_selection.py
         alone but red on the full suite (the extracted-room test). A targeted run
         proves the fix; only the full suite shows what else it touched.

P0.6  done   (item 1 commit c9451a5 + items 2-6/harness-split commit)
ruff:    clean
pytest:  300 passed, 4 xfailed, 1 xpassed in 8.44s
files:   mainwindow.py (item 1 debounce+cheap-count selection actions; item 3
         _update_totals off scene.changed onto the 180ms dirty timer),
         items.py (item 2 GroupItem._oriented_box cache; item 5 FurnishingItem
         DeviceCoordinateCache), rooms.py (item 4 cache QFontMetricsF x2 +
         boundary stroker), tests/test_scaling.py (split select op).
BEFORE -> AFTER ratios (t(2n)/t(n), n=4->8; before = P0.6 start):
                       before        after
           rebuild     2.48          2.84         (paint items don't touch it)
           select      25.90/75.5ms  -> SPLIT:
             select_burst              5.56 / 1.1ms   HARD PASS (debounce)
             select_interactive        3.63 / 6.6ms   HARD PASS (cheap-count)
           group       12.37         10.92        (still xfail -> P3.8)
           bake         4.53          4.69
           ungroup      8.56          5.62         (item 2's _oriented_box cache
                                                    cut its boundingRect cost.
                                                    Kept xfail(strict=False)->P3.8
                                                    -- see below: the sub-8 is
                                                    incidental, not a real fix.)
ITEM 1 (the headline): selecting all 64 rooms 75.5ms -> select_interactive 6.6ms
         (~11x on the honest per-click model; ~44x on the coalesced single pass).
         Split per the amendment: select_burst (no pump; debounce does the work)
         and select_interactive (processEvents per click; cheap-count does it).
         Both clear the threshold, so both are HARD PASSES (was one xfail).
ITEM 6: measured NoIndex vs BspTreeIndex on the 64-room grid -- NoIndex wins
         every op (rebuild 3.4 vs 3.6, group 138.6 vs 148.1, bake 136.9 vs 162.6,
         ungroup 197.5 vs 229.6 ms). Default UNCHANGED, per "only if BSP wins".
notes:   Items 2-5 are paint-time wins the headless harness barely reflects
         (no repaint), so rebuild/bake/group ratios move within noise; they are
         behaviour-preserving (full suite green, no test changed except the
         harness split).
       * select_burst: CONVERTED to an absolute assertion (large < 5 ms), ratio
         assertion dropped for that op only. 0.2 ms -> 1.1 ms is timer-floor
         noise; a ratio on it is noise wearing a threshold's clothing. Fixed now
         rather than waiting for it to flap.
       * ungroup: kept xfail(strict=False) -> P3.8 deliberately, NOT promoted.
         ungroup_selected calls coalesce_all on release, which is O(walls^2) by
         construction, so ungroup is genuinely super-linear. The sub-8 at n=8 is
         incidental (item 2 cut the boundingRect constant) and reasserts at
         larger n. Promoting would encode "ungroup is fine" -- false; only "less
         bad at n=8". P3.8's topology ops replace coalesce_all.

P0.7  done
ruff:    clean
pytest:  304 passed, 4 xfailed, 1 xpassed; pytest -m io = 38 passed (corpus)
files:   floorplanner/design/ (new pkg: __init__.py, validate.py, and the
         schema moved in via git mv from docs/); tools/validate_design.py (now a
         thin CLI over the package); tests/test_schema.py (new); requirements-
         dev.txt (+jsonschema); .github/workflows/ci.yml (+corpus-validate step);
         pyproject.toml (packages += floorplanner.design; package-data += the
         schema); docs/design-schema.v5.md (pointer); path refs updated in
         CLAUDE.md, DESIGN_MODEL_v5.md, SANITY_CHECK.md, and this plan's header
         + P0.0 block.
notes:   check(doc)->list[str] ported VERBATIM (pure Python, no third-party
         import) so it is safe to call from the app; JSON-Schema validation is a
         separate schema_errors() that LAZY-imports jsonschema -- a dev/test dep
         (requirements-dev.txt), never shipped, so importing floorplanner.design
         never requires it. Corpus results: symmetricP1 + site_demo schema PASS /
         invariants PASS; planc1.v5 schema PASS but 23 invariant errors incl I6
         -- test_corrupt_fixture_passes_schema_but_fails_I6 pins that (the "does
         not launder its input" guard). test_corpus_discovered guards against a
         rename silently emptying the parametrized corpus.
         The schema MOVED (git mv, not copied) into the package as packaged data;
         docs/ keeps design-schema.v5.md as the pointer. The CLI now defaults its
         schema to the packaged one and inserts the repo root on sys.path so it
         runs from any cwd (the package is not pip-installed; tests reach it via
         conftest). Ran only P0.7 as specified -- the actions/checkout@v5 +
         setup-python@v6 bump is deliberately held for a standalone commit at the
         top of Phase 1 (changing the CI environment is a different risk class
         from adding a step, and CI runs once per push).

GATE 1  manual sanity check — PASSED (user-run, 2026-07-26)
scope:   Phase 0 complete, format unchanged, CI green py3.10 + py3.13
result:  regression sweep clean; five P0.5 fixes verified; known regression
         (party-wall room via rubber-band) confirmed as expected; selection
         responsiveness confirmed improved.
meaning: the Phase 0 safety net is validated three ways — 304-test suite, CI on
         two Python versions, and a human using the application. Phase 1 may
         proceed. Next manual gate is Gate 2, after P2.2.

CI-bump  done   (commit 58590a2, pushed alone)
         actions/checkout@v5 + setup-python@v6. Shipped alone at the top of
         Phase 1; CI green on py3.10 + py3.13, Node-20 deprecation warning gone.

P1.1  done
ruff:    clean
pytest:  308 passed, 4 xfailed, 1 xpassed (+4 from test_design_model.py)
files:   floorplanner/design/model.py (new); floorplanner/design/__init__.py
         (+model exports); tests/test_design_model.py (new).
notes:   Qt-free dataclasses (Level, Vertex, Wall, Opening, Room, OutlineEdge,
         Furnishing, Group, Provenance, Design) over the v5 schema. from_dict/
         to_dict driven by a per-class FIELDS table; sub-structures the schema
         gives no object type (settings, anchor, placement, label, properties,
         pos, provenance fields) ride as RAW values.
         BYTE-IDENTICAL round-trip verified for symmetricP1.json AND site_demo.json
         -- both dict== and json.dumps== (not just the required symmetricP1). The
         crux is a _MISSING sentinel via d.get(k, _MISSING): a present-with-null
         field (free wall left: null) is kept null; an absent field (a room with
         no area_accounting) stays absent, never emitted as null. A dedicated test
         pins that distinction.
         WHY _MISSING IS LOAD-BEARING BEYOND P1.1: P2.1's "a v5 file never opens
         dirty" promise rests ENTIRELY on Design.from_dict(x).to_dict() == x. Had
         the model normalised absent -> null, every v5 file would round-trip
         structurally different from what was written and open dirty on every
         load -- and that bug would surface in Phase 2, months after the real
         cause. So this fidelity is a P2.1 dependency, not a P1.1 nicety.
         ZERO Qt: model.py imports only the stdlib. test_model_imports_zero_qt
         execs the file in ISOLATION (bypassing floorplanner/__init__, which star-
         imports the Qt scene layer) and asserts no PyQt6 module was pulled in --
         so it catches a stray Qt or floorplanner import, not just a direct one.
         No behaviour, no callers yet (the scene<->design bridge is P1.4/P1.5).
         Not pushed -- Phase 1 pushes at its end (or on the v5-topology branch for
         Phase 3), per the push policy.

P1.2  done
ruff:    clean
pytest:  312 passed, 4 xfailed, 1 xpassed
files:   floorplanner/design/validate.py (deep split + docstring); tests/
         test_schema.py (deep-gating + two negative tests); tests/
         test_design_model.py (planc1.v5.json added to the round-trip set).
notes:   COUNT CORRECTED (my error, was propagating): 15 named checks, not 14 --
         I1-I14 plus I5b. Split: deep-only 3 = I5b, I11, I14 (the O(n^2) ones);
         always-on 12 = I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I12 I13. Verified on the
         corpus: planc1.v5 trips I11 (deep) + I6 (always-on); deep=False drops
         I11 but still reports I6.
         DEFAULT = deep=True, and this FLIPS the "cheap by default" wording in my
         earlier P1.2 amendment (a894221) -- called out here because a changed
         decision is a red flag too. Rationale: forgetting deep=False on the hot
         path is a loud slowdown; forgetting deep=True on load/import is SILENT
         corruption (exactly where I11/I14 matter most). Loud failure wins. The
         per-command path (P1.6 --verify-design) opts out with deep=False; the
         CLI and corpus tests keep the default and validate fully -- no caller
         change needed.
         Negative tests each FAIL the check (not just not-crash): I14 fires on a
         welded corner split into two vertices 0.3" apart AND does not fire under
         deep=False (proves the gate); I6 fires on a wall side that disagrees with
         the room outlines.
         Also (riding with P1.2): planc1.v5.json added to the P1.1 round-trip --
         byte-identical, exercising wall: null open edges + a provenance block
         (three fixtures now). And recorded that _MISSING is a P2.1 dependency
         (see the P1.1 entry above) with a matching line added to P2.1's
         acceptance -- "opening a v5 file must not dirty it".

P1.3  done
ruff:    clean
pytest:  323 passed, 4 xfailed, 1 xpassed (+11 from test_topology.py)
files:   floorplanner/design/topology.py (new), floorplanner/design/legacy.py
         (new), floorplanner/design/__init__.py (+exports), tests/
         test_topology.py (new).
notes:   BOTH concrete acceptances hit exactly: trace_faces on symmetricP1
         recovers 19 room areas; weld_endpoints on legacy planc1.json welds 31.
         Per the three structural notes:
         (1) Ported to Design, not dicts: topology functions take and return
         P1.1 dataclasses; adjacency/pos are built from design.walls/vertices.
         (2) The one-shot legacy path is SEPARATE: weld_endpoints lives in
         design/legacy.py, on raw p1/p2 wall dicts (it runs at v1-v4 import,
         before a Design exists). Its lifetime ends when files are converted;
         split_edge/merge_collinear/trace_faces are forever. Not peers, so not
         in the same module.
         (3) Winding pinned by its own test: left = the (dy,-dx) side, verified
         79/79 walls-with-left on symmetricP1 (you said 61/61 -- the convention
         holds 100%, the count is 79). A second test ties trace_faces' winding
         to the stored `left`: the (dy,-dx) probe of a shared wall lands in a
         face whose area is the left room's. Without this, a flipped winding
         swaps every left/right and I6 still passes.
         The 19-vs-20: trace_faces returns 20 inner faces; exactly 19 match a
         stored room area. The sole unmatched room is the Garage (largest,
         boundary-touching) -- its face IS the outer boundary that _inner_faces
         drops. A test asserts unmatched == {Garage}, not just the count.
         Forward-looking ops (split_edge, merge_collinear, planarize) are pure
         Design->Design and tested for the invariant that matters -- they
         preserve trace_faces (rooms unchanged); planarize is idempotent on the
         already-planar corpus. DEFERRED with a note in the code: opening
         redistribution across a split, and crossing-point insertion, land at
         P3.3/P3.4 where the wall-move split rule is built -- split_edge leaves
         openings on the first segment for now.
         Zero Qt: model.py proven by isolated exec (P1.1); topology.py and
         legacy.py asserted Qt-free at the source level (no PyQt import; their
         only floorplanner imports are floorplanner.design.*), since importing
         them via the package would pull Qt through floorplanner/__init__.
         Not pushed -- Phase 1 pushes at its end.

P1.3-followup  done   (responding to the two P1.3 flags)
ruff:    clean
pytest:  324 passed, 4 xfailed, 1 xpassed (+1: split_edge raises-on-openings)
files:   design/topology.py (split_edge guard), design/legacy.py (docstring),
         tests/test_topology.py (raises test), docs/CODE_REVIEW_v2.md (defect 18),
         docs/V5_MIGRATION_PLAN.md (P1.4 acceptance amended).
notes:   FLAG 1 (landmine) fixed: split_edge no longer leaves openings on the
         first segment -- it RAISES NotImplementedError naming P3.3 on any wall
         carrying openings. P3.3 removes the guard as it builds redistribution.
         pytest.raises(match="P3.3") pins it. Same principle as deep=True: the
         failure mode is loud, at the call site, not a rendering oddity three
         tasks later.
         FLAG 2 (probe the unmatched face): I checked, and it is TWO findings,
         not the benign "no" branch.
         - The unmatched 60.6 sf face's centroid is inside NO room (Garage
           included) -- a genuinely unclaimed wall-bounded region in symmetricP1.
           Not an M-Bath-class outline/wall disagreement; a corpus observation.
         - Digging further: the Garage (868.5 sf) IS a valid raw traced face
           (9 edges) -- it is not unenclosed. _inner_faces DROPS it because its
           "drop the largest inner face as the outer boundary" heuristic is
           unsound: the true outer boundary (4535 sf) is opposite-wound and
           already excluded by the majority-sign filter, so inner[1:] discards
           the biggest ROOM. The migrator masks this (per-room enclosing_face
           recovers the room); standalone trace_faces loses it. Logged as
           DEFECT 18 -> P3.5 (identify the boundary by winding, not area).
         So the P1.3 "19 not 20" is really: Garage wrongly dropped by the
         heuristic + a separate 60.6 unclaimed region. The unmatched=={Garage}
         test still holds and still cannot pass for the wrong reason.
         Also corrected legacy.py's docstring: it is PRE-VERTEX geometry (raw
         p1/p2), used by BOTH the v4 importer (P2.1) AND design_from_scene (P1.4,
         scene still p1/p2 until P3.1) -- not purely import-only. Retired at P3.1.

P1.3b  done   (defect 18 fix + corpus diff, before P1.4)
ruff:    clean
pytest:  324 passed, 4 xfailed, 1 xpassed
files:   design/topology.py + tools/migrate_to_design_v5.py (_inner_faces /
         inner_faces fix), tests/test_topology.py (test updated to the fixed
         behaviour), docs/CODE_REVIEW_v2.md (defect 18 -> fixed), this plan
         (P1.3 acceptance 19->20).
notes:   FIX: _inner_faces now keeps the majority winding and drops ALL
         opposite-wound faces (one outer boundary per connected component --
         a detached garage or a Phase-4 floating room each has its own), never
         by size. Retargeted defect 18 P3.5 -> P1.3b and fixed NOW: P2.1's
         import traces outlines, so the old heuristic would have silently fallen
         back to stored corners for the largest room of every imported plan --
         user-facing, four tasks out. Fixed in BOTH topology.py and the migrator.
         Result: trace_faces on symmetricP1 now recovers all 20 rooms (Garage
         included), plus one extra face for the 60.6 sf unclaimed region.
         CORPUS DIFF (the required check): regenerated symmetricP1 with the fixed
         migrator (migrate(planc1.json, --clean --name "Symmetric P1"), the
         command that produced the committed file) and diffed. Result: GEOMETRY
         IDENTICAL -- Garage 868.5 sf both ways, same 9 edges, same cycle; the
         only file change is the Garage outline's start vertex rotating (the
         migrator now TRACES the Garage, rooms_traced 19->20, instead of the
         stored-corners fallback). So the Garage's stored outline AGREES with
         its traced face -- NOT an M-Bath-class disagreement. Per the decision
         tree that is the "identical" branch: the fixture STANDS, not
         regenerated (a cosmetic loop-rotation is not worth churning a fixture
         that P1.1/P1.4/P1.5/P1.6 pin). Had they disagreed, that would have been
         a corruption baked in by luck (the buggy fallback) -- they don't.

F5-correction  done   (doc-only commit e613b5d, taken BEFORE the P1.4 code)
ruff:    n/a (doc only)
pytest:  n/a
files:   docs/CODE_REVIEW_v2.md (F5 rewritten + a correction note),
         docs/DESIGN_MODEL_v5.md (section 6 sentence; a note at the head of 7a)
notes:   F5 and section 6 both said the editor welds "on every draw release and
         on load". The "on load" half is FALSE: apply_project_to_scene
         (mainwindow.py:1298) runs coalesce_all + rebuild_all_walls and no
         weld_all. Welds happen only at draw release (view.py:489) and via
         Edit > Coalesce all walls now (mainwindow.py:821).
         Corrected mechanism, verified in the source: coalesce is itself a gap
         SOURCE -- _coalesce_wall_impl (walls.py:200-201) re-snaps the survivor's
         p1/p2 onto the 6" on-centre grid independently of whatever neighbour an
         end was welded to, so it can pull a previously-welded end off its
         partner. Gaps are created and accumulated by the app's own pipeline and
         survive every round-trip, rather than merely failing to persist a weld
         the app already performed.
         CONSEQUENCE FOR P2.1, recorded in 7a: weld-on-load is NEW, deliberate
         repair behaviour the app has never applied to a user's file -- not
         persistence of something it already did. That strengthens the
         conversion report and the dirty flag rather than weakening them.

P1.4  done   (commit c78cb5e)
ruff:    clean
pytest:  337 passed, 4 xfailed, 1 xpassed in 10.16s (+13 from
         test_design_bridge.py; 324 -> 337, no other count moved)
files:   floorplanner/design/bridge.py (new), floorplanner/design/legacy.py
         (+VertexTable, +split_params -- PURELY ADDITIVE, weld_endpoints is
         byte-identical), floorplanner/design/__init__.py (docstring only),
         tests/test_design_bridge.py (new, 13 tests)
notes:   NO EXISTING TEST TOUCHED -- `git status` showed two modified source
         files and two new files, nothing else.
         The three notes, as built:
         (a) LEVEL-SCOPED BY CONSTRUCTION, not by filter. _by_floor() buckets the
         scene once; each level's walk receives ONLY its bucket, and the vertex
         table, wall graph and room polygons are per level. There is no global
         query left to forget to filter -- defect 12 closes structurally.
         test_walk_is_level_scoped builds two GEOMETRICALLY IDENTICAL rooms on
         two floors (coincident coordinates are precisely what a leaking walk
         would fuse) and asserts the levels share no vertex.
         (b) Outlines from RoomItem.corners, never trace_faces.
         (c) legacy.py grew the two pre-vertex helpers the walk needs:
         VertexTable (weld-on-insert at WELD_TOL 0.6") and split_params (cut at
         junctions + every room corner, so one wall spans one outline edge).
         THE WELD DECISION, resolved explicitly before any code: weld_endpoints
         is a CHECK, never an edit. It runs on a deepcopy to count what it WOULD
         move; the emitted geometry is always the scene's own. Non-zero ->
         report["unwelded_ends"] + a warning, and strict=True raises (the P1.6
         --verify-design hook). Rationale: silently welding would have made
         P2.2's Save move a user's walls up to 9", and would have made P1.6's
         shadow comparison diverge from the scene it shadows. Only the 0.6"
         weld-on-insert runs for real, and at that tolerance two points ARE one
         vertex -- representation, not repair.
         ACCEPTANCE: room areas match project_from_scene() EXACTLY (not merely
         within 0.1 sf) on planc1.json, sample_plan.json and fixture scenes.
         sample_plan walks fully clean: check(deep=True) == [], 0 unwelded ends,
         0 open edges, and schema_errors() == [] too. planc1 reports 17x I6 +
         1x I11 -- asserted as measured, per the acceptance, not forced to [].
         Same fault classes as its v5 fixture (I6 + I11), as predicted.
         FINDING 1 -- the 31 is a count of ATTEMPTS, not of damage. My checker
         reports 5 unwelded ends on planc1, not 31. Cross-checked: weld_endpoints
         returns 31 on the FILE geometry and 31 on the SCENE geometry -- identical,
         so the scene->raw-walls extraction is faithful and load's coalesce
         changed nothing here (46 walls in, 46 out). The 31/5 gap is the counting
         method: 31 counts weld OPERATIONS, and 26 of them are no-ops on
         junctions that are already exact. Measured displacements: 4 ends move
         1.529" (the documented divider gaps, y 655.529 -> 654.0) and 1 moves
         0.001" (float noise). So "31 wall ends were welded" in section 6 and in
         7a's user-facing conversion message overstates the geometry actually
         changed by ~6x. The P1.3 acceptance pinning 31 is still correct (it
         pins the function's return) and its test is untouched -- but 7a's
         message to the user should probably say "4 wall ends moved", not "31
         welded". FLAGGING, not editing: that is user-facing copy.
         FINDING 2 -- the SCENE's planc1 corruption is worse than the FILE's.
         On disk Hall and M Bath differ (243.5 sf / 18 corners vs 591.6 sf /
         24 corners). Load re-detects rooms, the 1.5" gap leaks the flood-fill,
         and BOTH label anchors resolve to the same merged region: they come out
         as the SAME 21-vertex loop at 243.5 sf each. I11 is firing on an exact
         coincidence, not a partial overlap. The test asserts the shared vertex
         set, so it cannot pass for the wrong reason. P2.1's repair has to fix
         a worse input than the file suggests.
         THREE CALLS the task text did not specify (all endorsed before coding):
         bridge.py is the home, and is deliberately NOT re-exported from
         design/__init__.py so model/topology/legacy/validate stay importable
         without the Qt scene layer; groups emit [] (defect 3 -- a grouped wall
         has no single id here, it splits into segments; emitting a guess would
         make characterization test 3 pass for the wrong reason, and both close
         at P4.5); settings.area_basis is "centerline", NOT the migrator's
         "inside_face", because the scene's areas ARE centreline areas and
         declaring the better basis would itself be a repair.
         Not pushed -- Phase 1 pushes at its end, per the push policy.

P1.4-followup  done   (doc-only; responding to the two P1.4 findings)
ruff:    n/a (doc only)
pytest:  n/a
files:   docs/DESIGN_MODEL_v5.md (7a message + the two-counter rule),
         docs/V5_MIGRATION_PLAN.md (P2.1 task text; this entry)
notes:   FINDING 1 SETTLED -- two counters, with the threshold taken from the
         document's own semantics rather than picked: the schema defines
         vertex_weld_in = 0.6" as the distance at which two coordinates ARE one
         vertex, so a displacement at or below it is not a geometry change BY
         DEFINITION. weld_ops = operations performed (31); ends_moved =
         displacement > 0.6" (4). Only ends_moved is ever shown to a user or
         written to provenance.endpoints_welded -- whose schema description
         already reads "Wall ends MOVED onto a neighbour", so the corrected
         reading is what the schema always meant and the fixture's stored 31
         contradicts its own field. 7a's example message now reads "4 wall ends
         moved to close gaps (31 junctions checked)".
         symmetricP1.json's provenance is NOT regenerated now -- deliberately.
         P1.1/P1.4/P1.5/P1.6 all pin that fixture; regenerating mid-phase is
         churn for a semantics fix P2.1 implements properly. Folded into P2.1's
         task text instead.
         FINDING 2 MADE BINDING -- P2.1's task text now REQUIRES the importer to
         derive outlines from the welded FILE geometry, never from the scene's
         re-detection, and cites the measurement: loading planc1 collapses Hall
         and M Bath into one identical 21-vertex region (both 243.5 sf, same
         vertex set), where the file keeps them distinct (243.5/18 corners vs
         591.6/24 corners). The scene's belief about a corrupt file is STRICTLY
         WORSE than the file. test_planc1_reports_its_real_faults pins the shared
         vertex set and is named in the plan as the guard.

P1.5  done   (commit 2678ff5)
ruff:    clean
pytest:  347 passed, 4 xfailed, 1 xpassed in 12.27s (+10; 337 -> 347)
files:   floorplanner/design/bridge.py (+apply_design_to_scene, +_canonicalize,
         +geometric ordering in the walk), tests/test_design_bridge.py (+10)
notes:   NO EXISTING TEST TOUCHED -- git status showed exactly two modified
         files, both mine. Existing IO and undo tests green unchanged.
         ACCEPTANCE MET on sample_plan.json AND planc1.json: scene -> Design ->
         scene -> Design is dict-identical at the second Design. planc1 is in
         the round-trip set deliberately -- a corrupt plan must round-trip as
         faithfully as a clean one; had apply quietly repaired the Hall/M Bath
         collision the second Design would be "better" and the bridge would be
         lying about what it holds.
         THE FINDING THAT SHAPED THE TASK -- ids were not canonical. The first
         round trip came back ISOMORPHIC BUT UNEQUAL: identical counts
         (8/8 vertices, 10/10 walls, 3/3 rooms on sample_plan; 61/80/20 on
         planc1) with different ids. Cause: P1.4 minted ids in EMISSION order,
         which is source-wall order, but apply turns each split segment into its
         own WallItem, so the second walk visits the same geometry in a
         different order. Fixed with _canonicalize: vertices sorted by
         (level, x, y), walls by (level, v1 pos, v2 pos, type), rooms by
         (level, name, centroid), furnishings by (level, pos, kind, rotation),
         openings renumbered along the wall -- then ids assigned and every
         reference rewritten. The walk's per-level item lists are sorted
         geometrically too, so the vertex-table weld order is deterministic.
         This is the same z-independence Project.to_dict already gives the v4
         snapshot (model.py:211-224) and for the same stated reason; P2.3's undo
         comparison needs it as well. A test pins it directly: bring a wall to
         the front, re-walk, document unchanged.
         The four mirror notes, as built:
         (1) NO coalesce/weld/detection in apply. Pinned by an OFF-GRID plan
         (205x101 at (7,3), no corner on the 6" wall-snap grid): a coalesce pass
         would re-snap the endpoints and the test asserts the exact
         coordinates survive.
         (2) Rooms READ, never re-detected. Ordering does the work --
         rebuild_all_walls runs BEFORE any RoomItem exists, so refresh_rooms
         returns at `if not rooms: return` and no flood-fill can overwrite a
         stored outline. Each room's _detect_sig is then primed via the public
         room_signature(scene, room) so a LATER rebuild also leaves it alone;
         the test asserts d1 == d2 across an explicit rebuild_all_walls.
         (3) Openings invert exactly. _opening_s is the algebraic inverse of the
         s -> anchor conversion, and the test compares openings wall-by-wall
         across planc1's 20+ openings (with a guard that the corpus has not
         silently got weaker), not just a count.
         (4) floor assigned from the level explicitly on every wall, room and
         furnishing. The test sets active_floor to the WRONG floor before
         applying, so anything trusting the active_floor() global lands
         visibly wrong.
         TWO SMALL CALLS: apply collapses the scene's anchor + label_offset into
         the anchor (v5 stores ONE label offset, relative to the centroid --
         the schema's stated intent), which round-trips exactly; and
         keep_backdrop / reference-image retention is deliberately NOT handled
         here, it belongs with the undo-restore path at P2.3.
         Opening failures are COLLECTED and surfaced (report["openings_failed"]
         + warning, strict=True raises), not dropped by the v4 path's silent
         `except ValueError: continue` -- pre-figures P3.6.
         Not pushed -- Phase 1 pushes at its end, after P1.6.

P1.6  done
ruff:    clean
pytest:  OFF  364 passed, 4 xfailed, 1 xpassed in 11.84s
         ON   364 passed, 4 xfailed, 1 xpassed in 12.50s   <- THE ACCEPTANCE
         DEEP 360 passed, 3 xfailed, 6 deselected in 11.23s  (-m "not perf")
files:   floorplanner/design/verify.py (new), floorplanner/mainwindow.py (3
         hooks + import), floorplanner/app.py (--verify-design -> env var),
         floorplanner/design/bridge.py (rebase at the end of apply),
         tests/conftest.py (fixture rebase + teardown verify),
         tests/test_verify_design.py (new, 17), .github/workflows/ci.yml
         (second suite run with the flag on), docs/CODE_REVIEW_v2.md (defect 19)
TEST CHANGED (declaring it, per the working agreement): tests/test_rooms.py
         `_overlapping_rooms` gained a `rebase(win)` call. NO assertion changed
         -- it declares that the helper's overlapping rooms are the deliberate
         INPUT to room_boolean, the same "this state is accepted" mechanism a
         corrupt legacy file uses at load. See finding 2.
notes:   Hooks at quiescent points only, never scene.changed (mid-operation the
         scene is legitimately inconsistent): _commit_if_changed before the
         snapshot (cheap twelve), save (deep), load (deep + REBASE), and the
         conftest fixture teardown -- that last one because the 180 ms dirty
         timer NEVER FIRES HEADLESS, so without it the suite would verify
         almost nothing.
         FINDING 1 -- unwelded_ends must NOT raise, and this contradicts the
         spec I was given ("same treatment as an invariant class"). Two
         independent reasons, both measured:
         (a) THE SCHEMA FORBIDS IT. join_tol_in is documented as "GESTURE
         TOLERANCE ... Never an invariant: a wall deliberately stopping 6"
         short of another is a legitimate design (a reveal, a pilaster gap),
         and nothing may silently close it." Raising would fail a user for
         drawing a reveal.
         (b) IT IS NOT A DOCUMENT PROPERTY. apply_design_to_scene rebuilds
         planc1 from a BYTE-IDENTICAL Design and the count goes 5 -> 15,
         because Design walls are edge-granular and a wall split at its
         junctions has more ends to be near things with. A metric that moves
         while the document is provably unchanged cannot be a document
         invariant. Resolution: REPORT_ONLY -- carried in the profile, warned
         once when it rises, never raised on. The real weld invariant is I14 at
         the 0.6" modelling tolerance, and that stays in the raising set.
         A test pins REPORT_ONLY's contents so adding to it can't silently
         disarm an invariant.
         FINDING 2 -- one I11 fired, and it is NOT a defect. Under the deep
         sweep, test_rooms::test_room_op_needs_two_rooms tripped "I11 two placed
         rooms overlap". Diagnosed rather than suppressed: the overlap is built
         by the `_overlapping_rooms` helper as the deliberate input to
         room_boolean, and the operation under test is a no-op by design, so
         nothing INTRODUCED it. Declared with a rebase in the helper.
         FINDING 3 -- defect 19, a real one. extract_from_reference writes
         detected walls into the scene and commits with no weld pass; per the
         corrected F5 nothing welds them later either. Every extracted plan is
         born with open junctions -- the exact condition that leaks room
         detection between spaces. Measured: 2 unwelded ends on the test_extract
         fixture. Logged -> P2.1. Note it is NOT caught by the gate (it is an
         unwelded_ends rise, which is report-only per finding 1), so it needs
         fixing on purpose.
         ON THE INVARIANT SCORE, honestly: ZERO invariant classes fired from
         app operations. Given this migration's hit rate I did not expect that,
         so I checked rather than celebrated -- which is what FP_VERIFY_DESIGN=
         deep is for. It promotes every quiescent point to all fifteen, so the
         sweep covers I5b/I11/I14 (the two that caught the real planc1
         corruption) across the whole suite, not just at save/load. Result after
         findings 2 and 3: still zero. Two honest caveats on that number -- the
         suite's scenes are small and mostly clean, and deep mode cannot run
         over the 64-room perf grid (O(rooms^2) + O(walls^2) per quiescent point
         is exactly what P1.2 split the invariants to avoid), so `-m "not perf"`.
         The acceptance run is the cheap twelve, as specced; deep is a
         diagnostic.
         CI now runs the suite TWICE per Python version, the second with
         FP_VERIFY_DESIGN=1. --verify-design on the CLI just sets the env var,
         so there is one switch however it is thrown.
         PHASE 1 COMPLETE. Ready to push (P1.1..P1.6 + the doc commits).

PHASE 1 PUSHED  (58590a2..52bd72e, 14 commits) -- CI GREEN on py3.10 + py3.13.
         Doubled suite: "Run tests" 14s / 15s, "Run tests with --verify-design"
         14s / 15s -- a clean doubling of the pytest step and nothing else
         (job total ~45s -> ~60s; the ~30s apt/pip setup is now amortised over
         two runs). NO cross-Python divergence with the flag on, which was a
         real risk worth measuring: P1.5's canonical sort keys are raw floats
         off QPointF, so a tie-break difference would have renumbered the
         document and broken the round-trip on one Python only. It did not.

P2.1  done   (commit ad62e66)
ruff:    clean
pytest:  OFF  377 passed, 4 xfailed, 1 xpassed in 12.51s
         ON   377 passed, 4 xfailed, 1 xpassed in 13.61s
         DEEP 373 passed, 3 xfailed, 6 deselected in 12.51s  (-m "not perf")
files:   floorplanner/design/importer.py (new), design/legacy.py
         (+weld_endpoints_counted), floorplanner/mainwindow.py (open_document,
         load_data split, _finish_open, defect 19), tools/migrate_to_design_v5.py
         (now a thin CLI), tests/test_load_path.py (new, 13),
         examples/symmetricP1.json + planc1.v5.json (surgical, see below)
notes:   NO EXISTING TEST TOUCHED.
         ACCEPTANCE HIT EXACTLY: planc1 opens at M Bath 182.0 sf / Hall 61.5 sf,
         provenance.endpoints_welded = 4, dirty; symmetricP1 opens clean and NOT
         dirty; the legacy file on disk is byte-identical afterwards (asserted).
         check(deep=True) on the converted document = 0 errors.
         FINDING 1 -- `load_data` was OVERLOADED, and migrating in it would have
         broken undo. It is the undo-restore path (mainwindow.py:896) AND a
         plain "apply this dict" helper used by a dozen round-trip tests. Had
         P2.1's migration gone there, EVERY UNDO would weld the geometry and
         re-trace every room -- a repair, not a restore, and silent. Split:
         `load_data` applies faithfully and never migrates (it now also accepts
         a v5 dict, routing to apply_design_to_scene); `open_document` is the
         file-open path that migrates, dirties and reports. load_path/open_plan
         call the latter. A test pins it with a divider stopping 1.5" short --
         geometry a weld WOULD move -- and asserts the gap survives an undo.
         The plan's task text says "Load path" as if it were one thing; it is
         two, and only one of them may repair.
         FINDING 2 -- a regression I introduced and caught: `active_floor` is
         VIEW state that the v4 FILE carries but the v5 Design deliberately does
         not (keeping it out is what stops a floor switch dirtying the
         document). Routing v4 opens through the importer silently forgot which
         floor the user was editing; test_floors::test_serialize_round_trip_two_
         floors caught it. Carried across by hand in open_document.
         FIXTURES: SURGICAL EDIT, NOT REGENERATION -- and the measurement is the
         reason. Regenerating symmetricP1.json produces TWENTY deltas: the two
         named (provenance.endpoints_welded 31->4, settings.area_basis
         inside_face->centerline) plus EIGHTEEN in rooms[5] -- the Garage
         outline's start vertex rotating, which is exactly the change P1.3b
         examined and deliberately declined to bake in ("the fixture STANDS,
         not regenerated"). A full regeneration would have silently reversed
         that decision. So the two fields were edited in place and the diff
         verified line-by-line: 3 changed lines across both fixtures, nothing
         else.
         THIRD FIXTURE DELTA, DECLARED: examples/planc1.v5.json also moves
         area_basis inside_face -> centerline. Not named in the brief, but it is
         the direct consequence of the approved importer decision, and leaving
         the corrupt fixture on inside_face would make the corpus disagree with
         the tool for no reason. Its corruption (I6 + I11) is untouched.
         FAITHFUL MODE PRESERVED. The importer keeps `clean=False`: it is what
         generates planc1.v5.json, the "does not launder its input" fixture from
         P0.7. Dropping it to serve only the load path would have orphaned that
         fixture. The CLI keeps naming ITSELF in provenance.tool, so
         symmetricP1's tool field did not move either.
         PROVENANCE IS RETAINED on the window (`_provenance`) rather than
         discarded after apply -- P2.2 needs it to write the audit trail into
         the saved file, and a v5 file that arrives with one keeps it.
         DEFECT 19 in-app arm closed: extract_from_reference now welds the walls
         it injects. Test asserts unwelded_ends == 0 after an extraction; it was
         2 before.
         CONCEPT-ROOM FIXTURE built as asked, because planc1 no longer exercises
         that path -- the weld closes its 1.5" gap, so M Bath and Hall now get a
         face each. The fixture is a single 20'x8' enclosure with TWO room
         labels and a chair in each half (the shape v4 produces because it never
         serialised open/archway edges). Pins: both rooms survive, the contest
         loser is category=concept + floating + extracted_from set, its outline
         edges are all wall:null, it is sized AROUND the furnishing it carried
         (asserted, not just counted), and check(deep=True) == [].
         FLAG for routing -- TWO THRESHOLDS FOR ONE IDEA. P1.6's bridge counts
         `unwelded_ends` at >1e-9 (reports 5 on planc1); this task's importer
         counts `ends_moved` at >0.6" (reports 4). Same underlying question,
         two numbers, which is the exact trap the 31-vs-4 episode was about. The
         0.6" floor is the principled one (it is the schema's own definition of
         "one vertex"). Aligning the bridge would change two P1.4/P1.6 test
         assertions, so I have NOT done it unasked -- flagging instead.

weld-floor  done   (commit e2a97b3; authorized follow-up to the P2.1 flag)
ruff:    clean
pytest:  377 passed, 4 xfailed, 1 xpassed (both flag OFF and ON)
files:   design/bridge.py (_weld_delta -> WELD_TOL), tests/test_design_bridge.py
notes:   One question, one floor. The bridge's telemetry counted movement above
         1e-9; the importer's ends_moved counts above 0.6". Now both use 0.6",
         the schema's own definition of "one vertex". The two NAMES stay
         distinct -- unwelded_ends is telemetry, ends_moved is a user report.
         ASSERTION CHANGED (authorized): test_weld_is_a_check_not_an_edit,
         planc1 unwelded_ends 5 -> 4. The dropped fifth is a 0.001" float nudge;
         the four real 1.5" divider gaps are unaffected, which is the point of a
         floor this small. The extract fixture stays at 0 (defect 19's weld at
         P2.1 already closed its 2 gaps, and they were far above 0.6" -- a floor
         this small does not launder a real gap). test_apply_design_rebases
         unaffected.
         ALSO CONFIRMED, in answer to the P2.1 report's omission: defect 19's
         in-app arm DID land at P2.1 (commit ad62e66) -- weld_all in
         extract_from_reference at mainwindow.py:1730 plus
         test_extracted_walls_are_welded. Only my summary dropped it; the
         register ticks correctly.

P2.2  done   (commit 6a7e5d4)
ruff:    clean
pytest:  OFF  386 passed, 4 xfailed, 1 xpassed in 13.35s
         ON   386 passed, 4 xfailed, 1 xpassed in 14.99s
         DEEP 382 passed, 3 xfailed, 6 deselected in 14.02s  (-m "not perf")
files:   floorplanner/design/canonical.py (new), design/bridge.py, design/
         importer.py, floorplanner/mainwindow.py (design_document, v5 save,
         legacy export), fp_extract.py, tests/test_load_path.py (+9),
         tests/test_floors.py (the authorized assertion), examples/
         symmetricP1.json + planc1.v5.json (regenerated)
notes:   ACCEPTANCE: save -> reopen -> check(deep=True) == [] and NOT dirty;
         legacy export round-trips through the old loader (asserted by loading
         it into a second window via load_data, the v4 path, and comparing room
         areas). Also pinned: save -> reopen -> save is a FIXED POINT, and
         opening a file the project wrote reproduces it exactly.
         THE ROTATION QUESTION, ANSWERED WITH A TEST rather than an assumption.
         It does NOT bite on save-reopen: apply builds RoomItem.corners in
         document order and the walk reads them back in that order, so rotation
         is carried, not regenerated (measured: Garage starts at (900.0, 12.0)
         both ways). The rotation delta was an artefact of REGENERATING the
         fixture, not of the save cycle. Per the ruling it is now moot anyway --
         canonical form DEFINES rotation.
         CANONICAL FORM MADE TOTAL. canonicalize() moved to design/canonical.py
         (Qt-free, so the importer can call it; it lived in bridge.py, which
         imports Qt) and now normalises outline rotation as well as ids: each
         loop restarts at its lexicographically-least (x, y) corner, orientation
         UNTOUCHED -- winding carries meaning, so reversing a loop would swap
         every wall's sides. Two tests pin it: outlines start at their least
         corner and canonicalize is a fixed point; and rotating every outline in
         the input produces byte-identical canonical output.
         FIXTURES REGENERATED, every delta class measured and named:
           symmetricP1.json  52/62 vertex ids renumbered; 0/20 room ids and
                             0/50 furnishing ids moved; 7/20 loops rotated
           planc1.v5.json    56/65 vertex ids; 0/20 and 0/50; 20/20 rotated
           BOTH: walls-as-coordinate-pairs IDENTICAL, vertex coordinate set
           IDENTICAL, room polygons identical as sets -- NO GEOMETRY MOVED.
           provenance identical, settings identical (area_basis and name carry
           over). planc1.v5.json still fails 23 invariants (I6 + I11), so the
           "does not launder its input" guard holds.
         THREE DATA LOSSES FOUND BY MEASUREMENT, not by a test failing. The
         P2.2 probe compared open(symmetricP1) -> design_from_scene against the
         file: vertices/walls/furnishings identical, but
           * rooms differed on exactly ONE field -- the Garage's
             area_accounting: "unconditioned" -- because the scene has no home
             for it. Fixed generally: v5 room/wall fields the scene cannot model
             are stashed on the item at apply and re-emitted by the walk, so
             category/placement/holes/nominal_size/thickness_in/finish_* survive
             a load-save too, not just the one field that showed up.
           * settings.name ("Symmetric P1") evaporated -- only DEFAULT_SETTINGS
             keys reach the global SETTINGS. Retained on the window.
           * provenance was dropped entirely. Now re-attached on EVERY save.
         ASSERTION CHANGED (authorized in advance; the third of the migration,
         and all three were declared before the fact): test_floors::
         test_serialize_round_trip_two_floors -- the file's remembered active
         floor moved from the top level to settings.active_floor, because the
         v5 root is a closed schema and settings is the designated open bag.
         Still absent from serialize(), so a floor switch still cannot dirty.
         fp_extract.py now calls export_legacy_v4_path, not save_path.
         Converting that writer is P2.4's, with the gallery/examples/macro
         tokens; save_path going v5 would have converted it early and out of
         step. Its output is not stranded -- opening a v4 file converts and
         welds it, which is defect 19's file arm.
         THE STASH'S LIFETIME, accepted rather than engineered around (recorded
         at review, and now a comment in bridge.py): the stash lives ON THE ITEM,
         so it survives ordinary edits but DIES WITH THE ITEM. A wall carrying
         thickness_in that is coalesced away, or a room deleted and re-detected,
         silently loses its stash. Acceptable only because these fields have no
         editor yet; P4/P5 model them properly (placement/nominal_size at
         P4.2-P4.4, area_accounting and finishes at P5.1-P5.3) and the stash
         retires then. Written down so it is a known limit, not a mystery.
         Not pushed -- Phase 2 pushes at its end.

P2.3  done   (commit bbe592c)
ruff:    clean
pytest:  OFF  393 passed, 4 xfailed, 1 xpassed in 15.33s
         ON   393 passed, 4 xfailed, 1 xpassed in 17.30s
         DEEP 388 passed, 3 xfailed, 7 deselected in 15.19s  (-m "not perf")
files:   floorplanner/mainwindow.py (snapshot, restore, dirty, serialize
         demoted), design/bridge.py (keep_backdrop, OpenWall rebuild, door_type),
         design/verify.py (reuse a caller's walk), tests/test_undo.py (+6),
         tests/test_scaling.py (snapshot + undo timings), tests/
         test_characterization.py + tests/test_io.py (the two assertions below)
notes:   snapshot() = canonicalize(design_from_scene().to_dict()), and undo,
         redo and the dirty flag are all defined on it. _restore_state applies
         through apply_design_to_scene with keep_backdrop (the retention
         deferred from P1.5). _is_dirty canonicalizes BOTH sides.
         ONE WALK per settled edit: _commit_if_changed builds the snapshot and
         passes it to verify(doc=..., walk_report=...) rather than walking the
         scene twice at the same quiescent point -- which also makes the latency
         number below honest instead of inflated by my own duplication.
         serialize() DEMOTED to the legacy exporter, with a comment naming its
         sole remaining caller and the release it dies with.
         GROUPS DO NOT CLOSE HERE, per the corrected task text. The bridge emits
         groups: [] until P4.5, so undo keeps dissolving groups exactly as
         today; I did NOT write the group-survives test. What is asserted is the
         narrower promise: undo after grouping restores the plan.
         WHY EDGE-GRANULAR RESTORE IS SAFE -- the canonical Design is
         GRANULARITY-INVARIANT. Whether the scene holds one long wall or three
         segments split at junctions, design_from_scene planarises to the same
         canonical document, so scene wall-count is PRESENTATION state, not
         document state. Pinned directly by
         test_undo::test_snapshot_is_granularity_invariant, which builds the
         same plan two ways and asserts one document. Consequences: (a) a test
         asserting scene wall counts across an undo is asserting presentation;
         (b) if coalesce re-merges collinear segments after a later edit, the
         document, dirty flag and undo comparison correctly do not notice.
         TWO REAL BUGS, found only because the restore now goes through the v5
         bridge:
           * OPEN WALLS were dropped. The v4 loader regenerated them via
             bind_room_walls -- which is DETECTION, and apply must not run it --
             so nothing rebuilt them. Undo silently ate every archway edge. apply
             now builds an OpenWall per `wall: null` outline edge; P3.7 retires
             the branch when null edges render dashed directly.
           * a WINDOW's door_type was clobbered to "". v5 carries door_type for
             DOORS only ("meaningful only when kind == door"), so absent means
             "not applicable", not "empty"; applying now leaves the scene's
             default alone. Caught by test_group_move_undo_restores, which was
             comparing v4 dicts.
         ASSERTIONS CHANGED (2, both presentation-vs-document, authorized in
         advance): test_group_move_undo_restores now compares snapshot() rather
         than serialize() -- v4 reported perimeter_corners ROTATED after an undo
         (same polygon, different first element) because canonical form
         normalises rotation; the polygon itself is now asserted separately so a
         REAL geometry change still fails. And test_unchanged_scene_is_not_
         falsely_dirty sets its baseline with snapshot(), as a save does.
         LATENCY BASELINE for P6.1, P0.3 grid, 16 -> 64 rooms:
           snapshot  2.1 ms -> 10.8 ms   ratio 5.10
           undo     22.0 ms -> 155.8 ms  ratio 7.09
         Guarded with ABSOLUTE bounds (undo < 500 ms, snapshot < 100 ms), not
         ratios: undo sits close enough to the threshold of 8 that a ratio
         assertion would flap -- the same call P0.6 made for select_burst. P6.1
         must make this independent of plan size; today it is not.
         KNOWN REGRESSION recorded in the table: after the first undo, a wall
         crossing a junction comes back split (measured by hand: one 480" wall
         with a mid-span T returns as two 240" walls), so body-dragging it moves
         half and leaves the neighbour. Checked deliberately rather than left
         for a user to find. Restored at P3.3/P3.4.
         Not pushed -- Phase 2 pushes at its end.

P2.4  done   (commit c085b8a)
ruff:    clean
pytest:  OFF  400 passed, 4 xfailed, 1 xpassed in 16.20s
         ON   400 passed, 4 xfailed, 1 xpassed in 17.78s
         DEEP 395 passed, 3 xfailed, 7 deselected in 18.35s  (-m "not perf")
files:   fp_extract.py (save_path), examples/make_examples.py, examples/
         README.md, examples/sample_plan.v5.json (new), tests/
         test_corpus_freeze.py (new, 6), tests/test_extract.py + tests/
         test_schema.py (the two assertions), gallery + example PNGs
ACCEPTANCE: `python docs/make_gallery.py` and `python examples/make_examples.py`
         both run; gallery images regenerated. `python tests/bench_rooms.py`
         also re-run (6x6: rebuild 59.1 ms, memoized no-op 1.9 ms).
notes:   THE FREEZE IS THE TASK. examples/planc1.json (v3) and
         examples/sample_plan.json (v1) are NOT converted and never will be:
         planc1 is the corruption fixture AND the importer's acceptance input;
         sample_plan is the clean legacy input the bridge tests run against, and
         the ONLY v1 file in the repo, so it exercises a migration path nothing
         else does. Converting either leaves the importer with no real v1-v4
         document to prove itself against.
         Made MECHANICAL rather than remembered: tests/test_corpus_freeze.py
         pins both files' format AND version and asserts the legacy corpus never
         drops below two files. Its failure message says what to do instead --
         write the v5 rendering ALONGSIDE, the planc1.json / planc1.v5.json
         pairing that already existed here, which is now what make_examples does
         for sample_plan. examples/README.md documents the freeze in a table.
         Chose that pairing over moving the legacy corpus to tests/fixtures/:
         planc1.json is referenced by path throughout CODE_REVIEW_v2.md,
         DESIGN_MODEL_v5.md, this plan and the migrator's CLI docs, and it has
         to stay in examples/ regardless -- splitting the pair across two
         directories would be worse than keeping both.
         VERIFIED, NOT ASSUMED: make_gallery.py and bench_rooms.py needed no
         format work (both build their scenes programmatically, neither reads
         the corpus), and the macro open/save tokens were already v5 via
         load_path/save_path.
         MACRO MODAL PATH TESTED, not claimed. `open` on a legacy plan through
         the macro runner converts, COLLECTS the report on win._conversion,
         writes it to the status line and leaves the document dirty -- with no
         QMessageBox. A modal there hangs a macro or a test forever, so the
         coverage matters more than the assertion (the test HANGS rather than
         fails if one returns, which is itself the signal). The v5 half is
         pinned too: not converted, not reported, not dirty.
         ASSERTIONS CHANGED (2, both declared in advance):
           * test_fp_extract_cli_end_to_end -- output is floorplanner-design
             now. The wall COUNT is deliberately relaxed to >= 5: v5 walls are
             edge-granular, so 5 detected runs planarise to however many graph
             edges they span. result["counts"]["walls"] == 5 still pins what was
             DETECTED, which is what that test is actually about.
           * test_corpus_discovered -- the pinned set grew by sample_plan.v5.json.
             It joined the validated sweep automatically the moment it existed
             (discovery works), and validates clean: schema 0, invariants 0 deep.
         Not pushed -- Phase 2 pushes after P2.5.

P2.4-followup  done   (commit 33e457d)
ruff:    clean · pytest: 400 passed, 4 xfailed, 1 xpassed
notes:   The `>= 5` wall bound was the WRONG SHAPE of guard -- a lower bound
         passes if planarisation ever explodes, so a bug splitting 5 detected
         runs into 500 spurious segments would sail through. Measured and
         hard-coded: 5 detected runs -> 9 graph edges over 8 vertices for that
         fixture, both exact (the fixture is deterministic and edge-granular
         walls are document state in v5). EIGHTH declared assertion change.
         Took the optional hardening too: the macro-modal test's failure mode
         was a HANG (a modal exec() blocks forever headless), which in CI means
         the job runs to its timeout. _modal_failsafe schedules a single-shot
         timer that dismisses any modal and records it, so the test goes RED
         instead. Timers fire inside nested exec loops -- the same mechanism
         macro._modal_step uses to drive dialogs, opposite purpose.

P2.5  done   (commit d274d21)
ruff:    clean
pytest:  OFF  400 passed, 4 xfailed, 1 xpassed in 14.89s
         ON   400 passed, 4 xfailed, 1 xpassed in 16.98s
         DEEP 395 passed, 3 xfailed, 7 deselected in 14.79s
files:   floorplanner/planio.py, csvio.py, imageio.py, levels.py (all new),
         floorplanner/mainwindow.py, CLAUDE.md
ACCEPTANCE: suite green with ZERO TEST CHANGES -- `git status tests/` empty --
         all three ways. MainWindow 100 methods / 2179 lines -> 49 / 1173,
         under the review's ~55 target.
INVENTORY (methods / lines):
         mainwindow.py  MainWindow    49  1173   UI wiring + edit orchestration
         planio.py      PlanIOMixin   26   544   open/save/export + bridges
         levels.py      LevelsMixin   13   198   the floor roster
         csvio.py       CsvIOMixin     6   260   room CSV import/export
         imageio.py     ImageIOMixin   6   186   reference image + extraction
notes:   MIXINS, NOT DELEGATING WRAPPERS. The suite calls these directly --
         win.serialize(), win.snapshot(), win.load_data(), win._import_rooms(),
         win._is_dirty(), win.switch_floor() -- and a mixin resolves every one
         unchanged with zero delegation boilerplate. A delegate-per-method split
         would ALSO have left MainWindow at 100 methods, missing the point of
         the target. The split is internal structure, invisible at the API.
         MOVER'S DISCIPLINE VERIFIED MECHANICALLY, not asserted: a script
         ast.unparse()s every method before and after the split and diffs them.
         100 before, 100 after, 0 missing, 0 CHANGED. Nothing improved in
         flight.
         BOTH KNOWN HAZARDS CHECKED rather than assumed: SETTINGS is ONE shared
         object (id() compared across config/planio/csvio/imageio/levels/
         mainwindow -- all identical; no module re-binds it), and serialize()
         travelled with its guard comment intact.
         The 84 unused imports left by copying mainwindow's header into each
         module were removed by `ruff --fix`; star imports keep their noqa.
         CLAUDE.md's module layout updated -- it described a layout that no
         longer existed and would have misdirected the next reader.
         NOTED FOR LATER, NOT DONE (the itches, per mover's discipline):
           * `import_from_image` (55 lines) and `_import_rooms` (137 lines) are
             both long enough to want splitting; neither is in P2.5's scope.
           * `apply_project_to_scene` (109 lines) is the v4 loader and is on a
             deletion path once the legacy export retires -- do not invest.
           * `room_boolean` (97 lines) stayed in mainwindow.py deliberately: it
             is rewritten as a polygon op at P3.5, so moving it now would churn
             a file that task rewrites.
         PHASE 2 COMPLETE. Ready to push.

PHASE 2 PUSHED  (52bd72e..3c2fbcf, 13 commits) -- CI GREEN on py3.10 + py3.13.
         Doubled suite: 16s/18s on py3.13, 17s/20s on py3.10; job total 1m13s.
         Still a clean doubling, still no cross-Python divergence.

GATE 2  manual sanity check -- FINDING, fixed on main before branching
         (commit d665e06)
ruff:    clean
pytest:  OFF  403 passed, 4 xfailed, 1 xpassed in 15.78s
         ON   403 passed, 4 xfailed, 1 xpassed in 18.43s
         DEEP 398 passed, 3 xfailed, 7 deselected in 15.84s
files:   floorplanner/design/importer.py (weld_room_corners),
         tests/test_load_path.py (+3), examples/symmetricP1.json (regenerated)
THE FINDING: reopening the app's OWN legacy-v4 export of a converted plan
         reported "5 wall ends moved (5 junctions checked)". Expected 0 -- the
         app's own output must never need repair. NO EXISTING TEST TOUCHED.
DIAGNOSIS -- (a), but UPSTREAM of the export. The export was faithful and the
         report honest (weld_ops == ends_moved == 5, nothing conflated). The
         IMPORTER baked a pre-repair artefact into the repaired document:
           1. the weld pulls the four divider ends 655.529 -> 654.0 (the fix);
           2. split_params then cuts those same walls at the STORED room
              corners, which are PRE-WELD data and still say 655.529;
           3. that injects a degree-2 vertex 1.53" from the freshly welded end
              and a 1.53" SLIVER wall -- the exact ghost of the gap just closed.
         The tell was the DIRECTION: displacements ran from 654.0 OUT to 655.53,
         away from the repair, not toward it.
         WHY NOTHING CAUGHT IT: 1.53 clears MIN_SPAN (1.0) so the sliver
         survives, and clears vertex_weld_in (0.6) so I14 stays silent; all 20
         room areas were correct. It is invisible until the document is exported
         and reopened, where the 2" end-to-end gesture weld fuses the pair.
FIX:     weld_room_corners() snaps stored perimeter_corners onto the welded wall
         ends using the same END_TOL the wall weld uses -- they describe the
         same corners. 66 corners welded on planc1; reopen now reports 0/0.
         It also removes a SECOND, quieter error: stored corners are rounded to
         2dp by _sync_corner_props, so using them verbatim seeded the vertex
         table with up to 0.005" of drift. Six symmetricP1 vertices gain
         precision (104.42 -> 104.4228, 280.24 -> 280.2416, ...).
WHY IT ESCAPED, and the missing test: P2.2 round-tripped only via load_data --
         the FAITHFUL apply, which never welds -- so the export was never taken
         back through the CONVERTER. The two paths were each covered and their
         composition was not. test_legacy_export_reopens_without_repair now
         drives the full journey (open -> save v5 -> export v4 -> reopen
         converting) and asserts ends_moved == 0 with areas identical, plus a
         unit test for the corner weld and a guard that no sub-2" sliver
         survives a conversion.
FIXTURE: symmetricP1.json regenerated, every delta class measured:
           2 sliver vertices REMOVED (the bug) -> 82 walls to 80; Hall 9->7,
             Great Room 11->10, M Bath 11->10 outline edges
           6 vertices gain precision (2dp stored corner -> exact wall endpoint)
           47/62 vertex ids renumbered, 11/20 loops rotated (consequences)
           0 OF 20 ROOM AREAS CHANGED -- the geometry is preserved
           provenance and settings identical
         planc1.v5.json BYTE-IDENTICAL: faithful mode never welds, so it never
         had the artefact -- which is itself a check on the diagnosis.
         Acceptance unchanged: M Bath 182.0, Hall 61.5, 4 ends moved, check
         clean. Side effect worth noting: suite warnings dropped 17 -> 2,
         because converted scenes no longer carry unwelded ends.
LESSON, recorded in one line because it generalises: both paths were covered;
         their composition was not -- COVERED-PATHS != COVERED-COMPOSITIONS.
         Every future gate should ask which pairs of covered paths have never
         been run back-to-back.
result:  GATE 2 -- PASSED, one finding found and fixed (d665e06). Patrick's two
         trailing checks (original file untouched on disk, undo feel) ride as
         optional confirmations, not blockers.
meaning: Phase 2's acceptance is complete. P3.1 may proceed.

P3.1  done   (commit f0990d4, on branch v5-topology)
ruff:    clean
pytest:  OFF  415 passed, 4 xfailed, 1 xpassed in 16.69s
         ON   415 passed, 4 xfailed, 1 xpassed in 20.20s
         DEEP 410 passed, 3 xfailed, 7 deselected in 18.22s
files:   floorplanner/vertex.py (new), floorplanner/walls.py (read-through
         p1/p2 + v1/v2), floorplanner/design/verify.py (split logging),
         tests/test_vertices.py (new, 12)
ACCEPTANCE: suite green with NO TEST CHANGES -- `git status tests/` shows only
         the new file -- and the --verify-design run stays green.
notes:   A Vertex is a shared, identity-bearing point; two wall ends holding the
         SAME Vertex object are the same corner. No registry: the "table" is the
         set of vertices reachable from the walls, exactly as Design.vertices is.
         SPLIT-ON-WRITE, per the ruling. Assigning a moved position mints a
         fresh vertex and leaves any sharer put; a NO-OP assignment returns the
         same vertex, so identity and sharing survive the many places that
         re-set the same coordinates. Pinned by a test that shares a corner
         explicitly, moves one end, and asserts the other did not follow.
         SPLIT LOGGING: verify() records the per-operation delta in
         win._vertex_split_log. It LOGS rather than warns -- a drag legitimately
         splits, so a warning per drag would be noise, not signal.
         A PERFORMANCE REGRESSION I INTRODUCED AND FIXED, recorded because the
         HARNESS caught it and review would not have: the first version
         allocated a QPointF on every p1/p2 READ and a uid string on every
         write. p1/p2 are read on every rebuild, paint and hit-test, so rebuild
         slowed ~50% and bake nearly doubled -- test_bake flapped at 8.54
         against a threshold of 8. Fixed by storing the QPointF once and
         returning it SHARED, and minting uids lazily. Both are safe only
         because a vertex is never mutated in place: a move produces a NEW
         vertex, so a caller holding an old p1 still sees the old position --
         identical to the previous behaviour, where assignment rebound the
         attribute to a fresh QPointF. Verified before relying on it (nothing in
         the codebase mutates a p1/p2 in place; every access is .x()/.y()) and
         pinned by test_vertex_is_never_mutated_in_place. bake now 43.7 -> 297
         ms ratio 6.83 vs P2.3's recorded 40.8 -> 278.7 ratio 6.83 -- restored,
         not merely under the threshold. This is the second time P0.3's harness
         has paid for itself on a change that looked free.
         FINDING -- WHY P3.1 STOPS AT THE REPRESENTATION. design_from_scene
         still builds its own vertex table by welding COORDINATES at 0.6"; it
         does not yet consume the live uids. It cannot: nothing creates sharing
         yet, so today every coincident wall end is a DISTINCT vertex, and
         emitting live uids would put two vertices 0" apart in the document and
         trip I14 across the whole corpus. Consuming the live table therefore
         has to wait until weld/join create shared vertices explicitly, at
         P3.3/P3.4. That ordering is not a shortcut -- it is the same
         representation-then-behaviour discipline the split-on-write ruling
         encodes.
         COMPOSITION GATE (the Gate 2 lesson): round trips asserted through BOTH
         apply paths -- load_data (faithful) and open_document (converting,
         composed all the way out to a legacy export and back).

CI-ON-BRANCH  done   (draft PR #1)
notes:   Pushing v5-topology ran NO CI -- ci.yml triggers on push-to-main and
         pull_request only, so the whole geometry rewrite would have gone
         unvalidated until the merge: exactly the situation P0.3 called out.
         Fixed with a DRAFT PR (v5-topology -> main) rather than editing
         ci.yml's push list: the pull_request trigger then covers every push,
         and it costs no config change on main that we would later revert. The
         PR also gives a running diff of the phase and is the merge vehicle at
         P3.8. First run green: ruff, py3.10 and py3.13, both suite runs.

P3.2  done   (commit 77bc91a, branch v5-topology)
ruff:    clean
pytest:  OFF  428 passed, 4 xfailed, 1 xpassed in 16.69s
         ON   428 passed, 4 xfailed, 1 xpassed in 18.64s
         DEEP 423 passed, 3 xfailed, 7 deselected in 16.80s
files:   floorplanner/rooms.py (OutlineEdge, derived corners, mirror deleted,
         edge->wall in bind_room_walls, clipboard fix), floorplanner/planio.py
         (export re-derives, load strips), floorplanner/items.py +
         mainwindow.py (mirror call sites), tests/test_outline.py (new, 13),
         tests/test_groups.py (one deleted-method call)
ACCEPTANCE: room areas unchanged across the corpus (asserted on sample_plan and
         planc1 through the faithful apply, with the document identical after);
         _sync_corner_props and its six call sites deleted.
notes:   INTERIM REPRESENTATION, stated not implied: an outline edge holds a
         COORDINATE, not a vertex identity. P3.1's split-on-write world has no
         shared corner vertex to name -- at every corner each wall owns a
         distinct Vertex. Borrowing one wall's end picks arbitrarily between
         two (and two rooms meeting there could pick differently); minting a
         room-owned vertex adds a third object no wall references. Both encode
         an authority that does not exist yet; a coordinate states exactly what
         is known. THE TEST FOR CHOOSING AN INTERIM REPRESENTATION IS WHICH ONE
         DOES NOT LIE.
         Two guards pin the gap: outline corner and wall end have equal
         coordinates but are distinct objects, and a corner is still two
         distinct wall vertices. Both say in their docstrings that FAILING is
         the signal P3.4 closed the gap, not that something broke.
         The edge->wall mapping is the real content of the task -- before it a
         room had corners and an unordered walls list with no correspondence.
         SHIPPED POPULATED (bind_room_walls already computed it to place
         OpenWall placeholders), so the fallback rider does not apply and P3.4
         inherits nothing.
         THREE FATES, all three exercised by tests: the live mirror DELETED;
         the legacy v4 export KEPT byte-compatibly via
         RoomItem.export_properties() re-deriving at serialization time at the
         same 2dp rounding (the v4 loader needs it for OPEN rooms, whose
         detection fails); the importer reading legacy FILES untouched forever.
         Plus "ignored on load" -- read for the fallback, then stripped.
         AUDIT FINDING -- THE MIRROR WAS MASKING A LATENT BUG, and only the
         grep-everything instruction found it. _copy_spec carried
         dict(self.properties) -- including the SOURCE room's perimeter_corners
         -- into the clipboard; paste_room passed it to the new RoomItem, where
         _sync_corner_props overwrote it. Deleting the mirror naively would have
         shipped the source room's geometry into every pasted room, in a corner
         the suite does not reach. Fixed by keeping geometry out of the
         clipboard, with a test. All 20 tree-wide hits reconcile: 6 importer
         (4 live + 2 docstrings), 2 mirror body, 1 legacy-load fallback, 1
         bridge pop, 1 tool docstring, 8 tests, 1 schema (which FORBIDS the key,
         confirming the plan's parenthetical).
         The room-properties dialog and the inventory paths were checked too:
         the dialog updates an explicit key list, inventory reads include_sqft
         only. Neither touches geometry.
         TEST CHANGED (1): tests/test_groups.py called room._sync_corner_props()
         directly -- a SEVENTH call site, in tests rather than production.
         Removed; a call to a deleted private method, not an assertion (the P0.2
         class). The change I PREDICTED to test_design_bridge's _project_areas
         did NOT materialise: because the export re-derives the key rather than
         dropping it, that helper reads it unchanged.

P3.3  done   (branch v5-topology)
ruff:    clean
pytest:  OFF  447 passed, 4 xfailed, 1 xpassed in 18.04s
         ON   447 passed, 4 xfailed, 1 xpassed in 19.61s
         DEEP 442 passed, 3 xfailed, 7 deselected in 17.69s
files:   floorplanner/vertex.py (relocated_to + call-site attribution),
         floorplanner/walls.py (_DragVertex, end_vertex/set_end_vertex,
         _is_continuation, _plan_vertex_moves, the drag rewritten),
         floorplanner/design/verify.py (SITE_LOG_ATTR),
         tests/test_wall_move.py (new, 19)
ACCEPTANCE: suite green with NO TEST CHANGES -- `git status tests/` shows only
         the new file, all three ways.
THE LOG ENTRY FOR THIS TASK WAS NOT ON DISK. The brief said the five settled
         points were in this Progress log; they were not, and 3d6d32e touched
         only two lines (defect 12a, and the P2.3 regression row). Reported
         rather than reconstructed, per the P0.6 rule. Two of the five WERE on
         disk and are quoted here: the same-level constraint (defect 12a,
         `_attached`) and `_collinear_run` at walls.py:888 gathering 2 of 2. The
         "72 splits" figure appears nowhere in the repo (a grep for it over
         docs/*.md is empty), so it is not quoted; the measured figure for this
         task's scenario is below. The 0.6" tolerance was verified in the CODE
         (walls.py, `QLineF(q, rp).length() < 0.6`), which matches
         vertex_weld_in / WELD_TOL -- the schema's own definition of one vertex,
         and now named SHARE_TOL rather than repeated as a literal.
THE HEADLINE NUMBER, measured both ways on the same 4x4 grid: 12 wall drags
         caused 148 SPLIT-ON-WRITES before this task and 2 after. The two that
         remain are the branches deliberately NOT promoted (see below), so the
         drag path is converted, not merely quieter.
(1) PROMOTION. The 0.6" scan used to discover coincident ends and then push each
         one by hand on every mouse event, which is split-on-write: the corner
         came apart and was rebuilt from coordinates 60 times a second. Now the
         scan runs ONCE at press and REBINDS those ends to one Vertex object
         (`set_end_vertex`), and the drag moves the vertex (`relocated_to`) --
         so a neighbour follows because it IS the corner. Asserted with `is`,
         never `==`: equal coordinates are exactly what the old code already
         produced and would not distinguish the two worlds.
         `relocated_to` CARRIES THE UID. A moved corner is the same corner, so
         renaming it would be wrong on its own terms and would also break P4.5,
         which serializes groups by member id. It is not counted as a split,
         because it is not one -- otherwise P3.3's own conversion would show up
         in the very telemetry that exists to find the call sites still needing
         it. A test pins that the count does not move across a drag.
         SAME LEVEL ONLY (defect 12a, now closed). Filtered at the LOOP HEAD, so
         cross-level sharing is impossible by construction. Note the filter
         covers the whole scan, not just the promotion: leaving the tee branch
         unfiltered would have left half of defect 12a alive for no benefit, and
         the transient cross-floor mis-drag is a real bug too. Declared because
         it is one line wider than "promotion is same-level".
(2) THE SPLIT RULE, and what it is really a rule about: what must NOT be shared.
         A wall collinear with the slide that continues past an endpoint cannot
         ride the corner -- the slide is perpendicular, so moving the shared end
         would swing its far end and SHEAR it. So the continuation is split off
         FIRST (its own vertex, and it stays put), before any sharing is made.
         Verified in both directions rather than asserted: with P3.3 reverted,
         test_a_collinear_continuation_is_never_sheared FAILS with the
         continuation's end at y=12 instead of y=0 -- it really was being
         dragged and sheared, so this is a behaviour FIX, not just a
         representation change.
         THE FIRST EARNED BEHAVIOUR CHANGE OF PHASE 3, and the label is the
         standard rather than a flourish. Phase 3's contract is that P3.1 and
         P3.2 are compat shims -- representation moves, behaviour does not, and
         "suite green with no test changes" is the receipt. A behaviour change
         inside that contract has to earn its place, which means all three of:
         DECLARED in advance (the split rule was in the task text), TESTED IN
         BOTH DIRECTIONS (it fails on reverted code, at a named coordinate, so
         the bug is exhibited and not merely described), and BRACKETED BY A
         MEASUREMENT (148 -> 2 splits over the same 12 drags, so the size of
         the change is known and not guessed). A behaviour change with fewer
         than three is a regression that has not been noticed yet.
         The rule also has to BREAK sharing that already exists, not merely
         decline to create it (a corner welded by an earlier operation is
         exactly what P3.4's weld produces). Own test.
(3) DETECTION STAYS AUTHORITATIVE. Nothing here reads outlines off vertices;
         room areas after a drag are what refresh_rooms arrives at, and the
         scene test asserts that. P3.5 flips it.
(4) CALL-SITE ATTRIBUTION, and the data it immediately produced. P3.1's counter
         said an operation splits; it could not say WHERE, and "which call sites
         should become real vertex moves" is a question about lines. `_blame()`
         walks past this module and past the p1/p2 setters -- blaming the
         setters would put every split on two lines and answer nothing.
         MEASURED, over coalesce + weld + group + bake + ungroup + 12 drags = 82
         splits:
             40  items.py:703 in bake()
             40  items.py:704 in bake()
              2  walls.py     in mouseMoveEvent()
         So 80 of 82 are GroupItem.bake, on two adjacent lines, and that is
         P4.5's ("groups move the real items -- no duplicate_wall"). The 2 are
         the tee and grouped branches this task deliberately left on the
         coordinate path. The drag's own corner moves contribute ZERO.
         TWO LOGS, not a wider tuple: SPLIT_LOG_ATTR keeps its (operation,
         splits) shape and SITE_LOG_ATTR carries the blame, so the P3.1 reader
         (and its test) is not broken to add data it did not ask for.
         COST measured, per the P3.1 lesson: 622 ns per split for the
         sys._getframe walk. Never on a READ -- reads are the hot path P3.1 had
         to fix -- and at 82 splits per heavy session it is under noise. The
         harness confirms: bake ratio 6.57 / 6.90 / 7.78 over three runs
         (absolute 303-332 ms) against P3.1's recorded 6.83 / 297 ms. The 7.78
         sample is variance, not a regression -- checked by re-running rather
         than by assuming, because the first run alone looked like one.
A HAZARD FOUND WHILE REVIEWING MY OWN DIFF, and it is not a corner case:
         GROUPING DUPLICATES A ROOM'S WALLS ONTO THE ORIGINALS, so a grouped end
         coincident with a dragged wall is the COMMON case. Promoting it would
         wire a group member to an outside wall permanently, and what a group is
         topologically is P4.5's open question. Grouped neighbours therefore
         keep the OLD coordinate path (`kind == "rigid"`) -- they still follow
         the drag exactly as today, they just do not become topology. Same
         instinct as the `group() is None` gate that keeps grouped walls out of
         coalesce, applied one task before the semantics that need it.
COMPOSITION GATE (the standing additions): both apply paths after a real drag --
         load_data (faithful) and open_document (converting, composed out to a
         legacy v4 export and back, ends_moved == 0) -- plus a corpus test that
         presses EVERY wall of sample_plan and planc1 without dragging and
         asserts the whole document is unchanged and zero splits occurred. That
         last one is the new risk this task introduces and nothing else would
         catch: the press rewrites which vertex a neighbour points at, on every
         wall the user so much as clicks. Areas would survive a promotion that
         re-pointed an end at the WRONG corner; the document would not, so the
         document is what is asserted. Measured on planc1: 80 walls pressed,
         document byte-identical, 0 splits.
DEFERRED, DECLARED, NOT DONE -- and it needs a ruling. The plan's P3.3 task text
         has a second half of the split rule: "a vertex landing on another
         wall's body splits that wall." It is NOT among the five settled points
         (which specify the promotion, detection authority, attribution, the
         four tests, and the gate), and it is P3.4's shape of work: splitting a
         WallItem at a landing point is `split_edge` scene-side, in the same
         task that replaces coalesce/weld/fracture. Doing it here would
         duplicate that and would add an automatic wall-splitting side effect to
         every drag release -- a wide blast radius for something no acceptance
         test asks for. The tee branch is left on the coordinate path with a
         comment naming P3.4. Flagging rather than quietly widening or
         narrowing the task: say the word and it lands here instead.
DEMO PORT: `w24` no longer exists as that wall. The demo named it, but ids are
         canonical and the Gate 2 regeneration (82 walls -> 80, 47/62 vertex ids
         renumbered) moved every id in symmetricP1.json -- w24 is now a Master
         Suite / Rear Porch wall, and pre-Gate-2 it was Hall / Lounge. The
         BEHAVIOURAL pin holds exactly on today's fixture: the Lounge / Front
         Porch party wall (currently w18, 210" at y=864), +12 y, Lounge +17.5 sf
         and Front Porch -17.5 sf, TOTAL UNCHANGED to 0.0, check(deep=True) ==
         []. The test picks the wall by rooms and axis, never by id, so it fails
         for a regression rather than for a renumbering. A second test pins that
         the chosen wall really has no collinear continuation -- the demo's own
         precondition -- so the first cannot pass by luck.

P3.5  done   (branch v5-topology; five sub-commits)
ruff:    clean
pytest:  OFF  497 passed, 5 xfailed in 13.7s
         ON   497 passed, 5 xfailed in 16.0s
         DEEP 492 passed, 3 xfailed, 7 deselected in 15.4s
         (baseline in: P3.4's 491/4/1.)
THE XFAIL/XPASS DELTA -- ASKED TWICE, ANSWERED FROM DISK. Both ends were run
         in worktrees and the marker lists diffed, rather than reasoned about:

           c133205 (P3.5 in)   493 passed, 4 xfailed, 1 xpassed
           f738437 (P3.5 out)  497 passed, 5 xfailed

         THERE IS NO "+1 XFAIL". The marked set is BYTE-IDENTICAL at both ends
         -- the same five tests, same order, same reason strings:
           test_characterization::test_delete_wall_actually_removes_the_wall  P4.1
           test_characterization::test_group_survives_roundtrip               P4.5
           test_groups::test_extracted_room_region_follows_move               P4.2
           test_scaling::test_group_scales_subquadratically                   P3.8
           test_scaling::test_ungroup_scales_subquadratically                 P3.8
         P3.5 added no marker and retired none.

         THE VANISHED XPASS IS THE LAST OF THEM, `test_ungroup_scales_
         subquadratically` -- same test, same `xfail(strict=False)` marker,
         reporting XPASS at c133205 and XFAIL at f738437 because its ratio
         crossed the threshold of 8. MEASURED 7.85 / 8.29 / 8.54 / 8.82 on
         successive runs of one build: it straddles. Its ABSOLUTE improved
         sharply (300.7 ms -> ~106 ms at n=8, from the deleted re-detection),
         which is exactly why it now sits ON the threshold instead of well
         above it.
         >> WIDENED AT P3.6 FROM ONE TEST TO THE CLASS, by measurement. The
         P3.6 gate audit replayed OFF and ON at all 27 code-touching branch
         commits and found 8 red -- of which SEVEN are this, and not one of
         them is `test_ungroup` alone: `test_bake_scales_subquadratically` was
         caught red at 8.05 against a threshold of 8, and every one of the
         seven shows the tell -- exactly "1 failed", ALTERNATING between the
         OFF and ON runs of the same commit. Code that is broken fails both
         gates; a ratio that straddles fails whichever run the machine was
         busier during. So the row is not one flaky test, it is the P0.3b
         TIMING-RATIO CLASS, flapping at roughly 7 of 27 replays (~26%), and
         whatever P3.8 decides -- a wider threshold, best-of-N, or moving them
         out of the suite entirely -- applies to the class and not to one
         member. Members seen flapping so far: `test_ungroup_scales_
         subquadratically`, `test_bake_scales_subquadratically`,
         `test_rebuild_scales_subquadratically`.
commits: ac9ad45 (0) . 600fdef (1) . 02eff1e (2) . 733d7d6 (3) . f07dbdb (4)
         Logged sub-commit by sub-commit per the handoff-spec rule, so a
         successor reads the state from here plus the four riders at lines
         416-424 rather than from a chat summary.
(0) done   commit ac9ad45 -- doc-only, committed BEFORE any code per rider 2.
         THE RETARGET WAS ITSELF A FINDING: both P3.2 guards' docstrings named
         P3.4 as the task that would close the coordinates-vs-identity gap.
         P3.4 replaced the coalesce/weld/fracture ops and never touched
         outlines, so both stayed green straight through it -- they were
         addressed to the wrong task. Retargeted in tests/test_outline.py
         (module + both docstrings + both failure messages) and rooms.py's
         OutlineEdge note, and the second guard's message now names BOTH ways
         it can fire so a red says which.
(1) done   commit 600fdef -- the flip.
ruff:    clean
pytest:  OFF  493 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   493 passed, 4 xfailed, 1 xpassed in 20.3s
         DEEP 488 passed, 3 xfailed, 7 deselected in 18.5s
files:   rooms.py (OutlineEdge holds a Vertex, `p` read-through;
         share_outline_vertices; the bind_room_walls hook), walls.py
         (_CornerIndex.vertex_at), vertex.py (defect 21),
         tests/test_outline.py (the two guards replaced + rider 1's test),
         tests/test_wall_move.py (+1, the defect-21 case)
THE GUARDS FLIPPED, AND ONLY THE GUARDS -- both P3.2 tests went red at this
         change and the whole rest of the suite stayed green through it. That
         is exactly what rider 2's sequencing was for: the red is the flip,
         not a weld that wandered in. Their two causes turned out to BE one
         cause: the weld is the flip's first step, because an outline can only
         NAME a vertex once the corner IS one vertex.
DEFECT 21 -- FOUND BY RIDER 1's OWN TEST, and it is the best kind of find.
         `relocated_to` copied `self._uid`, and uids mint LAZILY on first
         read, so a corner nobody had named carried None across a move and got
         a FRESH identity the moment anything asked. Invisible while only the
         document walk read uids -- which is how it survived P3.1, P3.3 and
         P3.4 -- and a live bug at P4.5, which serializes groups by member id.
         THE NEAR-MISS IS THE LESSON: P3.3's
         test_relocation_carries_the_vertex_identity has pinned this exact
         rule since P3.3 and PASSES FOR A REASON IT DOES NOT STATE -- it reads
         `v.uid` before relocating, which forces the mint. A test that
         establishes the precondition it means to test cannot see the bug.
         Fixed, and pinned by a test that constructs the unnamed case.
PERF, checked not assumed (the P3.1 lesson): test_bake flagged 8.83 against a
         threshold of 8 on the first full run. Re-ran three times -- 6.31 /
         6.89 / 7.17, absolutes 307-310 ms against P3.3's recorded 297-332 --
         so variance, not the new property read. Same call as P3.3's 7.78.
(2) done   commit 02eff1e -- the region derives from the outline.
ruff:    clean
pytest:  OFF  495 passed, 4 xfailed, 1 xpassed / ON same / DEEP 490, 3 xfailed
files:   rooms.py (path + area_sqft become properties; _translate relocates),
         walls.py (_DragVertex carries outline edges), items.py + mainwindow.py
         (three rigid-move sites go through set_region),
         tests/test_outline.py (+2)
THE STEP P3.2 AND (1) DID NOT TAKE, and without it the deletion is impossible
         rather than merely risky. `corners` derived from the outline at P3.2
         and the corners became real vertex identities at (1) -- but `path` and
         `area_sqft` were still a stored QPainterPath and a stored float that
         ONLY `refresh_rooms` refreshed. So an outline that moved by
         construction still reported a stale area until a detection pass caught
         up, and deleting that pass would have frozen every number a user reads.
         Both derive now, memoized on the corner COORDINATES -- not identity,
         because `relocated_to` returns a NEW vertex for a moved corner and an
         id-keyed memo would be stale in exactly the case that matters.
NO EXISTING TEST CHANGED.

(3) done   commit 733d7d6 -- the deletion, and the lift.
ruff:    clean
pytest:  OFF  495 passed, 5 xfailed / ON 495/4/1xpassed / DEEP 490, 3 xfailed
DELETED, 418 lines across 11 top-level definitions, all callerless:
         `_RoomGrid` (90) + `_WallGraph` (131) -- the two engines, a raster
         flood-fill and a hand-rolled planar face walk; `_detect_room` (12),
         `detect_room_region` (6), `trace_room_perimeter` (6); the memo,
         `room_signature` (23) + `refresh_rooms` (53) + `_room_probe_points`
         (19); `reloop_open_room` (48); `synthesize_room_edge` (15) and
         `_wall_along_segment` (15). Plus `bind_room_walls` 70 -> 38.
         rooms.py 1425 -> 1162 lines.
`detect_room` SURVIVES AS A NAME, and this is the census's one real divergence
         on the rooms.py side. The task line lists it among the dead; it has
         ~40 call sites across the app, the tooling, the fixtures and eleven
         test modules, and this task's authorized rewrite zone is two test
         files. Deleting the NAME would have been a rewrite of the suite
         wearing a deletion's clothes. What the line MEANS is delivered in
         full: the editor no longer has its own answer to "what is a face". It
         asks the document's, through `bridge.face_at` -> `enclosing_face`.
THE LIFT, and why it is allowed where P3.4 point 1 forbade it. That ruling
         rejected lift-to-Design for EDIT ops, on measurement: an edit runs per
         mouse event and a full-plan rebuild destroys item identity. "Detect
         room here" is a ONE-SHOT gesture -- the six call sites (csvio, macro,
         mainwindow x2, planio, view) each fire once per user action -- so the
         walk costs no more than the `_RoomGrid` + `_WallGraph` pair it
         replaces, both of which were also rebuilt per call and one of which
         was O(walls^2). Single-sourced instead of duplicated.
THREE THINGS CAME FREE, and they are why the swap is worth making rather than
         merely equivalent:
         * DEFECT 16 closes STRUCTURALLY. The grid was sized by `canvas_rect()`
           and any flood reaching its edge counted as unenclosed, so a plan
           larger than the canvas silently lost its edge rooms. A graph walk has
           no canvas in it. Closed by deletion, which is the only kind of fix
           that cannot regress. Pinned.
         * every returned edge NAMES the wall covering it, so `bind_room_walls`
           stopped SEARCHING for a room's own walls and now only attaches them.
           A room binds its outline as a fact the detection reports.
         * a wall split at a T yields one edge per SEGMENT -- invariant I5
           ("every outline edge maps to exactly one wall") holding by
           construction, where the old tracer dropped pass-through corners and
           could leave an edge no single wall covered.
DEFECT 13 -- REPRODUCED BEFORE THE SUBSTRATE WENT, which rider 3 asked for and
         which is the reason the verdict is worth anything. At zooms 0.25x-4x
         on the `detach_wall_from_room` path, measured on the code as it stood:
         * DETECTION was already IDENTICAL at every zoom -- same area, same
           corners, 5/5. It never read the view.
         * THE DRAG was not. The same scene-space gesture gave 0 open sides at
           0.25x and 1 at 0.5x-4x, leaving the wall's far end at y=120 vs y=60.
         So the defect is real and its mechanism is the drag's zoom terms
         (`20.0 / _view_scale()` catch radius, `16.0 / view_scale` stick),
         exactly as rider 3 predicted. Detection half CLOSED and now structural;
         drag half RETARGETED and left UNASSIGNED, the same disposition the P2.3
         row got, with P4.2 as the nearest task that touches the drag. NOT
         "repro substrate removed" -- the substrate was still there and the
         measurement was taken.
TWO CORRECTIONS THE LIFT NEEDED, both found by a failing test rather than by
         reasoning, and both are findings about `trace_faces` as much as about
         this task:
         * SPUR PRUNING. A dangling wall stub is IN the wall graph, so the face
           walk enters it and comes straight back out. Free for a FACE (the
           excursion encloses no area) and wrong for an OUTLINE: the room grows
           a corner at the stub's free end, and every consumer that asks "is
           this room inside the rubber band" answers from it. Caught by
           test_selection, which is not in the authorized zone and was right not
           to be changed. `bridge._prune_spurs`.
         * CANONICAL WINDING. `_inner_faces` picks the inner sign by MAJORITY,
           decisive from two rooms on but a TIE at exactly one -- a lone wall
           loop traces two faces of equal area and opposite winding. So a
           one-room plan came back wound whichever way the rest of the plan
           happened to vote, and the outline ORDER is serialized. Caught by
           test_room_walls' idempotent round-trip. Fixed at the one-shot entry
           to the sign the document already uses (positive shoelace, verified
           against every face of symmetricP1).
THE APPLY PATH NOW CARRIES THE DOCUMENT'S VERTEX IDENTITY, one live `Vertex`
         per document vertex, shared by every wall end and outline edge naming
         it. The first attempt reconstructed it by WELDING
         (`share_outline_vertices`) and `test_malformed_v5_is_reported_not_
         rewelded` caught it within the minute: apply must not repair, and a
         corner that has drifted 0.3" is a malformed file to be REPORTED, not
         quietly closed up. The document already knows the identities; reading
         them is exact where welding is a guess.

(4) done   commit f07dbdb -- defect 8, the predicates, the privatize ruling.
ruff:    clean
pytest:  OFF  497 passed, 5 xfailed / ON 497/5 / DEEP 492, 3 xfailed
DEFECT 8, and it was TWO faults with ONE cause -- `room_boolean` worked from a
         re-traced boundary rather than from what the rooms said they were made
         of. (a) It DELETED WALLS THAT WERE NOT ITS OWN: inputs came from
         `bounding_walls()`, a proximity query with no floor filter, and the op
         removes everything handed to it -- so a combine took the wall a third
         room shared with an input, breaking that room open, and any wall of any
         other FLOOR whose body touched the band. (b) It FORCED every result
         wall to "interior", downgrading 6" exterior walls to 4 1/2" ones.
         Both fixed at the source: inputs come from the room's OUTLINE
         (`room_walls`), a wall still bordering a non-input room is kept, and
         each result edge inherits type and floor from whichever input wall runs
         along it. TWO REGRESSION TESTS, both CONFIRMED FAILING against the old
         code before being kept -- and the first fixture was rebuilt on the
         shared-wall model, because two `make_room` calls leave a coincident
         PAIR at the boundary and a duplicate wall is a different problem.
THE TWO PREDICATES, rewritten and not deleted, exactly as rider 4 tabled.
         `room_owns_walls` and `walls_cover_room` keep their criteria and read
         the outline through a new `room_walls(room)` -- one answer to "which
         walls are this room's?" -- instead of the parallel bound-wall list the
         deleted binder maintained.
`_privatize_shared_walls` ASSESSED IN-TASK: KEEP. Its reason is untouched -- a
         party wall is one wall, so a room moving off it must stop owning it.
         It needed one repair to stay honest: it swapped the room's BOUND wall
         for a private copy and left the OUTLINE naming the shared one, and the
         outline is now the authority, so `room_walls` went on handing bake and
         room_boolean a wall the room had just given up.
         AND IT WORKS FOR A REASON WORTH WRITING DOWN: `_translate` RELOCATES
         corners, and a relocation mints a new `Vertex` that only the ends
         REBOUND to it follow -- so a wall the room no longer owns simply stays
         on the old corner, with nothing holding it back. P4.2's real `extract`
         still replaces the shape of it; `_perimeter_span` still falls with
         `fracture_delete_wall` at P4.1.

EXIT 1 -- MEASURED DELETION vs THE CENSUS. Rider 4 tabled ~470 from rooms.py
         + 34 from walls.py. MEASURED: 418 in whole definitions plus 32 from
         `bind_room_walls`' shrink = 450 of the ~470, and 0 from walls.py.
         Two divergences, both reported rather than forced:
         * `_wall_along_segment` (15) is REPLACED, not deleted, by `_edge_wall`
           (48) -- LARGER, because it absorbed the job the deleted three-priority
           search was doing: find the wall behind an outline edge that came from
           a FILE and names none. It also had to accept PARTIAL cover, or a v4
           reload stops agreeing with the live scene about a side whose corner
           was dragged away, and the round-trip stops being idempotent.
         * `_WallBBoxIndex` (34) CANNOT DIE, and P3.4 (iv) is why. That
           sub-commit reported it as P3.5's on the grounds that `refresh_rooms`
           was its last caller -- but the SAME sub-commit refused the adjacency
           swap in `_compute_wall_junctions` and said so at length: an unwelded
           crossing shares no corner, so bbox search is the only thing that can
           answer there. `_compute_wall_junctions` stays, so its index stays. A
           line dies when its LAST caller dies, and P3.4 (iv)'s own ruling
           created the caller that outlives this task.
EXIT 2 -- RIDER 1'S HEADLINE CHECK, PASSING, AND THE ASSERTIONS DID NOT MOVE.
         `test_a_dragged_wall_resizes_the_rooms_it_borders` -- the editor half
         of the Lounge / Front Porch demo -- still asserts equal and opposite
         resizing with the total unchanged, now with `refresh_rooms` DELETED.
         Written at P3.3 the numbers came from detection; they now arrive
         because the rooms' outlines hold the very vertices the divider holds.
         A `not hasattr(fp, "refresh_rooms")` guard makes the claim explicit
         rather than implied, so the test cannot quietly stop proving it.
EXIT 3 -- PERF, MEASURED NOT ASSUMED: the same harness on the same machine at
         c133205 (pre-P3.5) vs HEAD. P0.3 warned that `rebuild` at 2.7 was
         ALREADY sub-linear and that a regression there would be a real
         finding. It improved.
                        before (n=4 -> n=8)      after
           rebuild      1.2 -> 3.7   r 3.05     1.0 -> 2.4    r 2.31
           bake        44.8 -> 299.1 r 6.68     6.9 -> 28.0   r 4.03  <- 10.7x
           ungroup     45.9 -> 300.7 r 6.55    13.5 -> 106.1  r 7.85  <- 2.8x
           undo        21.3 -> 157.7 r 7.40    20.9 -> 123.5  r 5.92
           group       27.7 -> 360.1 r 12.99   33.3 -> 370.1  r 11.10 (P3.8's)
         `bake` is the headline and the mechanism is exactly the deletion: a
         group move ended in `rebuild_all_walls` -> `refresh_rooms`, which
         re-detected every room the move touched. Nothing re-detects now. The
         ungroup RATIO worsened while its absolute fell 2.8x -- it is
         xfail(strict=False) -> P3.8 either way, and P3.8 owns the reading.
EXIT 4 -- TOOLING. `python docs/make_gallery.py` and
         `python examples/make_examples.py` both run; images regenerated.
         `08-open-walls.png` legitimately changed and README's open-wall
         paragraph was corrected to match -- see the new Known-regressions row.

CHANGED-TEST LEDGER, one line each, since this is the second-biggest such risk
         in the plan after P3.4:
         * test_rooms.py [AUTHORIZED]: test_region_follows_wall_move rewritten
           -- coordinate assignment -> corner relocation, because a bare
           `w.p1 = ...` is SPLIT-ON-WRITE by P3.1's ruling, so the old test
           replaced wall ends and asked detection to notice. Three
           room_signature / refresh-memo tests DELETED with the memo they
           measured. +4: defect 13 (view-independence), defect 16 (no canvas
           clip), and the two defect-8 regressions.
         * test_room_walls.py [AUTHORIZED]: test_wall_stretch_keeps_binding
           rewritten, same one-line reason. +2 assertions in the privatize test.
         * test_open_walls.py [DIVERGENCE -- the whole file]: this is P3.7's
           rewrite arriving early, because P3.5 deletes the PRODUCER. An open
           side was an ITEM (a dashed `OpenWall`, regenerated by
           `reloop_open_room` + `bind_room_walls`); it is now a fact about the
           outline, reported by the new `RoomItem.open_edges()` -- which is
           where `bridge._rooms_of` has emitted it since P1.4. The scene was
           carrying a second, item-shaped representation of something the
           document already said. `test_open_wall_is_editable` DELETED: it
           asserted drag controls on a placeholder nothing constructs. The
           CLASS still dies at P3.7, as planned.
         * test_design_bridge.py + test_verify_design.py [OUTSIDE THE ZONE, and
           named as such]: planc1's I6 characterization 17 -> 13. planc1's four
           divider walls stop 1.5" short, so each is a dangling STUB; the old
           tracer carried those out-and-back excursions into the outline (which
           is how Hall and M Bath each held 21 corners, several at the free end
           of a wall nowhere near the room). Spur pruning drops them, so four
           walls only a spur ever touched stop being claimed. Same fault
           classes, same Hall/M Bath collapse, same areas -- all three verified.
         * test_wall_move.py: docstrings + the `refresh_rooms`-is-gone guard.
           The ASSERTIONS DID NOT MOVE; that is exit check 2.
         * test_outline.py: +3 (the region derives; the memo is keyed on
           coordinates; plus (1)'s pair).
PROCESS NOTE, since the working agreement is explicit about the mechanism: a
         `git checkout floorplanner/mainwindow.py`, used to undo a deliberate
         break-it-to-prove-the-test experiment, discarded that file's
         uncommitted work along with it. Reapplied and re-verified. The rule is
         written for handed-back DOC edits; it applies to uncommitted code just
         as literally, and the safe move is to make the experiment in a copy.
         RULED at the P3.5 close and now a working-agreement entry of its own
         ("Destructive experiments run in a worktree, or after a WIP commit"):
         the solution was already in use in this same task, since the perf
         comparison ran the old code in a `git worktree`. The followup below
         used exactly that to verify its new tests against pre-fix code.

DEFECT 28 -- RULINGS AT THE SESSION BOUNDARY (2026-07-29). Committed here
         before stopping, per the handoff-spec rule: a fresh session reads the
         state from this block and needs nothing from chat.

  1. TWO DEFECTS, NOT ONE. The leak has a test half and an app half and they
     are fixed separately.
       * THE FIXTURE LEAK -- `tests/conftest.py`'s `win` fixture ends with
         `w.close()`, which hides a window and neither destroys it nor stops
         its 180 ms dirty timer. Registered under DEFECT 28.
       * DEFECT 29 -- the APP half: `MainWindow.close()` leaves a timer running
         that walks the whole document. A user closing one plan window while
         another is open pays that cost invisibly, so this is a real behaviour
         defect and NOT to be slipped in under a test-isolation fix.

  2. LEAK GUARD AS ACCEPTANCE, WITH A FAIL-FIRST RECEIPT. The fix is accepted
     by a guard that asserts no stale `MainWindow` keeps an active dirty timer
     (equivalently: `live_mainwindows` stays bounded across the suite). The
     guard MUST be shown FAILING against the current tree before the fix
     lands -- the receipt standard, unchanged.

  3. THE CORPSE-TABLE STANDARD: NO BLANK ROWS. Every corpse is attributed to
     the test whose scene it actually holds, not the test that was running.
     A corpse with no owner is listed AS unowned rather than dropped.
     Currently unowned: **'Kitchen' / 'Pan' on symmetricP1** -- no test has yet
     been shown to leave that overlap, and until one is, defect 28 is NOT
     dissolved into "leaked windows misreport". `'A'`/`'B'` IS owned:
     `test_save_verifies_deep`'s own deliberate fixture, working as designed.

  4. RE-CERTIFICATION: DEEP GREEN 10/10 under the machine-written trailer
     (`tools/gate.py`). Not 1 clean run, not "it looks fixed" -- ten.

  5. THE HISTORICAL CLAIM IS BOUNDED. What is established: a leaked window CAN
     misreport an earlier test's state, and did, five times on two harvests.
     What is NOT established, and must not be asserted: that DEEP's green/red
     has been meaningless for its whole existence. The mechanism has existed as
     long as the timer has; the OBSERVED instances are all from P3.6, when the
     first tests loading a twenty-room plan into `win` arrived. Anything wider
     needs its own measurement.

  6. DEFECT 26's `E` SIGHTINGS, one line: they are the same mechanism -- a
     stale window's timer firing inside a later test -- so the four sightings
     and the "suppressing" interventions are all explained by it, and no
     separate cause is outstanding.

P3.6  CODE COMPLETE, NOT TICKED -- blocked by defect 28 (branch v5-topology)
         DEFECT 26 IS FIXED and the diagnosis is worth carrying forward as the
         standard for what "root cause" means here: a stack, then an
         explanation for every property the bug had, then a narrow fix. It was
         never memory corruption -- `verify()` raised inside a QTimer callback,
         and PyQt turns an exception escaping a C++ -> Python callback into
         `qFatal()` -> `abort()`. The guard is narrow (that exception type only,
         at the 7 callback paths reaching the 3 call sites) and the acceptance
         was 0/10 crashes against ~4/20 before.
         WHAT REMAINS IS DEFECT 28, which the crash was hiding: a group rotation
         genuinely produces overlapping placed rooms (I11), ~2/10 deep runs. The
         tick waits on it, because DEEP green-and-reliable is the condition.
         Every acceptance property is green and every ruling is implemented,
         and the tick is still withheld, because the gate ruled at this task
         is what found the reason. `tools/gate.py` runs the three gates with
         their output CAPTURED, and under `FP_VERIFY_DESIGN=deep` the suite
         then ABORTS about 40% of the time -- rc 0xC0000409, a hard process
         crash, not a failing test. Bisected to P3.6: 0 of 4 at `e3fabb6`,
         the commit immediately before this task's first. A phase whose gate
         cannot be relied on to run is not a phase that has passed its gate,
         whatever the counts say when it does complete.
ruff:    clean
pytest:  OFF  512 passed, 6 xfailed in 15.9s
         ON   512 passed, 6 xfailed in 19.8s
         DEEP 507 passed, 4 xfailed, 7 deselected in 20.0s
         516 collected; OFF 512+6 and DEEP 507+4+7 both reconcile against
         `--collect-only`.
commits: 94a4de6 (0 spec) . 2fb3c77 (1 the anchor) . f964394 (1a the phantom E)
         . 80435c1 (1b R4b/R2b rulings) . 7fe1aa2 (2 defect 24) . 3cdf046 (3
         R4b) . e4907c7 (3a the gate that was not gating) . 52111c3 (4 R2c) .
         41cc975 (5 R2b) . ea50dce (6 R5)

THE AMENDED ACCEPTANCE (R1), and each of its four properties green:
  (a) an opening anchored `from: "v2"` keeps its `offset_in` exactly when the
      wall is stretched AT v2 -- `test_an_opening_holds_its_offset_when_the_
      far_end_is_stretched`. RECEIPT: failed against s-based code before the
      anchor landed.
  (b) reversing a wall leaves the opening's physical position unchanged --
      `test_reversing_a_wall_leaves_its_openings_where_they_are`. RECEIPT:
      failed measurably, the door mirroring 200.0 -> 40.0.
  (c) the split of R2 -- `test_a_split_clear_of_a_door_leaves_it_exactly_where_
      it_was`. WRITTEN AT R2b, and it did not exist before: R1 listed it, but
      the split coverage was the two refusal pins, and refusal is not a
      property of the anchor -- it is the absence of one.
  (d) loading a plan whose door no longer fits REPORTS it --
      `test_an_opening_that_cannot_be_placed_is_reported_not_dropped`, on the
      v4 load path specifically.

THE THREE NUMBERS IN THE TASK LINE WERE ALL WRONG, and the read-back is what
         caught them: "13 `except ValueError` sites" was every such site in the
         package, not the opening drops (7 at baseline, 8 today); `walls.py:568`
         had moved to `:1004`; and "P0.4 test 1 passes without xfail" pinned
         nothing, having never been xfail. Corrected in place at 94a4de6.

TWO DEFECTS FOUND WHILE DOING IT, both measured before being claimed:
         * DEFECT 24 -- `offset_in` read and written as a CENTRE distance in
           `topology.py`, near-edge everywhere else. 18.00" on a 36" door.
           THREE sites, not the two first registered: the third was a fourth
           hand-written copy of the arithmetic inline in `apply_merge_plan`,
           found only when fixing the other two turned its test red. All now
           route through one conversion.
         * DEFECT 25 -- a gesture can create a door-straddles-junction scene
           state the document can only represent as a reported fault. Registered
           P4.1 per ruling, with my argument for P4.3 and a move trigger in the
           entry rather than swallowed.

THE GATE AUDIT, ruled at the process failure, and it is a measurement in three
         layers because the first two were not trustworthy:
         1. GREP of every commit message (44 branch + 172 main): ONE hit, and
            it is e4907c7 -- my own disclosure, not a gate committed over.
         2. WHY THAT IS NOT THE ANSWER: 3cdf046's gate line was transcribed
            WITHOUT its ", 2 errors". The message looked green. Grepping
            messages audits what I wrote, not what ran.
         3. EMPIRICAL REPLAY of OFF and ON at all 27 code-touching branch
            commits: 8 red. Re-replayed with the P0.3b ratio class excluded:
            SEVEN GO GREEN, ONE STAYS RED.
         VERDICT: exactly ONE commit was made over a genuinely red gate --
         3cdf046 (P3.6(3), R4b), red on ON and DEEP with 2 errors, green at
         e4907c7 the next commit. Everything else was the timing-ratio class.

AND THE SEVEN ARE THE FLAP ROW'S EVIDENCE. `test_bake_scales_subquadratically`
         was caught red at 8.05 against a threshold of 8, and all seven show
         the tell: exactly "1 failed", ALTERNATING between the OFF and ON runs
         of the same commit. Broken code fails both; a straddling ratio fails
         whichever run the machine was busier during. ~7 of 27 replays, so the
         P3.8 row is widened from one test to the CLASS, with three members
         named.

TESTS: +9 (tests/test_openings.py, new). CHANGED, each with its one line:
         * the two R2b PINS flipped -- `split_edge` raising, `split_wall_at`
           declining. Both were placeholders pending representability;
           `match="P3.6"` was one test naming its own executioner.
         * the drag-side twin of the decline in test_wall_move.
         * two in test_topology_ops / test_topology that had encoded defect
           24's arithmetic (offset 50.0 where the near edge is 18.0) or were
           passing only because of it (a midpoint split that always fell
           inside the door).
         * test_a_clipped_band_leaves_every_room_coherent gained `rebase(win)`
           -- see the phantom-E resolution above.

P3.5-followup  done   commit d0ab89d -- DEFECT 22: a group move is a vertex move.
ruff:    clean
pytest:  OFF  503 passed, 5 xfailed in 16.5s
         ON   503 passed, 5 xfailed in 19.4s
         DEEP 498 passed, 3 xfailed, 7 deselected in 19.1s
FOUND BY A SMOKE TEST, not by the suite, and the gap is the finding as much as
         the bug. Symptoms on a v5 plan: some rooms did not track a whole-design
         group move; later individual room moves worked; and `unwelded_ends`
         warnings fired repeatedly with a moving count on a file that opened at
         zero.
REPRODUCED HEADLESSLY BEFORE ANY FIX, per the standard:
         * 140 of 140 room outline corners held one of their own walls'
           vertices before the bake -- 0 of 140 after. A party-wall drag then
           resized NOTHING: M Bath -18.20 sf / WIC +9.50 sf before, +0.00 /
           +0.00 after.
         * `unwelded_ends` 0 -> 133 grouping every ROOM; 0 -> 1 on a rubber
           band; 0 -> 0 grouping every WALL.
         * split telemetry during the bake: 160, all at items.py:703/704 --
           the exact residue P3.4 (iv) attributed to `bake()` and assigned to
           P4.5.
THE HYPOTHESIS WAS CONFIRMED FOR THE LOAD-BEARING HALF AND REFUTED FOR THE
         VISIBLE ONE, which is worth separating. CONFIRMED: `bake` assigned new
         COORDINATES to every member wall end (split-on-write) and rebuilt each
         carried room's corner list beside it, so the two agreed numerically and
         shared nothing -- orphaning the outlines P3.5 made authoritative.
         `refresh_rooms` re-bound and re-shared after every bake, so deferring
         bake's conversion to P4.5 was safe exactly as long as detection
         existed; P3.5 changed the deferral's premise, which is why this is a
         P3.5-followup and not P4.5's. REFUTED as the cause of "some rooms don't
         track": that is duplicate-on-group (defect 3, P4.5). A rubber band
         needs an item FULLY inside, so a wall poking out is left behind, its
         room's walls are DUPLICATED into the group, and `room_owns_walls` is
         then correctly false -- 17 of 20 tracked, and the 3 that did not were
         right not to. P3.5 only removed the re-detection that used to hide it.
THE FIX IS THE PLAN'S OWN `move_vertices`, and it is smaller than what it
         replaces. `_corner_records` resolves every corner the group's geometry
         holds together with the wall ends and outline edges on it;
         `_apply_corner_records` relocates each once. Walls and outlines follow
         because they hold those corners -- a bake is now the same operation as
         a wall drag.
THE CARVE-OUT IS RESPECTED BY SPLITTING, not by an exclusion list. A corner a
         NON-member wall also holds is split off before anything moves, so the
         group goes and the outsider stays -- today's behaviour exactly.
         Relocating it wholesale would wire a member to an outside wall, which
         is what the `group() is None` guards exist to prevent. Own test.
ROTATION HAD THE IDENTICAL DEFECT (140/140 -> 0/140) and now moves through the
         same records, resolved once at `_begin_rotation` and re-applied from
         the START point each event -- drift-free AND identity-preserving, where
         before it was split-on-write per mouse move. THE FIRST ATTEMPT WAS
         WRONG AND SAID SO: re-welding at `_finish_rotation` CONVERGED rather
         than closed (0/140 -> 138/140, then 139/140 on a second pass), which is
         how a positional instrument fails where an identity one is needed.
THE WARNING'S ERGONOMICS, because a correct warning that misattributes teaches
         people to ignore the channel that will one day be right. It said
         "expected on a plan loaded from a legacy file" for EVERY case -- true
         of what a file arrives with, false of what an edit tears -- and fired
         on every debounced snapshot, so a plan that opened clean produced a
         stream of them with a moving count. Now the first walk after a load
         sets the BASELINE, only a walk finding MORE warns, the message names
         the split (opened-with vs NEW), and a repeat of the same state is
         silent. `strict=True` is untouched: two tests pin it.
PERF HELD, and the harness earned its keep twice. bake 6.5 -> 28.6 ms
         (n=4 -> n=8), ratio 4.39, against P3.5's 6.9 -> 28.0 / 4.03. The FIRST
         cut rebuilt each member wall inside the loop -- redundant with the
         `rebuild_all_walls` that follows, and cascading -- and cost 9x
         (25.9 -> 251.3 ms, ratio 9.70). Caught by `test_bake_scales_
         subquadratically` on the first full run.
TESTS ADDED (5), and one of them is NOT the receipt -- verified by running all
         five against pre-fix code in a worktree:
         * whole-plan group + move carries every room, unwelded_ends still 0.
           PASSES ON BOTH SIDES: the old bake translated each carried room's
           corner list explicitly, so the rooms tracked POSITIONALLY. It guards
           the property at a scale the rest of test_groups.py never reaches (20
           rooms / 80 walls vs ~5 members) and is the first group test to look
           at the debris counter at all. Annotated as such in its own docstring
           so it is not mistaken for the receipt later.
         * the outlines still hold their corners after a bake, and a corner move
           still resizes the rooms -- THE RECEIPT, fails pre-fix.
         * the rotation half -- fails pre-fix.
         * a group move never drags a wall outside it -- the carve-out guard;
           passes on both sides by design, since it pins what must NOT change.
         * the warning names its cause and says it once (plus its mirror, that a
           legacy plan is still blamed on the file) -- both fail pre-fix.
WHY 503 GREEN TESTS MISSED IT: every group test in the suite tops out at ~5
         members, and not one had ever asserted on `unwelded_ends`. The bug
         needed a plan big enough to have party walls and a check nobody was
         making. Both gaps are closed here.

P3.5-followup, PER-ROOM DIAGNOSIS -- asked for after the fix landed, to explain
         the TWO presentations in the reported screenshot (one room fully
         detached with its dashed outline at the original position, another
         offset but coherent). Measured per room on a rubber-band selection over
         92% of symmetricP1, reporting (a) outline vertices matching no endpoint
         of any wall the room names, (b) whether walls moved, outline moved,
         both or neither, and the identity count underneath both.
         THE TWO PRESENTATIONS ARE TWO DIFFERENT DEFECTS, and the prediction
         that they collapse to one cause is REFUTED. Recording that is the
         point of having predicted:
         * OFFSET BUT COHERENT -- 17 of 20 rooms. walls 13/13 moved, outline
           13/13 moved, (a) = 0. Nothing visible is wrong. IDENTITY 0/13: every
           corner is a different object from its wall's vertex, because the old
           bake computed the room's new corner list SEPARATELY from the walls'
           new coordinates and the two agreed only numerically. This is DEFECT
           22, it is invisible in any screenshot, and it is fixed -- the same
           run post-fix reads 13/13 identity with every other column unchanged.
         * FULLY DETACHED -- 3 of 20 (Garage, PKT Off, Util). walls 6/9 moved,
           outline 0/9, (a) = 5 stranded corners, identity 4/9 -- the four
           corners it shares with the walls that did NOT move. The room was not
           carried at all (`room_owns_walls` false), because the band clipped
           one of its walls and `group_selected` duplicated the rest.
           BYTE-IDENTICAL BEFORE AND AFTER THE DEFECT-22 FIX: 46.65" / 39.98" /
           23.32" of region-to-walls drift either way. The vertex translation
           cannot touch it, because the room is not in the set being moved.
         AND THE "P3.5 UNMASKED IT" CLAIM IS WITHDRAWN, having been asserted
         before it was measured. The same drift measurement on the pre-P3.5
         tree strands Garage by 148.3" against 46.65" now -- re-detection was
         not hiding the detachment, it was landing the room somewhere worse.
         The detached presentation predates P3.5 and is REGISTERED AS DEFECT 23
         against P4.5, because what to do about it is a semantics decision (does
         a room whose walls partly moved DEFORM to follow the corners that
         moved, as a party-wall drag already makes both its rooms do -- or stay
         put?) and that question is what a group IS.
         METHOD NOTE: metric (a) is NOT comparable across the P3.5 boundary.
         Before P3.5 an outline edge could be spanned by a LONGER wall, so a
         corner legitimately sat mid-wall; "corner matches no wall endpoint"
         only became a defect once one edge meant one wall end to end. The
         cross-boundary comparison is the drift number, which is basis-free.

P3.5-followup, ACCEPTANCE ITEMS -- four, answered in order.

COMMIT NAMING, and the rule was NOT honoured on the first pass. The fix, its
         telemetry and its tests went in as ONE commit, d0ab89d, not three. The
         full gate (ruff + OFF/ON/DEEP) was run immediately before it, so the
         green is real; what is missing is the ROLLBACK POINTS the sub-commit
         rule exists to create. Recorded rather than rewritten -- history
         surgery to make a log entry look tidier is the wrong trade. The
         remainder was split properly: 06c2145 (a) the warning wording,
         408adf7 (b) the tests, plus this doc commit, each at a full gate.

THE +6, named from a collect-only diff of f738437 against HEAD (502 -> 508
         collected; nothing removed):
           test_groups::test_whole_plan_group_move_carries_every_room
           test_groups::test_a_group_move_leaves_the_outlines_still_holding_
             their_corners
           test_groups::test_a_group_rotation_also_keeps_the_corners
           test_groups::test_a_group_move_never_drags_a_wall_outside_it
           test_design_bridge::test_the_warning_names_the_cause_and_says_it_once
           test_design_bridge::test_a_legacy_plan_is_blamed_on_the_file_not_on_
             an_edit
         Plus, at (b), a SEVENTH that is an xfail rather than a pass:
         test_groups::test_a_clipped_band_leaves_every_room_coherent -> P4.5.
         So the census is now 503 passed / 6 xfailed, and the sixth marker is
         that one -- named here so the next delta starts from a known set.

STEP 4 WAS HALF-DONE AND IS NOW WHOLE. The whole-plan test asserted only that
         each room's outline LANDED in the right place, which is why it passed
         against the pre-fix code. It now asserts all four per-room columns --
         walls-moved, outline-moved, identity, unwelded_ends -- on a 100%
         selection with no clipped rooms, and FAILS pre-fix (identity 0 where 4
         is required, verified in a worktree). The diagnosis's columns and the
         guard's columns are now the same columns.

STEP 5 WAS DONE AT d0ab89d, and the specific question is answered by
         measurement on the defect-23 repro POST-FIX: the duplicated walls left
         behind by a clipped band DO register as unwelded ends under a live
         gesture, so the rewording belongs to this task exactly as reasoned.
         Same 10-walk sequence (open, idle, group, bake, four debounced
         snapshots, a second move, one more snapshot):
           BEFORE  8 warnings, one per snapshot, every one of them saying
                   "expected on a plan loaded from a legacy file"
           AFTER   2 warnings, one per DISTINCT state (1 end, then 8), both
                   reading "... are NEW ... this is not the legacy-load case"
         The idle and post-open walks are silent in both, and the legacy case
         still says legacy (`test_a_legacy_plan_is_blamed_on_the_file_not_on_an_
         edit`). Reading the message the repro actually printed also caught the
         copy saying it backwards -- "0 of them since the plan was opened and 1
         NEW" -- fixed at 06c2145.

ONE UNEXPLAINED OBSERVATION, recorded rather than dismissed: a single `E`
         appeared in one DEEP run's truncated progress output. Not reproduced in
         five subsequent full DEEP runs (NOT "under different random seeds" --
         that phrase is withdrawn at defect 26 round 2: pytest-randomly is not
         installed, so every run in this project has always been in the same
         order), and an
         explicit ERROR grep over a full `-ra` run finds nothing. Most likely a
         cut-off pipe rather than a real error, but it is written down here so
         that if it recurs at P3.6 it is the second sighting, not the first.
         STANDING INSTRUCTION, carried into P3.6 by ruling: a recurrence during
         P3.6 is a SECOND SIGHTING and is investigated on the spot -- not
         re-filed as a first.
         >> RESOLVED AT P3.6, and the guess above was wrong in both halves: not
         a cut-off pipe, and not a timing flap. It is
         `test_a_clipped_band_leaves_every_room_coherent`, added at 408adf7 --
         the defect-23 characterization. It deliberately leaves the scene
         corrupt (stranded rooms are its subject) and never declared that state
         as a baseline, so under FP_VERIFY_DESIGN=deep the `win` fixture's
         teardown verify fires and pytest reports the test TWICE: an `E` in the
         progress line, a second XFAIL in the summary. Fixed with `rebase(win)`,
         the move `_overlapping_rooms` has always made for its deliberate
         overlap. THE SAME DOUBLE-REPORT WAS THE OFF-vs-DEEP CENSUS DISCREPANCY
         -- one cause, two symptoms. Recorded as a closed sighting; a THIRD
         would be a new bug, not this one.

P3.4  done   (branch v5-topology; four sub-commits + two riders)
ruff:    clean
pytest:  OFF  491 passed, 4 xfailed, 1 xpassed in 19.2s
         ON   491 passed, 4 xfailed, 1 xpassed in 24.6s
         DEEP 486 passed, 3 xfailed, 7 deselected in 22.2s
         (baseline in: P3.3's 447/4/1. +44 tests, one deleted -- see (iv).)
commits: ea54413 (i) · 340816c (ii) · a4a3336 457105e e49c07f (iii, three
         families) · 670fded (rider: the two divergence rulings) · 89f3d8b (iv)
         · cf7f850 (defect 20) · plus the per-sub-commit doc entries below.
         Logged sub-commit by sub-commit per the handoff-spec rule, so a
         successor session reads the state from here plus the seven settled
         points at lines 375-408 rather than from a chat summary.
(i) done   commit ea54413 -- planner/applier factoring + the scene applier for
         merge_collinear.
ruff:    clean
pytest:  OFF  468 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   468 passed, 4 xfailed, 1 xpassed in 21.9s
         DEEP 463 passed, 3 xfailed, 7 deselected in 18.5s
files:   floorplanner/design/topology.py (GraphView/WallView/OpeningView,
         Merge/PlannedOpening, plan_merge_collinear, apply_merge_plan,
         graph_from_design; merge_collinear becomes their composition),
         floorplanner/walls.py (graph_from_scene, apply_merge_plan_to_scene,
         merge_collinear_scene), tests/test_topology_ops.py (new, 21)
NO EXISTING TEST CHANGED -- `git status tests/` shows only the new file, all
         three ways. The changed-test budget point 4 governs is still untouched
         going into (iii).
THE SHAPE, since it is the crux and the thing (ii)-(iv) all lean on: the
         decision runs ONCE, pure, over a neutral `GraphView` whose keys and
         anchors are the CALLER's own handles -- wall ids and vertex ids for a
         Design, `WallItem`s and `Vertex` objects for a scene. It returns a
         `Merge` delta (survivor, absorbed, the corner anchors the ends adopt,
         the planned opening offsets, the corners consumed). Two thin appliers
         execute it, touching only what it names. The delta deliberately does
         NOT name room binding: a Design records that as wall.left/right, the
         scene as WallItem.rooms, and each applier derives its own from
         `Merge.absorbed`. That is the one thing the two targets genuinely
         represent differently, and saying so is cheaper than pretending
         otherwise.
TWO BEHAVIOUR CHANGES IN THE PURE OP, both found BY single-sourcing rather
         than in spite of it, and both fixes:
         * merge no longer REFUSES a wall carrying openings. They are
           redistributed onto the merged span and deduped -- DEFECT 9, closed
           on the live-editing path the task text names. Guarded both ways: the
           new op yields one door, and `_coalesce_all_impl` on the identical
           input still yields two, so the closure is legible rather than
           asserted.
         * the survivor keeps its OWN DIRECTION. The old code wrote
           `w1.v1, w1.v2 = far1, far2`, which REVERSES the survivor whenever the
           run extends behind its v1 -- and did not swap left/right to match, so
           every side on that wall silently flipped. Latent, unpinned, and
           invisible until the same code had to serve a scene that renders
           sides. Own test.
TELEMETRY, ahead of point 5's ledger: an exact end-to-end merge causes ZERO
         split-on-writes -- the merged end is re-pointed AT the corner's vertex
         (`set_end_vertex`), not assigned a coordinate as coalesce did. A merge
         absorbing a wall from up to perp_tol off the line still splits, and
         that is correct: that end lands where no corner was, so it is a new
         corner and should say so.
A NARROWER CLAIM THAN IT LOOKS, stated so (iii) does not inherit a
         misconception: the merge shares the SURVIVOR's end with the corner
         anchor. It does not rebind OTHER walls sitting at that corner -- that
         is weld's job, and weld is still on this task's deletion list. What is
         true today is that both ops resolve the same corner to the same
         representative `Vertex`, so they converge rather than fight.
(ii) done  commit 340816c -- split_edge scene-side, the split rule's second
         half, the guard retarget.
ruff:    clean
pytest:  OFF  482 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   482 passed, 4 xfailed, 1 xpassed in 21.8s
         DEEP 477 passed, 3 xfailed, 7 deselected in 20.7s
files:   design/topology.py (Split, plan_split_edge, apply_split_plan;
         split_edge becomes their composition), walls.py
         (apply_split_plan_to_scene, split_wall_at, WallItem.
         _split_body_landings + _run_wall_under), tests/test_wall_move.py
         (+7, ADDITIONS ONLY -- 0 deletions), tests/test_topology_ops.py (+7),
         tests/test_topology.py (the one rewrite, below)
THE SPLIT RULE IS NOW WHOLE. P3.3 built the first half and left the second
         declared-but-not-done, tee branch on the coordinate path with a
         comment naming this task. A body-landing now SPLITS the wall it lands
         on -- which MAKES the vertex it never had -- and is then promoted onto
         it exactly as a corner attachment is. The new segment joins the run,
         so the user still slides the whole wall they grabbed (own test; that
         is the way this could have silently gone wrong).
TEST CHANGED (1), the pre-authorized one, named per the working agreement:
         tests/test_topology.py::test_split_edge_raises_on_a_wall_with_openings
         asserted `pytest.raises(NotImplementedError, match="P3.3")`. OLD OP:
         split_edge refused any wall carrying an opening. NEW OP: it
         redistributes them. WHY THE ASSERTION MOVED: that message was a
         placeholder for unbuilt work and said so; the work is built here, so
         the assertion pinning its absence has nothing left to pin. Rewritten
         as TWO tests -- redistribution works, and the guard SURVIVES narrowed
         to the case redistribution genuinely cannot answer. Hence the
         pre-authorized string change, `match="P3.3"` -> `match="P3.6"`.
THE GUARD IS RETARGETED, NOT RETIRED, and the distinction is the content of the
         ruling. Redistribution answers "which segment owns the door". It
         cannot answer "which segment owns a door the cut runs THROUGH",
         because neither does -- that is an opening which no longer fits where
         it lands, and reporting one instead of silently sliding it is P3.6's
         line in this plan. So the guard keeps its P1.3-followup discipline
         (fail loud AT the call site) on a strictly smaller domain.
TWO POLICIES, ONE DECISION -- declared, because it is the closest this task
         comes to the applier drift point 1 forbids, and it is not that.
         `topology.split_edge` RAISES on a straddling split; the scene op
         DECLINES it. Same planner, same delta, same `straddled` flag. What
         differs is what each CALLER does with a flagged delta, because one is
         a document repair and the other is a mouse gesture that must not
         crash mid-drag. The decision is single-sourced; only the policy is
         local, and a declined split leaves P3.3's exact behaviour behind.
TELEMETRY -- point 5's prediction, measured BOTH ways rather than asserted:
         * dedicated tee scenario, 12 drags: 12 split-on-writes BEFORE
           (measured by disabling the new pass), 0 AFTER. The branch is silent,
           which is the claim point 5 makes.
         * composite (coalesce + weld + group + bake + ungroup + 12 drags):
           mouseMoveEvent splits 4 -> 1.
         * AND THE RESIDUE IS NOT THE TEE BRANCH FAILING. Two landings were
           DECLINED because the split point falls inside an opening -- and
           those openings turn out to be 15 IDENTICAL 96" windows stacked at
           one `s`, produced by the old `_coalesce_wall_impl` on the
           bake/ungroup path. That is DEFECT 9 in the wild, inside the code
           (iii)/(iv) delete. PREDICTION FOR (iii), recorded now so it is a
           prediction and not a rationalisation: retiring coalesce removes the
           stacks and those two landings then split.
         * a call site P3.3's scenario never triggered: 8 splits at
           walls.py:233 in `_coalesce_wall_impl`. Also (iii)/(iv)'s.
THE CORPUS GUARD HAS GONE VACUOUS, and saying so is the point. P3.3's
         press-every-wall test still passes -- but neither corpus plan has an
         unwelded body-landing, so pressing every wall of sample_plan and
         planc1 now makes exactly 0 splits (measured). It no longer exercises
         the risk it was written for. Added the case that DOES split, asserting
         the document is unchanged across it: the scene walk already cuts walls
         at junctions (`split_params`), so a press-time split only makes the
         scene agree with what the document always said. Verified rather than
         assumed -- 2 scene walls -> 3, document byte-identical, 3 document
         walls before and after.
(iii) done  commits a4a3336 (family 1), 457105e (family 2), e49c07f (family 3).
ruff:    clean
pytest:  OFF  491 passed, 4 xfailed, 1 xpassed in 16.7s
         ON   491 passed, 4 xfailed, 1 xpassed in 19.3s
         DEEP 486 passed, 3 xfailed, 7 deselected in 17.4s
NO EXISTING TEST CHANGED across all three families. The changed-test budget
         point 4 governs is still spent only on (ii)'s one pre-authorized
         rewrite, going into (iv).
FAMILY 1 -- COALESCE (5 sites): view.py:487 and walls.py:1385 (draw / drag
         release) -> `merge_wall`; planio.py:181 (load), rooms.py:1020 (room
         label drop), mainwindow.py:820 (ungroup) -> `merge_all`.
         `merge_wall` forces the passed wall to be the run's SURVIVOR -- the
         caller has just drawn or dragged that item, holds a reference to it,
         and it carries the selection; the planner takes the run's first wall
         in the caller's order, so the whole of "this one survives" is a sort
         key. UNGROUP IS WIRED, NOT MIGRATED, per the ruling, with the comment
         at the site: under P4.5 nothing is duplicated so nothing needs merging
         on ungroup, making that call P4.5's to DELETE rather than this task's
         to port.
         Behaviour change, small and a fix: the merged wall lands on the union
         span exactly, where `_coalesce_wall_impl` re-snapped both ends to the
         6" grid. bridge.py:550 already flags that snap in its own words
         ("Coalesce MOVES geometry"). No test depended on it.
         PERF: the planner gained `_candidate_groups`, `_WallIndex`'s line
         bucketing moved to where the merge decision now lives -- without it a
         per-wall merge scans every wall on every draw-release, trading
         coalesce's O(local) for O(plan), the direction P3.8 must not go.
FAMILY 2 -- WELD (3 sites): view.py:489 `join_endpoints` -> `weld_wall_ends`;
         imageio.py:180 `weld_all` -> `weld_scene`; mainwindow.py:827 ->
         `normalize_walls`. After this the whole coalesce+weld set is a
         CALLERLESS ISLAND.
         THE COMMAND OUTLIVES ITS IMPLEMENTATION, per the ruling. Edit ▸
         Coalesce all walls now is the explicit plan-wide normalization: merge
         every collinear run, then weld -- close the gaps, fold coincident ends
         onto one vertex, split a wall where another's end lands on its body.
         Same menu item, same intent, new machinery, still ungated.
         Welding now has a TOPOLOGY half. `weld_all` left a welded corner as
         two coordinates that happened to agree, which is exactly what P3.3's
         drag then had to rediscover by scanning at every press. The geometry
         snap is kept verbatim: closing a 9" gap is a repair, not topology, and
         it is the only way a drawn or extracted plan closes junctions at all.
         ONE RULE, FOUND BY A FAILING TEST. The first cut had `weld_scene`
         split body landings too, and test_extract_from_reference_adds_walls
         went 5 walls -> 7. The split is CORRECT topology -- but shipping it
         inside a call-site migration is a behaviour change smuggled under a
         rename, and it edits a wall the user never touched. So splitting
         belongs to the EXPLICIT pass and nowhere else: `weld_wall_ends`
         doesn't, `weld_scene` doesn't, `normalize_walls` does. Applying the
         rule uniformly made the test change unnecessary, which is the tell
         that the rule was right and not a dodge. P3.5 will want plan-wide
         planarity for `enclosing_face`; that is P3.5's to ask for, through the
         pass built for it.
FAMILY 3 -- THE QUERY HELPERS: one migrated, one policed, two divergences.
         `_joined_at` MIGRATED: a 0.6" coordinate search becomes a DEGREE
         lookup on a `_CornerIndex`, and `_WallIndex`'s endpoint hash is gone.
         Zero behaviour change, and the replacement carries its own oracle --
         `_joined_at`'s un-indexed fallback still runs the old search, so the
         test compares the two directly on every end rather than trusting the
         reasoning. `_CornerIndex` is now the SINGLE definition of "these ends
         are one corner"; both halves earn their place, since identity is the
         real question but load deliberately does not weld, so in a loaded plan
         only position can see the corner.
         `coincident_walls` POLICED, NOT MERGED, and that is a decision. It is
         on the hottest path in the app (`WallItem.rebuild`, once per wall per
         pass) and routing it through the planner would allocate a view per
         candidate to prove a predicate that is already a transcription. A
         drift gate pins the two equal across overlapping / off-grid /
         abutting / perpendicular / diagonal pairs instead -- the same move
         `--verify-design` makes for the two appliers.
TWO CENSUS DIVERGENCES, reported rather than forced (Touches lists are hints):
         * `_WallBBoxIndex` CANNOT die at P3.4. The task line lists it, but its
           last caller is rooms.py:340, the memoized room dirty-check -- and
           "refresh_rooms memoization" is on P3.5's list BY NAME. A line dies
           when its last caller dies, and this one's last caller is P3.5's.
         * `wall_endpoint_open` NOT migrated to degree, deliberately. Its
           tolerance is JOIN_TOL (9"), not SHARE_TOL: the 9" scan was a PROXY
           for a question the pre-vertex code could not ask. Degree is the
           truer question, but swapping them changes which ends the draw-snap
           offers to align with on unwelded geometry -- a behaviour change
           needing this task's own three-part earning, and it buys no deletion
           since the helper survives Phase 3 either way. Recommended as its own
           change or as P3.5's.
         Consequence: `_WallIndex` SHRINKS rather than dies. Its line buckets
         are a spatial index, not detection machinery, and the planner needed
         the identical bucketing badly enough that `_candidate_groups` is a
         copy of them. The honest end-state is one index, not zero.
RIDER (commit 670fded) -- the two (iii) divergences, ruled:
         * `wall_endpoint_open` REFRAMED PERMANENTLY, in its own docstring, so
           no future task "migrates" it out of a misplaced sense of
           completeness. It is not a survivor of the old world; it is a correct
           citizen of the new one. Its tolerance is JOIN_TOL, the GESTURE
           tolerance, and gesture questions are inherently spatial. Degree
           answers the MODELLING question ("are these ends one corner?"); this
           answers the AIMING question ("is there something near enough to snap
           to?"). Degree cannot serve here even in principle -- the ends worth
           offering the user are precisely the ones NOT yet welded, so a degree
           query calls every one of them free and the snap has nothing to aim
           at. The docstring names `_joined_at` as the one that DID migrate.
         * THE BUCKETING DUPLICATION UNIFIED, not pinned. `topology.line_bucket`
           + `bucket_reach` are the one definition; `_candidate_groups` and
           `_WallIndex` both call them and `_WallIndex.OFF` is gone.
           Unification beat a second drift gate because the policy is pure
           coordinates, so it belongs on the Qt-free side with the scene
           importing it -- the dependency flows the right way, which is not
           true of most things one might want to share across that fence.

(iv) done   commit 89f3d8b -- the deletion, the junction contract, the checks.
DELETED, 149 lines across 7 functions, all callerless after (iii):
         `_coalesce_wall_impl` (59), `coalesce_wall` (8), `_wall_count` (5),
         `_coalesce_all_impl` (26), `coalesce_all` (7), `weld_all` (23),
         `WallItem.join_endpoints` (21) -- plus `_WallIndex`'s endpoint hash,
         folded into `_CornerIndex` at (iii): 50 lines -> 40.
EXIT CHECK 1 -- MEASURED DELETION vs THE ESTIMATE. Estimated 375 across 13
         functions; MEASURED 149 across 7. The gap is three survivors with
         named reasons, not shortfall, and 169 lines of the census live on:
         * `fracture_delete_wall` (55) + `_merge_intervals` (9) -> P4.1. Two
           live callers, not migrated at (iii), and retiring them IS P4.1's
           deliverable -- its acceptance is literally "P0.4 test 2 flips to
           pass". AND THE MEASUREMENT IS THE FINDING: a plain delete now KEEPS
           the room (1 room, 100.0 sf, 3 built walls + 1 open edge -- exactly
           test 2b's assertion), because P3.2 gave RoomItem a stored outline.
           P4.1's blocker is already gone and P4.1 is now a small change;
           doing it here would be landing another task's deliverable under this
           one's name.
         * `_WallBBoxIndex` (34) -> P3.5, as reported at (iii).
         * `_compute_wall_junctions` (31) STAYS -- next paragraph.
         * `_WallIndex` (40) shrank rather than died.
EXIT CHECK 4 -- THE JUNCTION CONTRACT, AND THE SWAP IT REFUSED. Point 3 said
         "if the junction test needs touching, the replacement is wrong."
         IT NEEDS TOUCHING, so the replacement is not made. Measured on the
         structural guard's own scene -- a horizontal and a vertical wall
         crossing mid-span -- the two share ZERO corners (all four ends degree
         1) while their `_solid`s genuinely intersect and the bbox pass
         correctly clips both. Adjacency-only neighbours find nothing, set both
         clips to None, and fail the guard. An unwelded crossing is a legal
         scene state (crossing-point insertion is not built), so bbox search is
         not legacy machinery here -- it is the only thing that answers the
         question. The contract worked exactly as designed: it was written to
         catch a wrong replacement, and it caught one.
         THE PIXEL ASSERTION LANDED ANYWAY, an ADDITION, because it is what
         makes any future attempt safe. POLARITY MEASURED, NOT ASSUMED, and it
         is the INVERSE of the spec's wording: the wall body is grey (150) and
         a seam is a DARK line across the junction (56), so "no LIGHT seam
         pixel" names the wrong failure. Seam-free asserts the interior stays
         body-grey; the `< 190` threshold is used where it genuinely belongs --
         the negative half, clip cleared, where an antialiased 1-px dark line
         must read under 190 and nowhere near 100. Both halves in one test, so
         the positive assertion cannot go vacuous. The structural pin is green
         and UNCHANGED.
EXIT CHECK 2 -- THE P2.3 KNOWN-REGRESSIONS ROW DOES NOT CLOSE, and the row's
         predicted fix was wrong on its own terms. Checked by hand: the 480"
         wall still returns as two 240" segments after the undo restore,
         `merge_all` does NOT re-merge them, and the body-drag still moves one
         segment (p1.y 12 and 0). It MUST not -- the mid-span T is a degree-3
         vertex, load-bearing for the planar subdivision, and merging through
         it would destroy planarity. So this was never merge's row to close.
         NOT FLIPPED; retargeted in place with the real fix named: the drag's
         run-gathering, where `_collinear_run()` short-circuits to `[self]` for
         a room-less wall. Left unassigned rather than invented, with P4.2 as
         the nearest task that touches the drag.
EXIT CHECK 3 -- THE DEFECT-9 PREDICTION, GRADED HALF-RIGHT AND PRECISELY.
         FIRST HALF CONFIRMED: retiring coalesce removed the stacks -- 16
         openings on one wall became 1. SECOND HALF FALSIFIED: the two tee
         landings still decline. But the residual cause is now legitimate
         rather than debris -- the harness puts a 96" window at the centre of a
         240" wall and the neighbouring grid line lands at s=120, dead inside
         it (measured: openings [(120.0, 96.0)], straddled 1). A genuine
         straddle, correctly declined, P3.6's case. The count coinciding at 2
         is coincidence; the mechanism the prediction named was real and is
         gone. Recording the falsified half is the point of having predicted.
EXIT CHECK 5 -- TELEMETRY RESIDUE, 137 splits on the composite scenario:
         64 + 64  items.py:703/704 in bake()   -- P4.5's, correct that they stay
          8       walls.py in _adopt_end()     -- MOVED, not new
          1       walls.py in mouseMoveEvent() -- the grouped/rigid branch, P4.5
         The 8 were `_coalesce_wall_impl`'s at (ii); they are the merge
         applier splitting on write when an absorbed end lands where no corner
         was -- declared at (i) as correct for that case. Same count, honest
         new home.
TESTS REWRITTEN -- the plan's biggest changed-test risk, one line each:
         * test_coalesce.py (whole file): `_coalesce_*_impl` -> `merge_all` /
           `merge_wall`. THE ASSERTIONS DID NOT MOVE -- they are the behaviour
           contract, not the implementation, and every line still says exactly
           what it said. Only the call changed.
         * test_walls.py: `join_endpoints` -> `weld_wall_ends`, `weld_all` ->
           `weld_scene`, `_coalesce_wall_impl` -> `merge_wall`. Assertions
           unchanged: the geometry snap they pin was lifted verbatim into
           `_snap_wall_ends`. Plus the pixel test, an addition.
         * test_characterization.py 5 and test_floors.py: `coalesce_all` ->
           `merge_all`; the group-exemption and cross-floor assertions
           unchanged.
         * test_topology_ops.py: the defect-9 OLD-op comparison DELETED with
           the op it exercised. Once the defect's implementation is gone there
           is no old behaviour left to exhibit and the test would be asserting
           against a museum piece. It did its job at (i) and (ii); a claim
           about code that no longer exists belongs in this log, and a comment
           at the site says so.
         * test_scaling.py, test_design_bridge.py: stale `coalesce_all` wording
           only, no assertion touched.
(iv) EXIT CHECKS as fixed before the work (all five answered above):
         1. the measured deletion count against the estimated 375 across 13
            functions, with `_WallIndex`/`_WallBBoxIndex` surviving named;
         2. the P2.3 Known-regressions row re-checked BY HAND (the 480"
            body-drag moving as one run) and flipped ONLY if it genuinely
            closes;
         3. (ii)'s recorded prediction, promoted to an exit check by ruling:
            retiring coalesce removes the defect-9 stacks, so the two tee
            landings that DECLINED in the composite telemetry should then
            split. Falsifiable, cheap, and if it holds it is the cleanest
            demonstration yet that the old machinery was manufacturing the
            conditions that defeated the new one;
         4. the junction contract's two halves: `test_junction_outline_is_
            clipped_so_walls_read_solid` green UNCHANGED, plus the new pixel
            assertion at the `< 190` threshold;
         5. tests/test_scaling.py's ungroup xfail reason still says "calls
            O(walls^2) coalesce_all" -- stale from family 1, true again only as
            history. Fix it with the deletion, where the claim actually changes.
Census re-verified on disk before starting:
         `coincident_walls` at walls.py:656 and :695 and view.py:597,
         `wall_endpoint_open` at view.py:248, and the dying caller at
         walls.py:201 inside `_coalesce_wall_impl`. ONE CORRECTION to the
         census's wording, not its content: BOTH walls.py hits are inside
         `WallItem.rebuild` (:656 is the party-wall opening cascade, :695 the
         neighbour-rebuild tail), not "rebuild and paint" -- `paint` reads the
         already-built `_path`. The adjudication is unaffected; both survive
         Phase 3 and both migrate.
```
