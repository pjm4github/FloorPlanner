"""Qt-free dataclasses for the v5 design document (P1.1).

The single Python definition of the v5 schema's shape. `Design.from_dict` /
`to_dict` round-trip a `floorplanner-design` document BYTE-IDENTICALLY: a field
that is present-with-null (e.g. a free wall's `left: null`) is kept as null, and
a field that is absent (e.g. a room with no `area_accounting`) stays absent --
the `_MISSING` sentinel distinguishes the two. Sub-structures the schema does not
give their own object type (`settings`, `anchor`, `placement`, `label`,
`properties`, `pos`, provenance fields) are carried as raw values, so they
round-trip verbatim.

This module imports ONLY the standard library -- no Qt, no other floorplanner
module. `tests/test_design_model.py` asserts that in isolation. No behaviour and
no callers yet; the scene<->design bridge arrives at P1.4/P1.5.
"""
from dataclasses import dataclass
from typing import Any, ClassVar

# sentinel for "key absent from the source" -- distinct from JSON null (None),
# which is a present value we must preserve
_MISSING = object()

# field spec markers used in each dataclass's FIELDS table
RAW = "raw"                      # scalar / raw dict / raw list, stored as-is


def _list(child):
    return ("list", child)      # a JSON array of `child` dataclasses


@dataclass
class _Node:
    """Shared from_dict/to_dict driven by the subclass's FIELDS table.
    FIELDS is an ordered list of (name, spec); spec is RAW, a _Node subclass
    (nested object), or _list(subclass) (array of objects). Emit order follows
    FIELDS; absent (_MISSING) fields are omitted, so presence round-trips."""
    FIELDS: ClassVar = []

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls()
        for name, spec in cls.FIELDS:
            if name not in d:
                continue                        # leave the _MISSING default
            v = d[name]
            if spec is RAW or v is None:
                setattr(obj, name, v)
            elif isinstance(spec, tuple):       # ("list", child)
                setattr(obj, name, [spec[1].from_dict(x) for x in v])
            else:                               # nested object
                setattr(obj, name, spec.from_dict(v))
        return obj

    def to_dict(self) -> dict:
        out = {}
        for name, spec in self.FIELDS:
            v = getattr(self, name)
            if v is _MISSING:
                continue                        # absent in source -> absent here
            if spec is RAW or v is None:
                out[name] = v
            elif isinstance(spec, tuple):
                out[name] = [c.to_dict() for c in v]
            else:
                out[name] = v.to_dict()
        return out


@dataclass
class Level(_Node):
    FIELDS: ClassVar = [("id", RAW), ("name", RAW), ("elevation_in", RAW),
                        ("height_in", RAW), ("kind", RAW), ("reference", RAW)]
    id: Any = _MISSING
    name: Any = _MISSING
    elevation_in: Any = _MISSING
    height_in: Any = _MISSING
    kind: Any = _MISSING
    reference: Any = _MISSING


@dataclass
class Vertex(_Node):
    FIELDS: ClassVar = [("id", RAW), ("level", RAW), ("x", RAW), ("y", RAW),
                        ("locked", RAW)]
    id: Any = _MISSING
    level: Any = _MISSING
    x: Any = _MISSING
    y: Any = _MISSING
    locked: Any = _MISSING


@dataclass
class Opening(_Node):
    # data order: required (id,kind,code,anchor) then the door-only optionals;
    # sill_in/head_in are appended (absent in the corpus) so present fields keep
    # their source order
    FIELDS: ClassVar = [("id", RAW), ("kind", RAW), ("code", RAW),
                        ("anchor", RAW), ("door_type", RAW), ("hinge", RAW),
                        ("swings_toward", RAW), ("sill_in", RAW),
                        ("head_in", RAW)]
    id: Any = _MISSING
    kind: Any = _MISSING
    code: Any = _MISSING
    anchor: Any = _MISSING
    door_type: Any = _MISSING
    hinge: Any = _MISSING
    swings_toward: Any = _MISSING
    sill_in: Any = _MISSING
    head_in: Any = _MISSING


@dataclass
class Wall(_Node):
    FIELDS: ClassVar = [("id", RAW), ("level", RAW), ("v1", RAW), ("v2", RAW),
                        ("type", RAW), ("left", RAW), ("right", RAW),
                        ("openings", _list(Opening)), ("thickness_in", RAW),
                        ("finish_left", RAW), ("finish_right", RAW)]
    id: Any = _MISSING
    level: Any = _MISSING
    v1: Any = _MISSING
    v2: Any = _MISSING
    type: Any = _MISSING
    left: Any = _MISSING
    right: Any = _MISSING
    openings: Any = _MISSING
    thickness_in: Any = _MISSING
    finish_left: Any = _MISSING
    finish_right: Any = _MISSING


