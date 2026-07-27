# Code review v2 — measured against the v5 target

**Date:** 2026‑07‑26 · **Supersedes** `CODE_REVIEW.md` (2026‑06‑18)
**Baseline:** `floorplanner/` 8,646 lines / 13 modules · `tests/` **287 tests** / 24 files · CI = ruff + pytest on py3.10 & 3.13, `QT_QPA_PLATFORM=offscreen`

The first review asked *"what is wrong here?"*. This one asks a sharper question: **given that `docs/design-schema.v5.json` is now the agreed target, which code survives, which gets reworked, and which gets deleted?** That reframing changes several verdicts — some code that reads badly is about to be deleted wholesale, and some code that reads fine is load-bearing in a way that makes it risky to touch.

Baseline numbers, measured not estimated:

| | count |
|---|---|
| Full-scene scan sites (`…​.items()`) | **66** |
| `isinstance(…, WallItem)` filters | 54 |
| `isinstance(…, RoomItem)` filters | 20 |
| `setZValue` call sites (4 competing schemes) | 14 |
| `except ValueError` (the silent opening-drop family) | 13 |
| `group() is None` guards | 8 |
| Functions over 80 lines | 6 (5 in `mainwindow.py`) |
| **Lines named for deletion in Phase 3** | **882** |

---

## 1. Module verdicts against the v5 target

| Module | Lines | Verdict | Note |
|---|---|---|---|
| `app.py` | 28 | **KEEP** | Correct as-is. |
| `geometry.py` | 186 | **KEEP** | Pure, stateless, testable. Move `bring_to_front`/`send_to_back` out — they aren't geometry and they full-scan the scene. |
| `config.py` | 251 | **KEEP, extend** | Add `join_tol_in` beside `vertex_weld_in`; the `_FLOOR_STATE` runtime cache becomes level state. |
| `catalog.py` | 248 | **KEEP** | Independent of the model. Stop `apply_furnishing_prices` writing `assets/…/manifest.json` from a UI action. |
| `model.py` | 235 | **REPLACE** | Becomes `floorplanner/design/` — real dataclasses over the v5 schema. Today it is a serialization DTO whose `Wall.rooms` is write‑only. |
| `dialogs.py` | 579 | **REWORK (light)** | Move the inventory aggregation helpers to `reports.py`; they query the scene and none filter by floor. Add site-room schedule fields in Phase 5. |
| `view.py` | 618 | **REWORK** | Wheel-zoom coalescing is good engineering — keep it and copy the pattern to drags. Extract the 79‑line tool dispatch. **Fix: `select_in_rect` mutates the plan** (`view.py:445` synthesizes walls during a selection gesture). |
| `macro.py` | 901 | **KEEP, retarget** | Runner is sound. Its tokens address items positionally; Phase 3 gives it stable ids to use instead. Recorder's app-wide event filter with `except Exception: pass` (`:751`) stays fragile — out of scope. |
| `items.py` | 1,033 | **REWORK** | `FurnishingItem`/`StairItem` are fine. `GroupItem` (23 methods, 325 lines) gets simpler once rooms are the movable unit and groups stop copying walls. `ReferenceImageItem` untouched. |
| `walls.py` | 1,311 | **GUTTED** | ~330 lines deleted (coalesce ×4, weld, join_endpoints, fracture, the two indices, junction pass, `OpenWall`). What remains: `WallItem` rendering + a much smaller drag handler reading vertex ids. |
| `rooms.py` | 1,280 | **GUTTED** | ~550 lines deleted (`_RoomGrid`, `_WallGraph`, detection, memoization, binding, the two "does this room own these walls" predicates, privatize, duplicate). `RoomItem` becomes a view over `Design.rooms[i]`. |
| `mainwindow.py` | 1,956 | **SPLIT** | 92 methods / 1,924 lines in one class. IO, CSV import, image import, floors, room-boolean, alignment are each independent and testable. Split during Phase 2, not before. |

**Net:** Phase 3 removes 882 lines of named functions plus the call sites and special cases they force elsewhere, and replaces them with roughly 400 lines of topology operations (`split_edge`, `merge_collinear`, `trace_face`, `move_vertices`, `bind`/`unbind`) that need no `QApplication` to test.

---

## 2. Five structural findings

**F1 — There is no registry of canvas items.** 66 full-scene scans answer every "which items are there" question, each re-deciding whether to filter by floor. Ten of them don't, including `_WallIndex` — the *shared rebuild index* — and `weld_all`, both of which `CLAUDE.md:11` claims are floor-scoped. In v5 the `Design` document is the registry and the filter is one decision.

