# Code Review — FloorPlanner

Baseline version: **v1.0** (`APP_VERSION`) · file format v3 (`FILE_VERSION`)
Date: 2026-06-18
Scope: `FloorPlanner.py` (8,037 lines) plus tests, tooling, and supporting scripts (`fp_macro.py`, `fp_extract.py`, `_gen_assets.py`).

This review is constructive: the codebase is capable and well-engineered in several respects. The items below are ordered by leverage — fixing #1 and #2 unlocks most of the others.

---

## What's done well

- **`CLAUDE.md` is excellent.** The shared-wall model, performance hot-path notes, and headless-testing gotchas capture the institutional knowledge most projects lose. Keep investing here.
- **Real, documented performance engineering.** The `_RoomGrid` / `_WallGraph` / `_WallIndex` / `_WallBBoxIndex` indices, the memoized `refresh_rooms` (via `room_signature`), and the coalesced wheel-zoom (`wheelEvent` → one-shot timer → `_apply_zoom`) are thoughtful and measured (`tests/bench_rooms.py`).
- **Disciplined error handling.** Zero bare `except:`, only 6 `except Exception`, only 2 `print()` calls in the whole module.
- **A genuine test suite.** pytest with category markers, a `conftest.py` that owns the `QApplication`, ruff configured, and regression tests for past bugs (group GC, wall-drag in `test_groups.py`).

---

## Findings (priority order)

### 1. The application is a single 8,037-line module — *highest leverage*

`FloorPlanner.py` holds everything: geometry helpers, every `QGraphicsItem` subclass, all dialogs, the view, the main window, IO, and the macro runner. `MainWindow` alone is ~1,700 lines and 76 methods; `WallItem`, `RoomItem`, and `MacroRunner` are each very large.

**Cost:** navigation, code review, merge conflicts, and the inability to reason about one subsystem without scrolling past the rest.

**Why it's tractable:** the file already has clean internal seams. A natural package split:

- `geometry.py` — `grid_snap`, `wall_snap`, `line_intersection`, `dist_point_segment`, interval/merge helpers, etc.
- `walls.py` — `WallItem`, `OpenWall`, `_WallIndex`, coalesce/weld/fracture functions.
- `rooms.py` — `RoomItem`, `_RoomGrid`, `_WallGraph`, room detection/refresh.
- `items/` — `OpeningItem`, `FurnishingItem`, `StairItem`, `GroupItem`, `ReferenceImageItem`.
- `dialogs.py` — `InventoryDialog`, `RoomPropertiesDialog`, `SettingsDialog`, `AIPricingDialog`, `AboutDialog`, etc.
- `io.py` — serialize/`load_data`, save/load paths, export.
- `view.py` — `PlanView`.
- `mainwindow.py` — `MainWindow`.
- `macro.py` — `MacroRunner`, `MacroRecorderDialog`.

> Deferred to the next session per your request: a concrete, class-by-class module split plan.

### 2. No separation between the domain model and Qt

The `QGraphicsScene` and its items **are** the model. Domain state lives on the graphics items (e.g. `WallItem.rooms`, room properties on `RoomItem`). `serialize()` walks the scene to produce a dict, and `load_data()` rebuilds the scene from one.

