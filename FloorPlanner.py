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

import csv
import json
import math
import os
import re
import sys
from collections import deque
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import (QEvent, QLineF, QMimeData, QPoint, QPointF, QRect,
                          QRectF, QSettings, QSize, QStandardPaths, Qt, QTimer,
                          QUrl)
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QContextMenuEvent,
    QDesktopServices,
    QDrag,
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QIcon,
    QImage,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPixmap,
    QPolygonF,
    QTextCursor,
    QTransform,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRubberBand,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QToolBox,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtSvg import QSvgGenerator, QSvgRenderer
except ImportError:               # QtSvg missing: furnishings draw as boxes
    QSvgRenderer = None
    QSvgGenerator = None

# ----------------------------------------------------------------------------
# Constants (all linear values are inches)
# ----------------------------------------------------------------------------
FOOT = 12.0
EXTERIOR_T = 6.0          # standard exterior wall width
INTERIOR_T = 4.5          # standard interior wall width
GRID_MINOR = 12.0         # 1'-0"
GRID_MAJOR = 60.0         # 5'-0"
SNAP_STEP = 1.0           # fine geometry (openings, anchors) snaps to 1"
WALL_SNAP_DEFAULT = 6.0   # walls snap to 6" on centre while drawing
WALL_SNAP_CHOICES = [1.0, 2.0, 3.0, 6.0, 12.0]
ROTATE_SNAP_DEFAULT = 15.0          # Ctrl-drag rotation increment (degrees)
CANVAS_W_DEFAULT = 100.0 * FOOT     # default canvas 100'-0" x 70'-0"
CANVAS_H_DEFAULT = 70.0 * FOOT
MAX_CANVAS_IN = 500.0 * FOOT        # CSV import won't grow the canvas past
#                                     500' in either direction (typo guard)

# Plan-wide settings, edited in File > Settings… and saved in the file.
DEFAULT_SETTINGS = {
    "wall_snap_in": WALL_SNAP_DEFAULT,
    "rotate_snap_deg": ROTATE_SNAP_DEFAULT,
    "canvas_w_in": CANVAS_W_DEFAULT,
    "canvas_h_in": CANVAS_H_DEFAULT,
    "cost_per_sqft": 150.0,           # building cost estimate, $/sq ft
}
SETTINGS = dict(DEFAULT_SETTINGS)
JOIN_TOL = 9.0            # endpoints within 9" join together
MIN_WALL_LEN = 6.0
WALL_PROJECT_STICK = 9.0  # stretch sticks within 9" of an orthogonal wall line
WALL_PROJECT_NEAR = 48.0  # ...only when that wall actually passes within 4'


def canvas_rect() -> QRectF:
    """The canvas outline, sized by the plan settings (default 100'x70')."""
    return QRectF(0.0, 0.0, SETTINGS["canvas_w_in"], SETTINGS["canvas_h_in"])

TOOL_SELECT, TOOL_WALL_EXT, TOOL_WALL_INT, TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM = range(6)

DOOR_TYPES = ["LH", "RH", "BIFOLD", "POCKET", "SLIDER", "FRENCH", "DOORWAY",
              "GARAGE-1", "GARAGE-2"]
# picking a garage type auto-sizes undersized openings to these defaults
GARAGE_DEFAULTS = {"GARAGE-1": ("10884", 96.0),    # single 9'-0" x 7'-0"
                   "GARAGE-2": ("19284", 144.0)}   # double 16'-0" x 7'-0"

ROOM_CELL = 3.0           # flood-fill cell size for room detection (inches)

ROOM_TYPES = [
    "", "Bedroom", "Bathroom", "Kitchen", "Living Room", "Dining Room",
    "Family Room", "Office", "Closet", "Laundry", "Garage", "Hallway",
    "Foyer", "Pantry", "Mudroom", "Utility", "Shop", "Sunroom",
]
CEILING_TYPES = ["Flat", "Tray", "Vaulted", "Cathedral", "Coffered",
                 "Shed", "Beamed", "Drop"]
FLOOR_FINISHES = ["Hardwood", "Engineered Wood", "Laminate", "Carpet",
                  "Ceramic Tile", "Porcelain Tile", "Vinyl / LVP",
                  "Stone", "Concrete"]
WALL_FINISHES = ["Painted Drywall", "Wallpaper", "Tile", "Wood Paneling",
                 "Plaster", "Exposed Brick"]
HVAC_TYPES = ["Forced Air", "Radiant Floor", "Baseboard", "Mini-Split",
              "Radiator", "None"]

# Editable room properties and their defaults.  Measured values (area,
# width/length, perimeter, window glazing area, door/window counts) are
# computed live from the plan and are not stored here.
DEFAULT_ROOM_PROPS = {
    "room_type": "",
    "include_sqft": True,             # count in the building's total area
    "ceiling_height_in": 96.0,
    "ceiling_type": "Flat",
    "floor_finish": "Hardwood",
    "wall_finish": "Painted Drywall",
    "baseboard": 'Standard 3 1/4"',
    "crown_molding": False,
    "hvac": "Forced Air",
    "electrical": "",
    "notes": "",
}

FILE_FORMAT = "floorplanner-json"
FILE_VERSION = 2          # v2: walls carry an owning-room tag (rooms own walls)

APP_NAME = "FloorPlanner"
APP_VERSION = "1.0"
APP_URL = "https://github.com/pjm4github/FloorPlanner"


def config_dir() -> Path:
    """Per-user config directory in the OS-standard location, created on
    demand (e.g. %APPDATA%/FloorPlanner on Windows, ~/.config/FloorPlanner
    on Linux, ~/Library/Application Support/FloorPlanner on macOS)."""
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppConfigLocation)
    p = Path(base) if base else (Path.home() / ".floorplanner")
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return p


def settings_file() -> Path:
    """The app-wide settings file (INI) holding cross-session preferences
    such as a remembered AI API key."""
    return config_dir() / "floorplanner.ini"


def designs_dir() -> Path:
    """The OS-standard folder where plans are opened/saved by default
    (Documents/FloorPlanner), created on demand."""
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation)
    p = (Path(base) if base else Path.home()) / "FloorPlanner"
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return p


def app_settings() -> QSettings:
    """QSettings backed by settings_file() so preferences live in a real,
    standard-location INI file (not the Windows registry)."""
    return QSettings(str(settings_file()), QSettings.Format.IniFormat)

# Bundled fonts: Qt no longer ships fonts, so the DejaVu family in
# assets/fonts is registered at startup and used as the app default.
FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT_FAMILY = "DejaVu Sans"


def load_fonts():
    """Register every bundled .ttf with Qt.  Must run after the
    QApplication exists."""
    if not FONT_DIR.is_dir():
        print(f"Font directory not found: {FONT_DIR}", file=sys.stderr)
        return
    for font_file in sorted(FONT_DIR.glob("*.ttf")):
        if QFontDatabase.addApplicationFont(str(font_file)) == -1:
            print(f"Failed to load font {font_file}", file=sys.stderr)


# ----------------------------------------------------------------------------
# Bundled artwork: toolbar icons and the furnishing symbol library
# ----------------------------------------------------------------------------
ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"
FURN_DIR = Path(__file__).resolve().parent / "assets" / "furnishings"
FURN_MIME = "application/x-floorplanner-furnishing"

_FURN_CATALOG = None
_FURN_GROUPS = None
_FURN_RENDERERS = {}


def tool_icon(name: str) -> QIcon:
    p = ICON_DIR / f"{name}.svg"
    return QIcon(str(p)) if p.is_file() else QIcon()


def furnishing_catalog() -> list:
    """The furnishing library: assets/furnishings/manifest.json entries
    (id, name, category, file, width_in, depth_in — true sizes in inches).
    Each SVG's viewBox is in inches too, so symbols render at real scale."""
    global _FURN_CATALOG
    if _FURN_CATALOG is None:
        _FURN_CATALOG = []
        try:
            entries = json.loads((FURN_DIR / "manifest.json")
                                 .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            entries = []
        for ent in entries:
            try:
                spec = {
                    "id": str(ent["id"]),
                    "name": str(ent.get("name", ent["id"])),
                    "category": str(ent.get("category", "Misc")),
                    "file": str(ent["file"]),
                    "width_in": float(ent["width_in"]),
                    "depth_in": float(ent["depth_in"]),
                    "price": float(ent.get("price", 0.0) or 0.0),
                }
            except (KeyError, TypeError, ValueError):
                continue
            if (FURN_DIR / spec["file"]).is_file():
                _FURN_CATALOG.append(spec)
    return _FURN_CATALOG


def furnishing_spec(kind: str):
    for spec in furnishing_catalog():
        if spec["id"] == kind:
            return spec
    return None


def furnishing_groups() -> list:
    """Palette sections from assets/furnishings/groups.json:
    [{"name", "specs"}], in file order.  Items are SVG file names (ids
    also accepted); unknown names are skipped and a furnishing may sit
    in several groups.  The "All" group always holds the whole catalog.
    Without a usable groups.json, falls back to All + the manifest
    categories."""
    global _FURN_GROUPS
    if _FURN_GROUPS is None:
        cat = furnishing_catalog()
        by_name = {s["file"]: s for s in cat}
        by_name.update({s["id"]: s for s in cat})
        sections = []
        try:
            entries = json.loads((FURN_DIR / "groups.json")
                                 .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            entries = []
        for ent in entries if isinstance(entries, list) else []:
            name = str(ent.get("name", "")).strip()
            if not name:
                continue
            if name.lower() == "all":
                specs = list(cat)
            else:
                specs = []
                for raw in ent.get("items", []):
                    spec = by_name.get(str(raw))
                    if spec is not None and spec not in specs:
                        specs.append(spec)
            if specs:
                sections.append({"name": name, "specs": specs})
        if not sections:
            sections = [{"name": "All", "specs": list(cat)}]
            by_cat = {}
            for s in cat:
                by_cat.setdefault(s["category"], []).append(s)
            sections += [{"name": k, "specs": v} for k, v in by_cat.items()]
        _FURN_GROUPS = sections
    return _FURN_GROUPS


def furnishing_renderer(kind: str):
    """Shared QSvgRenderer for a furnishing kind (None if unavailable)."""
    if QSvgRenderer is None:
        return None
    if kind not in _FURN_RENDERERS:
        spec = furnishing_spec(kind)
        if spec is None:
            return None
        _FURN_RENDERERS[kind] = QSvgRenderer(str(FURN_DIR / spec["file"]))
    r = _FURN_RENDERERS[kind]
    return r if r.isValid() else None


# ----------------------------------------------------------------------------
# AI-assisted pricing — ask a model for current furnishing purchase prices
# and write them into manifest.json's `price` field.
# ----------------------------------------------------------------------------
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# AI systems offered in the AI ▸ Update prices… dialog drop-down.
AI_PROVIDERS = [
    {"name": "Anthropic Claude",
     "models": ["claude-sonnet-4-6", "claude-opus-4-8",
                "claude-haiku-4-5-20251001"]},
]


def default_pricing_prompt(catalog=None) -> str:
    """The editable prompt pre-filled into the pricing dialog: lists every
    catalog item and asks for a single current US retail price each, returned
    as a strict JSON object {id: dollars}."""
    if catalog is None:
        catalog = furnishing_catalog()
    lines = [f'{s["id"]}\t{s["name"]} '
             f'({fmt_ftin(s["width_in"])} x {fmt_ftin(s["depth_in"])}, '
             f'{s["category"]})'
             for s in catalog]
    return (
        "You are a procurement assistant pricing home furnishings and "
        "fixtures.\n"
        "For each catalog item below, give a single representative CURRENT "
        "US retail purchase price for a new, mid-range product, in US "
        "dollars.\n\n"
        "Respond with ONLY a JSON object that maps each item id to a number "
        "(plain dollars, no currency symbols, no ranges, no commentary and "
        "no markdown fences). Example: {\"sofa\": 899, \"toilet\": 180}\n\n"
        "Items (id <tab> description):\n" + "\n".join(lines) + "\n")


def parse_price_json(text: str) -> dict:
    """Extract a {id: float-price} mapping from an AI text reply, tolerating
    surrounding prose or ```json fences. Raises RuntimeError if nothing
    usable is found."""
    s = (text or "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1 or b < a:
        raise RuntimeError("No JSON object found in the AI reply.")
    try:
        obj = json.loads(s[a:b + 1])
    except ValueError as ex:
        raise RuntimeError(f"Could not parse the AI reply as JSON: {ex}") \
            from ex
    out = {}
    for key, val in (obj.items() if isinstance(obj, dict) else []):
        try:
            out[str(key)] = float(val)
        except (TypeError, ValueError):
            continue
    if not out:
        raise RuntimeError("The AI reply contained no usable prices.")
    return out


def anthropic_fetch_prices(api_key: str, model: str, prompt: str,
                           *, timeout: float = 60.0) -> dict:
    """POST the prompt to the Anthropic Messages API and return the parsed
    {id: price} mapping. Raises RuntimeError on any network/API failure.
    Uses only the standard library (no SDK dependency)."""
    import urllib.error
    import urllib.request
    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(ANTHROPIC_API_URL, data=body, method="POST")
    req.add_header("content-type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", ANTHROPIC_VERSION)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        detail = ex.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"API error {ex.code}: {detail}") from ex
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise RuntimeError(f"Could not reach the AI service: {ex}") from ex
    except ValueError as ex:
        raise RuntimeError(f"Unexpected reply from the AI service: {ex}") \
            from ex
    text = "".join(blk.get("text", "") for blk in payload.get("content", [])
                   if isinstance(blk, dict) and blk.get("type") == "text")
    return parse_price_json(text)


def apply_furnishing_prices(prices: dict) -> int:
    """Write {id: price} into manifest.json and the live catalog in place.
    Returns the number of catalog items whose price was set."""
    path = FURN_DIR / "manifest.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        entries = []
    if isinstance(entries, list):
        for ent in entries:
            if isinstance(ent, dict) and str(ent.get("id")) in prices:
                ent["price"] = float(prices[str(ent["id"])])
        path.write_text(json.dumps(entries, indent=2) + "\n",
                        encoding="utf-8")
    n = 0
    for spec in furnishing_catalog():
        if spec["id"] in prices:
            spec["price"] = float(prices[spec["id"]])
            n += 1
    return n


def load_saved_api_key() -> str:
    """The Anthropic API key remembered in the settings file, if any."""
    try:
        return str(app_settings().value("anthropic_api_key", "") or "")
    except Exception:                       # noqa: BLE001 - best effort
        return ""


def save_api_key(key: str) -> None:
    try:
        app_settings().setValue("anthropic_api_key", key)
    except Exception:                       # noqa: BLE001 - best effort
        pass


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fmt_ftin(inches: float) -> str:
    """Format a length in inches as feet-and-inches, e.g. 30.5 -> 2'-6 1/2"."""
    sign = "-" if inches < 0 else ""
    v = abs(inches)
    ft = int(v // 12)
    rem = round((v - 12 * ft) * 2) / 2          # nearest half inch
    if rem >= 12:
        ft += 1
        rem = 0
    if rem == int(rem):
        rem_s = str(int(rem))
    else:
        rem_s = f"{int(rem)} 1/2"
    return f"{sign}{ft}'-{rem_s}\""


def fmt_in(inches: float) -> str:
    """Format a length as whole/half inches, e.g. 84 -> 84\"  (30.5 -> 30 1/2\")."""
    sign = "-" if inches < 0 else ""
    v = round(abs(inches) * 2) / 2          # nearest half inch
    whole = int(v)
    frac = v - whole
    s = str(whole) if frac == 0 else f"{whole} 1/2"
    return f'{sign}{s}"'


def parse_feet(text) -> float:
    """Parse a length given in feet into INCHES.

    Accepts:  12   12.5   12'   12.5'   12'6   12'6"   12' 6"   12'-6"
    (plain numbers are feet; 6" alone is inches).  Raises ValueError on
    anything else."""
    s = str(text).strip().replace("’", "'").replace("”", '"')
    if not s:
        raise ValueError("empty length")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*'\s*(?:-?\s*"
                     r"(\d+(?:\.\d+)?)\s*\"?)?", s)
    if m:
        return float(m.group(1)) * 12.0 + float(m.group(2) or 0.0)
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*"', s)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"\d+(?:\.\d+)?", s)
    if m:
        return float(s) * 12.0
    raise ValueError(f"cannot parse length {text!r} "
                     "(use 12, 12.5, 12.5' or 12'6\")")


def grid_snap(p: QPointF, step: float = SNAP_STEP) -> QPointF:
    return QPointF(round(p.x() / step) * step, round(p.y() / step) * step)


def wall_snap(p: QPointF) -> QPointF:
    """Snap a wall centreline point to the configured on-centre grid."""
    return grid_snap(p, SETTINGS["wall_snap_in"])


def wall_snap_len(s: float) -> float:
    """Snap a distance along a wall axis to the configured grid."""
    step = SETTINGS["wall_snap_in"]
    return round(s / step) * step


def parse_wwhh(code: str):
    """Parse a size code -> (width_in, height_in). Raises ValueError.

    4 digits = WWHH (3280 = 32" x 80"); widths of 100" or more use
    5 digits WWWHH (10884 = 108" x 84") or 6 digits WWWHHH."""
    code = code.strip()
    if not code.isdigit() or len(code) not in (4, 5, 6):
        raise ValueError('Size must be digits "WWHH" (e.g. 3280 = 32" x '
                         '80"); wide openings use WWWHH (e.g. 10884 = '
                         '108" x 84").')
    split = 2 if len(code) == 4 else 3
    w, h = int(code[:split]), int(code[split:])
    if w < 8:
        raise ValueError("Width must be at least 8 inches.")
    if h < 8:
        raise ValueError("Height must be at least 8 inches.")
    return float(w), float(h)


def nearest_wall_endpoint(scene, p: QPointF, tol: float, exclude=None):
    """Closest endpoint of any wall (other than `exclude`) within `tol`."""
    best, best_d = None, tol
    if scene is None:
        return None
    for it in scene.items():
        if isinstance(it, WallItem) and it is not exclude:
            for q in (it.p1, it.p2):
                d = QLineF(p, q).length()
                if d < best_d:
                    best_d, best = d, QPointF(q)
    return best


def nearest_wall_body(scene, p: QPointF, tol: float, exclude=None):
    """Closest (wall, centreline point) within reach of `p`, or None.

    This is the fuse target for T-junctions: a wall end that stops at (or
    inside) the body of another wall snaps onto that wall's centreline so
    the two paint as one solid joint."""
    best, best_d = None, float("inf")
    if scene is None:
        return None
    for it in scene.items():
        if isinstance(it, WallItem) and it is not exclude:
            length = it.length()
            if length < 1e-6:
                continue
            u = it.unit()
            s = (p.x() - it.p1.x()) * u.x() + (p.y() - it.p1.y()) * u.y()
            s = max(0.0, min(length, s))
            q = it.point_at(s)
            d = QLineF(p, q).length()
            if d <= max(tol, it.t * 0.5 + 1.0) and d < best_d:
                best_d, best = d, (it, QPointF(q))
    return best


def nearest_wall_body_point(scene, p: QPointF, tol: float, exclude=None):
    hit = nearest_wall_body(scene, p, tol, exclude)
    return hit[1] if hit is not None else None


def line_intersection(p: QPointF, u: QPointF, q: QPointF, v: QPointF):
    """Intersection of the line through `p` with direction `u` and the line
    through `q` with direction `v`; None when parallel."""
    den = u.x() * v.y() - u.y() * v.x()
    if abs(den) < 1e-9:
        return None
    wx, wy = q.x() - p.x(), q.y() - p.y()
    s = (wx * v.y() - wy * v.x()) / den
    return QPointF(p.x() + u.x() * s, p.y() + u.y() * s)


def dist_point_segment(p: QPointF, a: QPointF, b: QPointF) -> float:
    """Shortest distance from point `p` to segment `a`-`b`."""
    abx, aby = b.x() - a.x(), b.y() - a.y()
    L2 = abx * abx + aby * aby
    if L2 < 1e-9:
        return QLineF(p, a).length()
    t = ((p.x() - a.x()) * abx + (p.y() - a.y()) * aby) / L2
    t = max(0.0, min(1.0, t))
    return QLineF(p, QPointF(a.x() + abx * t, a.y() + aby * t)).length()


# ----------------------------------------------------------------------------
# Stacking order: "Bring to front" / "Send to back" for any item's menu
# ----------------------------------------------------------------------------
def bring_to_front(item):
    """Stack `item` above every other scene item (transient -- z is not saved)."""
    sc = item.scene()
    if sc is None:
        return
    top = max((it.zValue() for it in sc.items() if it is not item),
              default=0.0)
    item.setZValue(top + 1.0)


def send_to_back(item):
    """Stack `item` below every other scene item."""
    sc = item.scene()
    if sc is None:
        return
    bot = min((it.zValue() for it in sc.items() if it is not item),
              default=0.0)
    item.setZValue(bot - 1.0)


def add_front_back_actions(menu):
    """Append the stacking actions to a context menu; returns (front, back)."""
    menu.addSeparator()
    return (menu.addAction("Bring to front"), menu.addAction("Send to back"))


def handle_front_back(item, chosen, a_front, a_back) -> bool:
    """Apply a chosen stacking action; True if it was one of them."""
    if chosen is a_front:
        bring_to_front(item)
        return True
    if chosen is a_back:
        send_to_back(item)
        return True
    return False


def axis_wall_intersection(target, anchor: QPointF, through: QPointF):
    """Where the ray anchor->through crosses `target`'s centreline
    (clamped to the segment), or None when parallel or degenerate.

    Snapping a wall end to this point (instead of the perpendicular
    projection) keeps the snapped wall's own direction intact."""
    dx, dy = through.x() - anchor.x(), through.y() - anchor.y()
    if math.hypot(dx, dy) < 1e-9:
        return None
    wx, wy = target.p2.x() - target.p1.x(), target.p2.y() - target.p1.y()
    den = dx * wy - dy * wx
    if abs(den) < 1e-9:
        return None
    ex, ey = target.p1.x() - anchor.x(), target.p1.y() - anchor.y()
    t = (ex * wy - ey * wx) / den
    if t <= 1e-9:
        return None                       # crossing is behind the anchored end
    s = max(0.0, min(1.0, (ex * dy - ey * dx) / den))
    return QPointF(target.p1.x() + wx * s, target.p1.y() + wy * s)


class _WallIndex:
    """Per-rebuild spatial cache so each wall's rebuild() is O(local) instead
    of O(all walls): an endpoint hash (joined corners) + per-line buckets
    (coincident party walls).  Built once by rebuild_all_walls and passed to
    every wall; the exact predicates are unchanged, the index just narrows the
    candidate set to a guaranteed superset."""

    EP = 4.0          # endpoint hash cell (>> the 0.6" join tolerance)
    OFF = 3.0         # line-offset bucket (>> the 1.5" coincidence tolerance)

    def __init__(self, scene):
        self.eps = {}            # (i, j) -> [(wall, x, y)]
        self.hb = {}             # round(y/OFF) -> [horizontal walls]
        self.vb = {}             # round(x/OFF) -> [vertical walls]
        self.diag = []           # non-axis-aligned real walls (rare)
        for w in (scene.items() if scene is not None else []):
            if not isinstance(w, WallItem):
                continue
            for p in (w.p1, w.p2):
                self.eps.setdefault((round(p.x() / self.EP),
                                     round(p.y() / self.EP)), []).append(
                    (w, p.x(), p.y()))
            if w.is_open or w.length() < 1e-6:
                continue
            u = w.unit()
            if abs(u.y()) < 1e-4:
                self.hb.setdefault(round(w.p1.y() / self.OFF), []).append(w)
            elif abs(u.x()) < 1e-4:
                self.vb.setdefault(round(w.p1.x() / self.OFF), []).append(w)
            else:
                self.diag.append(w)

    def joined_at(self, p, exclude) -> bool:
        px, py = p.x(), p.y()
        ki, kj = round(px / self.EP), round(py / self.EP)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for w, qx, qy in self.eps.get((ki + di, kj + dj), ()):
                    if w is not exclude and (qx - px) ** 2 + (qy - py) ** 2 \
                            < 0.36:
                        return True
        return False

    def coincident_candidates(self, wall):
        u = wall.unit()
        if abs(u.y()) < 1e-4:                          # horizontal query
            b = round(wall.p1.y() / self.OFF)
            return [w for d in (-1, 0, 1) for w in self.hb.get(b + d, ())] \
                + self.diag
        if abs(u.x()) < 1e-4:                          # vertical query
            b = round(wall.p1.x() / self.OFF)
            return [w for d in (-1, 0, 1) for w in self.vb.get(b + d, ())] \
                + self.diag
        return ([w for ws in self.hb.values() for w in ws]   # diagonal: rare
                + [w for ws in self.vb.values() for w in ws] + self.diag)


def coincident_walls(scene, wall, index=None):
    """Real walls that lie on the same line as `wall` and overlap its span --
    the duplicate party walls created when adjacent rooms each own their own
    wall on a shared boundary.  Used so a plain wall opens for the door or
    window carried by the wall coincident with it."""
    if scene is None or wall.length() < 1e-6:
        return []
    u = wall.unit()
    length = wall.length()
    out = []
    cands = (index.coincident_candidates(wall) if index is not None
             else scene.items())
    for w in cands:
        if not isinstance(w, WallItem) or w is wall or w.is_open \
                or w.length() < 1e-6:
            continue
        wu = w.unit()
        if abs(wu.x() * u.y() - wu.y() * u.x()) > 0.02:        # not parallel
            continue
        d1 = abs((w.p1.x() - wall.p1.x()) * u.y()              # off the line?
                 - (w.p1.y() - wall.p1.y()) * u.x())
        d2 = abs((w.p2.x() - wall.p1.x()) * u.y()
                 - (w.p2.y() - wall.p1.y()) * u.x())
        if d1 > 1.5 or d2 > 1.5:
            continue
        s1 = (w.p1.x() - wall.p1.x()) * u.x() + (w.p1.y() - wall.p1.y()) * u.y()
        s2 = (w.p2.x() - wall.p1.x()) * u.x() + (w.p2.y() - wall.p1.y()) * u.y()
        if max(s1, s2) > 0.5 and min(s1, s2) < length - 0.5:   # spans overlap
            out.append(w)
    return out


def wall_endpoint_open(scene, p: QPointF, ignore=()) -> bool:
    """True when `p` is a free, dangling wall end: no other (non-open) wall has
    an endpoint within JOIN_TOL of it.  Walls in `ignore` are skipped (the
    endpoint's own wall, and the wall being drawn)."""
    if scene is None:
        return False
    for w in scene.items():
        if not isinstance(w, WallItem) or w.is_open or w in ignore:
            continue
        if (QLineF(w.p1, p).length() < JOIN_TOL
                or QLineF(w.p2, p).length() < JOIN_TOL):
            return False
    return True


class _RoomGrid:
    """All non-open walls rasterised (solid, openings ignored) onto a flood-
    fill grid over the canvas.  Built ONCE so many room regions can be located
    against the same grid -- refresh_rooms re-detects every room from one grid
    instead of rebuilding it per room (the old O(rooms x walls) cost)."""

    def __init__(self, scene):
        canvas = canvas_rect()
        self.canvas = canvas
        self.cell = cell = ROOM_CELL
        self.x0, self.y0 = x0, y0 = canvas.left(), canvas.top()
        self.nx = nx = int(canvas.width() / cell)
        self.ny = ny = int(canvas.height() / cell)
        self.blocked = blocked = bytearray(nx * ny)
        self.has_walls = False
        if scene is None:
            return
        for w in scene.items():
            if not isinstance(w, WallItem) or w.is_open:
                continue
            length = w.length()
            if length < 1e-6:
                continue
            self.has_walls = True
            u = w.unit()
            ux, uy = u.x(), u.y()
            p1x, p1y = w.p1.x(), w.p1.y()
            p2x, p2y = w.p2.x(), w.p2.y()
            half = w.t * 0.5 + cell * 0.5
            i0 = max(0, int((min(p1x, p2x) - half - x0) / cell))
            i1 = min(nx - 1, int((max(p1x, p2x) + half - x0) / cell))
            j0 = max(0, int((min(p1y, p2y) - half - y0) / cell))
            j1 = min(ny - 1, int((max(p1y, p2y) + half - y0) / cell))
            for j in range(j0, j1 + 1):
                cy = y0 + (j + 0.5) * cell
                row = j * nx
                for i in range(i0, i1 + 1):
                    cx = x0 + (i + 0.5) * cell
                    dx, dy = cx - p1x, cy - p1y
                    s = dx * ux + dy * uy
                    if -half <= s <= length + half \
                            and abs(dy * ux - dx * uy) <= half:
                        blocked[row + i] = 1

    def region(self, p: QPointF):
        """(QPainterPath, area_sqft) for the enclosed region containing `p`, or
        None when it leaks to the canvas edge or `p` sits on a wall."""
        if not self.has_walls or not self.canvas.contains(p):
            return None
        cell, x0, y0 = self.cell, self.x0, self.y0
        nx, ny, blocked = self.nx, self.ny, self.blocked
        si, sj = int((p.x() - x0) / cell), int((p.y() - y0) / cell)
        if not (0 <= si < nx and 0 <= sj < ny) or blocked[sj * nx + si]:
            return None
        seen = bytearray(nx * ny)
        seen[sj * nx + si] = 1
        queue = deque([(si, sj)])
        cells = []
        while queue:
            i, j = queue.popleft()
            if i == 0 or j == 0 or i == nx - 1 or j == ny - 1:
                return None                 # leaked out -> not enclosed
            cells.append((i, j))
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                k = b * nx + a
                if not seen[k] and not blocked[k]:
                    seen[k] = 1
                    queue.append((a, b))
        rows = {}
        for i, j in cells:
            rows.setdefault(j, []).append(i)
        path = QPainterPath()
        for j, cols in rows.items():
            cols.sort()
            start = prev = cols[0]
            for i in cols[1:] + [None]:
                if i is not None and i == prev + 1:
                    prev = i
                    continue
                path.addRect(QRectF(x0 + start * cell, y0 + j * cell,
                                    (prev - start + 1) * cell, cell))
                if i is not None:
                    start = prev = i
        area_sqft = len(cells) * cell * cell / 144.0
        return path.simplified(), area_sqft


def detect_room_region(scene, p: QPointF):
    """Flood-fill the empty space around `p`, bounded by wall bodies.  Returns
    (QPainterPath, area_sqft) in scene coords, or None.  See _RoomGrid."""
    return _RoomGrid(scene).region(p)


def poly_area_sqft(corners) -> float:
    """Shoelace area of a closed polygon (inches) in square feet."""
    n = len(corners)
    a2 = 0.0
    for i in range(n):
        p, q = corners[i], corners[(i + 1) % n]
        a2 += p.x() * q.y() - q.x() * p.y()
    return abs(a2) / 2.0 / 144.0


class _WallGraph:
    """Planar graph of wall centrelines, split where walls join (corner/T) or
    cross.  Built ONCE so the enclosing face around many anchors can be walked
    against the same graph (refresh_rooms traces every room from one graph).

    The O(walls^2) split-finding caches endpoints as floats to avoid millions
    of QPointF.x()/.y() calls."""

    def __init__(self, scene):
        self.nodes = []           # QPointF per node
        self.edges = set()
        self.adj = {}
        walls = [it for it in (scene.items() if scene is not None else [])
                 if isinstance(it, WallItem) and not it.is_open
                 and it.length() > 1e-6]
        if not walls:
            return
        segs = []                 # (length, ux, uy, p1x, p1y, p2x, p2y)
        for w in walls:
            length, u = w.length(), w.unit()
            segs.append((length, u.x(), u.y(),
                         w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()))
        nc = []                   # node coords (x, y) parallel to self.nodes
        nodes, edges = self.nodes, self.edges

        def node_id(px, py):
            for k, (qx, qy) in enumerate(nc):
                if abs(qx - px) <= 0.6 and abs(qy - py) <= 0.6:
                    return k
            nc.append((px, py))
            nodes.append(QPointF(px, py))
            return len(nc) - 1

        for i, (length, ux, uy, p1x, p1y, p2x, p2y) in enumerate(segs):
            splits = {0.0, length}
            d1x, d1y = p2x - p1x, p2y - p1y
            for j, (_l2, _u2x, _u2y, q1x, q1y, q2x, q2y) in enumerate(segs):
                if i == j:
                    continue
                for qx, qy in ((q1x, q1y), (q2x, q2y)):   # T: endpoint on body
                    vx, vy = qx - p1x, qy - p1y
                    s = vx * ux + vy * uy
                    if 0.5 < s < length - 0.5 \
                            and abs(vy * ux - vx * uy) <= 0.75:
                        splits.add(s)
                d2x, d2y = q2x - q1x, q2y - q1y           # X: true crossing
                den = d1x * d2y - d1y * d2x
                if abs(den) > 1e-9:
                    ex, ey = q1x - p1x, q1y - p1y
                    t1 = (ex * d2y - ey * d2x) / den
                    t2 = (ex * d1y - ey * d1x) / den
                    if 0.0 <= t1 <= 1.0 and 0.0 <= t2 <= 1.0:
                        s = t1 * length
                        if 0.5 < s < length - 0.5:
                            splits.add(s)
            ss = sorted(splits)
            for a, b in zip(ss, ss[1:], strict=False):
                if b - a < 0.5:
                    continue
                na = node_id(p1x + a * ux, p1y + a * uy)
                nb = node_id(p1x + b * ux, p1y + b * uy)
                if na != nb:
                    edges.add((min(na, nb), max(na, nb)))
        for a, b in edges:
            self.adj.setdefault(a, []).append(b)
            self.adj.setdefault(b, []).append(a)

    def face(self, anchor: QPointF):
        """Corner QPointFs of the enclosing face around `anchor`, or None."""
        nodes, edges, adj = self.nodes, self.edges, self.adj
        if not edges:
            return None
        # +x ray from the anchor: the nearest crossing edge, oriented with the
        # anchor on its left, starts the face walk
        ax, ay = anchor.x(), anchor.y()
        start, best_x = None, None
        for a, b in edges:
            pa, pb = nodes[a], nodes[b]
            if (pa.y() > ay) == (pb.y() > ay):
                continue
            x_at = pa.x() + (ay - pa.y()) * (pb.x() - pa.x()) / (pb.y() - pa.y())
            if x_at <= ax or (best_x is not None and x_at >= best_x):
                continue
            cross = ((pb.x() - pa.x()) * (ay - pa.y())
                     - (pb.y() - pa.y()) * (ax - pa.x()))
            start, best_x = ((a, b) if cross > 0 else (b, a)), x_at
        if start is None:
            return None
        # at each node take the next edge clockwise from the reversed incoming
        # direction; this keeps the enclosed face on the left
        poly = [start[0]]
        cur = start
        for _ in range(2 * len(edges) + 8):
            u_, v_ = cur
            pv = nodes[v_]
            th_rev = math.atan2(nodes[u_].y() - pv.y(), nodes[u_].x() - pv.x())
            nxt, best_d = None, None
            for wn in adj[v_]:
                th = math.atan2(nodes[wn].y() - pv.y(), nodes[wn].x() - pv.x())
                delta = (th_rev - th) % (2.0 * math.pi)
                if delta < 1e-9:
                    delta = 2.0 * math.pi     # U-turn only as a last resort
                if best_d is None or delta < best_d:
                    best_d, nxt = delta, wn
            cur = (v_, nxt)
            if cur == start:
                break
            poly.append(v_)
        else:
            return None                       # never closed -> give up
        if len(poly) < 3:
            return None
        pts = [nodes[k] for k in poly]
        n = len(pts)
        if sum(pts[i].x() * pts[(i + 1) % n].y()
               - pts[(i + 1) % n].x() * pts[i].y() for i in range(n)) <= 0:
            return None                       # walked the unbounded outer face
        corners = []
        for i in range(n):                    # drop straight pass-through nodes
            p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
            ax1, ay1 = p1.x() - p0.x(), p1.y() - p0.y()
            bx1, by1 = p2.x() - p1.x(), p2.y() - p1.y()
            cross = ax1 * by1 - ay1 * bx1
            dot = ax1 * bx1 + ay1 * by1
            if dot < 0.0 or abs(cross) > \
                    0.05 * math.hypot(ax1, ay1) * math.hypot(bx1, by1):
                corners.append(QPointF(p1))
        return corners if len(corners) >= 3 else None


def trace_room_perimeter(scene, anchor: QPointF):
    """Polygon of wall-CENTRELINE corners enclosing `anchor`, or None.  See
    _WallGraph."""
    return _WallGraph(scene).face(anchor)


def _detect_room(grid, graph, anchor):
    """Detect the room at `anchor` against a prebuilt grid + graph."""
    res = grid.region(anchor)
    if res is None:
        return None
    path, area = res
    corners = graph.face(anchor)
    if corners:
        area = poly_area_sqft(corners)
    return path, area, corners


def detect_room(scene, anchor: QPointF):
    """Full room detection: flood-fill region + centreline perimeter.

    Returns (path, area_sqft, corners) or None.  When the perimeter trace
    succeeds, the area is the area inside the perimeter polygon; otherwise
    the flood-fill area is the fallback and corners is None."""
    return _detect_room(_RoomGrid(scene), _WallGraph(scene), anchor)


def unique_room_name(scene, base: str, exclude=None) -> str:
    """`base` if unused in the plan, else `base 2`, `base 3`, ..."""
    names = {it.name for it in scene.items()
             if isinstance(it, RoomItem) and it is not exclude}
    if base not in names:
        return base
    n = 2
    while f"{base} {n}" in names:
        n += 1
    return f"{base} {n}"


def refresh_rooms(scene):
    """Re-detect every room's region + perimeter after walls change.

    When the stored anchor no longer falls inside the room (its walls
    were moved or resized past it), probe points across the room's last
    known region for its new extent and move the anchor (and label)
    there — skipping any region that already belongs to another room."""
    if scene is None:
        return
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    if not rooms:
        return
    # build the wall grid + planar graph ONCE and reuse them for every room
    # (and probe point), instead of rebuilding both per room
    grid, graph = _RoomGrid(scene), _WallGraph(scene)
    for it in rooms:
        res = _detect_room(grid, graph, it.anchor)
        if res is None:
            others = [r for r in rooms if r is not it]
            for p in _room_probe_points(it):
                cand = _detect_room(grid, graph, p)
                if cand is None or any(cand[0].contains(o.anchor)
                                       for o in others):
                    continue
                res = cand
                it.prepareGeometryChange()
                it.anchor = QPointF(p)
                break
        if res is None and it.corners:
            # the room is open (a corner was pulled away) so flood-fill escapes:
            # rebuild the loop from the room's own walls, inserting corners and
            # dashed open segments wherever consecutive walls no longer meet
            res = reloop_open_room(it)
        if res is not None:
            it.set_region(*res)
            # re-affirm wall ownership against the new perimeter; settle=False
            # so we don't recurse back into rebuild_all_walls/refresh_rooms
            bind_room_walls(scene, it, settle=False)


def _room_probe_points(room) -> list:
    """Candidate interior points for re-finding a room whose anchor was
    left outside: the old perimeter's centroid, then a grid sample of
    the old region."""
    pts = []
    if room.corners:
        n = len(room.corners)
        pts.append(QPointF(sum(p.x() for p in room.corners) / n,
                           sum(p.y() for p in room.corners) / n))
    br = room.path.boundingRect()
    for iy in range(1, 6):
        for ix in range(1, 6):
            p = QPointF(br.left() + br.width() * ix / 6.0,
                        br.top() + br.height() * iy / 6.0)
            if room.path.contains(p):
                pts.append(p)
    return pts


def rebuild_all_walls(scene):
    if scene is None:
        return
    index = _WallIndex(scene)                # shared: rebuild is O(local), not
    for it in list(scene.items()):           # O(all walls) per wall
        if isinstance(it, WallItem):
            it.rebuild(cascade=False, index=index)
    refresh_rooms(scene)


# ----------------------------------------------------------------------------
# Wall
# ----------------------------------------------------------------------------
class WallItem(QGraphicsItem):
    """A straight wall segment.  Local coords == scene coords (pos stays 0,0).

    Geometry is defined by endpoints p1, p2 plus a standard thickness.
    Door/window OpeningItems are child items; each remembers its distance
    `s` along the wall from p1, so they ride along when the wall moves.
    """

    is_open = False                   # OpenWall (a dashed gap) sets this True

    def __init__(self, p1: QPointF, p2: QPointF, wall_type: str = "exterior"):
        super().__init__()
        self.wall_type = wall_type
        self.p1 = QPointF(p1)
        self.p2 = QPointF(p2)
        self.openings = []            # OpeningItem children
        self.room = None              # owning RoomItem (None = unbound)
        self._corners_unlocked = False  # endpoints draggable while in a room
        self._drawing = False         # True while being rubber-banded
        self._mode = None             # None | 'p1' | 'p2' | 'move'
        self._path = QPainterPath()
        self._hit = QPainterPath()
        self._bounds = QRectF()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(0)
        self.rebuild()

    def itemChange(self, change, value):
        # when removed from the scene, release the room that owns this wall so
        # RoomItem.walls never keeps a reference to a deleted item
        if (change == QGraphicsItem.GraphicsItemChange.ItemSceneChange
                and value is None and self.room is not None
                and not sip.isdeleted(self.room)):
            self.room.unbind_wall(self)
        return super().itemChange(change, value)

    # -- basic geometry ------------------------------------------------------
    @property
    def t(self) -> float:
        return EXTERIOR_T if self.wall_type == "exterior" else INTERIOR_T

    def length(self) -> float:
        return math.hypot(self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y())

    def angle_rad(self) -> float:
        return math.atan2(self.p2.y() - self.p1.y(), self.p2.x() - self.p1.x())

    def unit(self) -> QPointF:
        length = self.length()
        if length < 1e-9:
            return QPointF(1.0, 0.0)
        return QPointF((self.p2.x() - self.p1.x()) / length,
                       (self.p2.y() - self.p1.y()) / length)

    def point_at(self, s: float) -> QPointF:
        u = self.unit()
        return QPointF(self.p1.x() + u.x() * s, self.p1.y() + u.y() * s)

    def s_of(self, p: QPointF) -> float:
        """Project a scene point onto the wall axis -> distance from p1."""
        u = self.unit()
        s = (p.x() - self.p1.x()) * u.x() + (p.y() - self.p1.y()) * u.y()
        return max(0.0, min(self.length(), s))

    # -- geometry cache ------------------------------------------------------
    def _joined_at(self, p: QPointF, index=None) -> bool:
        """True when another wall shares (within 1/2") this endpoint."""
        if index is not None:
            return index.joined_at(p, self)
        sc = self.scene()
        if sc is None:
            return False
        for it in sc.items():
            if isinstance(it, WallItem) and it is not self:
                if (QLineF(p, it.p1).length() < 0.6
                        or QLineF(p, it.p2).length() < 0.6):
                    return True
        return False

    def rebuild(self, cascade=True, index=None):
        """Recompute the painted path (with openings cut out) and hit shape.

        When `cascade`, also rebuild any coincident party walls so they reopen
        for this wall's openings (and re-solidify when an opening leaves).
        rebuild_all_walls passes cascade=False since it rebuilds every wall."""
        self.prepareGeometryChange()
        length, t, ang = self.length(), self.t, self.angle_rad()

        # extend joined ends by half a thickness so corners fill in solid
        ext1 = t * 0.5 if self._joined_at(self.p1, index) else 0.0
        ext2 = t * 0.5 if self._joined_at(self.p2, index) else 0.0

        body = QPainterPath()
        body.addRect(QRectF(-ext1, -t / 2, length + ext1 + ext2, t))
        holes = QPainterPath()
        for op in self.openings:
            half = op.width / 2
            op.s = min(max(op.s, half), max(half, length - half))
            holes.addRect(QRectF(op.s - half, -t / 2 - 0.5, op.width, t + 1.0))
        # open the body where a coincident wall carries a door/window, so a
        # plain party wall doesn't cover the opening on the wall next to it
        if not self.is_open:
            u = self.unit()
            for w in coincident_walls(self.scene(), self, index):
                for op in w.openings:
                    p = w.point_at(op.s)
                    sl = ((p.x() - self.p1.x()) * u.x()
                          + (p.y() - self.p1.y()) * u.y())
                    half = op.width / 2
                    if -half < sl < length + half:
                        holes.addRect(QRectF(sl - half, -t / 2 - 0.5,
                                             op.width, t + 1.0))
        if not holes.isEmpty():
            body = body.subtracted(holes)

        tr = QTransform()
        tr.translate(self.p1.x(), self.p1.y())
        tr.rotateRadians(ang)
        self._path = tr.map(body)

        # hit shape: stroked centreline (no holes -> easy to click)
        line = QPainterPath()
        line.moveTo(self.p1)
        line.lineTo(self.p2)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(t, 1.0))
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
        self._hit = stroker.createStroke(line)
        if length < 0.01:
            self._hit.addEllipse(self.p1, t, t)

        b = self._path.boundingRect().united(self._hit.boundingRect())
        self._bounds = b.adjusted(-24, -24, 24, 24)   # room for handles/label

        for op in self.openings:
            op.sync()
        self.update()
        if cascade and not self.is_open:
            for w in coincident_walls(self.scene(), self):
                w.rebuild(cascade=False)

    # -- QGraphicsItem interface ---------------------------------------------
    def boundingRect(self) -> QRectF:
        return self._bounds

    def shape(self) -> QPainterPath:
        return self._hit

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        fill = QColor(60, 62, 68) if self.wall_type == "exterior" else QColor(150, 152, 158)
        painter.setPen(QPen(QColor(25, 25, 25), 0))
        painter.setBrush(QBrush(fill))
        painter.drawPath(self._path)

        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        lod = max(lod, 1e-6)

        if self.isSelected():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(0, 122, 255), 0))
            painter.drawPath(self._path)
            if self._ends_editable():       # endpoint knobs only when active
                hs = 9.0 / lod
                painter.setPen(QPen(QColor(40, 40, 40), 0))
                painter.setBrush(QBrush(QColor(255, 200, 0)))
                for q in (self.p1, self.p2):
                    painter.drawRect(QRectF(q.x() - hs / 2, q.y() - hs / 2,
                                            hs, hs))

        if self.isSelected() or self._drawing:
            u = self.unit()
            n = QPointF(-u.y(), u.x())
            mid = QPointF((self.p1.x() + self.p2.x()) / 2,
                          (self.p1.y() + self.p2.y()) / 2)
            off = self.t / 2 + 12.0 / lod
            tp = QPointF(mid.x() + n.x() * off, mid.y() + n.y() * off)
            f = QFont()
            f.setPixelSize(max(2, int(13.0 / lod)))
            painter.setFont(f)
            painter.setPen(QPen(QColor(0, 90, 200), 0))
            painter.drawText(tp, fmt_ftin(self.length()))

    # -- interaction ----------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _ends_editable(self) -> bool:
        """Endpoint knobs are active when the wall is not part of a room, when
        it is an open wall, or once its corners have been unlocked via
        'Detach wall from room' -- moving a corner away opens that side."""
        return self.room is None or self.is_open or self._corners_unlocked

    def mousePressEvent(self, e):
        if self.group() is not None:
            # grouped: let the group own the drag.  Running the wall-slide
            # / join logic on a group child mutates p1/p2 in the wrong
            # coordinate space and join_endpoints/grow_walls can collapse
            # walls -- ignore so the press falls through to the group.
            self._mode = None
            e.ignore()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)
            return
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+click toggles membership of the selection set
            self.setSelected(not self.isSelected())
            self._mode = None
            e.accept()
            return
        if not self.isSelected():
            self.scene().clearSelection()
        self.setSelected(True)
        if self.room is not None:          # bring the owning room to the front
            self.room.raise_to_front()

        sp = e.scenePos()
        tol = max(8.0, 12.0 / self._view_scale())
        ends = self._ends_editable()       # endpoints locked while in a room
        if ends and QLineF(sp, self.p1).length() <= tol:
            self._mode = "p1"
            self._anchor = QPointF(self.p2)
        elif ends and QLineF(sp, self.p2).length() <= tol:
            self._mode = "p2"
            self._anchor = QPointF(self.p1)
        else:
            self._mode = "move"
            self._press = QPointF(sp)
            self._o1 = QPointF(self.p1)
            self._o2 = QPointF(self.p2)
            # the whole collinear side slides as one (so an open-wall gap rides
            # along); perpendicular walls attached to the SIDE's endpoints then
            # stretch -- corner joints fully, T-joints sideways only
            self._slide_u = self.unit()
            self._run = self._collinear_run()
            self._run_orig = [(w, QPointF(w.p1), QPointF(w.p2))
                              for w in self._run]
            run_ids = {id(w) for w in self._run}
            run_pts = [p for w in self._run for p in (w.p1, w.p2)]
            self._attached = []
            sc, length = self.scene(), self.length()
            ux, uy = self._slide_u.x(), self._slide_u.y()
            if sc is not None:
                for w in sc.items():
                    if not isinstance(w, WallItem) or id(w) in run_ids:
                        continue
                    for attr in ("p1", "p2"):
                        q = getattr(w, attr)
                        if any(QLineF(q, rp).length() < 0.6 for rp in run_pts):
                            self._attached.append((w, attr, QPointF(q), True))
                        else:
                            vx, vy = q.x() - self.p1.x(), q.y() - self.p1.y()
                            s = vx * ux + vy * uy
                            if (0.0 < s < length
                                    and abs(vy * ux - vx * uy) <= 0.75):
                                self._attached.append((w, attr, QPointF(q), False))

        if self._mode in ("p1", "p2"):
            moving = self.p1 if self._mode == "p1" else self.p2
            d = QLineF(self._anchor, moving)
            if d.length() > 1e-6:
                self._axis = QPointF(d.dx() / d.length(), d.dy() / d.length())
            else:
                self._axis = QPointF(1.0, 0.0)
        e.accept()

    def _endpoint_target(self, sp: QPointF, mods) -> QPointF:
        """Lengthen / shorten this wall.  The end rides the wall's own axis,
        grid-snapped, and STICKS to the projected line of a close orthogonal
        wall when it lines up (so you can pull an end into a corner) -- it
        never fuses to another wall's endpoint or body.  Shift = free re-angle.
        """
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))          # free re-angle, grid only
        return self._axis_target(sp)

    def _axis_target(self, sp: QPointF) -> QPointF:
        o, u = self._anchor, self._axis
        s = (sp.x() - o.x()) * u.x() + (sp.y() - o.y()) * u.y()
        proj = self._project_to_orthogonal(o, u, s)
        s = proj if proj is not None else wall_snap_len(s)
        if s < MIN_WALL_LEN:                        # never collapse the wall
            s = MIN_WALL_LEN
        return QPointF(o.x() + u.x() * s, o.y() + u.y() * s)

    def _project_to_orthogonal(self, o: QPointF, u: QPointF, s: float):
        """The exact axis distance at which this wall's axis crosses the
        projected line of a NEARBY ORTHOGONAL wall, when the drag is within the
        stick tolerance of it -- else None (so it falls back to the grid).
        Snaps only to such lines, never to endpoints or bodies."""
        sc = self.scene()
        if sc is None:
            return None
        stick = max(WALL_PROJECT_STICK, 16.0 / max(self._view_scale(), 1e-6))
        best_s, best_d = None, stick
        for w in sc.items():
            if (not isinstance(w, WallItem) or w is self or w.is_open
                    or w.length() < 1e-6):
                continue
            v = w.unit()
            if abs(u.x() * v.x() + u.y() * v.y()) > 0.12:      # not orthogonal
                continue
            p = line_intersection(o, u, w.p1, v)
            if p is None:
                continue
            sp_ = (p.x() - o.x()) * u.x() + (p.y() - o.y()) * u.y()
            if sp_ <= MIN_WALL_LEN:                 # behind / at the anchor
                continue
            d = abs(sp_ - s)                         # drag distance to the line
            if d <= best_d and \
                    dist_point_segment(p, w.p1, w.p2) <= WALL_PROJECT_NEAR:
                best_s, best_d = sp_, d
        return best_s

    def _corner_target(self, sp: QPointF, mods) -> QPointF:
        """Endpoint target for a room wall whose corners were unlocked: move
        the end along the wall (Shift = any direction), grid-snapped and
        sticking to an orthogonal wall's projected line, WITHOUT fusing to
        neighbours -- so the corner can be pulled away to open a side."""
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))
        return self._axis_target(sp)

    def _collinear_run(self):
        """The full room 'side' this wall lies on: every wall of the same room
        (real and dashed open walls) that is collinear with it.  Body-sliding
        the wall moves the whole side -- including the open-wall gap -- as one,
        so the dashed segment travels with the wall."""
        if self.room is None or self.length() < 1e-6:
            return [self]
        u = self.unit()
        run = []
        for w in self.room.walls:
            if w is self:
                run.append(w)
                continue
            if w.length() < 1e-6:
                continue
            wu = w.unit()
            if abs(wu.x() * u.y() - wu.y() * u.x()) > 0.02:   # not parallel
                continue
            d = abs((w.p1.x() - self.p1.x()) * u.y()           # off this line?
                    - (w.p1.y() - self.p1.y()) * u.x())
            if d <= 1.5:
                run.append(w)
        return run

    def mouseMoveEvent(self, e):
        if self._mode is None:
            return
        sp = e.scenePos()
        target = (self._corner_target if self.room is not None
                  else self._endpoint_target)
        if self._mode == "p1":
            self.p1 = target(sp, e.modifiers())
        elif self._mode == "p2":
            self.p2 = target(sp, e.modifiers())
        elif self._mode == "move":
            delta = QPointF(sp.x() - self._press.x(), sp.y() - self._press.y())
            if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl: move freely in any direction
                np1 = wall_snap(QPointF(self._o1.x() + delta.x(),
                                        self._o1.y() + delta.y()))
                dx, dy = np1.x() - self._o1.x(), np1.y() - self._o1.y()
            else:
                # slide only orthogonally to the wall: each end rides the
                # line projected perpendicular from its starting point, so
                # attached rooms stay rectangular instead of shearing
                ux, uy = self._slide_u.x(), self._slide_u.y()
                nx_, ny_ = -uy, ux
                s = wall_snap_len(delta.x() * nx_ + delta.y() * ny_)
                dx, dy = nx_ * s, ny_ * s
            # translate the whole collinear side (self + open-wall gap + any
            # collinear neighbours) by the same delta
            for w, o1, o2 in self._run_orig:
                w.p1 = QPointF(o1.x() + dx, o1.y() + dy)
                w.p2 = QPointF(o2.x() + dx, o2.y() + dy)
                if w is not self:
                    w.rebuild()
            # corner joints follow fully; T-joints follow only the sideways
            # part of the slide so they stretch instead of tilting
            ux, uy = self._slide_u.x(), self._slide_u.y()
            along = dx * ux + dy * uy
            px, py = dx - along * ux, dy - along * uy
            for w, attr, orig, is_corner in self._attached:
                if is_corner:
                    setattr(w, attr, QPointF(orig.x() + dx, orig.y() + dy))
                else:
                    setattr(w, attr, QPointF(orig.x() + px, orig.y() + py))
                w.rebuild()
        self.rebuild()
        e.accept()

    def mouseReleaseEvent(self, e):
        if self._mode is not None:
            # stretching an end (p1/p2) never re-joins or grows to meet another
            # wall -- it sticks only to orthogonal projected lines while
            # dragging and stops where released; only a body-slide auto-joins
            endpoint_edit = self._mode in ("p1", "p2")
            corner_drag = endpoint_edit and self.room is not None
            if not endpoint_edit:
                self.join_endpoints()
            rebuild_all_walls(self.scene())
            # dragging a corner back so the room is fully walled again fuses
            # the wall back in: re-lock its corners (right-click to detach
            # again)
            if (corner_drag and self._corners_unlocked
                    and not any(w.is_open for w in self.room.walls)):
                self._corners_unlocked = False
                self.room.raise_to_front()       # normalise z back to siblings
        self._mode = None
        e.accept()

    def join_endpoints(self):
        """Snap each endpoint onto a nearby endpoint of another wall, or fuse
        it onto the body of a wall it stops on (T-junction), within JOIN_TOL.
        Never grows a wall toward a far one -- if it doesn't reach, the gap is
        left for the user to close by hand."""
        for attr, other in (("p1", "p2"), ("p2", "p1")):
            p = getattr(self, attr)
            q = nearest_wall_endpoint(self.scene(), p, JOIN_TOL, exclude=self)
            if q is None:
                hit = nearest_wall_body(self.scene(), p, JOIN_TOL, exclude=self)
                if hit is not None:
                    target, q = hit
                    ip = axis_wall_intersection(target, getattr(self, other), p)
                    if ip is not None and QLineF(ip, p).length() <= JOIN_TOL * 2:
                        q = ip
            if q is not None:
                setattr(self, attr, q)
        self.rebuild()

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_ext = menu.addAction("Exterior wall (6\")")
        a_ext.setCheckable(True)
        a_ext.setChecked(self.wall_type == "exterior")
        a_int = menu.addAction("Interior wall (4 1/2\")")
        a_int.setCheckable(True)
        a_int.setChecked(self.wall_type == "interior")
        a_detach = None
        if self.room is not None:
            menu.addSeparator()
            a_detach = menu.addAction("Detach wall from room")
        menu.addSeparator()
        a_del = menu.addAction("Delete wall")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        sc = self.scene()
        if chosen is a_ext:
            self.wall_type = "exterior"
            self.rebuild()
        elif chosen is a_int:
            self.wall_type = "interior"
            self.rebuild()
        elif a_detach is not None and chosen is a_detach and sc is not None:
            self.setSelected(True)
            detach_wall_from_room(sc, self)   # opens the vacated edge
        elif chosen is a_del and sc is not None:
            sc.removeItem(self)
            rebuild_all_walls(sc)
        e.accept()


