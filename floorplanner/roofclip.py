"""R4d (0164-ruling.md): roof intersection clipping -- the valley seam.

A PURE FUNCTION of the roofs (sec1): nothing here is stored, the roof's own
rectangle stays the document's truth, and the clip is recomputed whenever
any roof changes. Needs no scene -- `compute_roof_clips` takes the live
`RoofItem`s (or anything with their geometry API) and returns, per roof,
the region of its own footprint that is actually visible from above, the
seam segments where its surface meets another's at equal height, and any
warning that made it give up on a pair.

THE GEOMETRY (sec2). Each roof is a piecewise-planar surface over its
footprint: two side planes off the ridge, plus a hip plane past a hip end.
Two such surfaces meet along the equal-height locus, and because both are
planar within a cell the locus is a straight segment there -- so the
overlap of the two footprints is cut into convex cells by every line along
which either surface changes plane (each ridge line, each hip end's two
equal-height lines), and inside a cell the height DIFFERENCE is linear:
the seam is where it crosses zero on the cell's edges, found by exact
linear interpolation, never sampled. A roof keeps the part of a cell where
it is the higher surface; the part where it is lower lies under the other
roof and is dropped. Then the connected-component rule: a kept piece that
no longer touches the roof's own body outside the overlap (the wing poking
out the FAR side of the main roof, where the main's far slope has dropped
below the wing again) is dropped too -- "a clipped roof does not extend
past the joining roof" -- and the other roof shows through it.

EVERYTHING IS OUR OWN CONVEX-POLYGON ARITHMETIC, on plain lists of
`QPointF`. A region is a list of convex cells, a point is inside if any
cell holds it, and a drawn line is clipped to the region segment by
segment (Cyrus-Beck), so the paint, the hit shape and the tests all read
the same exact geometry -- no `QPainterPath` booleans, whose results on
touching-edge input are not something this module wants to depend on.
One trap measured while building this, and the reason `footprint_polygon`
returns COPIES: iterating a temporary `QPolygonF` yields points that alias
its buffer, and once the polygon is collected those points read whatever
lives there next (another roof's corners, in the run that found it) --
the same class as `fp_extract.py`'s `QImage` buffer trap in CLAUDE.md.

Degenerate pairs -- a cell where the difference is zero everywhere
(coplanar surfaces) -- are not clipped at all and are reported in
`warnings`, `Sheet.warnings`-style (the PDF converter's own honest
fallback): never a crash, never a silent guess.

Scope: roofs on the SAME floor clip each other; nothing else.
"""
import math
from typing import NamedTuple

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainterPath, QPolygonF

EPS = 1e-6            # inches / height units: "equal" for seam and degeneracy
MIN_CELL_AREA = 1e-3  # a sliver below this is float noise, not a cell


class RoofClip(NamedTuple):
    """One roof's clip: `region` is the visible part of its footprint (a
    `ClipRegion`; None = unclipped, draw everything); `seams` are solid
    seam segments to draw; `warnings` name any pair this roof could not
    be clipped against."""
    region: object
    seams: list
    warnings: list


# ---------------------------------------------------------------------------
# convex polygon tools (a polygon is a list of QPointF, any winding)
# ---------------------------------------------------------------------------
def _area(poly) -> float:
    n = len(poly)
    return abs(sum(poly[i].x() * poly[(i + 1) % n].y()
                   - poly[(i + 1) % n].x() * poly[i].y() for i in range(n))) / 2.0


