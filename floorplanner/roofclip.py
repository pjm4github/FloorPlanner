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
linear interpolation, never sampled.

WHICH SIDE OF THE SEAM A ROOF KEEPS is not "where it is the higher
surface" -- Patrick's own check of the first cut showed why: two roofs of
equal height meeting at an L put roof A's ridge, past the apex, ABOVE
roof B's slope, so the higher-surface rule kept A's whole end and it poked
out through B (his 3D view). The rule is the ruling's own sentence, "a
clipped roof does not extend past the joining roof": a roof STOPS AT THE
SEAM, on the side its own body is on. Concretely each roof's footprint is
one set of convex pieces (its cells outside the overlap, plus the overlap
cells split by the seam), a piece is reachable from another across a
shared boundary UNLESS that boundary is a seam segment, and a roof keeps
what it can reach from its ANCHOR -- the cell holding the ridge endpoint
that is NOT inside the other roof (its far end; both ends, for a roof the
other merely runs into; every outside cell, for a roof neither of whose
ends is inside the other). What a roof cannot reach it gives up: an overlap
piece neither body reaches goes to the roof whose surface is LOWER there
-- the higher surface is precisely the cut-off phantom (the far-side
island under a main roof shows the main; A's end past the apex shows B's
slope) -- and pieces OUTSIDE the overlap that are cut off (A's corner
past the seam) are drawn by nobody -- exactly the lines he erased.

A JOINING END EXTENDS. A roof whose ridge endpoint lies inside the other
roof does not end at its own end edge there: its planes continue past
that edge, inside the other roof, up to the seam -- that is how the outer
corner of an L closes, with a hip from the apex to where the two OUTER
eaves meet, behind the joining roof's nominal end. So for the pair the
joining roof's footprint is extended at that end (only inside the other
roof's own footprint), its eave lines are drawn on into the extension,
and its end line there -- a gable line, or a hip end's eave and hip lines
-- is not drawn at all: the end is joined, not open. The extension is
part of the `RoofClip` (`ext`), derived like everything else.

