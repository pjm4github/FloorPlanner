#!/usr/bin/env python3
"""
fp2dxf -- FloorPlanner v5 design JSON -> DXF R12, purpose-built for
Chief Architect X17's "CAD to Walls" import (KB-00170).

Zero dependencies (writes AC1009 ASCII DXF directly).

Chief's CAD-to-Walls contract, and how this file satisfies it:
  * ALL convertible wall lines on ONE layer            -> layer WALLS
  * railings on their own layer                        -> layer RAILS
  * door / window lines each on their own layer        -> layers DOORS, WINDOWS
  * import wizard: uncheck "Create CAD Blocks", leave the
    shared-endpoint polyline options off, units = inches, 1:1.

Geometry conventions:
  * FloorPlanner is plan-inches, x right, y DOWN (Qt scene).
    DXF is y UP, so every emitted y is negated.  Sidedness text
    (hinge / swings_toward) is passed through verbatim as annotation --
    it is defined in FloorPlanner's own frame and is for the human QC
    pass in Chief, not for geometry.
  * Walls are emitted as their two FACE lines (centerline +/- t/2),
    square-capped at the vertex projections.  Chief derives the wall
    from the pair and auto-joins coincident wall ends, so miters are
    unnecessary; shared-vertex topology in the schema guarantees the
    ends actually coincide.
  * Openings break both face lines; the two face continuations across
    the gap are emitted on DOORS / WINDOWS so Chief places a real
    door/window object of the correct width at the correct station.
  * Non-buildable landscape types (fence, hedge, retaining) and walls
    serving only `concept` rooms go to X-* reference layers that you
    simply leave un-converted (or un-imported) in the wizard.
  * A room outline edge with wall:null is an OPEN edge by design; it is
    drawn dashed on X-OPEN-EDGE so you can trace Invisible walls over
    it in Chief (Chief needs a wall, even invisible, to bound a room).

Everything the DXF cannot carry parametrically (sill/head heights,
door_type, hinge, swing, wall finishes, per-side rooms) is emitted as
small TEXT tags on NOTES next to each opening, plus a machine-readable
sidecar JSON keyed by opening id -> DXF station, for the QC pass.

Usage:
    python fp2dxf.py design.json [-o OUTDIR] [--level ID ...]
                     [--set exterior=6.5 --set interior=4.5 ...]

THICKNESS IS READ FROM `floorplanner.design.validate.STD_T`, NOT CARRIED
HERE (handoff 0038-ruling.md SS3). The first handoff of this module kept
its own `DEFAULT_THICKNESS` copy, reasoned as "must agree with
FloorPlanner's own per-type standards" -- an instruction, and four of
seven entries had already drifted from `STD_T` before this module had
even landed (D73's own lesson: "three tables that are synced become
three tables that disagree again" -- the fix is not a fourth table kept
in sync, it is not having a fourth table). Two DIFFERENT facts were
living in that one column: how thick a wall really is, and which named
Chief wall type it should become. `CHIEF_WALL_TYPE` below is the second
fact, on its own, honestly a name-to-name mapping rather than a
thickness pretending to be one.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------


def _load_stdt_module():
    """`_stdt.py`, loaded BY PATH -- the leaf `0077-ruling.md` sec5 built so
    this file and `fp2pdf.py` share one loader instead of one execing the
    other. Not `from floorplanner.export._stdt import ...`: importing ANY
    `floorplanner` submodule first runs `floorplanner/__init__.py`, which
    star-imports the whole Qt editor (measured at P5.2, D73's own text)."""
    path = Path(__file__).resolve().parent / "_stdt.py"
    spec = importlib.util.spec_from_file_location("_fp2dxf_stdt", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_std_t_cache = None


def _std_t() -> dict[str, float]:
    """THE NORMATIVE thickness table, read live from
    `floorplanner.design.validate` via `_stdt.py` -- never a copy.
    `wall_thickness()` still honours a wall's own `thickness_in` override
    first, exactly as the schema documents it.

    LAZY, NOT MODULE SCOPE (`0077-ruling.md` sec5): nothing runs merely by
    importing this file -- the same shape `fp2pdf.py`'s deferred `reportlab`
    import already has. Cached after the first call within one process;
    each call is otherwise a fresh read of whatever `validate.py` says
    right now."""
    global _std_t_cache
    if _std_t_cache is None:
        _std_t_cache = _load_stdt_module().load_std_thickness()
    return _std_t_cache

#: wall type -> the Chief Architect wall type NAME to pick in the CAD to
#: Walls dialog's Wall Type 1/2 dropdowns. A NAME, not a thickness --
#: keeping this separate from `STD_T` is the whole fix: one column cannot
#: carry "how thick is this wall" and "which Chief type should it become"
#: without the two disagreeing the moment either fact changes on its own
#: (the D74 rule: a channel committed to representing a real quantity
#: cannot also carry identity). Chief matches a line-pair spacing to a
#: wall type within +/-1 inch (README SS3.6), so `STD_T`'s own numbers
#: (exterior 6.0 against Siding-6's 6 7/16" = 0.44" off) are close enough
#: without restating either fact.
#:
#: Only the two types the verified workflow actually assigned a Chief
#: type to are named here. `partition` and `railing` have no confirmed
#: Chief type name on record (the handoff's own README hedges: partition
#: "pair with an Interior-3.5 type IF converted"; railing uses the CAD to
#: Walls dialog's separate Rail Layer slot, not a Wall Type dropdown at
#: all) -- naming one here would be inventing a fact the workflow does
#: not contain, which handoff 0022's own ruling already refused once for
#: a different feature ("--stack").
CHIEF_WALL_TYPE = {
    "exterior": "Siding-6",
    "interior": "Interior-4",
}

#: wall type -> (target layer, participates in CAD-to-Walls)
WALL_LAYER = {
    "exterior":  ("FP-WALLS", True),
    "interior":  ("FP-WALLS", True),
    "partition": ("FP-WALLS", True),
    "railing":   ("FP-RAILS", True),
    "fence":     ("FP-X-FENCE", False),
    "hedge":     ("FP-X-HEDGE", False),
    "retaining": ("FP-X-RETAINING", False),
}

#: opening kind -> layer for the gap-spanning lines.
#: cased / pass_through / gate become doorway-style objects in Chief;
#: they land on DOORS and the NOTES tag says what they really are.
OPENING_LAYER = {
    "door": "FP-DOORS", "window": "FP-WINDOWS",
    "cased": "FP-DOORS", "pass_through": "FP-DOORS", "gate": "FP-DOORS",
}

# layer -> (ACI colour, linetype)
LAYERS = {
    "FP-WALLS":        (7, "CONTINUOUS"),
    "FP-RAILS":        (4, "CONTINUOUS"),
    "FP-DOORS":        (1, "CONTINUOUS"),
    "FP-WINDOWS":      (5, "CONTINUOUS"),
    "FP-X-FENCE":      (8, "CONTINUOUS"),
    "FP-X-HEDGE":      (3, "CONTINUOUS"),
    "FP-X-RETAINING":  (8, "CONTINUOUS"),
    "FP-X-CONCEPT":    (9, "DASHED"),
    "FP-X-OPEN-EDGE":  (2, "DASHED"),
    "FP-ROOM-LABELS":  (7, "CONTINUOUS"),
    "FP-NOTES":        (6, "CONTINUOUS"),
    # 0285: the plan's own annotations, each on a layer of its own so a CAD
    # user can freeze them apart from the opening tags on FP-NOTES
    "FP-DIMENSIONS":   (3, "CONTINUOUS"),
    "FP-ANNOTATIONS":  (7, "CONTINUOUS"),
}

ROOM_LABEL_H = 8.0   # text height, inches
NOTE_H = 4.0
#: 0285: a leader's arrowhead and the shoulder under its text, plan inches
LEADER_ARROW_IN = 6.0                  # arrowhead length
LEADER_ARROW_HALF_IN = 2.0             # arrowhead half-width
LEADER_SHOULDER_IN = 8.0               # the short horizontal under the text


def _load_annot_module():
    """`_annot.py` -- the drawn dimensions' geometry and the ft-in label,
    the leaf shared with `fp2pdf.py` (0285), loaded BY PATH like `_stdt.py`
    so the two exporters draw a dimension the same way."""
    path = Path(__file__).resolve().parent / "_annot.py"
    spec = importlib.util.spec_from_file_location("_fp2dxf_annot", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_annot_cache = None


def _annot():
    """The `_annot.py` leaf, loaded on first use -- nothing runs merely by
    importing this file (0077-ruling.md sec5)."""
    global _annot_cache
    if _annot_cache is None:
        _annot_cache = _load_annot_module()
    return _annot_cache


# --------------------------------------------------------------------------
# minimal DXF R12 writer
# --------------------------------------------------------------------------

class DxfR12:
    """Just enough AC1009 to carry LINEs and TEXT on named layers."""

    def __init__(self) -> None:
        self._ent: list[str] = []

    @staticmethod
    def _g(code: int, value) -> str:
        if isinstance(value, float):
            value = f"{value:.6f}"
        return f"{code}\n{value}\n"

    def line(self, layer: str, x1: float, y1: float,
             x2: float, y2: float) -> None:
        g = self._g
        self._ent.append(
            g(0, "LINE") + g(8, layer)
            + g(10, x1) + g(20, y1) + g(30, 0.0)
            + g(11, x2) + g(21, y2) + g(31, 0.0))

    def arc(self, layer: str, cx: float, cy: float, r: float,
            a_start: float, a_end: float) -> None:
        """Arc, CCW from a_start to a_end (degrees)."""
        g = self._g
        self._ent.append(
            g(0, "ARC") + g(8, layer)
            + g(10, cx) + g(20, cy) + g(30, 0.0)
            + g(40, r) + g(50, a_start) + g(51, a_end))

    def text(self, layer: str, x: float, y: float, h: float,
             s: str, rot: float = 0.0, align: int = 0) -> None:
        """TEXT at (x, y). `align` is R12's horizontal justification
        (group 72): 0 left at the insertion point (the default, and the
        only form written before 0285), 1 centred on it, 2 right-aligned
        to it -- a justified TEXT carries its point as the alignment point
        (11/21/31) as well."""
        g = self._g
        ent = (g(0, "TEXT") + g(8, layer)
               + g(10, x) + g(20, y) + g(30, 0.0)
               + g(40, h) + g(1, s) + g(50, rot))
        if align:
            ent += g(72, align) + g(11, x) + g(21, y) + g(31, 0.0)
        self._ent.append(ent)

    def solid(self, layer: str, pts) -> None:
        """A filled triangle (R12 SOLID; its fourth corner repeats the
        third) -- a leader's arrowhead."""
        g = self._g
        (x1, y1), (x2, y2), (x3, y3) = pts
        self._ent.append(
            g(0, "SOLID") + g(8, layer)
            + g(10, x1) + g(20, y1) + g(30, 0.0)
            + g(11, x2) + g(21, y2) + g(31, 0.0)
            + g(12, x3) + g(22, y3) + g(32, 0.0)
            + g(13, x3) + g(23, y3) + g(33, 0.0))

    def dumps(self) -> str:
        g = self._g
        head = (g(0, "SECTION") + g(2, "HEADER")
                + g(9, "$ACADVER") + g(1, "AC1009")
                + g(0, "ENDSEC"))
        lt = (g(0, "TABLE") + g(2, "LTYPE") + g(70, 2)
              + g(0, "LTYPE") + g(2, "CONTINUOUS") + g(70, 0)
              + g(3, "Solid line") + g(72, 65) + g(73, 0) + g(40, 0.0)
              + g(0, "LTYPE") + g(2, "DASHED") + g(70, 0)
              + g(3, "Dashed __ __ __") + g(72, 65) + g(73, 2)
              + g(40, 12.0) + g(49, 9.0) + g(49, -3.0)
              + g(0, "ENDTAB"))
        la = g(0, "TABLE") + g(2, "LAYER") + g(70, len(LAYERS))
        for name, (aci, ltype) in LAYERS.items():
            la += (g(0, "LAYER") + g(2, name) + g(70, 0)
                   + g(62, aci) + g(6, ltype))
        la += g(0, "ENDTAB")
        st = (g(0, "TABLE") + g(2, "STYLE") + g(70, 1)
              + g(0, "STYLE") + g(2, "STANDARD") + g(70, 0)
              + g(40, 0.0) + g(41, 1.0) + g(50, 0.0) + g(71, 0)
              + g(42, 2.5) + g(3, "txt") + g(4, "")
              + g(0, "ENDTAB"))
        tables = g(0, "SECTION") + g(2, "TABLES") + lt + la + st + g(0, "ENDSEC")
        ents = g(0, "SECTION") + g(2, "ENTITIES") \
            + "".join(self._ent) + g(0, "ENDSEC")
        return head + tables + ents + g(0, "EOF")


# --------------------------------------------------------------------------
# schema helpers
# --------------------------------------------------------------------------

def parse_size_code(code: str) -> tuple[float, float]:
    """WWHH / WWWHH / WWWHHH -> (width_in, height_in)."""
    n = len(code)
    if n == 4:
        return float(code[:2]), float(code[2:])
    if n == 5:
        return float(code[:3]), float(code[3:])
    if n == 6:
        return float(code[:3]), float(code[3:])
    raise ValueError(f"bad size code {code!r}")


@dataclass
class OpeningSpan:
    opening: dict
    s0: float           # station of near edge, inches from v1
    s1: float           # station of far edge


@dataclass
class Ctx:
    doc: dict
    thickness: dict = field(default_factory=lambda: dict(_std_t()))
    warnings: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self.vx = {v["id"]: v for v in self.doc["vertices"]}
        self.rooms = {r["id"]: r for r in self.doc["rooms"]}

    def warn(self, msg: str) -> None:
        # COLLECTED ONLY -- not printed. `convert()` is a library call from
        # a Qt menu handler as well as the CLI below, and a GUI has no
        # stdout/stderr for a user to read (handoff 0038-ruling.md SS4:
        # "the README asks the menu item to show a completion summary...
        # so that summary must be RETURNED"). The CLI prints these itself,
        # once, after `convert()` returns.
        self.warnings.append(msg)

    def pt(self, vid: str) -> tuple[float, float]:
        """Vertex -> DXF coordinates (y negated: Qt y-down -> DXF y-up)."""
        v = self.vx[vid]
        return (float(v["x"]), -float(v["y"]))

    def wall_thickness(self, wall: dict) -> float:
        return float(wall.get("thickness_in") or self.thickness[wall["type"]])

    def wall_serves_only_concept(self, wall: dict) -> bool:
        sides = [wall.get("left"), wall.get("right")]
        sides = [s for s in sides if s]
        if not sides:
            return False
        return all(self.rooms[s]["category"] == "concept"
                   for s in sides if s in self.rooms)


def opening_spans(ctx: Ctx, wall: dict, length: float) -> list[OpeningSpan]:
    spans: list[OpeningSpan] = []
    for op in wall.get("openings", []) or []:
        w, _h = parse_size_code(op["code"])
        a = op["anchor"]
        off = float(a["offset_in"])
        if a["from"] == "v1":
            s0 = off
        elif a["from"] == "v2":
            s0 = length - off - w
        else:  # center: offset of opening CENTRE from wall midpoint
            s0 = length / 2.0 + off - w / 2.0
        s1 = s0 + w
        if s0 < -1e-6 or s1 > length + 1e-6:
            ctx.warn(f"opening {op['id']} ({op['code']}) overruns wall "
                     f"{wall['id']} (len {length:.1f}\"): clamped")
            s0, s1 = max(s0, 0.0), min(s1, length)
        spans.append(OpeningSpan(op, s0, s1))
    spans.sort(key=lambda s: s.s0)
    for a, b in zip(spans, spans[1:], strict=False):
        if b.s0 < a.s1 - 1e-6:
            ctx.warn(f"openings {a.opening['id']} / {b.opening['id']} "
                     f"overlap on wall {wall['id']}")
    return spans


def opening_tag(op: dict) -> str:
    parts = [op["kind"].upper()[0] if op["kind"] != "pass_through" else "P",
             op["code"]]
    if op.get("door_type"):
        parts.append(op["door_type"])
    if op.get("hinge") and op["hinge"] != "none":
        parts.append(f"hinge:{op['hinge']}")
    if op.get("swings_toward") and op["swings_toward"] != "none":
        parts.append(f"swing:{op['swings_toward']}")
    if op.get("sill_in") is not None:
        parts.append(f"sill:{op['sill_in']:g}")
    if op.get("head_in") is not None:
        parts.append(f"head:{op['head_in']:g}")
    return " ".join(parts)


# --------------------------------------------------------------------------
# emission
# --------------------------------------------------------------------------

def _door_symbol(kind: str, door_type) -> str | None:
    """Which DXF symbol an opening gets -- the vocabulary is
    `config.py:DOOR_TYPES`, drawn in the editor by `walls.py:_paint_door`
    and in the PDF exporter by `fp2pdf.py:_door_symbol` -- a third,
    independent transcription, because DXF geometry (LINE/ARC entities)
    shares nothing with either renderer's own primitives. 0135-ruling.md
    sec1's own finding, here too: `door_type == "sliding"` can never
    match this catalog, so every door exported as one hinged leaf+arc --
    including DOORWAY openings, which got a phantom swinging leaf they
    do not have. Returns `"unknown"` for a `door_type` string outside the
    catalog, drawn as a generic swing but named in `ctx.warn()`, not
    silently absorbed -- the same discipline D81 already established for
    `fp2pdf.py`."""
    if kind == "window":
        return "window"
    if kind == "gate":
        return "swing"
    if kind != "door":
        return None                       # cased / pass_through: gap only
    dt = (door_type or "").upper()
    if dt in ("LH", "RH", ""):
        return "swing"
    if dt == "FRENCH":
        return "french"
    if dt == "BIFOLD":
        return "bifold"
    if dt == "POCKET":
        return "pocket"
    if dt == "SLIDER":
        return "slider"
    if dt == "DOORWAY":
        return "doorway"
    if dt.startswith("GARAGE"):
        return "garage"
    return "unknown"


def _swing_leaf(dxf, op_layer, p1, ux, uy, nx, ny, hinge_s, radius,
                direction, sgn) -> None:
    """One swing leaf + quarter-circle arc, hinged at station `hinge_s`.
    `direction` = +1 if the jamb it swings toward sits at a HIGHER
    station, -1 if lower -- the DXF analogue of `fp2pdf.py`'s own `leaf`
    closure inside `draw_opening`, same geometry, LINE/ARC entities
    instead of a reportlab canvas."""
    hx, hy = p1[0] + ux * hinge_s, p1[1] + uy * hinge_s
    js = hinge_s + direction * radius
    jx, jy = p1[0] + ux * js, p1[1] + uy * js
    lx, ly = hx + nx * radius * sgn, hy + ny * radius * sgn
    dxf.line(op_layer, hx, hy, lx, ly)
    a_leaf = math.degrees(math.atan2(ly - hy, lx - hx))
    a_jamb = math.degrees(math.atan2(jy - hy, jx - hx))
    if (a_leaf - a_jamb) % 360.0 <= 180.0:
        dxf.arc(op_layer, hx, hy, radius, a_jamb, a_leaf)
    else:
        dxf.arc(op_layer, hx, hy, radius, a_leaf, a_jamb)


def emit_wall(ctx: Ctx, dxf: DxfR12, wall: dict, sidecar: dict) -> None:
    p1, p2 = ctx.pt(wall["v1"]), ctx.pt(wall["v2"])
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        ctx.warn(f"wall {wall['id']} has zero length; skipped")
        return
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux                       # unit normal
    t2 = ctx.wall_thickness(wall) / 2.0

    layer, convert_ = WALL_LAYER[wall["type"]]
    if ctx.wall_serves_only_concept(wall):
        layer, convert_ = "FP-X-CONCEPT", False

    def sta(s: float, side: float) -> tuple[float, float]:
        """station s (inches from v1) on face `side` (+1 / -1)."""
        return (p1[0] + ux * s + nx * t2 * side,
                p1[1] + uy * s + ny * t2 * side)

    spans = opening_spans(ctx, wall, length) if convert_ else []

    # face lines, broken at openings
    breaks = [0.0]
    for sp in spans:
        breaks += [sp.s0, sp.s1]
    breaks.append(length)
    for i in range(0, len(breaks) - 1, 2):        # solid segments
        a, b = breaks[i], breaks[i + 1]
        if b - a < 1e-6:
            continue
        for side in (+1.0, -1.0):
            (x1, y1), (x2, y2) = sta(a, side), sta(b, side)
            dxf.line(layer, x1, y1, x2, y2)

    # opening gap lines + tags
    for sp in spans:
        op_layer = OPENING_LAYER[sp.opening["kind"]]
        for side in (+1.0, -1.0):
            (x1, y1), (x2, y2) = sta(sp.s0, side), sta(sp.s1, side)
            dxf.line(op_layer, x1, y1, x2, y2)
        # Conventional symbol per catalog type: Chief's CAD to Walls
        # classifies openings by symbol shape (KB-00170) -- bare gap
        # lines read as a WINDOW, so doors need a leaf/arc, and windows
        # need their own glass line, to read as what they are.
        op = sp.opening
        w = sp.s1 - sp.s0
        mid_s = (sp.s0 + sp.s1) / 2.0
        symbol = _door_symbol(op["kind"], op.get("door_type"))

        def _pt(s, off=0.0):
            return (p1[0] + ux * s + nx * off, p1[1] + uy * s + ny * off)

        if symbol == "window":
            # the conventional triple-line symbol -- gap lines (already
            # emitted above) plus the glass line at the centerline
            dxf.line(op_layer, *_pt(sp.s0), *_pt(sp.s1))
        elif symbol is not None:
            if symbol == "unknown":
                ctx.warn(f"opening {op['id']}: unrecognized door_type "
                         f"{op.get('door_type')!r}, drawn as a generic "
                         f"swing")
            # No hinge/swing recorded -> still draw a symbol with a
            # DEFAULT handedness (hinge:v1, swing:left) so Chief
            # classifies it as a DOOR; handedness is a QC fix, the
            # object class is not. Qt 'left' of v1->v2 maps to geometric
            # CCW-left in DXF under the y-flip, so the sign convention
            # carries over.
            hinge = op.get("hinge") if op.get("hinge") in ("v1", "v2") else "v1"
            swing = (op.get("swings_toward")
                     if op.get("swings_toward") in ("left", "right")
                     else "left")
            sgn = 1.0 if swing == "left" else -1.0
            if symbol in ("swing", "unknown"):
                hinge_s = sp.s0 if hinge == "v1" else sp.s1
                direction = 1.0 if hinge == "v1" else -1.0
                _swing_leaf(dxf, op_layer, p1, ux, uy, nx, ny,
                            hinge_s, w, direction, sgn)
            elif symbol == "french":
                _swing_leaf(dxf, op_layer, p1, ux, uy, nx, ny,
                            sp.s0, w / 2.0, 1.0, sgn)
                _swing_leaf(dxf, op_layer, p1, ux, uy, nx, ny,
                            sp.s1, w / 2.0, -1.0, sgn)
            elif symbol == "bifold":
                face_d = sgn * t2
                rise = sgn * 0.35 * w
                for a, m, b in ((sp.s0, sp.s0 + 0.25 * w, mid_s),
                                (mid_s, sp.s0 + 0.75 * w, sp.s1)):
                    dxf.line(op_layer, *_pt(a, face_d), *_pt(m, face_d + rise))
                    dxf.line(op_layer, *_pt(m, face_d + rise), *_pt(b, face_d))
            elif symbol == "pocket":
                # a single line recessed into the wall cavity before s0 --
                # the panel slid out of the way, not the opening itself
                dxf.line(op_layer, *_pt(sp.s0 - w), *_pt(sp.s0))
            elif symbol == "slider":
                # two overlapping half-width panels on the centerline
                for k, side in ((0, +1.0), (1, -1.0)):
                    a = sp.s0 + k * w * 0.45
                    b = a + w * 0.55
                    dxf.line(op_layer, *_pt(a, 0.75 * side), *_pt(b, 0.75 * side))
            elif symbol == "garage":
                # a full-width panel line -- the closed overhead door
                dxf.line(op_layer, *_pt(sp.s0), *_pt(sp.s1))
            # symbol == "doorway": gap lines only, no leaf, no arc

        mid = (sp.s0 + sp.s1) / 2.0
        tx = p1[0] + ux * mid + nx * (t2 + NOTE_H * 1.5)
        ty = p1[1] + uy * mid + ny * (t2 + NOTE_H * 1.5)
        rot = math.degrees(math.atan2(uy, ux))
        if rot > 90 or rot <= -90:
            rot += 180.0                            # keep text readable
        dxf.text("FP-NOTES", tx, ty, NOTE_H, opening_tag(sp.opening), rot)
        sidecar[sp.opening["id"]] = {
            "wall": wall["id"], "kind": sp.opening["kind"],
            "code": sp.opening["code"],
            "station_in": [round(sp.s0, 3), round(sp.s1, 3)],
            "sill_in": sp.opening.get("sill_in"),
            "head_in": sp.opening.get("head_in"),
            "door_type": sp.opening.get("door_type"),
            "hinge": sp.opening.get("hinge"),
            "swings_toward": sp.opening.get("swings_toward"),
        }


def emit_room(ctx: Ctx, dxf: DxfR12, room: dict) -> None:
    loops = [room["outline"]] + list(room.get("holes") or [])
    # open edges (wall: null) -> dashed reference lines
    for loop in loops:
        n = len(loop)
        for i, edge in enumerate(loop):
            if edge.get("wall") is None:
                a = ctx.pt(edge["v"])
                b = ctx.pt(loop[(i + 1) % n]["v"])
                dxf.line("FP-X-OPEN-EDGE", a[0], a[1], b[0], b[1])
    # label at centroid + offset (offset is in Qt frame: negate its y)
    pts = [ctx.pt(e["v"]) for e in room["outline"]]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    off = (room.get("label") or {}).get("offset") or [0.0, 0.0]
    dxf.text("FP-ROOM-LABELS", cx + off[0], cy - off[1],
             ROOM_LABEL_H, room["name"])


def emit_leader(dxf: DxfR12, ann: dict) -> None:
    """A leader (0270) as the screen and the PDF draw it: the line from the
    text's end (`p2`) to the arrow's tip (`pos`), a filled arrowhead at the
    tip, a short shoulder under the text on the side away from the tip,
    the text beside the shoulder. Plan inches, y up."""
    tx, ty = float(ann["pos"][0]), -float(ann["pos"][1])
    p2 = ann.get("p2") or ann["pos"]
    ax, ay = float(p2[0]), -float(p2[1])
    side = 1.0 if ax >= tx else -1.0
    sx = ax + side * LEADER_SHOULDER_IN
    lay = "FP-ANNOTATIONS"
    dxf.line(lay, ax, ay, tx, ty)
    dxf.line(lay, ax, ay, sx, ay)
    dx, dy = tx - ax, ty - ay
    ln = math.hypot(dx, dy)
    if ln > 1e-6:
        ux, uy = dx / ln, dy / ln
        L, hw = min(LEADER_ARROW_IN, ln), LEADER_ARROW_HALF_IN
        bx, by = tx - ux * L, ty - uy * L
        dxf.solid(lay, [(tx, ty), (bx - uy * hw, by + ux * hw),
                        (bx + uy * hw, by - ux * hw)])
    gap = 1.5
    dxf.text(lay, sx + side * gap, ay - NOTE_H * 0.35, NOTE_H, ann["text"],
             align=0 if side > 0 else 2)


def emit_dimension(dxf: DxfR12, ann: dict, units: str) -> bool:
    """A drawn dimension (0263) as the screen draws it -- extension lines,
    the dimension line, a slash at each end, the length centred above the
    line -- from the geometry `_annot.py` shares with `fp2pdf.py`. False
    for a record with nothing to draw."""
    d = _annot().dimension_geometry(ann, units)
    if d is None:
        return False
    lay = "FP-DIMENSIONS"
    for (x1, y1), (x2, y2) in d["ext"] + [d["line"]] + d["slashes"]:
        dxf.line(lay, x1, y1, x2, y2)
    # the label sits just above the line: lift it along the line's normal
    r = math.radians(d["rot"])
    lift = NOTE_H * 0.6
    lx = d["label_at"][0] - math.sin(r) * lift
    ly = d["label_at"][1] + math.cos(r) * lift
    dxf.text(lay, lx, ly, NOTE_H, d["label"], d["rot"], align=1)
    return True


def emit_annotations(dxf: DxfR12, anns, settings: dict) -> int:
    """The level's annotations, by the plan's Show switches -- what the
    plan hides is not exported, as on the PDF (0268): the drawn dimensions
    while Show > Dimensions is on, the texts and leaders while Show >
    Annotations is on. Returns how many were written."""
    show_ann = bool(settings.get("show_annotations", True))
    show_dim = bool(settings.get("show_dimensions", True))
    units = settings.get("dimension_units", "ftin")
    n = 0
    for ann in anns:
        kind = ann.get("kind")
        if kind == "dimension" and show_dim:
            n += emit_dimension(dxf, ann, units)
        elif kind == "text" and show_ann and ann.get("text"):
            p = (float(ann["pos"][0]), -float(ann["pos"][1]))
            dxf.text("FP-ANNOTATIONS", p[0], p[1], NOTE_H,
                     ann["text"], -float(ann.get("rotation", 0)))
            n += 1
        elif kind == "leader" and show_ann and ann.get("text"):
            emit_leader(dxf, ann)
            n += 1
    return n


@dataclass
class ConvertResult:
    """Everything a caller needs to show a completion summary -- a GUI menu
    handler as much as the CLI below, per handoff 0038-ruling.md SS4: the
    module has no business deciding where its progress and warnings are
    READ, only collecting them."""
    written: list[Path] = field(default_factory=list)
    skipped_levels: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


#: the document versions this reader accepts -- the schema's own enum (5; 6 adds roofs)
SUPPORTED_VERSIONS = (5, 6)


def convert(doc: dict, outdir: Path, only_levels=None,
            thickness_overrides=None) -> ConvertResult:
    if doc.get("format") != "floorplanner-design" or doc.get("version") not in SUPPORTED_VERSIONS:
        # version 6 = 5 plus an optional `roofs` block (the schema's enum);
        # a plan with a roof was refused here until 2026-10-11 (fp2pdf.py
        # says why, the same fault, the same day)
        # A NORMAL EXCEPTION, NOT `raise SystemExit` (0038-ruling.md SS4):
        # this is a library call from a Qt menu handler as well as the CLI,
        # and an unhandled exception inside a Qt override presents as a
        # segfault with no traceback (SESSION_SNAPSHOT SS5) -- but at least
        # THAT is catchable. `SystemExit` inside a Qt call stack is not
        # something a `try/except Exception` around the menu action would
        # even see coming.
        raise ValueError(
            f"not a floorplanner-design document of version 5 or 6 "
            f"(format={doc.get('format')!r}, version={doc.get('version')!r})")
    ctx = Ctx(doc)
    if thickness_overrides:
        ctx.thickness.update(thickness_overrides)

    result = ConvertResult()
    for level in doc["levels"]:
        lid = level["id"]
        if only_levels and lid not in only_levels:
            continue
        if level.get("kind", "storey") == "site" and not only_levels:
            result.skipped_levels.append(lid)
            continue
        dxf, sidecar = DxfR12(), {}
        n_walls = 0
        for wall in doc["walls"]:
            if wall["level"] == lid:
                emit_wall(ctx, dxf, wall, sidecar)
                n_walls += 1
        for room in doc["rooms"]:
            if room["level"] == lid:
                emit_room(ctx, dxf, room)
        n_ann = emit_annotations(
            dxf, [a for a in doc.get("annotations", []) or [] if a.get("level") == lid],
            doc.get("settings") or {})

        out = outdir / f"{lid}.dxf"
        # ENCODING NAMED EXPLICITLY (0038-ruling.md SS4): the platform
        # default on Windows is cp1252, and room names -- which can be
        # anything a user typed -- are written verbatim onto FP-ROOM-LABELS.
        # The shipped sample's names are all ASCII, so the sample cannot
        # catch this; a non-ASCII room name would raise UnicodeEncodeError
        # at export time on a real plan.
        out.write_text(dxf.dumps(), encoding="utf-8")
        (outdir / f"{lid}.openings.json").write_text(
            json.dumps(sidecar, indent=2), encoding="utf-8")
        result.written.append(out)
        result.summary.append(
            f"level {lid!r}: {n_walls} walls, {len(sidecar)} openings"
            + (f", {n_ann} annotations" if n_ann else "")
            + f" -> {out.name}")
    result.warnings = ctx.warnings
    return result


# --------------------------------------------------------------------------

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("design", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, default=Path("dxf_out"))
    ap.add_argument("--level", action="append", dest="levels",
                    help="emit only this level id (repeatable; also "
                         "unlocks site levels)")
    ap.add_argument("--set", action="append", default=[],
                    metavar="TYPE=INCHES",
                    help="override a default wall thickness, "
                         "e.g. --set exterior=6.5")
    a = ap.parse_args(argv)
    overrides = {}
    for s in a.set:
        k, _, v = s.partition("=")
        if k not in _std_t():
            ap.error(f"unknown wall type {k!r}")
        overrides[k] = float(v)
    a.outdir.mkdir(parents=True, exist_ok=True)
    doc = json.loads(a.design.read_text())
    print(f"fp2dxf: {a.design}")
    result = convert(doc, a.outdir, a.levels, overrides)
    for lid in result.skipped_levels:
        print(f"  - skipping site level {lid!r} (request with --level {lid})")
    for line in result.summary:
        print(f"  {line}")
    for msg in result.warnings:
        print(f"  ! {msg}", file=sys.stderr)


if __name__ == "__main__":
    main()
