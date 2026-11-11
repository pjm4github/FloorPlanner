# 0313 — report: plan CAMERAS — a placeable viewpoint that opens an elevation of the wall it faces — on a branch

**Code, 2026‑11‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7). His
order 2026‑11‑11: *"I would like to have the ability to show elevations from
anywhere in the plan … a new command … click on the plan, in a room, or an
exterior wall and have a camera icon drop … rotate the camera … select options
on the camera … open a dialog box with an elevation view of the item that the
camera is pointing at … save its location, delete it, and so on."* Built on
branch `plan-cameras`, cut from `main`; **AMBER, awaiting his check**. His scope
for this first increment (his words, on the questions): **the elevation is of the
single wall/face the camera is aimed at** ("number 2 to start"); the camera's
**right-click menu is the extensible home** for the actions he will add; cameras
**persist in the plan file**; a **menu switch turns the cameras off**; and a
**double-click** on a placed camera opens the elevation. (No **Landed:** line —
AMBER.)

## 1. WHAT HE ORDERED

A viewpoint he can drop anywhere, aim, and read an elevation from — the first of
a family of per-camera actions. For this increment: place a camera by clicking,
aim it by rotating, double-click (or right-click → **Open elevation…**) for the
straight-on elevation of the wall it faces, **save it with the plan**, **delete**
it, and a **Show cameras** switch to hide them all.

## 2. WHAT IT DOES

- **`CameraItem`** (new `floorplanner/cameras.py`) — a movable, selectable plan
  glyph (a camera body + lens, a translucent field-of-view wedge and an aim
  arrow) modelled on `FurnishingItem`: a round rotator handle aims it (Ctrl
  sticks to the snap step), 90° steps on the menu, and it carries a `.floor` like
  every other item. Its **`rotation()` IS the aim** (degrees, 0 = +x).
- **The command** — **View ▸ Place camera** (shortcut **C**) starts the camera
  tool; a left-click on the plan drops a camera there on the active floor
  (`view.py`, the same idiom as the text/datum tools), then reverts to Select.
  The tool joins the exclusive tool group (no toolbar button, like the Datum
  tool).
- **The elevation** (`CameraItem.elevation()`) — the one new algorithm: it
  **ray-casts** from the camera along its aim to the **nearest wall on its floor**
  (`faced_wall`, a 2D ray/segment solve), then projects that wall **straight on,
  to scale**: every door and window located by `centre_in` (offset from the
  wall's middle, + toward the camera's right), `sill_in`/`head_in` (a window on
  its sill, a door/gate on the floor), and `w_in`/`h_in`. Doors and windows come
  back in **separate lists**. The top is the storey ceiling — the room the camera
  sits in, else a standard 96″ (a roof-capped top is a named follow-on, §5).
- **The dialog** — **double-click** the camera, or right-click → **Open
  elevation…**, opens a non-modal `CameraElevationDialog` whose
  `_WallElevationCanvas` paints the wall (a window as glass with a muntin cross, a
  door as a floor panel), with sill/head and centre-offset dimensions. A
  **Refresh** re-reads the camera, so he can move or re-aim it and update the
  view. (The twin of the gable End-On `_ElevationCanvas`, without the roof
  triangle.)
- **Persistence** — a camera **saves and reloads with the plan**: a new optional
  **`cameras`** array in the v6 schema (`id`, `level`, `pos`, `rotation`, `name`;
  older files still validate), a `Camera` dataclass in `design/model.py`, and
  `_cameras_of` / `_build_cameras` in `design/bridge.py` (write + read + the undo
  diff path), so it rides the existing save/undo plumbing.
- **The switch** — **View ▸ Show cameras** (checkable) hides or shows every camera
  at once (`_set_cameras_visible`); a camera placed while hidden starts hidden.
  Session UI state; the camera still saves with the plan.
- **The menu is the extension point** — the camera's `contextMenuEvent` is a
  plain action table (Open elevation…, Rotate 90°, Delete), so his future "other
  items" drop in as one line each.

## 3. RECEIPTS (instrument `docs/evidence/0313-plan-cameras/render.py`)

A 240″ exterior wall carrying a 36×48 window, a 32×80 door and a 24×36 window,
with a camera below it aimed up: `camera_elevation.png` draws the wall to its 96″
ceiling with the two windows on their 36″ sills (glass + muntin) and the door on
the floor, each dimensioned; `camera_plan.png` shows the camera glyph — the lens,
the field-of-view wedge and the aim arrow pointing at the wall. The dict reads
`window 36×48 sill 36 centre −60`, `door 32×80 sill 0 head 80 centre +30`,
`window 24×36 sill 36 centre +90` (offsets from the wall centre). Offscreen text
renders as tofu; `fmt_in` is ASCII and draws on the real display.

## 4. TESTS

`tests/test_cameras.py` (11): the aim ray finds the faced wall and the NEAREST of
two; aiming at open space yields no wall and no elevation; the elevation locates a
door and a window in their own lists (door on the floor, window on its sill) with
centre offsets from the wall middle; the default ceiling when no room; the record
round-trips; the `cameras` block round-trips through the document and **validates
against the v6 schema**, and is omitted when there are none; the **Show cameras**
toggle hides/shows, and **Place camera** starts the tool. Gate: full, GREEN.

## 5. NEXT

AMBER — his to check (View ▸ Place camera, click to drop one, drag the handle to
aim, double-click for the elevation; save and reload; Show cameras off/on). Known
limits / named follow-ons, for his word:
- **Flat ceiling (v1).** The elevation tops out at the room/standard ceiling; a
  wall under a gable does not yet show the roof triangle (the gable End-On tab
  does). Capping the camera elevation at the roofline is the natural next step and
  reuses `roofclip.surface_height`.
- **The other per-camera actions** he mentioned are his to name; the menu is built
  to take them (e.g. save a named view, open in 3D, a section, a label).
- **One wall, nearest hit.** The camera draws the single nearest wall it faces
  (his "number 2 to start"); a full "everything in view" elevation (depth,
  occlusion) remains the larger option he set aside. 0248's items 8–9 still named,
  not ordered.
