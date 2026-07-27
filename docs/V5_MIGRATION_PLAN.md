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
| ☑ | **P1.1** `design/model.py` — dataclasses | ruff + pytest |
| ☑ | **P1.2** `design/validate.py` — I1–I14 | ruff + pytest |
| ☑ | **P1.3** `design/topology.py` — weld/planarize/trace | ruff + pytest |
| ☑ | **P1.3b** Fix defect 18 (`_inner_faces` winding) + corpus diff | ruff + pytest |
| ☑ | **P1.4** `design_from_scene()` | ruff + pytest |
| ☑ | **P1.5** `apply_design_to_scene()` | ruff + pytest |
| ☑ | **P1.6** `--verify-design` shadow mode; suite runs with it on | ruff + pytest ×2 |
| ☑ | **P2.1** Load path: v1–v4 migrate + dirty + report; v5 direct | ruff + pytest |
| ☑ | **P2.2** Save writes v5; legacy export | ruff + pytest |
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
**Decide id policy here.** Items should carry **persistent uids, minted once** — stable across edits, and therefore macro-addressable — with `_canonicalize` (P1.5, `design/bridge.py`) applied only at **snapshot/serialization time**, for equality. Content-derived ids recomputed per walk are almost certainly the wrong thing to *persist*: P1.5's canonical ids sort by geometry, so moving one wall renumbers its neighbours. That is harmless for round-trip and undo comparison, which is all it was built for, but P3.1 makes scene items id-carrying and **P4.5 serializes groups by member id** — a group whose members are renumbered by an unrelated wall move is a live bug. Settle it at this task rather than discovering it at P4.5.
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
```
