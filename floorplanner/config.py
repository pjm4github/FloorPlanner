"""App-wide constants, plan settings, and OS path / font / icon helpers.

This is the home of the shared mutable ``SETTINGS`` dict (read across the whole
app) and the immutable constants.  Everything imports these from here so the
settings object is a single shared instance, never duplicated.
"""
import hashlib
import json
import os
import sys
import warnings
from pathlib import Path

from PyQt6.QtCore import QRectF, QStandardPaths
from PyQt6.QtGui import QColor, QFontDatabase, QIcon

from floorplanner.model import DEFAULT_FLOOR  # schema constant (single source)

__all__ = [
    "FOOT", "EXTERIOR_T", "INTERIOR_T", "GRID_MINOR", "GRID_MAJOR",
    "SNAP_STEP", "WALL_SNAP_DEFAULT", "WALL_SNAP_CHOICES", "ROTATE_SNAP_DEFAULT",
    "CANVAS_W_DEFAULT", "CANVAS_H_DEFAULT", "MAX_CANVAS_IN",
    "DEFAULT_SETTINGS", "SETTINGS", "editing_enabled", "coerce_setting",
    "SETTINGS_VERSION",
    "JOIN_TOL",
    "MIN_WALL_LEN",
    "WALL_PROJECT_STICK", "WALL_PROJECT_NEAR", "ROOM_SIG_MARGIN",
    "WALL_Z", "CLICK_SLOP", "OPENING_Z", "canvas_rect",
    "TOOL_SELECT", "TOOL_WALL_EXT", "TOOL_WALL_INT", "TOOL_DOOR",
    "TOOL_WINDOW", "TOOL_ROOM", "TOOL_ROOF_RIDGE",
    "DOOR_TYPES", "GARAGE_DEFAULTS", "ROOM_CELL",
    "ROOM_TYPES", "CEILING_TYPES", "FLOOR_FINISHES", "WALL_FINISHES",
    "HVAC_TYPES", "DEFAULT_ROOM_PROPS", "APP_NAME", "APP_VERSION", "APP_URL",
    "CODE_VERSION", "code_version",
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
    # editing modes (schema $defs.editing_modes, P4.3) -- persisted in the
    # file's settings.editing block; read through editing_enabled() below
    "auto_coalesce": True,            # fuse overlapping same-type walls on edit
    "shuffle": False,                 # shuffle mode: nothing joins automatically
    "auto_weld": True,                # snap a drawn end onto what it lands near
    "auto_bind": True,                # bind room edges to coincident walls
    #                                   (policy flag; no automatic site today --
    #                                   the P4.3 census, stated not invented)
    # R2c (0145-ruling.md sec2): Show roof / Edit roof, the Roof menu's own
    # pair, invariant Edit implies Show. True/True so every roof R1/R2/R2b
    # already wrote stays visible and editable without a migration.
    "show_roofs": True,
    "edit_roofs": True,
}
SETTINGS = dict(DEFAULT_SETTINGS)


def editing_enabled(flag: str) -> bool:
    """Effective editing-mode flag (P4.3). ``shuffle: true`` implies the three
    ``auto_*`` joining passes are all off -- the schema's own contract -- so
    every gate asks this one question instead of re-deriving the implication."""
    if SETTINGS.get("shuffle", False):
        return False
    return bool(SETTINGS.get(flag, True))