def _clip_by_values(poly, vals):
    """Keep the part of convex `poly` where the (linear) function with the
    given vertex values is >= 0 -- Sutherland-Hodgman against a value
    field, the crossing found by exact interpolation. Returns (kept
    polygon, crossing points in order)."""
    kept, crossings = [], []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        vp, vq = vals[i], vals[(i + 1) % n]
        if vp >= 0:
            kept.append(p)
        if (vp < 0) != (vq < 0) and abs(vp - vq) > EPS:
            t = vp / (vp - vq)
            x = QPointF(p.x() + (q.x() - p.x()) * t, p.y() + (q.y() - p.y()) * t)
            kept.append(x)
            crossings.append(x)
    # a crossing that lands on a kept vertex (a value exactly 0) would
    # list that point twice -- drop consecutive duplicates
    clean = []
    for p in kept:
        if not clean or abs(p.x() - clean[-1].x()) > EPS or abs(p.y() - clean[-1].y()) > EPS:
            clean.append(p)
    if (len(clean) > 1 and abs(clean[0].x() - clean[-1].x()) <= EPS
            and abs(clean[0].y() - clean[-1].y()) <= EPS):
        clean.pop()
    return clean, crossings


def _split_by_line(poly, a: QPointF, d: QPointF):
    """Cut convex `poly` by the infinite line through `a` with direction
    `d`; returns the non-empty pieces (1 or 2)."""
    vals = [(p.x() - a.x()) * d.y() - (p.y() - a.y()) * d.x() for p in poly]
    if all(v >= -EPS for v in vals) or all(v <= EPS for v in vals):
        return [poly]
    left, _ = _clip_by_values(poly, vals)
    right, _ = _clip_by_values(poly, [-v for v in vals])
    return [q for q in (left, right) if len(q) >= 3 and _area(q) > MIN_CELL_AREA]


def _centroid(poly) -> QPointF:
    return QPointF(sum(p.x() for p in poly) / len(poly),
                   sum(p.y() for p in poly) / len(poly))


def _edge_vals(poly, a, b, inside_pt):
    """Signed distances of `poly`'s vertices to the line a-b, oriented so
    that `inside_pt` is positive."""
    dx, dy = b.x() - a.x(), b.y() - a.y()

    def f(p):
        return (p.x() - a.x()) * dy - (p.y() - a.y()) * dx
    sign = 1.0 if f(inside_pt) >= 0 else -1.0
    return [sign * f(p) for p in poly]


def _convex_intersection(a, b):
    """a ∩ b for convex polygons: clip `a` against every edge of `b`."""
    out = list(a)
    cb = _centroid(b)
    n = len(b)
    for i in range(n):
        if len(out) < 3:
            return []
        out, _ = _clip_by_values(out, _edge_vals(out, b[i], b[(i + 1) % n], cb))
    return out if len(out) >= 3 and _area(out) > MIN_CELL_AREA else []


