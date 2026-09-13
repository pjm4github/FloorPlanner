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
MIN_CELL_AREA = 1e-3  # a sliver below this is float noise from the exact
                      # geometric construction itself -- not a cell at all
# a MULTI-COVERER cell this small is exact, real geometry (several
# near-parallel seam lines can legitimately converge on a tiny patch near
# a complex junction) -- but drawn on its own, its skirt (perimeter times
# height-drop, not footprint area) can read as a visible fin next to the
# surfaces around it. `compute_roof_clips` folds a cell this small into
# its own next-best coverer instead -- see the sliver fold-in there.
SLIVER_AREA_IN = 2.0


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


def _segments_cross(a1, a2, b1, b2):
    """The point where segments a1-a2 and b1-b2 cross, or None (parallel,
    or meeting outside either segment). Touching at an endpoint counts
    as a crossing at that point -- the caller measures how far past it
    an end lies."""
    dax, day = a2.x() - a1.x(), a2.y() - a1.y()
    dbx, dby = b2.x() - b1.x(), b2.y() - b1.y()
    den = dax * dby - day * dbx
    if abs(den) < EPS:
        return None
    rx, ry = b1.x() - a1.x(), b1.y() - a1.y()
    t = (rx * dby - ry * dbx) / den
    u = (rx * day - ry * dax) / den
    if t < -1e-9 or t > 1 + 1e-9 or u < -1e-9 or u > 1 + 1e-9:
        return None
    return Pt(a1.x() + dax * t, a1.y() + day * t)


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
                 gable=None, name=None, marker_end=1):
        # read-only, like RoofItem's: the gate's end-assignment census
        # polices the literal `.p1 =` spelling project-wide
        self._p1, self._p2 = Pt(p1), Pt(p2)
        self.span_in = self._pair(span_in)
        self.overhang_in = self._pair(overhang_in)
        self.ridge_h_in = float(ridge_h_in)
        self.eaves_h_in = float(eaves_h_in)
        self.gable = list(gable) if gable is not None else [True, True]
        self.clip_name = name
        # R4g (0177-ruling.md sec1): the reachability fallback anchor for a
        # roof with no single-coverage ground of its own -- `roofs.py`'s
        # own end-index convention, 0 = p1, 1 = p2
        self.marker_end = 1 if marker_end else 0

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
                   rec.get("gable") or [True, True], rec.get("id"),
                   rec.get("marker_end", 1))

    def marker_pt(self):
        return self.p2 if self.marker_end else self.p1

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


def _reach(start, pieces, allowed, blocked, no_step=None):
    """Indices reachable from `start` across shared boundaries, staying
    inside `allowed` and never crossing a pair in `blocked` (the two
    pieces a seam separates); `no_step(i, j)`, when given, vetoes the
    directed step i -> j (a joining end's extension climbing back above
    its host -- `compute_roof_clips`)."""
    reached = set(start)
    frontier = list(start)
    while frontier:
        i = frontier.pop()
        for j in allowed:
            if j in reached or (i, j) in blocked or (j, i) in blocked:
                continue
            if no_step is not None and no_step(i, j):
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


