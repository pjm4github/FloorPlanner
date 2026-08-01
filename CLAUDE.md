# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

- The app is the **`floorplanner/` package** (PyQt6 QGraphicsScene editor). Run with `python FloorPlanner.py` (a compatibility shim) or the `floorplanner` console script. `import FloorPlanner` still works — the shim re-exports the whole package API, so `fp.WallItem`, `fp.SETTINGS`, etc. resolve regardless of which submodule they live in.
- **Module layout** (dependency order, low → high): `config.py` (constants + the shared mutable `SETTINGS` + path/font/icon helpers) · `geometry.py` (pure coord/format helpers + item-stacking) · `catalog.py` (furnishing library + AI pricing) · `model.py` (Qt-free dataclasses — the single definition of the JSON schema; `Project.to_dict`/`from_dict` own version migration) · `walls.py` (`WallItem`/`OpeningItem` + wall-network algorithms) · `rooms.py` (`RoomItem` + outline/binding + room-edge helpers; the detection ENGINE went at P3.5 — `detect_room` survives as a one-shot lift to `Design`) · `items.py` (furnishings/stairs/groups/reference-image) · `dialogs.py` · `view.py` (`PlanView` + palette) · `macro.py` · **`planio.py` / `csvio.py` / `imageio.py` / `levels.py`** (mixins split out of `MainWindow` at P2.5 — plan open/save/export incl. the scene↔document bridges, room-CSV import/export, reference-image import + wall extraction, and the floor roster) · `mainwindow.py` (`MainWindow` = UI wiring + edit orchestration, inheriting those four mixins) · `app.py` (`main()`).
  - The four are **mixins, not delegating wrappers**, so every call site and test still resolves `win.serialize()`, `win._import_rooms(...)`, `win.switch_floor(...)` unchanged — the split is internal structure, invisible at the API. Add a method to the module that owns its concern, not to `MainWindow`.
  - Three payload methods live in `planio.py` and are deliberately distinct: `snapshot()` (canonical v5 doc — undo + dirty), `design_document()` (what gets written: snapshot + provenance + unmodelled settings + `active_floor`), and `serialize()` (legacy v4, **only** for File ▸ Export legacy v4). Submodules use Qt + lower-layer **star imports**; the `walls↔rooms` cycle is broken with 4 late (function-local) imports. When adding cross-module refs, keep the import direction acyclic (items←walls←rooms; UI imports the scene layer) and use a late import only to close a genuine cycle.
