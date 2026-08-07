# v5 migration plan — staged, gated, executable

**Target:** `floorplanner/design/design-schema.v5.json` (vendored at P0.7; pointer at `docs/design-schema.v5.md`) · **Review:** `docs/CODE_REVIEW_v2.md` · **Model rationale:** `docs/DESIGN_MODEL_v5.md`

Seven phases. Every task is small enough to finish and verify in one sitting, and **every task ends on a green gate**: `python -m ruff check .` then `python -m pytest -ra`, both clean, before the next task starts. `main` stays shippable throughout except during Phase 3, which runs on a branch.

---

## Working agreement

**Moved to [`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)** on 2026-08-06 -- the standing rules outlive this migration, so they are no longer filed inside it. Nothing was reworded in the move.

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
| ☑ | **P3.6** Opening anchors — *ticked 2026-07-30 on the re-certification: **10/10 GREEN** under full-mode `tools/gate.py` trailers (ruff + OFF + ON + DEEP, every sum reconciling). Defects 26, 28 and 29 all closed.* | ruff + pytest |
| ☑ | **P3.7** Delete `OpenWall` — *ticked 2026-07-30 against the amended acceptance: the cue is drawn from the outline and pinned by a pixel test with measured polarity, the class and its `is_open` flag are gone (zero `git grep` hits in `*.py`), and the P3.5 Known-regression row closes on that test.* | ruff + pytest |
| ☑ | **P3.8** Perf verification vs P0.3 · **+ split-on-write exit survey** — *ticked 2026-07-30; **Phase 3 merged to `main` at `03f3868` on 2026‑07‑31**, all eight P3 rows complete.*  *(P3.8 detail: `bake` 10.6× faster (279.0 → 26.4 ms at 64 rooms); all four survey rows answered or dispositioned; the flap class retired class-wide; defect 27's DEEP CI job green. Merge checklist items 1–4 done at the tick; Gate 3 passed 2026‑07‑31 and the merge followed.)* | ratios recorded |
| ☑ | **P4.1** Delete-wall keeps the room — *ticked 2026‑07‑31, accepted at **PR #2** (merge commit; sub-commits `0df3aa5` census + rulings, `a0e1b95` delete_wall + 2b flip, `cce2eb6` corpse + tests). Acceptance met: P0.4 test 2b flipped xfail→pass on exactly the call-site switch (513/6 → 514/5); census 526 unchanged; defect 17 closed with the visible-lie coda.* | ruff + pytest |
| ☑ | **P4.1b** Defect 25's gesture-time message — *ticked 2026‑08‑01, accepted at **PR #3** (merge commit `ec5f207`; sub-commits `1d3eaa6` mechanism + tests, `e0519ae` record). Acceptance met: both gestures produce the specific message naming the doorway at release, pinned by two gui tests with a fail-first receipt against `main@708dc2e`; defect 25 closed; census 526 → 528.* | ruff + pytest |
| ☑ | **P4.2** Extract / join — *ticked 2026‑08‑02, accepted at **PR #4** (merge commit; 26 sub-commits, `dfd30af` … `ed9286c` + the record commit: core 1–7, mini-gate findings 8–15, tooling & floors 16–23, hand-off 24, census hygiene 25, record 26) — the first task under the Phase‑4 ruling's **Patrick mini-gate: PASSED, all 8 items**, on a fresh launch with the version label verified. Acceptance met: extract → move 500″ → join with `check()` clean at every step, I12 while floating, furnishings and openings intact; the party-wall regression flipped xfail → hard pass via the real `extract` (the P0.5 Known-regressions row closes). Defects 30, 34 and 13 (drag half) closed; defect 35 closed on the reporter's confirmation; six mini-gate findings fixed against measured reproductions, pinned by his macros verbatim. Census 528 → 552, local == CI.* | ruff + pytest |
| ☑ | **P4.3** Shuffle mode — *ticked 2026‑08‑03 on Patrick's acceptance, merged at **PR #5** (merge commit `4050e44`; 6 sub-commits `a6ded30` … `545b79a`: census + rulings, plumbing, gesture gating + the tiered doorway weld, acceptance, ruling 1's execution, the fuse-straggler finding). Acceptance met: shuffle on, a floating room dragged across the plan through the real handlers leaves both unchanged, `check()` deep-clean at every step. The P2.3 Known-regressions row closed as superseded-by-ruling (STAY, two replacement hard passes); defect row 36 fixed with the macro pinned verbatim; census 552 → 569, local == CI, xfails 4 → 3.* | ruff + pytest |
| ☑ | **P4.4** Concept rooms, `nominal_size`, duplicate-as-template — *ticked 2026‑08‑04 on Patrick's acceptance ("it works perfectly"), merged at **PR #6** (merge commit `ae9f0ad`; 5 sub-commits `868e315` … `da38c46`: census + the four rulings, the `^H` chord + token, duplicate-as-template, concept rooms, the record). Acceptance met: a one-room file validates against the schema and all fifteen invariants and loads into an existing design as a floating room (pinned against a **second** `MainWindow`, so "an existing design" is genuinely another document). The **carried census note resolves** — `_copy_spec` + `_perimeter_span` deleted, so P4.5 inherits the binding/outline duality with its clipboard consumer resolved; register row 37 closed with `^H`. Census 576 → 598.* | ruff + pytest |
| ☑ | **P4.5** Group semantics + z-order — *ticked 2026‑08‑06 on Patrick's mini-gate (**all ten items run and passed**, including item 10 — Align to grid and Distribute on a plan with shared party walls — and the cross-cutting dashed-edge watch) and the reviewer's acceptance. Merged at **PR #10** (merge commit `4b379fc`; 45 sub-commits `fbbebf4` … `1c6ff61`). Acceptance met on all five: `test_group_survives_roundtrip` flips xfail → pass (defect 3); `test_a_clipped_band_leaves_every_room_coherent` passes **as a consequence of the mechanism, not as a fix** (§2a's required wording, and literally true — a split simply stopped happening); `…_still_copies_them` rewritten into its opposite; the three duplicate-on-group tests replaced; the twenty-room test widened to **creates no OBJECTS at all**. Headline number: group the whole 20-room plan, move, ungroup → **189 → 189 scene items, zero new objects**, against the review's ≥106 duplicate walls and ≥149 duplicate openings on that same gesture. Defects 3, 11a and 23 closed; register row 36 closed at source; rows 47, 48, 49 filed. The P3.1 split-on-write shim retired entirely, its guarantee moved to the gate (`end_assign=0`). Census 619 → 633, xfails 2 → 1 (the survivor is deliberate, against row 47).*<br><br>**⚠ CARVE-OUT — DEFECT 11 IS ONLY HALF CLOSED, and this row says so rather than letting the tick imply otherwise.** P4.5's charter named the z-order collapse. **11a landed** — a room raised on a ghost floor no longer escapes its floor band (measured z −99996 → +10 against an active floor at 4; fixed by re-basing the raise into the item's own band, openings deliberately exempt). **THE RUNTIME COLLAPSE DID NOT LAND.** It hangs `test_drag_split_macro_keeps_every_room_rectilinear` at the first drag, bisected to `geometry.py`, trigger is the MAGNITUDE of the z step (`×1.0` completes, `×Z_STACK_BAND` hangs); the work was reverted and nothing of it is on the branch. **The agreed rule carries forward intact (ruling 4, unchanged): z = `floor_term + stack_term + type_term`, the backdrop's −1e9 becomes a TYPE TERM rather than a magic number, `bring_to_front`'s full-scene max scan dies with it, and the band arithmetic becomes NAMED CONSTANTS with the inequality `max(type_term) < STACK_BAND` and `max(stack_term) < FLOOR_BAND` written beside them and PINNED BY A TEST** — otherwise it is three schemes again the first time someone raises a type constant. Proposed next step unchanged: instrument the drag with a bounded event counter to find the consumer, rather than choosing constants to avoid a symptom. **The SERIALIZATION half stays blocked** on the schema ruling (v5 has no stacking-index field and all four objects set `additionalProperties: false`), and returns to Patrick as its own decision. **Both halves go to the post-P4.5 queue, second after row 47.** | ruff + pytest |
| | **▲ PHASE 4 COMPLETE — 2026‑08‑06.** P4.1, P4.1b, P4.2, P4.3, P4.4 and P4.5 all merged and ticked (PRs #2, #3, #4, #5, #6, #10). Rooms are movable units, groups move the real items, the split-on-write shim is gone, and `main` is green on py3.10, py3.13, the deep-invariants job and ruff. **Carried out of the phase, not silently dropped:** defect 11's runtime z-order collapse (see the P4.5 row) and register rows 47, 48, 49. | |
| ☐ | **P5.1** Site levels, categories, area accounting | ruff + pytest |
| ☐ | **P5.2** Landscape wall types + gates | ruff + pytest |
| ☐ | **P5.3** Site schedule fields + reports | ruff + pytest |
| ☐ | **P6.1** `QUndoStack` + commands | ruff + pytest |
| ☐ | **P6.2** Retire snapshot undo | ruff + pytest |
| ☐ | **P6.3** Scene index + viewport update final pass | ratios recorded |

---

## Autonomy tiers

**Assigned by Patrick in [`ROADMAP.md`](ROADMAP.md), 2026‑08‑07, and recorded here so the
classification is on disk rather than in a conversation.** `ROADMAP.md` is the source; where
this table and that document disagree, read it — and where either disagrees with this plan,
the register or the snapshot, **those are authoritative and both are wrong.**

**Code does not self-classify.** The tier decides what happens at the end of the work, not how
carefully it is done.

| tier | criteria | what happens at the end |
|---|---|---|
| **GREEN** | a ruling exists on disk · **no new semantics, and nothing the user must learn** (amended 2026‑08‑07) · no format or schema change · acceptance is stated | PR, **merge on green CI**, report at the end of the batch |
| **AMBER** | a ruling exists, but the task changes what the user sees or what an operation produces | PR, then **stop** — Patrick's manual check is the merge condition |
| **RED** | a ruling is missing | **do not start** |

| tier | items |
|---|---|
| **GREEN** | **G1** D43 negative-assertion count · **G3** D27 Windows CI leg · **G2** D48 scene identity check (report-only) · **G4** D42 drag-side self-intersection report. Order: G1, G3, G2, G4 |
| **AMBER** | **A1** D47 fragment→extract · **A2** D11 runtime z collapse · **A3** D11 serialization half (unblocked by R‑B) · **A4** D49 deep checks at document boundaries · **A5** D41 simple-ring invariant (ruled at R‑A; read-back required) · **A6** grid snap |
| **RED** | grid snap's three sub-rulings · Phase 5 yard catalog and settable wall types · Phase 6 command undo · Phase 7 (7.1/7.2 `level.kind`, 7.3 roof) · D44 (an accepted limit — nothing to do) · D45, D46 (carried) |

**Two rulings issued with the tiers**, both recorded in full in `ROADMAP.md` §2:

* **R‑A — D41 gets a NEW invariant, not a widening of I5b.** `_seg_cross` tests *proper
  crossing* and must keep not firing on the collinear edges two rooms legitimately share. A
  ring that visits a vertex twice is a **degeneracy, not a crossing**, so it gets its own
  invariant: *a room outline is a simple ring; no vertex appears in it twice.* `symmetricP1`
  contains an instance, so the spur is fixed and the freeze re-cut **with its justification in
  the same commit**; `planc1.v5` keeps its instances, which are the point of that fixture.
* **R‑B — an ADDITIVE OPTIONAL field or enum value does not bump the document version.**
  `version: 5` describes the *model* — rooms own outlines, vertices are identity, walls are
  bindings — and an optional stacking index does not change it. What an addition breaks is an
  **old validator**, not an old reader, and the only validator ships with the app. The schema
  gains a revision marker, every addition is dated and reasoned, `additionalProperties: false`
  stays, and a **breaking** change (removing a field, changing a type, changing what a value
  means) bumps to **v6** with its own migration. This unblocks D11's serialization half.

**A GREEN item becomes RED mid-flight** if a measurement changes its scope, a finding
contradicts something decided, a ruling is needed that `ROADMAP.md` does not contain, or a
watch trips. Stopping is the mechanism working.

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
| ~~**P3.5**~~ **CLOSED at P3.7 (2)** | ~~**An open side of a room is not drawn.**~~ **The cue is back, drawn from the outline: `RoomItem._paint_open_edges` strokes every `open_edge_segments()` with the same colour, dash and lod-scaled width the `OpenWall` item used — so this closes as *the same cue from one representation*, which is what the "Restored at" column asked for, and not as a different cue. RECEIPT, and it is a pixel test rather than a structural one because every structural assertion in `test_open_walls.py` stayed green throughout the regression: `test_an_open_side_is_drawn_dashed`. Polarity measured first (wall body 150, dash ~124, gaps and bare background 255), and it FAILS against a tree without the paint addition with the row's own words — `[255, 255, … 255]`, the open side rendering as nothing.** Original text: **An open side of a room is not drawn.** Detach a wall from its room and pull a corner away and the side opens — the room keeps its shape and area, and the document says `wall: null` exactly as before — but the vacated stretch renders as nothing rather than as a dashed line. The producer of the dashed `OpenWall` placeholder was `refresh_rooms` → `reloop_open_room` → `bind_room_walls`, all deleted here; the fact itself moved onto the outline (`RoomItem.open_edges()`), which is where the document had always kept it. | None needed for correctness — nothing is lost but the on-screen cue. The room's area, outline and saved file are unaffected. | **P3.7** (`OpenWall` is deleted and a `wall: null` edge renders dashed from the outline, which is the same cue drawn from the one representation instead of a second one) |
| **P2.3** | **After the first undo, a wall that crosses a junction comes back split** — and if it borders NO room, body-dragging it moves only that segment. Measured at P3.3: one 480″ wall with a mid-span T returns as two 240″ walls. **Narrower than first recorded**: `_collinear_run()` (`walls.py:888`) gathers the whole room *side*, so for a wall on a room perimeter — the common case, and the one a user would notice — both halves still move as one. Verified with a room: `_collinear_run()` gathers 2 of 2. The row applies only to room-less walls, where `self.rooms` is empty and the run short-circuits to `[self]`. | Bind the wall to a room, or drag the halves together. Nothing is lost either way: the **document is unchanged**, since `design_from_scene` planarises to the same canonical form. | ~~P3.4~~ → **retargeted at P3.4 (iv), and the predicted fix was wrong on its own terms.** Re-checked by hand: the 480″ wall still returns as two 240″ segments, `merge_all` does **not** re-merge them, and the body-drag still moves one segment. It must not — the mid-span T is a **degree-3 vertex**, load-bearing for the planar subdivision, and merging through it would destroy planarity. `merge_collinear` refuses for exactly the right reason, so this row was never merge's to close. The fix belongs in the **drag's run-gathering**: `_collinear_run()` (`walls.py`) short-circuits to `[self]` when the wall borders no room, which is precisely the case the row describes. Gathering the run over **vertex adjacency** instead would carry both segments. Unassigned rather than invented — it is one small change, and the honest place is whichever task next touches the drag (**P4.2** extract/join is the nearest). **SECOND PREDICTED FIX REFUTED AT P4.2** — the vertex-adjacency gather was implemented (per ruling e) and turned P3.3's anti-shear pins red: `_tee_scene` (a wall, its collinear continuation, a stem at the shared corner) is topologically **identical** to the undo-split segments, and P3.3's settled "split first, shear never" rule — the continuation keeps its vertex and stays exactly where it is — occupies that topology with three pinned tests. The representation cannot distinguish "one wall stored as two segments" from "two walls drawn end-to-end", so one rule must own the topology, and the settled one does. Reverted; the row's wanted behaviour is pinned by the xfail `test_wall_move.py::test_a_roomless_split_wall_body_drags_as_one_run`. **The row now needs a RULING (carry vs stay), not a third predicted fix** — both of its predictions have now failed on their own terms, each caught by a settled rule doing its job. **RULED at P4.3 (2026‑08‑03): STAY — the row CLOSES as superseded-by-ruling.** The settled rule keeps the topology; the drag moves the grabbed segment only, permanently. The xfail pin is **replaced by two hard passes** per the ruling's amendment: `test_a_roomless_body_drag_moves_the_grabbed_segment_only` (the stay contract, promoted from implied to asserted — the topology's one owner) and `test_the_roomless_seam_heals_and_then_drags_as_one` (with `auto_coalesce` on, the room-less degree-2 collinear seam an undo leaves dissolves at the next merge pass and the merged wall body-drags as one — **the restoration this row actually wanted, arriving through the document instead of the gesture**). The workaround column survives only for the shuffle / `auto_coalesce`-off world, where staying split is honest. |

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

> **Branch.** `git switch -c v5-topology`. This is the only phase where `main` should not track HEAD.
>
> ## ✅ **MERGED — `03f3868`, 2026‑07‑31.** PR #1, as a **merge commit, not a squash**, so the sub-commit history keeps this phase's rollback points and the receipts in its commit messages. CI green on `main` at the merge commit: ruff, py3.10, py3.13, and the deep-invariant job. All six merge conditions met; the checklist below is closed. **`main` tracks HEAD again — Phase 4 opens against `main`.**

### What Phase 3 carries into Phase 4 — the open list, in one place

Written at the merge so Phase 4 starts from a list rather than a search. Each is registered in `docs/CODE_REVIEW_v2.md`; nothing here blocked the merge.

| | open item | argued phase |
|---|---|---|
| **23** | A group move strands a room it does not fully own. Confirmed by a real user at Gate 3 and reproduced exactly: a rubber band takes only items **wholly inside**, so a band that clips a room's wall set strands it — **100% coverage strands zero; every band short of it strands what it clipped**. The decision is semantic (deform-to-follow, or stay put?), which is what "what a group IS" means. | **P4.5** |
| **25** | A gesture can create a door-straddles-junction state the document can only report. **First real-user confirmation at Gate 3** (a wall drawn onto a doorway; the join correctly declines and the user gets the generic torn-network message). The mechanism works; the gesture-time message is missing. | **P4.1** *(my P4.3 dissent is on the record and Gate 3 weakened it)* |
| **30** | A body drag strands every room that holds the moved corner but owns no wall in the dragged run — its walls partly follow, its region does not. Measured with a real drag at a 4-way corner. | **P4.2** |
| **34** | A document gap in the (0.6″, 9.0″) band is reported by nothing and closed by nothing, and the command that looks like a repair only silences the report. **Must be a review, not an auto-repair** — a deliberate 6″ reveal is legitimate and nothing may silently close it. | **P4.2** *(alt P4.3)* |
| **13** (drag half) | Whether a gesture tolerance may set a geometric **result** — the endpoint catch radius and orthogonal stick are zoom-relative. Measured at P3.5; needs a ruling, not another number. | **P4.2** |
| — | **The P3.1 split-on-write shim**: `GroupItem.bake`'s residue is P4.5's by ruling, and the shim stays until that counter is owned entirely by P4.5's rebuild. | **P4.5** |
| — | **Two identity-churn assignment sites** (`_translate_shape`'s pair): they translate a whole selection by one delta, so the geometry stays self-consistent while identity is minted fresh. Lower stakes than the four defect-30 faces. | **P4.5** |

**They share one thesis, and P4.2 inherits it: every one is an operation that knows about ROOMS where it should know about CORNERS.** Phase 3 moved the geometry onto vertices; these are the call sites that still ask a room what they should be asking a corner.

### The Phase-3 merge checklist — ruled 2026‑07‑30

~~*Merge when P3.8 records its numbers.*~~ That one line was the whole condition, and it is not enough: it would have merged a branch whose gate can go red for reasons unrelated to the code, onto a `main` whose CI runs neither of the invariants that caught the only real corruption this project has seen. **PR #1 merges when ALL of the following hold.**

1. **P3.8's numbers are recorded** — a full P0.3 re-run against **both** the P0.3 baseline and the P3.5-exit numbers, ratios in the Progress log; and **grouping 20 rooms creates 0 new walls, asserted** (not observed).
2. **All four exit-survey rows are answered** — by measurement, or explicitly dispositioned to a named task. **No blank rows**, the corpse-table standard applied to the survey: the split-on-write assignment-site census, the stranding question, defect 13's drag half, and the P2.3 collinear-run row.
3. **The flap-class decision is made and applied to the CLASS** (all four members). **Constraint from member four, not negotiable: no wall-clock ratio may remain a gate-reddening hard pass on a shared machine.** Wider thresholds, best-of-N, or a non-gating recorded-benchmark lane with one very loose catastrophic guard — P3.8 decides from its own fresh numbers, but it decides for the class. *Why this is a merge condition and not housekeeping: as of today a red gate has two indistinguishable causes — a regression, or machine load — separable only by reading which test failed, which is the manual step the gate exists to replace.*
4. **Defect 27, first half: a DEEP CI job** (`FP_VERIFY_DESIGN=deep`, ubuntu) **is added and green before merge.** Defect 26's fix removed the crash that made this impossible. I11 and I14 caught `planc1`'s real corruption, and they do not land on `main` guarded by nothing but a human running a local gate. **The windows-latest half stays filed in defect 27 as its own task — desirable, not merge-blocking.**
5. ~~**Gate 3 passed by Patrick, findings dispositioned**~~ — **DONE, 2026‑07‑31.** Sections A and B re-run clean against the branch head. **Five findings, all dispositioned:** **31** the group-box stretch (fixed pre-merge, two mechanisms at defect 14's site) · **32** the warning's false advice (fixed pre-merge; a v5 plan is now silent on open) · **33** rooms left behind by a clipped band (**closed as a duplicate of 23** — measured: 100% band coverage strands zero, every band short of it strands what it clipped) · **34** a document gap in the (0.6″, 9.0″) band that nothing reports and nothing closes (**registered, carried to P4.2**; it wants a review, not an auto-repair) · and a **first real-user confirmation of defect 25's gesture arm** — a wall drawn onto a doorway leaves the end unwelded and the user sees only the generic torn-network message. Record in `docs/SANITY_CHECK.md`.
6. **CI green on the branch head**, and **merge commit, not squash.** The sub-commit history carries the rollback points and the receipts live in the commit messages; flattening it would delete the audit trail this phase spent so much effort making true.

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
~~**Acceptance.** `test_open_walls.py` rewritten against null edges; the class is gone.~~

**AMENDED ACCEPTANCE, settled 2026‑07‑30 before any code** *(the P3.6 lesson applied to a three-line task: a spec whose acceptance can pass vacuously is the same class of problem as a task line whose three numbers were all wrong — fix the spec first, then the code).*

**Two rulings from the read-back, and they are what the amendment implements.**

**R1 — RENDER-ONLY. No item, no interaction.** An open edge is *the absence of a wall*; interacting with an absence means either drawing a wall there (the draw tool already owns that) or moving the room (the room owns that). Selection of a nothing has no meaning to implement. `test_open_wall_is_editable`, deleted at P3.5 because "it asserted drag controls on a placeholder nothing constructs", **stays a precedent rather than a casualty**: no drag controls on something nothing constructs. The cue is drawn in `RoomItem.paint` from `RoomItem.open_edges()` — the fact and the cue from **one** representation, which is what the P3.5 Known-regression row promised. **Match the old `OpenWall` dash visually** so the row closes as *"same cue, one representation"* and not as *"different cue"*. If a later phase needs open-edge hit-testing, **that phase specs it** (P4.2 extract/join is the plausible candidate); a fence comment at the paint site naming P4.2 is welcome, not mandatory.

**R2 — THE PIXEL ASSERTION IS REQUIRED, on P3.4's junction-contract template:** render, **measure the polarity first**, then assert with a measured threshold. A dashed line is the canonical structurally-green / visually-absent cue, and the old acceptance would have passed with nothing drawn at all.

**The four acceptance items:**

**(a) `test_open_walls.py` against null edges — VERIFY, DO NOT RE-DO.** Already landed at P3.5 and logged there as `[DIVERGENCE — the whole file]`: `_open_count` sums `r.open_edges()` and the file's docstring states the old→new mechanism. What remains of it here is only its four `not w.is_open` helper filters, which fall with the flag in (c).

**(b) Pixel assertion, polarity measured**, on a room with an open edge: the dashed cue is drawn along the vacated stretch, and the closed sides are unaffected. Both halves in one test — positive and negative — so the positive assertion cannot go vacuous, exactly as P3.4's junction test does.

**(c) The class is gone**, by the standing rule (*a line dies when its last caller dies*). **Census taken on disk 2026‑07‑30, and it diverges from the estimate in two ways — reported rather than forced:**

- **THERE IS NO LIVE PRODUCER, and there has not been since P3.5.** `grep "OpenWall("` over the tree returns **zero** constructor calls. The **P2.3 producer branch in `apply`** named in the estimate is already deleted — `bridge.py:959` is now a *comment* recording that it went at P3.5. **The Progress-log line at P2.3 ("apply now builds an `OpenWall` per `wall: null` outline edge; P3.7 retires the branch") is stale history and is annotated as such**, not acted on. So the class is dead code today: deleting it removes a definition, not a behaviour.
- **`is_open` IS THE REAL SWEEP, and it is ~7× the estimate.** The estimate said "comments/docstrings ×7". Measured: the flag is read at **23 sites in `floorplanner/`, 19 in `tests/`, and 2 in `docs/make_gallery.py` — 44 readers across 17 files** — plus the definition (`walls.py:902`) and the override (`:1685`). **Every one of them is permanently `False`** once nothing constructs an `OpenWall`, and `walls.py:1631` already says so in a comment. The flag dies with its producer and the readers go with it: *a permanently-false flag is worse than no flag, because it tells every future reader that open walls exist as items.* Sub-committed separately from the rendering, so the mechanical sweep is its own rollback point.

**(d) The P3.5 Known-regression row closes**, citing the pixel test (b) as its receipt — not the deletion, and not "the code now draws something". The row's own wording is the bar: *the same cue drawn from the one representation instead of a second one.*

**Sub-commits:** (1) this amended acceptance; (2) rendering + pixel test; (3) the deletion sweep. **Full-mode `tools/gate.py` trailers throughout.**

### P3.8 — Perf verification
Re-run P0.3 and compare against the P0.6 numbers.
**Acceptance.** Ratios recorded in the log. Grouping 20 rooms creates **0** new walls — assert it.

**Also: the SPLIT-ON-WRITE EXIT SURVEY** *(added 2026‑07‑28)*. Assigning `p1`/`p2` mints a fresh vertex for that end, and three separate defects have now come from something downstream being left on the old one: the P3.1 shim's own telemetry, **defect 22** (bake orphaning room outlines) and **the anchor orphaning** found at P3.6(1) (12 of 41 openings mirrored on loading `planc1`). Three members is a pattern, not a coincidence. **Census at P3.6: 9 direct coordinate-assignment sites remain** — `mainwindow.py:568,569` (align to grid), `:578,579` (`_translate_shape`), `view.py:402` (the rubber-band wall being drawn), `walls.py:1511,1513` (the endpoint drag), `walls.py:1549,1551` (the `rigid` and `tee` branches, both P4.5's / P3.3's by ruling). P3.8 re-runs this grep, records the count, and for each survivor states what carries the things attached to that end — or names the task that will.

**And: the OPEN DRAG QUESTIONS.** *(table added 2026‑07‑30.)* Two questions about what a mouse gesture does have now been left explicitly unanswered rather than guessed, each because the measurement that would settle it was out of its task's scope. They are surveyed together here because they are the same organ — the endpoint drag — and because an unassigned question with no home is one nobody re-reads. **Neither is scoped to P3.8 by this table; P3.8 records the answer or names the task that will.** *(Structural note: this table is new. The split-on-write survey above is prose, and defect 13's drag half lives in the defect register's row 13 as "unassigned (drag)" — it is restated here so the two sit beside each other, not moved.)*

| question | why it is open | how to answer it |
|---|---|---|
| **Defect 13's drag half — does a drag's RESULT depend on view zoom?** *(**Status authoritative in register row 13; this row is the exit checkpoint.** One direction only — the register keeps the history, the survey blocks the exit. This row is a restatement, so it is the one that can drift.)* | Measured at P3.5 **before** anything was deleted: the same scene-space gesture gave **0 open sides at 0.25× and 1 at 0.5×–4×**, leaving the wall's far end at y=120 versus y=60. The detection half closed structurally; the zoom terms that remain are the drag's own — `mousePressEvent`'s `20.0 / _view_scale()` endpoint catch radius and `_project_to_orthogonal`'s `16.0 / view_scale` stick. Retargeted and left **unassigned** rather than invented a home for. | Drive the same gesture at pinned zooms and compare the resulting geometry, as P3.5 did — then decide whether a gesture tolerance *should* be zoom-relative (it probably should) and whether the RESULT may be. **P4.2** is the nearest task that touches the drag. |
| ~~**Does a real endpoint drag re-point every outline holder, or strand a third room?**~~ **ANSWERED at P3.8 (3): IT STRANDS — registered as defect 30.** A real viewport-driven body drag at `symmetricP1`'s 4-way corner (582, 714) moved it **(0, −24)**; Dining and Kitchen followed; **Foyer and Great Room were left behind**, each with one wall end at the new corner and one at the old while its outline stayed at the old. Step 4 gathers from the **run's rooms**, not the corner's **holders**. The ENDPOINT drag is a separate answer: it assigns `p1`/`p2`, which is split-on-write by P3.1's ruling and deliberately leaves the outline behind — that is the open-side feature, not a defect. Pinned `xfail` by `test_a_dragged_corner_carries_every_room_that_holds_it`. | The 38 synthetic drags at the defect-28 resolution **moved the corner in none of them**, so the app is neither cleared nor accused — that run's "0 stranded" is vacuous and was discarded rather than quoted as an acquittal. The question matters because the *test* that stranded a third room was hand-rolling what the drag does, and `mousePressEvent` step 4 gathers outline edges from the **run's rooms**, which is not obviously the same set as **every room holding the corner**. | **Answer with a real drag** — driven far enough to actually move the corner, asserted as having moved — **on a corner held by 3+ rooms**, then check every holder followed. |

---

# Phase 4 — Rooms as durable movable units

### Phase‑4 branch strategy — ruled 2026‑07‑31 at the P4.1 read-back

**Per-task branches**, each PR'd into `main` as a **merge commit** (never
squash), full-mode `tools/gate.py` trailers on every sub-commit. The facts that
changed since Phase 3's single-branch ruling: `main` now runs the DEEP
invariant job in CI itself (defect 27's closure), and Phase 4's tasks are
separable, releasable deliverables — each leaves `main` shippable, so there is
no intermediate state a long branch needs to hide.

**Two designated mini-gates:** P4.2 and P4.5 additionally require a Patrick
manual check before their PRs merge — they are the two tasks that change what
gestures MEAN (extract/join, and the group-semantics ruling). P4.1, P4.1b,
P4.3 and P4.4 merge on green CI plus reviewer acceptance.

### P4.1 — Delete-wall keeps the room
*(branch `p4.1-delete-wall`; scope verified and amended at the read-back, 2026‑07‑31)*

Deleting a wall genuinely deletes it; the room survives because its stored
outline (P3.2/P3.5) holds the corners — the vacated edge becomes open
(`wall: null`), drawn dashed by the room. No fracture, no trim-and-rebind.
**Defect 17 closes here**, with a coda measured at the read-back: post-P3.7 the
fracture "no-op" is not even silent any more — fracture deletes the original
wall and mints a replacement segment, the outline still names the dead wall,
and `open_edges()` therefore counts the edge open, so the room paints a dashed
open cue over an edge a wall actually covers (measured: 4 bound walls + 1 open
edge, against P0.4-era 4 + 0). Defect 17's silence aged into misinformation —
the final argument for deletion over repair.

**Census (fresh at the read-back, 2026‑07‑31):** `fracture_delete_wall`
(walls.py:653–709, 57 lines; live callers `delete_selected` at
mainwindow.py:490 and the wall context menu at walls.py:1666) and
`_merge_intervals` (walls.py:642–650, 9 lines; sole caller inside fracture)
die — **66 lines, two call sites**. `_perimeter_span` does **not** die here —
see the register's carried census note (authoritative copy).

**Tests that change, declared in advance and approved:** characterization 2b's
xfail marker comes off (the acceptance itself; its comment's "0 open edges"
figure is era-stale — today the no-op measures 4 built + 1 open);
`test_walls.py::test_fracture_delete_free_wall_removes_whole` preserves its
behaviour through the new delete entry point; `test_walls.py::
test_fracture_delete_keeps_room_edge_drops_overhang` and `test_room_walls.py::
test_fracture_delete_shared_wall_keeps_both_rooms` are **intentionally
replaced** to encode the measured new truth: the whole wall goes and each
bordering room keeps its area with one open edge (party-wall case measured at
the read-back: both rooms 100.0 sf, 3 bound + 1 open each).

**Acceptance.** P0.4 test 2 flips to pass.

### P4.1b — Defect 25's gesture-time message
*(ruled 2026‑07‑31: standalone and immediate — branches the moment P4.1's PR merges)*

The register's move trigger fired on both arms at once (P4.1 opened; Gate 3
delivered the first user report), and folding into P4.1 was rejected on the
fold-proposer's own honesty: the fold rested on next-to-touch plus the fired
trigger, not on mechanism. Scope, **message only**: draw-release and end-drag
say at gesture time what R2c's walk already detects and files — a message
naming *this* edit and *the doorway*, through the defect-6 edit-path
vocabulary, replacing the generic torn-network breadcrumb. Explicitly NOT in
scope: any change to what the gesture *does* — decline/split/weld policy stays
P4.3's with the `auto_*` flags (the dissent's surviving kernel).
**Acceptance.** Drawing a wall whose end lands inside a doorway produces the
specific message at release (and the same for an end-drag); the document
walk's report path stays unchanged as the load-path safety net.

### P4.2 — Extract / join
Per §4 of `DESIGN_MODEL_v5.md`. Extract privatizes walls and vertices, sets `state: floating`, `extracted_from`. Join welds, merges coincident walls, splits, rebinds, sets `state: placed`, and coalesces only the touched degree-2 vertices.
**Inherits a QUESTION from P4.1's census, not a claim** *(authoritative copy: the register's carried census note, 2026‑07‑31)*: whether `_perimeter_span` dies here — it does only if `_copy_spec` (its other surviving caller, owned by no phase) is also reshaped here. P4.2's read-back must answer it. *(ANSWERED at the P4.2 read-back: no — `_copy_spec` is §4's "Duplicate a room", which is P4.4's; re-argued to P4.4 as a contingency. See the register's note, which stays authoritative.)*
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
**Acceptance — CORRECTED 2026‑08‑04 against the merged tree, and the correction is the point.** The original line read *"P0.4 tests 3, 4 and 6 flip to pass"* and named three `test_groups.py` tests by LINE. Measured at `adaa519`: **only ONE flip is available** — test 3 (`test_characterization.py::test_group_survives_roundtrip`) is the sole surviving xfail of the three. Test 4 (`test_group_move_undo_restores`) was promoted to a hard pass at **P0.5** (its own comment says so) and test 6 (`test_group_ungroup_reaches_fixed_point`) passes today. The line numbers had also drifted — **the fourth instance of that class**, so every test below is named, never numbered.

**Acceptance, as it now stands:**
1. `test_characterization.py::test_group_survives_roundtrip` flips xfail → pass (defect 3).
2. `test_groups.py::test_a_clipped_band_leaves_every_room_coherent` passes — and the log must say it passed **as a consequence of the mechanism, not as a fix** (§2a's ruling).
3. `test_groups.py::test_grouping_rooms_without_their_walls_still_copies_them` is **rewritten into its opposite** (grouping a room alone creates nothing and moves the originals) — a declared assertion change.
4. The three tests encoding duplicate-on-group semantics are *intentionally* replaced, named not numbered: `test_grouping_a_room_duplicates_its_walls`, `test_grouping_room_with_its_walls_makes_no_coincident_copies`, `test_group_move_room_only_does_not_orphan_walls`.
5. `test_grouping_twenty_rooms_with_their_walls_creates_no_walls` is renamed and widened to **creates no OBJECTS at all** (walls *and* openings).

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

**Moved to [`progress/`](progress/)** on 2026-08-06, split by phase and left
verbatim -- 4,351 lines across seven files, indexed at
[`progress/README.md`](progress/README.md). It was 83% of this document and it
is the record, not the plan: what happened, in the order it happened, written
at the time.