def coerce_setting(key: str, val, default):
    """Coerce a raw settings value (from a loaded document, or any other
    untyped source) to the TYPE `DEFAULT_SETTINGS[key]` declares, rather than
    blindly forcing `float` -- 0073-ruling.md sec2: both settings loaders did
    exactly that, so a string setting (a title, an author) was silently
    replaced by its own default on every load, before anyone could see it.

    One function, used by every loader (planio.py, design/bridge.py) rather
    than duplicated -- "two implementations of a precedence chain is how the
    thickness tables happened" (0073 sec6). A value that cannot be coerced is
    REPORTED via a warning, not swallowed.

    THE BOOL BRANCH PARSES TEXT EXPLICITLY (0077-ruling.md sec2): a bare
    `bool(val)` on a string is `bool("false") is True` -- the exact
    string-typed hazard this whole thread exists to eliminate, alive again
    in the one function whose job is "do not blindly coerce"."""
    if isinstance(default, bool):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            low = val.strip().lower()
            if low in ("true", "1"):
                return True
            if low in ("false", "0"):
                return False
            warnings.warn(
                f"setting {key!r}: {val!r} is not a recognised boolean "
                f"('true'/'false'/'1'/'0'), using the default {default!r}",
                stacklevel=2)
            return default
        return bool(val)          # a real int/float: unambiguous
    if isinstance(default, str):
        return str(val)
    if isinstance(default, int):
        try:
            return int(val)
        except (TypeError, ValueError):
            warnings.warn(
                f"setting {key!r}: {val!r} is not an int, using the "
                f"default {default!r}", stacklevel=2)
            return default
    try:
        return float(val)
    except (TypeError, ValueError):
        warnings.warn(
            f"setting {key!r}: {val!r} is not a number, using the "
            f"default {default!r}", stacklevel=2)
        return default
JOIN_TOL = 9.0            # endpoints within 9" join together
MIN_WALL_LEN = 6.0
WALL_PROJECT_STICK = 9.0  # stretch sticks within 9" of an orthogonal wall line
WALL_PROJECT_NEAR = 48.0  # ...only when that wall actually passes within 4'
ROOM_SIG_MARGIN = 18.0    # walls within 18" of a room's bbox can affect it
# default stacking: furnishing (3) < translucent room fill/label (4) < wall < opening
WALL_Z = 5.0              # walls sit above the room fill so they stay crisp
# A press that moved no further than this is a CLICK, not a drag (D53).
# In VIEWPORT pixels, so it is a hand steadiness threshold and does not
# scale with zoom -- a real click jitters by a pixel or two.
CLICK_SLOP = 3
OPENING_Z = 6.0           # doors/windows sit above their wall


def canvas_rect() -> QRectF:
    """The canvas outline, sized by the plan settings (default 100'x70')."""
    return QRectF(0.0, 0.0, SETTINGS["canvas_w_in"], SETTINGS["canvas_h_in"])


(TOOL_SELECT, TOOL_WALL_EXT, TOOL_WALL_INT, TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM,
 TOOL_ROOF_RIDGE) = range(7)

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


def _read_code_version() -> str:
    """`vAPP_VERSION · <branch> @ <sha7>` for the checkout this process was
    launched from, read straight off `.git` (no subprocess). Falls back to
    the bare version outside a git checkout."""
    v = f"v{APP_VERSION}"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(root, ".git", "HEAD"), encoding="utf-8") as fh:
            head = fh.read().strip()
    except OSError:
        return v
    if not head.startswith("ref: "):
        return f"{v} · detached @ {head[:7]}"
    ref = head[5:].strip()
    branch = ref.rsplit("/", 1)[-1]
    sha = ""
    try:
        with open(os.path.join(root, ".git", *ref.split("/")),
                  encoding="utf-8") as fh:
            sha = fh.read().strip()[:7]
    except OSError:
        try:
            with open(os.path.join(root, ".git", "packed-refs"),
                      encoding="utf-8") as fh:
                for line in fh:
                    if line.strip().endswith(ref):
                        sha = line.split(None, 1)[0][:7]
                        break
        except OSError:
            pass
    return f"{v} · {branch}" + (f" @ {sha}" if sha else "")


# Captured ONCE, at import -- i.e. at launch. A running Python process keeps
# the code it imported, so the truthful answer to "which code is this window
# running?" is what .git said when the process started, not what is on disk
# now (the P4.2 mini-gate's stale-process lesson: a fix landed on disk while
# an app launched earlier kept reproducing the old bug).
CODE_VERSION = _read_code_version()


