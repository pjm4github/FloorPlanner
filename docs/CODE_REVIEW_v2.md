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
| 8 | ~~`room_boolean` deletes neighbours' and other floors' walls, forces `"interior"`~~ **FIXED at P3.5.** Two faults, one cause: the op worked from a **re-traced boundary** rather than from what the rooms said they were made of. Its inputs' walls came from `bounding_walls()` — a proximity query over the whole scene with **no floor filter** — and the op removes everything it is handed, so a combine took the wall a third room shared with an input (breaking that room open) and any wall of any other floor whose body touched the band. And every result wall was built `"interior"`, so a combine downgraded 6″ exterior walls to 4½″ ones. Fix: inputs come from each room's **outline** (`room_walls`), a wall still bordering a non-input room is kept, and each result edge inherits type and floor from whichever input wall runs along it (exterior wins a tie). Two regression tests, both verified to fail against the old code before being kept. | `mainwindow.py` (`_selected_room_shapes`, `room_boolean`, `_source_edge`) | **P3.5 (done)** |
| 9 | Coalesce absorbs openings with no dedup → stacked doors (3 found in `planc1`) | `walls.py:205‑212` | **P3.4** |
| 10 | Rubber-band selection creates walls | `view.py:445` | **P0.5** |
| 11 | Four competing z-order systems, two of which run on every wall click | `walls.py:723‑727` + 14 sites | **P4.5** |
| 12 | 10 query paths ignore the floor filter | `walls.py:81,266`; `rooms.py:522,531` … | **P1.4** |
| 12a | ~~**`WallItem._attached` is one of defect 12's unfiltered paths, and P3.3 raises its stakes.**~~ **FIXED at P3.3.** A cross-floor coincident end wrongly dragged by the scan was a *transient* bug that ended with the drag; promoting that discovery into real vertex sharing would have made it permanent, because a vertex carries exactly one level — so unfiltered promotion would either violate **I2** outright or silently rewrite a wall's level. Fix: `w.floor != self.floor` at the **loop head** of the scan, so cross-level sharing is impossible by construction rather than filtered afterwards. Two tests pin it, both built on geometrically identical walls on two floors (what a leaking scan cannot tell apart): the other floor is neither shared with nor dragged, and is never even scanned. | `walls.py` (`mousePressEvent`, the `_attached` scan) | **P3.3 (done)** |
| 13 | **Detection result depends on view zoom** (from the deleted `test_zzprobe`). **HALF CLOSED at P3.5, half RETARGETED — and it was reproduced first**, per the task's rider 3 (*a defect closed by the disappearance of its measuring instrument is not closed*). Measured at zooms 0.25×–4× on the `detach_wall_from_room` path **before** deleting anything: **detection was already identical at every zoom** (same area, same corners, 5/5 runs) — it never read the view. **The drag was not**: the same scene-space gesture gave 0 open sides at 0.25× and 1 at 0.5×–4×, and left the wall's far end at y=120 versus y=60. The zoom terms are the drag's — `mousePressEvent`'s `20.0 / _view_scale()` endpoint catch radius and `_project_to_orthogonal`'s `16.0 / view_scale` stick. **Detection half:** closed and now structural — `topology.enclosing_face` is a question about the wall graph with no pixel, cell or canvas in the answer (`test_detection_does_not_depend_on_the_view`). **Drag half:** unassigned, exactly as the P2.3 regression row was left — it is a tolerance question about a mouse gesture, and the honest place is whichever task next touches the drag (**P4.2** extract/join is the nearest). | detection: `rooms.py` (deleted); drag: `walls.py` (`mousePressEvent`, `_project_to_orthogonal`) | **P3.5 (detection) · unassigned (drag)** |
| 14 | `GroupItem.boundingRect` recomputes the oriented box 3× per paint | `items.py:509‑528` | **P0.6** |
| 15 | `_update_totals` full-scans on every `scene.changed` | `mainwindow.py:98,342` | **P0.6** |
| 17 | **Deleting a room's own perimeter wall is silently a no-op.** `fracture_delete_wall` keeps every stretch running along a room perimeter and rebinds it, so the user presses Delete and nothing happens — no wall removed, no message. Measured at P0.4: 4 walls in, 4 walls out, 0 open edges. | `walls.py:300‑354` | **P4.1** |
| 16 | ~~**Room detection is silently clipped to `canvas_rect()`** — a plan larger than the canvas loses its edge rooms with no warning. Found by the P0.3 harness, not by any test.~~ **CLOSED STRUCTURALLY at P3.5.** `_RoomGrid` rasterised onto a grid sized by `canvas_rect()` and treated any flood reaching the grid edge as unenclosed, so the clip was inseparable from the method. The replacement is a walk over the wall graph, which has no canvas in it at all — closed by deletion rather than by a bounds check, which is the only kind of fix that cannot regress. Pinned by `test_detection_is_not_clipped_to_the_canvas` (a room built well past the canvas edge detects and reports its true area). | `rooms.py:29` (`_RoomGrid`, deleted) | **P3.5 (done)** |
| 23 | **A group move strands the region of a room it does not fully own.** A rubber band selects only items FULLY inside it, so a wall poking out of the band is left behind; `group_selected` then DUPLICATES that room's walls into the group, `room_owns_walls` is correctly false, and the room is not carried. Its region therefore stays where it was while the member walls walk out from under it — the "detached, dashed outline at the original position" presentation. **Measured on `symmetricP1` with a band clipping 8% of the plan: 3 of 20 rooms stranded — Garage 46.7", PKT Off 40.0", Util 23.3" between the region's centroid and its own walls'.** NOT NEW AT P3.5, and the first guess that it was is corrected here: the same measurement on the pre-P3.5 tree strands Garage by **148.3"**, so re-detection was not hiding it — it was landing the room somewhere worse. Distinct from defect 22, which is the identity tear underneath a room that *does* get carried and looks correct. **The fix is a semantics decision, not a repair:** should a room whose walls partly moved DEFORM to follow the corners that moved (which is what a party-wall drag already does to both its rooms), or stay put? That is what a group IS, so it belongs with **P4.5**, alongside the duplicate-on-group behaviour that produces the case. | `mainwindow.py` (`group_selected`), `items.py` (`bake`) | **P4.5** |
| 22 | ~~**A group move orphans every room outline it carries.**~~ **FIXED as a P3.5-followup.** `GroupItem.bake` assigned new COORDINATES to every member wall end — split-on-write by P3.1's ruling, so each end came away on a fresh `Vertex` — and rebuilt each carried room's corner list beside it, minting a third set. The two agreed numerically and shared nothing, so after a bake a room's outline no longer held its walls' corners and the next wall drag left the room behind. **Measured on `symmetricP1`: 140/140 shared corners → 0/140, and a party-wall drag then resized nothing (−18.20 / +9.50 sf before, +0.00 / +0.00 after).** `_apply_rotation` had the identical defect. **Not a P3.5 mistake so much as a P3.5 consequence:** `refresh_rooms` re-bound and re-shared after every group move, so deferring bake's conversion to P4.5 was safe exactly as long as detection existed — P3.5 changed the deferral's premise. Fix: both paths move through one set of CORNER RECORDS and relocate each corner once, so walls and outlines follow by construction (the plan's own `move_vertices`); a corner a non-member wall also holds is SPLIT first, so the group moves and the outsider does not. **Found by a manual smoke test, not by the suite** — every group test tops out at ~5 members and none asserted on `unwelded_ends`; both gaps closed with five new tests. | `items.py` (`bake`, `_apply_rotation`, `_corner_records`) | **P3.5-followup (done)** |
| 19 | **The PNG extractor leaves its walls unwelded — and it has TWO arms.** Detected walls are written out with no weld pass, and per the corrected **F5** nothing welds them afterwards either, because load doesn't and coalesce doesn't. So every extracted plan is born with open junctions — precisely the condition that leaks room detection between spaces. Measured at P1.6: 2 unwelded ends on the `test_extract` fixture. **File arm:** `fp_extract.py` writes a plan file which is later opened — closes automatically once P2.1 welds on load. **In-app arm:** `extract_from_reference` (`mainwindow.py:1644`) injects walls *directly into the live scene* and commits, bypassing every load path, so **P2.1's weld-on-load never sees them**; this arm needs an explicit weld pass after the detected walls are written. Ride it with P2.1 — closing only the file arm would leave the exact reported reproduction alive. Not caught by shadow mode either (an `unwelded_ends` rise is report-only: the 9″ tolerance is a gesture, not an invariant), so it must be fixed on purpose rather than by a gate. | `fp_extract.py`; `mainwindow.py:1644` (`extract_from_reference`) | **P2.1 (both arms)** |
| 18 | ~~**`inner_faces` drops the largest INNER face as the "outer boundary" — discarding a real room.**~~ **FIXED at P1.3b.** The true outer boundary is opposite-wound and already excluded by the majority-sign filter, so `inner[1:]` threw away the biggest *room* (symmetricP1's Garage, 868.5 sf). Fix: keep the majority winding, drop *all* opposite-wound faces (one per component), never by size — in both `design/topology.py` and `tools/migrate_to_design_v5.py`. Retargeted P3.5 → **P1.3b** because P2.1's import traces outlines, so the bug would silently fall back to stored corners for the largest room of every imported plan. | `design/topology.py`, `tools/migrate_to_design_v5.py` (`inner_faces`) | **P1.3b (done)** |
| 20 | **Merging a collinear run can REVERSE the survivor without swapping `left`/`right`, silently flipping every side on that wall.** `merge_collinear` wrote `w1.v1, w1.v2 = far1, far2`, and `far1` is the survivor's *far* end — so whenever the run extends behind the survivor's `v1`, the merged wall comes out pointing the other way while its `left`/`right` stay as written. Every side on that wall is then on the wrong side. **Found by single-sourcing at P3.4(i)** — not by a test, not by review: it only became visible when the same decision logic had to serve a scene that *renders* sides. **Fixed in the pure op at P3.4(i)** (the survivor keeps its own direction; every other end projects onto its axis), with its own test. **Still live scene-side** in `_coalesce_wall_impl`, which is why this is a defect and not a footnote: coalesce runs on wall draw/move release, on load/import, on ungroup and from Edit ▸ Coalesce all walls now, so the flip is reachable in shipping code paths **today**. It **dies at P3.4(iv)**, when the scene-side callers are retired.<br><br>**The instructive part is why nothing caught it.** A reversal slips straight past **I6**, because I6 checks that a wall's sides *agree with the rooms that name it* as a **set** — not **which** side is which. That is precisely the blind spot the P1.3 winding-pin test was built for ("without this, a flipped winding swaps every left/right and I6 still passes"), and this is the **first wild specimen proving the blind spot is real** rather than theoretical. If a cheap side-orientation invariant ever joins the deep three, this defect is its justification — *noted, not scoped.* | `design/topology.py` (`merge_collinear`, fixed); `walls.py` (`_coalesce_wall_impl`, still live) | **P3.4** — *pure op fixed at (i); scene-side dies at (iv)* |
| 21 | ~~**`relocated_to` silently renames a corner that was never named.**~~ **FIXED at P3.5.** P3.3's rule is "a moved corner is the SAME corner, so it keeps its uid" — but `relocated_to` copied `self._uid`, and uids are minted **lazily on first read**. On a vertex nobody had yet named, that `None` crossed the move and the "same corner" got a fresh identity the first time anything asked. **Nothing observably broke** while only the document walk read uids — which is exactly why it survived P3.1, P3.3 and P3.4 — and it becomes a live bug at **P4.5**, which serializes groups by member id: a group whose member corner had never been walked, then dragged, comes back naming a vertex that no longer exists.<br><br>**Found by P3.5's by-construction test**, not by review, and the near-miss is the instructive part: `test_relocation_carries_the_vertex_identity` has pinned this rule since P3.3 and **passes for a reason it does not state** — it reads `v.uid` before relocating, forcing the mint. A test that establishes the precondition it is meant to be testing cannot see the bug. Fix: read `self.uid`, forcing the mint at relocation. Deliberately *not* the per-READ allocation P3.1 removed — a relocation is a genuine move, orders of magnitude rarer than the reads on the paint path. Pinned by `test_relocation_carries_identity_even_when_never_named`, which constructs the unnamed case the original could not. | `floorplanner/vertex.py` (`Vertex.relocated_to`) | **P3.5 (done)** |

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