- Scene units are **inches** (1 scene unit = 1 inch). Canvas size comes from `SETTINGS` via `canvas_rect()`.
- **Shared-wall model:** a `WallItem` carries a list `rooms` (the rooms it borders); on a boundary between two rooms there is **one** shared wall, not a duplicate per room. `RoomItem.bind_wall`/`unbind_wall` add/remove the association without stealing or deleting. **A CORNER IS ONE `Vertex` (Phase 3, merged at `03f3868`)** that the walls *and* the room outlines hold, so moving it moves everything on it — which is why there is no re-detection pass and no coalesce family any more. Overlapping collinear same-type walls **merge** (`merge_wall` / `merge_all`), ends **weld** onto a shared corner (`weld_wall_ends` / `weld_scene`), and Edit ▸ Coalesce all walls now is the explicit plan-wide pass (`normalize_walls` = merge + weld + split); `SETTINGS["auto_coalesce"]` still gates the automatic half. Grouped walls never merge (the `group() is None` guard). Deleting a wall is genuinely deletion since P4.1 (`delete_wall` — the fracture family is gone): the room survives via its stored outline and the vacated edge becomes an open edge. **Still on the old shape, and each dies in Phase 4:** moving a room privatizes its shared walls (`_privatize_shared_walls`, → P4.2); grouping a room *alone* duplicates its walls into the group (`duplicate_wall`, → P4.5, and the source of defect 23's stranding).
- **Floors (multi-floor; `FILE_VERSION = 4` is the LEGACY v4 writer, kept for File ▸ Export legacy v4 — the app reads and writes **v5 `floorplanner-design`** since P2.2):** every `WallItem`/`RoomItem`/`FurnishingItem`/`GroupItem` carries a `floor` (auto-tagged with the active floor via `active_floor()` at creation; `OpeningItem` uses `self.wall.floor`). The authoritative roster is `MainWindow.floors` (`model.Floor` dataclasses) + `self.active_floor`; `_sync_floor_state()` mirrors it into config's **runtime cache** (a mutable dict behind `active_floor()`/`set_floor_state()`/`floor_display_mode()` — NOT a bare global, because star-imports snapshot rebindable strings). You edit ONE active floor; the geometry hot paths (`face_at`/`coincident_walls`/`nearest_wall_*`/`_compute_wall_junctions`/`bind_room_walls`/`_WallBBoxIndex`) all filter to the relevant floor so floors never interact — and `design_from_scene`/`face_at` are level-scoped *by construction* (levels outer, items inner) rather than by a filter. `paint()` flat-grays non-active floors (`floor_display_mode`); `apply_floor_visibility` hides/disables them. The model emits `floors` + per-item `floor`; `active_floor` is **view state** — kept OUT of `serialize()` (so switching floors isn't undoable/dirty) but written to the file by `_write_plan`. v1–v3 files migrate to one `default` floor.
- Headless macro tool (for AI/script-driven edits): the in-app hook is `MainWindow.run_macro()` / `MacroRunner` plus `export_canvas`/`load_path`/`save_path`/`scene_summary`; the driver is `fp_macro.py`. Token grammar is in `docs/macro_language.md`. Note: don't synthesize Ctrl-modified key events headlessly — it leaks `QApplication.keyboardModifiers()`; route shortcuts/arrows through app methods (as `MacroRunner` does).
- PNG → plan extractor: `fp_extract.py` (numpy + `QImage`, no OpenCV/Pillow). Detects rectilinear walls and writes `floorplanner-json`. Gotchas: a `QApplication` must exist before `QImage` decodes a PNG (image plugins); keep the `QApplication` alive in a module global (a local gets GC'd and crashes `MainWindow`); copy QImage buffers into numpy (`arr.copy()`) — a view into the freed `QImage` segfaults. Its `setup_app()` sets the app font, so in-process tests use the conftest app/module (the `fp` fixture), not `setup_app()`.

## Starting a session

Read **`docs/SESSION_SNAPSHOT.md`** first: where the work stands, what to read in
what order, the rules that bind it, and the traps that waste time. It is an index
and a state marker — where it points at another document, that document wins.

## v5 migration (in progress)
The file format and domain model are moving to `floorplanner/design/design-schema.v5.json` (vendored at P0.7; pointer at `docs/design-schema.v5.md`).
Read `docs/V5_MIGRATION_PLAN.md` before changing walls/rooms/items/mainwindow —
it says which code is being deleted and in which phase. `OpenWall` and its
`is_open` flag went at P3.7 — an open side is an outline edge no wall spans
(`RoomItem.open_edges()`), drawn dashed by the room itself; there is no
placeholder item and nothing to filter out of a wall query. `coalesce_*` /
`weld_all` went at P3.4 (use
`merge_wall` / `merge_all` / `weld_scene` / `normalize_walls`); the room-detection
engine went at P3.5 (`detect_room` now lifts the scene to a `Design` and asks
`topology.enclosing_face`; `refresh_rooms` is gone entirely).

## Generated assets — never hand-edit

- Everything under `assets/` (tool icons, 56 furnishing SVGs, `manifest.json`, `groups.json`) is generated by `_gen_assets.py`. To change or add artwork, edit `_gen_assets.py` and run `python _gen_assets.py`.
- Furnishing SVG viewBox is in inches and equals the item's real-world footprint; `manifest.json` carries `width_in`/`depth_in` plus a `price` (USD purchase cost, filled in at runtime by the AI ▸ Update furnishing prices… tool; `_gen_assets.py` preserves existing prices across regeneration). The app loads catalogs dynamically — adding a symbol needs no app-code change.

## Performance

- **Room detection is no longer on the edit path at all (P3.5).** `rebuild_all_walls` used to end in `refresh_rooms`, which re-detected every room whose nearby walls had changed — a raster flood-fill plus a planar face walk, with a memo (`room_signature`) in front of it to keep the cost down. All of it is deleted. A `RoomItem`'s `path` and `area_sqft` **derive** from its `outline`, and the outline's corners are the very `Vertex` objects the walls hold, so a wall move updates the rooms it borders by construction. Measured effect on the P0.3 harness at 64 rooms: `bake` 299 ms → 28 ms, `rebuild` 3.7 ms → 2.4 ms. What remains: `rebuild` takes a shared `_WallIndex` so `coincident_walls`/`_joined_at` are O(local). Don't memoize the wall *path* build — profiled as already cheap; the cost is the neighbour queries. `tests/bench_rooms.py` measures it.
- "Detect room here" (the Room tool, CSV import, macro `room`, paste, legacy load) is `rooms.detect_room` → `design.bridge.face_at` → `topology.enclosing_face`: a **one-shot lift** of the level's walls into a `Design`. That is deliberately the opposite of the rule for edit ops (P3.4 forbids lift-to-Design there, because a per-event full-plan rebuild destroys item identity) — a detection is one user gesture, so it can afford the walk and gets one shared definition of "what is a face" instead of a second one in the editor.
- The view (`PlanView`) uses `FullViewportUpdate` — **every** change repaints all ~N items, so anything that fires per-event on a big plan is costly. Mouse-wheel zoom is **coalesced**: `wheelEvent` accumulates `angleDelta` and a one-shot 16 ms timer applies one `scale()` in `_apply_zoom`. Without this, a high-res wheel/trackpad emits dozens of events per notch → dozens of full repaints → multi-second stalls on a large plan. Keep any new per-event view work off the synchronous path. `tests/test_view.py` guards the coalescing.
- Walls render as one solid network: each `WallItem` fills its body with **no pen** (overlapping greys merge seamlessly) and draws its dark outline **clipped** to its bounds minus neighbouring wall bodies, so T/cross/L junctions have no inner seam. The clip (`_outline_clip`) is cached by `_compute_wall_junctions(scene)` — a single pass at the end of `rebuild_all_walls`, after every wall's `_solid` footprint is current (it needs all neighbours up to date, so it can't live in per-wall `rebuild()`). Uses the `_WallBBoxIndex` for O(local) neighbour lookup. Don't move junction work into `paint()` — path booleans per repaint would stall.