def code_version() -> str:
    """The launch-time code identity: version, branch and commit."""
    return CODE_VERSION


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
    """The app-wide settings file (JSON) holding cross-session preferences
    such as a remembered AI API key. Migrated at most once from a QSettings
    INI of the same name -- see `_ensure_settings_file` (0075-ruling.md)."""
    return config_dir() / "floorplanner.json"


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


def _legacy_ini_file() -> Path:
    """Where the app settings lived before 0075-ruling.md (a QSettings INI)
    -- read only by the one-shot migration below, never written again."""
    return config_dir() / "floorplanner.ini"


def _read_legacy_ini_value(path: Path, key: str):
    """One key out of the pre-migration QSettings INI, without QSettings --
    0075-ruling.md sec2 drops the Qt dependency from the app-settings store
    entirely. QSettings' IniFormat writes an ungrouped key under `[General]`,
    which is the one shape this reads; anything else is treated as absent
    (a partial/foreign INI is not this migration's problem to solve)."""
    import configparser
    cp = configparser.ConfigParser()
    try:
        if not cp.read(path, encoding="utf-8"):
            return None
    except configparser.Error:
        return None
    if cp.has_option("General", key):
        return cp.get("General", key)
    return None


#: Bumped whenever `DEFAULT_SETTINGS` changes shape (a key added, removed,
#: renamed, or re-defaulted) -- `0078-ruling.md` sec2. Full materialisation
#: (below) means an existing user's file has NO absent keys for a new
#: default to fall through to, so this version marker plus
#: `_SETTINGS_MIGRATIONS` is the only thing that can still reach them.
SETTINGS_VERSION = 2


def _migrate_v1_to_v2(data: dict) -> dict:
    """R2c (0145-ruling.md sec2): `show_roofs`/`edit_roofs` added to
    `DEFAULT_SETTINGS`. A v1 app-settings file predates them and, being
    fully materialised, has no absent-key fallback to reach their
    defaults through (the exact gap `SETTINGS_VERSION` exists to close) --
    `setdefault`, not assignment, in case a v1 file somehow already
    carries either key (hand-edited, or a future migration re-run)."""
    data.setdefault("show_roofs", True)
    data.setdefault("edit_roofs", True)
    return data


#: Ordered migration steps: `(from_version, fn)`, `fn(data: dict) -> dict`,
#: each upgrading a file from `from_version` to `from_version + 1`.
#: `_migrate_settings_data` applies every step in order and bumps the
#: marker. The mechanism was tested
#: (`test_changing_DEFAULT_SETTINGS_requires_a_version_bump`) before it was
#: ever needed, per this project's own "generation, or a gate that fails"
#: rule: a table that only gets written the day it is first needed is a
#: table nobody remembered to write. `(1, _migrate_v1_to_v2)` is that
#: table's first real row.
_SETTINGS_MIGRATIONS = [(1, _migrate_v1_to_v2)]


def _default_settings_fingerprint() -> str:
    """A hash of `DEFAULT_SETTINGS`' keys, TYPES and VALUES -- what
    `test_changing_DEFAULT_SETTINGS_requires_a_version_bump` pins against
    `SETTINGS_VERSION`. Editing a default without bumping the version
    reddens the gate; the fix is to bump `SETTINGS_VERSION`, add the
    migration row, and update the pin -- mechanical, not remembered
    (`0078-ruling.md` sec2)."""
    items = sorted((k, type(v).__name__, repr(v))
                   for k, v in DEFAULT_SETTINGS.items())
    return hashlib.sha256(repr(items).encode("utf-8")).hexdigest()[:16]


def _migrate_settings_data(data: dict) -> dict:
    """Apply every step in `_SETTINGS_MIGRATIONS` between `data`'s own
    `version` and `SETTINGS_VERSION`, in order; a file already current
    (the common case) is returned with only its `version` normalised, so
    this is cheap to call on every load, not just the first one. A key
    the file does not carry (an old file, or a migration step that does
    not touch it) still falls through to `DEFAULT_SETTINGS` at read
    time -- this function upgrades what is THERE, it does not fill gaps."""
    version = data.get("version", 0)
    for from_version, fn in _SETTINGS_MIGRATIONS:
        if version == from_version:
            data = fn(data)
            version = from_version + 1
    data["version"] = SETTINGS_VERSION
    return data