**Cost:**
- Domain logic (wall coalescing, room detection, binding) can't be unit-tested without constructing Qt items and a scene.
- Business rules are entangled with rendering and event handling.
- Undo and persistence are forced to operate on the whole scene (see #3).

**Direction:** introduce a plain-Python model layer (dataclasses: `Wall`, `Room`, `Opening`, `Furnishing`, `Floor`, `Project`) as the source of truth, with `QGraphicsItem`s as views over it. This can be done incrementally — start by moving serialization to operate on the model, then migrate logic off the items over time. This is the structural prerequisite that makes #3 and #6 cheap.

### 3. Undo/redo is whole-document snapshotting

`_commit_if_changed()` calls `serialize()` and pushes the entire plan dict onto `_undo_stack` (`UNDO_LIMIT = 100`); `undo()`/`redo()` restore by running `load_data()`, which rebuilds the whole scene and re-detects rooms.

**Cost:** O(plan size) in time and memory per edit. On a large plan, a single undo reloads and re-detects everything, and 100 full snapshots can be heavy.

**It works today** because `serialize()`/`load_data()` are robust — this is a scaling ceiling, not a bug.

**Direction:** a command stack (`QUndoStack` + `QUndoCommand` subclasses: `AddWall`, `MoveItems`, `DeleteItems`, `EditRoomProps`, …) scales with the size of the edit, not the plan. It pairs naturally with the model layer in #2 (each command mutates model + scene and reverses cleanly).

### 4. Global mutable `SETTINGS`

`SETTINGS = dict(DEFAULT_SETTINGS)` is a module-level mutable singleton read throughout the code.

**Cost:** process-wide shared state — two windows can't hold different settings, test isolation needs save/restore dances, and reads create hidden coupling.

**Direction:** hold settings on an instance/config object passed where needed (or on `MainWindow`). The module-level *constants* (`EXTERIOR_T`, `WALL_Z`, `GRID_MAJOR`, …) are fine as-is — this applies specifically to the mutable dict.

### 5. Dependency and packaging hygiene

- `requirements.txt` is unpinned (`PyQt6`, `pyqt6-sip`). A fresh install isn't reproducible; a PyQt6 minor bump could break the app silently.
- No `pyproject.toml` / entry point. A ~350 KB application is run as a bare script (`python FloorPlanner.py`).

**Direction:** pin versions (e.g. `PyQt6==6.x.y`), add a `pyproject.toml` with project metadata and a `console_scripts` entry point so it's installable (`pip install -e .`) and launchable as a command.

### 6. No multifloor concept — but it's the stated product goal

The editor is a single canvas, and `serialize()` is flat (`format`, `version`, `units`, `settings`, `walls`, `rooms` at the top level). The product intent is *multifloor* plans.

**Cost:** retrofitting a floor/level layer after the model is entangled (see #2) is exactly the migration pain to avoid.

**Direction:** introduce a `Floor`/level layer now — a `Project` owning an ordered list of `Floor`s, each owning its walls/rooms, with the active floor swapped into the scene. Far cheaper to design in before more code accretes on the flat assumption. Bump `FILE_VERSION` with a load-time migration from the current flat format (the existing v1→v3 geometry-rebind migration is a good model to follow).

### Minor

- **Repo clutter:** `snip.png`, `_tot.png`, and `trial-export-rooms.csv` sit in the repo root. Remove or gitignore.
- **Committed IDE state:** `.idea/workspace.xml` is tracked; IDE/workspace files are usually gitignored.

---

## Status (updated 2026-06-20)

- **#1 Module split — ✅ DONE.** `FloorPlanner.py` is a 163-line shim over the `floorplanner/` package.
- **#2 Model layer — ✅ DONE.** Qt-free `model.py` (`Project`/`Wall`/…); `serialize`/`load_data` bridge through it.
- **#3 Command-based undo — ⛔ STILL HOLDS** (unchanged). Plan below.
- **#4 Global mutable `SETTINGS` — ⚠️ PARTIALLY MITIGATED.** Centralized in `config.py` as one shared object; still a process-wide mutable singleton. Plan below.
- **#5 Packaging/pinning — ✅ DONE.** `pyproject.toml` + console entry point; pinned `PyQt6`/`PyQt6-sip`.
- **#6 Multifloor — ✅ DONE (Phase 1).** Built on the model layer per `TODO.md`: per-item `floor`, floor-scoped detection/coalesce/weld/junctions, gray rendering + visibility, a Floors menu + status-bar indicator, FILE_VERSION 4 with v1–v3 migration. (Phase 2 = duplicate-floor / move-between-floors / stacking view.)

## Fix plan — #4 Settings object (low risk, recommended first)

The mutable dict is read in ~50 sites across `config`/`geometry`/`walls`/`rooms`/
`items`/`dialogs`/`mainwindow`, many in free functions (`wall_snap`,
`canvas_rect`, coalesce tolerances) that have no window handle — so threading a
config object through every signature is high churn for a single-window app.
Encapsulate the global instead:

1. Add a small `Settings` wrapper in `config.py` (typed accessors over the dict
   + `load(dict)`/`as_dict()`), and a module-level `active_settings()` accessor
   backed by one current instance (default = `DEFAULT_SETTINGS`).
2. Repoint the free functions to read `active_settings()[…]` (or keep the name
   `SETTINGS` as a property that returns the active instance's dict — minimal
   diff).
3. `MainWindow` owns its `Settings`; on construction/load/new it sets the active
   instance. `load_data`/`SettingsDialog` mutate that instance, not a global.
4. Tests reset via `active_settings()` instead of the `SETTINGS.update(...)`
   save/restore dance in `conftest`.

Outcome: state is encapsulated and explicitly owned, test isolation is clean,
and a second window could swap the active settings on focus. (Full
threading-everywhere de-globalization is intentionally out of scope — modest ROI
for this app.) Module-level *constants* (`EXTERIOR_T`, `WALL_Z`, …) stay as-is.

## Fix plan — #3 Command-based undo (large, higher risk — defer)

Replace whole-document snapshots with `QUndoStack` + `QUndoCommand` subclasses so
cost scales with the edit, not the plan:

1. Add `QUndoStack` to `MainWindow`; wire `undo`/`redo`/enable-state to it.
2. One command per edit family: `AddItems`, `DeleteItems`, `MoveItems`,
   `EditWallEnds`, `EditRoomProps`, `EditOpening`, `Group`/`Ungroup`,
   `ChangeSettings` (and the floor ops once #6 lands). Each captures the minimal
   undo data (serialized form + positions of *affected* items), mutates the
   scene, and on undo/redo restores only those items, re-running a localized
   `rebuild_all_walls`/`refresh_rooms`.
3. Migrate edit paths incrementally — route each mutation through a command,
   keeping the snapshot stack as a fallback until every path is converted, then
   remove it. Pairs with the model layer (a command can mutate model + scene).

**Caveats:** undo correctness is currently bulletproof and this touches every
edit path (high regression risk); the review itself calls snapshot undo "a
scaling ceiling, not a bug." Recommend deferring until after #6, and profiling
the large plan first to confirm the snapshot cost is a felt pain before paying
the migration cost.

## Suggested sequencing (revised)

1. ~~Module split (#1)~~ ✅ · ~~Model layer (#2)~~ ✅ · ~~Packaging (#5)~~ ✅ · ~~Multifloor (#6, Phase 1)~~ ✅
2. **Settings object (#4)** — small, low-risk, improves test isolation. Anytime.
3. **Command-based undo (#3)** — large/risky scaling optimization; defer, profile first.
