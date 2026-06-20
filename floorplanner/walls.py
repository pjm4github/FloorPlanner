"""Wall graphics items (WallItem/OpenWall/OpeningItem) and the wall-network
algorithms: spatial indices, coalescing, welding, fracturing, junction
clipping, and the full-scene rebuild.

rebuild_all_walls() refreshes rooms and a couple of WallItem actions touch
room binding; those are LATE imports from floorplanner.rooms so this module
stays importable before rooms (which imports this one)."""
import math

from PyQt6 import sip
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401


def nearest_wall_endpoint(scene, p: QPointF, tol: float, exclude=None):
    """Closest endpoint of any wall (other than `exclude`) within `tol`."""
    best, best_d = None, tol
    if scene is None:
        return None
    for it in scene.items():
        if isinstance(it, WallItem) and it is not exclude:
            for q in (it.p1, it.p2):
                d = QLineF(p, q).length()
                if d < best_d:
                    best_d, best = d, QPointF(q)
    return best


def nearest_wall_body(scene, p: QPointF, tol: float, exclude=None):
    """Closest (wall, centreline point) within reach of `p`, or None.

    This is the fuse target for T-junctions: a wall end that stops at (or
    inside) the body of another wall snaps onto that wall's centreline so
    the two paint as one solid joint."""
    best, best_d = None, float("inf")
    if scene is None:
        return None
    for it in scene.items():
        if isinstance(it, WallItem) and it is not exclude:
            length = it.length()
            if length < 1e-6:
                continue
            u = it.unit()
            s = (p.x() - it.p1.x()) * u.x() + (p.y() - it.p1.y()) * u.y()
            s = max(0.0, min(length, s))
            q = it.point_at(s)
            d = QLineF(p, q).length()
            if d <= max(tol, it.t * 0.5 + 1.0) and d < best_d:
                best_d, best = d, (it, QPointF(q))
    return best


def nearest_wall_body_point(scene, p: QPointF, tol: float, exclude=None):
    hit = nearest_wall_body(scene, p, tol, exclude)
    return hit[1] if hit is not None else None


class _WallIndex:
    """Per-rebuild spatial cache so each wall's rebuild() is O(local) instead
    of O(all walls): an endpoint hash (joined corners) + per-line buckets
    (coincident party walls).  Built once by rebuild_all_walls and passed to
    every wall; the exact predicates are unchanged, the index just narrows the
    candidate set to a guaranteed superset."""

    EP = 4.0          # endpoint hash cell (>> the 0.6" join tolerance)
    OFF = 3.0         # line-offset bucket (>> the 1.5" coincidence tolerance)

    def __init__(self, scene):
        self.eps = {}            # (i, j) -> [(wall, x, y)]
        self.hb = {}             # round(y/OFF) -> [horizontal walls]
        self.vb = {}             # round(x/OFF) -> [vertical walls]
        self.diag = []           # non-axis-aligned real walls (rare)
        for w in (scene.items() if scene is not None else []):
            if not isinstance(w, WallItem):
                continue
            for p in (w.p1, w.p2):
                self.eps.setdefault((round(p.x() / self.EP),
                                     round(p.y() / self.EP)), []).append(
                    (w, p.x(), p.y()))
            if w.is_open or w.length() < 1e-6:
                continue
            u = w.unit()
            if abs(u.y()) < 1e-4:
                self.hb.setdefault(round(w.p1.y() / self.OFF), []).append(w)
            elif abs(u.x()) < 1e-4:
                self.vb.setdefault(round(w.p1.x() / self.OFF), []).append(w)
            else:
                self.diag.append(w)

    def joined_at(self, p, exclude) -> bool:
        px, py = p.x(), p.y()
        ki, kj = round(px / self.EP), round(py / self.EP)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for w, qx, qy in self.eps.get((ki + di, kj + dj), ()):
                    if w is not exclude and (qx - px) ** 2 + (qy - py) ** 2 \
                            < 0.36:
                        return True
        return False

    def coincident_candidates(self, wall, reach=1):
        u = wall.unit()
        rng = range(-reach, reach + 1)                  # widen for a bigger tol
        if abs(u.y()) < 1e-4:                          # horizontal query
            b = round(wall.p1.y() / self.OFF)
            return [w for d in rng for w in self.hb.get(b + d, ())] \
                + self.diag
        if abs(u.x()) < 1e-4:                          # vertical query
            b = round(wall.p1.x() / self.OFF)
            return [w for d in rng for w in self.vb.get(b + d, ())] \
                + self.diag
        return ([w for ws in self.hb.values() for w in ws]   # diagonal: rare
                + [w for ws in self.vb.values() for w in ws] + self.diag)


def coincident_walls(scene, wall, index=None, perp_tol=1.5):
    """Real walls that lie on (within `perp_tol` of) the same line as `wall` and
    overlap its span.  At the default 1.5" this finds the duplicate party walls
    on a shared boundary (so a plain wall opens for a coincident wall's door);
    coalescing passes the wider wall-snap grid so near-parallel walls merge.
    With perp_tol > the index buckets, pass index=None for a full scan."""
    if scene is None or wall.length() < 1e-6:
        return []
    u = wall.unit()
    length = wall.length()
    out = []
    if index is not None:
        reach = int(perp_tol / _WallIndex.OFF) + 1
        cands = index.coincident_candidates(wall, reach)
    else:
        cands = scene.items()
    for w in cands:
        if not isinstance(w, WallItem) or w is wall or w.is_open \
                or w.length() < 1e-6 or w.scene() is None:
            continue
        wu = w.unit()
        if abs(wu.x() * u.y() - wu.y() * u.x()) > 0.02:        # not parallel
            continue
        d1 = abs((w.p1.x() - wall.p1.x()) * u.y()              # off the line?
                 - (w.p1.y() - wall.p1.y()) * u.x())
        d2 = abs((w.p2.x() - wall.p1.x()) * u.y()
                 - (w.p2.y() - wall.p1.y()) * u.x())
        if d1 > perp_tol or d2 > perp_tol:
            continue
        s1 = (w.p1.x() - wall.p1.x()) * u.x() + (w.p1.y() - wall.p1.y()) * u.y()
        s2 = (w.p2.x() - wall.p1.x()) * u.x() + (w.p2.y() - wall.p1.y()) * u.y()
        if max(s1, s2) > 0.5 and min(s1, s2) < length - 0.5:   # spans overlap
            out.append(w)
    return out


