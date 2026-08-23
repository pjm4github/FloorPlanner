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
}

ROOM_LABEL_H = 8.0   # text height, inches
NOTE_H = 4.0


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
             s: str, rot: float = 0.0) -> None:
        g = self._g
        self._ent.append(
            g(0, "TEXT") + g(8, layer)
            + g(10, x) + g(20, y) + g(30, 0.0)
            + g(40, h) + g(1, s) + g(50, rot))

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
        # conventional door symbol (leaf + swing arc): Chief's CAD to
        # Walls classifies openings by symbol shape -- bare gap lines
        # read as a WINDOW, so doors need the leaf/arc to be doors.
        op = sp.opening
        hinge = op.get("hinge")
        swing = op.get("swings_toward")
        sliding = op["kind"] == "door" and op.get("door_type") == "sliding"
        if op["kind"] in ("door", "gate") and not sliding:
            # No hinge/swing recorded -> still draw a symbol with a
            # DEFAULT handedness (hinge:v1, swing:left) so Chief
            # classifies it as a DOOR; handedness is a QC fix, the
            # object class is not.
            if hinge not in ("v1", "v2"):
                hinge = "v1"
            if swing not in ("left", "right"):
                swing = "left"
            w = sp.s1 - sp.s0
            s_h = sp.s0 if hinge == "v1" else sp.s1
            s_j = sp.s1 if hinge == "v1" else sp.s0
            hx, hy = p1[0] + ux * s_h, p1[1] + uy * s_h   # hinge, centerline
            jx, jy = p1[0] + ux * s_j, p1[1] + uy * s_j   # jamb
            # Qt 'left' of v1->v2 maps to geometric CCW-left in DXF
            # under the y-flip, so the sign convention carries over.
            sgn = 1.0 if swing == "left" else -1.0
            lx, ly = hx + nx * w * sgn, hy + ny * w * sgn  # leaf tip
            dxf.line(op_layer, hx, hy, lx, ly)             # leaf
            a_leaf = math.degrees(math.atan2(ly - hy, lx - hx))
            a_jamb = math.degrees(math.atan2(jy - hy, jx - hx))
            if (a_leaf - a_jamb) % 360.0 <= 180.0:         # CCW 90-deg sweep
                dxf.arc(op_layer, hx, hy, w, a_jamb, a_leaf)
            else:
                dxf.arc(op_layer, hx, hy, w, a_leaf, a_jamb)
        elif sliding:
            # slider: two overlapping half-width panels on the centerline
            w = sp.s1 - sp.s0
            for k, side in ((0, +1.0), (1, -1.0)):
                a = sp.s0 + k * w * 0.45
                b = a + w * 0.55
                ox, oy = nx * 0.75 * side, ny * 0.75 * side
                dxf.line(op_layer,
                         p1[0] + ux * a + ox, p1[1] + uy * a + oy,
                         p1[0] + ux * b + ox, p1[1] + uy * b + oy)

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


def convert(doc: dict, outdir: Path, only_levels=None,
            thickness_overrides=None) -> ConvertResult:
    if doc.get("format") != "floorplanner-design" or doc.get("version") != 5:
        # A NORMAL EXCEPTION, NOT `raise SystemExit` (0038-ruling.md SS4):
        # this is a library call from a Qt menu handler as well as the CLI,
        # and an unhandled exception inside a Qt override presents as a
        # segfault with no traceback (SESSION_SNAPSHOT SS5) -- but at least
        # THAT is catchable. `SystemExit` inside a Qt call stack is not
        # something a `try/except Exception` around the menu action would
        # even see coming.
        raise ValueError("not a floorplanner-design v5 document")
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
        for ann in doc.get("annotations", []) or []:
            if ann["level"] == lid and ann["kind"] == "text" and ann.get("text"):
                p = (float(ann["pos"][0]), -float(ann["pos"][1]))
                dxf.text("FP-NOTES", p[0], p[1], NOTE_H,
                         ann["text"], -float(ann.get("rotation", 0)))

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
            f"level {lid!r}: {n_walls} walls, {len(sidecar)} openings "
            f"-> {out.name}")
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