def compute_roof_clips(roofs, diag=None) -> dict:
    """Every roof on one floor, clipped against every other AT ONCE, from a
    SINGLE shared 2D arrangement -- 0170-ruling.md sec2 (visibility as the
    upper envelope of every roof surface on the level), rebuilt properly
    after his own report that the pairwise-composed version (every fix
    through 0173-report.md) still left a real crack at a genuine 3-way
    junction: two roofs' own SEPARATELY-computed local decompositions can
    each place "the same" boundary vertex a hair apart in floating point,
    because nothing ever forced them to agree on one. The published,
    standard technique for exactly this problem (CGAL's `Envelope_3`
    package; the same idea underlies BSP-tree solid merging and the
    straight-skeleton roof algorithm) is to build the whole cell
    decomposition ONCE, from every surface's own geometry at once, so two
    surfaces meeting at a corner are FORCED to share the identical vertex
    -- not merely land close to it.

    THE ARRANGEMENT. Coplanar pairs are found and excluded first, exactly
    as before (both roofs left entirely unclipped, with a warning -- there
    is no seam locus to build where two surfaces coincide). Every
    remaining roof that overlaps at least one other ("live") gets its
    ridge ends extended toward whichever neighbour(s) swallow them
    (`joining_ext`'s own per-pair reach, twice that neighbour's diagonal,
    generalised so an end swallowed by SEVERAL neighbours at once reaches
    past the largest). The shared cut set is the UNION, over every live
    roof, of its own plane-change lines (`_cut_lines`: the ridge, any hip
    end's equal-height lines) AND its own extended footprint's four edges
    -- the footprint edges matter as much as the plane lines, since
    without them a cell could straddle a roof's own boundary and its
    "coverers" would not stay constant across it. Every live roof's own
    extended footprint is then split by every line in that ONE shared
    set, and the resulting cells (duplicated once per starting footprint
    wherever two roofs' rectangles physically overlap) are deduplicated
    by vertex set -- two separately-produced but geometrically identical
    pieces become the one true cell, at one set of vertices, that every
    affected roof's region and seams are built from. This is the
    structural fix: a physical location is decomposed exactly once, never
    once per pair.

    OWNERSHIP, PER CELL. A cell's "coverers" are the live roofs whose
    extended footprint contains it. One coverer: that roof keeps it
    outright. Several: each coverer's own local piece is found by
    clipping the cell, in turn, against every OTHER coverer's height
    there (`_clip_by_values`, chained -- affine differences, so the cut
    is exact) -- the surviving sub-piece for roof i is `{p : h_i(p) >=
    h_j(p) for every other coverer j}`, i.e. i's local maximum. Two
    adjacent sub-pieces from the same cell, split at their shared
    crossing, are a SEAM CANDIDATE, recorded against their own exact
    piece indices -- never re-matched by midpoint afterward, which risks
    the wrong same-owner piece when several sit near one boundary.

    REACHABILITY is the one rule plain "highest wins" does not give for
    free, and the reason this is closer to a CSG union of BOUNDED roof
    volumes than to an envelope of unbounded planes. Patrick's own check
    of R4d's first cut is the proof: at an equal-height L, roof A's ridge
    past the apex is numerically ABOVE roof B's slope there, yet the
    ruling is that A must stop at the seam anyway -- a roof's real body
    ends where its own construction ends, and a plane extended past that
    is a phantom, not a roof. So each live roof keeps only the
    local-maximum pieces reachable, by shared boundary, from its own
    ANCHOR.

    THE ANCHOR (0177-ruling.md sec1, correcting 0176's own first cut,
    which this fixture itself refuted): NOT "whichever ridge end is not
    swallowed by any other live roof" -- his own three-ridge fixture has
    a roof (rf1) BOTH of whose ends are locally the highest surface, yet
    the piece past one of them must still die, because that ground is
    reachable from the other end's real body only through a single POINT
    (a ridge-ridge crossing, a four-wedge saddle where the two equal-
    height lines cross and the far wedge touches the near one at that one
    vertex only) -- connectivity requires a shared boundary of POSITIVE
    LENGTH, so a vertex-only touch connects nothing, by the same
    `_adjacent` rule every other reachability step already uses. The
    anchor is instead THE COMPONENT HOLDING THE ROOF'S OWN SINGLE-
    COVERAGE GROUND -- territory no other live roof's candidacy reaches
    at all (`coverer_rank is None`, the one-coverer "root" case): that
    ground is unambiguously the roof's own, so whatever it connects to,
    by positive-length boundary, is real body too. A roof with NO single-
    coverage ground of its own (wholly inside another's candidacy) has no
    such root to start from, and anchors instead at the piece holding its
    `marker_end` -- the one ridge endpoint a person or the loader already
    identified as this roof's own reference end, `roofs.py`'s own R2b
    convention, reused here as the fallback because nothing GEOMETRIC
    distinguishes such a roof's two ends the way single-coverage ground
    does for every other one.

    PRUNE AND RE-ENVELOPE (0179-ruling.md sec2, replacing this module's
    first cut -- 0178-report.md's own rank-walking fallback, which handed
    an orphaned piece to "the next-ranked OTHER coverer bordering claimed
    territory", a fixed order computed ONCE against the ORIGINAL full
    coverer set). Ruled wrong for the reason a fixed rank order cannot
    fix: when a piece's true local-max owner is pruned, the ground does
    not "fall" to whoever was second in a ranking taken before the prune
    -- it is re-contested from scratch by whoever remains, and the second-
    ranked candidate at the ORIGINAL three-way comparison is not
    necessarily the winner of the resulting TWO-way one (the h_i==h_j
    crossing between the survivors can fall anywhere in the piece, not
    coincide with where the original loser's height happened to rank).
    So candidacy per cell is no longer fixed after the first pass: each
    round rebuilds the local-maximum envelope (the SAME per-cell chained
    clip described above) using only that cell's currently ACTIVE
    coverers; anchors and reach are then recomputed on THIS round's
    result; a piece whose owner cannot reach it prunes that owner from
    the piece's OWN ground (the cell splits into the round's pieces
    first, so a roof never loses a whole cell for one lost sub-piece);
    and the next round re-envelopes among whoever is left. This repeats
    to a fixed point -- every round that changes anything strictly
    shrinks some cell's active set, and the cells come from a finite
    arrangement. A cell whose EVERY coverer has been pruned draws for
    nobody -- the only way ground goes undrawn, matching the two-roof
    "corner past the seam" D85 already requires (there, the sole
    candidate prunes itself and nothing remains) as the n=2 case of the
    same one rule, rather than a special case of it.

    "ROOT" (single-coverage, anchor-eligible) ground is a property of the
    ORIGINAL candidacy alone, fixed before any pruning -- a cell that
    becomes single-active-coverer only THROUGH pruning is an ordinary,
    unconditional win for whoever is left (nobody else contests it any
    longer), not a newly-anchoring root; conflating the two would let a
    roof bootstrap an anchor from ground it never held independently.

    WHAT A ROOF MUST GIVE UP, AND WHAT IT MERELY CANNOT REACH YET
    (0181-ruling.md sec2, and the fixture measurements in the fixed-point
    comments below). A cut-off component of a roof's own pieces is one
    of three things. A PHANTOM holds a swallowed ridge end that has
    CROSSED a host's ridge -- the joining end's overshoot (A's wedge past
    the apex with the D85 corner behind it; rf1 east of the pinch): it
    prunes, and never comes back. A ROOT LIMB holds the roof's own
    single-coverage ground and no such end (rf3's whole rake-side body,
    a roof with free ends passing across others): it certifies iff it
    connects to the principal anchor through the roof's CONTINUITY
    NETWORK -- its own reached pieces plus every piece where its surface
    lies BELOW a real roof's drawn one, passing under; ground where it
    would stand ABOVE the drawn surface is phantom air and conducts
    nothing, a point contact conducts nothing. A certified limb anchors
    a walk of its own and draws wherever it wins; hidden ground conducts
    connectivity but never draws; an uncertified limb prunes with
    everything only it could reach, and its root ground is the ONE place
    blank ground is legal. Anything else cut off is an ORPHAN, judged
    only once no phantom remains anywhere -- whatever still cuts it off
    then is a real roof, and it prunes. Phantoms prune one at a time,
    the shorter overshoot first, so a join whose far arm was severed by
    nothing but another roof's phantom is judged on the re-enveloped
    ground; and a joining end's extension strip may pass from above its
    host to below, never back up.

    SEAMS are drawn from the SAME arrangement, read off the FINAL
    (converged) round only: a seam candidate is real iff both sides it
    separates are still active coverers of that cell when the fixed point
    is reached -- no separate post-hoc filtering against a third roof's
    height is needed, because each round's local partition already
    accounts for every one of that round's actual coverers, not just a
    pair considered in isolation.

    Two live roofs reduce to exactly the same natural overlap boundary
    `clip_pair` computes for a pair on its own -- the extra footprint-edge
    cuts this construction adds coincide with the corners `clip_pair`'s
    own overlap-region construction already has for exactly two roofs --
    the T/L regression 0170-ruling.md names. `clip_pair` itself is
    unchanged and still the two-roof reference every test checks this
    construction against; `compute_roof_clips` no longer calls it.

    THE PARTITION INVARIANT, refined once (0181-ruling.md sec3): the
    visible regions partition the union of footprints except for the
    root ground of uncertified limbs, asserted globally by a test through
    `diag` -- pass a dict and it comes back with the final cells, their
    original coverers, the blank cells and the limb cells, plus a record
    of every round. On his three-ridge fixture that blank set is empty;
    on the equal-height L it is D85's corner alone."""
    roofs = list(roofs)
    if len(roofs) < 2:
        return {id(rf): RoofClip(None, [], [], (0.0, 0.0)) for rf in roofs}

    footprints = {id(rf): footprint_polygon(rf) for rf in roofs}

    # -- coplanar pairs: excluded entirely, exactly as before ------------
    warn = {id(rf): [] for rf in roofs}
    coplanar = set()
    for i, a in enumerate(roofs):
        for b in roofs[i + 1:]:
            ov = _convex_intersection(footprints[id(a)], footprints[id(b)])
            if not ov:
                continue
            pts = list(ov) + [_centroid(ov)]
            if all(abs(surface_height(a, p) - surface_height(b, p)) <= EPS
                  for p in pts):
                coplanar.add(id(a))
                coplanar.add(id(b))
                msg = (f"roofs {_name(a)} and {_name(b)} share a coplanar "
                      f"surface -- drawn unclipped")
                warn[id(a)].append(msg)
                warn[id(b)].append(msg)

    # -- touched: overlaps at least one other, non-coplanar roof ---------
    touched = set()
    for i, a in enumerate(roofs):
        if id(a) in coplanar:
            continue
        for b in roofs[i + 1:]:
            if id(b) in coplanar:
                continue
            if _convex_intersection(footprints[id(a)], footprints[id(b)]):
                touched.add(id(a))
                touched.add(id(b))
    if not touched:
        return {id(rf): RoofClip(None, [], warn[id(rf)], (0.0, 0.0))
               for rf in roofs}

    live = [rf for rf in roofs if id(rf) in touched]

    # -- joining-end candidacy -- R4g (0176-ruling.md sec3 / 0177-ruling.md):
    # "candidacy is the roof's own footprint. Exactly. Nothing narrower
    # (`_strip` retires -- as a SCOPE, not as code: `clip_pair` still uses
    # the helper unchanged), nothing wider (no extended planes)." The
    # extension sliver itself is still cut off at the roof's own nominal
    # end edge (`_strip`, same shape `clip_pair` already trusts) -- that
    # part was never the "narrower" defect. What WAS narrower than the
    # roof's own footprint: the sliver was then intersected against just
    # the SPECIFIC host(s) whose footprint happened to swallow that ridge
    # endpoint. A THIRD live roof whose footprint also reaches that same
    # extension ground was never compared against at all, so its boundary
    # there was neither a seam nor a candidacy edge -- an unchecked height
    # jump (27 measured on his fixture, 0174-report.md sec6). The fix
    # widens the SET the sliver is checked against from "hosts" to "every
    # other live roof" -- the sliver's own SHAPE and reach are unchanged
    # (still `_strip`, still `2 * max(diagonal)` over whichever roof(s)
    # swallow the endpoint, exactly enough to fully cross them), so this
    # stays bounded to the roof's own real extension amount, never the
    # unrelated blanket rectangle the two REJECTED wider shapes were
    # (0174 sec6: phantom-overlapping every unrelated roof, or an
    # along-axis reach with no WIDTH limit at all -- this touches neither,
    # since `_strip` already IS the roof's own span width, and the
    # intersection with each `other` still bounds it to real overlap,
    # never open air).
    ext = {id(rf): [0.0, 0.0] for rf in live}
    domain = {id(rf): [footprints[id(rf)]] for rf in live}
    for rf in live:
        for end, pt in enumerate((rf.p1, rf.p2)):
            hosts = [other for other in live if other is not rf
                    and _contains(footprints[id(other)], pt)]
            if not hosts:
                continue
            reach = 2.0 * max(_diagonal(footprints[id(h)]) for h in hosts)
            ext[id(rf)][end] = reach
            one_end = [0.0, 0.0]
            one_end[end] = reach
            rf_ext_poly = footprint_polygon(rf, tuple(one_end))
            strip = _strip(rf, footprints[id(rf)], rf_ext_poly)
            if not strip:
                continue
            for other in live:
                if other is rf:
                    continue
                piece = _convex_intersection(strip, footprints[id(other)])
                if piece:
                    domain[id(rf)].append(piece)

    def _covers(rf, pt):
        return any(_contains(poly, pt, tol=-1e-6) for poly in domain[id(rf)])

    # -- the ONE shared cut set: every live roof's own plane-change lines,
    # its own nominal footprint's edges, and every strip's own edges --
    # a cell must never straddle any of these, or its coverers would not
    # stay constant across it
    cut_set = []
    for rf in live:
        cut_set.extend(_cut_lines(rf))
        for poly in domain[id(rf)]:
            m = len(poly)
            for k in range(m):
                a, b = poly[k], poly[(k + 1) % m]
                d = Pt(b.x() - a.x(), b.y() - a.y())
                if math.hypot(d.x(), d.y()) > EPS:
                    cut_set.append((a, d))

    cells = [list(poly) for rf in live for poly in domain[id(rf)]]
    for pt, d in cut_set:
        cells = [piece for cell in cells for piece in _split_by_line(cell, pt, d)]
    cells = _dedup_cells(cells)

    # -- ORIGINAL candidacy per cell, fixed for the rest of this function --
    # `orig_root[i]` (single coverer, from candidacy alone) is the anchor-
    # eligibility test 0177/0179 endorse; it never changes as pruning
    # proceeds (see the docstring's "ROOT ... is a property of the
    # ORIGINAL candidacy alone" paragraph). `active[i]` is the MUTABLE set
    # the fixed point below prunes from.
    orig_coverers = []
    for cell in cells:
        c = _centroid(cell)
        orig_coverers.append([rf for rf in live if _covers(rf, c)])
    orig_root = [len(cs) == 1 for cs in orig_coverers]
    active = [{id(rf) for rf in cs} for cs in orig_coverers]

    def _envelope_round(active):
        """One pass of the per-cell local-maximum envelope (module
        docstring's OWNERSHIP, PER CELL paragraph), using only each
        cell's CURRENTLY active coverers -- rebuilt from scratch every
        round, never a fixed rank order carried over from a wider set."""
        pieces, owner_of, coverer_rank, cell_of = [], [], [], []
        seam_segs, blocked = [], set()
        for ci, cell in enumerate(cells):
            coverers = [rf for rf in live if id(rf) in active[ci]]
            if not coverers:
                continue
            if len(coverers) == 1:
                pieces.append(cell)
                owner_of.append(id(coverers[0]))
                coverer_rank.append(None if orig_root[ci] else [id(coverers[0])])
                cell_of.append(ci)
                continue
            by_id = {id(rf): rf for rf in coverers}
            local = {}                     # id(rf) -> (piece, its pieces[] index)
            for rf in coverers:
                piece = cell
                for other in coverers:
                    if other is rf:
                        continue
                    vals = [surface_height(rf, p) - surface_height(other, p)
                            for p in piece]
                    piece, _ = _clip_by_values(piece, vals)
                    if not piece:
                        break
                if piece and _area(piece) > MIN_CELL_AREA:
                    sub_c = _centroid(piece)
                    ranked_ids = sorted(
                        (id(r) for r in coverers),
                        key=lambda rid: -surface_height(by_id[rid], sub_c))
                    pieces.append(piece)
                    owner_of.append(id(rf))
                    coverer_rank.append(ranked_ids)
                    cell_of.append(ci)
                    local[id(rf)] = (piece, len(pieces) - 1)
            idset = sorted(local.keys())
            for pa in range(len(idset)):
                for pb in range(pa + 1, len(idset)):
                    i_id, j_id = idset[pa], idset[pb]
                    vals = [surface_height(by_id[i_id], p) - surface_height(by_id[j_id], p)
                            for p in cell]
                    _, cross = _clip_by_values(cell, vals)
                    if len(cross) != 2:
                        continue
                    piece_i, idx_i = local[i_id]
                    seg = _clip_segment(piece_i, cross[0], cross[1])
                    if seg is not None:
                        idx_j = local[j_id][1]
                        seam_segs.append((idx_i, idx_j, seg))
                        blocked.add((idx_i, idx_j))
                        blocked.add((idx_j, idx_i))
        return pieces, owner_of, coverer_rank, cell_of, seam_segs, blocked

    def _components(pieces, indices, blocked):
        remaining = set(indices)
        comps = []
        while remaining:
            seed = next(iter(remaining))
            comp = _reach({seed}, pieces, indices, blocked)
            comps.append(comp)
            remaining -= comp
        return comps

    # -- THE FIXED POINT (0179-ruling.md sec2, refined at 0181-ruling.md
    # sec2): re-envelope, find anchors and reach on THIS round's result,
    # prune whoever cannot reach their own piece, and repeat. Terminates
    # because every round that does not converge prunes at least one
    # positive-area piece, and the pieces come from a finite arrangement
    # (cells only ever split along equal-height lines of finitely many
    # coverer subsets); the bound is a backstop against an implementation
    # bug, not slack the math needs.
    #
    # A SWALLOWED END NAMES THE PHANTOM. The one thing that distinguishes
    # ground a roof must give up from ground it merely cannot reach YET is
    # its own ridge end: a roof whose ridge END lies inside another roof
    # is a JOINING roof there (module docstring, R4d), and everything of
    # it cut off from its body on the far side of that seam is its
    # phantom -- A's wedge past the apex and the D85 corner behind it, B's
    # extension lens past its own start, rf1 east of the pinch, rf2's far
    # end inside rf3. That ground never comes back: it prunes, and any
    # limb of it holding root ground is the uncertified limb 0181 sec2
    # leaves blank. A cut-off piece that holds no swallowed end is an
    # ORPHAN: a roof with free ends passing across another (rf3 through
    # rf1 and rf2's far end), cut off in THIS round only because some
    # phantom stands in its corridor -- measured on his fixture, rf3's
    # whole rake-side body was severed from its NE body by nothing but
    # rf2's own phantom. So phantoms prune FIRST, and the vacated ground
    # re-envelopes; an orphan is judged only in a round where no phantom
    # remains anywhere, when whatever still cuts it off is a real roof --
    # and then either the under-pass network certifies it (a root limb
    # passing under a real roof to its own free end) or it prunes.
    #
    # A PHANTOM IS AN END THAT HAS CROSSED ITS HOST'S RIDGE. Not every
    # swallowed end is an overshoot: B's start at the L sits exactly ON
    # A's ridge, and rf2's south end stops 13" short of rf3's ridge --
    # each a JOIN, a ridge drawn to end at the roof it runs into. A's end
    # and rf1's east end lie PAST the ridge they crossed (50" and 49") --
    # "the rf1 ridge completely intersects the rf2 ridge. So the rf1
    # ridge will end at rf2", his own reading of the junction. So a
    # cut-off arm holding a swallowed end is a phantom only if that end
    # lies beyond a crossing of its own ridge with a host's ridge; a
    # cut-off join end is judged like any orphan, once no phantom
    # remains. (rf2's end has ALSO crossed rf1's ridge, 86" back -- so
    # it is a phantom candidate too, and the order below decides.)
    #
    # PHANTOMS PRUNE ONE AT A TIME, THE SHORTER OVERSHOOT FIRST. Two
    # crossed ends can cut each other off -- measured at his pinch: rf1's
    # ridge crosses rf2's at a single-point saddle, each ridge ends inside
    # the other roof, and each far arm is severed from its own body by
    # nothing but the other's far arm. Prune both at once and neither
    # survives (rf1/rf3 then meet in a false seam under rf2's own ridge,
    # and rf1 takes ground south of the pinch his reference gives rf2);
    # prune one and the other is judged on the re-enveloped ground, where
    # it reconnects around the pinch. Which one: the arm that stops
    # SOONER after the crossing is the one that was meant to end there
    # (rf1's 49" before rf2's 86") -- the ordinary T-join in the limit,
    # where a joining ridge drawn to end AT the main ridge overshoots it
    # by nothing. The same order holds with rf3 absent (the saddle in
    # isolation, 0177-ruling.md sec3's own receipt).
    #
    # A JOINING END'S EXTENSION NEVER COMES BACK UP. The strip past a
    # swallowed end exists to close the join UNDER the host (the hip
    # behind the apex, drawn as the lower surface under the phantom
    # wedge) or to carry the end's own planes the last few inches to the
    # seam while still above it -- it may pass from above the host's
    # planes to below them, never from below back to above. B's lens at
    # the L is exactly the forbidden move: B's extended ridge dips under
    # A right behind the apex, then climbs back above A's north slope --
    # and re-emergence into contested ground is what 0181 sec2 reserves
    # for root ground alone. Measured against the ORIGINAL coverers'
    # planes, pruned or not: the host's plane does not stop existing
    # where its own phantom was pruned.
    swallowed = {}
    for rf in live:
        swallowed[id(rf)] = []
        for end, pt in enumerate((rf.p1, rf.p2)):
            if ext[id(rf)][end] <= 0.0:
                continue
            overshoots = []
            for host in live:
                if host is rf or not _contains(footprints[id(host)], pt):
                    continue
                x = _segments_cross(rf.p1, rf.p2, host.p1, host.p2)
                if x is not None:
                    d = math.hypot(pt.x() - x.x(), pt.y() - x.y())
                    if d > 1e-3:
                        overshoots.append(d)
            swallowed[id(rf)].append((pt, min(overshoots) if overshoots else None))

    def _walk(rf, env):
        """(reached, phantoms, root_orphans) for one roof on one
        envelope: the principal anchor's own walk, and the cut-off
        remainder split into phantom components (each holding a crossed
        end, keyed by its overshoot) and orphan components that hold
        root ground (limb candidates for the network -- 0181-ruling.md
        sec2)."""
        pieces, owner_of, coverer_rank, cell_of, _seams, blocked = env
        n_pieces = len(pieces)
        own_idx = {k for k, o in enumerate(owner_of) if o == id(rf)}
        if not own_idx:
            return set(), [], []
        # `clip_pair`'s own reference (untouched, the two-roof case this
        # construction must reduce to) never walks a roof's reach through
        # ANOTHER roof's exclusive root/outside territory (`rb_idx` is not
        # in A's own `ra_idx | ov_idx` allowed set) -- but it DOES walk
        # through ANY overlap/contested piece, whoever currently owns it,
        # since the seam graph among THOSE is what actually decides
        # connectivity. `own_idx` alone (tried and measured wrong: the
        # equal-height L's own poke-through returned, because a roof's
        # reach could no longer even explore the contested pieces where
        # the real seam boundary does its blocking) drops that overlap-
        # transit half; `contested` restores exactly it, generalised from
        # two roofs to N: every piece with 2+ coverers, from ANY owner, is
        # a legal stepping stone, but another roof's OWN root ground never
        # is.
        contested = {k for k in range(n_pieces) if coverer_rank[k] is not None}
        root_idx = {k for k in own_idx if coverer_rank[k] is None}
        comps = _components(pieces, own_idx, blocked)
        by_root_area = sorted(
            comps, key=lambda comp: -sum(_area(pieces[k]) for k in comp & root_idx))
        principal = by_root_area[0] if by_root_area[0] & root_idx else None
        if principal is None:
            marker_pt = rf.p2 if getattr(rf, "marker_end", 1) else rf.p1
            principal = next(
                (comp for comp in comps
                 if any(_contains(pieces[k], marker_pt, tol=1e-3) for k in comp)),
                None)
        if principal is None:
            principal = own_idx
        allowed = own_idx | contested
        strip_below, strip_above = set(), set()
        for k in allowed:
            c = _centroid(pieces[k])
            if _contains(footprints[id(rf)], c, tol=-1e-6):
                continue
            others = [o for o in orig_coverers[cell_of[k]] if o is not rf]
            if others and surface_height(rf, c) < max(
                    surface_height(o, c) for o in others) - EPS:
                strip_below.add(k)
            else:
                strip_above.add(k)
        reached = _reach(principal, pieces, allowed, blocked,
                         no_step=lambda i, j: i in strip_below and j in strip_above)
        phantoms, orphans = [], []
        for comp in _components(pieces, own_idx - reached, blocked):
            overshoots = [d for pt, d in swallowed[id(rf)] if d is not None
                          and any(_contains(pieces[k], pt, tol=1e-3) for k in comp)]
            if overshoots:
                phantoms.append((min(overshoots), comp))
            elif comp & root_idx:
                orphans.append(comp)
        return reached, phantoms, orphans

    limb_cells = set()        # root cells pruned as uncertified limbs (sec2)
    for _round in range(10_000):
        env = _envelope_round(active)
        pieces, owner_of, coverer_rank, cell_of, seam_segs, blocked = env
        n_pieces = len(pieces)
        contested = {k for k in range(n_pieces) if coverer_rank[k] is not None}

        reach_of, limbs_of, phantoms = {}, {}, []
        for order, rf in enumerate(live):
            reach_of[id(rf)], own_phantoms, limbs_of[id(rf)] = _walk(rf, env)
            phantoms.extend((overshoot, sum(_area(pieces[k]) for k in comp), order, comp)
                            for overshoot, comp in own_phantoms)
        all_phantom = set().union(*(comp for *_, comp in phantoms)) if phantoms else set()

        # THE UNDER-PASS NETWORK (0181-ruling.md sec2). A root orphan --
        # real single-coverage ground of this roof, cut off from its body
        # by ground some other roof wins -- certifies, and anchors a walk
        # of its own, iff it connects to the principal through the roof's
        # CONTINUITY NETWORK: the pieces this roof is drawn on (its own
        # reached pieces) plus every piece where its surface lies BELOW a
        # real roof's drawn surface (hidden, passing under --
        # `_under_pieces`; a phantom above it is not a real roof and is
        # left out). Ground where it would stand ABOVE the drawn surface
        # is phantom air and conducts nothing; a point contact conducts
        # nothing (`_adjacent`). Certified ground draws wherever it wins;
        # hidden ground conducts connectivity but never draws.
        certified_of = {}
        for rf in live:
            limbs = limbs_of[id(rf)]
            certified_of[id(rf)] = []
            if not limbs:
                continue
            own_idx = {k for k, o in enumerate(owner_of) if o == id(rf)}
            reached = reach_of[id(rf)]
            hidden = _under_pieces(rf, pieces, owner_of, cell_of, orig_coverers,
                                   exclude=all_phantom)
            certified = _certify_limbs(limbs, reached & own_idx, pieces, hidden)
            for comp in certified:
                reached |= (_reach(comp, pieces, own_idx | contested, blocked)
                            - all_phantom)
            certified_of[id(rf)] = certified

        unsupported = {id(rf): {k for k, o in enumerate(owner_of)
                                if o == id(rf) and k not in reach_of[id(rf)]}
                       for rf in live}
        if not any(unsupported.values()):
            to_prune = set()
        elif phantoms:
            phantoms.sort(key=lambda entry: entry[:3])
            to_prune = set(phantoms[0][3])
        else:
            to_prune = {k for ks in unsupported.values() for k in ks}
        if diag is not None:
            diag.setdefault("rounds", []).append({
                "pieces": list(pieces), "owner_of": list(owner_of),
                "root": [coverer_rank[k] is None for k in range(n_pieces)],
                "cell_of": list(cell_of), "unsupported": unsupported,
                "blocked": set(blocked), "rank": list(coverer_rank),
                "phantoms": [(d, comp) for d, _a, _i, comp in phantoms],
                "limbs": limbs_of, "certified": certified_of,
                "pruned": sorted(to_prune)})
        if not to_prune:
            break

        # A ROOF PRUNES OVER ITS OWN LOST PIECE ONLY, never its whole
        # cell -- measured on the equal-height L: one cell held both A's
        # phantom strip east of the valley and B's extension wedge west
        # of it, and pruning A from the CELL for the strip's sake left
        # nobody to re-envelope the wedge once B lost it too, blank ground
        # A's own body should have carried. So every cell holding a piece
        # about to prune first splits into this round's own pieces --
        # they partition it exactly, each a convex local-maximum region
        # -- and each becomes a cell of its own, inheriting the original
        # candidacy (contested stays contested: ROOT is still a property
        # of the ORIGINAL cell alone).
        cell_of = list(cell_of)
        for ci in {cell_of[k] for k in to_prune}:
            parts = [k for k in range(n_pieces) if cell_of[k] == ci]
            if len(parts) == 1:
                continue
            base = set(active[ci])
            cells[ci] = pieces[parts[0]]
            for k in parts[1:]:
                cell_of[k] = len(cells)
                cells.append(pieces[k])
                orig_coverers.append(orig_coverers[ci])
                orig_root.append(orig_root[ci])
                active.append(set(base))
        for k in to_prune:
            active[cell_of[k]].discard(owner_of[k])
            if coverer_rank[k] is None:
                limb_cells.add(cell_of[k])

    # every piece surviving the fixed point already passed reachability
    # (else its round would have pruned it and looped again), so the
    # final envelope's own ownership needs no further reassignment for
    # correctness -- what follows is cosmetic only.
    final_owner = dict(enumerate(owner_of))

    if diag is not None:
        # the partition invariant, refined once (0181-ruling.md sec3):
        # blank ground is a subset of the root ground of uncertified
        # limbs -- a test asserts it globally from these
        diag["cells"] = cells
        diag["orig_coverers"] = [[id(rf) for rf in cs] for cs in orig_coverers]
        diag["blank"] = [ci for ci in range(len(cells)) if not active[ci]]
        diag["limb_cells"] = sorted(limb_cells)
        diag["active"] = [set(a) for a in active]
        diag["final"] = (pieces, owner_of, coverer_rank, cell_of)

    # -- a razor-thin sliver is exact math, not a bug (a cell where several
    # near-parallel seam lines converge can legitimately be tiny) -- but
    # extruded on its own it can carry a MEANINGFUL height difference
    # across a NEGLIGIBLE footprint, and `_prism_slab`'s own skirt (whose
    # area is perimeter times height-drop, not footprint area) then reads
    # as a tall, visible fin next to the real surfaces around it -- his
    # own second report. Relabelled to its cell's next-best coverer among
    # the FINAL round's own competitors, never left undrawn or double-
    # claimed -- but this is a RELABEL, not a merge: the tiny polygon
    # itself is unchanged and is still extruded as its own small prism,
    # now under a different roof's height formula at the same three-or-
    # more vertices. MEASURED, NOT CLAIMED: this does not, on its own,
    # make the sliver's own skirt any shorter -- doing that needs the
    # tiny piece folded into an ADJACENT same-owner cell's own polygon (a
    # real geometric merge), which this pass does not attempt. Left in
    # place as a harmless, honest partial step (it never creates a
    # double-claim or an undrawn gap) rather than removed, since a future
    # merge pass can build on the ranking it already computes.
    for k in range(n_pieces):
        if coverer_rank[k] is None or _area(pieces[k]) >= SLIVER_AREA_IN:
            continue
        remaining = [rid for rid in coverer_rank[k] if rid != final_owner[k]]
        if remaining:
            final_owner[k] = remaining[0]

    # the sliver fold-in is the only thing that can move a piece away
    # from its own converged `owner_of` -- so a seam is only drawn
    # between two pieces that BOTH kept it, checked against the FINAL
    # state, exactly as before.
    primary = {k for k in range(n_pieces) if final_owner.get(k) == owner_of[k]}

    final_pieces = {id(rf): [] for rf in live}
    for k, owner in final_owner.items():
        final_pieces[owner].append(pieces[k])

    seams = {id(rf): [] for rf in live}
    for idx_i, idx_j, seg in seam_segs:
        if idx_i not in primary or idx_j not in primary:
            continue
        oi, oj = final_owner[idx_i], final_owner[idx_j]
        if oi == oj:
            continue
        seams[oi].append(seg)
        seams[oj].append(seg)

    out = {}
    for rf in roofs:
        if id(rf) not in touched:
            out[id(rf)] = RoofClip(None, [], warn[id(rf)], (0.0, 0.0))
        else:
            out[id(rf)] = RoofClip(ClipRegion(final_pieces[id(rf)]),
                                   seams[id(rf)], warn[id(rf)],
                                   tuple(ext[id(rf)]))
    return out