def _coalesce_wall_impl(scene, wall, index=None, rebuild=True):
    """Merge `wall` with every parallel, SAME-type wall whose body overlaps its
    span and lies within the on-centre grid (perpendicular).  The survivor is
    `wall`, grown to the union span (snapped to grid) and carrying every merged
    wall's openings; its `rooms` become the union of all merged walls' rooms (a
    coalesced party wall borders several rooms -- the shared-wall model).
    Grouped and open walls are never merged.  Returns `wall`.  Pass
    rebuild=False in a bulk sweep where a single rebuild_all_walls follows."""
    if (scene is None or wall.scene() is None or wall.is_open
            or wall.group() is not None or wall.length() < 1e-6):
        return wall
    perp = SETTINGS.get("wall_snap_in", WALL_SNAP_DEFAULT)
    absorbed = [w for w in coincident_walls(scene, wall, index=index,
                                            perp_tol=perp)
                if not w.is_open and w.group() is None
                and w.wall_type == wall.wall_type and w.length() > 1e-6]
    if not absorbed:
        return wall
    origin, u = QPointF(wall.p1), wall.unit()
    ux, uy = u.x(), u.y()

    def s_of(p):
        return (p.x() - origin.x()) * ux + (p.y() - origin.y()) * uy

    ss = [0.0, s_of(wall.p2)]
    moved_ops = []                       # (kind, code, scene_pt, door_type, swing)
    new_rooms = list(wall.rooms)
    for w in absorbed:
        ss += [s_of(w.p1), s_of(w.p2)]
        for op in w.openings:
            moved_ops.append((op.kind, op.code, w.point_at(op.s),
                              op.door_type, op.swing))
        for r in w.rooms:
            if r not in new_rooms:
                new_rooms.append(r)
        for r in list(w.rooms):          # detach the absorbed wall from its
            r.unbind_wall(w)             # rooms (leaves survivor to carry them)
        scene.removeItem(w)
    smin, smax = min(ss), max(ss)
    wall.p1 = wall_snap(QPointF(origin.x() + ux * smin, origin.y() + uy * smin))
    wall.p2 = wall_snap(QPointF(origin.x() + ux * smax, origin.y() + uy * smax))
    for op in wall.openings:             # own openings ride the new p1
        op.s -= smin
    np1, nu = wall.p1, wall.unit()
    for kind, code, pt, dtype, swing in moved_ops:
        s = (pt.x() - np1.x()) * nu.x() + (pt.y() - np1.y()) * nu.y()
        try:
            op = OpeningItem(wall, kind, code, s)
        except ValueError:
            continue
        op.door_type, op.swing = dtype, swing
        wall.openings.append(op)
    for r in new_rooms:                  # survivor now borders every merged room
        r.bind_wall(wall)
    if rebuild:
        wall.rebuild()
    return wall


def coalesce_wall(scene, wall, index=None):
    """Auto-coalesce entry: a no-op when the user has switched auto-coalesce
    off (the manual 'Coalesce all walls now' action calls the _impl directly)."""
    if not SETTINGS.get("auto_coalesce", True):
        return wall
    return _coalesce_wall_impl(scene, wall, index)


def _wall_count(scene):
    return sum(1 for w in scene.items()
               if isinstance(w, WallItem) and not w.is_open)


def _coalesce_all_impl(scene):
    """Sweep the whole plan, merging every overlapping same-type wall pair to a
    fixed point.  Heavy (O(walls^2)); used by load/import and the manual sweep
    action.  Returns the number of walls absorbed."""
    if scene is None:
        return 0
    start = _wall_count(scene)
    changed = True
    while changed:
        changed = False
        index = _WallIndex(scene)            # one local index per pass
        walls = sorted((w for w in scene.items()
                        if isinstance(w, WallItem) and not w.is_open
                        and w.group() is None),
                       key=lambda w: (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y(),
                                      w.wall_type))
        before = _wall_count(scene)
        for w in walls:
            if w.scene() is None:                # already absorbed this pass
                continue
            _coalesce_wall_impl(scene, w, index, rebuild=False)
        if _wall_count(scene) < before:
            changed = True
    return start - _wall_count(scene)


def coalesce_all(scene):
    """Auto-coalesce sweep (load/import); a no-op when auto-coalesce is off."""
    if not SETTINGS.get("auto_coalesce", True):
        return 0
    return _coalesce_all_impl(scene)


def weld_all(scene, max_passes=6):
    """Weld every wall's free endpoints onto the walls they meet (T/L joints),
    so a drawn-or-loaded plan reads as one connected structure.  Iterated to a
    fixed point (a welded plan does not move on a further pass), which keeps
    save/load round-trips stable.  Grouped walls are left alone."""
    if scene is None:
        return
    for _ in range(max_passes):
        walls = sorted((w for w in scene.items()
                        if isinstance(w, WallItem) and not w.is_open
                        and w.group() is None),
                       key=lambda w: (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()))
        moved = False
        for w in walls:
            b1, b2 = QPointF(w.p1), QPointF(w.p2)
            w.join_endpoints(rebuild=False)
            if (QLineF(b1, w.p1).length() > 1e-6
                    or QLineF(b2, w.p2).length() > 1e-6):
                moved = True
        if not moved:
            break


