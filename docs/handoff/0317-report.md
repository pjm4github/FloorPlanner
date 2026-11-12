# 0317 — report: the camera ELEVATIONS THE WHOLE SIDE OF THE HOUSE when placed outside a room — a checkmark and a badge — on branch `camera-house-side`

**Code, 2026‑11‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7). His
order 2026‑11‑11: *"add the feature for the camera so that the camera can view
the entire side of a house when placed outside a room. There should be a
checkmark and a corresponding badge."* Built on branch `camera-house-side`;
**his word: "land it and merge"** — report on `main`, the one branch commit,
then merged. (He ordered the follow-on in the same breath — all levels, the
roof, the dormers, the gable ends — which §5 names as the next increment.)

## 1. WHAT HE ORDERED

Outside a room, the camera elevationed only the single exterior wall its aim ray
hit. He wants, as a switch, the ELEVATION OF THE WHOLE SIDE OF THE HOUSE — every
exterior wall across that side, laid out as one exterior elevation — reached by a
checkmark on the camera, with the plan glyph growing a badge so a glance says the
mode is on (the same pattern as the furnishings / cabinetry switches, 0315).

## 2. WHAT IT DOES

- **A third per‑camera switch** (`CameraItem`, `show_house_side`). Right‑click the
  camera ▸ **View whole house side** — checkable, beside Show furnishings / Show
  cabinetry; `set_show_house_side` flips it (`prepareGeometryChange` + `update`).
  Saved in the plan (`show_house_side`, v6 schema + `design/model.Camera`).
- **The glyph grows a HOUSE badge** (slate blue, a gabled silhouette with a door)
  when the switch is on — `_badges` / `_draw_badge` — drawn upright at any aim,
  the glyph's bounds opening to hold it.
- **The whole side, as an exterior elevation** (`CameraItem.elevation`). When the
  camera sits OUTSIDE a room and the switch is on, the elevation is EVERY exterior
  wall whose outside turns toward the camera, laid left→right. A wall qualifies
  when it (a) runs across the view, (b) stands in front, and (c) SEPARATES the
  camera‑side outdoors from an interior room — a `_room_at` probe just off each
  side of the wall. That third test is what drops the FAR side of the house (its
  camera‑facing side is indoors) and the perpendicular side walls (they run along
  the view, not across). Jogs and wings on that side are included. The faces reuse
  the room‑elevation data shape, so `_WallElevationCanvas` draws them unchanged —
  each wall its own panel with its openings, a faint‑grey seam between, widths
  dimensioned below.
- **A no‑op inside a room.** The switch only widens an OUTSIDE view; with the
  camera in a room the room‑wall elevation stands whether it is on or off. And
  outside with the switch OFF, the single faced wall reads as before.

## 3. RECEIPTS (instrument `docs/evidence/0317-house-side/render.py`)

The receipt stands a camera outside a house whose front is two exterior segments
(a door on one, two windows on the other), turns the switch on, and renders.
`house_side_elevation.png` draws BOTH segments as one exterior elevation — the
windows on their sills, the door on the floor, a faint seam between the two walls,
each width dimensioned — the far wall of the house and the two side walls absent.
`camera_glyphs.png` is the glyph in three states (plain / house‑side / all three
switches), the house badge beside the armchair and cabinet. The print confirms:
`faces [180, 120]` (the whole 300″ side), room `(outside)`.

## 4. TESTS

`tests/test_cameras.py` (25, up from 21): outside a room the switch elevations the
WHOLE side (both segments, far wall and side walls excluded); without the switch
an outside camera reads one wall; inside a room the switch is a no‑op; the switch
round‑trips through the v6 document; the glyph grows a third badge. Gate: full,
GREEN (2132 collected, 2125 passed OFF and ON, ruff clean).

## 5. NEXT — HIS NEXT ORDER

He ordered, in the same message: **the whole‑house‑side elevation across ALL
LEVELS, with the ROOF, the DORMERS and the GABLE ENDS.** This increment caps at
the flat ceiling of the storey the camera stands against; the next lifts it to a
full exterior elevation — every storey's exterior walls stacked by their floor
elevation, and the roof / dormer / gable geometry above drawn to the roofline
(reusing `roofclip.surface_height` and the roof/dormer gable readers the End‑On
elevation already has). That is the next branch. 0248's items 8–9 still stand.
