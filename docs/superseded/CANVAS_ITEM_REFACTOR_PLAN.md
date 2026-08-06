> **SUPERSEDED 2026-08-06 — not the current plan.** Replaced by [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md); kept because its group/drag trace and recovered `test_zz*` forensics exist nowhere else (see [`../README.md`](../README.md)). Nothing below this line has been edited.

# Canvas Item Management — Health Review & Refactor Plan

> **Superseded by [`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md).** Kept for the group/drag trace and the recovered `test_zz*` forensics it records, which are not duplicated elsewhere. Not the plan of record.

**Repo:** `C:\dev\GitHub\FloorPlanner` · **Reviewed:** 2026‑07‑26
**Baseline:** `floorplanner/` package, 7,116 lines app code + ~4,100 lines tests, FILE_VERSION 4
**Reference plan:** `examples/planc1.json` (FILE_VERSION 3 — 46 walls, 20 rooms, 41 openings, 50 furnishings)

**Decisions taken before writing this plan:**

1. **Grouping will move the real items.** A `GroupItem` becomes a pure selection/transform wrapper over the actual walls, rooms, openings and furnishings. No wall duplication on group, no `coalesce_all` on ungroup.
2. **Staged delivery.** Phase 1 = a maintained item registry + batched rebuilds (perf, low risk). Phase 2 = groups as first‑class serialized entities. Phase 3 = incremental undo. Each phase ships independently with its own tests.

---

## 1. What `planc1.json` tells us

The schema is clean and compact. Three top‑level arrays plus `format` / `version` / `units` / `settings`:

```jsonc
walls: [{ "type": "interior|exterior",
          "p1": [x, y], "p2": [x, y],
          "rooms": ["Hall", "M Bath", "WIC"],           // names, re-bound by geometry on load
          "openings": [{ "kind": "door|window", "code": "3680",
                         "s": 89.0,                      // scalar distance from p1
                         "door_type": "POCKET", "swing": -1 }] }]
rooms: [{ "name": "Clst", "anchor": [x, y], "label_offset": [dx, dy],
          "show_dimensions": false,
          "properties": { room_type, include_sqft, ceiling_height_in, ceiling_type,
                          floor_finish, wall_finish, baseboard, crown_molding,
                          hvac, electrical, notes,
                          perimeter_corners: [[x,y], …] } }]        // ← shadow copy of RoomItem.corners
furnishings: [{ "kind": "bathtub", "pos": [x, y], "rotation": 0.0, …extra }]
```

Four properties of this schema drive everything below.

**(a) There is no `groups` array.** Groups exist only as live `QGraphicsItemGroup` objects. `MainWindow.project_from_scene` (`mainwindow.py:1042‑1083`) has branches for `FurnishingItem`, `WallItem` and `RoomItem` only — **no `GroupItem` branch**. Consequences: Ctrl+G produces no undo step at all (the serialized dict is unchanged), and *any unrelated* undo runs `scene.clear()` (`mainwindow.py:1287`) and silently dissolves every group in the plan. Save/reload loses all grouping.

**(b) There is no z‑order.** Deliberately excluded from `to_dict` (`model.py:211‑213`) so undo comparison stays stable — which also means "Bring to front" is silently reverted by the next undo of anything else.

**(c) Walls are shared, and heavily.** In this one plan:

| Rooms bordered by one wall | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| Wall count | 1 | 13 | 17 | 8 | 3 | 1 | 3 |

Three walls border **six** rooms each; one of them (exterior) carries **eight openings**. This is the shared‑wall model working as designed — and it is exactly what makes the current grouping implementation explode (§3).

**(d) Openings are positioned by a scalar `s` along the wall.** Any code that moves `p1`, or changes the wall's length or angle, must re‑base every `op.s`. Thirteen sites mutate `p1`/`p2`; **four of them do not re‑base** (§4, bug #3).

---

## 2. Health assessment — what's solid, what isn't

Overall: **the bottom of the stack is genuinely good; the scene layer is where it comes apart.** `walls.py` + `rooms.py` + `items.py` + `mainwindow.py` are 4,580 lines — 74% of the app — and form a mutually entangled blob with no ownership index, invariants that self‑heal in only one direction, and four competing z‑order systems.

| Module | Lines | Verdict | Why |
|---|---|---|---|
| `app.py` | 28 | **Solid** | Minimal, correct, ordering constraints commented. |
| `geometry.py` | 186 | **Solid** | Pure, stateless, testable. Best module in the repo. One wart: `bring_to_front`/`send_to_back` (`:131‑148`) are not geometry — they full‑scan the scene and mutate z. |
| `config.py` | 251 | **Solid** | The `_FLOOR_STATE` runtime cache (`:206‑233`) is the right call and the docstring explains why. Layering nit: `config` imports `model` (`:13`), inverting the documented order. |
| `model.py` | 235 | **Solid as a schema** | Clean, Qt‑free, stable sort keys. But it is a serialization DTO, **not** a source of truth — nothing outside the two bridge functions imports it; `Wall.rooms` is write‑only (emitted at `model.py:99`, never read on load — bindings are re‑derived geometrically at `mainwindow.py:1347`). |
| `catalog.py` | 248 | **Acceptable** | Three uninvalidated module caches (`:24‑26`); `apply_furnishing_prices` (`:214‑233`) rewrites `assets/…/manifest.json` from a UI action — an app feature that edits its own build artifacts. |
| `dialogs.py` | 579 | **Acceptable** | Straightforward Qt. The inventory aggregation helpers (`:27‑129`) are clean pure functions living in the wrong file. None filter by floor. Essentially untested. |
| `view.py` | 618 | **Acceptable** | Wheel‑zoom coalescing (`:159‑179`) is real, measured, test‑guarded engineering. But `mousePressEvent` is a 79‑line flat if‑chain over three modal sub‑states, and **`select_in_rect` mutates the plan** — a rubber‑band selection calls `synthesize_room_edge` (`view.py:445`) which *creates walls* and dirties the document. |
| `macro.py` | 901 | **Runner acceptable / recorder fragile** | Table‑driven dispatch and per‑token error isolation are good. `MacroRecorderDialog` installs an app‑wide event filter with `except Exception: pass` inside (`:751‑753`) plus a timestamp‑based key‑dedup heuristic — it mis‑records silently rather than failing. |
| `walls.py` | 1,311 | **Fragile** | `WallItem` is ~540 lines / 26 methods and carries a five‑mode drag state machine whose attributes are created in `mousePressEvent` (`:729‑765`), not `__init__`. `rebuild()` silently clamps `op.s` (`:568`) — a paint method mutating domain state. `_coalesce_wall_impl` snaps `p1`/`p2` **independently** and re‑bases `op.s` against the *pre‑snap* origin (`:199‑203`). Five hand‑rolled copies of the same point‑onto‑axis projection with five different tolerances. |
| `rooms.py` | 1,280 | **Fragile** | `RoomItem` is ~600 lines / 30 methods and includes inventory‑report generation and clipboard serialization. **`RoomItem` has no `itemChange`** — five call sites remove a room without `clear_walls()`, leaving `WallItem.rooms` holding deleted C++ wrappers. `bounding_walls`/`interior_walls` (`:522‑541`) are full scene scans with `QPainterPath` booleans and no floor filter. `corners` is stored twice (live `QPointF`s + `properties["perimeter_corners"]`) synced by six manual call sites. |
| `items.py` | 1,033 | **Fragile** | `FurnishingItem`/`StairItem` are fine. **`GroupItem` is the most fragile class in the codebase** — hand‑rolled `adopt()` bypassing Qt's transform handling (`:627‑640`), `sip.transferto` needed in `dissolve()` (`:658`) to stop members being GC'd out of the scene, `boundingRect()` recomputing the oriented box **twice** per call with zero caching (`:509‑528`), and `_content_points` (`:475‑487`) mixing group‑local wall coords with scene‑space furnishing coords in one list. |
| `mainwindow.py` | 1,956 | **Fragile** | **92 methods.** Five functions over 80 lines. `room_boolean` (`:631‑727`) deletes every wall returned by the unfiltered `bounding_walls()` — including neighbours' and other floors' walls — and recreates them all as `"interior"`. `refresh_rooms_cmd` (`:589‑593`) **deletes every room not on the active floor**. `align_rooms_to_grid` (`:530‑534`) snaps `p1`/`p2` independently with no opening re‑base. |
| `FloorPlanner.py` shim | 163 | **Acceptable** | 147 lines of stale docstring (still documents v3). Re‑exports four private names purely so tests can reach them — the test suite is coupled to internals, which will fight this refactor. |

### The single structural gap

**There is no canonical answer to "who owns which canvas item."** No registry, no index, no ownership map. Every question is answered by re‑scanning `scene.items()` and filtering by `isinstance` — I count **~45 distinct scan sites** (`walls.py` 14, `rooms.py` 13, `mainwindow.py` 16). Thirteen different discovery mechanisms coexist: `scene.items()` + isinstance · `scene.items(rect)` · the `WallItem.openings` attribute list (parallel to Qt's real child list, hand‑synced at nine sites) · the bidirectional `WallItem.rooms` ↔ `RoomItem.walls` pair · `childItems()` · `group() is None` as "is grouped" · `parentItem() is None` as "is top‑level" · `scene() is not None` as liveness · `sip.isdeleted()` (used exactly once, `walls.py:502`) · four throwaway spatial indices · `MainWindow._sel_order` · ad‑hoc single‑item refs · `id()` sets.

The four spatial indices (`_WallIndex` `walls.py:66`, `_WallBBoxIndex` `walls.py:380`, `_RoomGrid` `rooms.py:22`, `_WallGraph` `rooms.py:128`) are the closest thing to a registry — but each is **rebuilt from scratch and discarded every pass**, and each has a *different* membership rule. `_WallIndex`, the shared rebuild index, **has no floor filter at all**, so a floor‑1 wall extends its end because a floor‑2 wall shares that coordinate.

This is the thing to fix first. It collapses ~45 scan sites and turns "does this query filter by floor?" from 45 separate decisions into one.

---

## 3. Root cause of the group/move problem

You reported it as slow and buggy when grouping and moving many named, populated rooms. It is both, and it's one design decision.

### 3.1 What Ctrl+G does today

`MainWindow.group_selected` (`mainwindow.py:729‑766`):

```python
elif isinstance(it, RoomItem):
    seen = set()                                   # ← per room, NOT across rooms
    for w in it.bounding_walls() + it.interior_walls():
        ...
        members.append(duplicate_wall(self.scene, w))
```

Selecting a room does not group the room. It **duplicates that room's bounding and interior walls** into the group and leaves the originals in place. The dedup `seen` set is scoped **inside the per‑room branch**, so a wall shared by six rooms is duplicated **six times** when all six are selected.

Applied to `planc1.json` with all 20 rooms selected, using the file's own `rooms` lists as a lower bound (`bounding_walls()` is geometric and returns a *superset*):

| | Before | After Ctrl+G (lower bound) |
|---|---|---|
| Walls | 46 | **≥ 152** |
| Openings | 41 | **≥ 190** |

**≥ 106 duplicate walls and ≥ 149 duplicate doors/windows created by a single keystroke** — and that is the floor, not the estimate.

### 3.2 What each duplication costs

`duplicate_wall` (`rooms.py:1068‑1082`) ends in `nw.rebuild()` with `index=None` and `cascade=True`. With no index that is:

- 2 × `_joined_at` → full `scene.items()` scan each (`walls.py:541‑547`)
- 1 × `coincident_walls` → full scan (`walls.py:139`)
- cascade: 1 more full scan, then 3 more per coincident wall — and the copy is *exactly* coincident with its original, so the cascade always fires

**≈ 7 full O(N) scene scans per duplicated wall.** With ≥106 duplications on a scene that is simultaneously growing past 150 walls, grouping the plan is **O(rooms × walls × items)**.

On top of that, `RoomItem.bounding_walls()`/`interior_walls()` (`rooms.py:522‑541`) each build a fresh `QPainterPathStroker` band and run a `QPainterPath.intersects`/`contains` against **every** wall — the expensive kind of geometry — once per selected room.

And `scene.selectionChanged` is wired to `_update_edit_actions` (`mainwindow.py:323`), which calls `_selected_room_shapes()` (`:598‑629`), which calls `bounding_walls()` **per already‑selected room**. Ctrl‑clicking room *k* re‑runs that for all *k* prior rooms: **O(R²·W) path booleans just to build the selection**, before you even press Ctrl+G.

### 3.3 What the drag costs

The drag loop itself is actually clean — no child `itemChange` fires, nothing rebuilds per mouse‑move. The per‑frame cost is:

- `GroupItem.boundingRect()` recomputes `_oriented_box()` **twice** (once directly, once via `_handle()`), and `paint()` a third time — all uncached, all O(members) with `mapToScene` per furnishing (`items.py:475‑554`).
- `_update_totals` is wired to `scene.changed` (`mainwindow.py:98`) and does a full `scene.items()` scan every update cycle (`:342`).
- `setItemIndexMethod(NoIndex)` (`mainwindow.py:78`) + `FullViewportUpdate` (`view.py:118`) + **zero `setCacheMode` calls anywhere** ⇒ every frame repaints every item, and `RoomItem.boundingRect()` constructs a `QFontMetricsF` on each call (`rooms.py:678‑689`).

The real cost lands on **release**, in `GroupItem.bake()` (`items.py:663‑700`): a full `scene.items()` scan × `room_owns_walls` per room, then an unconditional `rebuild_all_walls(sc)` — which rebuilds **every wall including the group's own children** (`walls.py:421` has no `group()` filter), builds two more `_WallBBoxIndex` instances, rasterises a 112,000‑cell `_RoomGrid`, and builds an explicitly O(W²) `_WallGraph` whose node dedup is itself O(nodes²) (`rooms.py:157‑163`).

Because a big group sweeps across the plan, nearly every room's `room_signature` changes, so the memoization in `refresh_rooms` — the thing that normally saves you — **defeats itself completely**: every room goes dirty, every room floods the grid, every room re‑binds its walls via `_wall_along_segment` (a full scan **per perimeter edge**).

Arrow‑key nudge is worse: `nudge_selected` (`mainwindow.py:503‑517`) calls `it.bake()` per key event — a **full plan rebuild + full room re‑detection per keyboard auto‑repeat tick**.

### 3.4 What ungroup costs, and the data corruption

`ungroup_selected` (`mainwindow.py:771‑783`) does `bake()` per group (→ full rebuild each), then `coalesce_all` — self‑documented as O(walls²), run to a fixed point, rebuilding `_WallIndex` and doing three full scans **per pass** — then `rebuild_all_walls` again.

And `_coalesce_wall_impl` appends absorbed openings with **no dedup** (`walls.py:205‑212`). So the round trip *group a room with a door → ungroup* leaves **two coincident doors on one wall, permanently.** On `planc1.json` that's ~149 duplicate openings collapsing back onto 46 walls with no de‑duplication.

### 3.5 What the deleted scratch tests confirm

`tests/__pycache__` still holds bytecode for three deleted files. Decompiling their constants:

- **`test_zzleak.py`** — *"THROWAWAY - realistic repeated group→move→ungroup cycles."* Two tests (`test_realistic_walls_and_room`, `test_realistic_room_only`) that loop `_cycle(select → group_selected → setPos → bake → ungroup_selected)` and print the non‑open wall count and room count each cycle. This is the wall‑leak accumulation hunt.
- **`test_zzrepro.py`** — *"THROWAWAY repro."* `test_walls_and_room_no_corners`: sets `room.corners = None`, groups walls+room, moves +200/+100, and prints `>>> BUG if room region/anchor stayed at ~(0,0) while walls moved to ~(200,100)`. The corner‑less room left behind by `walls_cover_room`.
- **`test_zzprobe.py`** — *"Does pinning an exact zoom make it deterministic?"* Parametrized over window size and view scale, counts `OpenWall`s after `detach_wall_from_room`. A **view‑scale‑dependent detection result** — i.e. a geometry query whose answer depends on the zoom level. That one is unresolved and worth its own look.

The permanent regression tests that came out of that hunt (`test_groups.py:99`, `:133`, `:155`) are good tests — but they encode the *duplicate‑on‑group* semantics as intended behaviour. They will need rewriting under decision #1, deliberately.

---

## 4. Correctness bugs to fix (ranked, independent of the refactor)

These are real defects found while reading, ordered by blast radius. Several are one‑line fixes.

| # | Bug | Site | Effect |
|---|---|---|---|
| 1 | **Groups are not serialized.** `project_from_scene` has no `GroupItem` branch. | `mainwindow.py:1042‑1083` | Ctrl+G creates no undo step; any unrelated undo dissolves every group; save/reload loses all grouping. |
| 2 | **`refresh_rooms_cmd` deletes every room on every non‑active floor.** It tests `room_walled()` for all rooms, but `_RoomGrid` rasterises only active‑floor walls — an off‑floor room can never be enclosed. | `mainwindow.py:589‑593`, `rooms.py:39‑42` | Rooms ▸ Refresh rooms silently wipes other floors. **Data loss.** |
| 3 | **Four `p1`/`p2` mutations don't re‑base `op.s`.** p1‑end drag (`walls.py:885‑886`), `join_endpoints` (`:954‑965`), `align_rooms_to_grid` (`mainwindow.py:531‑534`), and coalesce re‑basing against the *pre‑snap* origin while snapping p1/p2 independently (`walls.py:199‑203`). | see sites | Doors and windows slide along their wall; diagonal walls change angle. |
| 4 | **`room_boolean` deletes neighbours' walls.** Its deletion set is `bounding_walls()` — everything touching the boundary band, including other rooms' and other floors' walls — removed unconditionally, bypassing `fracture_delete_wall`, and recreated hardcoded as `"interior"`. | `mainwindow.py:674‑698` | Destroys exterior wall types and adjacent rooms. |
| 5 | **Undo snapshots alias live state.** `properties=it.properties` passes the live dict by reference into every stacked snapshot; `_sync_corner_props` then mutates it in place. | `mainwindow.py:1074`, `rooms.py:439‑445` | Past undo states silently mutate; property‑only changes can compare equal and produce **no undo step**. |
| 6 | **Seven `except ValueError: continue` sites silently delete an opening** when `set_code` rejects it as wider than the wall — including on **load** (`mainwindow.py:1304`). | `walls.py:209,342,1079`; `rooms.py:859`; `mainwindow.py:949,1304,1388` | Shrink a wall → `rebuild()` clamps `s` → save → reload → the door is gone, no message. |
| 7 | **`RoomItem` has no `itemChange`.** Five sites remove a room without `clear_walls()`. | `mainwindow.py:472,592,677,1234,1287` | `WallItem.rooms` holds deleted C++ wrappers; `primary_room.raise_to_front()` (`walls.py:724`) can raise `RuntimeError`. |
| 8 | **Coalesce duplicates openings** (no dedup on absorb). | `walls.py:205‑212` | Two coincident doors after group→ungroup. |
| 9 | **Rubber‑band selection mutates the plan** — `select_in_rect` calls `synthesize_room_edge`, creating walls. | `view.py:445` | A read‑only‑looking gesture dirties the document. |
| 10 | **Four competing z‑order systems** (static constants; `raise_to_front`'s `_z_top*10` counter; `bring_to_front`'s global max+1; `detach_wall_from_room`'s +1 drift). Both of the first two run on **every wall click** (`walls.py:723‑727`). | `items.py:451`, `rooms.py:568‑588`, `geometry.py:131‑148`, `rooms.py:1217` | They fight on different scales; after enough clicks `raise_to_front` pushes walls *backwards*. `GroupItem` z=1 also sits below ungrouped furnishings (z=3) and room fills (z=4). |
| 11 | **`_WallIndex` and `weld_all` don't filter by floor**, contradicting `CLAUDE.md:11`. Also unfiltered: `_project_to_orthogonal`, the wall‑drag `_attached` scan, `bounding_walls`, `interior_walls`, `wall_endpoint_open`, `StairItem._ceiling_height`, all inventory queries. | `walls.py:81‑96,266‑286`, `rooms.py:522‑541`, … | Cross‑floor geometry leaks. |
| 12 | **Detection depends on view zoom** (from `test_zzprobe`). | `detach_wall_from_room` path | Non‑deterministic open‑wall count. Needs reproduction. |

---

## 5. Test suite — what's guarded and what isn't

**Strengths.** The suite is real: 26 files, category markers, a conftest that owns the `QApplication`, and almost no mocking (only two justified monkeypatches). `test_rooms.py` (500 lines) covers detection, boolean ops, and — notably — the *memoization correctness* of `room_signature` (`:471‑496`). `test_walls.py` (436 lines) is dense on draw/snap/stretch/weld/fracture. `test_model.py` is Qt‑free and covers migration. `test_groups.py` has genuinely good fixed‑point tests (`:155‑181` runs four group/move/ungroup cycles and asserts the counts stop changing).

**The gaps that matter here.**

- **Nothing measures performance.** `bench_rooms.py` is not a test (no `test_` prefix, never collected), tops out at 36 rooms, prints numbers and **asserts nothing**. A 100× slowdown produces a green suite.
- **Every group test uses ≤ 5 members.** O(n²) at n=5 is invisible. The at‑risk paths — `bake()`'s full rebuild, `ungroup`'s O(W²) coalesce, `_oriented_box` per repaint, `_apply_rotation`'s `w.rebuild()` per mouse‑move — are all untested at scale.
- **No test groups anything and then calls `undo()`.** The two most stateful subsystems have zero intersection coverage.
- **No test serializes a grouped plan.** Adding `make_room → group_selected → serialize → load_data → assert group survives` would fail immediately and document bug #1.
- **No test asserts `op.s` survives a group move or rotation** — despite `_apply_rotation` calling `w.rebuild()` specifically to re‑sync openings.
- **Nothing asserts grouped walls are exempt from coalescing.** Deleting the `group() is None` guard would pass CI.
- **Groups across floors:** `GroupItem.floor = active_floor()` is set and never meaningfully read; `TODO.md:74` says "require members on one floor" — not implemented, not tested.
- **The one real drag test is `@pytest.mark.gui`**, so `pytest --quick` — the default fast loop — never exercises the actual mouse path that regression #1 was about.

**Quality issues to clean up as we go.** ~1/3 of tests reach into private API (`view._zoom_accum`, `g._angle`, `room._detect_sig`, `dup._path`, `win._sel_order`, `fp._coalesce_all_impl`); `first_furnishing` is `catalog()[0]["id"]` and silently changes subject if `manifest.json` is reordered; `test_ai_pricing.py` writes to a repo file; tolerances of `abs=6`–`abs=8` inches can hide a full grid‑cell regression; `test_groups.py:346` has a conditional assertion that passes in two structurally different worlds.

---

## 6. The refactor plan

### Phase 0 — Safety net (do this first, ~½ day)

Nothing below is safe to attempt without these.

- **0.1 Scaling harness.** Add `tests/test_scaling.py` (marked `slow`): build an *n*×*n* room grid with doors, windows and furnishings; time `group_selected`, group drag+`bake`, `ungroup_selected`, and `rebuild_all_walls` at *n* and 2*n*; assert the ratio stays under ~3×. This converts `bench_rooms.py`'s eyeball check into an actual guard and is the acceptance criterion for every phase below.
- **0.2 Characterization tests for what we're about to change.** Group a named room with doors/windows/furnishings; assert (a) opening `s` values unchanged after move and after rotation, (b) room properties intact, (c) wall count is a fixed point across four cycles, (d) `serialize → load_data` round‑trips the group. Several will fail today — that's the point; mark them `xfail` with the bug number and flip them as each lands.
- **0.3 Decouple tests from privates.** Promote the four private names re‑exported for tests (`FloorPlanner.py:155‑160`) to a small internal test API, or move those tests to import from the submodule directly. Do this now, before anything moves.
- **0.4 Fix the free bugs.** #5 (`dict(it.properties)`), #7 (add `RoomItem.itemChange` mirroring `walls.py:496‑504`), #2 (scope `refresh_rooms_cmd` to the active floor). Three small commits, each with a regression test.

### Phase 1 — The item registry and batched rebuilds (the performance work)

This is where the speed comes from. No schema change, no undo change, no behaviour change.

**1.1 `floorplanner/index.py` — a `PlanIndex` owned by the scene.**

One object, attached to the scene, maintained incrementally on add/remove/move rather than rebuilt per pass:

```python
class PlanIndex:
    # per floor: walls, rooms, furnishings, groups  (sets, not scans)
    # a uniform-grid bbox index over walls, updated on wall geometry change
    # dirty sets: walls_dirty, rooms_dirty
    def add(item) / remove(item) / mark_moved(item)
    def walls(floor=ACTIVE) -> Iterable[WallItem]
    def rooms(floor=ACTIVE) -> Iterable[RoomItem]
    def walls_near(rect, floor=ACTIVE) -> Iterable[WallItem]
```

Then replace the ~45 `scene.items()` + isinstance sites with `index.walls(floor)` / `index.rooms(floor)` / `index.walls_near(rect)`. **The floor filter becomes one decision instead of 45** — which fixes the entire bug #11 class as a side effect.

Subsume the four throwaway indices: `_WallIndex` and `_WallBBoxIndex` become views onto `PlanIndex`; `_RoomGrid` and `_WallGraph` stay per‑pass (they're genuinely derived) but get built from `index.walls_near(dirty_bbox)` rather than the whole plan.

Sequencing so it stays green: land `PlanIndex` alongside the existing scans first, with a `--verify-index` debug mode that asserts `set(index.walls()) == {scans}` after every operation. Run the suite with it on. Then delete the scans module by module.

**1.2 A rebuild scheduler — `with plan.batch():`.**

Today `rebuild_all_walls` is called unconditionally and does the whole plan. Replace with:

- A dirty‑region accumulator. `mark_moved(item)` adds its bbox (before and after) to a dirty rect.
- `rebuild_dirty()` rebuilds only walls intersecting the dirty rect, recomputes junctions only for those plus their neighbours, and calls `refresh_rooms` scoped to rooms whose signature bbox intersects the dirty rect.
- A `batch()` context manager that coalesces N mutations into one rebuild, so `bake()`, `ungroup`, CSV import and load each rebuild **once** instead of once per sub‑operation.
- Also: `rebuild_all_walls` currently rebuilds grouped walls even though coalesce, weld and binding all skip them (`walls.py:421`). Add the `group() is None` filter.

Fixes the double rebuild in `ungroup_selected` (`bake()` rebuilds, then lines 781‑782 rebuild again) and the per‑keystroke rebuild in `nudge_selected`.

**1.3 Defer geometry work during a drag.**

Follow the pattern the wheel‑zoom coalescing already established (`view.py:159‑179`) — it's the right instinct, it just was never applied to drags.

- Set a `plan.interactive = True` flag on drag start. While set: no rebuild, no room detection, no `_update_totals`.
- Debounce `_update_totals` behind the same 180 ms timer `_mark_dirty` uses, instead of firing on every `scene.changed` (`mainwindow.py:98`).
- On drag end: one batched `rebuild_dirty()`.

**1.4 Rendering cost.**

- **Re‑enable the scene BSP index.** `NoIndex` (`mainwindow.py:78`) makes every hit test a linear scan calling `shape()` on every item. If it was set to work around item‑geometry lies, fix the lie (`prepareGeometryChange` discipline) rather than disabling the index. Measure both.
- **Cache `GroupItem`'s oriented box.** Compute `_oriented_box` once per geometry change, not 3× per paint (`items.py:509‑528`). Same for `RoomItem._label_rect`'s `QFontMetricsF` (`rooms.py:678`) and `_boundary_band`'s stroker (`rooms.py:514`).
- **`setCacheMode(DeviceCoordinateCache)`** on furnishings and room fills — static SVG content repainted every frame today.
- Revisit `FullViewportUpdate` (`view.py:118`) once item bounding rects are trustworthy; `SmartViewportUpdate` with correct rects is a large win.

**1.5 Batch selection signals.**

`ungroup_selected` calls `setSelected(True)` per member (`mainwindow.py:779‑780`), emitting one `selectionChanged` per item, each triggering `_selected_room_shapes()` with its O(R·W) path booleans. Wrap multi‑select operations in a signal block + one final emit, and make `_update_edit_actions` cheap (it should read cached counts from `PlanIndex`, not re‑derive room shapes).

**Acceptance:** `test_scaling.py` shows group/drag/ungroup on a 20‑room plan at least an order of magnitude faster, with sub‑quadratic scaling from *n* to 2*n*.

### Phase 2 — Groups as first‑class entities (the correctness work)

**2.1 Change the semantics.** Per decision #1, `group_selected` stops calling `duplicate_wall`. A group holds references to the real items:

- Selecting a room brings the room, its bound walls, their openings, and the furnishings inside its path.
- A **shared** wall (one bordering a room outside the selection) is resolved **once** at group time via the existing `_privatize_shared_walls` mechanism (`rooms.py:838‑865`) — split along the selection boundary, not duplicated wholesale. Its openings re‑base through the single `rebase_openings()` helper from 2.3.
- Ungroup no longer calls `coalesce_all`. Nothing was duplicated, so nothing needs merging. (Keep Edit ▸ Coalesce all walls now as the explicit user‑invoked path.)
- Add an explicit **Duplicate into group** command if you still want the stamp/copy behaviour — it's a genuinely useful tool, it just shouldn't be what Ctrl+G does.

This deletes the ≥106‑duplication explosion, the ≥149 duplicate openings, the O(W²) coalesce on every ungroup, and the whole `room_owns_walls` / `walls_cover_room` ambiguity (`rooms.py:1030‑1065`) — the group *is* the set of moved items, so there is nothing to infer.

**2.2 Serialize groups.** Add to `model.py`:

```python
@dataclass
class Group:
    members: list[GroupRef]     # stable ids into walls/rooms/furnishings
    rotation: float
    floor: str
```

This requires **stable item ids** — currently items are identified positionally by geometry sort order. Add a `uid` (monotonic int or uuid4 hex) to `WallItem`/`RoomItem`/`FurnishingItem`, emit it in the schema, and bump `FILE_VERSION` to 5 with a v4 migration that assigns uids on load. Stable ids are independently valuable: they're what Phase 3 needs to reference items in undo commands, and they make the `Wall.rooms` name‑based binding (`model.py:73`, currently write‑only) unnecessary.

**Constrain groups to one floor** (`TODO.md:74`) and enforce it in `adopt()`, with a test.

**2.3 One opening‑rebase helper.** `rebase_openings(wall, old_p1, old_unit)` called by **every** site that mutates `p1`/`p2`. Route all thirteen through it and add an assertion in `WallItem.rebuild` that `op.s` is in range rather than silently clamping (`walls.py:568`).

**2.4 Collapse z‑order to one system.** Either fully static (constants + explicit per‑item `z_offset` that *is* serialized) or fully dynamic and serialized. The current hybrid cannot be made correct. Also raise `GroupItem`'s z above furnishings and room fills.

**2.5 Fix the remaining bugs** from §4: #4 (`room_boolean` scoping), #6 (surface rejected openings instead of dropping them), #8 (dedup on coalesce absorb), #9 (make `select_in_rect` read‑only), #12 (the zoom‑dependent detection from `test_zzprobe`).

### Phase 3 — Incremental undo (defer until Phases 1–2 are settled)

Only worth doing once groups are serialized and items have stable ids — both are prerequisites.

Replace the whole‑document snapshot (`_commit_if_changed` → `serialize()` → deep dict compare, `mainwindow.py:842‑853`, 100 retained snapshots) with `QUndoStack` + commands: `AddItems`, `DeleteItems`, `MoveItems`, `EditWallEnds`, `EditRoomProps`, `EditOpening`, `Group`/`Ungroup`, `ChangeSettings`, floor ops. Each captures only the affected items (by uid) and re‑runs a **scoped** `rebuild_dirty()` — which Phase 1 already built.

Migrate incrementally: route one edit family at a time through a command, keep the snapshot stack as a fallback until every path is converted, then remove it. `CODE_REVIEW.md:126‑146` already scoped this correctly; the only change is that Phase 1's dirty‑region rebuild makes each command cheap.

### Deliberately not in scope

- Splitting `MainWindow`'s 92 methods. Worth doing (IO, CSV, image import, floors, boolean ops are each independent and testable) but it's churn that competes with the above. Do it after Phase 2, when the seams are clean.
- Making `model.py` the live source of truth with items as views. That's a much bigger rewrite than the ~45‑scan fix, and Phase 1 + 2 capture most of its benefit.
- De‑globalizing `SETTINGS` (`CODE_REVIEW.md` #4). Independent, low value, land anytime.

---

## 7. Sequencing and risk

| Phase | Effort | Risk | Payoff |
|---|---|---|---|
| 0 — safety net + free bug fixes | ½–1 day | none | Makes everything else verifiable |
| 1 — `PlanIndex`, batching, drag deferral, render caching | 3–5 days | **low** — mechanical, verifiable against the existing scans | The performance fix; also closes the cross‑floor leak class |
| 2 — group semantics + serialization + uids + `rebase_openings` | 4–6 days | **medium** — changes user‑visible behaviour and the file format | The correctness fix; deletes the duplication explosion |
| 3 — command undo | 4–6 days | medium‑high — touches every edit path | Scaling ceiling, not a bug. Profile after Phase 1 before committing. |

**Two rules for the whole effort:**

1. `python -m ruff check .` then `python -m pytest` green after every step. Phase 1 additionally runs with `--verify-index` on.
2. When a scratch repro is faster than a test — the `test_zz*` pattern — **promote it to a real test before deleting it.** All three deleted files were investigating bugs that are still live in the code; the evidence only survived by accident in `__pycache__`.

**Start here:** Phase 0.1 (the scaling harness) and Phase 0.4 (the three free bug fixes). The harness gives you a number to point at, and the numbers in §3.1 give you the target: grouping `planc1.json`'s 20 rooms should create **0 new walls**, not 106.