def _merge_intervals(intervals):
    """Merge (lo, hi) ranges into disjoint, ascending intervals."""
    out = []
    for lo, hi in sorted(intervals):
        if out and lo <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def fracture_delete_wall(scene, wall, settle=True):
    """Delete `wall`, but FRACTURE it at room perimeters: every stretch that
    runs along a bordering room's edge is kept (as a segment still bound to
    that room) so deleting the wall never breaks a room open; the stretches no
    room needs are removed.  A wall that borders no room is deleted whole."""
    if scene is None or wall.scene() is None:
        return
    if wall.is_open or not wall.rooms:
        for r in list(wall.rooms):
            r.unbind_wall(wall)
        scene.removeItem(wall)
        if settle:
            rebuild_all_walls(scene)
        return
    room_spans = []                          # (room, (s0, s1)) along the wall
    for r in list(wall.rooms):
        span = r._perimeter_span(wall)
        if span is not None:
            room_spans.append((r, span))
    if not room_spans:                       # touches rooms but is no edge
        for r in list(wall.rooms):
            r.unbind_wall(wall)
        scene.removeItem(wall)
        if settle:
            rebuild_all_walls(scene)
        return
    keep = _merge_intervals([s for _, s in room_spans])
    u, p1 = wall.unit(), QPointF(wall.p1)
    ops = [(op.kind, op.code, op.s, op.door_type, op.swing)
           for op in wall.openings]
    for s0, s1 in keep:
        if s1 - s0 < MIN_WALL_LEN:
            continue
        a = QPointF(p1.x() + u.x() * s0, p1.y() + u.y() * s0)
        b = QPointF(p1.x() + u.x() * s1, p1.y() + u.y() * s1)
        seg = WallItem(a, b, wall.wall_type)
        scene.addItem(seg)
        for kind, code, s, dtype, swing in ops:
            if s0 <= s <= s1:
                try:
                    op = OpeningItem(seg, kind, code, s - s0)
                except ValueError:
                    continue
                op.door_type, op.swing = dtype, swing
                seg.openings.append(op)
        for r, (a0, a1) in room_spans:       # bind to the rooms it still serves
            if a0 < s1 - 1e-6 and a1 > s0 + 1e-6:
                r.bind_wall(seg)
        seg.rebuild()
    for r in list(wall.rooms):
        r.unbind_wall(wall)
    scene.removeItem(wall)
    if settle:
        rebuild_all_walls(scene)


def wall_endpoint_open(scene, p: QPointF, ignore=()) -> bool:
    """True when `p` is a free, dangling wall end: no other (non-open) wall has
    an endpoint within JOIN_TOL of it.  Walls in `ignore` are skipped (the
    endpoint's own wall, and the wall being drawn)."""
    if scene is None:
        return False
    for w in scene.items():
        if not isinstance(w, WallItem) or w.is_open or w in ignore:
            continue
        if (QLineF(w.p1, p).length() < JOIN_TOL
                or QLineF(w.p2, p).length() < JOIN_TOL):
            return False
    return True


def wall_bbox(w) -> QRectF:
    """A wall's scene bbox padded by its thickness."""
    t = w.t
    return QRectF(QPointF(min(w.p1.x(), w.p2.x()), min(w.p1.y(), w.p2.y())),
                  QPointF(max(w.p1.x(), w.p2.x()), max(w.p1.y(), w.p2.y()))
                  ).adjusted(-t, -t, t, t)


class _WallBBoxIndex:
    """Walls hashed by bbox cells so 'which walls are near this box' is
    O(local) -- used by the memoized room dirty-check instead of scanning every
    wall per room."""

    CELL = 60.0          # 5 ft cells

    def __init__(self, scene):
        self.cells = {}
        for w in (scene.items() if scene is not None else []):
            if not isinstance(w, WallItem):
                continue
            wb = wall_bbox(w)
            for i in range(int(wb.left() / self.CELL),
                           int(wb.right() / self.CELL) + 1):
                for j in range(int(wb.top() / self.CELL),
                               int(wb.bottom() / self.CELL) + 1):
                    self.cells.setdefault((i, j), []).append((w, wb))

    def near(self, box):
        seen, out = set(), []
        for i in range(int(box.left() / self.CELL),
                       int(box.right() / self.CELL) + 1):
            for j in range(int(box.top() / self.CELL),
                           int(box.bottom() / self.CELL) + 1):
                for w, wb in self.cells.get((i, j), ()):
                    if id(w) not in seen and wb.intersects(box):
                        seen.add(id(w))
                        out.append(w)
        return out


def rebuild_all_walls(scene):
    from floorplanner.rooms import refresh_rooms  # late: breaks the walls<->rooms cycle
    if scene is None:
        return
    index = _WallIndex(scene)                # shared: rebuild is O(local), not
    walls = [it for it in scene.items() if isinstance(it, WallItem)]
    for it in walls:                         # O(all walls) per wall
        it.rebuild(cascade=False, index=index)
    _compute_wall_junctions(scene, walls)
    refresh_rooms(scene)


def _compute_wall_junctions(scene, walls=None):
    """For each wall, cache an outline clip = its bounds minus the bodies of the
    walls it overlaps, so the dark outline is drawn only on the OUTER boundary
    of the wall network -- T/cross/L joints read as one solid piece, not a seam.
    Runs once after every wall's footprint (`_solid`) is up to date."""
    if walls is None:
        walls = [it for it in scene.items() if isinstance(it, WallItem)]
    bbi = _WallBBoxIndex(scene)
    for w in walls:
        if w.is_open:                        # dashed placeholders don't merge
            w._outline_clip = None
            continue
        wb = w._solid.boundingRect()
        union = QPainterPath()
        found = False
        for other in bbi.near(wb):
            if (other is w or not isinstance(other, WallItem)
                    or other.is_open or other._solid.isEmpty()):
                continue
            if (other._solid.boundingRect().intersects(wb)
                    and other._solid.intersects(w._solid)):
                union = union.united(other._solid)
                found = True
        if found:
            clip = QPainterPath()
            clip.addRect(wb.adjusted(-2, -2, 2, 2))
            w._outline_clip = clip.subtracted(union)
        else:
            w._outline_clip = None
        w.update()