class OpenWall(WallItem):
    """A dashed placeholder for a room edge that has no built wall.

    It belongs to a room's edge loop (so the room stays closed for area
    and re-detection through the gap) and carries the SAME drag controls
    as a wall, but it does not block room flood-fill and is drawn as a thin
    dashed line.  Open walls are derived from a room's open edges, so they
    are regenerated by bind_room_walls rather than serialized."""

    is_open = True

    def __init__(self, p1: QPointF, p2: QPointF, room=None):
        super().__init__(p1, p2, "interior")
        self.room = room
        self.setZValue(0)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        lod = max(option.levelOfDetailFromTransform(painter.worldTransform()),
                  1e-6)
        pen = QPen(QColor(90, 120, 170), max(1.2, 1.6 / lod),
                   Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(self.p1, self.p2)
        if self.isSelected():
            hs = 9.0 / lod
            painter.setPen(QPen(QColor(40, 40, 40), 0))
            painter.setBrush(QBrush(QColor(255, 200, 0)))
            for q in (self.p1, self.p2):
                painter.drawRect(QRectF(q.x() - hs / 2, q.y() - hs / 2, hs, hs))


# ----------------------------------------------------------------------------
# Door / window opening
# ----------------------------------------------------------------------------
class OpeningItem(QGraphicsItem):
    """A door or window.  Child of its wall; local x runs along the wall,
    local y across the thickness.  `s` = distance of centre from wall.p1."""

    def __init__(self, wall: WallItem, kind: str, code: str, s: float):
        super().__init__(wall)
        self.wall = wall
        self.kind = kind                  # 'door' | 'window'
        self.code = "3280"
        self.width, self.height = 32.0, 80.0
        self.door_type = "LH"
        self.swing = -1                   # -1 / +1 : which face it swings to
        self.s = s
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(2)
        self.set_code(code, rebuild=False)
        self.sync()

    # -- data -----------------------------------------------------------------
    def set_code(self, code: str, rebuild: bool = True):
        w, h = parse_wwhh(code)
        if w > self.wall.length():
            raise ValueError("Opening is wider than the wall.")
        self.code = code.strip()
        self.prepareGeometryChange()
        self.width, self.height = w, h
        if rebuild:
            self.wall.rebuild()           # re-cuts the gap, re-syncs children

    def set_door_type(self, name: str):
        """Change the door type; garage doors auto-size an undersized
        opening to their standard size (if the wall is long enough)."""
        self.prepareGeometryChange()
        self.door_type = name
        if name in GARAGE_DEFAULTS:
            code, min_w = GARAGE_DEFAULTS[name]
            if self.width < min_w:
                try:
                    self.set_code(code)
                except ValueError:
                    pass                  # wall too short: keep the size
        self.update()

    def sync(self):
        """Reposition/orient on the wall after any wall geometry change."""
        self.prepareGeometryChange()
        self.setPos(self.wall.point_at(self.s))
        self.setRotation(math.degrees(self.wall.angle_rad()))
        self.update()

    # -- QGraphicsItem ---------------------------------------------------------
    def boundingRect(self) -> QRectF:
        # Tightly bound only what paint() actually draws (local coords: x
        # along the wall, y across it).  A swing arc / overhead outline
        # reaches out on its swing side; everything else stays in the
        # opening footprint.  (A symmetric width+16 margin made the rect
        # huge for wide openings, ballooning any enclosing group's box.)
        w, t = self.width, self.wall.t
        x0, x1, y0, y1 = -w / 2, w / 2, -t / 2, t / 2
        if self.kind == "door":
            dt = self.door_type
            reach = {"LH": w, "RH": w, "FRENCH": w / 2,
                     "BIFOLD": 0.4 * w}.get(dt, 0.0)
            if dt in GARAGE_DEFAULTS:
                reach = min(self.height, 96.0)
            if self.swing < 0:
                y0 -= reach
            else:
                y1 += reach
            if dt == "POCKET":
                x0 -= w               # the panel slides into the wall
        pad = 18.0                    # line widths + the WWHH label
        return QRectF(x0 - pad, y0 - pad,
                      (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)

    def shape(self) -> QPainterPath:
        w, t = self.width, self.wall.t
        p = QPainterPath()
        p.addRect(QRectF(-w / 2, -t / 2 - 1, w, t + 2))
        return p

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, t = self.width, self.wall.t
        ink = QPen(QColor(20, 20, 20), 0)
        painter.setPen(ink)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # jambs (the cut ends of the wall)
        painter.drawLine(QPointF(-w / 2, -t / 2), QPointF(-w / 2, t / 2))
        painter.drawLine(QPointF(w / 2, -t / 2), QPointF(w / 2, t / 2))

        if self.kind == "window":
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(QRectF(-w / 2, -t / 2, w, t))
            painter.drawLine(QPointF(-w / 2, 0), QPointF(w / 2, 0))   # glazing
        else:
            self._paint_door(painter, w, t)

        # WWHH label, kept clear of the swing side
        f = QFont()
        f.setPixelSize(6)
        painter.setFont(f)
        painter.setPen(QPen(QColor(70, 70, 90) if not self.isSelected()
                            else QColor(0, 122, 255), 0))
        label = self.code if self.kind == "window" else f"{self.code} {self.door_type}"
        if self.kind == "door" and self.swing < 0:
            ty = t / 2 + 9
        else:
            ty = -t / 2 - 3
        painter.drawText(QPointF(-w / 2, ty), label)

        if self.isSelected():
            painter.setPen(QPen(QColor(0, 122, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-w / 2, -t / 2 - 1, w, t + 2))

    def _swing_arc(self, painter, hx, hy, sy, radius, hinge_left):
        """Door panel + quarter-circle swing arc from a hinge point."""
        painter.drawLine(QPointF(hx, hy), QPointF(hx, hy + sy * radius))
        rect = QRectF(hx - radius, hy - radius, 2 * radius, 2 * radius)
        if sy < 0:
            start = 0 if hinge_left else 90      # ends at N (visually up)
        else:
            start = 270 if hinge_left else 180   # ends at S (visually down)
        painter.drawArc(rect, start * 16, 90 * 16)

    def _paint_door(self, painter, w, t):
        sy = self.swing
        face = sy * t / 2
        dt = self.door_type
        white = QBrush(QColor(255, 255, 255))

        if dt == "LH":
            self._swing_arc(painter, -w / 2, face, sy, w, hinge_left=True)
        elif dt == "RH":
            self._swing_arc(painter, w / 2, face, sy, w, hinge_left=False)
        elif dt == "FRENCH":
            self._swing_arc(painter, -w / 2, face, sy, w / 2, hinge_left=True)
            self._swing_arc(painter, w / 2, face, sy, w / 2, hinge_left=False)
        elif dt == "BIFOLD":
            rise = sy * 0.35 * w
            painter.drawPolyline(QPolygonF([
                QPointF(-w / 2, face), QPointF(-w / 4, face + rise),
                QPointF(0, face)]))
            painter.drawPolyline(QPolygonF([
                QPointF(0, face), QPointF(w / 4, face + rise),
                QPointF(w / 2, face)]))
        elif dt == "POCKET":
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.setBrush(white)
            painter.drawRect(QRectF(-w / 2 - w, -t / 2 + 0.75, w, t - 1.5))
            painter.setPen(QPen(QColor(20, 20, 20), 0))
            painter.drawRect(QRectF(-w / 2, -t / 6, w / 2, t / 3))
        elif dt == "SLIDER":
            painter.setBrush(white)
            pw = 0.55 * w
            painter.drawRect(QRectF(-w / 2, -t * 0.35, pw, t * 0.30))
            painter.drawRect(QRectF(w / 2 - pw, t * 0.05, pw, t * 0.30))
        elif dt == "DOORWAY":
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.drawLine(QPointF(-w / 2, -t / 2), QPointF(w / 2, -t / 2))
            painter.drawLine(QPointF(-w / 2, t / 2), QPointF(w / 2, t / 2))
        elif dt in GARAGE_DEFAULTS:
            # closed panel in the opening + dashed OVERHEAD outline of the
            # open door projecting inward (the swing side), as deep as the
            # door is tall
            painter.setBrush(white)
            painter.drawRect(QRectF(-w / 2, -t * 0.25, w, t * 0.5))
            depth = sy * min(self.height, 96.0)
            y0 = sy * t / 2
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-w / 2, min(y0, y0 + depth),
                                    w, abs(depth)))
            if dt == "GARAGE-2":          # double-wide: two-car divider
                painter.drawLine(QPointF(0, y0), QPointF(0, y0 + depth))

    # -- interaction -------------------------------------------------------------
    def mousePressEvent(self, e):
        if self.wall is not None and self.wall.group() is not None:
            # the opening's wall is grouped: let the group own the drag
            # instead of sliding the opening along its wall
            e.ignore()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)
            return
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.setSelected(not self.isSelected())    # toggle membership
            e.accept()
            return
        if not self.isSelected():
            self.scene().clearSelection()
        self.setSelected(True)
        if self.wall is not None and self.wall.room is not None:
            self.wall.room.raise_to_front()
        e.accept()

    def mouseMoveEvent(self, e):
        if self.wall is not None and self.wall.group() is not None:
            e.ignore()
            return
        # slide along the wall, snapping to the nearest inch
        s = round(self.wall.s_of(e.scenePos()))
        half = self.width / 2
        self.s = min(max(s, half), max(half, self.wall.length() - half))
        self.wall.rebuild()             # cascades to the coincident party wall
        e.accept()

    def mouseDoubleClickEvent(self, e):
        self._prompt_size()
        e.accept()

    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def _prompt_size(self):
        v = self._view()
        code, ok = QInputDialog.getText(
            v, f"{self.kind.title()} size",
            'Size WWHH (width inches, height inches):', text=self.code)
        if not ok:
            return
        try:
            self.set_code(code)
        except ValueError as ex:
            QMessageBox.warning(v, "Invalid size", str(ex))

    def contextMenuEvent(self, e):
        menu = QMenu()
        type_actions = {}
        if self.kind == "door":
            tmenu = menu.addMenu("Type")
            for name in DOOR_TYPES:
                a = tmenu.addAction(name)
                a.setCheckable(True)
                a.setChecked(name == self.door_type)
                type_actions[a] = name
            a_flip = menu.addAction("Flip swing side")
        else:
            a_flip = None
        a_size = menu.addAction("Set size (WWHH)\u2026")
        menu.addSeparator()
        a_del = menu.addAction(f"Delete {self.kind}")
        a_front, a_back = add_front_back_actions(menu)

        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen in type_actions:
            self.set_door_type(type_actions[chosen])
        elif chosen is a_flip and a_flip is not None:
            self.swing = -self.swing
            self.update()
        elif chosen is a_size:
            self._prompt_size()
        elif chosen is a_del:
            wall, sc = self.wall, self.scene()
            if self in wall.openings:
                wall.openings.remove(self)
            sc.removeItem(self)
            wall.rebuild()
        e.accept()