**F2 — Geometry is stored twice and reconciled continuously.** Each corner exists as two coordinates on two walls, and the app spends `weld_all`, `join_endpoints`, `nearest_wall_endpoint`, `coincident_walls` and `_WallGraph.node_id` rediscovering they are the same point — with **five different tolerances** (0.6, 0.75, 1.0, 1.5, 0.02). v5 makes a corner one vertex.

**F3 — Room shape is derived, never stored.** A 112,000‑cell flood-fill plus an O(W²) planar graph reconstruct on every edit what v5 stores directly. This is also the root of the data corruption: with no stored outline, a 1.5″ gap merges two rooms silently.

**F4 — `serialize()` is not a faithful snapshot.** Groups are absent from `project_from_scene` entirely, so Ctrl+G produces no undo step and any unrelated undo dissolves every group. `is_open` walls are skipped, which is why archway edges are lost on save. Z-order is deliberately excluded, so "Bring to front" is silently reverted by the next undo of anything else. Undo and the dirty flag both rest on this function.

**F5 — The pipeline creates unwelded gaps and never closes them.** The editor welds at `JOIN_TOL = 9.0″` **only at draw release** (`view.py:489`, the wall just drawn) and on the explicit Edit ▸ Coalesce all walls now command (`mainwindow.py:821`), then writes the *unwelded* coordinates. **Load does not weld at all**: `apply_project_to_scene` (`mainwindow.py:1298`) runs `coalesce_all` + `rebuild_all_walls`, and no `weld_all`. Worse, coalesce is itself a gap *source* — `_coalesce_wall_impl` (`walls.py:200‑201`) re-snaps the survivor's `p1`/`p2` onto the on-centre grid (`wall_snap`, default 6″) independently of whatever neighbour that end was welded to, so it can pull a previously-welded end up to half a grid step off its partner. Gaps are therefore **created and accumulated by the app's own pipeline**, and they survive every save/open round-trip. **Every plan the app has ever saved carries this.** In `planc1.json` it is 31 wall ends, and it is what produced a 591 sf master bath overlapping two other rooms.

> **Corrected 2026‑07‑26 (during P1.4).** This finding previously read "Welded geometry is never persisted… the editor welds on every draw release **and on load**." The "on load" half is wrong — there is no `weld_all` on the load path, verified at `mainwindow.py:1298`. The distinction is not academic. Under the old wording, P2.1's weld-on-load merely *persists something the app already did*; under the corrected mechanism it is **new, deliberate repair behaviour the app has never applied to the user's file before**. That strengthens the case for §7a's conversion report and dirty flag rather than weakening it: the user must be told precisely because this is new. It also means a legacy file loaded into the scene is *unwelded in the scene*, which is why `design_from_scene` (P1.4) reports a non-zero weld count on `planc1.json` instead of zero.

---

## 3. Defect register

Ranked by blast radius; each mapped to the phase that closes it.

