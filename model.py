"""Plain-Python domain model for a floor plan — the Qt-free source of truth
for the on-disk JSON schema.

`Project` (and the `Wall`/`Room`/`Opening`/`Furnishing`/`Floor` dataclasses it
owns) is the single definition of the documented `floorplanner-json` format.
`Project.to_dict()` / `Project.from_dict()` round-trip the format and own the
load-time version migration. None of this imports Qt, so the schema and its
migration are unit-testable without a `QApplication`.

The live editor still edits `QGraphicsItem`s in a scene; `MainWindow` bridges
the two (`project_from_scene` / `apply_project_to_scene`).  Coordinates here are
plain `(x, y)` float tuples, converted to/from `QPointF` only at that bridge.

Forward-compat for multi-floor plans (REFACTOR_PLAN.md / TODO.md): every item
carries a `floor` and `Project` carries `floors` + `active_floor`, defaulting to
a single "default" floor.  These fields are NOT yet serialized — `to_dict()`
still emits the v3 shape exactly — so the Floors feature owns the v4 bump and
the per-item `floor` emission.  Reading them here is harmless on v3 files.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

FILE_FORMAT = "floorplanner-json"
FILE_VERSION = 3          # v3: walls carry a list of owning rooms (shared walls)
DEFAULT_FLOOR = "default"

Coord = tuple[float, float]


def _coord(v) -> Coord:
    return (float(v[0]), float(v[1]))


# ---------------------------------------------------------------------------
# Leaf items
# ---------------------------------------------------------------------------
@dataclass
class Opening:
    kind: str = "door"
    code: str = "3280"
    s: float = 0.0
    door_type: str = "LH"
    swing: int = -1

    @classmethod
    def from_dict(cls, d: dict, default_s: float) -> "Opening":
        return cls(
            kind=d.get("kind", "door"),
            code=str(d.get("code", "3280")),
            s=float(d.get("s", default_s)),
            door_type=d.get("door_type", "LH"),
            swing=-1 if float(d.get("swing", -1)) < 0 else 1,
        )

    def to_dict(self) -> dict:
        return {"kind": self.kind, "code": self.code, "s": self.s,
                "door_type": self.door_type, "swing": self.swing}


@dataclass
class Wall:
    wall_type: str = "interior"
    p1: Coord = (0.0, 0.0)
    p2: Coord = (0.0, 0.0)
    rooms: list[str] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)
    floor: str = DEFAULT_FLOOR

    def length(self) -> float:
        return math.hypot(self.p2[0] - self.p1[0], self.p2[1] - self.p1[1])

    @classmethod
    def from_dict(cls, d: dict) -> "Wall":
        p1, p2 = _coord(d["p1"]), _coord(d["p2"])
        half = math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 2.0
        return cls(
            wall_type=d.get("type", "interior"),
            p1=p1, p2=p2,
            rooms=list(d.get("rooms", [])),
            openings=[Opening.from_dict(o, half) for o in d.get("openings", [])],
            floor=d.get("floor", DEFAULT_FLOOR),
        )

    def to_dict(self) -> dict:
        # rooms + openings are emitted in a stable order (matches the legacy
        # serialize()): rooms sorted by name, openings sorted along the wall.
        return {
            "type": self.wall_type,
            "p1": [self.p1[0], self.p1[1]],
            "p2": [self.p2[0], self.p2[1]],
            "rooms": sorted(self.rooms),
            "openings": [o.to_dict()
                         for o in sorted(self.openings, key=lambda o: o.s)],
        }


@dataclass
class Room:
    name: str = "Room"
    anchor: Coord = (0.0, 0.0)
    label_offset: Coord = (0.0, 0.0)
    show_dimensions: bool = False
    properties: dict | None = None
    floor: str = DEFAULT_FLOOR

    @classmethod
    def from_dict(cls, d: dict) -> "Room":
        return cls(
            name=d.get("name", "Room"),
            anchor=_coord(d.get("anchor", [0.0, 0.0])),
            label_offset=_coord(d.get("label_offset", [0.0, 0.0])),
            show_dimensions=bool(d.get("show_dimensions", False)),
            properties=d.get("properties"),
            floor=d.get("floor", DEFAULT_FLOOR),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "anchor": [self.anchor[0], self.anchor[1]],
            "label_offset": [self.label_offset[0], self.label_offset[1]],
            "show_dimensions": self.show_dimensions,
            "properties": self.properties,
        }


@dataclass
class Furnishing:
    kind: str = ""
    pos: Coord = (0.0, 0.0)
    rotation: float = 0.0
    extra: dict = field(default_factory=dict)   # per-kind state (stair flight, ...)
    floor: str = DEFAULT_FLOOR

    @classmethod
    def from_dict(cls, d: dict) -> "Furnishing":
        extra = {k: v for k, v in d.items()
                 if k not in ("kind", "pos", "rotation", "floor")}
        return cls(
            kind=str(d.get("kind", "")),
            pos=_coord(d.get("pos", [0.0, 0.0])),
            rotation=float(d.get("rotation", 0.0)),
            extra=extra,
            floor=d.get("floor", DEFAULT_FLOOR),
        )

    def to_dict(self) -> dict:
        return {"kind": self.kind, "pos": [self.pos[0], self.pos[1]],
                "rotation": self.rotation, **self.extra}


@dataclass
class Floor:
    name: str = DEFAULT_FLOOR
    reference: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "Floor":
        return cls(name=d.get("name", DEFAULT_FLOOR),
                   reference=bool(d.get("reference", False)))

    def to_dict(self) -> dict:
        return {"name": self.name, "reference": self.reference}


# ---------------------------------------------------------------------------
# The whole document
# ---------------------------------------------------------------------------
@dataclass
class Project:
    version: int = FILE_VERSION
    units: str = "inches"
    settings: dict = field(default_factory=dict)
    walls: list[Wall] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    furnishings: list[Furnishing] = field(default_factory=list)
    # forward-compat (not serialized until the Floors feature bumps to v4)
    floors: list[Floor] = field(
        default_factory=lambda: [Floor(DEFAULT_FLOOR)])
    active_floor: str = DEFAULT_FLOOR

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        if d.get("format") != FILE_FORMAT:
            raise ValueError("Not a Floor Planner JSON file.")
        floors = [Floor.from_dict(f) for f in d.get("floors", [])] \
            or [Floor(DEFAULT_FLOOR)]
        return cls(
            version=int(d.get("version", FILE_VERSION)),
            units=d.get("units", "inches"),
            settings=dict(d.get("settings", {})),
            walls=[Wall.from_dict(w) for w in d.get("walls", [])],
            rooms=[Room.from_dict(r) for r in d.get("rooms", [])],
            furnishings=[Furnishing.from_dict(f)
                         for f in d.get("furnishings", [])],
            floors=floors,
            active_floor=d.get("active_floor", floors[0].name),
        )

    def to_dict(self) -> dict:
        """Emit the documented v3 JSON.  Arrays are sorted z-independently
        (by geometry, exactly as the legacy serialize() did) so bring-to-front
        z changes never alter the snapshot — keeping undo/redo comparison
        correct.  `floors`/`active_floor` are intentionally NOT emitted yet."""
        walls = [w.to_dict() for w in self.walls]
        rooms = [r.to_dict() for r in self.rooms]
        furnishings = [f.to_dict() for f in self.furnishings]
        walls.sort(key=lambda w: (w["p1"], w["p2"], w["type"],
                                  tuple(w["rooms"])))
        rooms.sort(key=lambda r: r["name"])
        furnishings.sort(key=lambda f: (f["pos"], f["kind"], f["rotation"]))
        return {
            "format": FILE_FORMAT,
            "version": self.version,
            "units": self.units,
            "settings": dict(self.settings),
            "walls": walls,
            "rooms": rooms,
            "furnishings": furnishings,
        }