class WallItem(QGraphicsItem):
    """A straight wall segment.  Local coords == scene coords (pos stays 0,0).

    Geometry is defined by endpoints p1, p2 plus a standard thickness.
    Door/window OpeningItems are child items; each remembers its distance
    `s` along the wall from p1, so they ride along when the wall moves.
    """

    is_open = False                   # OpenWall (a dashed gap) sets this True

    def __init__(self, p1: QPointF, p2: QPointF, wall_type: str = "exterior"):
        super().__init__()
        self.wall_type = wall_type
        self.p1 = QPointF(p1)
        self.p2 = QPointF(p2)
        self.openings = []            # OpeningItem children
        self.rooms = []               # RoomItems this wall borders ([] = free)
        self._corners_unlocked = False  # endpoints draggable while in a room
        self._drawing = False         # True while being rubber-banded
        self._mode = None             # None | 'p1' | 'p2' | 'move'
        self._path = QPainterPath()
        self._solid = QPainterPath()     # body footprint, no opening holes
        self._outline_clip = None        # outline-clip so junctions read solid
        self._hit = QPainterPath()
        self._bounds = QRectF()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z)           # above the translucent room fill (3)
        self.rebuild()

    @property
    def primary_room(self):
        """A representative owning room (the first), or None when free."""
        return self.rooms[0] if self.rooms else None

    def itemChange(self, change, value):
        # when removed from the scene, release every room that borders this wall
        # so no RoomItem.walls keeps a reference to a deleted item
        if (change == QGraphicsItem.GraphicsItemChange.ItemSceneChange
                and value is None and self.rooms):
            for r in list(self.rooms):
                if not sip.isdeleted(r):
                    r.unbind_wall(self)
        return super().itemChange(change, value)

    # -- basic geometry ------------------------------------------------------
    @property
    def t(self) -> float:
        return EXTERIOR_T if self.wall_type == "exterior" else INTERIOR_T

    def length(self) -> float:
        return math.hypot(self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y())

    def angle_rad(self) -> float:
        return math.atan2(self.p2.y() - self.p1.y(), self.p2.x() - self.p1.x())

    def unit(self) -> QPointF:
        length = self.length()
        if length < 1e-9:
            return QPointF(1.0, 0.0)
        return QPointF((self.p2.x() - self.p1.x()) / length,
                       (self.p2.y() - self.p1.y()) / length)

    def point_at(self, s: float) -> QPointF:
        u = self.unit()
        return QPointF(self.p1.x() + u.x() * s, self.p1.y() + u.y() * s)

    def s_of(self, p: QPointF) -> float:
        """Project a scene point onto the wall axis -> distance from p1."""
        u = self.unit()
        s = (p.x() - self.p1.x()) * u.x() + (p.y() - self.p1.y()) * u.y()
        return max(0.0, min(self.length(), s))

    # -- geometry cache ------------------------------------------------------
    def _joined_at(self, p: QPointF, index=None) -> bool:
        """True when another wall shares (within 1/2") this endpoint."""
        if index is not None:
            return index.joined_at(p, self)
        sc = self.scene()
        if sc is None:
            return False
        for it in sc.items():
            if isinstance(it, WallItem) and it is not self:
                if (QLineF(p, it.p1).length() < 0.6
                        or QLineF(p, it.p2).length() < 0.6):
                    return True
        return False

    def rebuild(self, cascade=True, index=None):
        """Recompute the painted path (with openings cut out) and hit shape.

        When `cascade`, also rebuild any coincident party walls so they reopen
        for this wall's openings (and re-solidify when an opening leaves).
        rebuild_all_walls passes cascade=False since it rebuilds every wall."""
        self.prepareGeometryChange()
        length, t, ang = self.length(), self.t, self.angle_rad()

        # extend joined ends by half a thickness so corners fill in solid
        ext1 = t * 0.5 if self._joined_at(self.p1, index) else 0.0
        ext2 = t * 0.5 if self._joined_at(self.p2, index) else 0.0

        body = QPainterPath()
        body.addRect(QRectF(-ext1, -t / 2, length + ext1 + ext2, t))
        solid_local = QPainterPath(body)   # footprint before openings are cut
        holes = QPainterPath()
        for op in self.openings:
            half = op.width / 2
            op.s = min(max(op.s, half), max(half, length - half))
            holes.addRect(QRectF(op.s - half, -t / 2 - 0.5, op.width, t + 1.0))
        # open the body where a coincident wall carries a door/window, so a
        # plain party wall doesn't cover the opening on the wall next to it
        if not self.is_open:
            u = self.unit()
            for w in coincident_walls(self.scene(), self, index):
                for op in w.openings:
                    p = w.point_at(op.s)
                    sl = ((p.x() - self.p1.x()) * u.x()
                          + (p.y() - self.p1.y()) * u.y())
                    half = op.width / 2
                    if -half < sl < length + half:
                        holes.addRect(QRectF(sl - half, -t / 2 - 0.5,
                                             op.width, t + 1.0))
        if not holes.isEmpty():
            body = body.subtracted(holes)

        tr = QTransform()
        tr.translate(self.p1.x(), self.p1.y())
        tr.rotateRadians(ang)
        self._path = tr.map(body)
        self._solid = tr.map(solid_local)
        # cleared here; rebuild_all_walls' junction pass recomputes the clip so
        # neighbouring wall bodies hide this wall's inner seams (T/cross joints)
        self._outline_clip = None

        # hit shape: stroked centreline (no holes -> easy to click)
        line = QPainterPath()
        line.moveTo(self.p1)
        line.lineTo(self.p2)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(t, 1.0))
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
        self._hit = stroker.createStroke(line)
        if length < 0.01:
            self._hit.addEllipse(self.p1, t, t)

        b = self._path.boundingRect().united(self._hit.boundingRect())
        self._bounds = b.adjusted(-24, -24, 24, 24)   # room for handles/label

        for op in self.openings:
            op.sync()
        self.update()
        if cascade and not self.is_open:
            for w in coincident_walls(self.scene(), self):
                w.rebuild(cascade=False)

    # -- QGraphicsItem interface ---------------------------------------------
    def boundingRect(self) -> QRectF:
        return self._bounds

    def shape(self) -> QPainterPath:
        return self._hit

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        fill = QColor(60, 62, 68) if self.wall_type == "exterior" else QColor(150, 152, 158)
        # fill the body with NO outline so overlapping walls read as one solid
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(fill))
        painter.drawPath(self._path)
        # dark outline, clipped to the wall-network's outer boundary so the
        # seams INSIDE a T/cross/L junction don't show (one solid wall)
        painter.save()
        if self._outline_clip is not None:
            painter.setClipPath(self._outline_clip)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(25, 25, 25), 0))
        painter.drawPath(self._path)
        painter.restore()

        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        lod = max(lod, 1e-6)

        if self.isSelected():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(0, 122, 255), 0))
            painter.drawPath(self._path)
            if self._ends_editable():       # endpoint knobs only when active
                hs = 13.0 / lod             # bigger knob -> easier to aim at
                painter.setPen(QPen(QColor(40, 40, 40), 0))
                painter.setBrush(QBrush(QColor(255, 200, 0)))
                for q in (self.p1, self.p2):
                    painter.drawRect(QRectF(q.x() - hs / 2, q.y() - hs / 2,
                                            hs, hs))

        if self.isSelected() or self._drawing:
            u = self.unit()
            n = QPointF(-u.y(), u.x())
            mid = QPointF((self.p1.x() + self.p2.x()) / 2,
                          (self.p1.y() + self.p2.y()) / 2)
            off = self.t / 2 + 12.0 / lod
            tp = QPointF(mid.x() + n.x() * off, mid.y() + n.y() * off)
            f = QFont()
            f.setPixelSize(max(2, int(13.0 / lod)))
            painter.setFont(f)
            painter.setPen(QPen(QColor(0, 90, 200), 0))
            painter.drawText(tp, fmt_ftin(self.length()))

    # -- interaction ----------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _ends_editable(self) -> bool:
        """Every wall's endpoints are draggable.  In the shared-wall model a
        wall IS the room boundary (not a hidden copy), so the user edits it
        directly: a free wall re-angles/projects, a room wall moves its end
        along the wall axis (pulling a corner away opens that side)."""
        return True

    def mousePressEvent(self, e):
        if self.group() is not None:
            # grouped: let the group own the drag.  Running the wall-slide
            # / join logic on a group child mutates p1/p2 in the wrong
            # coordinate space and join_endpoints/grow_walls can collapse
            # walls -- ignore so the press falls through to the group.
            self._mode = None
            e.ignore()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)
            return
        sp = e.scenePos()
        # generous endpoint catch radius (~20 px on screen, larger when zoomed
        # in) so the little end-knob is easy to grab without missing -- but
        # never more than a third of the wall, so a SHORT wall keeps a grabbable
        # middle to body-slide perpendicular (else the end zones cover it all)
        tol = max(12.0, 20.0 / self._view_scale())
        ep_tol = min(tol, self.length() / 3.0)
        ends = self._ends_editable()       # endpoints locked while in a room
        near_p1 = ends and QLineF(sp, self.p1).length() <= ep_tol
        near_p2 = ends and QLineF(sp, self.p2).length() <= ep_tol
        ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if ctrl and not (near_p1 or near_p2):
            # Ctrl+click on the body toggles selection-set membership; Ctrl on
            # an endpoint instead starts an angle-snapped drag (handled below)
            self.setSelected(not self.isSelected())
            self._mode = None
            e.accept()
            return
        if not self.isSelected() and not ctrl:
            self.scene().clearSelection()
        self.setSelected(True)
        if self.rooms:                     # bring an owning room to the front
            self.primary_room.raise_to_front()
        # ...then lift THIS wall above its siblings so clicking the wall you
        # want never buries it behind a coincident/crossing room wall
        bring_to_front(self)

        if near_p1:
            self._mode = "p1"
            self._anchor = QPointF(self.p2)
        elif near_p2:
            self._mode = "p2"
            self._anchor = QPointF(self.p1)
        else:
            self._mode = "move"
            self._press = QPointF(sp)
            self._o1 = QPointF(self.p1)
            self._o2 = QPointF(self.p2)
            # the whole collinear side slides as one (so an open-wall gap rides
            # along); perpendicular walls attached to the SIDE's endpoints then
            # stretch -- corner joints fully, T-joints sideways only
            self._slide_u = self.unit()
            self._run = self._collinear_run()
            self._run_orig = [(w, QPointF(w.p1), QPointF(w.p2))
                              for w in self._run]
            run_ids = {id(w) for w in self._run}
            run_pts = [p for w in self._run for p in (w.p1, w.p2)]
            self._attached = []
            sc, length = self.scene(), self.length()
            ux, uy = self._slide_u.x(), self._slide_u.y()
            if sc is not None:
                for w in sc.items():
                    if not isinstance(w, WallItem) or id(w) in run_ids:
                        continue
                    for attr in ("p1", "p2"):
                        q = getattr(w, attr)
                        if any(QLineF(q, rp).length() < 0.6 for rp in run_pts):
                            self._attached.append((w, attr, QPointF(q), True))
                        else:
                            vx, vy = q.x() - self.p1.x(), q.y() - self.p1.y()
                            s = vx * ux + vy * uy
                            if (0.0 < s < length
                                    and abs(vy * ux - vx * uy) <= 0.75):
                                self._attached.append((w, attr, QPointF(q), False))

        if self._mode in ("p1", "p2"):
            moving = self.p1 if self._mode == "p1" else self.p2
            d = QLineF(self._anchor, moving)
            if d.length() > 1e-6:
                self._axis = QPointF(d.dx() / d.length(), d.dy() / d.length())
            else:
                self._axis = QPointF(1.0, 0.0)
        e.accept()

    def _endpoint_target(self, sp: QPointF, mods) -> QPointF:
        """Lengthen / shorten this wall.  The end rides the wall's own axis,
        grid-snapped, and STICKS to the projected line of a close orthogonal
        wall when it lines up (so you can pull an end into a corner) -- it
        never fuses to another wall's endpoint or body.  Shift = free re-angle;
        Ctrl = re-angle in fixed increments (45 deg etc.)."""
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))          # free re-angle, grid only
        if mods & Qt.KeyboardModifier.ControlModifier:
            return self._angle_snapped_target(sp)
        return self._axis_target(sp)

    def _angle_snapped_target(self, sp: QPointF) -> QPointF:
        """Ctrl-drag: swing the dragged end around the anchored end in fixed
        angular increments (SETTINGS['rotate_snap_deg'], default 15 deg), with a
        grid-snapped length -- so the user can build 45 deg and other off-axis
        walls, not just lengthen along the existing axis."""
        o = self._anchor
        dx, dy = sp.x() - o.x(), sp.y() - o.y()
        if math.hypot(dx, dy) < 1e-6:
            dx, dy = self._axis.x(), self._axis.y()
        step = math.radians(max(1.0, SETTINGS.get("rotate_snap_deg", 15.0)))
        ang = round(math.atan2(dy, dx) / step) * step
        length = max(MIN_WALL_LEN, wall_snap_len(math.hypot(dx, dy)))
        return QPointF(o.x() + math.cos(ang) * length,
                       o.y() + math.sin(ang) * length)

    def _axis_target(self, sp: QPointF) -> QPointF:
        o, u = self._anchor, self._axis
        s = (sp.x() - o.x()) * u.x() + (sp.y() - o.y()) * u.y()
        proj = self._project_to_orthogonal(o, u, s)
        s = proj if proj is not None else wall_snap_len(s)
        if s < MIN_WALL_LEN:                        # never collapse the wall
            s = MIN_WALL_LEN
        return QPointF(o.x() + u.x() * s, o.y() + u.y() * s)

    def _project_to_orthogonal(self, o: QPointF, u: QPointF, s: float):
        """The exact axis distance at which this wall's axis crosses the
        projected line of a NEARBY ORTHOGONAL wall, when the drag is within the
        stick tolerance of it -- else None (so it falls back to the grid).
        Snaps only to such lines, never to endpoints or bodies."""
        sc = self.scene()
        if sc is None:
            return None
        stick = max(WALL_PROJECT_STICK, 16.0 / max(self._view_scale(), 1e-6))
        best_s, best_d = None, stick
        for w in sc.items():
            if (not isinstance(w, WallItem) or w is self or w.is_open
                    or w.length() < 1e-6):
                continue
            v = w.unit()
            if abs(u.x() * v.x() + u.y() * v.y()) > 0.12:      # not orthogonal
                continue
            p = line_intersection(o, u, w.p1, v)
            if p is None:
                continue
            sp_ = (p.x() - o.x()) * u.x() + (p.y() - o.y()) * u.y()
            if sp_ <= MIN_WALL_LEN:                 # behind / at the anchor
                continue
            d = abs(sp_ - s)                         # drag distance to the line
            if d <= best_d and \
                    dist_point_segment(p, w.p1, w.p2) <= WALL_PROJECT_NEAR:
                best_s, best_d = sp_, d
        return best_s

    def _corner_target(self, sp: QPointF, mods) -> QPointF:
        """Endpoint target for a room wall: move the end along the wall
        (Shift = any direction, Ctrl = fixed 15 deg increments), grid-snapped
        and sticking to an orthogonal wall's projected line, WITHOUT fusing to
        neighbours -- so the corner can be pulled away to open a side."""
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))
        if mods & Qt.KeyboardModifier.ControlModifier:
            return self._angle_snapped_target(sp)
        return self._axis_target(sp)

    def _collinear_run(self):
        """The full room 'side' this wall lies on: every wall of the same room
        (real and dashed open walls) that is collinear with it.  Body-sliding
        the wall moves the whole side -- including the open-wall gap -- as one,
        so the dashed segment travels with the wall."""
        if not self.rooms or self.length() < 1e-6:
            return [self]
        u = self.unit()
        run = []
        side = {self}
        for r in self.rooms:
            side.update(r.walls)
        for w in side:
            if w is self:
                run.append(w)
                continue
            if w.length() < 1e-6:
                continue
            wu = w.unit()
            if abs(wu.x() * u.y() - wu.y() * u.x()) > 0.02:   # not parallel
                continue
            d = abs((w.p1.x() - self.p1.x()) * u.y()           # off this line?
                    - (w.p1.y() - self.p1.y()) * u.x())
            if d <= 1.5:
                run.append(w)
        return run

    def mouseMoveEvent(self, e):
        if self._mode is None:
            return
        sp = e.scenePos()
        target = (self._corner_target if self.rooms
                  else self._endpoint_target)
        if self._mode == "p1":
            self.p1 = target(sp, e.modifiers())
        elif self._mode == "p2":
            self.p2 = target(sp, e.modifiers())
        elif self._mode == "move":
            delta = QPointF(sp.x() - self._press.x(), sp.y() - self._press.y())
            if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl: move freely in any direction
                np1 = wall_snap(QPointF(self._o1.x() + delta.x(),
                                        self._o1.y() + delta.y()))
                dx, dy = np1.x() - self._o1.x(), np1.y() - self._o1.y()
            else:
                # slide only orthogonally to the wall: each end rides the
                # line projected perpendicular from its starting point, so
                # attached rooms stay rectangular instead of shearing
                ux, uy = self._slide_u.x(), self._slide_u.y()
                nx_, ny_ = -uy, ux
                s = wall_snap_len(delta.x() * nx_ + delta.y() * ny_)
                dx, dy = nx_ * s, ny_ * s
            # translate the whole collinear side (self + open-wall gap + any
            # collinear neighbours) by the same delta
            for w, o1, o2 in self._run_orig:
                w.p1 = QPointF(o1.x() + dx, o1.y() + dy)
                w.p2 = QPointF(o2.x() + dx, o2.y() + dy)
                if w is not self:
                    w.rebuild()
            # corner joints follow fully; T-joints follow only the sideways
            # part of the slide so they stretch instead of tilting
            ux, uy = self._slide_u.x(), self._slide_u.y()
            along = dx * ux + dy * uy
            px, py = dx - along * ux, dy - along * uy
            for w, attr, orig, is_corner in self._attached:
                if is_corner:
                    setattr(w, attr, QPointF(orig.x() + dx, orig.y() + dy))
                else:
                    setattr(w, attr, QPointF(orig.x() + px, orig.y() + py))
                w.rebuild()
        self.rebuild()
        e.accept()

    def mouseReleaseEvent(self, e):
        if self._mode is not None:
            # A wall is left exactly where the drag put it -- never snapped to
            # another wall on release, so a body-slide can't yank an end over
            # and tilt the wall.  Stretching an end (p1/p2) only sticks to an
            # orthogonal projected line while dragging (and a free wall fuses
            # if it now overlaps a same-type one); the angle changes only with
            # Shift.
            endpoint_edit = self._mode in ("p1", "p2")
            corner_drag = endpoint_edit and bool(self.rooms)
            coalesce_wall(self.scene(), self)       # fuse if it now overlaps
            rebuild_all_walls(self.scene())
            # dragging a corner back so the room is fully walled again fuses
            # the wall back in: re-lock its corners (right-click to detach
            # again)
            if (corner_drag and self._corners_unlocked
                    and not any(w.is_open for r in self.rooms
                                for w in r.walls)):
                self._corners_unlocked = False
                self.primary_room.raise_to_front()   # normalise z to siblings
        self._mode = None
        e.accept()

    def join_endpoints(self, rebuild=True):
        """Weld each endpoint onto a nearby endpoint of another wall, or onto
        the body of a wall it stops on (T-junction), within JOIN_TOL.  Never
        grows a wall toward a far one -- if it doesn't reach, the gap is left
        for the user to close by hand.  Pass rebuild=False in a bulk weld where
        a single rebuild_all_walls follows."""
        for attr, other in (("p1", "p2"), ("p2", "p1")):
            p = getattr(self, attr)
            q = nearest_wall_endpoint(self.scene(), p, JOIN_TOL, exclude=self)
            if q is None:
                hit = nearest_wall_body(self.scene(), p, JOIN_TOL, exclude=self)
                if hit is not None:
                    target, q = hit
                    ip = axis_wall_intersection(target, getattr(self, other), p)
                    if ip is not None and QLineF(ip, p).length() <= JOIN_TOL * 2:
                        q = ip
            if q is not None:
                setattr(self, attr, q)
        if rebuild:
            self.rebuild()

    def contextMenuEvent(self, e):
        from floorplanner.rooms import detach_wall_from_room  # late (cycle)
        menu = QMenu()
        a_ext = menu.addAction("Exterior wall (6\")")
        a_ext.setCheckable(True)
        a_ext.setChecked(self.wall_type == "exterior")
        a_int = menu.addAction("Interior wall (4 1/2\")")
        a_int.setCheckable(True)
        a_int.setChecked(self.wall_type == "interior")
        a_detach = None
        if self.rooms:
            menu.addSeparator()
            a_detach = menu.addAction("Detach wall from room")
        menu.addSeparator()
        a_del = menu.addAction("Delete wall")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        sc = self.scene()
        if chosen is a_ext:
            self.wall_type = "exterior"
            self.rebuild()
        elif chosen is a_int:
            self.wall_type = "interior"
            self.rebuild()
        elif a_detach is not None and chosen is a_detach and sc is not None:
            self.setSelected(True)
            detach_wall_from_room(sc, self)   # opens the vacated edge
        elif chosen is a_del and sc is not None:
            fracture_delete_wall(sc, self)   # keep room-edge stretches intact
        e.accept()


