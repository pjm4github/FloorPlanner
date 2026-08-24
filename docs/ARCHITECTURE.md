# Architecture — module layout, phase history, and the mechanics `CLAUDE.md` no longer restates

**Moved out of `CLAUDE.md` by [`handoff/0085-ruling.md`](handoff/0085-ruling.md):**
that file is now traps only — things a competent reader would get *wrong*
from the code, not things they would only get *slowly*. This document is the
"slowly" material: still true, still useful, just not reloaded on every turn.
Nothing here is a second source of truth — where it disagrees with the code,
the code wins.

## Module layout (dependency order, low → high)

`config.py` (constants + the shared mutable `SETTINGS` + path/font/icon
helpers) · `geometry.py` (pure coord/format helpers + item-stacking) ·
`catalog.py` (furnishing library + AI pricing) · `model.py` (Qt-free
dataclasses — the single definition of the JSON schema; `Project.to_dict`/
`from_dict` own version migration) · `walls.py` (`WallItem`/`OpeningItem` +
wall-network algorithms) · `rooms.py` (`RoomItem` + outline/binding +
room-edge helpers) · `items.py` (furnishings/stairs/groups/reference-image) ·
`extract.py` (extract/join — rooms as movable units; above `items` because a
floating room carries its furnishings; `rooms.py` reaches it by late import,
the `dialogs` pattern) · `dialogs.py` · `view.py` (`PlanView` + palette) ·
`macro.py` · `planio.py` / `csvio.py` / `imageio.py` / `levels.py` (mixins
split out of `MainWindow` — plan open/save/export incl. the scene↔document
bridges, room-CSV import/export, reference-image import + wall extraction,
and the floor roster) · `mainwindow.py` (`MainWindow` = UI wiring + edit
orchestration, inheriting those four mixins) · `app.py` (`main()`).

Every module carries this same information in its own docstring — this
roster is a map for someone who hasn't opened any of them yet, not a second
copy to keep in sync. Submodules use Qt + lower-layer star imports; the
`walls↔rooms` cycle is broken with a handful of late (function-local)
imports. Keep the import direction acyclic (`items ← walls ← rooms`; UI
imports the scene layer) and use a late import only to close a genuine cycle.

## Phase history — what changed, and when

The codebase carries phase markers (`P0.1`, `P3.5`, `P4.2`, …) in comments
and commit messages throughout. **`docs/V5_MIGRATION_PLAN.md`** is the
authoritative phase-by-phase account — status table, specs, sequencing
rationale. **`docs/progress/`** is the contemporaneous, verbatim log, split
by phase. Neither is restated here; this section exists only to say where to
look, since `CLAUDE.md` used to carry fragments of both inline.

## Extract / join — rooms as movable units

Fully documented in `extract.py`'s own module docstring: `extract_room`
lifts a placed room out of the shared wall network (`placed → floating`) so
it can move as one closed unit; `join_room` is the inverse. Both are built
ON the existing merge/split/weld machinery, not beside it. I12 (a floating
room shares no wall and no vertex with the plan) holds by construction. A
placed room's label-drag **is** extract → move → join through those ops. A
floating room paints distinctly and the document walk folds it in its own
vertex namespace (I14 exempts floating-vs-plan pairs).

**Still on the old shape:** grouping a room *alone* duplicates its walls
into the group (`duplicate_wall`) — a known gap, not yet closed.

## Floors (multi-floor)

`FILE_VERSION = 4` is the legacy v4 writer, kept only for File ▸ Export
legacy v4 — the app reads and writes v5 `floorplanner-design`.

Every `WallItem`/`RoomItem`/`FurnishingItem`/`GroupItem` carries a `floor`
(auto-tagged with the active floor via `active_floor()` at creation;
`OpeningItem` uses `self.wall.floor`). The authoritative roster is
`MainWindow.floors` (`model.Floor` dataclasses) + `self.active_floor`;
`_sync_floor_state()` mirrors it into `config.py`'s runtime cache — see that
file's own comment for why it is a mutable dict behind accessor functions
and not a bare global (star-imports would snapshot a rebindable string).

You edit ONE active floor; the geometry hot paths (`face_at`/
`coincident_walls`/`nearest_wall_*`/`_compute_wall_junctions`/
`bind_room_walls`/`_WallBBoxIndex`) all filter to the relevant floor so
floors never interact — and `design_from_scene`/`face_at` are level-scoped
*by construction* (levels outer, items inner) rather than by a filter.
`paint()` flat-grays non-active floors (`floor_display_mode`);
`apply_floor_visibility` hides/disables them. The model emits `floors` +
per-item `floor`; `active_floor` is view state — kept OUT of `serialize()`
(so switching floors isn't undoable/dirty) but written to the file by
`_write_plan`. v1–v3 files migrate to one `default` floor.

## Performance — the measurements behind the KEEP-list traps

- **Room detection is off the edit path entirely.** A `RoomItem`'s `path`
  and `area_sqft` derive from its `outline`, and the outline's corners are
  the same `Vertex` objects the walls hold, so a wall move updates the
  rooms it borders by construction — no re-detection pass exists. Measured
  on the P0.3 harness at 64 rooms: `bake` 299 ms → 28 ms, `rebuild` 3.7 ms
  → 2.4 ms. `rebuild` takes a shared `_WallIndex` so `coincident_walls`/
  `_joined_at` are O(local); the wall *path* build itself profiled as
  already cheap (`tests/bench_rooms.py` measures this).
- **"Detect room here"** (the Room tool, CSV import, macro `room`, paste,
  legacy load) is `rooms.detect_room` → `design.bridge.face_at` →
  `topology.enclosing_face`: a one-shot lift of the level's walls into a
  `Design`. Deliberately the opposite of the edit-op rule (a per-event
  full-plan rebuild would destroy item identity) — a detection is one user
  gesture, so it can afford the walk.
- **Wall junctions.** Each `WallItem` fills its body with no pen (overlapping
  greys merge seamlessly) and draws its outline clipped to its bounds minus
  neighbouring wall bodies, so T/cross/L junctions have no inner seam. The
  clip is cached by `_compute_wall_junctions(scene)` — one pass at the end
  of `rebuild_all_walls`, after every wall's own footprint is current (it
  needs all neighbours up to date, so it can't live in per-wall `rebuild()`).
  Uses `_WallBBoxIndex` for O(local) neighbour lookup.