| # | Defect | Site | Phase |
|---|---|---|---|
| 1 | Welded coordinates never saved → silent room merges | `mainwindow.py` save path | **P2.1** |
| 2 | `refresh_rooms_cmd` deletes every room on non-active floors | `mainwindow.py:589‑593` | **P0.5** |
| 3 | Groups not serialized; grouping isn't undoable; undo dissolves groups | `mainwindow.py:1042‑1083` | **P4.5** — *partly closed early: defect 4's fix made group→move→undo restore the plan correctly. The remaining half (the group itself surviving save/load and redo) is still open and is held by characterization test 3.* |
| 4 | Undo snapshots alias the live `properties` dict | `mainwindow.py:1074` + `rooms.py:439` | **P0.5** |
| 5 | `RoomItem` has no `itemChange` → dangling `WallItem.rooms` at 5 sites | `rooms.py`, `mainwindow.py:472,592,677,1234,1287` | **P0.5** |
| 6 | 13 `except ValueError: continue` silently delete an opening, incl. on load | `walls.py:209,342,1079`; `mainwindow.py:1304` … | **P3.6** |
| 7 | Four `p1`/`p2` mutations don't re-base `op.s` | `walls.py:885,954,199`; `mainwindow.py:531` | **P3.6** |
| 8 | `room_boolean` deletes neighbours' and other floors' walls, forces `"interior"` | `mainwindow.py:674‑698` | **P3.5** |
| 9 | Coalesce absorbs openings with no dedup → stacked doors (3 found in `planc1`) | `walls.py:205‑212` | **P3.4** |
| 10 | Rubber-band selection creates walls | `view.py:445` | **P0.5** |
| 11 | Four competing z-order systems, two of which run on every wall click | `walls.py:723‑727` + 14 sites | **P4.5** |
| 12 | 10 query paths ignore the floor filter | `walls.py:81,266`; `rooms.py:522,531` … | **P1.4** |
| 13 | Detection result depends on view zoom (from the deleted `test_zzprobe`) | `detach_wall_from_room` path | **P3.5** |
| 14 | `GroupItem.boundingRect` recomputes the oriented box 3× per paint | `items.py:509‑528` | **P0.6** |
| 15 | `_update_totals` full-scans on every `scene.changed` | `mainwindow.py:98,342` | **P0.6** |
| 17 | **Deleting a room's own perimeter wall is silently a no-op.** `fracture_delete_wall` keeps every stretch running along a room perimeter and rebinds it, so the user presses Delete and nothing happens — no wall removed, no message. Measured at P0.4: 4 walls in, 4 walls out, 0 open edges. | `walls.py:300‑354` | **P4.1** |
| 16 | **Room detection is silently clipped to `canvas_rect()`** — a plan larger than the canvas loses its edge rooms with no warning. Found by the P0.3 harness, not by any test. | `rooms.py:29` (`_RoomGrid`) | **P3.5** |
| 18 | ~~**`inner_faces` drops the largest INNER face as the "outer boundary" — discarding a real room.**~~ **FIXED at P1.3b.** The true outer boundary is opposite-wound and already excluded by the majority-sign filter, so `inner[1:]` threw away the biggest *room* (symmetricP1's Garage, 868.5 sf). Fix: keep the majority winding, drop *all* opposite-wound faces (one per component), never by size — in both `design/topology.py` and `tools/migrate_to_design_v5.py`. Retargeted P3.5 → **P1.3b** because P2.1's import traces outlines, so the bug would silently fall back to stored corners for the largest room of every imported plan. | `design/topology.py`, `tools/migrate_to_design_v5.py` (`inner_faces`) | **P1.3b (done)** |

---

## 4. Test-suite readiness

**287 tests across 24 files**, green in 7.6 s, with markers, a headless conftest, and almost no mocking. That is a real asset and the migration depends on it. Three problems have to be fixed *before* Phase 1, not after.

1. **Coupling to internals.** Roughly a third of tests reach into private API — `fp._coalesce_all_impl`, `view._zoom_accum`, `g._angle`, `room._detect_sig`, `dup._path`, `win._sel_order`, and the four private names re-exported from `FloorPlanner.py:155‑160` purely so tests can reach them. Phase 3 deletes several of these outright. **P0.2** must land first or the suite blocks the refactor.

2. **No performance guard.** `bench_rooms.py` is not collected by pytest (no `test_` prefix), tops out at 36 rooms, and asserts nothing. Every group test uses ≤5 members, where O(n²) is invisible. A 100× regression passes CI today. The baseline makes this concrete: the whole suite runs in **7.6 s**, and the slowest test is 0.75 s — not because the code is fast, but because **nothing in the suite is large**. **P0.3.**

3. **The behaviours we are about to change are untested.** Nothing asserts that opening positions survive a group move or rotation; nothing groups anything and then calls `undo()`; nothing serializes a grouped plan; nothing asserts grouped walls are exempt from coalescing (deleting that guard would pass CI). **P0.4** adds these as characterization tests, `xfail` where they currently fail, flipped to pass as each phase lands.

Also worth fixing in passing: `first_furnishing` is `catalog()[0]["id"]`, so reordering `manifest.json` silently changes the subject of every furnishing and group test; `test_ai_pricing.py` writes to a repo file; several tolerances are `abs=6`–`abs=8` inches, wide enough to hide a full grid-cell regression; and `test_groups.py:346` has a conditional assertion that passes in two structurally different worlds.

**CI is in good shape** and needs only one addition: schema + invariant validation of `examples/*.json` (**P0.7**), which turns the twelve-plus-two invariants into a build gate rather than a document.

---

## 5. What the target buys, quantified

| | today | after Phase 3 |
|---|---|---|
| Room area | 112,000‑cell flood fill + O(W²) graph, memoized, per edit | shoelace of the stored outline |
| "Which rooms does this wall bound?" | full scene scan + `QPainterPath` boolean per wall | `wall.left` / `wall.right` |
| Coalesce | O(walls²) to a fixed point, 4 full scans per pass | dissolve a degree-2 collinear vertex, O(1) |
| Grouping 20 rooms | **≥106 duplicate walls, ≥149 duplicate openings** | 0 new objects |
| Move a shared wall | not supported without tearing | 2 vertices; both rooms resize; **verified** |
| Delete a wall | room can be destroyed by `refresh_rooms` | edge becomes `wall: null`; room intact |
| Overlapping rooms | unrepresentable *as an error* — silently stored | rejected at load (I6, I11) |
| Duplicate walls | the failure mode | unrepresentable (I4) |

Two of those rows are measured on `planc1.json`, not projected.