def _under_pieces(rf, pieces, owner_of, cell_of, orig_coverers, exclude=()):
    """The ground `rf` passes UNDER (0181-ruling.md sec2): for every piece
    another roof currently draws, inside a cell `rf`'s own candidacy
    covers (a roof's surface exists only within its own footprint), the
    part where `rf`'s surface lies below the drawn one. A piece `rf`
    would stand wholly above is phantom air and contributes nothing; a
    piece it crosses is cut at the equal-height line and only the
    under-side kept. `exclude` names pieces that are nobody's real roof
    (another roof's phantom, about to prune) -- passing under those is
    not passing under anything."""
    by_id = {}
    out = []
    for k, piece in enumerate(pieces):
        rid = owner_of[k]
        if rid == id(rf) or k in exclude:
            continue
        coverers = orig_coverers[cell_of[k]]
        if not any(c is rf for c in coverers):
            continue
        owner = by_id.get(rid)
        if owner is None:
            owner = by_id[rid] = next(c for c in coverers if id(c) == rid)
        vals = [surface_height(owner, p) - surface_height(rf, p) for p in piece]
        if min(vals) >= -EPS:
            out.append(piece)
        elif max(vals) > EPS:
            under, _ = _clip_by_values(piece, vals)
            if len(under) >= 3 and _area(under) > MIN_CELL_AREA:
                out.append(under)
    return out


