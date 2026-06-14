# Floor Planner

A 2D architectural floor-plan editor written in Python with PyQt6 — a single
file, `FloorPlanner.py`, plus bundled fonts and artwork.

![Floor Planner screenshot](docs/screenshot.png)

## Features

- **Walls** — exterior (6") and interior (4½") walls drawn by click-drag,
  orthogonal from the anchor (Shift for free angles). While drawing, the
  endpoint snaps to **line up with the nearest orthogonal wall** it points
  at while staying horizontal/vertical; any gap is left for you to extend
  to manually. Shared endpoints join into mitred corners. Dragging a wall's
  body slides it orthogonally — attached walls stretch and shrink so rooms
  stay rectangular (Ctrl for free movement).
- **Doors & windows** — placed on a wall with WWHH sizes
  (`3280` = 32" × 80"), they cut the opening and ride the wall when
  dragged. Door types: LH, RH, bifold, pocket, slider, French, doorway,
  and single / double **garage doors** (shown as the opening plus a
  dashed overhead outline of the open door).
- **Rooms** — click inside any enclosed area to name it. The room traces
  its perimeter along the wall centrelines, computes the true interior
  area, can draw double-headed dimension arrows on every enclosing wall
  (opposite equal walls dimensioned once), and carries a property sheet
  (room type, ceiling, finishes, HVAC, notes…). A labelled room **owns its
  boundary walls**: left-drag the name to move the whole room — walls,
  doors and windows travel together — and on a shared boundary each room
  keeps its own wall, so adjacent rooms stay aligned without disturbing one
  another. Clicking a room's name or any of its walls brings that room to
  the front. Ctrl-drag the name to nudge just the label; stretch an
  individual wall to reshape the room as before. A room wall's end-knobs
  are locked while it belongs to the room — right-click it and **Detach
  wall from room** to free it (then drag its ends along the wall, or hold
  Shift for any angle). Move a wall away and the edge it left becomes a
  dashed **open wall** that keeps the room closed for area, drags like a
  real wall, and disappears once a wall fills the gap again. Right-click a
  room name for an **inventory** — its
  properties plus every furnishing and opening in the room, in an aligned
  table you can copy as TSV for Excel. Rooms can be copied and pasted
  elsewhere with their walls and openings.
- **Furnishings** — a bundled CC0 library of 70 top-view symbols across
  Living, Dining, Kitchen, Bedroom, Bathroom, Laundry, Office, Garage
  (cars, boat + trailer, workbench, yard equipment), **Shop** (table saw,
  lathe, jointer, drill press, bandsaw, planer…), **Sunroom** (swim spa,
  sauna, whirlpool, lounge chairs…), **HVAC** (gas/electric/oil
  furnaces, water heaters, water softener, gas/oil tanks, electric panel,
  car charger, battery wall, well pump, heat exchanger) and **Framing**
  (stairs, residential elevator). Drag one from the
  right-hand
  palette onto the plan and it lands at **true scale** (scene units are
  inches; a 16' SUV takes up 16'). The palette is organised in expandable
  room sections; placed items move with 1" snap and rotate via a grab
  handle (Ctrl = snap to the configured increment).
- **Stairs** — the Framing **stairs** symbol draws the right number of
  steps for the **ceiling height of the room it sits in** (standard ~7"
  risers) and shows an **UP / DN** travel arrow. Right-click it to switch
  between a **full flight** and a **half flight to a landing** that either
  ends at half height or **turns left / right**, and to flip the arrow up
  or down. Move it into a room with a different ceiling and the step count
  re-computes.