# ----------------------------------------------------------------------------
# Room
# ----------------------------------------------------------------------------
class RoomItem(QGraphicsItem):
    """A named room: the wall-enclosed region around an anchor point.

    The translucent region, label and dimension arrows paint in scene
    coords (pos stays 0,0).  Only the label text is clickable, so wall
    editing and panning inside the room keep working.  Right-click the
    name for dimensions / properties / rename / delete."""

    def __init__(self, name: str, anchor: QPointF, path: QPainterPath,
                 area_sqft: float, properties=None, corners=None):
        super().__init__()
        self.name = name
        self.anchor = QPointF(anchor)
        self.label_offset = QPointF(0.0, 0.0)   # label drag, relative to anchor
        self._dragging_label = False
        self.path = QPainterPath(path)
        self.area_sqft = float(area_sqft)
        self.corners = [QPointF(c) for c in corners] if corners else None
        self.walls = []                  # WallItems this room owns (edge loop)
        self._moving_room = False        # drag-the-name moves the whole room
        self._room_grab = QPointF(0.0, 0.0)
        self.show_dims = False
        self.properties = dict(DEFAULT_ROOM_PROPS)
        if properties:
            self.properties.update(properties)
        self._sync_corner_props()
        self._font = QFont(FONT_FAMILY)
        self._font.setPixelSize(14)       # 14" tall text reads well at plan scale
        self._sub_font = QFont(FONT_FAMILY)
        self._sub_font.setPixelSize(9)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # above the walls: the fill only covers floor space (it stops at
        # the wall faces) and the perimeter dashes must paint OVER the walls
        self.setZValue(4)

    # -- data ------------------------------------------------------------------
    def set_region(self, path: QPainterPath, area_sqft: float, corners=None):
        self.prepareGeometryChange()
        self.path = QPainterPath(path)
        self.area_sqft = float(area_sqft)
        self.corners = [QPointF(c) for c in corners] if corners else None
        self._sync_corner_props()
        self.update()

    def _sync_corner_props(self):
        """Mirror the perimeter corner coordinates into the properties."""
        if self.corners:
            self.properties["perimeter_corners"] = [
                [round(c.x(), 2), round(c.y(), 2)] for c in self.corners]
        else:
            self.properties.pop("perimeter_corners", None)

    def interior_rect(self) -> QRectF:
        return self.path.boundingRect()

    def perimeter_in(self) -> float:
        if self.corners:
            n = len(self.corners)
            return sum(QLineF(self.corners[i], self.corners[(i + 1) % n]).length()
                       for i in range(n))
        poly = self.path.toFillPolygon()
        return sum(QLineF(poly[i], poly[i + 1]).length()
                   for i in range(poly.size() - 1))

    def _perimeter_span(self, w) -> tuple | None:
        """[s0, s1] of wall `w`'s centreline that runs along this room's
        perimeter, or None when the wall doesn't follow any edge of it."""
        if not self.corners:
            return None
        u, length = w.unit(), w.length()
        lo = hi = None
        n = len(self.corners)
        for i in range(n):
            a, b = self.corners[i], self.corners[(i + 1) % n]
            da = abs((a.y() - w.p1.y()) * u.x() - (a.x() - w.p1.x()) * u.y())
            db = abs((b.y() - w.p1.y()) * u.x() - (b.x() - w.p1.x()) * u.y())
            if max(da, db) > 1.0:         # edge not collinear with the wall
                continue
            sa = (a.x() - w.p1.x()) * u.x() + (a.y() - w.p1.y()) * u.y()
            sb = (b.x() - w.p1.x()) * u.x() + (b.y() - w.p1.y()) * u.y()
            s0, s1 = max(0.0, min(sa, sb)), min(length, max(sa, sb))
            if s1 - s0 < 1.0:
                continue
            lo = s0 if lo is None else min(lo, s0)
            hi = s1 if hi is None else max(hi, s1)
        if lo is None or hi - lo < MIN_WALL_LEN:
            return None
        return lo, hi

    def _copy_spec(self) -> dict:
        """Clipboard payload: the room plus its bounding walls/openings,
        each wall trimmed to the stretch that follows the room perimeter
        (shared/through walls don't drag their full length along)."""
        walls = []
        for w in self.bounding_walls():
            span = self._perimeter_span(w)
            if span is None:
                if self.corners:
                    continue              # touches the room but isn't part
                span = (0.0, w.length())  # of the perimeter -> don't copy
            lo, hi = span
            tp1, tp2 = w.point_at(lo), w.point_at(hi)
            walls.append({
                "type": w.wall_type,
                "p1": [tp1.x(), tp1.y()],
                "p2": [tp2.x(), tp2.y()],
                "openings": [{
                    "kind": op.kind, "code": op.code, "s": op.s - lo,
                    "door_type": op.door_type, "swing": op.swing,
                } for op in w.openings if lo <= op.s <= hi],
            })
        return {
            "name": self.name,
            "anchor": [self.anchor.x(), self.anchor.y()],
            "show_dimensions": self.show_dims,
            "properties": dict(self.properties),
            "walls": walls,
        }

    def _boundary_band(self) -> QPainterPath:
        # wide enough to safely contain the wall centrelines: the flood
        # region edge sits up to t/2 + one raster cell from a centreline,
        # and a point exactly on the stroke edge tests as outside
        stroker = QPainterPathStroker()
        stroker.setWidth(3.0 * EXTERIOR_T)
        return stroker.createStroke(self.path)

    def bounding_walls(self):
        """Walls whose body touches this room's boundary."""
        sc = self.scene()
        if sc is None:
            return []
        band = self._boundary_band()
        return [it for it in sc.items()
                if isinstance(it, WallItem) and it._hit.intersects(band)]

    # -- owned walls (the room's edge loop) ----------------------------------
    def bind_wall(self, w):
        """Make this room the owner of wall `w` (stealing it from any prior
        owner).  A wall belongs to at most one room."""
        if w.room is self:
            if w not in self.walls:
                self.walls.append(w)
            return
        if w.room is not None:
            w.room.unbind_wall(w)
        w.room = self
        if w not in self.walls:
            self.walls.append(w)

    def unbind_wall(self, w):
        if w.room is self:
            w.room = None
        if w in self.walls:
            self.walls.remove(w)

    def clear_walls(self):
        for w in list(self.walls):
            self.unbind_wall(w)

    def room_openings(self):
        return [op for w in self.walls for op in w.openings]

    def raise_to_front(self):
        """Bring this room and its owned walls/openings above every other
        room (uses a running max-z on the window; z is not serialized)."""
        win = None
        v = self._view()
        if v is not None:
            win = getattr(v, "win", None)
        if win is None or not hasattr(win, "_z_top"):
            return
        win._z_top += 1
        base = win._z_top * 10
        for w in self.walls:
            # an unlocked wall sits just above its siblings so corner clicks
            # at a shared corner grab IT (to edit) rather than a locked neighbour
            w.setZValue(base + 1 if w._corners_unlocked else base)
        for op in self.room_openings():
            op.setZValue(base + 2)
        self.setZValue(base + 4)

    def opening_stats(self):
        """(window count, window glazing sq ft, door count) on this
        room's bounding walls, counting only openings that sit on the
        stretch of wall actually facing the room."""
        band = self._boundary_band()
        wins, win_area, doors = 0, 0.0, 0
        for wall in self.bounding_walls():
            for op in wall.openings:
                if not band.contains(wall.point_at(op.s)):
                    continue
                if op.kind == "window":
                    wins += 1
                    win_area += op.width * op.height / 144.0
                else:
                    doors += 1
        return wins, win_area, doors

    # editable properties, in display order, for the inventory listing
    PROP_LABELS = [
        ("room_type", "Room type"),
        ("ceiling_height_in", "Ceiling height"),
        ("ceiling_type", "Ceiling type"),
        ("floor_finish", "Floor finish"),
        ("wall_finish", "Wall finish"),
        ("baseboard", "Baseboard / trim"),
        ("crown_molding", "Crown molding"),
        ("hvac", "Heating / cooling"),
        ("electrical", "Electrical"),
        ("notes", "Notes"),
    ]

    def inventory_rows(self) -> list:
        """Two-column (name, value/quantity) rows describing the room:
        its properties, then every item in it — furnishings whose centre
        sits inside the room plus the doors/windows on its walls."""

        def clean(v) -> str:
            return " ".join(str(v).split())     # no tabs/newlines in cells

        rows = [("Room", self.name), ("", ""), ("Property", "Value"),
                ("Area (sq ft)", f"{self.area_sqft:.1f}")]
        r = self.interior_rect()
        rows.append(("Interior width", fmt_ftin(r.width())))
        rows.append(("Interior length", fmt_ftin(r.height())))
        rows.append(("Perimeter", fmt_ftin(self.perimeter_in())))
        wins, win_area, doors = self.opening_stats()
        rows.append(("Window glazing (sq ft)", f"{win_area:.1f}"))
        for key, label in self.PROP_LABELS:
            v = self.properties.get(key, "")
            if key == "ceiling_height_in":
                v = fmt_ftin(float(v or 0))
            elif key == "crown_molding":
                v = "Yes" if v else "No"
            rows.append((label, clean(v)))

        counts = {}
        sc = self.scene()
        if sc is not None:
            for it in sc.items():
                if isinstance(it, FurnishingItem) and \
                        self.path.contains(it.pos()):
                    counts[it.name] = counts.get(it.name, 0) + 1
        band = self._boundary_band()
        for wall in self.bounding_walls():
            for op in wall.openings:
                if not band.contains(wall.point_at(op.s)):
                    continue
                if op.kind == "window":
                    name = f'Window {op.width:g}" × {op.height:g}"'
                else:
                    name = (f'Door {op.width:g}" × {op.height:g}" '
                            f'({op.door_type})')
                counts[name] = counts.get(name, 0) + 1

        rows += [("", ""), ("Item", "Quantity")]
        rows += [(n, str(q)) for n, q in sorted(counts.items())]
        return rows

    def inventory_text(self) -> str:
        """The inventory as tab-separated text, ready for Excel."""
        return "\n".join(f"{a}\t{b}" for a, b in self.inventory_rows())

    # -- QGraphicsItem -----------------------------------------------------------
    def _label_centre(self) -> QPointF:
        return QPointF(self.anchor.x() + self.label_offset.x(),
                       self.anchor.y() + self.label_offset.y())

    def _label_rect(self) -> QRectF:
        fm = QFontMetricsF(self._font)
        w = max(fm.horizontalAdvance(self.name), 48.0) + 10.0
        h = fm.height() + 13.0
        c = self._label_centre()
        return QRectF(c.x() - w / 2, c.y() - h / 2, w, h)

    def boundingRect(self) -> QRectF:
        r = self.path.boundingRect().united(self._label_rect())
        if self.corners:
            r = r.united(QPolygonF(self.corners).boundingRect())
        return r.adjusted(-24, -24, 24, 24)

    def shape(self) -> QPainterPath:
        p = QPainterPath()
        p.addRect(self._label_rect())
        return p

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(120, 170, 255, 26)))
        painter.drawPath(self.path)
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 122, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path)

        if self.corners and self.isSelected():
            # perimeter along wall centrelines, shown while selected
            painter.setPen(QPen(QColor(0, 110, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(QPolygonF(self.corners))

        r = self._label_rect()
        painter.setFont(self._font)
        painter.setPen(QPen(QColor(40, 40, 70), 0))
        painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                         | Qt.AlignmentFlag.AlignTop, self.name)
        painter.setFont(self._sub_font)
        painter.setPen(QPen(QColor(115, 115, 135), 0))
        painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                         | Qt.AlignmentFlag.AlignBottom,
                         f"{self.area_sqft:.0f} sq ft")
        if self.show_dims:
            self._paint_dims(painter)

    def _paint_dims(self, painter):
        """Double-headed arrows along every wall edge enclosing the room.
        Falls back to width/length arrows when no perimeter was traced."""
        col = QColor(178, 58, 40)
        painter.setPen(QPen(col, 0))
        painter.setBrush(QBrush(col))
        painter.setFont(self._sub_font)
        fm = QFontMetricsF(self._sub_font)

        if self.corners:
            n = len(self.corners)
            edges = []
            for i in range(n):
                a, b = self.corners[i], self.corners[(i + 1) % n]
                d = QLineF(a, b)
                length = d.length()
                if length < 18:
                    continue
                edges.append((a, b, length, d.dx() / length, d.dy() / length))
            shown = []
            for edge in edges:
                _, _, length, ux, uy = edge
                # opposite walls (anti-parallel) of equal length are
                # dimensioned only once
                if any(ux * vx + uy * vy < -0.999 and abs(length - vlen) < 1.0
                       for (_, _, vlen, vx, vy) in shown):
                    continue
                shown.append(edge)
            for a, b, length, ux, uy in shown:
                nx_, ny_ = -uy, ux        # room interior is left of the edge
                off = 14.0
                pa = QPointF(a.x() + ux * 4 + nx_ * off,
                             a.y() + uy * 4 + ny_ * off)
                pb = QPointF(b.x() - ux * 4 + nx_ * off,
                             b.y() - uy * 4 + ny_ * off)
                self._arrow(painter, pa, pb)
                text = fmt_ftin(length)
                ang = math.degrees(math.atan2(uy, ux))
                if ang > 90.0 or ang <= -90.0:
                    ang -= 180.0          # keep text upright
                painter.save()
                painter.translate(
                    QPointF((a.x() + b.x()) / 2 + nx_ * (off + 6),
                            (a.y() + b.y()) / 2 + ny_ * (off + 6)))
                painter.rotate(ang)
                painter.drawText(
                    QPointF(-fm.horizontalAdvance(text) / 2, 3), text)
                painter.restore()
            return

        r = self.interior_rect()
        if r.width() < 12 or r.height() < 12:
            return
        lc = self._label_centre()
        y = r.center().y()                # keep clear of the name label
        if abs(y - lc.y()) < 22:
            y = min(r.bottom() - 8, lc.y() + 26)
        self._arrow(painter, QPointF(r.left() + 1, y), QPointF(r.right() - 1, y))
        text = fmt_ftin(r.width())
        painter.drawText(QPointF(r.center().x() - fm.horizontalAdvance(text) / 2,
                                 y - 3), text)

        x = r.center().x()
        if abs(x - lc.x()) < 50:
            x = max(r.left() + 10, lc.x() - 60)
        self._arrow(painter, QPointF(x, r.top() + 1), QPointF(x, r.bottom() - 1))
        text = fmt_ftin(r.height())
        painter.save()
        painter.translate(x - 3, r.center().y() + fm.horizontalAdvance(text) / 2)
        painter.rotate(-90)
        painter.drawText(QPointF(0, 0), text)
        painter.restore()

    @staticmethod
    def _arrow(painter, a: QPointF, b: QPointF):
        painter.drawLine(a, b)
        d = QLineF(a, b)
        if d.length() < 1e-6:
            return
        ux, uy = d.dx() / d.length(), d.dy() / d.length()
        nx, ny = -uy, ux
        hl, hw = 7.0, 2.6                 # arrowhead length / half-width
        for tip, s in ((a, 1.0), (b, -1.0)):
            bx, by = tip.x() + ux * hl * s, tip.y() + uy * hl * s
            painter.drawPolygon(QPolygonF([
                tip,
                QPointF(bx + nx * hw, by + ny * hw),
                QPointF(bx - nx * hw, by - ny * hw)]))

    # -- interaction -------------------------------------------------------------
    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def _rename(self):
        name, ok = QInputDialog.getText(self._view(), "Room name", "Name:",
                                        text=self.name)
        if ok and name.strip():
            self.prepareGeometryChange()
            self.name = unique_room_name(self.scene(), name.strip(),
                                         exclude=self)
            self.update()

    def _translate(self, dx: float, dy: float):
        """Rigidly shift the room's owned walls, openings and region."""
        if not dx and not dy:
            return
        self.prepareGeometryChange()
        for w in self.walls:
            w.p1 = QPointF(w.p1.x() + dx, w.p1.y() + dy)
            w.p2 = QPointF(w.p2.x() + dx, w.p2.y() + dy)
            w.rebuild()                       # repositions its openings too
        self.path = QTransform.fromTranslate(dx, dy).map(self.path)
        if self.corners:
            self.corners = [QPointF(c.x() + dx, c.y() + dy)
                            for c in self.corners]
        self.anchor = QPointF(self.anchor.x() + dx, self.anchor.y() + dy)
        self._sync_corner_props()
        self.update()

    def mousePressEvent(self, e):
        # left-drag on the name moves the WHOLE room (walls, doors/windows and
        # region) when the room owns walls; Ctrl-drag keeps the legacy
        # label-only nudge (and unbound rooms always nudge the label).
        if (e.button() == Qt.MouseButton.LeftButton
                and self._label_rect().contains(e.pos())):
            self.setSelected(True)
            self.raise_to_front()
            ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
            self._dragging_label = True
            if self.walls and not ctrl:
                self._moving_room = True
                self._room_grab = QPointF(e.scenePos())
            else:
                self._moving_room = False
                c = self._label_centre()
                self._label_grab = QPointF(e.scenePos().x() - c.x(),
                                           e.scenePos().y() - c.y())
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging_label and self._moving_room:
            sp = e.scenePos()
            dx = wall_snap_len(sp.x() - self._room_grab.x())
            dy = wall_snap_len(sp.y() - self._room_grab.y())
            if dx or dy:
                self._translate(dx, dy)
                self._room_grab = QPointF(self._room_grab.x() + dx,
                                          self._room_grab.y() + dy)
            e.accept()
            return
        if self._dragging_label:
            self.prepareGeometryChange()
            nx = e.scenePos().x() - self._label_grab.x()
            ny = e.scenePos().y() - self._label_grab.y()
            self.label_offset = QPointF(nx - self.anchor.x(),
                                        ny - self.anchor.y())
            self.update()
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging_label:
            moved, self._dragging_label, self._moving_room = (
                self._moving_room, False, False)
            if moved:
                sc = self.scene()
                if sc is not None:
                    rebuild_all_walls(sc)     # re-detect region + re-bind walls
                self.raise_to_front()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        self._rename()
        e.accept()

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_dims = menu.addAction("Show dimensions")
        a_dims.setCheckable(True)
        a_dims.setChecked(self.show_dims)
        a_props = menu.addAction("Properties…")
        a_inv = menu.addAction("Inventory…")
        a_ren = menu.addAction("Rename…")
        a_copy = menu.addAction("Copy room")
        menu.addSeparator()
        a_del = menu.addAction("Delete room")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen is a_dims:
            self.show_dims = not self.show_dims
            self.update()
        elif chosen is a_copy:
            v = self._view()
            if v is not None:
                v.win.room_clipboard = self._copy_spec()
                v.win.status(f"Copied room '{self.name}' — with the Room "
                             "Name tool active, right-click a blank spot "
                             "to paste.")
        elif chosen is a_props:
            dlg = RoomPropertiesDialog(self, self._view())
            if dlg.exec() == QDialog.DialogCode.Accepted:
                dlg.apply()
                self.prepareGeometryChange()
                self.update()
                v = self._view()
                if v is not None:
                    v.win._update_totals()    # include / name may have changed
        elif chosen is a_inv:
            RoomInventoryDialog(self, self._view()).exec()
        elif chosen is a_ren:
            self._rename()
        elif chosen is a_del and self.scene() is not None:
            self.clear_walls()           # release walls (they stay on canvas)
            self.scene().removeItem(self)
        e.accept()


# ----------------------------------------------------------------------------
# Inventories — itemised tables of the plan, exportable to Excel as CSV.
# ----------------------------------------------------------------------------
FURN_INV_HEADERS = ["Item", "Quantity", "Unit price", "Line total"]
HOUSE_INV_HEADERS = ["Item", "Detail", "Quantity", "Size"]
TOTAL_INV_HEADERS = ["Category", "Item", "Quantity", "Value"]


def _money(v: float) -> str:
    return f"${v:,.0f}" if v > 0 else "-"


def classify_furnishings(scene):
    """Split the scene's furnishings into (interior, yard).  An item is
    interior only when its centre sits inside a non-garage room and it is
    not itself a garage-category item; cars, yard equipment and anything in
    the garage count as yard, as does anything outside the walls."""
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    interior, yard = [], []
    for it in scene.items():
        if not isinstance(it, FurnishingItem):
            continue
        pt = it.scenePos()
        room = next((r for r in rooms if r.path.contains(pt)), None)
        spec = furnishing_spec(it.kind) or {}
        is_garage_room = (room is not None
                          and room.properties.get("room_type", "") == "Garage")
        is_garage_item = spec.get("category", "") == "Garage"
        if room is not None and not is_garage_room and not is_garage_item:
            interior.append(it)
        else:
            yard.append(it)
    return interior, yard


def furnishing_inventory_rows(items):
    """Rows for FURN_INV_HEADERS aggregated by name, with a TOTAL row.
    Returns (rows, total_qty, total_cost)."""
    agg = {}
    for it in items:
        rec = agg.setdefault(it.name, {"qty": 0,
                                       "price": float(getattr(it, "price",
                                                              0.0) or 0.0)})
        rec["qty"] += 1
    rows, total_qty, total_cost = [], 0, 0.0
    for name in sorted(agg, key=str.lower):
        qty, price = agg[name]["qty"], agg[name]["price"]
        line = qty * price
        total_qty += qty
        total_cost += line
        rows.append([name, str(qty), _money(price), _money(line)])
    rows.append(["TOTAL", str(total_qty), "", _money(total_cost)])
    return rows, total_qty, total_cost


def _opening_counts(scene):
    """{label: qty} of doors/windows across every wall (each opening once)."""
    counts = {}
    for w in scene.items():
        if not isinstance(w, WallItem):
            continue
        for op in w.openings:
            if op.kind == "window":
                name = f'Window {op.width:g}" x {op.height:g}"'
            else:
                name = f'Door {op.width:g}" x {op.height:g}" ({op.door_type})'
            counts[name] = counts.get(name, 0) + 1
    return counts


def house_inventory_rows(scene):
    """Rows for HOUSE_INV_HEADERS: rooms, openings and walls. Returns
    (rows, total_sqft)."""
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    rows, total_sqft = [], 0.0
    for r in sorted(rooms, key=lambda x: x.name.lower()):
        total_sqft += r.area_sqft
        rows.append([r.name, r.properties.get("room_type", "") or "Room",
                     "1", f"{r.area_sqft:,.1f} sq ft"])
    for name, qty in sorted(_opening_counts(scene).items()):
        kind, _, detail = name.partition(" ")
        rows.append([kind, detail.strip(), str(qty), ""])
    for wt in ("exterior", "interior"):
        walls = [w for w in scene.items()
                 if isinstance(w, WallItem) and w.wall_type == wt]
        if walls:
            ft = sum(w.length() for w in walls) / FOOT
            rows.append([f"{wt.title()} wall", "", str(len(walls)),
                         f"{ft:,.1f} ft total"])
    return rows, total_sqft


def total_inventory_rows(scene):
    """Rows for TOTAL_INV_HEADERS: an executive summary of structure and
    furnishings with a grand total cost."""
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    total_sqft = sum(r.area_sqft for r in rooms)
    building_cost = total_sqft * float(SETTINGS.get("cost_per_sqft", 0.0))
    opens = _opening_counts(scene)
    doors = sum(q for n, q in opens.items() if n.startswith("Door"))
    windows = sum(q for n, q in opens.items() if n.startswith("Window"))
    interior, yard = classify_furnishings(scene)
    _, iq, ic = furnishing_inventory_rows(interior)
    _, yq, yc = furnishing_inventory_rows(yard)
    grand = building_cost + ic + yc
    return [
        ["Structure", "Rooms", str(len(rooms)), f"{total_sqft:,.1f} sq ft"],
        ["Structure", "Doors", str(doors), ""],
        ["Structure", "Windows", str(windows), ""],
        ["Structure", "Est. building cost", "", _money(building_cost)],
        ["Furnishings", "Interior items", str(iq), _money(ic)],
        ["Furnishings", "Yard items", str(yq), _money(yc)],
        ["Grand total", "Building + furnishings", str(iq + yq),
         _money(grand)],
    ]


def inventory_tsv(headers, rows) -> str:
    """Headers + rows as tab-separated text — Excel splits it into columns on
    paste.  Any tab/newline inside a cell is collapsed to single spaces."""
    def cell(v) -> str:
        return " ".join(str(v).split())

    lines = ["\t".join(cell(h) for h in headers)]
    for row in rows:
        cells = [cell(c) for c in row]
        cells += [""] * (len(headers) - len(cells))
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


class InventoryDialog(QDialog):
    """A read-only inventory shown as an aligned table.  'Copy to clipboard
    (TSV)' puts tab-separated values on the clipboard, which Excel splits
    straight into columns when pasted."""

    def __init__(self, title, headers, rows, parent=None, note=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.headers = list(headers)
        self.rows = [list(r) for r in rows]
        lay = QVBoxLayout(self)
        if note:
            lab = QLabel(note)
            lab.setWordWrap(True)
            lab.setStyleSheet("color: #555;")
            lay.addWidget(lab)
        self.table = QTableWidget(len(self.rows), len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        right = [self._align_right(h) for h in self.headers]
        for ri, row in enumerate(self.rows):
            bold = bool(row) and str(row[0]).strip().upper() in (
                "TOTAL", "GRAND TOTAL")
            for ci in range(len(self.headers)):
                val = row[ci] if ci < len(row) else ""
                cell = QTableWidgetItem(str(val))
                if right[ci]:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                          | Qt.AlignmentFlag.AlignVCenter)
                if bold:
                    f = cell.font()
                    f.setBold(True)
                    cell.setFont(f)
                self.table.setItem(ri, ci, cell)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.headers:
            self.table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumSize(560, 440)
        lay.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.btn_copy = buttons.addButton(
            "Copy to clipboard (TSV)", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_copy.clicked.connect(self._copy)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    @staticmethod
    def _align_right(header) -> bool:
        h = str(header).lower()
        return any(k in h for k in ("price", "total", "quantity", "qty",
                                    "value", "cost", "size", "$"))

    def tsv_text(self) -> str:
        return inventory_tsv(self.headers, self.rows)

    def _copy(self):
        QApplication.clipboard().setText(self.tsv_text())
        self.btn_copy.setText("Copied ✓")


class RoomInventoryDialog(InventoryDialog):
    """Per-room inventory (right-click a room name) as an aligned table:
    its properties followed by the furnishings and openings it contains."""

    def __init__(self, room: RoomItem, parent=None):
        super().__init__(f"Inventory — {room.name}", ["Field", "Value"],
                         room.inventory_rows(), parent=parent,
                         note="Copy to clipboard (TSV) to paste straight "
                              "into Excel.")


class AboutDialog(QDialog):
    """Help ▸ About: app identity plus where FloorPlanner keeps designs and
    its settings file, using the operating system's standard locations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        v = QVBoxLayout(self)
        head = QLabel(
            f'<h2 style="margin-bottom:2px;">{APP_NAME}</h2>'
            f'<p style="color:#555;margin-top:0;">Version {APP_VERSION} '
            "— a 2D architectural floor-plan editor built with PyQt6.<br>"
            f'<a href="{APP_URL}">{APP_URL}</a></p>')
        head.setTextFormat(Qt.TextFormat.RichText)
        head.setOpenExternalLinks(True)
        v.addWidget(head)

        info = QLabel(
            "<b>Where your files are kept</b>"
            "<ul style='margin-left:-20px;'>"
            "<li><b>Designs</b> (your plans) open and save by default in:"
            f"<br><code>{designs_dir()}</code></li>"
            "<li>The <b>settings file</b> (app preferences, including a "
            "remembered AI key) is:"
            f"<br><code>{settings_file()}</code></li>"
            "<li><b>Per-plan settings</b> — wall snap, rotation snap, canvas "
            "size and cost per square foot — are saved inside each plan's "
            "<code>.json</code> file.</li>"
            "</ul>"
            "These all use your operating system's standard locations. The "
            "AI key can also be supplied via the "
            "<code>ANTHROPIC_API_KEY</code> environment variable.")
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        v.addWidget(info)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.btn_designs = buttons.addButton(
            "Open designs folder", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_config = buttons.addButton(
            "Open settings folder", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_designs.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(designs_dir()))))
        self.btn_config.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(config_dir()))))
        buttons.rejected.connect(self.reject)
        v.addWidget(buttons)
        self.setMinimumWidth(480)


class RoomPropertiesDialog(QDialog):
    """Property sheet for a room.  Measured values (area, dimensions,
    perimeter, glazing, counts) are computed from the plan and shown
    read-only; the rest are editable and saved with the plan."""

    def __init__(self, room: RoomItem, parent=None):
        super().__init__(parent)
        self.room = room
        self.setWindowTitle(f"Room properties — {room.name}")
        form = QFormLayout(self)
        r = room.interior_rect()
        wins, win_area, doors = room.opening_stats()
        p = room.properties

        self.ed_name = QLineEdit(room.name)
        form.addRow("Name", self.ed_name)
        self.cb_type = self._combo(ROOM_TYPES, p.get("room_type", ""))
        form.addRow("Room type", self.cb_type)

        form.addRow("Area", QLabel(f"{room.area_sqft:.1f} sq ft"))
        self.ck_include = QCheckBox("Include in total square footage")
        self.ck_include.setChecked(bool(p.get("include_sqft", True)))
        form.addRow("", self.ck_include)
        form.addRow("Interior width", QLabel(fmt_ftin(r.width())))
        form.addRow("Interior length", QLabel(fmt_ftin(r.height())))
        form.addRow("Perimeter", QLabel(fmt_ftin(room.perimeter_in())))
        if room.corners:
            txt = "  ".join(f"({fmt_ftin(c.x())}, {fmt_ftin(c.y())})"
                            for c in room.corners)
        else:
            txt = "—  (no closed wall loop traced)"
        lab_c = QLabel(txt)
        lab_c.setWordWrap(True)
        form.addRow("Corners", lab_c)
        form.addRow("Windows", QLabel(f"{wins}  ({win_area:.1f} sq ft glazing)"))
        form.addRow("Doors", QLabel(str(doors)))

        self.sp_ceiling = QDoubleSpinBox()
        self.sp_ceiling.setRange(60.0, 300.0)
        self.sp_ceiling.setSuffix(" in")
        self.sp_ceiling.setValue(float(p.get("ceiling_height_in", 96.0)))
        form.addRow("Ceiling height", self.sp_ceiling)

        self.cb_ceiling = self._combo(CEILING_TYPES, p.get("ceiling_type", "Flat"))
        form.addRow("Ceiling type", self.cb_ceiling)
        self.cb_floor = self._combo(FLOOR_FINISHES, p.get("floor_finish", ""))
        form.addRow("Floor finish", self.cb_floor)
        self.cb_wall = self._combo(WALL_FINISHES, p.get("wall_finish", ""))
        form.addRow("Wall finish", self.cb_wall)
        self.ed_base = QLineEdit(str(p.get("baseboard", "")))
        form.addRow("Baseboard / trim", self.ed_base)
        self.ck_crown = QCheckBox()
        self.ck_crown.setChecked(bool(p.get("crown_molding", False)))
        form.addRow("Crown molding", self.ck_crown)
        self.cb_hvac = self._combo(HVAC_TYPES, p.get("hvac", ""))
        form.addRow("Heating / cooling", self.cb_hvac)
        self.ed_elec = QLineEdit(str(p.get("electrical", "")))
        form.addRow("Electrical", self.ed_elec)
        self.ed_notes = QPlainTextEdit(str(p.get("notes", "")))
        self.ed_notes.setFixedHeight(70)
        form.addRow("Notes", self.ed_notes)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    @staticmethod
    def _combo(items, value):
        cb = QComboBox()
        cb.setEditable(True)
        cb.addItems(items)
        cb.setCurrentText(str(value))
        return cb

    def apply(self):
        name = self.ed_name.text().strip()
        if name:
            sc = self.room.scene()
            if sc is not None:
                name = unique_room_name(sc, name, exclude=self.room)
            self.room.name = name
        self.room.properties.update({
            "room_type": self.cb_type.currentText().strip(),
            "include_sqft": self.ck_include.isChecked(),
            "ceiling_height_in": self.sp_ceiling.value(),
            "ceiling_type": self.cb_ceiling.currentText().strip(),
            "floor_finish": self.cb_floor.currentText().strip(),
            "wall_finish": self.cb_wall.currentText().strip(),
            "baseboard": self.ed_base.text().strip(),
            "crown_molding": self.ck_crown.isChecked(),
            "hvac": self.cb_hvac.currentText().strip(),
            "electrical": self.ed_elec.text().strip(),
            "notes": self.ed_notes.toPlainText(),
        })


# ----------------------------------------------------------------------------
# View (zoom / pan / tools)
# ----------------------------------------------------------------------------
class SettingsDialog(QDialog):
    """File > Settings…: plan-wide preferences, saved in the plan file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        form = QFormLayout(self)

        self.cb_snap = QComboBox()
        vals = list(WALL_SNAP_CHOICES)
        cur = SETTINGS["wall_snap_in"]
        if cur not in vals:
            vals = sorted(set(vals) | {cur})
        for v in vals:
            self.cb_snap.addItem(f'{v:g}"', v)
        self.cb_snap.setCurrentIndex(vals.index(cur))
        form.addRow("Wall snap (on centre)", self.cb_snap)

        self.sp_rot = QDoubleSpinBox()
        self.sp_rot.setRange(1.0, 90.0)
        self.sp_rot.setDecimals(1)
        self.sp_rot.setSuffix("°")
        self.sp_rot.setValue(float(SETTINGS["rotate_snap_deg"]))
        form.addRow("Rotation snap (Ctrl-drag)", self.sp_rot)

        self.sp_cw = QDoubleSpinBox()
        self.sp_cw.setRange(20.0, 500.0)
        self.sp_cw.setDecimals(1)
        self.sp_cw.setSuffix(" ft")
        self.sp_cw.setValue(SETTINGS["canvas_w_in"] / FOOT)
        form.addRow("Canvas width", self.sp_cw)

        self.sp_ch = QDoubleSpinBox()
        self.sp_ch.setRange(20.0, 500.0)
        self.sp_ch.setDecimals(1)
        self.sp_ch.setSuffix(" ft")
        self.sp_ch.setValue(SETTINGS["canvas_h_in"] / FOOT)
        form.addRow("Canvas height", self.sp_ch)

        self.sp_cost = QDoubleSpinBox()
        self.sp_cost.setRange(0.0, 100000.0)
        self.sp_cost.setDecimals(0)
        self.sp_cost.setPrefix("$ ")
        self.sp_cost.setSuffix(" / sq ft")
        self.sp_cost.setValue(float(SETTINGS.get("cost_per_sqft", 0.0)))
        form.addRow("Building cost", self.sp_cost)

        note = QLabel("Defaults: 6\" wall snap, 15° rotation snap, "
                      "100' × 70' canvas, $150 / sq ft.\n"
                      "Settings are saved with the plan.")
        note.setStyleSheet("color: #666;")
        form.addRow(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def apply(self):
        SETTINGS["wall_snap_in"] = float(self.cb_snap.currentData())
        SETTINGS["rotate_snap_deg"] = float(self.sp_rot.value())
        SETTINGS["canvas_w_in"] = float(self.sp_cw.value()) * FOOT
        SETTINGS["canvas_h_in"] = float(self.sp_ch.value()) * FOOT
        SETTINGS["cost_per_sqft"] = float(self.sp_cost.value())


class ImageImportDialog(QDialog):
    """File > Import from image…: scale + detection settings for turning a
    raster floor-plan PNG into walls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import plan from image")
        form = QFormLayout(self)

        self.sp_width = QDoubleSpinBox()
        self.sp_width.setRange(1.0, 2000.0)
        self.sp_width.setDecimals(1)
        self.sp_width.setSuffix(" ft")
        self.sp_width.setValue(40.0)
        form.addRow("Real width of the drawing", self.sp_width)

        self.sp_merge = QDoubleSpinBox()
        self.sp_merge.setRange(1.0, 200.0)
        self.sp_merge.setDecimals(0)
        self.sp_merge.setSuffix(" px")
        self.sp_merge.setValue(3.0)
        form.addRow("Merge double-line walls within", self.sp_merge)

        self.sp_thresh = QDoubleSpinBox()
        self.sp_thresh.setRange(1.0, 254.0)
        self.sp_thresh.setDecimals(0)
        self.sp_thresh.setValue(128.0)
        form.addRow("Wall darkness threshold (0–255)", self.sp_thresh)

        note = QLabel("Best on clean, axis-aligned plans (dark walls on a "
                      "light background).\nThe detected walls preview in blue "
                      "before you add them.")
        note.setStyleSheet("color: #666;")
        form.addRow(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return (float(self.sp_width.value()), int(self.sp_merge.value()),
                int(self.sp_thresh.value()))


class AIPricingDialog(QDialog):
    """AI ▸ Update furnishing prices…: choose an AI system, edit the prompt,
    and fetch up-to-date purchase prices for the whole furnishing catalog.
    On success, `result_prices` holds the {id: price} mapping and the dialog
    accepts; the prompt and provider drop-down are fully editable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI · Update furnishing prices")
        self.result_prices = None
        v = QVBoxLayout(self)

        form = QFormLayout()
        self.cb_provider = QComboBox()
        for prov in AI_PROVIDERS:
            self.cb_provider.addItem(prov["name"])
        form.addRow("AI system", self.cb_provider)

        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        form.addRow("Model", self.cb_model)

        self.ed_key = QLineEdit()
        self.ed_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.ed_key.setPlaceholderText("sk-ant-…  (or set ANTHROPIC_API_KEY)")
        form.addRow("API key", self.ed_key)

        self.ck_remember = QCheckBox("Remember this key on this computer")
        form.addRow("", self.ck_remember)
        v.addLayout(form)

        v.addWidget(QLabel("Prompt (sent to the AI — edit freely):"))
        self.ed_prompt = QPlainTextEdit()
        self.ed_prompt.setPlainText(default_pricing_prompt())
        v.addWidget(self.ed_prompt, 1)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #555;")
        v.addWidget(self.lbl_status)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel)
        self.btn_fetch = self.buttons.addButton(
            "Fetch prices", QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttons.rejected.connect(self.reject)
        self.btn_fetch.clicked.connect(self._fetch)
        v.addWidget(self.buttons)

        self.cb_provider.currentIndexChanged.connect(self._sync_models)
        self._sync_models()
        self.ed_key.setText(load_saved_api_key()
                            or os.environ.get("ANTHROPIC_API_KEY", ""))
        self.resize(640, 580)

    def _sync_models(self):
        self.cb_model.clear()
        idx = max(self.cb_provider.currentIndex(), 0)
        self.cb_model.addItems(AI_PROVIDERS[idx]["models"])

    def _fetch(self):
        key = self.ed_key.text().strip()
        if not key:
            self.lbl_status.setText(
                "Enter an API key, or set the ANTHROPIC_API_KEY "
                "environment variable.")
            return
        model = self.cb_model.currentText().strip()
        prompt = self.ed_prompt.toPlainText()
        self.lbl_status.setText("Contacting the AI…  this may take a moment.")
        self.btn_fetch.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            prices = anthropic_fetch_prices(key, model, prompt)
        except Exception as ex:             # noqa: BLE001 - shown to the user
            QApplication.restoreOverrideCursor()
            self.btn_fetch.setEnabled(True)
            self.lbl_status.setText(str(ex))
            return
        QApplication.restoreOverrideCursor()
        if self.ck_remember.isChecked():
            save_api_key(key)
        self.result_prices = prices
        self.accept()


class FurnishingItem(QGraphicsItem):
    """A furniture / fixture symbol placed on the plan at true scale.

    The symbol comes from the bundled library (assets/furnishings); its
    SVG viewBox is in inches, so it is rendered 1:1 into a scene rect of
    the catalog's width_in x depth_in.  Drag to move (snaps to 1").
    When selected, a round ROTATOR HANDLE floats above the symbol: drag
    it to spin the item freely (Ctrl = stick to 15-degree increments).
    Right-clicking still offers 90-degree steps and delete.
    """

    def __init__(self, kind: str, pos: QPointF, rotation: float = 0.0):
        super().__init__()
        spec = furnishing_spec(kind) or {
            "name": kind, "width_in": 24.0, "depth_in": 24.0}
        self.kind = kind
        self.name = spec["name"]
        self.w = float(spec["width_in"])
        self.d = float(spec["depth_in"])
        self.price = float(spec.get("price", 0.0) or 0.0)
        self._rotating = False
        self._rot_offset = 0.0
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setAcceptHoverEvents(True)
        self.setZValue(3)                 # over walls, under room labels
        self.setPos(pos)                  # pos = symbol centre
        self.setRotation(rotation)        # rotates about the centre
        tip = f"{self.name} — {fmt_in(self.w)} × {fmt_in(self.d)}"
        if self.price > 0:
            tip += f"  ·  ${self.price:,.0f}"
        self.setToolTip(tip)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            return grid_snap(value)
        return super().itemChange(change, value)

    # -- rotator handle -------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _handle(self) -> tuple:
        """(centre, radius) of the rotator handle in ITEM coordinates;
        sized in view pixels so it stays grabbable at any zoom."""
        s = self._view_scale()
        stem, r = 14.0 / s, 5.0 / s
        return QPointF(0.0, -self.d / 2 - stem - r), r

    def _on_handle(self, item_pt: QPointF) -> bool:
        c, r = self._handle()
        return QLineF(item_pt, c).length() <= r * 1.8

    def _handle_visible(self) -> bool:
        """The individual selection box + rotator only show when the item
        is selected on its own; inside a group the group's outline and
        handle govern the whole set."""
        return self.isSelected() and self.group() is None

    def boundingRect(self) -> QRectF:
        rect = QRectF(-self.w / 2 - 1.5, -self.d / 2 - 1.5,
                      self.w + 3, self.d + 3)
        c, r = self._handle()
        rect.setTop(c.y() - r - 1.5)
        return rect

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QRectF(-self.w / 2, -self.d / 2, self.w, self.d))
        if self.isSelected():
            c, r = self._handle()
            path.addEllipse(c, r * 1.8, r * 1.8)
        return path

    def paint(self, painter, option, widget=None):
        rect = QRectF(-self.w / 2, -self.d / 2, self.w, self.d)
        r = furnishing_renderer(self.kind)
        if r is not None:
            r.render(painter, rect)
        else:
            painter.setPen(QPen(QColor(55, 65, 81), 1.0))
            painter.setBrush(QBrush(QColor(248, 250, 252)))
            painter.drawRect(rect)
        if self._handle_visible():
            blue = QColor(0, 110, 255)
            painter.setPen(QPen(blue, 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(-1, -1, 1, 1))
            # rotator handle: stem + circle + centre dot
            c, hr = self._handle()
            painter.setPen(QPen(blue, 0))
            painter.drawLine(QPointF(0.0, -self.d / 2),
                             QPointF(c.x(), c.y() + hr))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(c, hr, hr)
            painter.setBrush(QBrush(blue))
            painter.drawEllipse(c, hr * 0.35, hr * 0.35)

    def hoverMoveEvent(self, e):
        if self._handle_visible() and self._on_handle(e.pos()):
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(e)

    def hoverLeaveEvent(self, e):
        self.unsetCursor()
        super().hoverLeaveEvent(e)

    def _mouse_angle(self, scene_pt: QPointF) -> float:
        """Angle (degrees) of the mouse around the symbol centre."""
        return math.degrees(math.atan2(scene_pt.y() - self.pos().y(),
                                       scene_pt.x() - self.pos().x()))

    def mousePressEvent(self, e):
        if (e.button() == Qt.MouseButton.LeftButton and self._handle_visible()
                and self._on_handle(e.pos())):
            self._rotating = True
            self._rot_offset = self.rotation() - self._mouse_angle(e.scenePos())
            e.accept()
            return
        self._rotating = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._rotating:
            rot = self._mouse_angle(e.scenePos()) + self._rot_offset
            if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
                step = max(SETTINGS["rotate_snap_deg"], 1.0)
                rot = round(rot / step) * step    # stick to snap steps
            else:
                rot = round(rot)                  # whole degrees
            self.setRotation(rot % 360.0)
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._rotating:
            self._rotating = False
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_cw = menu.addAction("Rotate 90° CW")
        a_ccw = menu.addAction("Rotate 90° CCW")
        menu.addSeparator()
        a_del = menu.addAction(f"Delete {self.name}")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen is a_cw:
            self.setRotation((self.rotation() + 90.0) % 360.0)
        elif chosen is a_ccw:
            self.setRotation((self.rotation() - 90.0) % 360.0)
        elif chosen is a_del:
            self.scene().removeItem(self)
        e.accept()

    def extra_state(self) -> dict:
        """Per-kind state to persist alongside kind/pos/rotation.  Plain
        furnishings have none; subclasses (e.g. StairItem) override this."""
        return {}


# ----------------------------------------------------------------------------
# Stairs — a dynamic "Framing" furnishing.  The step count comes from the
# ceiling height of the room it sits in (standard ~7" risers); it can be a
# full flight or a half flight to a landing that ends or turns left/right,
# and shows an UP / DOWN arrow.
# ----------------------------------------------------------------------------
STAIR_WIDTH = 36.0            # standard residential stair width
STAIR_TREAD = 10.5           # standard tread run
STAIR_RISER = 7.0            # target riser height (drives the step count)
DEFAULT_CEILING_IN = 96.0    # fallback when a stair is not inside a room


class StairItem(FurnishingItem):
    """A stair flight whose number of steps is computed from the ceiling
    height of the room it is placed in.  `flight` is 'full' or 'half';
    a half flight rises to a landing that either ends ('none') or turns
    'left'/'right' for the remaining rise.  `direction` ('up'/'down')
    flips the travel arrow."""

    def __init__(self, pos: QPointF, rotation: float = 0.0, *,
                 flight: str = "full", turn: str = "left",
                 direction: str = "up"):
        self.flight = flight if flight in ("full", "half") else "full"
        self.turn = turn if turn in ("none", "left", "right") else "left"
        self.direction = direction if direction in ("up", "down") else "up"
        self.n_risers = 14
        self._off = QPointF(0.0, 0.0)
        self._geo = {"rects": [], "steps": [], "arrow": [], "label": ""}
        super().__init__("stairs", pos, rotation)
        self._recompute()

    def extra_state(self) -> dict:
        return {"flight": self.flight, "turn": self.turn,
                "direction": self.direction}

    # -- geometry ------------------------------------------------------------
    def _ceiling_height(self) -> float:
        sc = self.scene()
        if sc is not None:
            pt = self.scenePos()
            for it in sc.items():
                if isinstance(it, RoomItem) and it.path.contains(pt):
                    return float(it.properties.get("ceiling_height_in",
                                                   DEFAULT_CEILING_IN))
        return DEFAULT_CEILING_IN

    def _build(self) -> dict:
        """Stair geometry in natural coords (first flight rising along +Y
        from the origin): rectangles, interior step lines, the travel-arrow
        polyline, and the floor-level label point."""
        w, t = STAIR_WIDTH, STAIR_TREAD
        treads = max(1, self.n_risers - 1)
        rects, steps = [], []
        if self.flight == "full":
            run = treads * t
            rects.append(QRectF(0, 0, w, run))
            for i in range(1, treads):
                steps.append((0, i * t, w, i * t))
            line = [QPointF(w / 2, t * 0.5), QPointF(w / 2, run - t * 0.5)]
            label_pt = QPointF(w / 2 + 1, t * 0.5)
        else:
            first = max(1, treads // 2)
            second = treads - first
            run1 = first * t
            land = w
            rects.append(QRectF(0, 0, w, run1))          # first flight
            for i in range(1, first):
                steps.append((0, i * t, w, i * t))
            rects.append(QRectF(0, run1, w, land))       # landing
            line = [QPointF(w / 2, t * 0.5),
                    QPointF(w / 2, run1 + land / 2)]
            label_pt = QPointF(w / 2 + 1, t * 0.5)
            if self.turn in ("left", "right") and second > 0:
                run2 = second * t
                if self.turn == "left":
                    rects.append(QRectF(-run2, run1, run2, w))
                    for j in range(1, second):
                        steps.append((-j * t, run1, -j * t, run1 + w))
                    line.append(QPointF(-run2 + t * 0.5, run1 + w / 2))
                else:
                    rects.append(QRectF(w, run1, run2, w))
                    for j in range(1, second):
                        steps.append((w + j * t, run1, w + j * t, run1 + w))
                    line.append(QPointF(w + run2 - t * 0.5, run1 + w / 2))
            else:
                line[-1] = QPointF(w / 2, run1 + land - t * 0.5)
        return {"rects": rects, "steps": steps, "line": line,
                "label_pt": label_pt}

    def _recompute(self):
        self.prepareGeometryChange()
        self.n_risers = max(2, round(self._ceiling_height() / STAIR_RISER))
        geo = self._build()
        bbox = QRectF(geo["rects"][0])
        for r in geo["rects"][1:]:
            bbox = bbox.united(r)
        self._geo = geo
        self._bbox = bbox
        self.w = bbox.width()
        self.d = bbox.height()
        self._off = QPointF(-bbox.center().x(), -bbox.center().y())
        rise_ft = self.n_risers * STAIR_RISER / FOOT
        kind = "full flight" if self.flight == "full" else \
            ("half flight, ends at landing" if self.turn == "none"
             else f"half flight, turns {self.turn}")
        self.setToolTip(f"Stairs — {self.n_risers} risers ({kind}), "
                        f"{self.direction.upper()}; rise ~{rise_ft:.1f} ft")
        self.update()

    def itemChange(self, change, value):
        res = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            self._recompute()
        return res

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._recompute()             # the room under the stair may differ

    # -- painting ------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        painter.save()
        painter.translate(self._off)
        ink = QColor(55, 65, 81)
        painter.setPen(QPen(ink, 1.2))
        painter.setBrush(QBrush(QColor(248, 250, 252)))
        for r in self._geo["rects"]:
            painter.drawRect(r)
        painter.setPen(QPen(ink, 0.7))
        for x1, y1, x2, y2 in self._geo["steps"]:
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        self._paint_arrow(painter, ink)
        painter.restore()
        if self._handle_visible():
            self._paint_selection(painter)

    def _paint_arrow(self, painter, ink):
        line = list(self._geo["line"])
        if self.direction == "down":
            line.reverse()
        painter.setPen(QPen(ink, 1.4))
        for a, b in zip(line[:-1], line[1:], strict=False):
            painter.drawLine(a, b)
        head, prev = line[-1], line[-2]
        ang = math.atan2(head.y() - prev.y(), head.x() - prev.x())
        for da in (math.radians(150), math.radians(-150)):
            painter.drawLine(head, QPointF(head.x() + 7 * math.cos(ang + da),
                                           head.y() + 7 * math.sin(ang + da)))
        font = painter.font()
        font.setPointSizeF(7.0)
        font.setBold(True)
        painter.setFont(font)
        lp = self._geo["label_pt"]
        painter.drawText(QRectF(lp.x(), lp.y() - 1, 24, 11),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         "UP" if self.direction == "up" else "DN")

    def _paint_selection(self, painter):
        rect = QRectF(-self.w / 2, -self.d / 2, self.w, self.d)
        blue = QColor(0, 110, 255)
        painter.setPen(QPen(blue, 0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(-1, -1, 1, 1))
        c, hr = self._handle()
        painter.setPen(QPen(blue, 0))
        painter.drawLine(QPointF(0.0, -self.d / 2), QPointF(c.x(), c.y() + hr))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(c, hr, hr)
        painter.setBrush(QBrush(blue))
        painter.drawEllipse(c, hr * 0.35, hr * 0.35)

    def contextMenuEvent(self, e):
        menu = QMenu()
        m_flight = menu.addMenu("Flight")
        for label, val in [("Full flight", "full"),
                           ("Half flight (landing)", "half")]:
            a = m_flight.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.flight == val)
            a.setData(("flight", val))
        m_turn = menu.addMenu("Half-flight direction")
        m_turn.setEnabled(self.flight == "half")
        for label, val in [("Turn left", "left"), ("Turn right", "right"),
                           ("End at landing", "none")]:
            a = m_turn.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.turn == val)
            a.setData(("turn", val))
        m_dir = menu.addMenu("Travel")
        for label, val in [("Going up", "up"), ("Going down", "down")]:
            a = m_dir.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.direction == val)
            a.setData(("direction", val))
        menu.addSeparator()
        a_cw = menu.addAction("Rotate 90° CW")
        a_ccw = menu.addAction("Rotate 90° CCW")
        menu.addSeparator()
        a_del = menu.addAction("Delete stairs")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if chosen is None:
            e.accept()
            return
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        data = chosen.data()
        if isinstance(data, tuple):
            setattr(self, data[0], data[1])
            self._recompute()
        elif chosen is a_cw:
            self.setRotation((self.rotation() + 90.0) % 360.0)
        elif chosen is a_ccw:
            self.setRotation((self.rotation() - 90.0) % 360.0)
        elif chosen is a_del and self.scene() is not None:
            self.scene().removeItem(self)
        e.accept()


def make_furnishing(kind: str, pos: QPointF, rotation: float = 0.0,
                    state: dict = None):
    """Create the right item for a catalog `kind`: a dynamic StairItem for
    'stairs', otherwise a plain FurnishingItem.  `state` carries per-kind
    extras (e.g. stair flight/turn/direction) from the plan/clipboard."""
    state = state or {}
    if kind == "stairs":
        return StairItem(pos, rotation,
                         flight=state.get("flight", "full"),
                         turn=state.get("turn", "left"),
                         direction=state.get("direction", "up"))
    return FurnishingItem(kind, pos, rotation)


class GroupItem(QGraphicsItemGroup):
    """A group of walls / furnishings that selects and moves as one
    (Ctrl+G to group, Ctrl+Shift+G to ungroup).

    After every drag the group's translation is BAKED back into its
    members — wall p1/p2 are scene coordinates, so they must be shifted
    for hit-testing, joining and room detection to keep working — and
    the group itself returns to (0, 0).
    """

    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self._rotating = False
        self._angle = 0.0                 # current orientation of the box

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            return grid_snap(value)
        return super().itemChange(change, value)

    # -- rotator handle -------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    @staticmethod
    def _rot_transform(center: QPointF, angle: float) -> QTransform:
        tr = QTransform()
        tr.translate(center.x(), center.y())
        tr.rotate(angle)
        tr.translate(-center.x(), -center.y())
        return tr

    def _content_points(self) -> list:
        """Scene-coord extreme points of the members (wall endpoints and
        furnishing footprint corners) -- the box hugs these."""
        pts = []
        for ch in self.childItems():
            if isinstance(ch, WallItem):
                pts += [ch.p1, ch.p2]
            elif isinstance(ch, FurnishingItem):
                r = QRectF(-ch.w / 2, -ch.d / 2, ch.w, ch.d)
                pts += [ch.mapToScene(r.topLeft()), ch.mapToScene(r.topRight()),
                        ch.mapToScene(r.bottomRight()),
                        ch.mapToScene(r.bottomLeft())]
        return pts

    def _oriented_box(self) -> tuple:
        """(localRect, centre): an axis-aligned rectangle in the frame
        rotated by -self._angle that tightly contains the content.  Drawn
        back through +self._angle it becomes an oriented box hugging the
        members at the group's current orientation."""
        pts = self._content_points()
        if not pts:
            b = self.childrenBoundingRect()
            return b, b.center()
        cx = sum(p.x() for p in pts) / len(pts)
        cy = sum(p.y() for p in pts) / len(pts)
        center = QPointF(cx, cy)
        local = [self._rot_transform(center, -self._angle).map(p) for p in pts]
        xs = [p.x() for p in local]
        ys = [p.y() for p in local]
        m = EXTERIOR_T                    # margin for wall half-thickness
        rect = QRectF(min(xs) - m, min(ys) - m,
                      max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m)
        return rect, center

    def _handle(self) -> tuple:
        """(centre, radius) of the rotator handle in scene coords; floats
        above the oriented box and turns with it."""
        rect, center = self._oriented_box()
        s = self._view_scale()
        stem, r = 18.0 / s, 6.0 / s
        local_c = QPointF(rect.center().x(), rect.top() - stem - r)
        return self._rot_transform(center, self._angle).map(local_c), r

    def _on_handle(self, item_pt: QPointF) -> bool:
        c, r = self._handle()
        return QLineF(item_pt, c).length() <= r * 1.8

    def boundingRect(self) -> QRectF:
        rect, center = self._oriented_box()
        poly = self._rot_transform(center, self._angle).map(QPolygonF(rect))
        br = poly.boundingRect()
        c, r = self._handle()
        return br.united(
            QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r)).adjusted(-4, -4, 4, 4)

    def paint(self, painter, option, widget=None):
        sel = self.isSelected()
        rect, center = self._oriented_box()
        pen = QPen(QColor(0, 110, 255) if sel else QColor(165, 173, 185), 0,
                   Qt.PenStyle.DashLine)
        painter.save()
        painter.translate(center.x(), center.y())   # draw in the box's frame
        painter.rotate(self._angle)
        painter.translate(-center.x(), -center.y())
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(-2, -2, 2, 2))
        if sel:
            s = self._view_scale()
            stem, hr = 18.0 / s, 6.0 / s
            c = QPointF(rect.center().x(), rect.top() - stem - hr)
            blue = QColor(0, 110, 255)
            painter.setPen(QPen(blue, 0))
            painter.drawLine(QPointF(rect.center().x(), rect.top()),
                             QPointF(c.x(), c.y() + hr))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(c, hr, hr)
            painter.setBrush(QBrush(blue))
            painter.drawEllipse(c, hr * 0.35, hr * 0.35)
        painter.restore()

    def hoverMoveEvent(self, e):
        if self.isSelected() and self._on_handle(e.pos()):
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(e)

    def hoverLeaveEvent(self, e):
        self.unsetCursor()
        super().hoverLeaveEvent(e)

    # -- rotation (baked live into the members about a fixed centre) ----------
    def _angle_to(self, scene_pt: QPointF) -> float:
        c = self._rot_center
        return math.degrees(math.atan2(scene_pt.y() - c.y(),
                                       scene_pt.x() - c.x()))

    def _begin_rotation(self, scene_pt: QPointF):
        self._rotating = True
        self._rot_center = self.childrenBoundingRect().center()
        self._rot_start = self._angle_to(scene_pt)
        self._rot_angle0 = self._angle
        self._snap_walls = [(w, QPointF(w.p1), QPointF(w.p2))
                            for w in self.childItems()
                            if isinstance(w, WallItem)]
        self._snap_furn = [(f, QPointF(f.pos()), f.rotation())
                           for f in self.childItems()
                           if isinstance(f, FurnishingItem)]
        group_walls = {w for w, _, _ in self._snap_walls}
        self._snap_rooms = []
        sc = self.scene()
        if sc is not None and group_walls:
            for it in sc.items():
                if isinstance(it, RoomItem) and walls_cover_room(group_walls, it):
                    self._snap_rooms.append(
                        (it, [QPointF(c) for c in (it.corners or [])],
                         QPointF(it.anchor), QPainterPath(it.path)))

    def _apply_rotation(self, scene_pt: QPointF, snap: bool):
        theta = self._angle_to(scene_pt) - self._rot_start
        if snap:
            step = max(SETTINGS["rotate_snap_deg"], 1.0)
            theta = round(theta / step) * step
        self._angle = (self._rot_angle0 + theta) % 360.0
        c = self._rot_center
        tr = QTransform()
        tr.translate(c.x(), c.y())
        tr.rotate(theta)
        tr.translate(-c.x(), -c.y())
        self.prepareGeometryChange()
        for w, p1_0, p2_0 in self._snap_walls:
            w.p1, w.p2 = tr.map(p1_0), tr.map(p2_0)
            w.rebuild()                       # re-syncs its openings too
        for f, pos_0, rot_0 in self._snap_furn:
            f.setPos(tr.map(pos_0))
            f.setRotation((rot_0 + theta) % 360.0)
        for room, corners_0, anchor_0, path_0 in self._snap_rooms:
            room.prepareGeometryChange()
            if corners_0:
                room.corners = [tr.map(p) for p in corners_0]
            room.anchor = tr.map(anchor_0)
            room.path = tr.map(path_0)
            room._sync_corner_props()
            room.update()
        self.update()

    def _finish_rotation(self):
        self._snap_walls = self._snap_furn = self._snap_rooms = []
        self.prepareGeometryChange()
        self.update()

    def adopt(self, item):
        """addToGroup without Qt's transform juggling.  The group always
        sits at (0,0) untransformed, so children can simply keep their
        own scene position and rotation.  (Qt's addToGroup bakes a
        rotated child's rotation into its transform(), which then
        combines with the still-set rotation() and double-rotates.)"""
        sp, rot = item.scenePos(), item.rotation()
        self.addToGroup(item)
        item.setTransform(QTransform())
        if isinstance(item, WallItem):
            item.setPos(0.0, 0.0)         # walls live in their p1/p2
        else:
            item.setPos(sp)
        item.setRotation(rot)

    def dissolve(self) -> list:
        """Remove the group, leaving its members in the scene exactly
        where they are now; returns the members."""
        children = list(self.childItems())
        sc = self.scene()
        for c in children:
            sp, rot = c.scenePos(), c.rotation()
            self.removeFromGroup(c)
            c.setTransform(QTransform())
            c.setPos(QPointF(0.0, 0.0) if isinstance(c, WallItem) else sp)
            c.setRotation(rot)
            # removeFromGroup() hands ownership back to Python; with no
            # external reference the wrapper (and its C++ item) would be
            # garbage-collected straight out of the scene.  Tie its
            # lifetime to the scene so it survives.
            if sc is not None:
                sip.transferto(c, sc)
        if sc is not None:
            sc.removeItem(self)
        return children

    def bake(self):
        """Fold the group's current translation into its members and
        reset the group to (0, 0).  A room whose perimeter is fully walled
        by the group rides along -- its anchor (label) and region shift too
        -- even when an extra coincident wall (e.g. a shared party wall the
        room edge was copied from) also touches its boundary."""
        d = self.pos()
        if abs(d.x()) < 1e-9 and abs(d.y()) < 1e-9:
            return
        sc = self.scene()
        moved_rooms = []
        group_walls = {ch for ch in self.childItems()
                       if isinstance(ch, WallItem)}
        if sc is not None and group_walls:
            for it in sc.items():
                if isinstance(it, RoomItem) and walls_cover_room(group_walls, it):
                    moved_rooms.append(it)
        self.prepareGeometryChange()
        for ch in self.childItems():
            if isinstance(ch, WallItem):
                ch.p1 = QPointF(ch.p1.x() + d.x(), ch.p1.y() + d.y())
                ch.p2 = QPointF(ch.p2.x() + d.x(), ch.p2.y() + d.y())
            else:
                ch.setPos(ch.pos().x() + d.x(), ch.pos().y() + d.y())
        tr = QTransform.fromTranslate(d.x(), d.y())
        for r in moved_rooms:
            r.prepareGeometryChange()
            r.anchor = QPointF(r.anchor.x() + d.x(), r.anchor.y() + d.y())
            # carry the region itself: a rigid translation of the walls
            # translates the room rigidly, so the fill/outline stay put
            # even before (and in case) re-detection runs
            r.path = tr.map(r.path)
            if r.corners:
                r.corners = [QPointF(c.x() + d.x(), c.y() + d.y())
                             for c in r.corners]
            r._sync_corner_props()
        self.setPos(0.0, 0.0)
        rebuild_all_walls(sc)             # re-detects rooms at new anchors

    def mousePressEvent(self, e):
        if (e.button() == Qt.MouseButton.LeftButton and self.isSelected()
                and self._on_handle(e.pos())):
            self._begin_rotation(e.scenePos())
            e.accept()
            return
        self._rotating = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._rotating:
            self._apply_rotation(
                e.scenePos(),
                bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier))
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._rotating:
            self._rotating = False
            self._finish_rotation()
            e.accept()
            return
        super().mouseReleaseEvent(e)
        self.bake()

    def contextMenuEvent(self, e):
        win = None
        sc = self.scene()
        if sc and sc.views():
            win = sc.views()[0].win
        menu = QMenu()
        a_un = menu.addAction("Ungroup")
        a_cut = menu.addAction("Cut group")
        a_copy = menu.addAction("Copy group")
        menu.addSeparator()
        a_del = menu.addAction("Delete group")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if win is not None and chosen in (a_un, a_cut, a_del):
            sc.clearSelection()
            self.setSelected(True)
            # defer: these destroy this item, which must not happen
            # while Qt is still delivering its context-menu event
            slot = {a_un: win.ungroup_selected, a_cut: win.cut_selected,
                    a_del: win.delete_selected}[chosen]
            QTimer.singleShot(0, slot)
        elif chosen is a_copy and win is not None:
            sc.clearSelection()
            self.setSelected(True)
            win.copy_selected()
        e.accept()


