# REFACTOR PLAN — Model layer (#2) then Package split (#1)

Baseline version: **v1.0** (`APP_VERSION`) · file format v3 → v4 (`FILE_VERSION`)
Targets: **v1.1** (structural; no user-facing feature) — bump `APP_VERSION` when it lands.

> Source: `CODE_REVIEW.md` findings **#2** (no separation between domain model
> and Qt) and **#1** (single 8,037-line module). The user asked to do the
> **model layer first**, then the **package split** on top of it — the reverse of
> the review's suggested sequencing, and the better order: once serialization
> runs through a Qt-free model, the eventual `io` module is a thin wrapper and
> the split's riskiest seam (IO ↔ every item) is already clean.
>
> Guardrail for every step: `python -m ruff check .` then `python -m pytest`
> must stay green. Commit/push only when asked. Never commit personal files
> (`floorplan*.json`, `layout_wiscaway.csv`, `snip.png`, `trial-export-rooms.csv`).

---

## Where the entanglement actually is (verified against the code)

Domain state lives directly on Qt graphics items; the scene **is** the model:

| Item (line) | Domain state carried |
|---|---|
| `WallItem` (1579) | `p1, p2, wall_type, rooms[], openings[], is_open` (`floor` planned) |
| `OpeningItem` (2148) | `kind, code, s, door_type, swing`, parent `wall` |
| `RoomItem` (2422) | `name, anchor, label_offset, show_dims, properties{}, corners` |
| `FurnishingItem` (3578) | `kind, pos, rotation, extra_state()` |
| `StairItem` (3764) | subclass of `FurnishingItem` |
| `GroupItem` (3986) | `QGraphicsItemGroup` of the above |

The two choke points that convert between scene and dict:
- `MainWindow.serialize()` (6439) — walks `self.scene.items()`, emits the documented JSON.
- `MainWindow.load_data()` (6493) — clears the scene and rebuilds items from a dict,
  then `coalesce_all` → `rebuild_all_walls` → room re-detection.

`serialize`/`load_data` are also the **undo** path (`_commit_if_changed`/`_restore_state`),
so they are well-exercised and a safe place to insert a model in the middle.

The compatibility surface that must NOT break: every test, plus
`docs/make_gallery.py`, `examples/make_examples.py`, `tests/bench_rooms.py`, all do
`import FloorPlanner as FP` and reach for `FP.WallItem`, `FP.SETTINGS`,
`FP.rebuild_all_walls`, `FP.detect_room`, `FP.RoomItem`, `FP.MainWindow`, … The
`FloorPlanner` name must keep exposing the full current public API after both phases.

---

# PHASE A — Plain-Python model layer (finding #2)

Goal: a Qt-free dataclass model that is the **single definition of the JSON schema**,
with `serialize()`/`load_data()` rerouted through it. Behavior-identical; the win is
that the schema + version migration become unit-testable without a `QApplication`,
and the later `io` split (and the Floors feature) drop onto a clean seam. The deeper
"move coalesce/detect/bind logic onto the model" is explicitly **out of scope here** —
the review calls it incremental ("over time"); we set up the seam, not the migration.

### A1. `model.py` — dataclasses mirroring the dict exactly
Coordinates as plain `(x, y)` tuples (no `QPointF`) so the module imports **zero Qt**.

```
@dataclass
class Opening:    kind, code, s, door_type, swing
@dataclass
class Wall:       wall_type, p1, p2, rooms: list[str], openings: list[Opening], floor="default"
@dataclass
class Room:       name, anchor, label_offset, show_dimensions, properties: dict
@dataclass
class Furnishing: kind, pos, rotation, extra: dict          # extra == extra_state()
@dataclass
class Floor:      name, reference=False                      # forward-compat (finding #6 / TODO)
@dataclass
class Project:    version, units, settings: dict, walls, rooms, furnishings,
                  floors=[Floor("default")], active_floor="default"
```

