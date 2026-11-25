"""The PYRAMID-ROOF parametric kind (0367): its parameters, what its dialog
reports, its plan symbol and its findings. The arithmetic is
`pyramid_geometry.py`.

REGISTERED (stage 2) now that `PyramidRoofItem` draws one and the catalog
offers it in the Framing group: a drag from the palette places it on the room
under the drop, a double-click opens the generic dialog, and the plan symbol is
drawn from the parameters (the wall-line and eave polygons, the hips and the
apex). Stage 1 built the kind but withheld `register()`, exactly as the
dormer's phase 1 built `DormerKind` before `DormerItem` could draw it.

`context` (all optional) is what the item will know about where it stands:

    ceiling_in     the ceiling of the room it is dropped on, above this level;
                   the `room_top` eaves bind follows it
    room_present   True/False: a room is defined under it; None/absent = nobody
                   looked. Drives `pyramid.no_room`
    off_room_in    how far the wall-line polygon lies off that room's walls, in
                   inches; drives `pyramid.off_room`
    buried         True when the pyramid lies wholly under another, higher roof
                   so nothing of it shows; drives `pyramid.buried`
"""
from floorplanner.parametric import pyramid_geometry as pg
from floorplanner.parametric.findings import ADVISORY, ERROR, WARNING, Finding
from floorplanner.parametric.params import (
    ENUM, FLOAT, INT, ParamSpec, pitch_unit_modes)
from floorplanner.parametric.registry import ParametricKind, register


def _fmt(x, places=1):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def _manual_eaves(values):
    return values.get("eaves_bind") == "manual"


