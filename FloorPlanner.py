#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Patrick Moran and Claude (Anthropic). See LICENSE.
"""
Floor Planner (PyQt6)
=====================

A 2D architectural floor-plan editor.

Free to use, copy, and modify under the MIT License — created by Patrick
Moran with Claude (Anthropic); retain the credit notice in copies.
See LICENSE.

Units
-----
Scene units are INCHES (1 scene unit = 1").  The grid shows 1'-0" minor
lines and 5'-0" major lines.  The "canvas" outline defaults to
100'-0" x 70'-0" and can be resized in File > Settings….

Tools (icon toolbar or keys S/E/I/D/W/R)
--------------------------------
1  Select      - click items, drag to move, drag wall ENDS to stretch
2  Ext Wall    - click-drag to draw a 6" exterior wall (orthogonal from
                 the anchor point; hold Shift for a free angle)
3  Int Wall    - click-drag to draw a 4-1/2" interior wall (same snapping)
4  Door        - click on a wall, enter WWHH size (inches x inches)
5  Window      - click on a wall, enter WWHH size
6  Room Name   - click inside an enclosed area to create a named ROOM
The toolbar shows SVG icons from assets/icons (hover for the name/key).

Furnishings palette (right side)
--------------------------------
The dock on the right shows the bundled furnishing library
(assets/furnishings: CC0 top-view symbols + manifest.json with each
item's true width/depth in inches) as EXPANDING SECTIONS, one per room
group from assets/furnishings/groups.json (a furnishing may belong to
several groups).  Click a section header (e.g. Bedroom) to expand it;
the "All" section — the whole library — is open by default.
DRAG a symbol onto the plan to
place it at real scale (scene units are inches).  Placed furnishings
can be dragged to move (1" snap) and are saved in the plan file.
Selecting one shows a round ROTATOR HANDLE above it: drag the handle
to spin the item (hold Ctrl to stick to the rotation snap from
File > Settings…, default 15°).  Right-click for 90-degree steps or
delete.

Mouse
-----
Wheel               zoom (anchored under cursor)
Left-drag (empty)   pan                (middle-drag pans in any tool)
Left-drag item      move / stretch
Right-click door    popup: LH, RH, BIFOLD, POCKET, SLIDER, FRENCH, DOORWAY,
                    GARAGE-1 (single 9'), GARAGE-2 (double 16').  Garage
                    doors draw the opening plus a dashed OVERHEAD outline
                    of the open door projecting inward; picking one
                    auto-sizes an undersized opening (9'x7' / 16'x7').
Right-click room name   popup: show dimensions, properties, inventory,
                        rename, copy, delete.  Inventory… lists the room's
                        properties and everything in the room (furnishings,
                        doors, windows) as name/quantity rows of
                        tab-separated text to copy into Excel.
Double-click door/window/room label    edit size / text

Behaviour
---------
* Walls have a standard width: exterior 6", interior 4-1/2".
* Wall centrelines snap to an on-centre grid while drawing, stretching,
  sliding and pasting (default 6").  File > Settings… opens a dialog
  with the wall snap, the Ctrl-drag rotation snap (default 15°) and the
  canvas size; all are saved in the plan file ("settings" section).
* Dragging a wall END lengthens/shortens it along its axis
  (hold Shift to re-angle freely).  Dragging the wall BODY slides it
  orthogonally to itself - the ends ride lines projected perpendicular
  from their starting points, so rooms stay rectangular instead of
  shearing into parallelograms.  Hold Ctrl to move the wall freely.
* Wall endpoints that are released near another wall's endpoint snap
  together and the corner is joined (mitred fill).
* A wall end drawn or released near or on the BODY of another wall fuses
  to it (T-junction): interior walls fuse to exterior walls and to other
  interior walls alike.  The fuse point is where the wall's own axis
  crosses the other wall, so snapping never changes the wall's direction.
* Gaps close themselves (up to 2'-0"): a wall end released short of the
  wall it points at projects forward onto it, and existing walls that
  point at a newly drawn wall but stop short GROW to meet it.
* Rooms are detected by flood-filling the enclosed empty space where you
  click; the room shows its name and area, can draw interior dimension
  arrows (double-headed) and carries a property sheet (right-click name).
* A named room traces its PERIMETER along the centrelines of the
  surrounding walls (thin blue dashed line, shown while the room is
  selected).  The corner coordinates are carried in the room properties
  and the area is the area inside that perimeter.  The perimeter
  re-traces whenever the walls change.  "Show dimensions" draws a
  double-headed arrow along EVERY wall edge enclosing the room; opposite
  walls with the same length are dimensioned only once.
* Sliding a wall (dragging its body) stretches/shrinks the walls attached
  to it: corner-joined walls follow the moved endpoints, T-joined walls
  follow sideways so they stay fused.
* Room names are unique in the plan; clashes get " 2", " 3", ... appended.
* Right-click a room name to COPY it (walls included); with the Room Name
  tool active, right-click a blank spot to PASTE it there.
* SELECTION SET: Ctrl is the multi-select modifier.  Ctrl+click an item
  to toggle it in/out of the selection set; Ctrl+drag on empty canvas
  sweeps a rubber band that ADDS everything it touches to the set
  (grouped items join as their group).  Edit > Group enables once the
  set holds two or more walls/furnishings.
* GROUPS: Ctrl+click to multi-select walls/furnishings, then Edit >
  Group (Ctrl+G) makes them select and move as one unit (dashed
  outline; Ctrl+Shift+G ungroups leaving the members where they sit,
  right-click for a menu).  A room whose walls all belong to a moved
  group rides along: its label, outline and shaded region re-detect at
  the new location.  Edit >
  Cut/Copy (Ctrl+X / Ctrl+C) takes the selection or group to an
  internal clipboard and Paste (Ctrl+V) recreates it centred on the
  mouse position, re-grouped; walls keep the on-centre snap and bring
  their doors/windows along.
* Doors and windows cut an opening in the wall and ride along it when
  dragged; sizes use the WWHH convention (e.g. 3280 = 32" w x 80" h);
  openings 100" or wider use WWWHH (e.g. 19284 = 192" w x 84" h).

CSV room import
---------------
File > Import rooms from CSV… bulk-creates walled rooms.  Columns:
Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes — Type (a room type),
locations and Notes are optional.  Lengths are feet and accept
12, 12.5, 12.5' or 12'6".  X_ft/Y_ft are the room's width/length
(wall centreline to centreline); X_loc_ft/Y_loc_ft place the room's
bottom-left corner measured from the canvas's BOTTOM-LEFT corner
(y upward).  Rows without a location are placed on the first clear
spot of the canvas.  Shared edges between imported rooms reuse the
existing wall instead of doubling it.  File > Export rooms to CSV…
writes the plan's rooms back out in the same format (decimal feet),
so room schedules round-trip.

File format
-----------
File > Save / Open store the plan as plain human-editable JSON (all
lengths in inches).  Top level: {format, version, units, settings,
walls, rooms, furnishings};
settings: {wall_snap_in, rotate_snap_deg, canvas_w_in, canvas_h_in};
each wall: {type, p1, p2, openings:[{kind, code, s, door_type, swing}]};
each room: {name, anchor, show_dimensions, properties};
each furnishing: {kind, pos, rotation} where `kind` is the id in
assets/furnishings/manifest.json.  Room geometry is re-detected from
the walls around `anchor` on load.

Run:  pip install PyQt6    then    python floor_planner.py
"""

# Compatibility shim: the app is now the ``floorplanner`` package.  This module
# re-exports the package's public API so ``import FloorPlanner`` and
# ``python FloorPlanner.py`` keep working.
from floorplanner import *  # noqa: F401,F403
from floorplanner.app import main  # noqa: F401
# underscore internals that star-import skips but tests still reference as fp.*
from floorplanner.dialogs import _money  # noqa: F401
from floorplanner.walls import (  # noqa: F401
    _WallBBoxIndex,
    _coalesce_all_impl,
    _coalesce_wall_impl,
)

if __name__ == "__main__":
    main()