class OpenWall(WallItem):
    """A dashed placeholder for a room edge that has no built wall.

    It belongs to a room's edge loop (so the room stays closed for area
    and re-detection through the gap) and carries the SAME drag controls
    as a wall, but it does not block room flood-fill and is drawn as a thin
    dashed line.  Open walls are derived from a room's open edges, so they
    are regenerated by bind_room_walls rather than serialized."""

    is_open = True

    def __init__(self, p1: QPointF, p2: QPointF, room=None):
        super().__init__(p1, p2, "interior")
        self.rooms = [room] if room is not None else []
        self.setZValue(WALL_Z)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        lod = max(option.levelOfDetailFromTransform(painter.worldTransform()),
                  1e-6)
        pen = QPen(QColor(90, 120, 170), max(1.2, 1.6 / lod),
                   Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(self.p1, self.p2)
        if self.isSelected():
            hs = 9.0 / lod
            painter.setPen(QPen(QColor(40, 40, 40), 0))
            painter.setBrush(QBrush(QColor(255, 200, 0)))
            for q in (self.p1, self.p2):
                painter.drawRect(QRectF(q.x() - hs / 2, q.y() - hs / 2, hs, hs))


class OpeningItem(QGraphicsItem):
    """A door or window.  Child of its wall; local x runs along the wall,
    local y across the thickness.  `s` = distance of centre from wall.p1."""

    def __init__(self, wall: WallItem, kind: str, code: str, s: float):
        super().__init__(wall)
        self.wall = wall
        self.kind = kind                  # 'door' | 'window'
        self.code = "3280"
        self.width, self.height = 32.0, 80.0
        self.door_type = "LH"
        self.swing = -1                   # -1 / +1 : which face it swings to
        self.s = s
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(OPENING_Z)
        self.set_code(code, rebuild=False)
        self.sync()

    # -- data -----------------------------------------------------------------
    def set_code(self, code: str, rebuild: bool = True):
        w, h = parse_wwhh(code)
        if w > self.wall.length():
            raise ValueError("Opening is wider than the wall.")
        self.code = code.strip()
        self.prepareGeometryChange()
        self.width, self.height = w, h
        if rebuild:
            self.wall.rebuild()           # re-cuts the gap, re-syncs children

    def set_door_type(self, name: str):
        """Change the door type; garage doors auto-size an undersized
        opening to their standard size (if the wall is long enough)."""
        self.prepareGeometryChange()
        self.door_type = name
        if name in GARAGE_DEFAULTS:
            code, min_w = GARAGE_DEFAULTS[name]
            if self.width < min_w:
                try:
                    self.set_code(code)
                except ValueError:
                    pass                  # wall too short: keep the size
        self.update()

    def sync(self):
        """Reposition/orient on the wall after any wall geometry change."""
        self.prepareGeometryChange()
        self.setPos(self.wall.point_at(self.s))
        self.setRotation(math.degrees(self.wall.angle_rad()))
        self.update()

    # -- QGraphicsItem ---------------------------------------------------------
    def boundingRect(self) -> QRectF:
        # Tightly bound only what paint() actually draws (local coords: x
        # along the wall, y across it).  A swing arc / overhead outline
        # reaches out on its swing side; everything else stays in the
        # opening footprint.  (A symmetric width+16 margin made the rect
        # huge for wide openings, ballooning any enclosing group's box.)
        w, t = self.width, self.wall.t
        x0, x1, y0, y1 = -w / 2, w / 2, -t / 2, t / 2
        if self.kind == "door":
            dt = self.door_type
            reach = {"LH": w, "RH": w, "FRENCH": w / 2,
                     "BIFOLD": 0.4 * w}.get(dt, 0.0)
            if dt in GARAGE_DEFAULTS:
                reach = min(self.height, 96.0)
            if self.swing < 0:
                y0 -= reach
            else:
                y1 += reach
            if dt == "POCKET":
                x0 -= w               # the panel slides into the wall
        pad = 18.0                    # line widths + the WWHH label
        return QRectF(x0 - pad, y0 - pad,
                      (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)

    def shape(self) -> QPainterPath:
        w, t = self.width, self.wall.t
        p = QPainterPath()
        p.addRect(QRectF(-w / 2, -t / 2 - 1, w, t + 2))
        return p

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, t = self.width, self.wall.t
        ink = QPen(QColor(20, 20, 20), 0)
        painter.setPen(ink)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # jambs (the cut ends of the wall)
        painter.drawLine(QPointF(-w / 2, -t / 2), QPointF(-w / 2, t / 2))
        painter.drawLine(QPointF(w / 2, -t / 2), QPointF(w / 2, t / 2))

        if self.kind == "window":
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(QRectF(-w / 2, -t / 2, w, t))
            painter.drawLine(QPointF(-w / 2, 0), QPointF(w / 2, 0))   # glazing
        else:
            self._paint_door(painter, w, t)

        # WWHH label, kept clear of the swing side
        f = QFont()
        f.setPixelSize(6)
        painter.setFont(f)
        painter.setPen(QPen(QColor(70, 70, 90) if not self.isSelected()
                            else QColor(0, 122, 255), 0))
        label = self.code if self.kind == "window" else f"{self.code} {self.door_type}"
        if self.kind == "door" and self.swing < 0:
            ty = t / 2 + 9
        else:
            ty = -t / 2 - 3
        painter.drawText(QPointF(-w / 2, ty), label)

        if self.isSelected():
            painter.setPen(QPen(QColor(0, 122, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-w / 2, -t / 2 - 1, w, t + 2))

    def _swing_arc(self, painter, hx, hy, sy, radius, hinge_left):
        """Door panel + quarter-circle swing arc from a hinge point."""
        painter.drawLine(QPointF(hx, hy), QPointF(hx, hy + sy * radius))
        rect = QRectF(hx - radius, hy - radius, 2 * radius, 2 * radius)
        if sy < 0:
            start = 0 if hinge_left else 90      # ends at N (visually up)
        else:
            start = 270 if hinge_left else 180   # ends at S (visually down)
        painter.drawArc(rect, start * 16, 90 * 16)

    def _paint_door(self, painter, w, t):
        sy = self.swing
        face = sy * t / 2
        dt = self.door_type
        white = QBrush(QColor(255, 255, 255))

        if dt == "LH":
            self._swing_arc(painter, -w / 2, face, sy, w, hinge_left=True)
        elif dt == "RH":
            self._swing_arc(painter, w / 2, face, sy, w, hinge_left=False)
        elif dt == "FRENCH":
            self._swing_arc(painter, -w / 2, face, sy, w / 2, hinge_left=True)
            self._swing_arc(painter, w / 2, face, sy, w / 2, hinge_left=False)
        elif dt == "BIFOLD":
            rise = sy * 0.35 * w
            painter.drawPolyline(QPolygonF([
                QPointF(-w / 2, face), QPointF(-w / 4, face + rise),
                QPointF(0, face)]))
            painter.drawPolyline(QPolygonF([
                QPointF(0, face), QPointF(w / 4, face + rise),
                QPointF(w / 2, face)]))
        elif dt == "POCKET":
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.setBrush(white)
            painter.drawRect(QRectF(-w / 2 - w, -t / 2 + 0.75, w, t - 1.5))
            painter.setPen(QPen(QColor(20, 20, 20), 0))
            painter.drawRect(QRectF(-w / 2, -t / 6, w / 2, t / 3))
        elif dt == "SLIDER":
            painter.setBrush(white)
            pw = 0.55 * w
            painter.drawRect(QRectF(-w / 2, -t * 0.35, pw, t * 0.30))
            painter.drawRect(QRectF(w / 2 - pw, t * 0.05, pw, t * 0.30))
        elif dt == "DOORWAY":
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.drawLine(QPointF(-w / 2, -t / 2), QPointF(w / 2, -t / 2))
            painter.drawLine(QPointF(-w / 2, t / 2), QPointF(w / 2, t / 2))
        elif dt in GARAGE_DEFAULTS:
            # closed panel in the opening + dashed OVERHEAD outline of the
            # open door projecting inward (the swing side), as deep as the
            # door is tall
            painter.setBrush(white)
            painter.drawRect(QRectF(-w / 2, -t * 0.25, w, t * 0.5))
            depth = sy * min(self.height, 96.0)
            y0 = sy * t / 2
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-w / 2, min(y0, y0 + depth),
                                    w, abs(depth)))
            if dt == "GARAGE-2":          # double-wide: two-car divider
                painter.drawLine(QPointF(0, y0), QPointF(0, y0 + depth))

    # -- interaction -------------------------------------------------------------
    def mousePressEvent(self, e):
        if self.wall is not None and self.wall.group() is not None:
            # the opening's wall is grouped: let the group own the drag
            # instead of sliding the opening along its wall
            e.ignore()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)
            return
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.setSelected(not self.isSelected())    # toggle membership
            e.accept()
            return
        if not self.isSelected():
            self.scene().clearSelection()
        self.setSelected(True)
        if self.wall is not None and self.wall.rooms:
            self.wall.primary_room.raise_to_front()
        e.accept()

    def mouseMoveEvent(self, e):
        if self.wall is not None and self.wall.group() is not None:
            e.ignore()
            return
        # slide along the wall, snapping to the nearest inch
        s = round(self.wall.s_of(e.scenePos()))
        half = self.width / 2
        self.s = min(max(s, half), max(half, self.wall.length() - half))
        self.wall.rebuild()             # cascades to the coincident party wall
        e.accept()

    def mouseDoubleClickEvent(self, e):
        self._prompt_size()
        e.accept()

    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def _prompt_size(self):
        v = self._view()
        code, ok = QInputDialog.getText(
            v, f"{self.kind.title()} size",
            'Size WWHH (width inches, height inches):', text=self.code)
        if not ok:
            return
        try:
            self.set_code(code)
        except ValueError as ex:
            QMessageBox.warning(v, "Invalid size", str(ex))

    def contextMenuEvent(self, e):
        menu = QMenu()
        type_actions = {}
        if self.kind == "door":
            tmenu = menu.addMenu("Type")
            for name in DOOR_TYPES:
                a = tmenu.addAction(name)
                a.setCheckable(True)
                a.setChecked(name == self.door_type)
                type_actions[a] = name
            a_flip = menu.addAction("Flip swing side")
        else:
            a_flip = None
        a_size = menu.addAction("Set size (WWHH)\u2026")
        menu.addSeparator()
        a_del = menu.addAction(f"Delete {self.kind}")
        a_front, a_back = add_front_back_actions(menu)

        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen in type_actions:
            self.set_door_type(type_actions[chosen])
        elif chosen is a_flip and a_flip is not None:
            self.swing = -self.swing
            self.update()
        elif chosen is a_size:
            self._prompt_size()
        elif chosen is a_del:
            wall, sc = self.wall, self.scene()
            if self in wall.openings:
                wall.openings.remove(self)
            sc.removeItem(self)
            wall.rebuild()
        e.accept()