@dataclass
class OutlineEdge(_Node):
    FIELDS: ClassVar = [("v", RAW), ("wall", RAW)]
    v: Any = _MISSING
    wall: Any = _MISSING


@dataclass
class Room(_Node):
    FIELDS: ClassVar = [("id", RAW), ("level", RAW), ("name", RAW),
                        ("category", RAW), ("outline", _list(OutlineEdge)),
                        ("placement", RAW), ("label", RAW), ("properties", RAW),
                        ("area_accounting", RAW), ("holes", RAW),
                        ("nominal_size", RAW)]
    id: Any = _MISSING
    level: Any = _MISSING
    name: Any = _MISSING
    category: Any = _MISSING
    outline: Any = _MISSING
    placement: Any = _MISSING
    label: Any = _MISSING
    properties: Any = _MISSING
    area_accounting: Any = _MISSING
    holes: Any = _MISSING
    nominal_size: Any = _MISSING


@dataclass
class Furnishing(_Node):
    FIELDS: ClassVar = [("id", RAW), ("level", RAW), ("kind", RAW),
                        ("room", RAW), ("pos", RAW), ("rotation", RAW),
                        ("state", RAW)]
    id: Any = _MISSING
    level: Any = _MISSING
    kind: Any = _MISSING
    room: Any = _MISSING
    pos: Any = _MISSING
    rotation: Any = _MISSING
    state: Any = _MISSING


@dataclass
class Group(_Node):
    FIELDS: ClassVar = [("id", RAW), ("level", RAW), ("name", RAW),
                        ("members", RAW), ("rotation", RAW)]
    id: Any = _MISSING
    level: Any = _MISSING
    name: Any = _MISSING
    members: Any = _MISSING
    rotation: Any = _MISSING


@dataclass
class Roof(_Node):
    """P1.1's own additive shape, added at 0139-ruling.md ("the roofline
    plan") R1: a ridge line, two heights, an overhang, and a per-end
    gable/hip flag. `ridge`/`gable` are raw 2-element arrays -- points
    and booleans respectively -- not their own dataclasses, the same
    RAW-passthrough convention `Furnishing.pos`/`Room.placement` already
    use for a schema shape with no sub-object identity of its own.
    Pitch is DERIVED (rise over the ridge-to-eaves horizontal run), never
    stored -- the two heights are the source of truth, so a UI showing a
    live pitch and one accepting a typed pitch are the same dialog
    recomputing whichever height is unlocked, not two representations
    that can disagree."""
    FIELDS: ClassVar = [("id", RAW), ("level", RAW), ("ridge", RAW),
                        ("eaves_h_in", RAW), ("ridge_h_in", RAW),
                        ("overhang_in", RAW), ("gable", RAW)]
    id: Any = _MISSING
    level: Any = _MISSING
    ridge: Any = _MISSING
    eaves_h_in: Any = _MISSING
    ridge_h_in: Any = _MISSING
    overhang_in: Any = _MISSING
    gable: Any = _MISSING


@dataclass
class Provenance(_Node):
    FIELDS: ClassVar = [("migrated_from", RAW), ("tool", RAW), ("mode", RAW),
                        ("endpoints_welded", RAW), ("openings_deduped", RAW),
                        ("notes", RAW)]
    migrated_from: Any = _MISSING
    tool: Any = _MISSING
    mode: Any = _MISSING
    endpoints_welded: Any = _MISSING
    openings_deduped: Any = _MISSING
    notes: Any = _MISSING


@dataclass
class Design(_Node):
    FIELDS: ClassVar = [("format", RAW), ("version", RAW), ("units", RAW),
                        ("settings", RAW), ("levels", _list(Level)),
                        ("vertices", _list(Vertex)), ("walls", _list(Wall)),
                        ("rooms", _list(Room)),
                        ("furnishings", _list(Furnishing)),
                        ("groups", _list(Group)), ("reference_images", RAW),
                        ("annotations", RAW), ("roofs", _list(Roof)),
                        ("provenance", Provenance)]
    format: Any = _MISSING
    version: Any = _MISSING
    units: Any = _MISSING
    settings: Any = _MISSING
    levels: Any = _MISSING
    vertices: Any = _MISSING
    walls: Any = _MISSING
    rooms: Any = _MISSING
    furnishings: Any = _MISSING
    groups: Any = _MISSING
    reference_images: Any = _MISSING
    annotations: Any = _MISSING
    roofs: Any = _MISSING
    provenance: Any = _MISSING