class FurnishingList(QListWidget):
    """One palette section: an icon grid of furnishing symbols; drag a
    symbol onto the plan to place it at true scale."""

    def __init__(self, specs, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(52, 52))
        self.setGridSize(QSize(88, 92))
        self.setMovement(QListWidget.Movement.Static)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setDragEnabled(True)
        self.setWordWrap(True)
        self.setSpacing(2)
        for spec in specs:
            it = QListWidgetItem(self._icon(spec), spec["name"])
            it.setData(Qt.ItemDataRole.UserRole, spec["id"])
            it.setToolTip(self._tooltip(spec))
            self.addItem(it)

    @staticmethod
    def _tooltip(spec) -> str:
        t = (f'{spec["name"]} — {fmt_in(spec["width_in"])} × '
             f'{fmt_in(spec["depth_in"])}  ({spec["category"]})')
        price = float(spec.get("price", 0.0) or 0.0)
        if price > 0:
            t += f'  ·  ${price:,.0f}'
        return t

    def refresh_tooltips(self):
        """Re-read each item's price from the live catalog (after an AI
        price update) and rebuild its tooltip."""
        for row in range(self.count()):
            it = self.item(row)
            spec = furnishing_spec(it.data(Qt.ItemDataRole.UserRole))
            if spec is not None:
                it.setToolTip(self._tooltip(spec))

    @staticmethod
    def _icon(spec) -> QIcon:
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        r = furnishing_renderer(spec["id"])
        if r is not None:
            w, d = spec["width_in"], spec["depth_in"]
            s = 56.0 / max(w, d)
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            r.render(p, QRectF((64 - w * s) / 2, (64 - d * s) / 2,
                               w * s, d * s))
            p.end()
        return QIcon(pm)

    def startDrag(self, actions):
        it = self.currentItem()
        kind = it.data(Qt.ItemDataRole.UserRole) if it else None
        if not kind:
            return
        mime = QMimeData()
        mime.setData(FURN_MIME, str(kind).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        pm = it.icon().pixmap(48, 48)
        drag.setPixmap(pm)
        drag.setHotSpot(QPoint(pm.width() // 2, pm.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)


class FurnishingPalette(QToolBox):
    """Right-hand palette: one expandable tab per room group from
    assets/furnishings/groups.json (a furnishing may appear in several
    groups).  Clicking a tab expands that section; "All" — the whole
    library — is the section open by default."""

    def __init__(self, parent=None):
        super().__init__(parent)
        all_index = 0
        for i, group in enumerate(furnishing_groups()):
            lst = FurnishingList(group["specs"], self)
            self.addItem(lst, f'{group["name"]}  ({len(group["specs"])})')
            if group["name"].lower() == "all":
                all_index = i
        self.setCurrentIndex(all_index)

    def refresh_prices(self):
        """Refresh every section's tooltips after an AI price update."""
        for i in range(self.count()):
            w = self.widget(i)
            if isinstance(w, FurnishingList):
                w.refresh_tooltips()


# ----------------------------------------------------------------------------
# Rubber-band selection helpers
# ----------------------------------------------------------------------------
def item_fully_inside(item, area: QRectF) -> bool:
    """True when `item` lies entirely within the scene rectangle `area`."""
    if isinstance(item, WallItem):
        return area.contains(item.p1) and area.contains(item.p2)
    if isinstance(item, RoomItem):
        if item.corners:
            return all(area.contains(c) for c in item.corners)
        return area.contains(item.path.boundingRect())
    if isinstance(item, FurnishingItem):
        foot = item.mapToScene(
            QRectF(-item.w / 2, -item.d / 2, item.w, item.d)).boundingRect()
        return area.contains(foot)
    if isinstance(item, GroupItem):
        return area.contains(item.sceneBoundingRect())
    return False


def _wall_endpoints_match(w, a: QPointF, b: QPointF, tol: float = 1.0) -> bool:
    return ((QLineF(w.p1, a).length() <= tol and QLineF(w.p2, b).length() <= tol)
            or (QLineF(w.p1, b).length() <= tol
                and QLineF(w.p2, a).length() <= tol))


def _wall_spans_segment(w, a: QPointF, b: QPointF) -> bool:
    """True when wall `w`'s body runs along and contains the segment a->b
    (both ends project within the wall's length, ~collinear with it)."""
    u, length = w.unit(), w.length()
    if length < 1e-6:
        return False
    for p in (a, b):
        vx, vy = p.x() - w.p1.x(), p.y() - w.p1.y()
        s = vx * u.x() + vy * u.y()
        if not (-0.6 <= s <= length + 0.6
                and abs(vy * u.x() - vx * u.y()) <= 1.5):
            return False
    return True


def _wall_along_segment(scene, a: QPointF, b: QPointF):
    """The wall whose body runs along (and spans) the segment a->b -- i.e.
    the longer wall that carries a room edge.  None if there isn't one."""
    for w in scene.items():
        if (isinstance(w, WallItem) and not w.is_open
                and _wall_spans_segment(w, a, b)):
            return w
    return None


def walls_cover_room(walls, room) -> bool:
    """True when `walls` form a complete loop along every edge of the
    room's perimeter -- so moving exactly those walls moves the whole
    room, even if extra (coincident) walls also touch the boundary."""
    if not room.corners:
        return False
    n = len(room.corners)
    for i in range(n):
        a, b = room.corners[i], room.corners[(i + 1) % n]
        if not any(_wall_spans_segment(w, a, b) for w in walls):
            return False
    return True


def synthesize_room_edge(scene, a: QPointF, b: QPointF):
    """Create a new wall along a->b for a room's own copy of a shared/party
    wall.  It takes the carrier's type but NOT its openings -- a door/window
    belongs to one wall only; this plain copy opens its body for it instead
    (so there are never two doors or windows on top of each other)."""
    src = _wall_along_segment(scene, a, b)
    nw = WallItem(QPointF(a), QPointF(b),
                  src.wall_type if src is not None else "interior")
    scene.addItem(nw)
    nw.rebuild()
    return nw


def bind_room_walls(scene, room, settle=True):
    """Bind `room`'s edge loop, backing every perimeter edge with exactly one
    item, in priority order:

      1. a real ownable wall whose endpoints match the edge (bound directly);
      2. else, if a neighbour-owned exact wall or a longer/party wall spans
         the edge, a room-owned copy is synthesized (keeps adjacent rooms
         decoupled);
      3. else an OpenWall -- a dashed gap that keeps the loop closed but is
         not a built wall.

    Corner geometry (including the extra corners created when a wall's end is
    pulled away, opening a side) comes from reloop_open_room via refresh; this
    just attaches a wall/open-wall to each edge.  Idempotent: a previously
    synthesized copy or OpenWall is reused, so the count does not grow; open
    walls that closed up are removed.  Pass settle=False from refresh_rooms."""
    if not room.corners:
        return
    old_open = [w for w in room.walls if w.is_open]
    room.clear_walls()
    corners = room.corners
    n = len(corners)
    band_walls = room.bounding_walls()
    reused_open = set()
    for i in range(n):
        a, b = corners[i], corners[(i + 1) % n]
        if QLineF(a, b).length() < MIN_WALL_LEN:
            continue
        match = next((w for w in band_walls
                      if not w.is_open
                      and (w.room is None or w.room is room)
                      and _wall_endpoints_match(w, a, b)), None)
        if match is not None:                            # 1. own this wall
            room.bind_wall(match)
            continue
        if _wall_along_segment(scene, a, b) is not None:  # 2. party / neighbour
            nw = synthesize_room_edge(scene, a, b)
            room.bind_wall(nw)
            band_walls.append(nw)
            continue
        ow = next((w for w in old_open if w not in reused_open    # 3. open edge
                   and _wall_endpoints_match(w, a, b)), None)
        if ow is None:
            ow = OpenWall(QPointF(a), QPointF(b), room)
            scene.addItem(ow)
        else:
            reused_open.add(ow)
        room.bind_wall(ow)
    for w in old_open:                       # drop open edges that closed up
        if w not in reused_open and w.room is None and w.scene() is not None:
            scene.removeItem(w)
    if settle:
        rebuild_all_walls(scene)


def reloop_open_room(room):
    """Rebuild an OPEN room's corner loop from its bound real walls when
    flood-fill can't enclose it.  Each real wall is matched (using the last
    known corners for order) to a perimeter edge; the loop is then the walls'
    current endpoints in order, with extra corners + dashed open segments
    inserted wherever consecutive walls no longer meet.  Returns
    (path, area, corners) or None."""
    prev = room.corners
    # include open walls: a body-slid side carries its dashed gap, so the open
    # edge must follow the open wall's CURRENT position, not the stale corners
    walls = [w for w in room.walls if w.length() > 1e-6]
    if not prev or not walls:
        return None
    n = len(prev)
    used, segs = set(), []
    for i in range(n):
        a, b = prev[i], prev[(i + 1) % n]
        best, best_d, orient = None, 1e18, None
        for w in walls:
            if id(w) in used:
                continue
            d1 = QLineF(w.p1, a).length() + QLineF(w.p2, b).length()
            d2 = QLineF(w.p2, a).length() + QLineF(w.p1, b).length()
            d, o = (d1, (w.p1, w.p2)) if d1 <= d2 else (d2, (w.p2, w.p1))
            if d < best_d:
                best_d, best, orient = d, w, o
        if best is not None and best_d <= QLineF(a, b).length() + 2 * JOIN_TOL:
            used.add(id(best))
            segs.append((QPointF(orient[0]), QPointF(orient[1])))   # wall ends
        else:
            segs.append(None)                                       # open edge
    pts = []
    for i in range(n):
        a, b = prev[i], prev[(i + 1) % n]
        s, e = segs[i] if segs[i] is not None else (a, b)
        if not pts or QLineF(pts[-1], s).length() > 0.6:
            pts.append(s)
        if QLineF(s, e).length() > 0.6:
            pts.append(e)
    if len(pts) > 1 and QLineF(pts[0], pts[-1]).length() <= 0.6:
        pts.pop()
    # keep collinear gap corners (a shortened wall leaves a collinear open
    # segment); only exact near-duplicates were already dropped above
    if len(pts) < 3:
        return None
    return (room_path_from_corners(pts), poly_area_sqft(pts), pts)


def detach_wall_from_room(scene, wall):
    """Unlock `wall`'s corners so the user can drag its endpoints.  The wall
    stays part of the room; pulling a corner away from the neighbouring wall
    opens that side (a dashed OpenWall bridges the gap)."""
    if wall.room is None:
        return
    wall._corners_unlocked = True
    wall.setZValue(wall.zValue() + 1)    # above locked neighbours at corners
    wall.update()


# ----------------------------------------------------------------------------
# Room boolean operations (treat room perimeters as polygons)
# ----------------------------------------------------------------------------
def room_path_from_corners(corners) -> QPainterPath:
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(c) for c in corners]))
    path.closeSubpath()
    return path


