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
| ☐ | **P1.1** `design/model.py` — dataclasses | ruff + pytest |
| ☐ | **P1.2** `design/validate.py` — I1–I14 | ruff + pytest |
| ☐ | **P1.3** `design/topology.py` — weld/planarize/trace | ruff + pytest |
| ☐ | **P1.4** `design_from_scene()` | ruff + pytest |
| ☐ | **P1.5** `apply_design_to_scene()` | ruff + pytest |
| ☐ | **P1.6** `--verify-design` shadow mode; suite runs with it on | ruff + pytest ×2 |
| ☐ | **P2.1** Load path: v1–v4 migrate + dirty + report; v5 direct | ruff + pytest |
| ☐ | **P2.2** Save writes v5; legacy export | ruff + pytest |
| ☐ | **P2.3** Undo snapshots the v5 dict | ruff + pytest |
| ☐ | **P2.4** Convert the corpus and the tooling | ruff + pytest |
| ☐ | **P2.5** Split `MainWindow` IO/CSV/image/floors out | ruff + pytest |
| ☐ | **P3.1** Vertex table live; `WallItem` holds `v1`/`v2` | branch, ruff + pytest |
| ☐ | **P3.2** `RoomItem.outline`; drop `perimeter_corners` | ruff + pytest |
| ☐ | **P3.3** Wall move = move vertices + split rule | ruff + pytest |
| ☐ | **P3.4** Topology ops replace coalesce/weld/fracture | ruff + pytest |
| ☐ | **P3.5** Delete the detection engine | ruff + pytest |
| ☐ | **P3.6** Opening anchors | ruff + pytest |
| ☐ | **P3.7** Delete `OpenWall` | ruff + pytest |
| ☐ | **P3.8** Perf verification vs P0.3 | ratios recorded |
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

### P1.2 — `design/validate.py`
Port all fourteen invariants from `tools/validate_design.py`. Keep the O(n²) ones (I5b, I11, I14) behind a `deep=True` flag so a per-command check can run the cheap ten.
**Acceptance.** `check()` returns `[]` for `symmetricP1.json` and `site_demo.json`, and non-empty for `planc1.v5.json`. Negative tests: nudge a shared vertex 0.3″ → I14 fires; point a wall's `left` at a room that doesn't name it → I6 fires.

### P1.3 — `design/topology.py`
Port from `tools/migrate_to_design_v5.py`: `weld_endpoints`, `planarize`, `split_edge`, `merge_collinear`, `trace_faces`, `enclosing_face`. Pure functions over the `Design`; no Qt.
**Acceptance.** `trace_faces` on `symmetricP1` returns 19 faces whose areas match the stored room areas. `weld_endpoints` on the legacy `planc1.json` geometry welds exactly 31 ends.

### P1.4 — `design_from_scene()`
Walk the live scene into a `Design`. **This is where the ten unfiltered floor queries get fixed** — the walk is level-scoped by construction.
**Acceptance.** For every `examples/*.json`: load into a scene the old way, `design_from_scene()`, `check()` returns `[]` (except the known-corrupt fixture). Room areas match `project_from_scene()`'s to 0.1 sf.

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
**Acceptance.** Opening `examples/planc1.json` yields M Bath 182.0 sf, Hall 61.5 sf, 31 welds in `provenance`, and a dirty document. Opening `examples/symmetricP1.json` is clean and not dirty. The legacy file on disk is never modified.

### P2.2 — Save writes v5
Plus **File ▸ Export legacy v4…** for one release, so nobody is stranded.
**Acceptance.** Save → reopen → `check()` clean, not dirty. Legacy export round-trips through the old loader.

### P2.3 — Undo snapshots the v5 dict
Still whole-document; only the payload changes. Groups now serialize, so **defect 3 partially closes here**.
**Acceptance.** `test_undo.py` green. New test: group, undo, redo — the group survives.

### P2.4 — Convert the corpus and the tooling
`examples/*.json`, `docs/make_gallery.py`, `examples/make_examples.py`, `tests/bench_rooms.py`, `fp_extract.py`'s writer, and the macro `open`/`save` tokens.
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
**Acceptance.** Suite green with no test changes. The `--verify-design` run stays green.

### P3.2 — `RoomItem.outline`
`RoomItem` gains `outline: list[OutlineEdge]`. `corners` becomes a derived property. `properties["perimeter_corners"]` is dropped on save and ignored on load (the schema already forbids it).
**Acceptance.** Room areas unchanged across the corpus. `_sync_corner_props` and its six call sites deleted.

### P3.3 — Wall move = move vertices, plus the split rule
Dragging a wall moves its two vertices. Implement the split rule: a collinear continuation past an endpoint splits first; a vertex landing on another wall's body splits that wall.
**Acceptance.** Port `tools/demo_move_wall.py` to `tests/test_wall_move.py`: moving `w24` by +12 y changes exactly Lounge and Front Porch by ±17.5 sf, total unchanged, `check()` clean. Add a split-rule test with a T-junction continuation.

### P3.4 — Topology ops replace coalesce/weld/fracture
`coalesce_wall`, `coalesce_all`, `_coalesce_*_impl`, `weld_all`, `join_endpoints`, `fracture_delete_wall`, `_WallIndex`, `_WallBBoxIndex`, `_compute_wall_junctions` → `merge_collinear`, `split_edge`, vertex adjacency. **Defect 9 closes here** (merge dedups openings).
**Acceptance.** `test_coalesce.py` and the coalesce half of `test_walls.py` rewritten against the new ops — **and this is the biggest "changed test" risk in the plan, so every rewritten assertion must be justified in the log.** ~330 lines deleted from `walls.py`.

### P3.5 — Delete the detection engine
`_RoomGrid`, `_WallGraph`, `detect_room`, `_detect_room`, `room_signature`, `refresh_rooms` memoization, `bind_room_walls`, `_wall_along_segment`, `_perimeter_span`, `room_owns_walls`, `walls_cover_room`, `duplicate_wall`, `_privatize_shared_walls`, `synthesize_room_edge`, `reloop_open_room`. "Detect room here" becomes `topology.enclosing_face`. **Defects 8 and 13 close here.**
**Acceptance.** ~550 lines deleted from `rooms.py`. `test_rooms.py` and `test_room_walls.py` pass against stored outlines. `room_boolean` rewritten as a polygon op on outlines that touches only its own walls.

### P3.6 — Opening anchors
`s` → `{from, offset_in}`. Delete the silent clamp in `WallItem.rebuild` (`walls.py:568`) — an out-of-range opening is an error surfaced to the user, not a slid door. Replace the 13 `except ValueError: continue` sites with a collected, reported error list. **Defects 6 and 7 close here.**
**Acceptance.** P0.4 test 1 passes without xfail. Loading a plan whose door no longer fits reports it instead of dropping it.

### P3.7 — Delete `OpenWall`
An outline edge with `wall: null` renders dashed.
**Acceptance.** `test_open_walls.py` rewritten against null edges; the class is gone.

### P3.8 — Perf verification
Re-run P0.3 and compare against the P0.6 numbers.
**Acceptance.** Ratios recorded in the log. Grouping 20 rooms creates **0** new walls — assert it.

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
```