- **Groups & multi-select** — Ctrl+drag a rubber band to add items to a
  selection set, or Ctrl+click to toggle individual items. The rubber band
  only takes items it **fully encloses**, so you can lasso a single room
  without grabbing the party walls that run past it — and when a room's
  interior is enclosed, any edge carried by such a longer wall is copied so
  the room comes through as a complete, movable loop (the shared wall is
  left in place). Group the set (Ctrl+G) to move it as one unit — walls,
  furnishings and the rooms they enclose travel together — then ungroup
  (Ctrl+Shift+G) to drop everything in place. A selected group also has a
  **rotation handle**: drag it to spin the whole group about its centre
  (Ctrl snaps to the rotation increment), e.g. to re-orient a room. Groups
  can be cut, copied and pasted.
- **Room import / export (CSV)** — File ▸ Import / Export rooms… reads and
  writes `Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes`. Sizes and
  locations accept feet-and-inches (`12`, `12.5`, `12'6"`); rooms without
  a location auto-place on the first clear spot. Rooms that fall outside
  the canvas **grow it to fit** (up to 500'; larger values are rejected as
  typos). See [`examples/`](examples/) for sample files and previews.
- **Room boolean operations** — select two rooms (Ctrl+click their names)
  and the **Rooms** menu treats their perimeters as polygons: *Combine*
  unions them (dropping the shared interior walls), *Intersect* keeps just
  the overlap, and *Subtract* removes the second room from the first. Each
  result is freshly walled and re-detected.
- **Fragment** — *Rooms ▸ Fragment* splits two overlapping rooms into three
  pieces — each room minus the overlap, plus the overlap itself — and puts
  **each piece in its own group with a complete set of walls** (shared
  edges get a wall per piece). So you can drag any fragment away and it
  stays a fully enclosed room while the others keep theirs. *Rooms ▸ Align
  to grid* snaps the selected rooms' walls to the wall-snap grid (keeping
  them orthogonal); *Rooms ▸ Distribute horizontally / vertically* spaces
  three or more selected rooms with equal gaps (the outermost two stay
  put); and *Rooms ▸ Refresh rooms* re-scans the canvas and drops any room
  whose walls have been moved away, clearing gray areas left behind.
- **Nudging** — arrow keys move the selected group or furnishing by the
  wall-snap step; hold Ctrl for a fine 1" step.
- **Undo / redo** — the **↺ / ↻** toolbar buttons (to the right of the
  zoom-fit magnifier, also **Ctrl+Z** / **Ctrl+Y**) step back and forward
  through every canvas operation — drawing and moving walls, openings,
  rooms, furnishings, groups, room boolean ops, nudges, deletes and pastes.
  History resets when you start a new plan or open one.
- **Inventory menu** — itemised, Excel-ready tables for the whole plan:
  *House* (rooms, doors, windows and walls), *Interior furnishings* and
  *Yard items* (furnishings split by location — cars, yard equipment and
  anything in the garage or outside the walls count as yard, each with
  quantities and AI-sourced prices), and *Total* (a summary with the grand
  building-plus-furnishings cost). Each opens as an aligned table; **Copy
  to clipboard (TSV)** emits tab-separated values that paste straight into
  a spreadsheet.
- **AI pricing** — the **AI** menu's *Update furnishing prices…* opens a
  dialog with a drop-down of AI systems (Anthropic Claude) and a fully
  editable, pre-filled prompt that asks for current US retail prices for
  the whole catalog. The reply (a JSON `{id: dollars}` map) is written into
  each furnishing's new `price` field in `manifest.json`, and palette and
  placed-item tooltips show the cost. The call uses your Anthropic API key
  (entered in the dialog — optionally remembered on this computer — or read
  from the `ANTHROPIC_API_KEY` environment variable).
- **Building totals** — the far right of the toolbar shows a live
  **Totals: Cost / Sq. Feet** label: the floor area of every room with
  *Include in total square footage* ticked (in its right-click Properties),
  priced at the cost per square foot set in Settings. Cost is shown in
  thousands; it updates as rooms are added, removed, resized, or toggled.
- **Settings** — File ▸ Settings… controls the wall snap (default 6" on
  centre), the rotation snap (default 15°), the canvas size (default
  100' × 70') and the building **cost per square foot** (default $150).
  Save with the **Save** button; all settings are stored with the plan.