## Linting

Run `python -m ruff check .` after edits; config is `ruff.toml` (E402 is suppressed in headless scripts because `QT_QPA_PLATFORM` must be set before Qt imports).

## Tests

`pytest` suite in `tests/` (headless; conftest owns the QApplication). Install with `pip install -r requirements-dev.txt`.

- `pytest` runs everything; `pytest --quick` skips the `slow`+`gui` markers for fast feedback.
- Tests are tagged by category (`geometry`, `walls`, `rooms`, `groups`, `io`, …); select/skip with `-m`, e.g. `pytest -m "not gui"`. Markers are registered in `pytest.ini`; see `tests/README.md`.
- Prefer the bare `scene` fixture over `win` (full MainWindow) when the UI isn't needed — much faster.
- When fixing a bug, add a regression test (the group GC + wall-drag bugs live in `test_groups.py`).

## Headless testing pattern (for one-off scratch scripts)

When a throwaway repro is quicker than a test, use this pattern:

- Set `os.environ["QT_QPA_PLATFORM"] = "offscreen"` before importing PyQt6; create `QApplication([])` before `import FloorPlanner`.
- Anything that can raise a modal `QMessageBox` hangs headless — use the `interactive=False` parameter on methods like `_import_rooms`/`_export_rooms` (errors land in `self._import_errors`).
- Console is cp1252: never print `≈`, `×`, or other non-ASCII in test output.
- Pixel assertions on antialiased 1-px lines need a lenient threshold (e.g. `< 190`, not `< 100`).
- `QTest.mouseMove` does not synthesize button-held drags; build `QMouseEvent`s with `buttons=Qt.MouseButton.LeftButton` and send via `QApplication.sendEvent` to the view's viewport.
- Delete throwaway test scripts when done.

## Screenshots / feature gallery

Regenerate with `python docs/make_gallery.py` — builds one demo plan and writes the hero `docs/screenshot.png` plus a per-feature gallery in `docs/gallery/` (canvas shots + dialog shots). When a feature changes the UI, update the relevant gallery shot there (don't hand-edit PNGs).

## Repo etiquette

- Commit and push **only when explicitly asked**.
- Never commit the user's plan files: `floorplan*.json`, `layout_wiscaway.csv` (gitignored).
- `gh` is not on PATH in this environment; call it as `& "C:\Program Files\GitHub CLI\gh.exe"`.
