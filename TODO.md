# TODO — Floors (multi-floor plans), Phase 1

Baseline version: **v1.0** (`APP_VERSION`) · file format → v4 (`FILE_VERSION`)
Targets: **v1.2** (user-facing feature; build on the v1.1 model layer) — bump `APP_VERSION` when it lands.

> **Resuming:** open a new session and say *"Read TODO.md and build the Floors
> feature (Phase 1) per the plan."* All design decisions below are already
> locked with the user; go straight to implementation (the plan lists the order).
> Run `python -m ruff check .` and `python -m pytest` after changes. Commit/push
> only when asked. Never commit personal files (`floorplan*.json`,
> `layout_wiscaway.csv`, `snip.png`, `trial-export-rooms.csv`).
>
> **DEPENDS ON the model layer (`REFACTOR_PLAN.md` Phase A).** This plan is
> reconciled to the plain-Python model: the floor **roster** and **serialization**
> live in the `Project`/`Floor` dataclasses (`model.py`), not in bespoke
> `serialize()`/`load_data()` code or `MainWindow` dicts. Build Phase A first.
> What the model owns: the floor list, `active_floor`, the v3→v4 file migration,
> and per-item `floor` round-tripping (all Qt-free + unit-tested in
> `test_model.py`). What stays runtime Qt (unchanged from the original design):
> the live per-item `.floor` tag the scene edits, the geometry/render/visibility
> filters, and the menu/status-bar UI.

## Context

The editor is single-storey. Add **floors**: every wall/room/furnishing/stair/
group belongs to a floor; you edit ONE active floor at a time; other floors are
hidden or shown as a gray non-editable backdrop ("reference") for tracing/
alignment. Phase 1 is the full vertical slice: floor data model, per-item floor
tagging, floor-scoped room detection + coalesce/weld/junctions, gray rendering +
visibility, a Floors menu + status-bar indicator, serialization/undo.
(Duplicate-floor, move-items-between-floors, stacking view = Phase 2.)

Single file: `FloorPlanner.py`. Tests in `tests/`.

### Locked decisions (from the user)
1. **True gray tint** for non-active (reference/ghosted) floors — repaint flat
   gray, not opacity fade.
2. **Active + reference floors visible** by default; other floors hidden unless a
   "Show other floors (ghosted)" toggle is on.
3. **New floor starts empty** (duplicate-from-existing is Phase 2).
4. **Switch via the Floors menu + a status-bar indicator** of the active floor.

---

## Design

### Module state (a runtime CACHE the paint()/detection hot paths read)
```
DEFAULT_FLOOR = "default"
ACTIVE_FLOOR = "default"        # the one editable floor
REFERENCE_FLOORS = set()        # floors shown as a gray backdrop
SHOW_OTHER_FLOORS = False       # ghost the rest in gray (else hidden)
```
These globals are **not** authoritative — they're a fast, window-handle-free
mirror so `paint()`/detection avoid a lookup. The **authoritative roster is the
model**: `MainWindow.floors` is a `list[Floor]` (the `Floor` dataclass from
`model.py`, `{name, reference}`) and `MainWindow.active_floor` is a name. A single
`_sync_floor_state(self)` mirrors `self.floors`/`self.active_floor` into the
globals and calls `apply_floor_visibility(self.scene)` + `self.scene.update()`.
At serialize time `project_from_scene()` reads `self.floors` into
`Project.floors` (an empty floor has no scene items, so the roster MUST be stored,
not re-derived from items); at load time `apply_project_to_scene()` writes
`project.floors` back to `self.floors` and calls `_sync_floor_state`.

`floor_display_mode(floor) -> "active" | "reference" | "ghost" | "hidden"`
(active==ACTIVE_FLOOR; reference if in REFERENCE_FLOORS; else ghost if
SHOW_OTHER_FLOORS else hidden).