- **Plans are plain JSON** — human-editable, documented in the module
  docstring: walls, openings, rooms, furnishings and settings, all lengths
  in inches.
- **Where files live** — **Help ▸ About** shows the app version and the
  OS-standard storage locations: plans open/save by default in
  `Documents/FloorPlanner`, and the app settings file (preferences,
  including a remembered AI key) lives in the standard per-user config
  directory (e.g. `%APPDATA%/FloorPlanner` on Windows, `~/.config/
  FloorPlanner` on Linux). Per-plan settings stay inside each plan's
  `.json`. Buttons in the dialog open either folder.

## Install & run

```bash
pip install -r requirements.txt
python FloorPlanner.py
```

Requires Python 3.10+ and PyQt6. Fonts (DejaVu) ship in `assets/fonts`,
so no system fonts are needed.

## Controls

| Action | How |
|---|---|
| Choose a tool | Toolbar icons or keys **1**–**6** |
| Zoom / pan | Mouse wheel / drag empty space (middle-drag anywhere) |
| Draw a wall | Click-drag (Shift = free angle, Esc = cancel) |
| Stretch / slide a wall | Drag its end / body in Select mode |
| Place a door or window | Tool 4 / 5, click a wall, enter WWHH size |
| Name a room | Tool 6, click an enclosed area (one-shot; Ctrl-pick the tool to keep it) |
| Move a room (with its walls) | Drag the room name (Ctrl-drag = nudge the label only) |
| Detach a wall from its room | Right-click the wall → *Detach wall from room* |
| Room dimensions / properties / inventory | Right-click the room name |
| Place furniture | Drag from the right palette onto the plan |
| Rotate furniture | Select it, drag the round handle (Ctrl = snapped) |
| Multi-select | Ctrl+drag a rubber band (encloses items / a room), Ctrl+click to toggle |
| Group / ungroup | **Ctrl+G** / **Ctrl+Shift+G** |
| Rotate a group | Select it, drag the rotation handle (Ctrl = snapped) |
| Nudge selection | Arrow keys (Ctrl = fine 1" step) |
| Room boolean ops | Select two rooms, use the **Rooms** menu |
| Plan inventories (TSV) | **Inventory** menu → House / Interior / Yard / Total |
| Update furnishing prices (AI) | **AI** menu → *Update furnishing prices…* |
| About / file locations | **Help** menu → *About FloorPlanner…* |
| Undo / redo | **Ctrl+Z** / **Ctrl+Y** (or the ↺ / ↻ toolbar buttons) |
| Cut / copy / paste | **Ctrl+X** / **Ctrl+C** / **Ctrl+V** |
| Import / export rooms (CSV) | File menu |
| Delete | Select + **Del** |
| Zoom to fit | **F** |

## Asset pipeline

All SVG artwork (toolbar icons, furnishing symbols, `manifest.json`,
`groups.json`) is generated by `_gen_assets.py` — edit it and re-run to
change or extend the library. Every furnishing SVG uses a viewBox in
inches matching its real footprint, which is what makes true-scale
placement work; see `assets/furnishings/README.md` for how to add your
own symbols. `docs/make_screenshot.py` rebuilds the screenshot above, and
`examples/make_examples.py` regenerates the sample files and previews.

## Development

```bash
pip install -r requirements-dev.txt
pytest              # full headless test suite
pytest --quick      # skip the slower gui tests during feature work
ruff check .        # lint
```

Tests live in `tests/` (see `tests/README.md`); they run headless via Qt's
offscreen platform. Categories are tagged with markers so subsets can be
run or skipped, e.g. `pytest -m "not gui"`.

## Licenses

- Furnishing symbols and toolbar icons: CC0 1.0 (drawn for this project,
  see `assets/furnishings/LICENSE`)
- DejaVu fonts: see `assets/fonts/LICENSE`