class PyramidRoofKind(ParametricKind):
    kind = "pyramid_roof"
    title = "Pyramid Roof Properties"

    def specs(self):
        d = pg.STATE_DEFAULTS
        return [
            ParamSpec("sides", "Sides", INT, d["sides"],
                      minimum=pg.MIN_SIDES, maximum=pg.MAX_SIDES, step=1,
                      tooltip="A regular polygon of 3 to 12 sides; the pyramid "
                              "has one face per side."),
            ParamSpec("inradius_in", "Inradius", FLOAT, d["inradius_in"],
                      unit="in", minimum=pg.MIN_INRADIUS_IN, maximum=600.0,
                      step=1.0,
                      tooltip="Centre to the WALL line (the eaves-start line) -- "
                              "the run the pitch climbs to the apex."),
            ParamSpec("eaves_bind", "Eaves", ENUM, d["eaves_bind"],
                      choices=(("room_top", "Follow the room ceiling"),
                               ("manual", "Set by hand")),
                      tooltip="ROOM-TOP keeps the eaves at the ceiling of the "
                              "room it sits on; MANUAL sets the eaves height "
                              "directly."),
            ParamSpec("eaves_h_in", "Eaves height", FLOAT, d["eaves_h_in"],
                      unit="in", minimum=0.0, maximum=480.0, step=0.5,
                      enabled_fn=_manual_eaves,
                      tooltip="The eaves-start line above THIS level's floor. "
                              "Editable only when the eaves are set by hand."),
            ParamSpec("pitch_12", "Pitch", FLOAT, d["pitch_12"], unit="in 12",
                      minimum=0.5, maximum=24.0, step=0.5,
                      unit_modes=pitch_unit_modes(0.5, 24.0),
                      unit_setting="pitch_units",
                      tooltip="Rise per 12 in of run, on EVERY face, OR in "
                              "degrees. The apex height is derived from it."),
            ParamSpec("overhang_in", "Eave overhang", FLOAT, d["overhang_in"],
                      unit="in", minimum=0.0, maximum=60.0, step=1.0,
                      tooltip="How far the eave projects past the wall line, in "
                              "plan."),
            ParamSpec("weld", "Weld into roof", ENUM, d["weld"],
                      choices=(("auto", "Auto (where higher)"), ("off", "Off")),
                      tooltip="AUTO draws the pyramid only where it is the higher "
                              "surface, cutting it into the surrounding roof "
                              "(stage 3); OFF draws it whole and ignores every "
                              "roof."),
        ]

    def normalize(self, state):
        st = dict(pg.normalize_state(state))
        st["apex_h_in"] = pg.apex_height(st)
        return st

    def to_state(self, values):
        st = pg.normalize_state(values)
        return {k: st[k] for k in pg.STATE_DEFAULTS}

    def evaluate(self, values, context):
        st = pg.normalize_state(values)
        ctx = context or {}
        findings = []

        # the room it sits on (R3). no room -> the eaves cannot follow a
        # ceiling, so they are read as manual.
        room_present = ctx.get("room_present")
        ceiling = ctx.get("ceiling_in")
        try:
            ceiling = None if ceiling is None else float(ceiling)
        except (TypeError, ValueError):
            ceiling = None
        est = dict(st)
        bound = st["eaves_bind"] == "room_top" and room_present is not False
        if bound and ceiling is not None:
            est["eaves_h_in"] = ceiling

        if st["pitch_12"] <= 0.0:
            findings.append(Finding(
                "pyramid.flat", ERROR,
                "A pyramid roof needs a pitch above zero.",
                field="pitch_12", overridable=True))

        if room_present is False:
            findings.append(Finding(
                "pyramid.no_room", WARNING,
                "This pyramid sits on no room, so its eaves cannot follow a "
                "ceiling and are set by hand. Drop it on a room, or set the "
                "eaves height.", field="eaves_bind"))

        off = ctx.get("off_room_in")
        try:
            off = None if off is None else float(off)
        except (TypeError, ValueError):
            off = None
        if off is not None and off > pg.MIN_INRADIUS_IN:
            findings.append(Finding(
                "pyramid.off_room", ADVISORY,
                f"The wall line stands up to {_fmt(off)} in off this room's "
                "walls. Resize or move it to sit on them.",
                actual=off, field="inradius_in"))

        if ctx.get("buried"):
            findings.append(Finding(
                "pyramid.buried", ADVISORY,
                "This pyramid lies wholly under another, higher roof: nothing "
                "of it shows. Raise it, or move it out from under."))

        derived = {
            "state": est,
            "apex_h_in": pg.apex_height(est),
            "eaves_h_in": est["eaves_h_in"],
            "eave_h_in": pg.eave_height(est),
            "circumradius_in": pg.circumradius(est),
            "plan": pg.plan(est),
            "faces": pg.face_planes(est),
            "footprint": pg.footprint(est),
            "bbox": pg.bbox(est),
            "eaves_bound": bound,
        }
        return derived, findings

    def summary(self, values, derived, context):
        if derived is None:
            return [("Result", "cannot be built")]
        st = derived["state"]
        rows = [
            ("Plan", f"{st['sides']}-sided, {_fmt(st['inradius_in'])} in to the "
                     f"wall line ({_fmt(derived['circumradius_in'])} in to a "
                     "corner)"),
            ("Eaves height", f"{_fmt(derived['eaves_h_in'])} in above this floor"
                             + (" (from the room ceiling)" if derived["eaves_bound"]
                                else " (set by hand)")),
            ("Apex height", f"{_fmt(derived['apex_h_in'])} in above this floor"),
            ("Pitch", f"{_fmt(st['pitch_12'])} in 12, every face"),
            ("Eave overhang", f"{_fmt(st['overhang_in'])} in past the wall line"),
            ("Weld", "into the surrounding roof" if st["weld"] == "auto"
                     else "off (drawn whole)"),
        ]
        return rows

    def footprint(self, state):
        return pg.bbox(pg.normalize_state(state))

    def plan_symbol(self, state):
        """The plan symbol drawn from the parameters (C1: `pyramid_geometry`):
        the eave polygon (solid), the wall-line polygon (dashed), the hips
        (apex to each eave corner) and the apex dot. A generic `{"prims": ...}`
        list in the item's frame -- x across, `f` DOWN from the top edge, as
        `FurnishingItem._paint_plan_prims` reads it. The eave bbox is symmetric
        about the centre, so the item's `pos` (the apex in plan) sits at
        `f = depth / 2` and the local point `(x, y)` is `(x, y + depth / 2)`."""
        st = pg.normalize_state(state)
        half = pg.bbox(st)[1] / 2.0          # the eave bbox depth, halved

        def f(y):
            return y + half

        prims = [("poly", "solid", [(x, f(y)) for x, y in pg.eaves_polygon(st)]),
                 ("poly", "dashed", [(x, f(y)) for x, y in pg.wall_polygon(st)])]
        prims += [("line", 0.0, half, cx, f(cy))
                  for (_apex, (cx, cy)) in pg.hips(st)]
        prims.append(("dot", 0.0, half, 2.0))
        return {"prims": prims}


# Registered (stage 2): the item, the catalog symbol and the plan drawing now
# exist, so the palette offers a pyramid roof and a double-click edits it.
PYRAMID_ROOF = register(PyramidRoofKind())