### Per-item floor (auto-tag via the module global — minimal threading)
`WallItem`/`RoomItem`/`FurnishingItem.__init__` set `self.floor = ACTIVE_FLOOR`,
so any item created while floor F is active (drawn, pasted, synthesized,
privatized, fractured) is tagged F automatically — no threading through the many
creation sites. `OpeningItem` has no own floor (uses `self.wall.floor`).
`GroupItem`: tag `self.floor` when grouping; require members on one floor.
**Load overrides** each item's `floor` from the file, so the default is
irrelevant there. Where a wall is *derived from a specific wall*
(`synthesize_room_edge`, `_privatize_shared_walls`, `fracture_delete_wall`,
`duplicate_wall`) also set `new.floor = src.floor` explicitly.

### Floor-scoped geometry — filter checklist (every wall-iterating site)
Detection has ONE choke point (grid+graph build); the rest are coalesce/weld/
junction neighbour scans. Add a `w.floor == ACTIVE_FLOOR` (or `== wall.floor`)
guard to each:
- `_RoomGrid.__init__` (~1137) and `_WallGraph.__init__` (~1242): only
  `w.floor == ACTIVE_FLOOR` → detection is naturally floor-scoped.
- `refresh_rooms` (~1465): only re-detect rooms with `room.floor == ACTIVE_FLOOR`;
  build `_WallBBoxIndex(scene, ACTIVE_FLOOR)`.
- `coincident_walls` (~885): skip `w.floor != wall.floor` (coalesce on one floor).
- `nearest_wall_endpoint`/`nearest_wall_body` (weld helpers ~701/715): skip
  other-floor walls.
- `_compute_wall_junctions` (~1544): union only same-floor neighbours.
- `bind_room_walls` (~4501): filter `band_walls`/`_wall_along_segment` to
  `room.floor`.
- `_WallBBoxIndex.__init__` (~1418): optional `floor=None` param.
`rebuild_all_walls`/`_compute_wall_junctions` still iterate all walls for geometry
caches (cheap, floor-independent); only the neighbour unions/queries are filtered.

### Rendering (true gray tint)
In each `paint()`, `mode = floor_display_mode(self.floor)` (`OpeningItem` uses
`self.wall.floor`). `mode == "active"` → existing colors; else flat gray
(`FLOOR_GHOST` ≈ `QColor(176,176,176)` ink/fill, fainter for room fill) and skip
the selection highlight. Walls keep `_outline_clip`; just swap the color when
ghosted. `PlanView` is `FullViewportUpdate`, so `scene.update()` on switch
repaints everything.

### Visibility + interactivity
`apply_floor_visibility(scene)`: per top-level item, `mode = display_mode`;
`it.setVisible(mode != "hidden")`; `it.setEnabled(mode == "active")` (disabled
QGraphicsItems get no mouse events and propagate to children, so only the active
floor is editable). Call on switch, after load, and on reference/show-others
toggle.