EVERYTHING IS OUR OWN CONVEX-POLYGON ARITHMETIC, on plain lists of
the editor's point type. A region is a list of convex cells, a point is inside if any
cell holds it, and a drawn line is clipped to the region segment by
segment (Cyrus-Beck), so the paint, the hit shape and the tests all read
the same exact geometry -- no the toolkit's path type booleans, whose results on
touching-edge input are not something this module wants to depend on.
One trap measured while building this, and the reason `footprint_polygon`
returns COPIES: iterating a temporary toolkit polygon yields points that alias
its buffer, and once the polygon is collected those points read whatever
lives there next (another roof's corners, in the run that found it) --
the same class as `fp_extract.py`'s `QImage` buffer trap in CLAUDE.md.

Degenerate pairs -- a cell where the difference is zero everywhere
(coplanar surfaces) -- are not clipped at all and are reported in
`warnings`, `Sheet.warnings`-style (the PDF converter's own honest
fallback): never a crash, never a silent guess.

Scope: roofs on the SAME floor clip each other; nothing else.

QT-FREE (R4e, 0167-report.md sec2): `viewer/fp3d.py` builds the 3D roof
meshes from this same clip, and that file is deliberately free of the Qt
bindings (loaded by path, source-grep-guarded -- CLAUDE.md), so this module
speaks plain points. A point is anything with `.x()` and `.y()` -- the
editor's own point type passes straight in -- and every point this module
CREATES is a `Pt`. `roofs.py` converts back to its own type where it draws.
`RoofGeom` is the Qt-free twin of `RoofItem`'s geometry, built from a
document record, so a document alone (no scene) can be clipped.
"""
import math
from typing import NamedTuple


class Pt:
    """A plain plan point with the editor point type's accessor spelling."""
    __slots__ = ("_x", "_y")

    def __init__(self, x, y=None):
        if y is None:                 # copy-construct from anything point-like
            x, y = x.x(), x.y()
        self._x, self._y = float(x), float(y)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __repr__(self):
        return f"Pt({self._x:.3f}, {self._y:.3f})"

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
    ext: tuple = (0.0, 0.0)     # per-end extension a joining end was given


# ---------------------------------------------------------------------------
# convex polygon tools (a polygon is a list of editor point, any winding)
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
            x = Pt(p.x() + (q.x() - p.x()) * t, p.y() + (q.y() - p.y()) * t)
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


def _split_by_line(poly, a, d):
    """Cut convex `poly` by the infinite line through `a` with direction
    `d`; returns the non-empty pieces (1 or 2)."""
    vals = [(p.x() - a.x()) * d.y() - (p.y() - a.y()) * d.x() for p in poly]
    if all(v >= -EPS for v in vals) or all(v <= EPS for v in vals):
        return [poly]
    left, _ = _clip_by_values(poly, vals)
    right, _ = _clip_by_values(poly, [-v for v in vals])
    return [q for q in (left, right) if len(q) >= 3 and _area(q) > MIN_CELL_AREA]


def _centroid(poly):
    return Pt(sum(p.x() for p in poly) / len(poly),
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
    if len(a) < 3 or len(b) < 3:
        return []
    out = list(a)
    cb = _centroid(b)
    n = len(b)
    for i in range(n):
        if len(out) < 3:
            return []
        out, _ = _clip_by_values(out, _edge_vals(out, b[i], b[(i + 1) % n], cb))
    return out if len(out) >= 3 and _area(out) > MIN_CELL_AREA else []


def _contains(poly, pt, tol: float = 1e-6) -> bool:
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


def _clip_segment(poly, p, q):
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
    return (Pt(p.x() + dx * t0, p.y() + dy * t0),
            Pt(p.x() + dx * t1, p.y() + dy * t1))


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
            mid = Pt((p.x() + q.x()) / 2.0, (p.y() + q.y()) / 2.0)
            if any(_dist_to_segment(mid, y[j], y[(j + 1) % m]) < tol
                   for j in range(m)):
                return True
    return False


class ClipRegion:
    """A visible region as a list of convex cells -- the only geometry
    the item (and fp3d) ever consults: `contains(pt)`, `clip_segment(p,
    q)` for drawing and hit-testing, `cells` themselves for the 3D mesh."""

    def __init__(self, cells):
        self.cells = [list(c) for c in cells if len(c) >= 3]
        self.ext = (0.0, 0.0)

    def contains(self, pt) -> bool:
        return any(_contains(c, pt) for c in self.cells)

    def clip_segment(self, p, q):
        out = []
        for c in self.cells:
            seg = _clip_segment(c, p, q)
            if seg is not None:
                out.append(seg)
        return out

    def area(self) -> float:
        return sum(_area(c) for c in self.cells)


# ---------------------------------------------------------------------------
# a roof's geometry without the scene: the document record's twin
# ---------------------------------------------------------------------------
class RoofGeom:
    """`RoofItem`'s geometry API (`p1`/`p2`, `_axis`, `_eave_ends`,
    `hip_extension`, `length`, the heights and per-side fields) rebuilt
    from a document `roof` record -- so `fp3d.py` can clip a document
    with no scene at all. The formulas are `roofs.py`'s, line for line
    (tests cross-check the two on the same data); `span_in`/`overhang_in`
    accept the pre-R4a bare-number shape the way the loader does."""

    def __init__(self, p1, p2, span_in, overhang_in, ridge_h_in, eaves_h_in,
                 gable=None, name=None):
        # read-only, like RoofItem's: the gate's end-assignment census
        # polices the literal `.p1 =` spelling project-wide
        self._p1, self._p2 = Pt(p1), Pt(p2)
        self.span_in = self._pair(span_in)
        self.overhang_in = self._pair(overhang_in)
        self.ridge_h_in = float(ridge_h_in)
        self.eaves_h_in = float(eaves_h_in)
        self.gable = list(gable) if gable is not None else [True, True]
        self.clip_name = name

    @staticmethod
    def _pair(value):
        if isinstance(value, (list, tuple)):
            return [float(value[0]), float(value[1])]
        return [float(value), float(value)]

    @classmethod
    def from_record(cls, rec, span_fallback=144.0):
        """From a `roof` document record; a pre-R4a record (no `span_in`)
        takes `span_fallback` both sides -- the caller decides what that
        is (fp3d's own nearest-wall search)."""
        ridge = rec["ridge"]
        return cls(Pt(ridge[0][0], ridge[0][1]), Pt(ridge[1][0], ridge[1][1]),
                   rec.get("span_in", span_fallback),
                   rec.get("overhang_in", 0.0) or 0.0,
                   rec.get("ridge_h_in", 132.0), rec.get("eaves_h_in", 96.0),
                   rec.get("gable") or [True, True], rec.get("id"))

    @property
    def p1(self):
        return self._p1

    @property
    def p2(self):
        return self._p2

    def length(self) -> float:
        return math.hypot(self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y())

    def _axis(self):
        dx, dy = self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y()
        ln = math.hypot(dx, dy) or 1.0
        return dx / ln, dy / ln, -dy / ln, dx / ln

    def hip_extension(self, end, gable=None, span=None):
        flags = self.gable if gable is None else gable
        spans = self.span_in if span is None else span
        if flags[end]:
            return 0.0, 0.0
        return ((spans[0] + spans[1]) / 2.0,
                (self.overhang_in[0] + self.overhang_in[1]) / 2.0)

    def _extended_ridge(self, gable=None):
        ux, uy, _, _ = self._axis()
        r1, o1 = self.hip_extension(0, gable)
        r2, o2 = self.hip_extension(1, gable)
        e1, e2 = r1 + o1, r2 + o2
        return (Pt(self.p1.x() - ux * e1, self.p1.y() - uy * e1),
                Pt(self.p2.x() + ux * e2, self.p2.y() + uy * e2))

    def _eave_ends(self):
        _, _, nx, ny = self._axis()
        a1, a2 = self._extended_ridge()
        reach_l = self.span_in[0] + self.overhang_in[0]
        reach_r = self.span_in[1] + self.overhang_in[1]
        return (Pt(a1.x() + nx * reach_l, a1.y() + ny * reach_l),
                Pt(a2.x() + nx * reach_l, a2.y() + ny * reach_l),
                Pt(a1.x() - nx * reach_r, a1.y() - ny * reach_r),
                Pt(a2.x() - nx * reach_r, a2.y() - ny * reach_r))


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


def surface_height(rf, pt) -> float:
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


def footprint_polygon(rf, ext=(0.0, 0.0)):
    """The outer eave rectangle (overhang and hip extensions included) --
    the region the roof paints, and the domain of its surface -- as a
    list of four fresh the editor's point types (module docstring: never points that
    alias a temporary toolkit polygon). `ext` pushes end 0 / end 1 outward
    along the ridge axis (a joining end, module docstring)."""
    e1a, e1b, e2a, e2b = rf._eave_ends()
    ux, uy, _, _ = rf._axis()
    e0, e1 = ext
    return [Pt(e1a.x() - ux * e0, e1a.y() - uy * e0),
            Pt(e1b.x() + ux * e1, e1b.y() + uy * e1),
            Pt(e2b.x() + ux * e1, e2b.y() + uy * e1),
            Pt(e2a.x() - ux * e0, e2a.y() - uy * e0)]


def _diagonal(poly) -> float:
    xs = [p.x() for p in poly]
    ys = [p.y() for p in poly]
    return math.hypot(max(xs) - min(xs), max(ys) - min(ys))


def joining_ext(rf, other_fp):
    """`(e0, e1)`: how far each of `rf`'s ends is extended for the clip --
    far enough to cross the other roof entirely when that ridge endpoint
    lies inside the other's footprint, nothing otherwise."""
    reach = 2.0 * _diagonal(other_fp)
    return tuple(reach if _contains(other_fp, pt) else 0.0
                 for pt in (rf.p1, rf.p2))


def _cut_lines(rf):
    """Lines (point, direction) along which `rf`'s surface changes plane:
    the ridge line, and for each hip end the two equal-height lines where
    the hip plane meets each side plane (through the ridge end; for a
    symmetric roof, exactly the drawn hip lines)."""
    p1, ux, uy, nx, ny = _frame(rf)
    lines = [(Pt(p1), Pt(ux, uy))]
    slope_l, slope_r = _slopes(rf)
    L = rf.length()
    for end in (0, 1):
        run, _ = rf.hip_extension(end)
        if run <= EPS:
            continue
        slope_h = (rf.ridge_h_in - rf.eaves_h_in) / run
        end_pt = Pt(p1.x() + ux * (0.0 if end == 0 else L),
                         p1.y() + uy * (0.0 if end == 0 else L))
        out = -1.0 if end == 0 else 1.0        # "beyond" direction along u
        for sign, slope_s in ((1.0, slope_l), (-1.0, slope_r)):
            if slope_s <= EPS or slope_h <= EPS:
                continue                       # a flat plane: no equal-height line
            # slope_s * |perp| == slope_h * beyond  ->  direction (u: out*slope_s,
            # n: sign*slope_h), any positive scale
            dirx = ux * out * slope_s + nx * sign * slope_h
            diry = uy * out * slope_s + ny * sign * slope_h
            lines.append((Pt(end_pt), Pt(dirx, diry)))
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
        d = Pt(b.x() - a.x(), b.y() - a.y())
        cells = [piece for cell in cells for piece in _split_by_line(cell, a, d)]
    return [c for c in cells if not _contains(overlap, _centroid(c), tol=-1e-6)]


def _reach(start, pieces, allowed, blocked):
    """Indices reachable from `start` across shared boundaries, staying
    inside `allowed` and never crossing a pair in `blocked` (the two
    pieces a seam separates)."""
    reached = set(start)
    frontier = list(start)
    while frontier:
        i = frontier.pop()
        for j in allowed:
            if j in reached or (i, j) in blocked or (j, i) in blocked:
                continue
            if _adjacent(pieces[i], pieces[j]):
                reached.add(j)
                frontier.append(j)
    return reached


def _anchors(rf, other_fp, root_indices, pieces):
    """The pieces a roof keeps FROM (module docstring): the root cells
    holding its ridge endpoints that lie outside the other roof's
    footprint; every root cell when neither end (or both ends) is inside
    the other, or when no root cell holds a far end (numerical edge)."""
    far = [pt for pt in (rf.p1, rf.p2) if not _contains(other_fp, pt)]
    if len(far) != 1:
        return set(root_indices)
    hit = {i for i in root_indices if _contains(pieces[i], far[0], tol=1e-3)}
    return hit or set(root_indices)


def clip_pair(a, b):
    """Clip roof `a` against roof `b` and vice versa. Returns
    `(region_a, region_b, seams, warnings)` where a region is a
    `ClipRegion` (the visible part of that roof's footprint) or None when
    the pair does not interact (no overlap) or is degenerate."""
    fa, fb = footprint_polygon(a), footprint_polygon(b)
    if not _convex_intersection(fa, fb):
        return None, None, [], []
    ext_a, ext_b = joining_ext(a, fb), joining_ext(b, fa)
    fa_ext, fb_ext = footprint_polygon(a, ext_a), footprint_polygon(b, ext_b)
    # the overlap, in three convex parts: both nominal footprints; a's
    # nominal under b's extension; b's nominal under a's extension
    ov_a = _convex_intersection(fa, fb_ext)      # everything of a under b(+ext)
    ov_b = _convex_intersection(fb, fa_ext)      # everything of b under a(+ext)
    overlap = _convex_intersection(fa, fb)
    cells = [c for c in (overlap,
                         _convex_intersection(ov_a, _strip(b, fb, fb_ext)),
                         _convex_intersection(ov_b, _strip(a, fa, fa_ext))) if c]
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

    root_a = _root_cells(fa, ov_a) if ov_a else [list(fa)]
    root_b = _root_cells(fb, ov_b) if ov_b else [list(fb)]
    # one piece list: a's outside cells, b's outside cells, then every
    # overlap piece (ka and kb alike -- both roofs' footprints hold them)
    pieces = list(root_a) + list(root_b) + list(ka_pieces) + list(kb_pieces)
    n_ra, n_rb, n_ka = len(root_a), len(root_b), len(ka_pieces)
    ra_idx = set(range(n_ra))
    rb_idx = set(range(n_ra, n_ra + n_rb))
    ka_idx = set(range(n_ra + n_rb, n_ra + n_rb + n_ka))
    kb_idx = set(range(n_ra + n_rb + n_ka, len(pieces)))
    ov_idx = ka_idx | kb_idx
    blocked = {(n_ra + n_rb + ia, n_ra + n_rb + n_ka + ib) for ia, ib, _ in seam_of}

    # each roof reaches what it can from its anchors, over its own pieces
    reach_a = (_reach(_anchors(a, fb, ra_idx, pieces), pieces, ra_idx | ov_idx, blocked)
               if root_a else set())
    reach_b = (_reach(_anchors(b, fa, rb_idx, pieces), pieces, rb_idx | ov_idx, blocked)
               if root_b else set())

    owner = {}
    for i in ov_idx:
        in_a, in_b = i in reach_a, i in reach_b
        if in_a and not in_b:
            owner[i] = "a"
        elif in_b and not in_a:
            owner[i] = "b"
        elif in_a and in_b:
            owner[i] = "a" if i in ka_idx else "b"   # tie: the higher surface
    # unclaimed overlap pieces -- the far-side island, a's phantom end past
    # the apex, the wedge behind b's end edge -- belong to the roof whose
    # surface is LOWER there: the higher one is exactly the part that was
    # cut off at the seam, and the real roof underneath shows through.
    # (A roof with no body outside the other at all keeps where it is
    # higher instead: a dormer-like roof poking out of a bigger one.)
    for i in ov_idx:
        if i in owner:
            continue
        if not root_a and root_b:
            owner[i] = "a" if i in ka_idx else "b"
        elif not root_b and root_a:
            owner[i] = "a" if i in ka_idx else "b"
        elif not root_a and not root_b:
            owner[i] = "a" if i in ka_idx else "b"
        else:
            owner[i] = "b" if i in ka_idx else "a"

    final_a = ([pieces[i] for i in sorted(reach_a & ra_idx)]
               + [pieces[i] for i in sorted(ov_idx) if owner[i] == "a"])
    final_b = ([pieces[i] for i in sorted(reach_b & rb_idx)]
               + [pieces[i] for i in sorted(ov_idx) if owner[i] == "b"])
    seams = [seg for ia, ib, seg in seam_of
             if owner[n_ra + n_rb + ia] != owner[n_ra + n_rb + n_ka + ib]]
    region_a, region_b = ClipRegion(final_a), ClipRegion(final_b)
    region_a.ext, region_b.ext = ext_a, ext_b
    return region_a, region_b, seams, []


def _strip(rf, fp_nom, fp_ext):
    """The extension of `rf`'s footprint: `fp_ext` minus `fp_nom`, which
    is the union of at most two convex strips (one per extended end).
    Returned as ONE convex polygon when only one end is extended (the
    common case); with both ends extended the two strips are merged into
    their bounding convex hull along the axis, which is the whole
    extended rectangle -- correct, just not minimal."""
    ends_extended = [i for i, e in enumerate(rf_ext_of(fp_nom, fp_ext)) if e > EPS]
    if not ends_extended:
        return []
    if len(ends_extended) == 2:
        return list(fp_ext)
    end = ends_extended[0]
    # strip = the extended rectangle cut off at the nominal end edge
    ux, uy, _, _ = rf._axis()
    edge_a, edge_b = (fp_nom[0], fp_nom[3]) if end == 0 else (fp_nom[1], fp_nom[2])
    d = Pt(edge_b.x() - edge_a.x(), edge_b.y() - edge_a.y())
    pieces = _split_by_line(list(fp_ext), edge_a, d)
    outward = Pt(-ux, -uy) if end == 0 else Pt(ux, uy)
    c_nom = _centroid(fp_nom)
    for piece in pieces:
        c = _centroid(piece)
        if (c.x() - c_nom.x()) * outward.x() + (c.y() - c_nom.y()) * outward.y() > 0 \
                and not _contains(fp_nom, c, tol=-1e-6):
            return piece
    return []


def rf_ext_of(fp_nom, fp_ext):
    """Recover the two end extensions from a nominal and an extended
    footprint (the distance each end edge moved)."""
    return (math.hypot(fp_ext[0].x() - fp_nom[0].x(), fp_ext[0].y() - fp_nom[0].y()),
            math.hypot(fp_ext[1].x() - fp_nom[1].x(), fp_ext[1].y() - fp_nom[1].y()))


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
    exts = {id(rf): [0.0, 0.0] for rf in roofs}
    roofs = list(roofs)
    for i, a in enumerate(roofs):
        for b in roofs[i + 1:]:
            ra, rb, ss, ww = clip_pair(a, b)
            for rf, region in ((a, ra), (b, rb)):
                if region is None:
                    continue
                cur = regions[id(rf)]
                exts[id(rf)] = [max(x, y) for x, y in zip(exts[id(rf)], region.ext, strict=True)]
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
    return {id(rf): RoofClip(regions[id(rf)], seams[id(rf)], warns[id(rf)],
                             tuple(exts[id(rf)]))
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
