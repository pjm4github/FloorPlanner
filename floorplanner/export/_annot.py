#!/usr/bin/env python3
"""The plan's DRAWN dimensions as geometry -- a LEAF shared by `fp2pdf.py`
and `fp2dxf.py`, loaded by each BY PATH (the `_stdt.py` pattern,
0077-ruling.md sec5), never by `import floorplanner...`.

0268 put the drawn dimensions on the PDF; 0285 puts them in the DXF. Both
draw the same thing the screen draws (`annotations.py` DimensionItem):
extension lines off the two measured points, one dimension line offset on
the measured line's left, a slash at each end, the length at the label
point. Kept here once so the two exporters cannot drift apart -- the D73
lesson ("three tables that are synced become three tables that disagree
again").

Standard library only; nothing runs at import beyond defining these."""
import math

#: the screen's own numbers (annotations.py DIM_TICK_IN / DIM_EXT_GAP_IN),
#: in plan inches
DRAWN_TICK_IN = 4.0                   # the "/" slash, half-length
DRAWN_EXT_GAP_IN = 2.0                # the extension line starts this far off the point
DRAWN_OFFSET_IN = 18.0                # a record without `offset_in`


def ftin(v_in: float, dash: bool = True) -> str:
    """246.5 -> 20'-6 1/2\" """
    neg = v_in < 0
    v = abs(v_in)
    whole = math.floor(v + 1e-9)
    frac = v - whole
    sixt = round(frac * 16)
    if sixt == 16:
        whole, sixt = whole + 1, 0
    ft, inch = divmod(whole, 12)
    fs = ""
    if sixt:
        num, den = sixt, 16
        while num % 2 == 0:
            num, den = num // 2, den // 2
        fs = f" {num}/{den}"
    sep = "-" if dash else " "
    s = f"{ft}'{sep}{inch}{fs}\"" if ft else f"{inch}{fs}\""
    return ("-" if neg else "") + s


def _flip(pt):
    """A screen point (y down) in plan coordinates (y up)."""
    return (pt[0], -pt[1])


def dimension_geometry(ann: dict, units: str = "ftin"):
    """One `dimension` annotation record resolved to plan coordinates
    (y up): `line` (the dimension line's two ends), `ext` (two extension
    lines), `slashes` (two), `label`, `label_at`, `rot` (the label's angle,
    degrees CCW, never upside down) and `pts` (every point it reaches, for a
    frame). None for a record without `p2` or of zero length.

    Every point is built in the SCREEN's frame (y down, the offset on the
    measured line's left), then flipped, so the output puts the line on the
    side the plan does."""
    if ann.get("kind") != "dimension" or not ann.get("p2"):
        return None
    ax, ay = float(ann["pos"][0]), float(ann["pos"][1])
    bx, by = float(ann["p2"][0]), float(ann["p2"][1])
    dx, dy = bx - ax, by - ay
    ln = math.hypot(dx, dy)
    if ln < 1e-6:
        return None
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    o = float(ann.get("offset_in", DRAWN_OFFSET_IN))
    t = min(0.95, max(0.05, float(ann.get("label_t", 0.5))))
    px, py = ax + nx * o, ay + ny * o
    qx, qy = bx + nx * o, by + ny * o
    sgn = 1.0 if o >= 0 else -1.0
    ext = []
    for mx, my in ((ax, ay), (bx, by)):
        ext.append(((mx + nx * sgn * DRAWN_EXT_GAP_IN, my + ny * sgn * DRAWN_EXT_GAP_IN),
                    (mx + nx * (o + sgn * DRAWN_TICK_IN), my + ny * (o + sgn * DRAWN_TICK_IN))))
    slashes = []
    for mx, my in ((px, py), (qx, qy)):
        slashes.append(((mx + (ux - nx) * DRAWN_TICK_IN, my + (uy - ny) * DRAWN_TICK_IN),
                        (mx - (ux - nx) * DRAWN_TICK_IN, my - (uy - ny) * DRAWN_TICK_IN)))
    label = f"{round(ln, 2):g}\"" if units == "in" else ftin(ln)
    rot = math.degrees(math.atan2(-uy, ux))
    if rot > 90 or rot <= -90:
        rot += 180
    return {
        "line": (_flip((px, py)), _flip((qx, qy))),
        "ext": [(_flip(a), _flip(b)) for a, b in ext],
        "slashes": [(_flip(a), _flip(b)) for a, b in slashes],
        "label": label,
        "label_at": _flip((px + (qx - px) * t, py + (qy - py) * t)),
        "rot": rot,
        "pts": [_flip((px, py)), _flip((qx, qy)), _flip((ax, ay)), _flip((bx, by))],
    }