def _contains(poly, pt: QPointF, tol: float = 1e-6) -> bool:
    """Point in convex polygon; `tol` > 0 is boundary-inclusive, < 0
    strictly interior by that margin."""
    n = len(poly)
    c = _centroid(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b.x() - a.x(), b.y() - a.y()
        ln = math.hypot(dx, dy)
        if ln < EPS:
            continue
        f_pt = ((pt.x() - a.x()) * dy - (pt.y() - a.y()) * dx) / ln
        f_c = ((c.x() - a.x()) * dy - (c.y() - a.y()) * dx) / ln
        if f_c >= 0 and f_pt < -tol:
            return False
        if f_c < 0 and f_pt > tol:
            return False
    return True


def _clip_segment(poly, p: QPointF, q: QPointF):
    """The part of segment p-q inside convex `poly` (Cyrus-Beck), or None."""
    t0, t1 = 0.0, 1.0
    c = _centroid(poly)
    n = len(poly)
    dx, dy = q.x() - p.x(), q.y() - p.y()
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b.x() - a.x(), b.y() - a.y()
        sign = 1.0 if ((c.x() - a.x()) * ey - (c.y() - a.y()) * ex) >= 0 else -1.0
        fp = sign * ((p.x() - a.x()) * ey - (p.y() - a.y()) * ex)
        fd = sign * (dx * ey - dy * ex)
        if abs(fd) < EPS:
            if fp < -EPS:
                return None
            continue
        t = -fp / fd
        if fd > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1 + EPS:
            return None
    if t1 - t0 < EPS:
        return None
    return (QPointF(p.x() + dx * t0, p.y() + dy * t0),
            QPointF(p.x() + dx * t1, p.y() + dy * t1))


def _dist_to_segment(p, a, b) -> float:
    abx, aby = b.x() - a.x(), b.y() - a.y()
    L2 = abx * abx + aby * aby
    if L2 < EPS:
        return math.hypot(p.x() - a.x(), p.y() - a.y())
    t = max(0.0, min(1.0, ((p.x() - a.x()) * abx + (p.y() - a.y()) * aby) / L2))
    return math.hypot(p.x() - (a.x() + abx * t), p.y() - (a.y() + aby * t))


def _adjacent(a, b, tol: float = 1e-5) -> bool:
    """Two cells share a boundary segment of positive length: the
    midpoint of some edge of one lies on an edge of the other (either
    way round -- a short edge against a long one counts). Vertex counting
    is NOT enough: two cells can share exactly one corner and nothing
    else, and the crossing-point bookkeeping can list a vertex twice."""
    for x, y in ((a, b), (b, a)):
        n, m = len(x), len(y)
        for i in range(n):
            p, q = x[i], x[(i + 1) % n]
            if math.hypot(q.x() - p.x(), q.y() - p.y()) < tol:
                continue
            mid = QPointF((p.x() + q.x()) / 2.0, (p.y() + q.y()) / 2.0)
            if any(_dist_to_segment(mid, y[j], y[(j + 1) % m]) < tol
                   for j in range(m)):
                return True
    return False


class ClipRegion:
    """A visible region as a list of convex cells -- the only geometry
    the item ever consults: `contains(pt)`, `clip_segment(p, q)` for
    drawing and hit-testing, `path()` for anything that wants a
    `QPainterPath` (winding fill, so adjacent cells read as one area)."""

    def __init__(self, cells):
        self.cells = [list(c) for c in cells if len(c) >= 3]

    def contains(self, pt: QPointF) -> bool:
        return any(_contains(c, pt) for c in self.cells)

    def clip_segment(self, p: QPointF, q: QPointF):
        out = []
        for c in self.cells:
            seg = _clip_segment(c, p, q)
            if seg is not None:
                out.append(seg)
        return out

    def area(self) -> float:
        return sum(_area(c) for c in self.cells)

    def path(self) -> QPainterPath:
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        for c in self.cells:
            path.addPolygon(QPolygonF(c))
            path.closeSubpath()
        return path


# ---------------------------------------------------------------------------
# the surface
# ---------------------------------------------------------------------------
def _frame(rf):
    ux, uy, nx, ny = rf._axis()
    return rf.p1, ux, uy, nx, ny


def _slopes(rf):
    rise = rf.ridge_h_in - rf.eaves_h_in
    sl, sr = rf.span_in
    return (rise / sl if sl > EPS else 0.0), (rise / sr if sr > EPS else 0.0)


def surface_height(rf, pt: QPointF) -> float:
    """The roof surface's height at plan point `pt` -- the level-base datum
    every roof height uses. Valid over the footprint; outside it the side
    planes simply continue (callers never ask there)."""
    p1, ux, uy, nx, ny = _frame(rf)
    dx, dy = pt.x() - p1.x(), pt.y() - p1.y()
    along = dx * ux + dy * uy
    perp = dx * nx + dy * ny
    slope_l, slope_r = _slopes(rf)
    h = rf.ridge_h_in - (slope_l if perp >= 0 else slope_r) * abs(perp)
    L = rf.length()
    for end, beyond in ((0, -along), (1, along - L)):
        if beyond > 0:
            run, _ = rf.hip_extension(end)
            if run > EPS:
                h = min(h, rf.ridge_h_in - (rf.ridge_h_in - rf.eaves_h_in)
                        / run * beyond)
    return h


def footprint_polygon(rf):
    """The outer eave rectangle (overhang and hip extensions included) --
    the region the roof paints, and the domain of its surface -- as a
    list of four fresh `QPointF`s (module docstring: never points that
    alias a temporary `QPolygonF`)."""
    e1a, e1b, e2a, e2b = rf._eave_ends()
    return [QPointF(e1a), QPointF(e1b), QPointF(e2b), QPointF(e2a)]


def _cut_lines(rf):
    """Lines (point, direction) along which `rf`'s surface changes plane:
    the ridge line, and for each hip end the two equal-height lines where
    the hip plane meets each side plane (through the ridge end; for a
    symmetric roof, exactly the drawn hip lines)."""
    p1, ux, uy, nx, ny = _frame(rf)
    lines = [(QPointF(p1), QPointF(ux, uy))]
    slope_l, slope_r = _slopes(rf)
    L = rf.length()
    for end in (0, 1):
        run, _ = rf.hip_extension(end)
        if run <= EPS:
            continue
        slope_h = (rf.ridge_h_in - rf.eaves_h_in) / run
        end_pt = QPointF(p1.x() + ux * (0.0 if end == 0 else L),
                         p1.y() + uy * (0.0 if end == 0 else L))
        out = -1.0 if end == 0 else 1.0        # "beyond" direction along u
        for sign, slope_s in ((1.0, slope_l), (-1.0, slope_r)):
            if slope_s <= EPS or slope_h <= EPS:
                continue                       # a flat plane: no equal-height line
            # slope_s * |perp| == slope_h * beyond  ->  direction (u: out*slope_s,
            # n: sign*slope_h), any positive scale
            dirx = ux * out * slope_s + nx * sign * slope_h
            diry = uy * out * slope_s + ny * sign * slope_h
            lines.append((QPointF(end_pt), QPointF(dirx, diry)))
    return lines


# ---------------------------------------------------------------------------
# a pair, then the whole floor
# ---------------------------------------------------------------------------
def _root_cells(footprint, overlap):
    """`footprint` minus the convex `overlap`, as convex cells: split the
    footprint by each overlap edge line and keep the cells whose centroid
    is outside the overlap."""
    cells = [list(footprint)]
    n = len(overlap)
    for i in range(n):
        a, b = overlap[i], overlap[(i + 1) % n]
        d = QPointF(b.x() - a.x(), b.y() - a.y())
        cells = [piece for cell in cells for piece in _split_by_line(cell, a, d)]
    return [c for c in cells if not _contains(overlap, _centroid(c), tol=-1e-6)]


def _connected(pieces, roots):
    """Indices of `pieces` reachable from any root cell through shared
    edges (BFS). With no roots at all (a roof wholly inside the other),
    every piece counts."""
    if not roots:
        return set(range(len(pieces)))
    reached = {i for i, p in enumerate(pieces) if any(_adjacent(p, r) for r in roots)}
    frontier = list(reached)
    while frontier:
        i = frontier.pop()
        for j, p in enumerate(pieces):
            if j not in reached and _adjacent(pieces[i], p):
                reached.add(j)
                frontier.append(j)
    return reached


def clip_pair(a, b):
    """Clip roof `a` against roof `b` and vice versa. Returns
    `(region_a, region_b, seams, warnings)` where a region is a
    `ClipRegion` (the visible part of that roof's footprint) or None when
    the pair does not interact (no overlap) or is degenerate."""
    fa, fb = footprint_polygon(a), footprint_polygon(b)
    overlap = _convex_intersection(fa, fb)
    if not overlap:
        return None, None, [], []
    cells = [overlap]
    for pt, d in _cut_lines(a) + _cut_lines(b):
        cells = [piece for cell in cells for piece in _split_by_line(cell, pt, d)]

    # per cell: the piece where a is higher, the piece where b is, the seam
    ka_pieces, kb_pieces, seam_of = [], [], []
    for cell in cells:
        vals = [surface_height(a, p) - surface_height(b, p) for p in cell]
        if all(abs(v) <= EPS for v in vals):
            return None, None, [], [
                f"roofs {_name(a)} and {_name(b)} share a coplanar surface "
                f"-- drawn unclipped"]
        ka, cross = _clip_by_values(cell, vals)
        kb, _ = _clip_by_values(cell, [-v for v in vals])
        ia = ib = None
        if len(ka) >= 3 and _area(ka) > MIN_CELL_AREA:
            ka_pieces.append(ka)
            ia = len(ka_pieces) - 1
        if len(kb) >= 3 and _area(kb) > MIN_CELL_AREA:
            kb_pieces.append(kb)
            ib = len(kb_pieces) - 1
        if len(cross) == 2 and ia is not None and ib is not None:
            seam_of.append((ia, ib, (cross[0], cross[1])))

    root_a, root_b = _root_cells(fa, overlap), _root_cells(fb, overlap)
    # a's islands go to b, b's islands go to a; repeat until stable
    own_a = set(range(len(ka_pieces)))
    own_b = set(range(len(kb_pieces)))
    extra_a, extra_b = [], []          # pieces inherited from the other's islands
    for _ in range(3):
        idx_a = sorted(own_a)
        keep_a = _connected([ka_pieces[i] for i in idx_a] + extra_a, root_a)
        dropped_a = [i for k, i in enumerate(idx_a) if k not in keep_a]
        idx_b = sorted(own_b)
        keep_b = _connected([kb_pieces[i] for i in idx_b] + extra_b, root_b)
        dropped_b = [i for k, i in enumerate(idx_b) if k not in keep_b]
        if not dropped_a and not dropped_b:
            break
        own_a -= set(dropped_a)
        own_b -= set(dropped_b)
        extra_b += [ka_pieces[i] for i in dropped_a]
        extra_a += [kb_pieces[i] for i in dropped_b]

    final_a = [ka_pieces[i] for i in sorted(own_a)] + extra_a
    final_b = [kb_pieces[i] for i in sorted(own_b)] + extra_b
    seams = [seg for ia, ib, seg in seam_of if ia in own_a and ib in own_b]
    return (ClipRegion(root_a + final_a), ClipRegion(root_b + final_b),
            seams, [])


def _name(rf) -> str:
    return getattr(rf, "clip_name", None) or f"ridge {rf.p1.x():.0f},{rf.p1.y():.0f}"


def compute_roof_clips(roofs) -> dict:
    """Every pairwise clip among `roofs` (all on one floor), folded per
    roof: with more than one partner a roof's region is what every
    partner leaves it -- the cells of one partner's region clipped
    against the other's (convex ∩ convex, exact); seams and warnings
    accumulate. A roof no pair touched maps to `RoofClip(None, [], [])`."""
    regions = {id(rf): None for rf in roofs}
    seams = {id(rf): [] for rf in roofs}
    warns = {id(rf): [] for rf in roofs}
    roofs = list(roofs)
    for i, a in enumerate(roofs):
        for b in roofs[i + 1:]:
            ra, rb, ss, ww = clip_pair(a, b)
            for rf, region in ((a, ra), (b, rb)):
                if region is None:
                    continue
                cur = regions[id(rf)]
                if cur is None:
                    regions[id(rf)] = region
                else:
                    pieces = []
                    for c1 in cur.cells:
                        for c2 in region.cells:
                            piece = _convex_intersection(c1, c2)
                            if piece:
                                pieces.append(piece)
                    regions[id(rf)] = ClipRegion(pieces)
                seams[id(rf)].extend(ss)
            if ww:
                warns[id(a)].extend(ww)
                warns[id(b)].extend(ww)
    return {id(rf): RoofClip(regions[id(rf)], seams[id(rf)], warns[id(rf)])
            for rf in roofs}


def seam_heights(a, b, seams):
    """For a receipt: `[(h_a, h_b), ...]` at every seam vertex -- each pair
    must agree to within EPS (0164-ruling.md sec3: z1 == z2 exactly)."""
    out = []
    for p, q in seams:
        for pt in (p, q):
            out.append((surface_height(a, pt), surface_height(b, pt)))
    return out


def seam_length(seams) -> float:
    return sum(math.hypot(q.x() - p.x(), q.y() - p.y()) for p, q in seams)