### Menus + status bar
- New top-level **`&Floors`** menu in `_build_menus` (~5629), before `&Help`:
  `New floor…` (asks a name), separator, then one **submenu per floor** titled
  `"{name}{ (R)}{ ●}"` with: `Edit this floor` (sets active; ●=active),
  `Rename…`, `Reference floor` (checkable → REFERENCE_FLOORS + "(R)"),
  `Delete floor` (refuse the last floor; confirm, then delete that floor's items).
  Separator, then `Show other floors (ghosted)` checkable. `_rebuild_floor_menu()`
  repopulates after any change. Reuse the existing checkable/`QActionGroup`
  pattern.
- **Status bar**: a permanent `QLabel` "Floor: {active}" (next to `coord_label`,
  ~5535); clicking it pops a small floors menu for quick switch. Updated by
  `_sync_floor_state`.

### Serialization / undo (delegated to the model — keep floor-SWITCHING out of undo/dirty)
Serialization is **handled by `model.py`, not bespoke `serialize()`/`load_data()`
code** (Phase A already routes both through `Project`). The Floors-specific work
here is just to extend the model and the scene↔model bridge:
- **`model.py` (Phase A):** `Project` carries `floors: list[Floor]`; `Wall`/`Room`/
  `Furnishing` each carry `floor` (default `"default"`). `Project.to_dict()` emits
  `"floors"` + per-item `"floor"`. **`active_floor`/`show_other_floors` are NOT in
  `to_dict()`** — they're view state, so a floor switch must not change the snapshot
  (no spurious undo step, no false "unsaved"). `FILE_VERSION` 3 → 4.
- **Migration lives in `Project.from_dict()` (Qt-free, unit-tested):** v1–v3 files
  (no `floors`/`floor`) → one `Floor(DEFAULT_FLOOR)`, every item `floor="default"`.
- **Bridge:** `project_from_scene()` packs `self.floors` + each item's `.floor` into
  the `Project`; `apply_project_to_scene()` restores `self.floors`/per-item `.floor`
  and calls `_sync_floor_state`.
- **`_write_plan`/`save_path`:** add `state["active_floor"] = self.active_floor`
  *after* `to_dict()` so the file remembers it (still out of undo/dirty);
  `Project.from_dict` reads optional `active_floor`, default = first floor.
- **Undo invariant unchanged:** add/rename/delete/reference-toggle a floor mutates
  `self.floors` → changes `to_dict()` → undoable + dirty; plain switching only
  touches `active_floor` (view state) → not. Undo round-trips via the bridge;
  `_restore_state` passes `keep_backdrop`; `_sync_floor_state` restores visibility.

---

## Implementation order (land + green-test in chunks)
0. **Prereq — `REFACTOR_PLAN.md` Phase A model layer must already exist.** Extend it
   for floors: add `Floor` dataclass + `Project.floors`/`active_floor`; per-item
   `floor` field; v3→v4 migration in `Project.from_dict`; Qt-free tests in
   `test_model.py`. (This subsumes the old "serialization v4" step.)
1. Module state + `floor_display_mode`/`apply_floor_visibility`/`_sync_floor_state`;
   per-item `floor` defaults; `MainWindow.floors` (`list[Floor]`)/`active_floor` init;
   bridge reads/writes them in `project_from_scene`/`apply_project_to_scene`.
2. Floor-scoped geometry filters (the checklist) — verify single-floor behaviour
   unchanged (one floor named "default").
3. Rendering gray tint + visibility/enabled.
4. `_write_plan` writes `active_floor` after `to_dict()`; confirm switch ≠ dirty/undo
   while add/rename/delete/reference-toggle ARE (most of v4 is done in step 0).
5. Floors menu + status-bar indicator + ops (new/rename/reference/delete/switch/
   show-others).

---

## Tests (new `tests/test_floors.py`, plus additions)
- New items get `ACTIVE_FLOOR`; switching active floor changes
  `floor_display_mode` and item `setEnabled`/`setVisible` (active editable,
  reference visible+disabled, others hidden; show-others reveals them ghosted).
- **Floor isolation**: two walls at the same coords on different floors do NOT
  coalesce, weld, or junction-merge; a room on floor B is bounded only by floor-B
  walls; detecting a room ignores other-floor walls (area correct).
- **Model (`test_model.py`, Qt-free):** `Project` round-trips `floors` + per-item
  `floor`; a v3 dict migrates to one `default` floor with all items tagged
  `default`; `active_floor` stays out of `to_dict()`.
- **Switching floors does NOT mark dirty and does NOT create an undo step**
  (`serialize()` unchanged across a switch); renaming/adding/deleting DOES.
- Undo round-trips floor edits; the saved file remembers `active_floor`.
- Existing suite stays green (single-floor plans behave exactly as before).

## Verification
- `python -m ruff check .`; `python -m pytest -m "not gui"` then full `pytest`.
- Manual (`python FloorPlanner.py`): draw a plan on "default"; Floors ▸ New floor
  "Upper"; switch (status bar shows "Floor: Upper") — first floor hidden; mark
  "default" Reference → it shows gray as a tracing backdrop; draw on Upper aligned
  to it; toggle "Show other floors" → both ghosted; switch back — Upper hidden;
  one floor's walls never affect the other (coalesce/weld/detect). Save, reopen
  (on the saved active floor), undo/redo across floor edits. Load an existing
  single-floor `.json` → one "default" floor, intact. Switch floors repeatedly →
  no unsaved-changes star, no spurious undo steps.