Each gets `to_dict()` / `from_dict()` that reproduce the **current** JSON byte-for-byte
(same keys, same sort order as `serialize()`: walls by `(p1,p2,type,tuple(rooms))`,
rooms by name, furnishings by `(pos,kind,rotation)`). `Project.from_dict` owns the
**version migration** (v1–v3 → current), mirroring the existing geometry-rebind logic's
spirit but on plain data; unknown/old files default `floor="default"`, one `Floor`.

### A2. Scene ↔ model bridge (the only Qt-touching part of the seam)
Two functions on `MainWindow` (or a small `_scene_bridge` helper):
- `project_from_scene() -> Project` — exactly the body of today's `serialize()` loop,
  but emitting dataclasses instead of dicts. `is_open` walls still skipped;
  `extra_state()` → `Furnishing.extra`.
- `apply_project_to_scene(project)` — exactly the body of today's `load_data()`
  (settings apply, keep-backdrop dance, build `WallItem`/`OpeningItem`/`RoomItem`/
  furnishings, `coalesce_all` → `rebuild_all_walls` → room detection).

### A3. Reroute the choke points (behavior-preserving)
- `serialize()` becomes `return self.project_from_scene().to_dict()`.
- `load_data(data, keep_backdrop)` becomes
  `self.apply_project_to_scene(Project.from_dict(data), keep_backdrop)`.
