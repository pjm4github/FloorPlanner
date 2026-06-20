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

## Suggested sequencing

1. **Module split (#1)** — mechanical, low-risk, unblocks everything else. *(Next session.)*
2. **Model layer (#2)** — introduce dataclasses, move serialization onto the model first.
3. **Multifloor (#6)** — build on the model layer while it's still small.
4. **Command-based undo (#3)** — once the model exists.
5. **Settings object (#4)** and **packaging/pinning (#5)** — independent, can land anytime.