def path_area_sqft(path: QPainterPath) -> float:
    poly = path.toFillPolygon()
    pts = [poly[i] for i in range(poly.count())]
    return poly_area_sqft(pts) if len(pts) >= 3 else 0.0


def simplify_corners(poly) -> list:
    """Clean corner list from a boolean-result polygon: drop the closing
    duplicate, merge near-duplicates, and drop collinear points."""
    pts = [QPointF(poly[i]) for i in range(poly.count())]
    if len(pts) > 1 and QLineF(pts[0], pts[-1]).length() < 0.5:
        pts.pop()
    dedup = []
    for p in pts:
        if not dedup or QLineF(dedup[-1], p).length() > 0.5:
            dedup.append(p)
    n = len(dedup)
    if n < 3:
        return dedup
    corners = []
    for i in range(n):
        a, b, c = dedup[(i - 1) % n], dedup[i], dedup[(i + 1) % n]
        cross = ((b.x() - a.x()) * (c.y() - b.y())
                 - (b.y() - a.y()) * (c.x() - b.x()))
        if abs(cross) > 1.0:           # a real corner, not collinear filler
            corners.append(b)
    return corners if len(corners) >= 3 else dedup


def interior_point(poly) -> QPointF:
    """A point strictly inside a (possibly concave) polygon."""
    rule = Qt.FillRule.OddEvenFill
    c = poly.boundingRect().center()
    if poly.containsPoint(c, rule):
        return c
    br = poly.boundingRect()
    for iy in range(1, 12):
        for ix in range(1, 12):
            p = QPointF(br.left() + br.width() * ix / 12.0,
                        br.top() + br.height() * iy / 12.0)
            if poly.containsPoint(p, rule):
                return p
    return c


def room_walled(scene, room) -> bool:
    """True while the room's region is still enclosed by walls -- a flood
    fill from inside it doesn't escape to the canvas edge."""
    pts = []
    if room.corners:
        pts.append(interior_point(QPolygonF(room.corners)))
    pts.append(room.anchor)
    return any(detect_room(scene, p) is not None for p in pts)


def group_room(group):
    """The room whose perimeter the group's walls fully enclose, or None --
    so a grouped (extracted) room can be picked up from its group."""
    sc = group.scene()
    gw = {c for c in group.childItems() if isinstance(c, WallItem)}
    if sc is None or not gw:
        return None
    for it in sc.items():
        if isinstance(it, RoomItem) and walls_cover_room(gw, it):
            return it
    return None


def trace_wall_loop(walls):
    """Ordered corner points of the single closed loop formed by `walls`
    (e.g. a grouped wall-loop with no RoomItem), or None if they don't form
    one simple loop."""
    if len(walls) < 3:
        return None

    def key(p):
        return (round(p.x() * 2) / 2.0, round(p.y() * 2) / 2.0)

    pts, adj = {}, {}
    for w in walls:
        a, b = key(w.p1), key(w.p2)
        if a == b:
            continue
        pts[a], pts[b] = w.p1, w.p2
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    if not adj or any(len(v) != 2 for v in adj.values()):
        return None
    start = next(iter(adj))
    loop, prev, cur = [start], None, start
    while True:
        nxt = next((n for n in adj[cur] if n != prev), None)
        if nxt is None or nxt == start:
            break
        loop.append(nxt)
        prev, cur = cur, nxt
        if len(loop) > len(adj):
            return None
    if len(loop) != len(adj):
        return None                # not one loop covering every node
    return [QPointF(pts[k]) for k in loop]


class PlanView(QGraphicsView):
    def __init__(self, scene, win):
        super().__init__(scene)
        self.win = win
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)
        self._panning = False
        self._pan_last = None
        self._temp_wall = None
        self._last_scene = None           # last mouse position (paste target)
        self._rubber = None               # Ctrl+drag selection rubber band
        self._rubber_origin = None
        self._img_mode = None             # None | "calibrate" | "crop"
        self._img_ref = None              # the ReferenceImageItem being edited
        self._calib_pts = []              # collected calibration points
        self._crop_start = None           # crop rubber-band start (scene)

    # -- reference-image (PNG import) modes ----------------------------------
    def start_image_calibrate(self, item):
        self._img_mode, self._img_ref, self._calib_pts = "calibrate", item, []
        self.win.status("Calibrate: click two points a known distance apart "
                        "on the image (Esc to cancel).")

    def start_image_crop(self, item):
        self._img_mode, self._img_ref = "crop", item
        self._crop_start = None
        self.win.status("Crop: drag a rectangle over the area to keep "
                        "(Esc to cancel).")

    def _end_image_mode(self):
        self._img_mode = self._img_ref = self._crop_start = None
        self._calib_pts = []
        if self._rubber is not None:
            self._rubber.hide()

    # -- zoom ------------------------------------------------------------------
    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        if delta == 0:
            return
        factor = 1.0015 ** delta
        cur = self.transform().m11()
        target = max(0.03, min(40.0, cur * factor))
        self.scale(target / cur, target / cur)
        e.accept()

    # -- background grid --------------------------------------------------------
    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor(252, 252, 250))
        lod = max(self.transform().m11(), 1e-6)

        def vgrid(step, pen):
            painter.setPen(pen)
            x = math.floor(rect.left() / step) * step
            while x <= rect.right():
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                x += step
            y = math.floor(rect.top() / step) * step
            while y <= rect.bottom():
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                y += step

        if lod > 0.22:
            vgrid(GRID_MINOR, QPen(QColor(234, 237, 241), 0))
        if lod > 0.05:
            vgrid(GRID_MAJOR, QPen(QColor(206, 213, 221), 0))

        # canvas outline (size from File > Settings…; default 100' x 70')
        painter.setPen(QPen(QColor(150, 158, 170), 0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(canvas_rect())

        # foot labels along the major grid
        if lod > 0.08:
            f = QFont()
            f.setPixelSize(max(2, int(11.0 / lod)))
            painter.setFont(f)
            painter.setPen(QPen(QColor(160, 166, 176), 0))
            x = math.floor(rect.left() / GRID_MAJOR) * GRID_MAJOR
            ytop = rect.top() + 14.0 / lod
            while x <= rect.right():
                painter.drawText(QPointF(x + 2.0 / lod, ytop), f"{int(x // 12)}'")
                x += GRID_MAJOR
            y = math.floor(rect.top() / GRID_MAJOR) * GRID_MAJOR
            xleft = rect.left() + 3.0 / lod
            while y <= rect.bottom():
                painter.drawText(QPointF(xleft, y - 2.0 / lod), f"{int(y // 12)}'")
                y += GRID_MAJOR

    # -- snapping helpers ---------------------------------------------------------
    def _snap_start(self, sp: QPointF) -> QPointF:
        tol = max(6.0, 10.0 / max(self.transform().m11(), 1e-6))
        q = nearest_wall_endpoint(self.scene(), sp, tol)
        if q is None:
            q = nearest_wall_body_point(self.scene(), sp, tol)
        return q if q is not None else wall_snap(sp)

    def _align_to_wall(self, exclude, pt, horizontal) -> QPointF:
        """Snap the drawn endpoint's free coordinate (x when horizontal, y
        when vertical) to the projected line of a nearby OPEN-ENDED wall (a
        dangling end), so the new wall lines up with it while staying H/V.
        Fully-joined walls are ignored, and any gap is left as-is -- nothing
        auto-grows; the user extends to meet by hand."""
        sc = self.scene()
        if sc is None:
            return pt
        tol = max(JOIN_TOL, 16.0 / max(self.transform().m11(), 1e-6))
        base = pt.x() if horizontal else pt.y()
        best, bestd = None, tol
        for w in sc.items():
            if not isinstance(w, WallItem) or w is exclude or w.is_open:
                continue
            for end in (w.p1, w.p2):
                if not wall_endpoint_open(sc, end, ignore=(w, exclude)):
                    continue
                c = end.x() if horizontal else end.y()
                d = abs(base - c)
                if d < bestd:
                    bestd, best = d, c
        if best is None:
            return pt
        return QPointF(best, pt.y()) if horizontal else QPointF(pt.x(), best)

    def _wall_end_point(self, wall, sp, mods) -> QPointF:
        dx, dy = sp.x() - wall.p1.x(), sp.y() - wall.p1.y()
        if math.hypot(dx, dy) < 1e-6:
            return QPointF(wall.p1)
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))     # free angle
        ang = math.atan2(dy, dx)              # orthogonal from the anchor
        a = round(ang / (math.pi / 2)) * (math.pi / 2)
        horizontal = abs(math.cos(a)) > 0.5
        proj = wall_snap_len(dx * math.cos(a) + dy * math.sin(a))
        pt = QPointF(wall.p1.x() + math.cos(a) * proj,
                     wall.p1.y() + math.sin(a) * proj)
        # align the endpoint with the nearest orthogonal wall, staying H/V
        return self._align_to_wall(wall, pt, horizontal)

    def _make_named_room(self, sp, name, res):
        """Create a named room at sp from a detection result; the Room tool
        is one-shot, so it reverts to Select unless it was Ctrl-set sticky."""
        path, area, corners = res
        name = unique_room_name(self.scene(), name)
        room = RoomItem(name, grid_snap(sp), path, area, corners=corners)
        self.scene().addItem(room)
        bind_room_walls(self.scene(), room)   # fuse the enclosing walls in
        room.raise_to_front()
        if self.win._recorder is not None:
            # record the name the user typed so replay needs no dialog
            self.win._recorder.on_room(name, room.anchor)
        if not self.win._room_sticky:
            self.win.set_tool(TOOL_SELECT)
        return room

    # -- mouse / tools ----------------------------------------------------------
    def mousePressEvent(self, e):
        pos = e.position().toPoint()
        sp = self.mapToScene(pos)
        tool = self.win.tool

        if self._img_mode is not None \
                and e.button() == Qt.MouseButton.LeftButton:
            if self._img_mode == "calibrate":
                self._calib_pts.append(QPointF(sp))
                if len(self._calib_pts) == 2:
                    self.win._finish_calibrate(
                        self._img_ref, self._calib_pts)
                    self._end_image_mode()
                e.accept()
                return
            if self._img_mode == "crop":
                self._crop_start = QPointF(sp)
                e.accept()
                return

        if e.button() == Qt.MouseButton.MiddleButton:
            self._panning, self._pan_last = True, pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            e.accept()
            return

        if e.button() == Qt.MouseButton.LeftButton:
            # Ctrl+drag on empty space: rubber-band that ADDS to the
            # selection set (Ctrl+click on items toggles membership)
            if (tool == TOOL_SELECT
                    and e.modifiers() & Qt.KeyboardModifier.ControlModifier
                    and self.itemAt(pos) is None):
                self._rubber_origin = pos
                if self._rubber is None:
                    self._rubber = QRubberBand(
                        QRubberBand.Shape.Rectangle, self.viewport())
                self._rubber.setGeometry(QRect(pos, QSize(1, 1)))
                self._rubber.show()
                e.accept()
                return
            if tool in (TOOL_WALL_EXT, TOOL_WALL_INT):
                p = self._snap_start(sp)
                wt = "exterior" if tool == TOOL_WALL_EXT else "interior"
                w = WallItem(p, p, wt)
                w._drawing = True
                self.scene().addItem(w)
                self._temp_wall = w
                e.accept()
                return
            if tool == TOOL_DOOR:
                self._place_opening(sp, "door")
                e.accept()
                return
            if tool == TOOL_WINDOW:
                self._place_opening(sp, "window")
                e.accept()
                return
            if tool == TOOL_ROOM:
                res = detect_room(self.scene(), sp)
                if res is None:
                    QMessageBox.information(
                        self, "Room",
                        "Click inside an area completely enclosed by walls.")
                else:
                    name, ok = QInputDialog.getText(self, "Room name", "Name:")
                    if ok and name.strip():
                        self._make_named_room(sp, name.strip(), res)
                e.accept()
                return
            # SELECT tool: pan when pressing empty space
            if self.itemAt(pos) is None:
                self._panning, self._pan_last = True, pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.scene().clearSelection()
                e.accept()
                return

        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        sp = self.mapToScene(pos)
        self._last_scene = QPointF(sp)
        self.win.show_coords(sp)

        if self._img_mode == "crop" and self._crop_start is not None:
            origin = self.mapFromScene(self._crop_start)
            if self._rubber is None:
                self._rubber = QRubberBand(QRubberBand.Shape.Rectangle,
                                           self.viewport())
            self._rubber.setGeometry(QRect(origin, pos).normalized())
            self._rubber.show()
            e.accept()
            return

        if self._rubber_origin is not None:
            self._rubber.setGeometry(
                QRect(self._rubber_origin, pos).normalized())
            e.accept()
            return

        if self._panning and self._pan_last is not None:
            d = pos - self._pan_last
            self._pan_last = pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - d.y())
            e.accept()
            return

        if self._temp_wall is not None:
            self._temp_wall.p2 = self._wall_end_point(self._temp_wall, sp,
                                                      e.modifiers())
            self._temp_wall.rebuild()
            e.accept()
            return

        super().mouseMoveEvent(e)

    def select_in_rect(self, area: QRectF):
        """Additively select everything the rubber band fully encloses.

        Only items wholly inside `area` are selected, so a room can be
        picked out by its walls while the longer party walls that run past
        it stay unselected.  When a room's interior is enclosed but an edge
        is carried by such a longer wall, a fresh copy of that edge is
        synthesized (and selected) so the room comes through as a complete,
        movable loop -- the original long wall is left untouched."""
        scene = self.scene()
        if scene is None:
            return
        # walls / furnishings / groups that sit entirely within the band
        for it in scene.items(area, Qt.ItemSelectionMode.IntersectsItemShape):
            top = it.group() or it         # grouped items select the group
            if (isinstance(top, (WallItem, FurnishingItem, GroupItem))
                    and item_fully_inside(top, area)):
                top.setSelected(True)
        # rooms whose perimeter is enclosed: select the room and make sure
        # every edge is a selected wall (duplicating shared/longer walls)
        rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
        made_edges = False
        for room in rooms:
            if not room.corners or not item_fully_inside(room, area):
                continue
            room.setSelected(True)
            n = len(room.corners)
            for i in range(n):
                a, b = room.corners[i], room.corners[(i + 1) % n]
                w = next((x for x in scene.items()
                          if isinstance(x, WallItem)
                          and _wall_endpoints_match(x, a, b)), None)
                if w is not None:
                    w.setSelected(True)      # the room's own edge wall
                else:
                    synthesize_room_edge(scene, a, b).setSelected(True)
                    made_edges = True
        if made_edges:
            rebuild_all_walls(scene)

    def mouseReleaseEvent(self, e):
        if (self._img_mode == "crop" and self._crop_start is not None
                and e.button() == Qt.MouseButton.LeftButton):
            rect = QRectF(self._crop_start,
                          self.mapToScene(e.position().toPoint())).normalized()
            ref = self._img_ref
            self._end_image_mode()
            if ref is not None and rect.width() > 1 and rect.height() > 1:
                ref.crop_to_scene_rect(rect)
                self.win.status("Cropped the image.")
            e.accept()
            return

        if (self._rubber_origin is not None
                and e.button() == Qt.MouseButton.LeftButton):
            rect = QRect(self._rubber_origin,
                         e.position().toPoint()).normalized()
            self._rubber.hide()
            self._rubber_origin = None
            area = self.mapToScene(rect).boundingRect()
            self.select_in_rect(area)
            e.accept()
            return

        if self._panning and e.button() in (Qt.MouseButton.LeftButton,
                                            Qt.MouseButton.MiddleButton):
            self._panning, self._pan_last = False, None
            self.unsetCursor()
            e.accept()
            return

        if self._temp_wall is not None and e.button() == Qt.MouseButton.LeftButton:
            w, self._temp_wall = self._temp_wall, None
            w._drawing = False
            if w.length() < MIN_WALL_LEN:
                self.scene().removeItem(w)
            else:
                # the drawn endpoint is already aligned to the nearest
                # orthogonal wall; do NOT fuse or grow walls to meet -- any
                # gap is left for the user to extend to manually
                rebuild_all_walls(self.scene())
            e.accept()
            return

        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        # Room Name tool + blank canvas -> offer to paste the copied room
        if self.win.tool == TOOL_ROOM and self.itemAt(e.pos()) is None:
            menu = QMenu(self)
            a_paste = menu.addAction("Paste room")
            a_paste.setEnabled(self.win.room_clipboard is not None)
            if menu.exec(e.globalPos()) is a_paste:
                self.win.paste_room(grid_snap(self.mapToScene(e.pos())))
            e.accept()
            return
        super().contextMenuEvent(e)

    # -- furnishing drag & drop ---------------------------------------------------
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(FURN_MIME):
            e.acceptProposedAction()
            return
        super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(FURN_MIME):
            e.acceptProposedAction()
            return
        super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasFormat(FURN_MIME):
            kind = bytes(e.mimeData().data(FURN_MIME)).decode("utf-8")
            sp = grid_snap(self.mapToScene(e.position().toPoint()))
            item = make_furnishing(kind, sp)
            self.scene().addItem(item)
            if self.win._recorder is not None:
                self.win._recorder.on_place(kind, sp)
            self.win.status(f"Placed {item.name} ({fmt_ftin(item.w)} × "
                            f"{fmt_ftin(item.d)}). Drag to move; select and "
                            f"drag the round handle to rotate (Ctrl = 15° "
                            f"steps).")
            e.acceptProposedAction()
            return
        super().dropEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            if self._img_mode is not None:
                self._end_image_mode()
                self.win.status("Cancelled.")
                return
            self.cancel_temp()
            super().keyPressEvent(e)
            return
        nudges = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                  Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if e.key() in nudges:
            dx, dy = nudges[e.key()]
            fine = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if self.win.nudge_selected(dx, dy, fine):
                e.accept()
                return
        super().keyPressEvent(e)

    def cancel_temp(self):
        if self._temp_wall is not None:
            self.scene().removeItem(self._temp_wall)
            self._temp_wall = None

    # -- door / window placement ---------------------------------------------------
    def _place_opening(self, sp: QPointF, kind: str):
        wall = None
        for it in self.scene().items(sp):
            if isinstance(it, WallItem):
                wall = it
                break
            if isinstance(it, OpeningItem):
                wall = it.wall
                break
        if wall is None:
            self.win.status(f"Click on a wall to place a {kind}.")
            return

        default = self.win.last_door if kind == "door" else self.win.last_window
        code, ok = QInputDialog.getText(
            self, f"{kind.title()} size",
            'Size WWHH (width inches, height inches):', text=default)
        if not ok:
            return
        try:
            w, _h = parse_wwhh(code)
        except ValueError as ex:
            QMessageBox.warning(self, "Invalid size", str(ex))
            return
        if w > wall.length():
            QMessageBox.warning(self, "Too wide",
                                f"A {fmt_ftin(w)} opening will not fit in a "
                                f"{fmt_ftin(wall.length())} wall.")
            return

        s = round(wall.s_of(sp))
        s = min(max(s, w / 2), wall.length() - w / 2)
        # never stack two openings on top of each other (on this wall or a
        # coincident party wall): refuse if one already overlaps this span
        ctr = wall.point_at(s)
        for ow in [wall, *coincident_walls(self.scene(), wall)]:
            for ex in ow.openings:
                if QLineF(ow.point_at(ex.s), ctr).length() < (w + ex.width) / 2:
                    QMessageBox.warning(
                        self, "Opening in the way",
                        "There is already a door or window here (on this wall "
                        "or the wall coincident with it). Move or resize that "
                        "one instead.")
                    return
        op = OpeningItem(wall, kind, code.strip(), s)
        wall.openings.append(op)
        rebuild_all_walls(self.scene())   # coincident walls open for the new one
        if kind == "door":
            self.win.last_door = code.strip()
        else:
            self.win.last_window = code.strip()
        if self.win._recorder is not None:
            # record the size the user typed so replay needs no dialog
            self.win._recorder.on_opening(kind, sp, code.strip())


# ----------------------------------------------------------------------------
# Reference image backdrop (for importing a plan from a PNG)
# ----------------------------------------------------------------------------
class ReferenceImageItem(QGraphicsItem):
    """A raster floor-plan image dropped on the canvas as a movable, scalable,
    croppable, translucent backdrop for tracing / wall extraction.  `ipp` is
    inches-per-image-pixel (the scale): drag the body to move, drag a corner
    to rescale, right-click to calibrate / crop / extract / remove."""

    Z = -100.0
    HANDLE_PX = 9.0           # corner handle half-size, in view pixels
    MIN_IPP = 0.05

    def __init__(self, image, ipp: float, threshold: int = 128, merge: int = 3):
        super().__init__()
        self._img = image                       # QImage (RGB/whatever)
        self._ipp = float(ipp)
        self.threshold = int(threshold)
        self.merge = int(merge)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setZValue(self.Z)
        self._scaling = None                    # corner index while scaling

    # -- scale / geometry ----------------------------------------------------
    def inches_per_pixel(self) -> float:
        return self._ipp

    def set_inches_per_pixel(self, ipp: float):
        self.prepareGeometryChange()
        self._ipp = max(float(ipp), self.MIN_IPP)
        self.update()

    def _size_in(self):
        return (self._img.width() * self._ipp, self._img.height() * self._ipp)

    def _corner_local(self, i: int) -> QPointF:
        w, h = self._size_in()
        return [QPointF(0, 0), QPointF(w, 0), QPointF(w, h),
                QPointF(0, h)][i]

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _handle_in(self) -> float:
        return self.HANDLE_PX / self._view_scale()

    def boundingRect(self) -> QRectF:
        w, h = self._size_in()
        m = self._handle_in() + 1
        return QRectF(-m, -m, w + 2 * m, h + 2 * m)

    def paint(self, painter, option, widget=None):
        w, h = self._size_in()
        rect = QRectF(0, 0, w, h)
        painter.setOpacity(0.7)
        painter.drawImage(rect, self._img)
        painter.setOpacity(1.0)
        pen = QPen(QColor(37, 99, 235), 0)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
        if self.isSelected():
            hs = self._handle_in()
            painter.setBrush(QColor(37, 99, 235))
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(4):
                c = self._corner_local(i)
                painter.drawRect(QRectF(c.x() - hs, c.y() - hs, 2 * hs, 2 * hs))

    # -- corner-drag scaling -------------------------------------------------
    def _corner_at(self, local_pt: QPointF):
        hs = self._handle_in() * 1.6
        for i in range(4):
            if (self._corner_local(i) - local_pt).manhattanLength() <= 2 * hs:
                return i
        return None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._scaling = self._corner_at(e.pos())
            if self._scaling is not None:
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._scaling is not None:
            opp = (self._scaling + 2) % 4
            anchor = self.mapToScene(self._corner_local(opp))   # stays fixed
            new_w = abs(e.scenePos().x() - anchor.x())
            self.set_inches_per_pixel(new_w / max(self._img.width(), 1))
            self.setPos(anchor - self._corner_local(opp))       # re-anchor
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._scaling is not None:
            self._scaling = None
            e.accept()
            return
        super().mouseReleaseEvent(e)

    # -- calibrate / crop / extract (testable model methods) -----------------
    def calibrate(self, scene_p1: QPointF, scene_p2: QPointF, real_in: float):
        """Set the scale so the two scene points are `real_in` inches apart."""
        a, b = self.mapFromScene(scene_p1), self.mapFromScene(scene_p2)
        d_px = QLineF(a, b).length() / max(self._ipp, 1e-9)     # image pixels
        if d_px > 1e-6 and real_in > 0:
            self.set_inches_per_pixel(real_in / d_px)

    def crop_to_scene_rect(self, scene_rect: QRectF) -> bool:
        w, h = self._size_in()
        local = self.mapRectFromScene(scene_rect).intersected(
            QRectF(0, 0, w, h))
        if local.width() < self._ipp or local.height() < self._ipp:
            return False
        px = QRect(round(local.x() / self._ipp), round(local.y() / self._ipp),
                   round(local.width() / self._ipp),
                   round(local.height() / self._ipp)).intersected(
                       self._img.rect())
        if px.width() < 1 or px.height() < 1:
            return False
        shift = QPointF(px.x() * self._ipp, px.y() * self._ipp)
        self.prepareGeometryChange()
        self._img = self._img.copy(px)
        self.setPos(self.pos() + shift)
        self.update()
        return True

    def wall_segments(self, min_wall_in: float = 12.0):
        """Detected walls as (x0, y0, x1, y1) scene-inch tuples at the current
        scale/position."""
        import fp_extract
        gray = fp_extract.gray_from_qimage(self._img)
        out = []
        for x0, y0, x1, y1 in fp_extract.detect_walls(
                gray, self.threshold, 24, self.merge, 40):
            a = self.mapToScene(QPointF(x0 * self._ipp, y0 * self._ipp))
            b = self.mapToScene(QPointF(x1 * self._ipp, y1 * self._ipp))
            a = grid_snap(a, SETTINGS["wall_snap_in"])
            b = grid_snap(b, SETTINGS["wall_snap_in"])
            if (a - b).manhattanLength() >= min_wall_in:
                out.append((a.x(), a.y(), b.x(), b.y()))
        return out

    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_cal = menu.addAction("Calibrate scale (2 points)…")
        a_crop = menu.addAction("Crop to region")
        a_ext = menu.addAction("Extract walls")
        menu.addSeparator()
        a_rem = menu.addAction("Remove image")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        view = self._view()
        if chosen is a_cal and view is not None:
            view.start_image_calibrate(self)
        elif chosen is a_crop and view is not None:
            view.start_image_crop(self)
        elif chosen is a_ext and view is not None:
            view.win.extract_from_reference(self)
        elif chosen is a_rem and self.scene() is not None:
            self.scene().removeItem(self)
        e.accept()