def _certify_limbs(limbs, drawn, pieces, hidden):
    """Which of `limbs` (root components of one roof, each a set of piece
    indices) connect to that roof's `drawn` pieces through its continuity
    network -- the drawn pieces plus the `hidden` polygons it passes
    under -- by positive-length adjacency only. A certified limb joins
    the network at once, so a further limb may connect through it."""
    frontier = [pieces[k] for k in drawn]
    seen_hidden = set()
    pending = list(limbs)
    certified = []
    while frontier and pending:
        cur = frontier.pop()
        for h, poly in enumerate(hidden):
            if h not in seen_hidden and _adjacent(cur, poly):
                seen_hidden.add(h)
                frontier.append(poly)
        for comp in list(pending):
            if any(_adjacent(cur, pieces[k]) for k in comp):
                pending.remove(comp)
                certified.append(comp)
                frontier.extend(pieces[k] for k in comp)
    return certified


def _dedup_cells(cells, tol=1e-4):
    """Convex `cells` starting one candidate per roof's own footprint can
    repeat the same physical overlap piece once per covering roof -- a
    convex polygon's vertex SET (order-independent) identifies it. Used
    once, at arrangement-construction time in `compute_roof_clips` --
    there is only one arrangement now, so no second, coarser dedup pass
    is needed downstream."""
    seen = set()
    out = []
    for c in cells:
        key = tuple(sorted((round(p.x() / tol), round(p.y() / tol)) for p in c))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


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
