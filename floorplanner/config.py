"""App-wide constants, plan settings, and OS path / font / icon helpers.

This is the home of the shared mutable ``SETTINGS`` dict (read across the whole
app) and the immutable constants.  Everything imports these from here so the
settings object is a single shared instance, never duplicated.
"""
import sys
from pathlib import Path

from PyQt6.QtCore import QRectF, QSettings, QStandardPaths
from PyQt6.QtGui import QColor, QFontDatabase, QIcon

from floorplanner.model import DEFAULT_FLOOR  # schema constant (single source)

__all__ = [
    "FOOT", "EXTERIOR_T", "INTERIOR_T", "GRID_MINOR", "GRID_MAJOR",
    "SNAP_STEP", "WALL_SNAP_DEFAULT", "WALL_SNAP_CHOICES", "ROTATE_SNAP_DEFAULT",
    "CANVAS_W_DEFAULT", "CANVAS_H_DEFAULT", "MAX_CANVAS_IN",
    "DEFAULT_SETTINGS", "SETTINGS", "JOIN_TOL", "MIN_WALL_LEN",
    "WALL_PROJECT_STICK", "WALL_PROJECT_NEAR", "ROOM_SIG_MARGIN",
    "WALL_Z", "OPENING_Z", "canvas_rect",
    "TOOL_SELECT", "TOOL_WALL_EXT", "TOOL_WALL_INT", "TOOL_DOOR",
    "TOOL_WINDOW", "TOOL_ROOM", "DOOR_TYPES", "GARAGE_DEFAULTS", "ROOM_CELL",
    "ROOM_TYPES", "CEILING_TYPES", "FLOOR_FINISHES", "WALL_FINISHES",
    "HVAC_TYPES", "DEFAULT_ROOM_PROPS", "APP_NAME", "APP_VERSION", "APP_URL",
    "config_dir", "settings_file", "designs_dir", "app_settings",
    "FONT_DIR", "FONT_FAMILY", "load_fonts",
    "ICON_DIR", "FURN_DIR", "FURN_MIME", "tool_icon",
    "DEFAULT_FLOOR", "FLOOR_GHOST", "active_floor", "set_floor_state",
    "floor_display_mode", "apply_floor_visibility",
]

# repo root (this file lives in floorplanner/, assets/ sits one level up)
_ROOT = Path(__file__).resolve().parent.parent

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
    "auto_coalesce": True,            # fuse overlapping same-type walls on edit
}
SETTINGS = dict(DEFAULT_SETTINGS)
JOIN_TOL = 9.0            # endpoints within 9" join together
MIN_WALL_LEN = 6.0
WALL_PROJECT_STICK = 9.0  # stretch sticks within 9" of an orthogonal wall line
WALL_PROJECT_NEAR = 48.0  # ...only when that wall actually passes within 4'
ROOM_SIG_MARGIN = 18.0    # walls within 18" of a room's bbox can affect it
# default stacking: furnishing (3) < translucent room fill/label (4) < wall < opening
WALL_Z = 5.0              # walls sit above the room fill so they stay crisp
OPENING_Z = 6.0           # doors/windows sit above their wall


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

APP_NAME = "FloorPlanner"
APP_VERSION = "1.2"
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
FONT_DIR = _ROOT / "assets" / "fonts"
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
ICON_DIR = _ROOT / "assets" / "icons"
FURN_DIR = _ROOT / "assets" / "furnishings"
FURN_MIME = "application/x-floorplanner-furnishing"


def tool_icon(name: str) -> QIcon:
    p = ICON_DIR / f"{name}.svg"
    return QIcon(str(p)) if p.is_file() else QIcon()


# ----------------------------------------------------------------------------
# Floors — runtime view state read by paint() and the geometry hot paths
# without a window handle.  Authoritative roster lives on MainWindow
# (self.floors / self.active_floor); _sync_floor_state mirrors it here.
#
# Backed by a MUTABLE dict + accessor FUNCTIONS (not bare module globals): the
# scene modules pull these via star import, so a rebindable string global would
# be a stale snapshot in each module.  Functions reading one shared dict — like
# SETTINGS — stay live across the whole package.
# ----------------------------------------------------------------------------
FLOOR_GHOST = QColor(176, 176, 176)     # flat gray for non-active floors

_FLOOR_STATE = {
    "active": DEFAULT_FLOOR,             # the one editable floor
    "reference": set(),                  # floors shown as a gray backdrop
    "show_others": False,                # ghost the rest in gray (else hidden)
}


def active_floor() -> str:
    return _FLOOR_STATE["active"]


def set_floor_state(active=None, reference=None, show_others=None):
    """Update the runtime floor cache (called by MainWindow._sync_floor_state)."""
    if active is not None:
        _FLOOR_STATE["active"] = active
    if reference is not None:
        _FLOOR_STATE["reference"] = set(reference)
    if show_others is not None:
        _FLOOR_STATE["show_others"] = bool(show_others)


def floor_display_mode(floor) -> str:
    """'active' | 'reference' | 'ghost' | 'hidden' for a floor name."""
    if floor == _FLOOR_STATE["active"]:
        return "active"
    if floor in _FLOOR_STATE["reference"]:
        return "reference"
    return "ghost" if _FLOOR_STATE["show_others"] else "hidden"


def apply_floor_visibility(scene):
    """Show/enable top-level items by their floor's display mode: only the
    active floor is editable; reference floors are visible but disabled;
    others are hidden (or ghosted when 'show others' is on).  Items without a
    `floor` (e.g. the PNG backdrop) are left untouched."""
    if scene is None:
        return
    for it in scene.items():
        if it.parentItem() is not None:          # top-level items only
            continue
        floor = getattr(it, "floor", None)
        if floor is None:
            continue
        mode = floor_display_mode(floor)
        it.setVisible(mode != "hidden")
        it.setEnabled(mode == "active")