- `_write_plan`/`save_path` still add `state["active_floor"]` after `to_dict()`
  (kept out of `serialize()` so floor-switching doesn't dirty/undo — matches TODO.md).

### A4. Tests — `tests/test_model.py` (NO `QApplication` needed)
- Round-trip: `Project.from_dict(d).to_dict() == d` for a representative plan dict.
- Version migration: a v1/v2/v3 dict loads to one `default` floor, every item tagged.
- Schema stability: keys + sort order match a frozen sample (guards the rewrite).
- Existing IO/undo tests stay green (they prove the bridge preserves behavior).

**Decision flagged to the user (do not resolve silently):** the pending Floors
feature (`TODO.md`) currently plans a **module-global `ACTIVE_FLOOR` + per-Qt-item
`.floor`** approach. If the model layer lands first, Floors should instead live in
`Project.floors` / `Floor` (finding #6), which is the whole point of #2 → #6. These
two designs conflict. Recommend: land Phase A, then **revisit TODO.md** so Floors is
built on the model, not on Qt-item tagging. (Phase A includes `Floor`/`active_floor`
as forward-compat fields so this is a small step, not a rewrite.)

---

# PHASE B — Package split (finding #1)

Goal: turn the 8,037-line `FloorPlanner.py` into a `floorplanner/` package with clean
seams, while `import FloorPlanner` keeps exposing the full API. Mechanical and
low-risk **if** done leaf-first with the test suite run after every move.

### B0. The two hazards to manage up front
1. **The shared mutable globals.** `SETTINGS`/`DEFAULT_SETTINGS` (finding #4) and the
   constants (`EXTERIOR_T`, `WALL_Z`, `OPENING_Z`, `GRID_MAJOR`, `FILE_VERSION`,
   `FILE_FORMAT`, the planned `ACTIVE_FLOOR`…) are read across the whole module. They
   must live in **one** module (`floorplanner/config.py`) and be **imported**, never
   duplicated — duplication would split `SETTINGS` into two objects and silently break
   settings/undo. Everything imports `from .config import SETTINGS` (same object).
2. **The walls ↔ rooms cycle.** `rebuild_all_walls` → `refresh_rooms` → `detect_room`
   iterates `WallItem`s; `RoomItem.bind_wall` mutates `WallItem.rooms`. Verified the
   real dependency is **one-way**: `rooms` imports `walls`; `WallItem.rooms` just holds
   room objects **duck-typed** (no import of `RoomItem` needed). Keep it that way — do
   not add a `walls → rooms` import. If one creeps in, break it with a late import.

### B1. Target layout (compatibility shim is the keystone)
```
floorplanner/
  __init__.py      # re-exports the full public API (star-import each submodule)
  config.py        # paths, QSettings, SETTINGS/DEFAULT_SETTINGS, constants, fonts/icons
  model.py         # (from Phase A) Qt-free dataclasses + dict migration
  geometry.py      # grid_snap, wall_snap, line_intersection, dist_point_segment,
                   #   _merge_intervals, axis_wall_intersection, fmt/parse helpers
  walls.py         # WallItem, OpenWall, _WallIndex, coincident/coalesce/weld/fracture,
                   #   _compute_wall_junctions, _WallBBoxIndex, rebuild_all_walls
  rooms.py         # RoomItem, _RoomGrid, _WallGraph, detect_room/refresh_rooms,
                   #   bind_room_walls and room-edge helpers
  items.py         # OpeningItem, FurnishingItem, StairItem, GroupItem,
                   #   ReferenceImageItem, make_furnishing
  catalog.py       # furnishing_catalog/spec/groups/renderer, pricing (anthropic_fetch_prices…)
  dialogs.py       # Inventory/RoomProperties/Settings/ImageImport/AIPricing/About dialogs
  view.py          # PlanView
  mainwindow.py    # MainWindow  (+ serialize/load_data bridge from Phase A)
  macro.py         # MacroRunner, MacroRecorderDialog
  app.py           # main()
FloorPlanner.py    # shim: `from floorplanner import *` + `main` passthrough so
                   #        `python FloorPlanner.py` and `import FloorPlanner` both work
```

### B2. Extraction order (leaf → root; green-test after each)
1. `config.py` (constants + `SETTINGS` + paths/fonts/icons). Have `FloorPlanner.py`
   import from it. Run tests — proves the shared-globals plumbing.
2. `geometry.py` (pure helpers; depends only on Qt geometry + config).
3. `catalog.py` (furnishing catalog/pricing; near-leaf).
4. `walls.py`, then `rooms.py` (rooms imports walls — one-way per B0.2).
5. `items.py` (openings/furnishings/group/reference-image; duck-typed refs to walls/rooms).
6. `dialogs.py`, `view.py`.
7. `macro.py`.
8. `mainwindow.py` (largest; pulls in all of the above + the Phase-A bridge).
9. `app.py` `main()`; reduce `FloorPlanner.py` to the shim.

Each step: cut the class/functions into the new module, add the imports it needs,
let the old file import the names back (so the shim stays whole), `ruff` + `pytest`.

### B3. `__init__.py` / shim contract
- Each submodule declares `__all__`; `__init__.py` does `from .module import *` for all,
  re-exposing the union as the `floorplanner` (and via the shim, `FloorPlanner`) API.
- `FloorPlanner.py`:
  ```python
  from floorplanner import *          # noqa: F401,F403
  from floorplanner.app import main
  if __name__ == "__main__":
      main()
  ```
- Acceptance: `tests/`, `docs/make_gallery.py`, `examples/make_examples.py`,
  `tests/bench_rooms.py` all run unchanged. `python FloorPlanner.py` launches the app.

### B4. Packaging hygiene (folds in finding #5, cheap once split)
Add `pyproject.toml` with metadata + a `console_scripts = floorplanner = floorplanner.app:main`
entry point and a **pinned** `PyQt6==<current>`; keep `requirements-dev.txt` for tests.
(Independent of the split; land alongside B3 or right after.)

---

## Sequencing & risk

1. **Phase A** (model layer) — small, isolated, adds Qt-free tests; reversible.
2. **Decision gate** — reconcile `TODO.md` Floors with the model (recommend model-based).
3. **Phase B** (split) — mechanical, one module at a time, suite green throughout.
4. Then resume the Floors feature on the new foundation.

Findings deliberately **out of scope** here (review's later items, each independent):
**#3** command-based undo, **#4** settings-as-object (we only *centralize* `SETTINGS` in
`config.py`, not de-globalize it), **#6** full multifloor (Phase A only adds the fields).
Minor repo-clutter items (`snip.png`, `trial-export-rooms.csv`, `.idea/workspace.xml`)
can be gitignored anytime.