def _materialize_settings(migrated_key=None) -> dict:
    """Every `DEFAULT_SETTINGS` key at its default value, plus `version` --
    Patrick's own words: *"if it doesn't exist then it creates a default
    version"* (`0078-ruling.md` sec1). `anthropic_api_key` is added ONLY
    when migration found a real one -- materialisation never mints a slot
    for a secret (`0075-ruling.md` sec3 clause 2)."""
    data = {"version": SETTINGS_VERSION}
    data.update(DEFAULT_SETTINGS)
    if migrated_key:
        data["anthropic_api_key"] = migrated_key
    return data


def _ensure_settings_file() -> Path:
    """Create `settings_file()` if it does not exist yet, or QUARANTINE it
    and start fresh if it exists but cannot be parsed (`0077-ruling.md`
    sec6: a truncated write -- power loss, full disk -- must not be
    silently emptied the moment the next save runs; `catalog.py`'s own
    `except Exception: return ""` guarantees nobody would otherwise hear
    about it).

    MIGRATES the legacy INI's `anthropic_api_key` ONLY when the JSON is
    genuinely absent -- never on a quarantine-and-recreate. A JSON file
    existed here once, so the INI stays dead exactly as ordinary
    idempotence already requires (`0075-ruling.md` sec3): re-consulting
    the INI on every recovery would let a corrupted file resurrect an
    intentionally-cleared key, which is the loophole that rule exists to
    close, reached by a different road."""
    path = settings_file()
    genuinely_fresh = not path.exists()
    if not genuinely_fresh:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            bad = path.with_name(path.name + ".bad")
            try:
                path.replace(bad)
            except OSError:
                pass
            else:
                warnings.warn(
                    f"{path} could not be read as JSON; preserved as "
                    f"{bad} and starting fresh with default settings",
                    stacklevel=2)
        else:
            return path                          # valid existing file
    migrated_key = None
    if genuinely_fresh:
        legacy = _legacy_ini_file()
        if legacy.exists():
            migrated_key = _read_legacy_ini_value(legacy, "anthropic_api_key")
    data = _materialize_settings(migrated_key)
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True),
                        encoding="utf-8")
    except OSError:
        pass
    return path


class _JsonSettings:
    """A minimal shim over a plain JSON file, shaped to the two methods
    `app_settings()`'s one caller (`catalog.py`) uses -- same names as the
    `QSettings` object this replaces, but a DIFFERENT GUARANTEE: `value()`
    returns the type that was stored, not an untyped INI string. That is
    the whole reason for the change (0075-ruling.md sec1): `QSettings`' INI
    backend, and `configparser` equally, would hand back the string
    `"false"` for a stored `False` -- truthy, silently inverting every
    boolean flag on read."""

    def __init__(self, path: Path):
        self._path = path
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._data = {}
            return
        # version-upgrade on load, not only at creation (0078-ruling.md
        # sec2): a file materialised under an OLDER SETTINGS_VERSION still
        # needs to walk forward, and a key it does not carry still falls
        # through to DEFAULT_SETTINGS at read time regardless.
        if self._data.get("version") != SETTINGS_VERSION:
            self._data = _migrate_settings_data(self._data)
            try:
                self._path.write_text(
                    json.dumps(self._data, indent=2, sort_keys=True),
                    encoding="utf-8")
            except OSError:
                pass

    def value(self, key, default=None):
        return self._data.get(key, default)

    def setValue(self, key, value):
        self._data[key] = value
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2, sort_keys=True),
                encoding="utf-8")
        except OSError:
            pass


def app_settings() -> "_JsonSettings":
    """The app-wide settings store: a plain JSON file, not `QSettings`
    (0075-ruling.md) -- an untyped INI string was the exact hazard being
    eliminated, and `configparser` carries the identical one under a
    different name. Same two-method shape every existing caller already
    uses; `catalog.py` needs no change."""
    return _JsonSettings(_ensure_settings_file())


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