# ----------------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    HINTS = {
        TOOL_SELECT: ("Select: drag wall BODY to slide it sideways (Ctrl = "
                      "free move) \u2022 drag wall ENDS to lengthen/shorten "
                      "(Shift = free angle) \u2022 drag furnishings from the "
                      "right palette onto the plan \u2022 Ctrl+click toggles "
                      "items in the selection set, Ctrl+drag rubber-bands "
                      "more in, Ctrl+G groups, Ctrl+X/C/V cut-copy-paste "
                      "\u2022 drag empty space to pan \u2022 wheel zoom"),
        TOOL_WALL_EXT: "Exterior wall (6\"): click-drag to draw. Orthogonal "
                       "from the anchor (hold Shift for free angle). Esc "
                       "cancels.",
        TOOL_WALL_INT: "Interior wall (4 1/2\"): click-drag to draw. "
                       "Orthogonal from the anchor (hold Shift for free "
                       "angle). Esc cancels.",
        TOOL_DOOR: "Door: click on a wall, then enter the WWHH size "
                   "(e.g. 3280 = 32\" x 80\").",
        TOOL_WINDOW: "Window: click on a wall, then enter the WWHH size "
                     "(e.g. 3648 = 36\" x 48\").",
        TOOL_ROOM: "Room name: click inside an enclosed area to name a room, "
                   "then the tool reverts to Select. Ctrl+click the tool to "
                   "keep it active for several rooms.",
    }

    def __init__(self):
        super().__init__()
        self.tool = TOOL_SELECT
        self._room_sticky = False        # one-shot Room tool unless Ctrl-set
        self.last_door = "3280"
        self.last_window = "3648"
        self.current_path = None
        self.room_clipboard = None
        self.item_clipboard = None        # cut/copied walls + furnishings
        self._recorder = None             # active MacroRecorderDialog (or None)
        self._recorder_dialog = None      # the (reused) recorder window
        self._update_title()

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        self._apply_canvas()
        self.view = PlanView(self.scene, self)
        self.setCentralWidget(self.view)

        self._build_toolbar()
        self._build_menus()
        self._build_palette()

        self.coord_label = QLabel("")
        self.statusBar().addPermanentWidget(self.coord_label)
        self.status(self.HINTS[TOOL_SELECT])

        # keep the toolbar totals current as rooms are added/resized/removed
        self.scene.changed.connect(self._update_totals)
        self._update_totals()

        self._z_top = 0                  # running max-z for bring-to-front

        # undo / redo: full-document snapshots captured after each change
        # settles (debounced), so every canvas operation is reversible
        self._undo_stack = []
        self._redo_stack = []
        self._restoring = False
        self._committed_state = self.serialize()
        self._dirty_timer = QTimer(self)
        self._dirty_timer.setSingleShot(True)
        self._dirty_timer.setInterval(180)
        self._dirty_timer.timeout.connect(self._commit_if_changed)
        self.scene.changed.connect(self._mark_dirty)
        self._update_undo_actions()

        self.resize(1280, 860)
        self.view.scale(1.1, 1.1)
        self.view.centerOn(QPointF(24 * FOOT, 16 * FOOT))

    # -- UI ------------------------------------------------------------------
    def _build_toolbar(self):
        tb = self.addToolBar("Tools")
        tb.setMovable(False)
        tb.setIconSize(QSize(26, 26))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        group = QActionGroup(self)
        group.setExclusive(True)
        self._tool_actions = {}

        defs = [
            (TOOL_SELECT, "Select", "S", "select"),
            (TOOL_WALL_EXT, "Exterior Wall", "E", "wall_ext"),
            (TOOL_WALL_INT, "Interior Wall", "I", "wall_int"),
            (TOOL_DOOR, "Door", "D", "door"),
            (TOOL_WINDOW, "Window", "W", "window"),
            (TOOL_ROOM, "Room Name", "R", "room"),
        ]
        for tool, label, key, icon in defs:
            a = QAction(tool_icon(icon), label, self)
            a.setCheckable(True)
            a.setShortcut(key)
            a.setToolTip(f"{label}  [{key}]")
            a.triggered.connect(lambda _=False, t=tool: self.set_tool(t))
            group.addAction(a)
            tb.addAction(a)
            self._tool_actions[tool] = a
        self._tool_actions[TOOL_SELECT].setChecked(True)

        tb.addSeparator()
        a_del = QAction(tool_icon("delete"), "Delete", self)
        a_del.setShortcuts([QKeySequence(Qt.Key.Key_Delete),
                            QKeySequence(Qt.Key.Key_Backspace)])
        a_del.setToolTip("Delete selection  [Del]")
        a_del.triggered.connect(self.delete_selected)
        tb.addAction(a_del)

        a_fit = QAction(tool_icon("zoomfit"), "Zoom Fit", self)
        a_fit.setShortcut("F")
        a_fit.setToolTip("Zoom to fit the plan  [F]")
        a_fit.triggered.connect(self.zoom_fit)
        tb.addAction(a_fit)

        tb.addSeparator()
        self.a_undo = QAction(tool_icon("undo"), "Undo", self)
        self.a_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.a_undo.setToolTip("Undo  [Ctrl+Z]")
        self.a_undo.triggered.connect(self.undo)
        self.a_undo.setEnabled(False)
        tb.addAction(self.a_undo)
        self.a_redo = QAction(tool_icon("redo"), "Redo", self)
        self.a_redo.setShortcuts([QKeySequence.StandardKey.Redo,
                                  QKeySequence("Ctrl+Y")])
        self.a_redo.setToolTip("Redo  [Ctrl+Y]")
        self.a_redo.triggered.connect(self.redo)
        self.a_redo.setEnabled(False)
        tb.addAction(self.a_redo)

        tb.addSeparator()
        a_rec = QAction(tool_icon("record"), "Record macro", self)
        a_rec.setToolTip("Record / debug a macro…")
        a_rec.triggered.connect(self.open_macro_recorder)
        tb.addAction(a_rec)

        spacer = QWidget()                       # push the totals to the right
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)
        self.totals_label = QLabel("Totals:  Cost-$0K   Sq. Feet-0")
        self.totals_label.setStyleSheet("padding: 0 12px; font-weight: 600;")
        self.totals_label.setToolTip(
            "Building total: the floor area of every room with “Include "
            "in total square footage” ticked (right-click a room name "
            "→ Properties…), priced at the cost per square foot set "
            "in File ▸ Settings….  Cost is shown in thousands of "
            "dollars.")
        tb.addWidget(self.totals_label)

        a_esc = QAction("select-esc", self)
        a_esc.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        a_esc.triggered.connect(lambda: self.set_tool(TOOL_SELECT))
        self.addAction(a_esc)

    def _build_palette(self):
        dock = QDockWidget("Furnishings", self)
        dock.setObjectName("furnishings")
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.furn_palette = FurnishingPalette(self)
        dock.setWidget(self.furn_palette)
        dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_menus(self):
        m_file = self.menuBar().addMenu("&File")
        a_new = QAction("&New plan", self)
        a_new.setShortcut(QKeySequence.StandardKey.New)
        a_new.triggered.connect(self.new_plan)
        m_file.addAction(a_new)
        a_open = QAction("&Open…", self)
        a_open.setShortcut(QKeySequence.StandardKey.Open)
        a_open.triggered.connect(self.open_plan)
        m_file.addAction(a_open)
        a_imp = QAction("&Import rooms from CSV…", self)
        a_imp.triggered.connect(self.import_rooms_csv)
        m_file.addAction(a_imp)
        a_img = QAction("Import from i&mage (PNG)…", self)
        a_img.triggered.connect(lambda: self.start_image_import())
        m_file.addAction(a_img)
        a_exp = QAction("&Export rooms to CSV…", self)
        a_exp.triggered.connect(self.export_rooms_csv)
        m_file.addAction(a_exp)
        m_file.addSeparator()
        a_save = QAction("&Save", self)
        a_save.setShortcut(QKeySequence.StandardKey.Save)
        a_save.triggered.connect(self.save_plan)
        m_file.addAction(a_save)
        a_saveas = QAction("Save &As…", self)
        a_saveas.setShortcut(QKeySequence.StandardKey.SaveAs)
        a_saveas.triggered.connect(self.save_plan_as)
        m_file.addAction(a_saveas)
        m_edit = self.menuBar().addMenu("&Edit")
        m_edit.addAction(self.a_undo)    # same actions as the toolbar buttons
        m_edit.addAction(self.a_redo)
        m_edit.addSeparator()
        for label, keys, slot in [
                ("Cu&t", QKeySequence.StandardKey.Cut, self.cut_selected),
                ("&Copy", QKeySequence.StandardKey.Copy, self.copy_selected),
                ("&Paste", QKeySequence.StandardKey.Paste,
                 self.paste_clipboard)]:
            a = QAction(label, self)
            a.setShortcut(QKeySequence(keys))
            a.triggered.connect(slot)
            m_edit.addAction(a)
        m_edit.addSeparator()
        self.a_group = QAction("&Group", self)
        self.a_group.setShortcut(QKeySequence("Ctrl+G"))
        self.a_group.triggered.connect(self.group_selected)
        m_edit.addAction(self.a_group)
        self.a_ungroup = QAction("&Ungroup", self)
        self.a_ungroup.setShortcut(QKeySequence("Ctrl+Shift+G"))
        self.a_ungroup.triggered.connect(self.ungroup_selected)
        m_edit.addAction(self.a_ungroup)

        m_rooms = self.menuBar().addMenu("&Rooms")
        self._room_op_actions = []
        for label, op in [("&Combine (union)", "combine"),
                          ("&Fragment into pieces", "fragment"),
                          ("&Subtract (1st − 2nd)", "subtract"),
                          ("&Intersect (overlap only)", "intersect")]:
            a = QAction(label, self)
            a.triggered.connect(lambda _checked, o=op: self.room_boolean(o))
            m_rooms.addAction(a)
            self._room_op_actions.append(a)
        m_rooms.addSeparator()
        self.a_align = QAction("&Align to grid", self)
        self.a_align.triggered.connect(self.align_rooms_to_grid)
        m_rooms.addAction(self.a_align)
        self._distribute_actions = []
        for label, horiz in [("Distribute &horizontally", True),
                             ("Distribute &vertically", False)]:
            a = QAction(label, self)
            a.triggered.connect(lambda _c, h=horiz: self.distribute_rooms(h))
            m_rooms.addAction(a)
            self._distribute_actions.append(a)
        a_refresh = QAction("&Refresh rooms (drop unwalled)", self)
        a_refresh.triggered.connect(self.refresh_rooms_cmd)
        m_rooms.addAction(a_refresh)

        m_inv = self.menuBar().addMenu("In&ventory")
        for label, slot in [("&House (structure)…", self.inventory_house),
                            ("&Interior furnishings…",
                             self.inventory_interior),
                            ("&Yard items…", self.inventory_yard),
                            ("&Total…", self.inventory_total)]:
            a = QAction(label, self)
            a.triggered.connect(slot)
            m_inv.addAction(a)

        m_ai = self.menuBar().addMenu("&AI")
        a_prices = QAction("Update furnishing &prices…", self)
        a_prices.triggered.connect(self.update_furnishing_prices)
        m_ai.addAction(a_prices)

        m_macro = self.menuBar().addMenu("&Macro")
        a_record = QAction("&Record / Debug…", self)
        a_record.setToolTip("Open the non-modal macro recorder")
        a_record.triggered.connect(self.open_macro_recorder)
        m_macro.addAction(a_record)

        m_help = self.menuBar().addMenu("&Help")
        a_about = QAction(f"&About {APP_NAME}…", self)
        a_about.triggered.connect(self.show_about)
        m_help.addAction(a_about)

        self.scene.selectionChanged.connect(self._update_edit_actions)
        self._update_edit_actions()

        m_file.addSeparator()
        a_set = QAction("Se&ttings…", self)
        a_set.triggered.connect(self.edit_settings)
        m_file.addAction(a_set)
        m_file.addSeparator()
        a_quit = QAction("&Quit", self)
        a_quit.setShortcut(QKeySequence.StandardKey.Quit)
        a_quit.triggered.connect(self.close)
        m_file.addAction(a_quit)

    # -- actions ----------------------------------------------------------------
    def _update_totals(self, *args):
        """Refresh the toolbar Totals label: floor area of the rooms flagged
        for inclusion, and that area priced at the cost per square foot."""
        if not hasattr(self, "totals_label"):
            return
        sqft = sum(it.area_sqft for it in self.scene.items()
                   if isinstance(it, RoomItem)
                   and it.properties.get("include_sqft", True))
        cost_k = sqft * float(SETTINGS.get("cost_per_sqft", 0.0)) / 1000.0
        self.totals_label.setText(
            f"Totals:  Cost-${cost_k:,.0f}K   Sq. Feet-{sqft:,.0f}")

    def edit_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        dlg.apply()
        self._apply_canvas()
        self._update_totals()            # cost per sq ft may have changed
        c = canvas_rect()
        self.status(f'Wall snap {SETTINGS["wall_snap_in"]:g}" · rotation '
                    f'snap {SETTINGS["rotate_snap_deg"]:g}° · canvas '
                    f"{fmt_ftin(c.width())} × {fmt_ftin(c.height())} · "
                    f'${SETTINGS["cost_per_sqft"]:g}/sq ft.')

    def update_furnishing_prices(self):
        """AI ▸ Update furnishing prices…: fetch current purchase prices for
        the whole catalog from the chosen AI system and store them in the
        manifest, refreshing palette tooltips and any placed items."""
        dlg = AIPricingDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.result_prices:
            return
        n = apply_furnishing_prices(dlg.result_prices)
        if hasattr(self, "furn_palette"):
            self.furn_palette.refresh_prices()
        for it in self.scene.items():
            if isinstance(it, FurnishingItem):
                spec = furnishing_spec(it.kind)
                if spec is not None:
                    it.price = float(spec.get("price", 0.0) or 0.0)
                    tip = (f"{it.name} — {fmt_ftin(it.w)} × {fmt_ftin(it.d)}")
                    if it.price > 0:
                        tip += f"  ·  ${it.price:,.0f}"
                    it.setToolTip(tip)
        self.status(f"Updated purchase prices for {n} furnishing(s) "
                    "from the AI.")

    def show_about(self):
        AboutDialog(self).exec()

    # -- inventories ----------------------------------------------------------
    def _show_inventory(self, title, headers, rows, note=None):
        InventoryDialog(title, headers, rows, parent=self, note=note).exec()

    def inventory_house(self):
        rows, sqft = house_inventory_rows(self.scene)
        self._show_inventory(
            "Inventory — House (structure)", HOUSE_INV_HEADERS, rows,
            note=f"Rooms, doors, windows and walls.  "
                 f"Total floor area {sqft:,.1f} sq ft.")

    def inventory_interior(self):
        interior, _ = classify_furnishings(self.scene)
        rows, qty, cost = furnishing_inventory_rows(interior)
        self._show_inventory(
            "Inventory — Interior furnishings", FURN_INV_HEADERS, rows,
            note=f"{qty} furnishing(s) inside rooms.  Prices come from the "
                 "AI ▸ Update furnishing prices… tool.")

    def inventory_yard(self):
        _, yard = classify_furnishings(self.scene)
        rows, qty, cost = furnishing_inventory_rows(yard)
        self._show_inventory(
            "Inventory — Yard items", FURN_INV_HEADERS, rows,
            note=f"{qty} item(s) outside any room (vehicles, yard "
                 "equipment, patio furniture…).")

    def inventory_total(self):
        rows = total_inventory_rows(self.scene)
        self._show_inventory(
            "Inventory — Total", TOTAL_INV_HEADERS, rows,
            note="Whole-plan summary.  Building cost uses File ▸ Settings ▸ "
                 "cost per sq ft; furnishing prices come from the AI menu.")

    def _apply_canvas(self):
        """Resize the scene around the configured canvas and refresh."""
        m = 30 * FOOT
        self.scene.setSceneRect(canvas_rect().adjusted(-m, -m, m, m))
        self.scene.update()
        self._update_title()

    def set_tool(self, tool):
        self.tool = tool
        self.view.cancel_temp()
        self._tool_actions[tool].setChecked(True)
        self.status(self.HINTS[tool])
        if tool == TOOL_ROOM:
            # Ctrl held while choosing the tool keeps it active (sticky);
            # otherwise it reverts to Select after one room is named
            self._room_sticky = bool(QApplication.keyboardModifiers()
                                     & Qt.KeyboardModifier.ControlModifier)
        if self._recorder is not None:
            self._recorder.on_tool(tool)

    def open_macro_recorder(self):
        """Open (or re-show) the non-modal macro recorder / debugger window."""
        if self._recorder_dialog is None:
            self._recorder_dialog = MacroRecorderDialog(self)
        self._recorder_dialog.show()
        self._recorder_dialog.raise_()
        self._recorder_dialog.activateWindow()

    def status(self, msg):
        self.statusBar().showMessage(msg)

    def show_coords(self, sp: QPointF):
        self.coord_label.setText(
            f"x {fmt_ftin(sp.x())}   y {fmt_ftin(sp.y())}")

    def delete_selected(self):
        for it in list(self.scene.selectedItems()):
            if it.scene() is None:
                continue
            if isinstance(it, OpeningItem):
                wall = it.wall
                if it in wall.openings:
                    wall.openings.remove(it)
                self.scene.removeItem(it)
                if wall.scene() is not None:
                    wall.rebuild()
            elif isinstance(it, (WallItem, RoomItem, FurnishingItem,
                                 GroupItem)):
                self.scene.removeItem(it)
        rebuild_all_walls(self.scene)

    # -- group / ungroup / cut / copy / paste -------------------------------------
    def _update_edit_actions(self):
        """Group is enabled once the selection set holds 2+ groupable
        items; Ungroup once it holds a group; room ops once exactly two
        rooms are selected.  Also tracks click order for subtract."""
        sel = self.scene.selectedItems()
        selset = set(sel)
        order = getattr(self, "_sel_order", [])
        order = [it for it in order if it in selset]
        for it in sel:
            if it not in order:
                order.append(it)
        self._sel_order = order
        n = sum(1 for it in sel
                if isinstance(it, (WallItem, FurnishingItem, GroupItem)))
        self.a_group.setEnabled(n >= 2)
        self.a_ungroup.setEnabled(
            any(isinstance(it, GroupItem) for it in sel))
        # room ops act on two rooms/wall-loops, selected directly or grouped;
        # align works on one or more
        nshapes = len(self._selected_room_shapes())
        for a in getattr(self, "_room_op_actions", []):
            a.setEnabled(nshapes == 2)
        if hasattr(self, "a_align"):
            self.a_align.setEnabled(nshapes >= 1)
        for a in getattr(self, "_distribute_actions", []):
            a.setEnabled(nshapes >= 3)

    def nudge_selected(self, dx: int, dy: int, fine: bool = False) -> bool:
        """Arrow-key nudge of selected groups / ungrouped furnishings by one
        wall-snap step (a fine 1" step with Ctrl).  Returns True if anything
        moved."""
        step = SNAP_STEP if fine else SETTINGS["wall_snap_in"]
        moved = 0
        for it in self.scene.selectedItems():
            if isinstance(it, GroupItem):
                it.setPos(it.pos().x() + dx * step, it.pos().y() + dy * step)
                it.bake()                 # fold the move into the members
                moved += 1
            elif isinstance(it, FurnishingItem) and it.group() is None:
                it.setPos(it.pos().x() + dx * step, it.pos().y() + dy * step)
                moved += 1
        return moved > 0

    def align_rooms_to_grid(self):
        """Snap the walls of every selected room (or grouped wall-loop) to
        the wall-snap grid, so off-grid rooms line up.  Axis-aligned walls
        stay orthogonal because both endpoints share a coordinate that
        snaps to the same grid line."""
        shapes = self._selected_room_shapes()
        if not shapes:
            self.status("Select rooms (or grouped rooms) to align to the grid.")
            return
        step = SETTINGS["wall_snap_in"]
        walls = set()
        for s in shapes:
            walls.update(s["walls"])
        for w in walls:
            w.p1 = grid_snap(w.p1, step)
            w.p2 = grid_snap(w.p2, step)
        rebuild_all_walls(self.scene)     # rooms re-detect on the new walls
        self.status(f"Aligned {len(shapes)} room(s) to the "
                    f'{step:g}" grid.')

    @staticmethod
    def _translate_shape(shape, dx, dy):
        """Rigidly shift a room shape (its walls and, if any, its region)."""
        for w in shape["walls"]:
            w.p1 = QPointF(w.p1.x() + dx, w.p1.y() + dy)
            w.p2 = QPointF(w.p2.x() + dx, w.p2.y() + dy)
        r = shape["room"]
        if r is not None:
            r.prepareGeometryChange()
            r.anchor = QPointF(r.anchor.x() + dx, r.anchor.y() + dy)
            r.path = QTransform.fromTranslate(dx, dy).map(r.path)
            if r.corners:
                r.corners = [QPointF(c.x() + dx, c.y() + dy) for c in r.corners]
            r._sync_corner_props()

    def distribute_rooms(self, horizontal: bool):
        """Space the selected rooms so the gaps between them are equal,
        keeping the two outermost rooms fixed (3+ rooms needed)."""
        shapes = self._selected_room_shapes()
        if len(shapes) < 3:
            self.status("Select at least three rooms to distribute evenly.")
            return
        items = [(s, QPolygonF(s["corners"]).boundingRect()) for s in shapes]
        if horizontal:
            items.sort(key=lambda t: t[1].left())
            free = ((items[-1][1].right() - items[0][1].left())
                    - sum(b.width() for _, b in items))
            gap = free / (len(items) - 1)
            cursor = items[0][1].left()
            for s, b in items:
                self._translate_shape(s, cursor - b.left(), 0.0)
                cursor += b.width() + gap
        else:
            items.sort(key=lambda t: t[1].top())
            free = ((items[-1][1].bottom() - items[0][1].top())
                    - sum(b.height() for _, b in items))
            gap = free / (len(items) - 1)
            cursor = items[0][1].top()
            for s, b in items:
                self._translate_shape(s, 0.0, cursor - b.top())
                cursor += b.height() + gap
        rebuild_all_walls(self.scene)
        self.status(f"Distributed {len(shapes)} rooms evenly "
                    f"{'horizontally' if horizontal else 'vertically'}.")

    def refresh_rooms_cmd(self):
        """Re-scan the canvas: delete any room whose region is no longer
        enclosed by walls (e.g. a gray area left behind after its walls
        were moved away), then re-detect the survivors."""
        sc = self.scene
        removed = 0
        for it in list(sc.items()):
            if isinstance(it, RoomItem) and not room_walled(sc, it):
                sc.removeItem(it)
                removed += 1
        refresh_rooms(sc)                 # re-detect the survivors' regions
        self.status(f"Rooms refreshed — removed {removed} orphaned room(s)."
                    if removed else "Rooms refreshed — all rooms are walled.")

    def _selected_room_shapes(self):
        """Ordered list of room shapes from the selection.  Each is a dict
        {corners, name, props, walls, room, group}.  A shape comes from a
        directly selected room, the room a selected group encloses, or --
        when a group is just a closed wall-loop with no RoomItem -- the
        traced loop itself."""
        shapes, seen = [], set()
        for it in getattr(self, "_sel_order", []):
            shape = None
            if isinstance(it, RoomItem) and it.corners:
                shape = {"corners": [QPointF(c) for c in it.corners],
                         "name": it.name, "props": dict(it.properties),
                         "walls": list(it.bounding_walls()),
                         "room": it, "group": None, "key": id(it)}
            elif isinstance(it, GroupItem):
                gw = [c for c in it.childItems() if isinstance(c, WallItem)]
                room = group_room(it)
                if room is not None and room.corners:
                    shape = {"corners": [QPointF(c) for c in room.corners],
                             "name": room.name, "props": dict(room.properties),
                             "walls": gw, "room": room, "group": it,
                             "key": id(room)}
                else:
                    loop = trace_wall_loop(gw)
                    if loop:
                        shape = {"corners": loop, "name": "Room", "props": {},
                                 "walls": gw, "room": None, "group": it,
                                 "key": id(it)}
            if shape is not None and shape["key"] not in seen:
                seen.add(shape["key"])
                shapes.append(shape)
        return shapes

    def room_boolean(self, op: str):
        """Boolean op on the two selected rooms' perimeter polygons.

        combine = union, intersect = overlap only, subtract = first room
        minus second (selection order), fragment = the three pieces
        (first-only, second-only, overlap).  The two rooms may be selected
        directly, via their groups, or as grouped wall-loops.  The inputs
        and their walls are replaced by freshly walled result rooms."""
        shapes = self._selected_room_shapes()
        if len(shapes) != 2:
            self.status("Select two rooms or grouped wall-loops first.")
            return
        s1, s2 = shapes
        sc = self.scene
        # free any grouped sources so their walls are normal scene walls
        for s in (s1, s2):
            g = s["group"]
            if g is not None and g.scene() is not None:
                g.bake()
                g.dissolve()
        p1, p2 = (room_path_from_corners(s1["corners"]),
                  room_path_from_corners(s2["corners"]))
        overlap = p1.intersected(p2)
        name1, name2 = s1["name"], s2["name"]
        if op in ("intersect", "subtract", "fragment") \
                and path_area_sqft(overlap) < 1.0:
            self.status(f"{name1} and {name2} do not overlap.")
            return

        if op == "combine":
            results = [(p1.united(p2), name1, s1["props"])]
        elif op == "subtract":
            results = [(p1.subtracted(p2), name1, s1["props"])]
        elif op == "intersect":
            results = [(overlap, "Overlap", {})]
        elif op == "fragment":
            results = [(p1.subtracted(p2), name1, s1["props"]),
                       (p2.subtracted(p1), name2, s2["props"]),
                       (overlap, "Overlap", {})]
        else:
            return

        # drop the input rooms and the walls that defined them
        old_walls = set(s1["walls"]) | set(s2["walls"])
        for s in (s1, s2):
            if s["room"] is not None and s["room"].scene() is not None:
                sc.removeItem(s["room"])
        for w in old_walls:
            if w.scene() is not None:
                sc.removeItem(w)

        # gather result sub-polygons
        regions = []
        for path, base, props in results:
            for poly in path.simplified().toSubpathPolygons():
                corners = simplify_corners(poly)
                if len(corners) >= 3 and poly_area_sqft(corners) >= 1.0:
                    regions.append((corners, base, props))
        # build a COMPLETE wall loop for every region -- shared edges get a
        # wall per region (no dedup), tracked per region, so each fragment
        # owns all its walls
        region_walls = []
        for corners, _, _ in regions:
            ws, n = [], len(corners)
            for j in range(n):
                a, b = corners[j], corners[(j + 1) % n]
                if QLineF(a, b).length() >= MIN_WALL_LEN:
                    w = WallItem(QPointF(a), QPointF(b), "interior")
                    sc.addItem(w)
                    ws.append(w)
            region_walls.append(ws)
        rebuild_all_walls(sc)

        # detect + create the result rooms; for fragment, group each
        # fragment with its own walls so it moves as a self-contained,
        # fully-enclosed unit (coincident neighbour walls stay put)
        sc.clearSelection()
        created = 0
        for (corners, base, props), ws in zip(regions, region_walls,
                                              strict=True):
            res = detect_room(sc, interior_point(QPolygonF(corners)))
            if res is None:
                continue
            room = RoomItem(unique_room_name(sc, base),
                            interior_point(QPolygonF(corners)),
                            res[0], res[1], corners=res[2], properties=props)
            sc.addItem(room)
            bind_room_walls(sc, room)
            created += 1
            if op == "fragment" and len(ws) >= 2:
                grp = GroupItem()
                sc.addItem(grp)
                for w in ws:
                    grp.adopt(w)
            else:
                room.setSelected(True)
        self.status(f"{op.title()}: {name1} + {name2} -> {created} room(s).")

    def group_selected(self):
        """Group the selected walls/furnishings (existing groups merge)."""
        members, old_groups = [], []
        for it in list(self.scene.selectedItems()):
            if isinstance(it, GroupItem):
                old_groups.append(it)
            elif isinstance(it, (WallItem, FurnishingItem)):
                members.append(it)
        for g in old_groups:
            g.bake()
            members += g.dissolve()
        if len(members) < 2:
            self.status("Select at least two walls/furnishings to group "
                        "(Ctrl+click to multi-select).")
            return
        self.scene.clearSelection()
        group = GroupItem()
        self.scene.addItem(group)
        for it in members:
            group.adopt(it)
        group.setSelected(True)
        self.status(f"Grouped {len(members)} items — drag to move, "
                    "Ctrl+Shift+G to ungroup.")

    def ungroup_selected(self):
        groups = [it for it in self.scene.selectedItems()
                  if isinstance(it, GroupItem)]
        if not groups:
            self.status("Select a group to ungroup.")
            return
        for g in groups:
            g.bake()                      # members keep their moved spot
            for c in g.dissolve():
                c.setSelected(True)
        rebuild_all_walls(self.scene)     # rooms re-detect region/outline
        self.status("Ungrouped — items left in place.")

    def _selection_spec(self):
        """Selected walls/furnishings (groups expand to their members)
        as a clipboard dict, or None when nothing usable is selected."""
        items = []
        for it in self.scene.selectedItems():
            if isinstance(it, GroupItem):
                it.bake()
                items += it.childItems()
            elif isinstance(it, (WallItem, FurnishingItem)):
                items.append(it)
        if not items:
            return None
        walls, furns = [], []
        xs, ys = [], []
        for it in items:
            if isinstance(it, WallItem):
                walls.append({
                    "type": it.wall_type,
                    "p1": [it.p1.x(), it.p1.y()],
                    "p2": [it.p2.x(), it.p2.y()],
                    "openings": [{
                        "kind": op.kind, "code": op.code, "s": op.s,
                        "door_type": op.door_type, "swing": op.swing,
                    } for op in it.openings],
                })
                xs += [it.p1.x(), it.p2.x()]
                ys += [it.p1.y(), it.p2.y()]
            else:
                p = it.scenePos()
                furns.append({"kind": it.kind, "pos": [p.x(), p.y()],
                              "rotation": it.rotation(), **it.extra_state()})
                xs.append(p.x())
                ys.append(p.y())
        ref = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]
        return {"ref": ref, "walls": walls, "furnishings": furns,
                "grouped": len(items) > 1}

    # -- undo / redo ---------------------------------------------------------
    UNDO_LIMIT = 100

    def _mark_dirty(self, *args):
        """A scene change happened: (re)start the debounce so a burst of
        changes (e.g. a drag) becomes one undo step once it settles."""
        if not self._restoring:
            self._dirty_timer.start()

    def _commit_if_changed(self):
        """Snapshot the plan as one undo step if it differs from the last
        committed state."""
        if self._restoring:
            return
        state = self.serialize()
        if state == self._committed_state:
            return
        self._undo_stack.append(self._committed_state)
        if len(self._undo_stack) > self.UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._committed_state = state
        self._update_undo_actions()

    def _restore_state(self, state):
        self._dirty_timer.stop()
        self._restoring = True
        try:
            self.load_data(state)
        finally:
            self._restoring = False
        self._committed_state = self.serialize()
        self._update_undo_actions()

    def _reset_undo(self):
        """Drop the history (after New / Open): the current plan becomes the
        baseline state."""
        self._dirty_timer.stop()
        self._z_top = 0
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._committed_state = self.serialize()
        self._update_undo_actions()

    def undo(self):
        self._commit_if_changed()        # fold in any pending change first
        if not self._undo_stack:
            self.status("Nothing to undo.")
            return
        self._redo_stack.append(self._committed_state)
        self._restore_state(self._undo_stack.pop())
        self.status("Undo.")

    def redo(self):
        self._commit_if_changed()
        if not self._redo_stack:
            self.status("Nothing to redo.")
            return
        self._undo_stack.append(self._committed_state)
        self._restore_state(self._redo_stack.pop())
        self.status("Redo.")

    def _update_undo_actions(self):
        if hasattr(self, "a_undo"):
            self.a_undo.setEnabled(bool(self._undo_stack))
            self.a_redo.setEnabled(bool(self._redo_stack))

    def cut_selected(self):
        spec = self._selection_spec()
        if spec is None:
            self.status("Select walls/furnishings (or a group) to cut.")
            return
        self.item_clipboard = spec
        for it in list(self.scene.selectedItems()):
            if isinstance(it, (GroupItem, WallItem, FurnishingItem)) \
                    and it.scene() is not None:
                self.scene.removeItem(it)
        rebuild_all_walls(self.scene)
        n = len(spec["walls"]) + len(spec["furnishings"])
        self.status(f"Cut {n} item(s) — Ctrl+V to paste at the mouse "
                    "position.")

    def copy_selected(self):
        spec = self._selection_spec()
        if spec is None:
            self.status("Select walls/furnishings (or a group) to copy.")
            return
        self.item_clipboard = spec
        n = len(spec["walls"]) + len(spec["furnishings"])
        self.status(f"Copied {n} item(s) — Ctrl+V to paste at the mouse "
                    "position.")

    def paste_clipboard(self):
        """Paste the cut/copied items centred on the mouse position,
        re-grouped when more than one item was taken."""
        spec = self.item_clipboard
        if not spec:
            self.status("Nothing to paste — cut or copy items first.")
            return
        target = self.view._last_scene
        if target is None:
            target = self.view.mapToScene(
                self.view.viewport().rect().center())
        dx, dy = target.x() - spec["ref"][0], target.y() - spec["ref"][1]
        if spec["walls"]:                 # keep walls on the on-centre grid
            dx, dy = wall_snap_len(dx), wall_snap_len(dy)
        else:
            dx, dy = round(dx), round(dy)
        pasted = []
        for wd in spec["walls"]:
            wall = WallItem(QPointF(wd["p1"][0] + dx, wd["p1"][1] + dy),
                            QPointF(wd["p2"][0] + dx, wd["p2"][1] + dy),
                            wd["type"])
            self.scene.addItem(wall)
            for od in wd["openings"]:
                try:
                    op = OpeningItem(wall, od["kind"], od["code"], od["s"])
                except ValueError:
                    continue
                op.door_type = od["door_type"]
                op.swing = od["swing"]
                wall.openings.append(op)
            wall.rebuild()
            pasted.append(wall)
        for fd in spec["furnishings"]:
            f = make_furnishing(
                fd["kind"], QPointF(fd["pos"][0] + dx, fd["pos"][1] + dy),
                fd["rotation"], fd)
            self.scene.addItem(f)
            pasted.append(f)
        rebuild_all_walls(self.scene)
        self.scene.clearSelection()
        if spec.get("grouped") and len(pasted) > 1:
            group = GroupItem()
            self.scene.addItem(group)
            for it in pasted:
                group.adopt(it)
            group.setSelected(True)
        else:
            for it in pasted:
                it.setSelected(True)
        self.status(f"Pasted {len(pasted)} item(s).")

    def zoom_fit(self):
        items = [it for it in self.scene.items() if isinstance(it, WallItem)]
        if items:
            rect = QRectF()
            for it in items:
                rect = rect.united(it.boundingRect())
            rect = rect.adjusted(-5 * FOOT, -5 * FOOT, 5 * FOOT, 5 * FOOT)
        else:
            rect = QRectF(-2 * FOOT, -2 * FOOT, 60 * FOOT, 44 * FOOT)
        self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def new_plan(self):
        if QMessageBox.question(
                self, "New plan", "Clear everything and start over?"
        ) == QMessageBox.StandardButton.Yes:
            self.scene.clear()
            self.current_path = None
            SETTINGS.update(DEFAULT_SETTINGS)
            self._apply_canvas()
            self._reset_undo()

    # -- save / load -------------------------------------------------------------
    def _update_title(self):
        if self.current_path:
            self.setWindowTitle(f"Floor Planner — {self.current_path}")
        else:
            c = canvas_rect()
            self.setWindowTitle(f"Floor Planner — canvas "
                                f"{fmt_ftin(c.width())} × "
                                f"{fmt_ftin(c.height())}")

    def serialize(self) -> dict:
        """Plan -> plain dict matching the documented JSON format.

        The walls/rooms/furnishings arrays are emitted in a stable,
        z-independent order (sorted by geometry) so that bring-to-front
        z changes never alter the serialized document — keeping the
        undo/redo snapshot comparison correct."""
        walls, rooms, furnishings = [], [], []
        for it in self.scene.items():
            if isinstance(it, FurnishingItem):
                furnishings.append({
                    "kind": it.kind,
                    "pos": [it.pos().x(), it.pos().y()],
                    "rotation": it.rotation(),
                    **it.extra_state(),
                })
            elif isinstance(it, WallItem) and not it.is_open:
                # open walls are derived from a room's open edges, so they are
                # regenerated on load rather than stored
                walls.append({
                    "type": it.wall_type,
                    "p1": [it.p1.x(), it.p1.y()],
                    "p2": [it.p2.x(), it.p2.y()],
                    "room": it.room.name if it.room is not None else None,
                    "openings": [{
                        "kind": op.kind,
                        "code": op.code,
                        "s": op.s,
                        "door_type": op.door_type,
                        "swing": op.swing,
                    } for op in sorted(it.openings, key=lambda o: o.s)],
                })
            elif isinstance(it, RoomItem):
                rooms.append({
                    "name": it.name,
                    "anchor": [it.anchor.x(), it.anchor.y()],
                    "label_offset": [it.label_offset.x(), it.label_offset.y()],
                    "show_dimensions": it.show_dims,
                    "properties": it.properties,
                })
        walls.sort(key=lambda w: (w["p1"], w["p2"], w["type"],
                                  w["room"] or ""))
        rooms.sort(key=lambda r: r["name"])
        furnishings.sort(key=lambda f: (f["pos"], f["kind"], f["rotation"]))
        return {
            "format": FILE_FORMAT,
            "version": FILE_VERSION,
            "units": "inches",
            "settings": dict(SETTINGS),
            "walls": walls,
            "rooms": rooms,
            "furnishings": furnishings,
        }

    def load_data(self, data: dict):
        if data.get("format") != FILE_FORMAT:
            raise ValueError("Not a Floor Planner JSON file.")
        loaded = data.get("settings", {})
        for key, default in DEFAULT_SETTINGS.items():
            try:
                SETTINGS[key] = float(loaded.get(key, default))
            except (TypeError, ValueError):
                SETTINGS[key] = default
        self._apply_canvas()
        self.scene.clear()
        self._z_top = 0                  # bring-to-front counter resets per doc
        for wd in data.get("walls", []):
            wall = WallItem(QPointF(*wd["p1"]), QPointF(*wd["p2"]),
                            wd.get("type", "interior"))
            self.scene.addItem(wall)
            for od in wd.get("openings", []):
                try:
                    op = OpeningItem(wall, od.get("kind", "door"),
                                     str(od.get("code", "3280")),
                                     float(od.get("s", wall.length() / 2)))
                except ValueError:
                    continue              # e.g. opening wider than the wall
                op.door_type = od.get("door_type", "LH")
                op.swing = -1 if float(od.get("swing", -1)) < 0 else 1
                wall.openings.append(op)
            wall.rebuild()
        rebuild_all_walls(self.scene)
        missing = []
        for rd in data.get("rooms", []):
            anchor = QPointF(*rd.get("anchor", [0, 0]))
            res = detect_room(self.scene, anchor)
            if res is None:
                # an open room (a wall was detached/moved away) won't flood-fill
                # -> rebuild it from the saved perimeter corners
                saved = (rd.get("properties") or {}).get("perimeter_corners")
                if saved and len(saved) >= 3:
                    corners = [QPointF(c[0], c[1]) for c in saved]
                    res = (room_path_from_corners(corners),
                           poly_area_sqft(corners), corners)
                else:
                    # keep the room (so it survives a re-save); placeholder
                    path = QPainterPath()
                    path.addRect(QRectF(anchor.x() - 12, anchor.y() - 12,
                                        24, 24))
                    res = (path, 0.0, None)
                    missing.append(rd.get("name", "?"))
            name = unique_room_name(self.scene, rd.get("name", "Room"))
            room = RoomItem(name, anchor, res[0], res[1],
                            rd.get("properties"), res[2])
            room.show_dims = bool(rd.get("show_dimensions", False))
            room.label_offset = QPointF(*rd.get("label_offset", [0.0, 0.0]))
            self.scene.addItem(room)
            # bind this room's walls by geometry (works for both v2 plans,
            # which store coincident party walls, and legacy v1 plans)
            bind_room_walls(self.scene, room, settle=False)
        unknown = []
        for fd in data.get("furnishings", []):
            kind = str(fd.get("kind", ""))
            if furnishing_spec(kind) is None:
                unknown.append(kind or "?")
                continue
            self.scene.addItem(make_furnishing(
                kind, QPointF(*fd.get("pos", [0.0, 0.0])),
                float(fd.get("rotation", 0.0)), fd))
        notes = []
        if missing:
            notes.append("Could not re-detect room(s): " + ", ".join(missing)
                         + " — check the walls around them.")
        if unknown:
            notes.append("Skipped unknown furnishing kind(s): "
                         + ", ".join(unknown) + ".")
        if notes:
            self.status("  ".join(notes))

    def paste_room(self, sp: QPointF):
        """Recreate the copied room (walls, openings, properties) with its
        anchor at `sp`; the name gets a number appended if already used."""
        spec = self.room_clipboard
        if not spec:
            return
        src = QPointF(*spec["anchor"])
        dx = wall_snap_len(sp.x() - src.x())   # pasted walls stay on the
        dy = wall_snap_len(sp.y() - src.y())   # same on-centre grid
        for wd in spec["walls"]:
            wall = WallItem(QPointF(wd["p1"][0] + dx, wd["p1"][1] + dy),
                            QPointF(wd["p2"][0] + dx, wd["p2"][1] + dy),
                            wd["type"])
            self.scene.addItem(wall)
            for od in wd["openings"]:
                try:
                    op = OpeningItem(wall, od["kind"], od["code"], od["s"])
                except ValueError:
                    continue
                op.door_type = od["door_type"]
                op.swing = od["swing"]
                wall.openings.append(op)
            wall.rebuild()
        rebuild_all_walls(self.scene)
        anchor = QPointF(src.x() + dx, src.y() + dy)
        res = detect_room(self.scene, anchor)
        if res is None:
            self.status("Pasted the walls, but no enclosed room was "
                        "detected at the paste point.")
            return
        path, area, corners = res
        name = unique_room_name(self.scene, spec["name"])
        room = RoomItem(name, anchor, path, area,
                        dict(spec["properties"]), corners)
        room.show_dims = bool(spec["show_dimensions"])
        self.scene.addItem(room)
        bind_room_walls(self.scene, room)
        self.status(f"Pasted room '{name}'.")

    # -- CSV room import ----------------------------------------------------------
    def _wall_exists(self, p1: QPointF, p2: QPointF) -> bool:
        for it in self.scene.items():
            if isinstance(it, WallItem) and (
                    (QLineF(it.p1, p1).length() < 0.6
                     and QLineF(it.p2, p2).length() < 0.6)
                    or (QLineF(it.p1, p2).length() < 0.6
                        and QLineF(it.p2, p1).length() < 0.6)):
                return True
        return False

    def _free_spot(self, w_in: float, h_in: float):
        """Top-left corner (snapped) of a canvas spot where a w x h room
        won't touch existing walls or rooms (24" clearance)."""
        margin = 24.0
        canvas = canvas_rect()
        occupied = []
        for it in self.scene.items():
            if isinstance(it, WallItem):
                occupied.append(it.boundingRect())
            elif isinstance(it, RoomItem):
                occupied.append(it.path.boundingRect())
        step = max(SETTINGS["wall_snap_in"], 12.0)
        y = canvas.top() + margin
        while y + h_in + margin <= canvas.bottom():
            x = canvas.left() + margin
            while x + w_in + margin <= canvas.right():
                cand = QRectF(x - margin / 2, y - margin / 2,
                              w_in + margin, h_in + margin)
                if not any(cand.intersects(r) for r in occupied):
                    return x, y
                x += step
            y += step
        # canvas full: park it to the right of everything
        right = max([r.right() for r in occupied], default=canvas.left())
        return wall_snap_len(right + margin), canvas.top() + margin

    def import_rooms_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import rooms from CSV", "",
            "CSV files (*.csv);;All files (*)")
        if path:
            self._import_rooms(path)

    # -- import a plan from a PNG image (preview -> accept) -------------------
    def import_from_image(self, path=None, *, width_ft=40.0, merge=3,
                          threshold=128, wall_type="exterior",
                          interactive=True):
        """File > Import from image: detect walls in a raster floor plan, show
        them as a blue ghost overlay, and add them on accept.  Pass
        interactive=False (with explicit params) to run headlessly."""
        if interactive and path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import plan from image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*)")
            if not path:
                return None
            dlg = ImageImportDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return None
            width_ft, merge, threshold = dlg.values()
        try:
            import fp_extract
            gray = fp_extract.load_gray(path)
            h, w = gray.shape
            walls_px = fp_extract.detect_walls(gray, threshold, 24, merge, 40)
            segs = fp_extract.scene_segments(walls_px, w, h, width_ft=width_ft)
        except Exception as ex:                       # noqa: BLE001
            if interactive:
                QMessageBox.critical(self, "Import failed", str(ex))
            return None
        if not segs:
            if interactive:
                QMessageBox.information(
                    self, "Import from image",
                    "No walls detected.  Try a cleaner image or adjust the "
                    "threshold / merge settings.")
            return None

        self._show_wall_ghost(segs)
        if interactive:
            ok = QMessageBox.question(
                self, "Import from image",
                f"Detected {len(segs)} wall(s), shown in blue on the canvas.\n"
                "Add them to the plan?") == QMessageBox.StandardButton.Yes
            self._clear_wall_ghost()
            if not ok:
                return None
        else:
            self._clear_wall_ghost()

        for x0, y0, x1, y1 in segs:
            self.scene.addItem(
                WallItem(QPointF(x0, y0), QPointF(x1, y1), wall_type))
        rebuild_all_walls(self.scene)
        self._update_totals()
        self._commit_if_changed()
        self.status(f"Imported {len(segs)} wall(s) from {os.path.basename(path)}"
                    " — click an enclosed area with the Room tool to name it.")
        return len(segs)

    def _show_wall_ghost(self, segs):
        """Draw the candidate walls as a translucent blue overlay and fit the
        view to them so the user can preview before accepting."""
        self._clear_wall_ghost()
        path = QPainterPath()
        for x0, y0, x1, y1 in segs:
            path.moveTo(QPointF(x0, y0))
            path.lineTo(QPointF(x1, y1))
        item = QGraphicsPathItem(path)
        pen = QPen(QColor(37, 99, 235, 170), 6.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        item.setPen(pen)
        item.setZValue(1_000_000)                     # above everything
        self.scene.addItem(item)
        self._wall_ghost = item
        self.view.fitInView(item.boundingRect().adjusted(-24, -24, 24, 24),
                            Qt.AspectRatioMode.KeepAspectRatio)

    def _clear_wall_ghost(self):
        item = getattr(self, "_wall_ghost", None)
        if item is not None:
            if item.scene() is not None:
                self.scene.removeItem(item)
            self._wall_ghost = None

    # -- interactive image backdrop: place, calibrate, extract ---------------
    def start_image_import(self, path=None):
        """File > Import from image: drop the PNG on the canvas as a backdrop
        to move / scale / crop / calibrate, then Extract walls."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import plan from image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*)")
            if not path:
                return None
        img = QImage(path)
        if img.isNull():
            QMessageBox.critical(self, "Import failed",
                                 f"Could not read image:\n{path}")
            return None
        ipp = canvas_rect().width() * 0.7 / max(img.width(), 1)
        item = ReferenceImageItem(img, ipp)
        item.setPos(QPointF(canvas_rect().width() * 0.1,
                            canvas_rect().height() * 0.1))
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        self.view.fitInView(item.sceneBoundingRect().adjusted(-48, -48, 48, 48),
                            Qt.AspectRatioMode.KeepAspectRatio)
        self.status("Image placed — drag to move, drag a corner to scale, "
                    "right-click for Calibrate / Crop / Extract walls / "
                    "Remove.")
        return item

    def _finish_calibrate(self, item, pts):
        val, ok = QInputDialog.getDouble(
            self, "Calibrate scale",
            "Real distance between the two clicked points (feet):",
            10.0, 0.01, 100000.0, 2)
        if not ok or item is None:
            return
        item.calibrate(pts[0], pts[1], val * FOOT)
        self.status(f"Calibrated — that span is now {fmt_ftin(val * FOOT)}.")

    def extract_from_reference(self, item, interactive=True):
        """Detect walls in the (scaled/cropped) backdrop and add them, with a
        blue ghost preview when interactive."""
        segs = item.wall_segments()
        if not segs:
            if interactive:
                QMessageBox.information(
                    self, "Extract walls",
                    "No walls detected.  Calibrate/crop closer or adjust the "
                    "image, then try again.")
            return None
        self._show_wall_ghost(segs)
        if interactive:
            ok = QMessageBox.question(
                self, "Extract walls",
                f"Detected {len(segs)} wall(s), shown in blue.  Add them to "
                "the plan?") == QMessageBox.StandardButton.Yes
            self._clear_wall_ghost()
            if not ok:
                return None
        else:
            self._clear_wall_ghost()
        for x0, y0, x1, y1 in segs:
            self.scene.addItem(
                WallItem(QPointF(x0, y0), QPointF(x1, y1), "exterior"))
        rebuild_all_walls(self.scene)
        self._update_totals()
        self._commit_if_changed()
        self.status(f"Added {len(segs)} wall(s) — right-click the image to "
                    "remove it, then name rooms with the Room tool.")
        return len(segs)

    def _import_rooms(self, path: str, interactive: bool = True):
        """Create walled rooms from a CSV with the columns
        Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes (Type, locations and
        Notes optional).  X_ft/Y_ft are the room's perimeter width and
        length; X_loc/Y_loc place its BOTTOM-LEFT corner, measured in
        feet from the canvas's bottom-left corner.  Rooms without a
        location go to the first clear spot on the canvas.

        The canvas grows (never shrinks) so every room fits, up to
        MAX_CANVAS_IN; a room whose size/location needs more than that is
        rejected as a likely typo."""
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise ValueError("Empty CSV file.")
                rows = [{(k or "").strip().lower(): (v or "").strip()
                         for k, v in row.items()} for row in reader]
        except (OSError, csv.Error, ValueError) as ex:
            if interactive:
                QMessageBox.critical(self, "Import failed", str(ex))
            self.status(f"Import failed: {ex}")
            return
        margin = 2.0 * FOOT
        max_in = MAX_CANVAS_IN

        # -- pass 1: parse + validate every row (no placement yet) --------
        specs, errors = [], []
        for i, row in enumerate(rows, start=2):     # 1 = header line
            name = row.get("name", "")
            try:
                if not name:
                    raise ValueError("missing Name")
                w_in = parse_feet(row["x_ft"])
                h_in = parse_feet(row["y_ft"])
                if w_in < 36.0 or h_in < 36.0:
                    raise ValueError("rooms must be at least 3' x 3'")
                xl, yl = row.get("x_loc_ft", ""), row.get("y_loc_ft", "")
                if xl and yl:
                    xl_in, yl_in, located = parse_feet(xl), parse_feet(yl), True
                elif xl or yl:
                    raise ValueError("give both X_loc_ft and Y_loc_ft, "
                                     "or neither")
                else:
                    xl_in = yl_in = None
                    located = False
                far_w = (xl_in + w_in) if located else w_in
                far_h = (yl_in + h_in) if located else h_in
                if far_w > max_in or far_h > max_in:
                    raise ValueError(
                        f"exceeds the {max_in / FOOT:g}' canvas limit "
                        "(check for a typo)")
            except (KeyError, ValueError) as ex:
                errors.append(f"line {i} ({name or '?'}): {ex}")
                continue
            specs.append({"name": name, "w": w_in, "h": h_in,
                          "located": located, "xl": xl_in, "yl": yl_in,
                          "type": row.get("type", ""),
                          "notes": row.get("notes", "")})

        # -- grow the canvas so every room fits (grow only, capped) -------
        # located rooms drive both dimensions; auto-placed rooms only need
        # the height to be tall enough to hold them (width grows afterwards)
        req_w = max([s["xl"] + s["w"] + margin
                     for s in specs if s["located"]], default=0.0)
        req_h = max([s["yl"] + s["h"] + margin
                     for s in specs if s["located"]]
                    + [s["h"] + 2 * margin
                       for s in specs if not s["located"]], default=0.0)
        new_w = min(max(SETTINGS["canvas_w_in"], req_w), max_in)
        new_h = min(max(SETTINGS["canvas_h_in"], req_h), max_in)
        resized = (new_w > SETTINGS["canvas_w_in"]
                   or new_h > SETTINGS["canvas_h_in"])
        if resized:
            SETTINGS["canvas_w_in"], SETTINGS["canvas_h_in"] = new_w, new_h
            self._apply_canvas()

        # -- pass 2: build the rooms (canvas height is now final) ---------
        canvas = canvas_rect()
        imported = 0
        for s in specs:
            w_in, h_in = s["w"], s["h"]
            if s["located"]:
                left = wall_snap_len(s["xl"])
                top = wall_snap_len(canvas.bottom() - s["yl"] - h_in)
            else:
                left, top = self._free_spot(w_in, h_in)
            corners = [QPointF(left, top), QPointF(left + w_in, top),
                       QPointF(left + w_in, top + h_in),
                       QPointF(left, top + h_in)]
            for j in range(4):
                p1, p2 = corners[j], corners[(j + 1) % 4]
                if not self._wall_exists(p1, p2):
                    self.scene.addItem(WallItem(QPointF(p1), QPointF(p2),
                                                "interior"))
            rebuild_all_walls(self.scene)
            centre = QPointF(left + w_in / 2, top + h_in / 2)
            res = detect_room(self.scene, centre)
            if res is None:
                errors.append(f"{s['name']}: no enclosed area detected "
                              "(overlapping another room?)")
                continue
            room = RoomItem(unique_room_name(self.scene, s["name"]), centre,
                            res[0], res[1], corners=res[2])
            if s["type"]:
                room.properties["room_type"] = next(
                    (t for t in ROOM_TYPES if t.lower() == s["type"].lower()),
                    s["type"])
            if s["notes"]:
                room.properties["notes"] = s["notes"]
            self.scene.addItem(room)
            bind_room_walls(self.scene, room)
            imported += 1

        # -- grow width for any auto-placed room parked past the edge -----
        walls = [it for it in self.scene.items() if isinstance(it, WallItem)]
        right = max([p.x() for it in walls for p in (it.p1, it.p2)],
                    default=0.0)
        if right + margin > canvas.right():
            grow_w = min(right + margin, max_in)
            if grow_w > SETTINGS["canvas_w_in"]:
                SETTINGS["canvas_w_in"] = grow_w
                self._apply_canvas()
                resized = True

        note = ""
        if resized:
            c = canvas_rect()
            note = (f" Canvas resized to {c.width() / FOOT:g}' × "
                    f"{c.height() / FOOT:g}'.")
        self.status(f"Imported {imported} room(s) from {path}"
                    + (f" — {len(errors)} row(s) skipped." if errors else ".")
                    + note)
        self._import_errors = errors      # inspectable (and testable)
        if errors and interactive:
            QMessageBox.warning(self, "Import finished with problems",
                                "\n".join(errors[:20]))

    def export_rooms_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export rooms to CSV", "rooms.csv",
            "CSV files (*.csv);;All files (*)")
        if path:
            self._export_rooms(path)

    def _export_rooms(self, path: str, interactive: bool = True):
        """Write every room as a CSV row in the same format the importer
        reads (Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes), so a plan's
        rooms round-trip.  Sizes/locations come from the room perimeter
        (wall centrelines); locations are the bottom-left corner in feet
        from the canvas's bottom-left corner, lengths in decimal feet."""

        def ft(v: float) -> str:
            return f"{v / 12.0:g}"

        canvas = canvas_rect()
        rooms = sorted((it for it in self.scene.items()
                        if isinstance(it, RoomItem)),
                       key=lambda r: r.name.lower())
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(["Name", "Type", "X_ft", "Y_ft",
                             "X_loc_ft", "Y_loc_ft", "Notes"])
                for r in rooms:
                    if r.corners:
                        xs = [c.x() for c in r.corners]
                        ys = [c.y() for c in r.corners]
                    else:                   # no traced perimeter: use the
                        rect = r.interior_rect()      # flood region box
                        xs = [rect.left(), rect.right()]
                        ys = [rect.top(), rect.bottom()]
                    wr.writerow([
                        r.name,
                        r.properties.get("room_type", ""),
                        ft(max(xs) - min(xs)),
                        ft(max(ys) - min(ys)),
                        ft(min(xs)),
                        ft(canvas.bottom() - max(ys)),
                        " ".join(str(r.properties.get("notes", ""))
                                 .split()),
                    ])
        except OSError as ex:
            if interactive:
                QMessageBox.critical(self, "Export failed", str(ex))
            self.status(f"Export failed: {ex}")
            return
        self.status(f"Exported {len(rooms)} room(s) to {path}")

    def open_plan(self):
        start = self.current_path or str(designs_dir())
        path, _ = QFileDialog.getOpenFileName(
            self, "Open plan", start,
            "Floor plan JSON (*.json);;All files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.load_data(data)
        except (OSError, ValueError, KeyError, TypeError) as ex:
            QMessageBox.critical(self, "Open failed", str(ex))
            return
        self.current_path = path
        self._update_title()
        self._reset_undo()               # opened document is the new baseline
        self.status(f"Opened {path}")

    def save_plan(self):
        if not self.current_path:
            self.save_plan_as()
            return
        self._write_plan(self.current_path)

    def save_plan_as(self):
        start = self.current_path or str(designs_dir() / "floorplan.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save plan", start,
            "Floor plan JSON (*.json);;All files (*)")
        if not path:
            return
        self._write_plan(path)

    def _write_plan(self, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.serialize(), f, indent=2)
        except OSError as ex:
            QMessageBox.critical(self, "Save failed", str(ex))
            return
        self.current_path = path
        self._update_title()
        self.status(f"Saved {path}")

    # -- headless / macro hooks ----------------------------------------------
    # These let an external driver (fp_macro.py) load, edit, snapshot and save
    # a plan with no dialogs.  See docs/macro_language.md for the macro syntax.

    def load_path(self, path: str):
        """Non-interactive open (no dialogs).  Raises on failure."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_data(data)
        self.current_path = path
        self._update_title()
        self._reset_undo()

    def save_path(self, path: str):
        """Non-interactive save (no dialogs).  Raises on failure."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.serialize(), f, indent=2)
        self.current_path = path
        self._update_title()

    def clear_plan(self):
        """Non-interactive New (no confirm dialog)."""
        self.scene.clear()
        self.current_path = None
        SETTINGS.update(DEFAULT_SETTINGS)
        self._apply_canvas()
        self._reset_undo()

    def prepare_headless(self, w: int = 1280, h: int = 860):
        """Size the window/view and fit the canvas so scene<->viewport
        mapping is valid for synthesized mouse events when running
        offscreen.  Call once before driving a macro that uses CLICK/DRAG."""
        self.resize(w, h)
        self.view.resize(w, max(200, h - 120))
        margin = 5 * FOOT
        self.view.setSceneRect(canvas_rect().adjusted(
            -margin, -margin, margin, margin))
        self.view.fitInView(self.view.sceneRect(),
                            Qt.AspectRatioMode.KeepAspectRatio)
        QApplication.processEvents()

    def _content_rect(self) -> QRectF:
        """Bounding box of all walls/rooms/furnishings (or the canvas when
        empty), with a 1' margin — the region a snapshot should frame."""
        box = QRectF()
        for it in self.scene.items():
            if isinstance(it, (WallItem, RoomItem, FurnishingItem)):
                box = box.united(it.sceneBoundingRect())
        if box.isNull():
            box = canvas_rect()
        return box.adjusted(-FOOT, -FOOT, FOOT, FOOT)

    def export_canvas(self, path: str, rect: QRectF = None,
                      scale: float = 2.0) -> bool:
        """Render the scene (items only, no editor grid) to a PNG or SVG file,
        chosen by the path's extension.  `rect` defaults to the content box."""
        rect = QRectF(rect) if rect is not None else self._content_rect()
        if str(path).lower().endswith(".svg"):
            return self._export_svg(path, rect)
        return self._export_png(path, rect, scale)

    def _export_png(self, path, rect, scale) -> bool:
        img = QImage(max(1, int(rect.width() * scale)),
                     max(1, int(rect.height() * scale)),
                     QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.scene.render(p, QRectF(0, 0, img.width(), img.height()), rect)
        p.end()
        return bool(img.save(str(path)))

    def _export_svg(self, path, rect) -> bool:
        if QSvgGenerator is None:
            raise RuntimeError("QtSvg is unavailable -- cannot write SVG.")
        gen = QSvgGenerator()
        gen.setFileName(str(path))
        gen.setSize(QSize(max(1, int(rect.width())),
                          max(1, int(rect.height()))))
        gen.setViewBox(QRectF(0, 0, rect.width(), rect.height()))
        gen.setTitle("FloorPlanner canvas")
        gen.setDescription("Scene units are inches (1 unit = 1 inch). "
                           "Origin at the framed region's top-left.")
        p = QPainter(gen)
        self.scene.render(p, QRectF(0, 0, rect.width(), rect.height()), rect)
        p.end()
        return True

    def scene_summary(self) -> dict:
        """A machine-readable description of the layout for an AI driver:
        the full serialized model plus item counts."""
        data = self.serialize()
        data["counts"] = {
            "walls": len(data["walls"]),
            "rooms": len(data["rooms"]),
            "furnishings": len(data["furnishings"]),
        }
        return data

    def run_macro(self, text: str) -> dict:
        """Execute a macro string against this window; returns a result dict
        {ok, steps, log, errors}.  See MacroRunner for the token grammar."""
        return MacroRunner(self).run(text)


# ----------------------------------------------------------------------------
# Macro language (Part 1 of the headless tool — the in-app hook).
# ----------------------------------------------------------------------------
class MacroRunner:
    """Drives a MainWindow from a space/newline-delimited macro string so an
    external program (or an AI) can edit a plan headlessly.

    A macro is a flat list of whitespace-separated tokens; '#' starts a
    line comment and double-quoted tokens may contain spaces (room names).
    Positions are in SCENE INCHES (1 unit = 1 inch); a value may also be
    written in feet like 10' or 10'6".

    Tokens
      Tool select   S E I D W R        Select / Exterior-wall / Interior-wall /
                                       Door / Window / Room  (also: TOOL <name>;
                                       legacy digits 1-6 still work)
      Shortcuts     ^N ^Z ^Y ^X ^C ^V ^G ^A ^S
                                       new / undo / redo / cut / copy / paste /
                                       group / select-all / save-to-current.
                                       Prefix '+' adds Shift: ^+G ungroup,
                                       ^+Z redo.
      Arrow nudge   LEFT RIGHT UP DOWN          (^ prefix = fine 1" step)
      Keys          ESC DEL ENTER
      Mouse         CLICK x y | ^CLICK x y (Ctrl) | RCLICK x y | MOVE x y |
                    CLICK x1 y1 DRAG x2 y2  (press-drag-release; ^CLICK for a
                    Ctrl-drag) | DRAG x1 y1 x2 y2 | PRESS x y | RELEASE x y
      Place / edit  PLACE kind x y [rot] | WALL x1 y1 x2 y2 [ext|int] |
                    DOOR x y code | WINDOW x y code | ROOM name x y |
                    SELECT x y | SELECTALL | DESELECT | ROTATE deg |
                    MOVETO x y | DELETE | ZOOMFIT
      Context menu  PUP x y [UP DOWN LEFT RIGHT ENTER ESC HOME END TAB
                    BACKSPACE DELETE | TYPE "..."]  pop up the right-click
                    menu and drive it AND any dialog it opens; TYPE enters
                    text into the dialog's field (ENTER selects/accepts)
      Files / shot  OPEN path | SAVE path | NEW | SHOT path | WAIT

    `run()` returns {ok, steps, log, errors, counts}; a bad token is recorded
    in `errors` and skipped, so one mistake doesn't abort the whole macro.
    """

    # single-char tool codes (mnemonic): Select Exterior Interior Door
    # Window Room.  The legacy 1-6 digits are still accepted for old macros.
    _TOOL_CODES = {"S": TOOL_SELECT, "E": TOOL_WALL_EXT, "I": TOOL_WALL_INT,
                   "D": TOOL_DOOR, "W": TOOL_WINDOW, "R": TOOL_ROOM}
    _DIGIT_TOOLS = [TOOL_SELECT, TOOL_WALL_EXT, TOOL_WALL_INT,
                    TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM]
    _TOOL_NAMES = {"select": TOOL_SELECT, "extwall": TOOL_WALL_EXT,
                   "intwall": TOOL_WALL_INT, "door": TOOL_DOOR,
                   "window": TOOL_WINDOW, "room": TOOL_ROOM}
    _CARET_METHODS = {"Z": "undo", "Y": "redo", "+Z": "redo",
                      "X": "cut_selected", "C": "copy_selected",
                      "V": "paste_clipboard", "G": "group_selected",
                      "+G": "ungroup_selected", "N": "clear_plan"}
    _ARROWS = {"LEFT": (-1, 0), "RIGHT": (1, 0), "UP": (0, -1), "DOWN": (0, 1)}
    # keys that drive a popped-up menu / modal dialog after a PUP token
    _MENU_KEYS = {"UP": Qt.Key.Key_Up, "DOWN": Qt.Key.Key_Down,
                  "LEFT": Qt.Key.Key_Left, "RIGHT": Qt.Key.Key_Right,
                  "ENTER": Qt.Key.Key_Return, "ESC": Qt.Key.Key_Escape,
                  "HOME": Qt.Key.Key_Home, "END": Qt.Key.Key_End,
                  "TAB": Qt.Key.Key_Tab, "BACKSPACE": Qt.Key.Key_Backspace,
                  "DELETE": Qt.Key.Key_Delete}
    _MODAL_DELAY = 20          # ms between keys fed to a menu / modal dialog

    def __init__(self, win):
        self.win = win
        self.log = []
        self.errors = []
        self.steps = 0

    # -- public --------------------------------------------------------------
    def run(self, text: str) -> dict:
        toks = self._tokenize(text)
        i = 0
        while i < len(toks):
            raw = toks[i]
            i += 1
            try:
                i = self._dispatch(raw, toks, i)
                self.steps += 1
                self.log.append(f"ok  {raw}")
            except Exception as ex:                       # noqa: BLE001
                self.errors.append(f"{raw}: {ex}")
                self.log.append(f"ERR {raw}: {ex}")
            QApplication.processEvents()
        return {"ok": not self.errors, "steps": self.steps,
                "log": self.log, "errors": self.errors,
                "counts": self.win.scene_summary()["counts"]}

    # -- tokenizing / args ---------------------------------------------------
    @staticmethod
    def _tokenize(text: str):
        out = []
        for line in str(text).splitlines():
            line = line.split("#", 1)[0]
            for m in re.finditer(r'"([^"]*)"|(\S+)', line):
                out.append(m.group(1) if m.group(1) is not None else m.group(2))
        return out

    @staticmethod
    def _num(tok: str) -> float:
        return parse_feet(tok) if ("'" in tok or '"' in tok) else float(tok)

    def _take(self, toks, i, n):
        if i + n > len(toks):
            raise ValueError(f"expected {n} more argument(s)")
        return toks[i:i + n], i + n

    # -- dispatch ------------------------------------------------------------
    def _dispatch(self, raw, toks, i):
        cmd = raw.upper()
        if cmd == "CLICK":
            return self._do_click(toks, i, ctrl=False)
        if cmd == "^CLICK":
            return self._do_click(toks, i, ctrl=True)
        if raw.startswith("^"):
            return self._caret(raw[1:], i)
        if len(cmd) == 1 and cmd in self._TOOL_CODES:
            self.win.set_tool(self._TOOL_CODES[cmd])
            return i
        if len(raw) == 1 and raw in "123456":           # legacy digit tools
            self.win.set_tool(self._DIGIT_TOOLS[int(raw) - 1])
            return i
        if cmd in self._ARROWS:                  # coarse nudge of the selection
            dx, dy = self._ARROWS[cmd]
            self.win.nudge_selected(dx, dy, fine=False)
            return i
        if cmd == "ESC":
            self.win.view.cancel_temp()
            return i
        if cmd == "ENTER":
            self._key(Qt.Key.Key_Return, text="\r")
            return i
        if cmd in ("DEL", "DELETE"):
            self.win.delete_selected()
            return i

        handler = getattr(self, f"_cmd_{cmd.lower()}", None)
        if handler is None:
            raise ValueError("unknown command")
        return handler(toks, i)

    def _caret(self, key, i):
        key = key.upper()
        if key in self._ARROWS:                  # ^LEFT = fine (1") nudge
            dx, dy = self._ARROWS[key]
            self.win.nudge_selected(dx, dy, fine=True)
            return i
        if key == "S":
            if not self.win.current_path:
                raise ValueError("no current file — use 'SAVE path'")
            self.win.save_path(self.win.current_path)
            return i
        if key == "O":
            raise ValueError("use 'OPEN path' in a macro")
        if key == "A":
            self._select_all()
            return i
        meth = self._CARET_METHODS.get(key)
        if meth is None:
            raise ValueError("unknown shortcut")
        getattr(self.win, meth)()
        return i

    # -- input synthesis -----------------------------------------------------
    def _vpos(self, x, y):
        return self.win.view.mapFromScene(QPointF(x, y))

    def _mouse(self, etype, x, y, button, buttons,
               mods=Qt.KeyboardModifier.NoModifier):
        vp = self.win.view.viewport()
        pos = self._vpos(x, y)
        ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                         button, buttons, mods)
        QApplication.sendEvent(vp, ev)
        QApplication.processEvents()

    def _click(self, x, y, button=Qt.MouseButton.LeftButton,
               mods=Qt.KeyboardModifier.NoModifier):
        self._mouse(QEvent.Type.MouseButtonPress, x, y, button, button, mods)
        self._mouse(QEvent.Type.MouseButtonRelease, x, y, button,
                    Qt.MouseButton.NoButton, mods)

    def _drag(self, x1, y1, x2, y2, mods=Qt.KeyboardModifier.NoModifier):
        # press at the start, move (so the app sees a drag), release at the
        # end — the modifier rides every event so Ctrl-drags reproduce.
        left = Qt.MouseButton.LeftButton
        self._mouse(QEvent.Type.MouseButtonPress, x1, y1, left, left, mods)
        self._mouse(QEvent.Type.MouseMove, (x1 + x2) / 2, (y1 + y2) / 2,
                    Qt.MouseButton.NoButton, left, mods)
        self._mouse(QEvent.Type.MouseMove, x2, y2,
                    Qt.MouseButton.NoButton, left, mods)
        self._mouse(QEvent.Type.MouseButtonRelease, x2, y2, left,
                    Qt.MouseButton.NoButton, mods)

    def _key(self, key, mods=Qt.KeyboardModifier.NoModifier, text=""):
        view = self.win.view
        QApplication.sendEvent(
            view, QKeyEvent(QEvent.Type.KeyPress, key, mods, text))
        QApplication.sendEvent(
            view, QKeyEvent(QEvent.Type.KeyRelease, key, mods, text))
        QApplication.processEvents()

    def _select_all(self):
        self.win.scene.clearSelection()
        for it in self.win.scene.items():
            if isinstance(it, (WallItem, FurnishingItem, GroupItem)) \
                    and it.group() is None:
                it.setSelected(True)

    # -- command handlers (one per token) ------------------------------------
    def _cmd_tool(self, toks, i):
        (name,), i = self._take(toks, i, 1)
        self.win.set_tool(self._TOOL_NAMES[name.lower()])
        return i

    def _do_click(self, toks, i, ctrl):
        """CLICK / ^CLICK x y.  If the next token is DRAG, the click is the
        START of a drag (press at the click point, drag to the DRAG point,
        release) — so a Ctrl-drag reads ``^CLICK x1 y1 DRAG x2 y2``."""
        (x, y), i = self._take(toks, i, 2)
        x, y = self._num(x), self._num(y)
        mods = (Qt.KeyboardModifier.ControlModifier if ctrl
                else Qt.KeyboardModifier.NoModifier)
        if i < len(toks) and toks[i].upper() == "DRAG":
            (ex, ey), i = self._take(toks, i + 1, 2)   # DRAG end point only
            self._drag(x, y, self._num(ex), self._num(ey), mods)
        else:
            self._click(x, y, mods=mods)
        return i

    def _cmd_rclick(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._click(self._num(x), self._num(y), Qt.MouseButton.RightButton)
        return i

    def _cmd_move(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._mouse(QEvent.Type.MouseMove, self._num(x), self._num(y),
                    Qt.MouseButton.NoButton, Qt.MouseButton.NoButton)
        return i

    def _cmd_press(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._mouse(QEvent.Type.MouseButtonPress, self._num(x), self._num(y),
                    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        return i

    def _cmd_release(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._mouse(QEvent.Type.MouseButtonRelease, self._num(x), self._num(y),
                    Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton)
        return i

    def _cmd_drag(self, toks, i):
        # standalone 4-arg DRAG x1 y1 x2 y2 (a following DRAG after CLICK is
        # consumed by _do_click as a 2-arg continuation instead)
        (x1, y1, x2, y2), i = self._take(toks, i, 4)
        self._drag(*map(self._num, (x1, y1, x2, y2)))
        return i

    def _cmd_place(self, toks, i):
        kind = toks[i]
        (x, y), j = self._take(toks, i + 1, 2)
        i = j
        rot = 0.0
        if i < len(toks) and self._is_num(toks[i]):
            rot = self._num(toks[i])
            i += 1
        if furnishing_spec(kind) is None:
            raise ValueError(f"unknown furnishing '{kind}'")
        item = make_furnishing(kind, grid_snap(QPointF(self._num(x),
                                                       self._num(y))), rot)
        self.win.scene.addItem(item)
        return i

    def _cmd_wall(self, toks, i):
        (x1, y1, x2, y2), i = self._take(toks, i, 4)
        wtype = "exterior"
        if i < len(toks) and toks[i].lower() in (
                "ext", "exterior", "int", "interior"):
            wtype = "interior" if toks[i].lower().startswith("int") \
                else "exterior"
            i += 1
        w = WallItem(QPointF(self._num(x1), self._num(y1)),
                     QPointF(self._num(x2), self._num(y2)), wtype)
        self.win.scene.addItem(w)
        rebuild_all_walls(self.win.scene)
        return i

    def _cmd_door(self, toks, i):
        return self._opening(toks, i, "door")

    def _cmd_window(self, toks, i):
        return self._opening(toks, i, "window")

    def _opening(self, toks, i, kind):
        (x, y, code), i = self._take(toks, i, 3)
        pt = QPointF(self._num(x), self._num(y))
        wall = next((it for it in self.win.scene.items(pt)
                     if isinstance(it, WallItem)), None)
        if wall is None:
            raise ValueError(f"no wall at ({x}, {y})")
        w, _h = parse_wwhh(code)
        if w > wall.length():
            raise ValueError(f"{kind} too wide for the wall")
        s = min(max(round(wall.s_of(pt)), w / 2), wall.length() - w / 2)
        op = OpeningItem(wall, kind, code, s)
        wall.openings.append(op)
        rebuild_all_walls(self.win.scene)
        return i

    def _cmd_room(self, toks, i):
        (name, x, y), i = self._take(toks, i, 3)
        res = detect_room(self.win.scene, QPointF(self._num(x), self._num(y)))
        if res is None:
            raise ValueError("no enclosed area at that point")
        room = RoomItem(name, QPointF(self._num(x), self._num(y)),
                        res[0], res[1], corners=res[2])
        self.win.scene.addItem(room)
        bind_room_walls(self.win.scene, room)
        return i

    def _cmd_select(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        hits = list(self.win.scene.items(QPointF(self._num(x), self._num(y))))
        self.win.scene.clearSelection()
        # prefer an editable item (furnishing / wall / group) over a room,
        # whose label can sit on top of what you meant to grab
        pick = next((it for it in hits
                     if isinstance(it, (FurnishingItem, WallItem, GroupItem))),
                    None)
        if pick is None:
            pick = next((it for it in hits if it.flags()
                         & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable),
                        None)
        if pick is not None:
            pick.setSelected(True)
        return i

    def _cmd_selectall(self, toks, i):
        self._select_all()
        return i

    def _cmd_deselect(self, toks, i):
        self.win.scene.clearSelection()
        return i

    def _cmd_rotate(self, toks, i):
        (deg,), i = self._take(toks, i, 1)
        deg = self._num(deg)
        for it in self.win.scene.selectedItems():
            if isinstance(it, FurnishingItem):
                it.setRotation((it.rotation() + deg) % 360.0)
        return i

    def _cmd_moveto(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        x, y = self._num(x), self._num(y)
        sel = [it for it in self.win.scene.selectedItems()
               if isinstance(it, (FurnishingItem, GroupItem))]
        if not sel:
            raise ValueError("nothing selected to move")
        base = sel[0]
        dx, dy = x - base.pos().x(), y - base.pos().y()
        for it in sel:
            it.setPos(it.pos().x() + dx, it.pos().y() + dy)
            if isinstance(it, GroupItem):
                it.bake()
        return i

    def _cmd_zoomfit(self, toks, i):
        self.win.zoom_fit()
        QApplication.processEvents()
        return i

    def _cmd_pup(self, toks, i):
        """PUP x y [nav/edit/TYPE...] — pop up the context (right-click) menu
        at a scene point, then drive it (and any modal dialog it opens) with
        the tokens that follow:

          nav/edit keys  UP DOWN LEFT RIGHT ENTER ESC HOME END TAB
                         BACKSPACE DELETE
          text           TYPE "..."   (typed into the active line edit)

        e.g. resize a door:  ``PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER``
        The tokens are consumed here (the menu/dialog is only open during this
        step); ENTER selects/accepts, ESC cancels.  A bare PUP just opens and
        cancels the menu."""
        (x, y), i = self._take(toks, i, 2)
        x, y = self._num(x), self._num(y)
        actions = []
        while i < len(toks):
            t = toks[i].upper()
            if t == "TYPE":
                if i + 1 >= len(toks):
                    break
                actions.append(("text", toks[i + 1]))
                i += 2
            elif t in self._MENU_KEYS:
                actions.append(("key", self._MENU_KEYS[t]))
                i += 1
            else:
                break
        self._popup(x, y, actions)
        return i

    def _popup(self, x, y, actions):
        # arm the key pump to run inside the menu/dialog modal loop(s), then
        # raise the context menu (which blocks in exec() until it all closes)
        self._modal_queue = list(actions)
        QTimer.singleShot(0, self._modal_step)
        vp = self.win.view.viewport()
        pos = self.win.view.mapFromScene(QPointF(x, y))
        ev = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos,
                               vp.mapToGlobal(pos))
        QApplication.sendEvent(vp, ev)
        QApplication.processEvents()

    def _modal_step(self):
        """Feed one queued action to the currently-active menu/dialog.  Runs
        from a timer so it threads through nested exec() loops; reschedules
        BEFORE sending (a key may open another modal that blocks here)."""
        popup = QApplication.activePopupWidget()
        modal = QApplication.activeModalWidget()
        if popup is None and modal is None:
            self._modal_queue = []                 # interaction ended
            return
        if not self._modal_queue:
            (popup or modal).close()               # nothing left -> cancel
            return
        kind, val = self._modal_queue.pop(0)
        QTimer.singleShot(self._MODAL_DELAY, self._modal_step)
        # a popup MENU handles nav keys itself (it may not hold Qt focus, esp.
        # on Windows), so target it directly; a modal DIALOG routes keys to its
        # text field — find it directly since focus may not be set the instant
        # the dialog opens
        if popup is not None:
            target = popup
        else:
            target = (modal.findChild(QLineEdit)
                      or QApplication.focusWidget() or modal)
        if kind == "key":
            self._send_key(target, val)
        else:
            for ch in val:
                self._send_key(target, self._char_key(ch), ch)
        QApplication.processEvents()

    @staticmethod
    def _char_key(ch):
        seq = QKeySequence(ch)
        return Qt.Key(seq[0].key()) if seq.count() else Qt.Key.Key_unknown

    @staticmethod
    def _send_key(widget, key, text=""):
        for et in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            QApplication.sendEvent(widget, QKeyEvent(
                et, key, Qt.KeyboardModifier.NoModifier, text))

    def _cmd_type(self, toks, i):
        # stand-alone TYPE "text" -> type into whatever currently has focus
        (text,), i = self._take(toks, i, 1)
        target = QApplication.focusWidget()
        if target is not None:
            for ch in text:
                self._send_key(target, self._char_key(ch), ch)
        return i

    def _cmd_open(self, toks, i):
        (path,), i = self._take(toks, i, 1)
        self.win.load_path(path)
        return i

    def _cmd_save(self, toks, i):
        (path,), i = self._take(toks, i, 1)
        self.win.save_path(path)
        return i

    def _cmd_new(self, toks, i):
        self.win.clear_plan()
        return i

    def _cmd_shot(self, toks, i):
        (path,), i = self._take(toks, i, 1)
        if not self.win.export_canvas(path):
            raise ValueError("export failed")
        return i

    def _cmd_wait(self, toks, i):
        for _ in range(3):
            QApplication.processEvents()
        return i

    @staticmethod
    def _is_num(tok: str) -> bool:
        try:
            MacroRunner._num(tok)
            return True
        except ValueError:
            return False


# ----------------------------------------------------------------------------
# Macro recorder / debugger (non-modal): capture live interaction into macro
# text, then replay a selected portion or save it.  Opened from the toolbar
# Record button or the Macro menu.
# ----------------------------------------------------------------------------
class MacroRecorderDialog(QDialog):
    """A non-modal window that records mouse/keyboard/tool actions performed
    in the FloorPlanner window as macro tokens, lets you edit them, replay a
    selected portion, and Save As a .fpm file.

    Workflow: **Start**, switch to the plan window and interact (draw walls,
    drop furnishings, copy/paste, nudge…), come back and **Stop**.  Select
    any part of the recorded text and **Replay** to watch it run; **Save As…**
    to keep it.  The grammar is the same as `MacroRunner` / `fp_macro.py`.
    """

    MOVE_THRESHOLD = 4.0          # scene inches; a shorter drag becomes a CLICK
    _CARET_KEYS = {Qt.Key.Key_C: "C", Qt.Key.Key_V: "V", Qt.Key.Key_X: "X",
                   Qt.Key.Key_Z: "Z", Qt.Key.Key_Y: "Y", Qt.Key.Key_G: "G",
                   Qt.Key.Key_A: "A", Qt.Key.Key_N: "N", Qt.Key.Key_S: "S"}
    _ARROW_KEYS = {Qt.Key.Key_Left: "LEFT", Qt.Key.Key_Right: "RIGHT",
                   Qt.Key.Key_Up: "UP", Qt.Key.Key_Down: "DOWN"}
    _TOOL_CODES = {TOOL_SELECT: "S", TOOL_WALL_EXT: "E", TOOL_WALL_INT: "I",
                   TOOL_DOOR: "D", TOOL_WINDOW: "W", TOOL_ROOM: "R"}

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Macro Recorder / Debug")
        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self._recording = False
        self._paused = False
        self._press_scene = None
        self._press_moved = False
        self._press_tool = TOOL_SELECT
        self._press_ctrl = False
        self._type_buffer = ""           # printable run while a modal is open
        self._modal_line = False         # a PUP + its menu/dialog keys, 1 line
        self._last_key_ev = None         # de-dupe doubled key deliveries
        self._last_key_sig = None        # (timestamp, key, mods) of last press
        self._replay_lines = []
        self._replay_idx = 0

        self.edit = QPlainTextEdit()
        self.edit.setFont(QFont("DejaVu Sans Mono", 10))
        self.edit.setPlaceholderText(
            "Recorded macro tokens appear here.  Edit freely; select a "
            "portion and click Replay to run just that part.")

        self.nl_check = QCheckBox("New line after each mouse action")
        self.nl_check.setChecked(True)
        self.status_lbl = QLabel("Idle.")

        self.b_start = QPushButton("Start")
        self.b_pause = QPushButton("Pause")
        self.b_stop = QPushButton("Stop")
        self.b_replay = QPushButton("Replay")
        self.b_saveas = QPushButton("Save As…")
        self.b_cancel = QPushButton("Cancel")
        self.b_start.clicked.connect(self.start)
        self.b_pause.clicked.connect(self.toggle_pause)
        self.b_stop.clicked.connect(self.stop)
        self.b_replay.clicked.connect(self.replay)
        self.b_saveas.clicked.connect(self.save_as)
        self.b_cancel.clicked.connect(self.cancel)
        self.edit.selectionChanged.connect(self._sync_buttons)
        self.edit.textChanged.connect(self._sync_buttons)

        row = QHBoxLayout()
        for b in (self.b_start, self.b_pause, self.b_stop, self.b_replay,
                  self.b_saveas, self.b_cancel):
            row.addWidget(b)
        lay = QVBoxLayout(self)
        lay.addWidget(self.edit)
        lay.addWidget(self.nl_check)
        lay.addLayout(row)
        lay.addWidget(self.status_lbl)
        self.resize(600, 440)

        self._replay_timer = QTimer(self)
        self._replay_timer.timeout.connect(self._replay_step)
        self._sync_buttons()

    # -- button state --------------------------------------------------------
    def _sync_buttons(self):
        rec, replaying = self._recording, self._replay_timer.isActive()
        self.b_start.setEnabled(not rec and not replaying)
        self.b_stop.setEnabled(rec)
        self.b_pause.setEnabled(rec)
        self.b_pause.setText("Resume" if self._paused else "Pause")
        self.b_replay.setEnabled(self.edit.textCursor().hasSelection()
                                 and not rec and not replaying)
        self.b_saveas.setEnabled(bool(self.edit.toPlainText().strip()))

    # -- record --------------------------------------------------------------
    def start(self):
        if self._recording:
            return
        self._recording = True
        self._paused = False
        self._press_scene = None
        self._last_key_ev = None
        self._last_key_sig = None
        self.win._recorder = self
        app = QApplication.instance()
        app.removeEventFilter(self)        # ensure exactly one installation
        app.installEventFilter(self)
        self.status_lbl.setText(
            "Recording…  Interact with the FloorPlanner window, then Stop.")
        self._sync_buttons()
        self.win.raise_()
        self.win.activateWindow()

    def stop(self):
        if not self._recording:
            return
        self._end_modal_line()             # close any open PUP line
        QApplication.instance().removeEventFilter(self)
        self.win._recorder = None
        self._recording = False
        self._paused = False
        self._press_scene = None
        self.status_lbl.setText(
            "Stopped.  Select macro text and Replay, or Save As….")
        self.raise_()
        self.activateWindow()
        self._sync_buttons()

    def toggle_pause(self):
        if not self._recording:
            return
        self._paused = not self._paused
        self.status_lbl.setText("Paused." if self._paused else "Recording…")
        self._sync_buttons()

    def cancel(self):
        self.stop()
        self._replay_timer.stop()
        self.close()

    def closeEvent(self, e):
        self.stop()
        self._replay_timer.stop()
        super().closeEvent(e)

    # -- replay --------------------------------------------------------------
    def replay(self):
        cur = self.edit.textCursor()
        text = (cur.selection().toPlainText() if cur.hasSelection()
                else self.edit.toPlainText())
        # step one recorded line at a time so the canvas updates visibly
        self._replay_lines = [ln for ln in text.splitlines() if ln.strip()]
        self._replay_idx = 0
        if not self._replay_lines:
            return
        self.status_lbl.setText("Replaying…")
        self.win.raise_()
        self._replay_timer.start(180)
        self._sync_buttons()

    def _replay_step(self):
        if self._replay_idx >= len(self._replay_lines):
            self._replay_timer.stop()
            self.status_lbl.setText("Replay complete.")
            self._sync_buttons()
            return
        line = self._replay_lines[self._replay_idx]
        self._replay_idx += 1
        res = self.win.run_macro(line)
        if res["errors"]:
            self.status_lbl.setText("Replay: " + "; ".join(res["errors"][:2]))

    # -- save ----------------------------------------------------------------
    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save macro", str(designs_dir() / "macro.fpm"),
            "Macro files (*.fpm *.txt);;All files (*)")
        if not path:
            return
        try:
            self._write_macro(path)
        except OSError as ex:
            QMessageBox.critical(self, "Save failed", str(ex))

    def _write_macro(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.edit.toPlainText())
        self.status_lbl.setText(f"Saved {path}")

    # -- hooks called by the instrumented app --------------------------------
    def on_tool(self, tool):
        if self._active():
            self._end_modal_line()
            code = self._TOOL_CODES.get(tool)
            if code:
                self._append(code)

    def on_place(self, kind, scene_pt):
        if self._active():
            self._end_modal_line()
            self._append(f"PLACE {kind} {round(scene_pt.x())} "
                         f"{round(scene_pt.y())}",
                         newline=self.nl_check.isChecked())

    def on_popup(self, scene_pt):
        # PUP keeps the menu's nav/text keys on the SAME line; the line is
        # ended (newline) when the modal closes and the next action arrives
        if self._active():
            self._end_modal_line()
            self._append(f"PUP {round(scene_pt.x())} {round(scene_pt.y())}")
            self._modal_line = True

    def on_opening(self, kind, scene_pt, code):
        # door/window size came from a dialog, not keystrokes — capture the
        # value into a self-contained DOOR/WINDOW token so replay needs no
        # dialog (the raw click for this tool is suppressed in _capture).
        if self._active():
            self._end_modal_line()
            tok = "DOOR" if kind == "door" else "WINDOW"
            self._append(f"{tok} {round(scene_pt.x())} {round(scene_pt.y())} "
                         f"{code}", newline=self.nl_check.isChecked())

    def on_room(self, name, scene_pt):
        # room name came from a dialog — capture it into a ROOM token.
        if self._active():
            self._end_modal_line()
            tok = f'"{name}"' if " " in name else name
            self._append(f"ROOM {tok} {round(scene_pt.x())} "
                         f"{round(scene_pt.y())}",
                         newline=self.nl_check.isChecked())

    # -- live capture (application event filter) -----------------------------
    def _active(self) -> bool:
        return self._recording and not self._paused

    def eventFilter(self, obj, ev):
        if self._active():
            try:
                self._capture(obj, ev)
            except Exception:                          # noqa: BLE001
                pass                                   # capture never breaks UI
        return False                                   # never consume events

    def _capture(self, obj, ev):
        et = ev.type()
        if et == QEvent.Type.KeyRelease:
            self._last_key_ev = None       # a press/release pair completed
            self._last_key_sig = None
            return
        if obj is self.win.view.viewport():
            if et == QEvent.Type.MouseButtonPress and \
                    ev.button() == Qt.MouseButton.LeftButton:
                self._press_scene = self.win.view.mapToScene(
                    ev.position().toPoint())
                self._press_moved = False
                self._press_tool = self.win.tool       # tool at press time
                self._press_ctrl = bool(ev.modifiers()
                                        & Qt.KeyboardModifier.ControlModifier)
            elif et == QEvent.Type.MouseMove and self._press_scene is not None \
                    and (ev.buttons() & Qt.MouseButton.LeftButton):
                self._press_moved = True
            elif et == QEvent.Type.MouseButtonRelease and \
                    ev.button() == Qt.MouseButton.LeftButton and \
                    self._press_scene is not None:
                end = self.win.view.mapToScene(ev.position().toPoint())
                # door/window/room clicks are recorded by their dedicated
                # hooks (with the dialog value), so skip the raw click here
                if self._press_tool not in (TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM):
                    self._emit_mouse(self._press_scene, end,
                                     self._press_moved, self._press_ctrl)
                self._press_scene = None
            elif et == QEvent.Type.ContextMenu:
                # a right-click context menu -> PUP x y (nav keys captured
                # below while the menu is open)
                sp = self.win.view.mapToScene(ev.pos())
                self.on_popup(sp)
        elif et == QEvent.Type.KeyPress:
            # de-dupe: one physical key press can reach this filter more than
            # once — Qt propagates an unaccepted key up the parent chain, and a
            # popup/dialog re-dispatches it.  Skip a repeat of the same event
            # object, or (for real events) the same (timestamp, key, mods); a
            # KeyRelease resets this so genuine repeats still record.
            ts = ev.timestamp()
            sig = (ts, ev.key(), ev.modifiers())
            if ev is self._last_key_ev or (ts and sig == self._last_key_sig):
                return
            self._last_key_ev = ev
            self._last_key_sig = sig
            in_modal = (QApplication.activePopupWidget() is not None
                        or QApplication.activeModalWidget() is not None)
            # only capture modal keystrokes for a PUP-opened menu/dialog;
            # tool-driven dialogs (door/window size, room name) already record
            # their value via on_opening/on_room, so don't double-capture them
            if in_modal and self._modal_line:
                self._emit_modal_key(ev)
            elif not in_modal and self._belongs_to_main(obj):
                self._emit_key(ev)

    def _emit_mouse(self, p1, p2, moved, ctrl):
        self._end_modal_line()
        # a click is "[^]CLICK x y"; a drag is the click START plus a DRAG end
        # point on the same line: "[^]CLICK x1 y1 DRAG x2 y2".  The '^' marks
        # the Ctrl modifier (e.g. Ctrl-drag a room name, or Ctrl+click toggle).
        x1, y1, x2, y2 = (round(p1.x()), round(p1.y()),
                          round(p2.x()), round(p2.y()))
        pre = "^CLICK" if ctrl else "CLICK"
        if moved and QLineF(p1, p2).length() >= self.MOVE_THRESHOLD:
            tok = f"{pre} {x1} {y1} DRAG {x2} {y2}"
        else:
            tok = f"{pre} {x1} {y1}"
        self._append(tok, newline=self.nl_check.isChecked())

    _MENU_KEY_TOKENS = {Qt.Key.Key_Up: "UP", Qt.Key.Key_Down: "DOWN",
                        Qt.Key.Key_Left: "LEFT", Qt.Key.Key_Right: "RIGHT",
                        Qt.Key.Key_Return: "ENTER", Qt.Key.Key_Enter: "ENTER",
                        Qt.Key.Key_Escape: "ESC", Qt.Key.Key_Home: "HOME",
                        Qt.Key.Key_End: "END", Qt.Key.Key_Tab: "TAB",
                        Qt.Key.Key_Backspace: "BACKSPACE",
                        Qt.Key.Key_Delete: "DELETE"}

    def _emit_modal_key(self, ev):
        # keystrokes while a PUP menu / modal dialog is open: named keys pass
        # through (no newline — stay on the PUP line); printable text is
        # buffered into a TYPE "..." run.
        tok = self._MENU_KEY_TOKENS.get(ev.key())
        if tok:
            self._flush_type()
            self._append(tok)
            return
        text = ev.text()
        if text and text.isprintable():
            self._type_buffer += text

    def _flush_type(self):
        if self._type_buffer:
            self._append(f'TYPE "{self._type_buffer}"')
            self._type_buffer = ""

    def _newline(self):
        if self.edit.toPlainText() and not self.edit.toPlainText().endswith("\n"):
            cur = self.edit.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End)
            cur.insertText("\n")
            self.edit.setTextCursor(cur)
            self.edit.ensureCursorVisible()

    def _end_modal_line(self):
        # close out a PUP line (flush any typed text, drop to a new line)
        if self._modal_line:
            self._flush_type()
            self._newline()
            self._modal_line = False

    def _emit_key(self, ev):
        self._end_modal_line()             # a modal closed -> end its line
        key, mods = ev.key(), ev.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        if key in self._ARROW_KEYS:
            self._append(("^" if ctrl else "") + self._ARROW_KEYS[key])
        elif key == Qt.Key.Key_Escape:
            self._append("ESC")
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._append("DEL")
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._append("ENTER")
        elif ctrl and key in self._CARET_KEYS:
            self._append("^" + ("+" if shift else "") + self._CARET_KEYS[key])

    def _belongs_to_main(self, obj) -> bool:
        """True if `obj` is the plan window or one of its children (not this
        recorder dialog), so we record canvas keystrokes but not text edits."""
        w = obj
        while w is not None:
            if w is self:
                return False
            if w is self.win:
                return True
            w = w.parent() if hasattr(w, "parent") else None
        return False

    def _append(self, token, newline=False):
        cur = self.edit.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        text = self.edit.toPlainText()
        sep = "" if (not text or text.endswith(("\n", " "))) else " "
        cur.insertText(sep + token + ("\n" if newline else ""))
        self.edit.setTextCursor(cur)
        self.edit.ensureCursorVisible()


def main():
    # point Qt's own font lookup at the bundled fonts as well: platforms
    # without system font discovery (e.g. offscreen) read this during
    # QApplication startup, which silences the missing-font-dir warning
    if FONT_DIR.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(FONT_DIR))
    app = QApplication(sys.argv)
    # set only the application name (no org) so the standard AppConfig path
    # is .../FloorPlanner rather than .../FloorPlanner/FloorPlanner
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    load_fonts()
    app.setFont(QFont(FONT_FAMILY, 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
