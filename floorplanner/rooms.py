"""The RoomItem graphics item plus room detection/binding algorithms and the
room-edge helpers.

Imports wall items + a few wall algorithms from floorplanner.walls at module
level (walls loads first).  FurnishingItem and the room dialogs are reached via
LATE imports to avoid an import cycle."""
import math
from collections import deque

from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.walls import (
    OpenWall, OpeningItem, WallItem, _WallBBoxIndex, coalesce_all,
    rebuild_all_walls, wall_bbox,
)


class _RoomGrid:
    """All non-open walls rasterised (solid, openings ignored) onto a flood-
    fill grid over the canvas.  Built ONCE so many room regions can be located
    against the same grid -- refresh_rooms re-detects every room from one grid
    instead of rebuilding it per room (the old O(rooms x walls) cost)."""

    def __init__(self, scene):
        canvas = canvas_rect()
        self.canvas = canvas
        self.cell = cell = ROOM_CELL
        self.x0, self.y0 = x0, y0 = canvas.left(), canvas.top()
        self.nx = nx = int(canvas.width() / cell)
        self.ny = ny = int(canvas.height() / cell)
        self.blocked = blocked = bytearray(nx * ny)
        self.has_walls = False
        if scene is None:
            return
        for w in scene.items():
            if not isinstance(w, WallItem) or w.is_open:
                continue
            length = w.length()
            if length < 1e-6:
                continue
            self.has_walls = True
            u = w.unit()
            ux, uy = u.x(), u.y()
            p1x, p1y = w.p1.x(), w.p1.y()
            p2x, p2y = w.p2.x(), w.p2.y()
            half = w.t * 0.5 + cell * 0.5
            i0 = max(0, int((min(p1x, p2x) - half - x0) / cell))
            i1 = min(nx - 1, int((max(p1x, p2x) + half - x0) / cell))
            j0 = max(0, int((min(p1y, p2y) - half - y0) / cell))
            j1 = min(ny - 1, int((max(p1y, p2y) + half - y0) / cell))
            for j in range(j0, j1 + 1):
                cy = y0 + (j + 0.5) * cell
                row = j * nx
                for i in range(i0, i1 + 1):
                    cx = x0 + (i + 0.5) * cell
                    dx, dy = cx - p1x, cy - p1y
                    s = dx * ux + dy * uy
                    if -half <= s <= length + half \
                            and abs(dy * ux - dx * uy) <= half:
                        blocked[row + i] = 1

    def region(self, p: QPointF):
        """(QPainterPath, area_sqft) for the enclosed region containing `p`, or
        None when it leaks to the canvas edge or `p` sits on a wall."""
        if not self.has_walls or not self.canvas.contains(p):
            return None
        cell, x0, y0 = self.cell, self.x0, self.y0
        nx, ny, blocked = self.nx, self.ny, self.blocked
        si, sj = int((p.x() - x0) / cell), int((p.y() - y0) / cell)
        if not (0 <= si < nx and 0 <= sj < ny) or blocked[sj * nx + si]:
            return None
        seen = bytearray(nx * ny)
        seen[sj * nx + si] = 1
        queue = deque([(si, sj)])
        cells = []
        while queue:
            i, j = queue.popleft()
            if i == 0 or j == 0 or i == nx - 1 or j == ny - 1:
                return None                 # leaked out -> not enclosed
            cells.append((i, j))
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                k = b * nx + a
                if not seen[k] and not blocked[k]:
                    seen[k] = 1
                    queue.append((a, b))
        rows = {}
        for i, j in cells:
            rows.setdefault(j, []).append(i)
        path = QPainterPath()
        for j, cols in rows.items():
            cols.sort()
            start = prev = cols[0]
            for i in cols[1:] + [None]:
                if i is not None and i == prev + 1:
                    prev = i
                    continue
                path.addRect(QRectF(x0 + start * cell, y0 + j * cell,
                                    (prev - start + 1) * cell, cell))
                if i is not None:
                    start = prev = i
        area_sqft = len(cells) * cell * cell / 144.0
        return path.simplified(), area_sqft


def detect_room_region(scene, p: QPointF):
    """Flood-fill the empty space around `p`, bounded by wall bodies.  Returns
    (QPainterPath, area_sqft) in scene coords, or None.  See _RoomGrid."""
    return _RoomGrid(scene).region(p)


def poly_area_sqft(corners) -> float:
    """Shoelace area of a closed polygon (inches) in square feet."""
    n = len(corners)
    a2 = 0.0
    for i in range(n):
        p, q = corners[i], corners[(i + 1) % n]
        a2 += p.x() * q.y() - q.x() * p.y()
    return abs(a2) / 2.0 / 144.0


class _WallGraph:
    """Planar graph of wall centrelines, split where walls join (corner/T) or
    cross.  Built ONCE so the enclosing face around many anchors can be walked
    against the same graph (refresh_rooms traces every room from one graph).

    The O(walls^2) split-finding caches endpoints as floats to avoid millions
    of QPointF.x()/.y() calls."""

    def __init__(self, scene):
        self.nodes = []           # QPointF per node
        self.edges = set()
        self.adj = {}
        walls = [it for it in (scene.items() if scene is not None else [])
                 if isinstance(it, WallItem) and not it.is_open
                 and it.length() > 1e-6]
        if not walls:
            return
        segs = []                 # (length, ux, uy, p1x, p1y, p2x, p2y)
        for w in walls:
            length, u = w.length(), w.unit()
            segs.append((length, u.x(), u.y(),
                         w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()))
        nc = []                   # node coords (x, y) parallel to self.nodes
        nodes, edges = self.nodes, self.edges

        def node_id(px, py):
            for k, (qx, qy) in enumerate(nc):
                if abs(qx - px) <= 0.6 and abs(qy - py) <= 0.6:
                    return k
            nc.append((px, py))
            nodes.append(QPointF(px, py))
            return len(nc) - 1

        for i, (length, ux, uy, p1x, p1y, p2x, p2y) in enumerate(segs):
            splits = {0.0, length}
            d1x, d1y = p2x - p1x, p2y - p1y
            for j, (_l2, _u2x, _u2y, q1x, q1y, q2x, q2y) in enumerate(segs):
                if i == j:
                    continue
                for qx, qy in ((q1x, q1y), (q2x, q2y)):   # T: endpoint on body
                    vx, vy = qx - p1x, qy - p1y
                    s = vx * ux + vy * uy
                    if 0.5 < s < length - 0.5 \
                            and abs(vy * ux - vx * uy) <= 0.75:
                        splits.add(s)
                d2x, d2y = q2x - q1x, q2y - q1y           # X: true crossing
                den = d1x * d2y - d1y * d2x
                if abs(den) > 1e-9:
                    ex, ey = q1x - p1x, q1y - p1y
                    t1 = (ex * d2y - ey * d2x) / den
                    t2 = (ex * d1y - ey * d1x) / den
                    if 0.0 <= t1 <= 1.0 and 0.0 <= t2 <= 1.0:
                        s = t1 * length
                        if 0.5 < s < length - 0.5:
                            splits.add(s)
            ss = sorted(splits)
            for a, b in zip(ss, ss[1:], strict=False):
                if b - a < 0.5:
                    continue
                na = node_id(p1x + a * ux, p1y + a * uy)
                nb = node_id(p1x + b * ux, p1y + b * uy)
                if na != nb:
                    edges.add((min(na, nb), max(na, nb)))
        for a, b in edges:
            self.adj.setdefault(a, []).append(b)
            self.adj.setdefault(b, []).append(a)

    def face(self, anchor: QPointF):
        """Corner QPointFs of the enclosing face around `anchor`, or None."""
        nodes, edges, adj = self.nodes, self.edges, self.adj
        if not edges:
            return None
        # +x ray from the anchor: the nearest crossing edge, oriented with the
        # anchor on its left, starts the face walk
        ax, ay = anchor.x(), anchor.y()
        start, best_x = None, None
        for a, b in edges:
            pa, pb = nodes[a], nodes[b]
            if (pa.y() > ay) == (pb.y() > ay):
                continue
            x_at = pa.x() + (ay - pa.y()) * (pb.x() - pa.x()) / (pb.y() - pa.y())
            if x_at <= ax or (best_x is not None and x_at >= best_x):
                continue
            cross = ((pb.x() - pa.x()) * (ay - pa.y())
                     - (pb.y() - pa.y()) * (ax - pa.x()))
            start, best_x = ((a, b) if cross > 0 else (b, a)), x_at
        if start is None:
            return None
        # at each node take the next edge clockwise from the reversed incoming
        # direction; this keeps the enclosed face on the left
        poly = [start[0]]
        cur = start
        for _ in range(2 * len(edges) + 8):
            u_, v_ = cur
            pv = nodes[v_]
            th_rev = math.atan2(nodes[u_].y() - pv.y(), nodes[u_].x() - pv.x())
            nxt, best_d = None, None
            for wn in adj[v_]:
                th = math.atan2(nodes[wn].y() - pv.y(), nodes[wn].x() - pv.x())
                delta = (th_rev - th) % (2.0 * math.pi)
                if delta < 1e-9:
                    delta = 2.0 * math.pi     # U-turn only as a last resort
                if best_d is None or delta < best_d:
                    best_d, nxt = delta, wn
            cur = (v_, nxt)
            if cur == start:
                break
            poly.append(v_)
        else:
            return None                       # never closed -> give up
        if len(poly) < 3:
            return None
        pts = [nodes[k] for k in poly]
        n = len(pts)
        if sum(pts[i].x() * pts[(i + 1) % n].y()
               - pts[(i + 1) % n].x() * pts[i].y() for i in range(n)) <= 0:
            return None                       # walked the unbounded outer face
        corners = []
        for i in range(n):                    # drop straight pass-through nodes
            p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
            ax1, ay1 = p1.x() - p0.x(), p1.y() - p0.y()
            bx1, by1 = p2.x() - p1.x(), p2.y() - p1.y()
            cross = ax1 * by1 - ay1 * bx1
            dot = ax1 * bx1 + ay1 * by1
            if dot < 0.0 or abs(cross) > \
                    0.05 * math.hypot(ax1, ay1) * math.hypot(bx1, by1):
                corners.append(QPointF(p1))
        return corners if len(corners) >= 3 else None


def trace_room_perimeter(scene, anchor: QPointF):
    """Polygon of wall-CENTRELINE corners enclosing `anchor`, or None.  See
    _WallGraph."""
    return _WallGraph(scene).face(anchor)


def _detect_room(grid, graph, anchor):
    """Detect the room at `anchor` against a prebuilt grid + graph."""
    res = grid.region(anchor)
    if res is None:
        return None
    path, area = res
    corners = graph.face(anchor)
    if corners:
        area = poly_area_sqft(corners)
    return path, area, corners


def detect_room(scene, anchor: QPointF):
    """Full room detection: flood-fill region + centreline perimeter.

    Returns (path, area_sqft, corners) or None.  When the perimeter trace
    succeeds, the area is the area inside the perimeter polygon; otherwise
    the flood-fill area is the fallback and corners is None."""
    return _detect_room(_RoomGrid(scene), _WallGraph(scene), anchor)


def unique_room_name(scene, base: str, exclude=None) -> str:
    """`base` if unused in the plan, else `base 2`, `base 3`, ..."""
    names = {it.name for it in scene.items()
             if isinstance(it, RoomItem) and it is not exclude}
    if base not in names:
        return base
    n = 2
    while f"{base} {n}" in names:
        n += 1
    return f"{base} {n}"


def room_signature(scene, room, wall_index=None):
    """A hash of the walls that can affect `room`: every wall whose bbox is
    within ROOM_SIG_MARGIN of the room's region bbox, with its geometry, type
    and open-state.  Two equal signatures mean the room's detection is
    unchanged, so it can be skipped.  Returns None for an open/undetected room
    (whose flood escapes through a gap and so depends on far walls) -- those
    are always re-detected."""
    if any(w.is_open for w in room.walls):
        return None
    br = room.path.boundingRect()
    if br.isNull():
        return None
    box = br.adjusted(-ROOM_SIG_MARGIN, -ROOM_SIG_MARGIN,
                      ROOM_SIG_MARGIN, ROOM_SIG_MARGIN)
    near = (wall_index.near(box) if wall_index is not None
            else [w for w in scene.items() if isinstance(w, WallItem)
                  and wall_bbox(w).intersects(box)])
    sig = [(round(w.p1.x()), round(w.p1.y()), round(w.p2.x()), round(w.p2.y()),
            w.wall_type, w.is_open) for w in near]
    return tuple(sorted(sig))


def refresh_rooms(scene):
    """Re-detect rooms after walls change -- but ONLY those whose defining
    walls actually changed (memoized by room_signature), and skip the whole
    grid/graph build when nothing is dirty.  An edit then recomputes just the
    one or two rooms it touched, not every room on the canvas.

    When a re-detected room's anchor no longer falls inside it, probe points
    across the room's last known region for its new extent and move the anchor
    there -- skipping any region that already belongs to another room."""
    if scene is None:
        return
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    if not rooms:
        return
    wall_index = _WallBBoxIndex(scene)      # O(local) 'walls near this room'
    dirty = []
    for it in rooms:
        sig = room_signature(scene, it, wall_index)
        if sig is None or sig != it._detect_sig:
            dirty.append(it)
    if not dirty:
        return                              # nothing relevant changed
    grid, graph = _RoomGrid(scene), _WallGraph(scene)
    for it in dirty:
        res = _detect_room(grid, graph, it.anchor)
        if res is None:
            others = [r for r in rooms if r is not it]
            for p in _room_probe_points(it):
                cand = _detect_room(grid, graph, p)
                if cand is None or any(cand[0].contains(o.anchor)
                                       for o in others):
                    continue
                res = cand
                it.prepareGeometryChange()
                it.anchor = QPointF(p)
                break
        if res is None and it.corners:
            # the room is open (a corner was pulled away) so flood-fill escapes:
            # rebuild the loop from the room's own walls, inserting corners and
            # dashed open segments wherever consecutive walls no longer meet
            res = reloop_open_room(it)
        if res is not None:
            it.set_region(*res)
            # re-affirm wall ownership against the new perimeter; settle=False
            # so we don't recurse back into rebuild_all_walls/refresh_rooms
            bind_room_walls(scene, it, settle=False)
        it._detect_sig = room_signature(scene, it)   # remember for next time


def _room_probe_points(room) -> list:
    """Candidate interior points for re-finding a room whose anchor was
    left outside: the old perimeter's centroid, then a grid sample of
    the old region."""
    pts = []
    if room.corners:
        n = len(room.corners)
        pts.append(QPointF(sum(p.x() for p in room.corners) / n,
                           sum(p.y() for p in room.corners) / n))
    br = room.path.boundingRect()
    for iy in range(1, 6):
        for ix in range(1, 6):
            p = QPointF(br.left() + br.width() * ix / 6.0,
                        br.top() + br.height() * iy / 6.0)
            if room.path.contains(p):
                pts.append(p)
    return pts


class RoomItem(QGraphicsItem):
    """A named room: the wall-enclosed region around an anchor point.

    The translucent region, label and dimension arrows paint in scene
    coords (pos stays 0,0).  Only the label text is clickable, so wall
    editing and panning inside the room keep working.  Right-click the
    name for dimensions / properties / rename / delete."""

    def __init__(self, name: str, anchor: QPointF, path: QPainterPath,
                 area_sqft: float, properties=None, corners=None):
        super().__init__()
        self.name = name
        self.anchor = QPointF(anchor)
        self.label_offset = QPointF(0.0, 0.0)   # label drag, relative to anchor
        self._dragging_label = False
        self.path = QPainterPath(path)
        self.area_sqft = float(area_sqft)
        self.corners = [QPointF(c) for c in corners] if corners else None
        self.walls = []                  # WallItems this room owns (edge loop)
        self._detect_sig = None          # memoize: walls that defined this room
        self._moving_room = False        # drag-the-name moves the whole room
        self._room_grab = QPointF(0.0, 0.0)
        self.show_dims = False
        self.properties = dict(DEFAULT_ROOM_PROPS)
        if properties:
            self.properties.update(properties)
        self._sync_corner_props()
        self._font = QFont(FONT_FAMILY)
        self._font.setPixelSize(14)       # 14" tall text reads well at plan scale
        self._sub_font = QFont(FONT_FAMILY)
        self._sub_font.setPixelSize(9)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # above the walls: the fill only covers floor space (it stops at
        # the wall faces) and the perimeter dashes must paint OVER the walls
        self.setZValue(4)

    # -- data ------------------------------------------------------------------
    def set_region(self, path: QPainterPath, area_sqft: float, corners=None):
        self.prepareGeometryChange()
        self.path = QPainterPath(path)
        self.area_sqft = float(area_sqft)
        self.corners = [QPointF(c) for c in corners] if corners else None
        self._sync_corner_props()
        self.update()

    def _sync_corner_props(self):
        """Mirror the perimeter corner coordinates into the properties."""
        if self.corners:
            self.properties["perimeter_corners"] = [
                [round(c.x(), 2), round(c.y(), 2)] for c in self.corners]
        else:
            self.properties.pop("perimeter_corners", None)

    def interior_rect(self) -> QRectF:
        return self.path.boundingRect()

    def perimeter_in(self) -> float:
        if self.corners:
            n = len(self.corners)
            return sum(QLineF(self.corners[i], self.corners[(i + 1) % n]).length()
                       for i in range(n))
        poly = self.path.toFillPolygon()
        return sum(QLineF(poly[i], poly[i + 1]).length()
                   for i in range(poly.size() - 1))

    def _perimeter_span(self, w) -> tuple | None:
        """[s0, s1] of wall `w`'s centreline that runs along this room's
        perimeter, or None when the wall doesn't follow any edge of it."""
        if not self.corners:
            return None
        u, length = w.unit(), w.length()
        lo = hi = None
        n = len(self.corners)
        for i in range(n):
            a, b = self.corners[i], self.corners[(i + 1) % n]
            da = abs((a.y() - w.p1.y()) * u.x() - (a.x() - w.p1.x()) * u.y())
            db = abs((b.y() - w.p1.y()) * u.x() - (b.x() - w.p1.x()) * u.y())
            if max(da, db) > 1.0:         # edge not collinear with the wall
                continue
            sa = (a.x() - w.p1.x()) * u.x() + (a.y() - w.p1.y()) * u.y()
            sb = (b.x() - w.p1.x()) * u.x() + (b.y() - w.p1.y()) * u.y()
            s0, s1 = max(0.0, min(sa, sb)), min(length, max(sa, sb))
            if s1 - s0 < 1.0:
                continue
            lo = s0 if lo is None else min(lo, s0)
            hi = s1 if hi is None else max(hi, s1)
        if lo is None or hi - lo < MIN_WALL_LEN:
            return None
        return lo, hi

    def _copy_spec(self) -> dict:
        """Clipboard payload: the room plus its bounding walls/openings,
        each wall trimmed to the stretch that follows the room perimeter
        (shared/through walls don't drag their full length along)."""
        walls = []
        for w in self.bounding_walls():
            span = self._perimeter_span(w)
            if span is None:
                if self.corners:
                    continue              # touches the room but isn't part
                span = (0.0, w.length())  # of the perimeter -> don't copy
            lo, hi = span
            tp1, tp2 = w.point_at(lo), w.point_at(hi)
            walls.append({
                "type": w.wall_type,
                "p1": [tp1.x(), tp1.y()],
                "p2": [tp2.x(), tp2.y()],
                "openings": [{
                    "kind": op.kind, "code": op.code, "s": op.s - lo,
                    "door_type": op.door_type, "swing": op.swing,
                } for op in w.openings if lo <= op.s <= hi],
            })
        return {
            "name": self.name,
            "anchor": [self.anchor.x(), self.anchor.y()],
            "show_dimensions": self.show_dims,
            "properties": dict(self.properties),
            "walls": walls,
        }

    def _boundary_band(self) -> QPainterPath:
        # wide enough to safely contain the wall centrelines: the flood
        # region edge sits up to t/2 + one raster cell from a centreline,
        # and a point exactly on the stroke edge tests as outside
        stroker = QPainterPathStroker()
        stroker.setWidth(3.0 * EXTERIOR_T)
        return stroker.createStroke(self.path)

    def bounding_walls(self):
        """Walls whose body touches this room's boundary."""
        sc = self.scene()
        if sc is None:
            return []
        band = self._boundary_band()
        return [it for it in sc.items()
                if isinstance(it, WallItem) and it._hit.intersects(band)]

    def interior_walls(self):
        """Real walls that lie wholly inside this room (partitions etc.) -- not
        part of its perimeter band."""
        sc = self.scene()
        if sc is None or self.path.isEmpty():
            return []
        band = self._boundary_band()
        return [it for it in sc.items()
                if isinstance(it, WallItem) and not it.is_open
                and not it._hit.intersects(band)
                and self.path.contains(it.p1) and self.path.contains(it.p2)]

    # -- owned walls (the room's edge loop) ----------------------------------
    def bind_wall(self, w):
        """Add this room to wall `w`'s set of bordering rooms.  A wall may be
        SHARED by several rooms (a coalesced party wall borders both), so this
        does not steal `w` from anyone -- it just adds the association."""
        if self not in w.rooms:
            w.rooms.append(self)
        if w not in self.walls:
            self.walls.append(w)

    def unbind_wall(self, w):
        """Detach this room from wall `w`.  Leaves `w` in the scene -- a shared
        wall survives for the other rooms that still border it."""
        if self in w.rooms:
            w.rooms.remove(self)
        if w in self.walls:
            self.walls.remove(w)

    def clear_walls(self):
        for w in list(self.walls):
            self.unbind_wall(w)

    def room_openings(self):
        return [op for w in self.walls for op in w.openings]

    def raise_to_front(self):
        """Bring this room and its owned walls/openings above every other
        room (uses a running max-z on the window; z is not serialized)."""
        win = None
        v = self._view()
        if v is not None:
            win = getattr(v, "win", None)
        if win is None or not hasattr(win, "_z_top"):
            return
        win._z_top += 1
        base = win._z_top * 10
        # the translucent fill + label sit at `base` (above OTHER rooms); the
        # walls/openings sit ABOVE the fill so a wall is never hidden under its
        # own room tint and a 'Bring to front' is not undone on the next click
        self.setZValue(base)
        for w in self.walls:
            # an unlocked wall sits just above its siblings so corner clicks
            # at a shared corner grab IT (to edit) rather than a locked neighbour
            w.setZValue(base + 5 if w._corners_unlocked else base + 4)
        for op in self.room_openings():
            op.setZValue(base + 6)

    def opening_stats(self):
        """(window count, window glazing sq ft, door count) on this
        room's bounding walls, counting only openings that sit on the
        stretch of wall actually facing the room."""
        band = self._boundary_band()
        wins, win_area, doors = 0, 0.0, 0
        for wall in self.bounding_walls():
            for op in wall.openings:
                if not band.contains(wall.point_at(op.s)):
                    continue
                if op.kind == "window":
                    wins += 1
                    win_area += op.width * op.height / 144.0
                else:
                    doors += 1
        return wins, win_area, doors

    # editable properties, in display order, for the inventory listing
    PROP_LABELS = [
        ("room_type", "Room type"),
        ("ceiling_height_in", "Ceiling height"),
        ("ceiling_type", "Ceiling type"),
        ("floor_finish", "Floor finish"),
        ("wall_finish", "Wall finish"),
        ("baseboard", "Baseboard / trim"),
        ("crown_molding", "Crown molding"),
        ("hvac", "Heating / cooling"),
        ("electrical", "Electrical"),
        ("notes", "Notes"),
    ]

    def inventory_rows(self) -> list:
        """Two-column (name, value/quantity) rows describing the room:
        its properties, then every item in it — furnishings whose centre
        sits inside the room plus the doors/windows on its walls."""
        from floorplanner.items import FurnishingItem  # late (cycle)

        def clean(v) -> str:
            return " ".join(str(v).split())     # no tabs/newlines in cells

        rows = [("Room", self.name), ("", ""), ("Property", "Value"),
                ("Area (sq ft)", f"{self.area_sqft:.1f}")]
        r = self.interior_rect()
        rows.append(("Interior width", fmt_ftin(r.width())))
        rows.append(("Interior length", fmt_ftin(r.height())))
        rows.append(("Perimeter", fmt_ftin(self.perimeter_in())))
        wins, win_area, doors = self.opening_stats()
        rows.append(("Window glazing (sq ft)", f"{win_area:.1f}"))
        for key, label in self.PROP_LABELS:
            v = self.properties.get(key, "")
            if key == "ceiling_height_in":
                v = fmt_ftin(float(v or 0))
            elif key == "crown_molding":
                v = "Yes" if v else "No"
            rows.append((label, clean(v)))

        counts = {}
        sc = self.scene()
        if sc is not None:
            for it in sc.items():
                if isinstance(it, FurnishingItem) and \
                        self.path.contains(it.pos()):
                    counts[it.name] = counts.get(it.name, 0) + 1
        band = self._boundary_band()
        for wall in self.bounding_walls():
            for op in wall.openings:
                if not band.contains(wall.point_at(op.s)):
                    continue
                if op.kind == "window":
                    name = f'Window {op.width:g}" × {op.height:g}"'
                else:
                    name = (f'Door {op.width:g}" × {op.height:g}" '
                            f'({op.door_type})')
                counts[name] = counts.get(name, 0) + 1

        rows += [("", ""), ("Item", "Quantity")]
        rows += [(n, str(q)) for n, q in sorted(counts.items())]
        return rows

    def inventory_text(self) -> str:
        """The inventory as tab-separated text, ready for Excel."""
        return "\n".join(f"{a}\t{b}" for a, b in self.inventory_rows())

    # -- QGraphicsItem -----------------------------------------------------------
    def _label_centre(self) -> QPointF:
        return QPointF(self.anchor.x() + self.label_offset.x(),
                       self.anchor.y() + self.label_offset.y())

    def _label_rect(self) -> QRectF:
        fm = QFontMetricsF(self._font)
        w = max(fm.horizontalAdvance(self.name), 48.0) + 10.0
        h = fm.height() + 13.0
        c = self._label_centre()
        return QRectF(c.x() - w / 2, c.y() - h / 2, w, h)

    def boundingRect(self) -> QRectF:
        r = self.path.boundingRect().united(self._label_rect())
        if self.corners:
            r = r.united(QPolygonF(self.corners).boundingRect())
        return r.adjusted(-24, -24, 24, 24)

    def shape(self) -> QPainterPath:
        p = QPainterPath()
        p.addRect(self._label_rect())
        return p

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(120, 170, 255, 26)))
        painter.drawPath(self.path)
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 122, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path)

        if self.corners and self.isSelected():
            # perimeter along wall centrelines, shown while selected
            painter.setPen(QPen(QColor(0, 110, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(QPolygonF(self.corners))

        r = self._label_rect()
        painter.setFont(self._font)
        painter.setPen(QPen(QColor(40, 40, 70), 0))
        painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                         | Qt.AlignmentFlag.AlignTop, self.name)
        painter.setFont(self._sub_font)
        painter.setPen(QPen(QColor(115, 115, 135), 0))
        painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                         | Qt.AlignmentFlag.AlignBottom,
                         f"{self.area_sqft:.0f} sq ft")
        if self.show_dims:
            self._paint_dims(painter)

    def _paint_dims(self, painter):
        """Double-headed arrows along every wall edge enclosing the room.
        Falls back to width/length arrows when no perimeter was traced."""
        col = QColor(178, 58, 40)
        painter.setPen(QPen(col, 0))
        painter.setBrush(QBrush(col))
        painter.setFont(self._sub_font)
        fm = QFontMetricsF(self._sub_font)

        if self.corners:
            n = len(self.corners)
            edges = []
            for i in range(n):
                a, b = self.corners[i], self.corners[(i + 1) % n]
                d = QLineF(a, b)
                length = d.length()
                if length < 18:
                    continue
                edges.append((a, b, length, d.dx() / length, d.dy() / length))
            shown = []
            for edge in edges:
                _, _, length, ux, uy = edge
                # opposite walls (anti-parallel) of equal length are
                # dimensioned only once
                if any(ux * vx + uy * vy < -0.999 and abs(length - vlen) < 1.0
                       for (_, _, vlen, vx, vy) in shown):
                    continue
                shown.append(edge)
            for a, b, length, ux, uy in shown:
                nx_, ny_ = -uy, ux        # room interior is left of the edge
                off = 14.0
                pa = QPointF(a.x() + ux * 4 + nx_ * off,
                             a.y() + uy * 4 + ny_ * off)
                pb = QPointF(b.x() - ux * 4 + nx_ * off,
                             b.y() - uy * 4 + ny_ * off)
                self._arrow(painter, pa, pb)
                text = fmt_ftin(length)
                ang = math.degrees(math.atan2(uy, ux))
                if ang > 90.0 or ang <= -90.0:
                    ang -= 180.0          # keep text upright
                painter.save()
                painter.translate(
                    QPointF((a.x() + b.x()) / 2 + nx_ * (off + 6),
                            (a.y() + b.y()) / 2 + ny_ * (off + 6)))
                painter.rotate(ang)
                painter.drawText(
                    QPointF(-fm.horizontalAdvance(text) / 2, 3), text)
                painter.restore()
            return

        r = self.interior_rect()
        if r.width() < 12 or r.height() < 12:
            return
        lc = self._label_centre()
        y = r.center().y()                # keep clear of the name label
        if abs(y - lc.y()) < 22:
            y = min(r.bottom() - 8, lc.y() + 26)
        self._arrow(painter, QPointF(r.left() + 1, y), QPointF(r.right() - 1, y))
        text = fmt_ftin(r.width())
        painter.drawText(QPointF(r.center().x() - fm.horizontalAdvance(text) / 2,
                                 y - 3), text)

        x = r.center().x()
        if abs(x - lc.x()) < 50:
            x = max(r.left() + 10, lc.x() - 60)
        self._arrow(painter, QPointF(x, r.top() + 1), QPointF(x, r.bottom() - 1))
        text = fmt_ftin(r.height())
        painter.save()
        painter.translate(x - 3, r.center().y() + fm.horizontalAdvance(text) / 2)
        painter.rotate(-90)
        painter.drawText(QPointF(0, 0), text)
        painter.restore()

    @staticmethod
    def _arrow(painter, a: QPointF, b: QPointF):
        painter.drawLine(a, b)
        d = QLineF(a, b)
        if d.length() < 1e-6:
            return
        ux, uy = d.dx() / d.length(), d.dy() / d.length()
        nx, ny = -uy, ux
        hl, hw = 7.0, 2.6                 # arrowhead length / half-width
        for tip, s in ((a, 1.0), (b, -1.0)):
            bx, by = tip.x() + ux * hl * s, tip.y() + uy * hl * s
            painter.drawPolygon(QPolygonF([
                tip,
                QPointF(bx + nx * hw, by + ny * hw),
                QPointF(bx - nx * hw, by - ny * hw)]))

    # -- interaction -------------------------------------------------------------
    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def _rename(self):
        name, ok = QInputDialog.getText(self._view(), "Room name", "Name:",
                                        text=self.name)
        if ok and name.strip():
            self.prepareGeometryChange()
            self.name = unique_room_name(self.scene(), name.strip(),
                                         exclude=self)
            self.update()

    def _privatize_shared_walls(self):
        """Before a move, swap every wall shared with another room for a private
        copy of just this room's edge (carrying in-span openings), so moving the
        room never drags the neighbour.  Dropped walls re-coalesce on release."""
        sc = self.scene()
        if sc is None:
            return
        for w in list(self.walls):
            if w.is_open or len(w.rooms) <= 1:
                continue
            span = self._perimeter_span(w)
            if span is None:
                continue
            s0, s1 = span
            c = WallItem(w.point_at(s0), w.point_at(s1), w.wall_type)
            sc.addItem(c)
            for op in w.openings:             # carry this edge's doors/windows
                if s0 - 1e-6 <= op.s <= s1 + 1e-6:
                    try:
                        nop = OpeningItem(c, op.kind, op.code, op.s - s0)
                    except ValueError:
                        continue
                    nop.door_type, nop.swing = op.door_type, op.swing
                    c.openings.append(nop)
            self.unbind_wall(w)               # this room drops the shared wall
            self.bind_wall(c)                 # and takes its private copy
            c.rebuild()

    def _translate(self, dx: float, dy: float):
        """Rigidly shift the room's owned walls, openings and region."""
        if not dx and not dy:
            return
        self.prepareGeometryChange()
        for w in self.walls:
            w.p1 = QPointF(w.p1.x() + dx, w.p1.y() + dy)
            w.p2 = QPointF(w.p2.x() + dx, w.p2.y() + dy)
            w.rebuild()                       # repositions its openings too
        self.path = QTransform.fromTranslate(dx, dy).map(self.path)
        if self.corners:
            self.corners = [QPointF(c.x() + dx, c.y() + dy)
                            for c in self.corners]
        self.anchor = QPointF(self.anchor.x() + dx, self.anchor.y() + dy)
        self._sync_corner_props()
        self.update()

    def mousePressEvent(self, e):
        # left-drag on the name moves the WHOLE room (walls, doors/windows and
        # region) when the room owns walls; Ctrl-drag keeps the legacy
        # label-only nudge (and unbound rooms always nudge the label).
        if (e.button() == Qt.MouseButton.LeftButton
                and self._label_rect().contains(e.pos())):
            self.setSelected(True)
            self.raise_to_front()
            ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
            self._dragging_label = True
            if self.walls and not ctrl:
                self._moving_room = True
                self._privatize_shared_walls()   # don't drag neighbours' walls
                self._room_grab = QPointF(e.scenePos())
            else:
                self._moving_room = False
                c = self._label_centre()
                self._label_grab = QPointF(e.scenePos().x() - c.x(),
                                           e.scenePos().y() - c.y())
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging_label and self._moving_room:
            sp = e.scenePos()
            dx = wall_snap_len(sp.x() - self._room_grab.x())
            dy = wall_snap_len(sp.y() - self._room_grab.y())
            if dx or dy:
                self._translate(dx, dy)
                self._room_grab = QPointF(self._room_grab.x() + dx,
                                          self._room_grab.y() + dy)
            e.accept()
            return
        if self._dragging_label:
            self.prepareGeometryChange()
            nx = e.scenePos().x() - self._label_grab.x()
            ny = e.scenePos().y() - self._label_grab.y()
            self.label_offset = QPointF(nx - self.anchor.x(),
                                        ny - self.anchor.y())
            self.update()
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging_label:
            moved, self._dragging_label, self._moving_room = (
                self._moving_room, False, False)
            if moved:
                sc = self.scene()
                if sc is not None:
                    coalesce_all(sc)          # dropped adjacent -> re-merge
                    rebuild_all_walls(sc)     # re-detect region + re-bind walls
                self.raise_to_front()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        self._rename()
        e.accept()

    def contextMenuEvent(self, e):
        from floorplanner.dialogs import (  # late: dialogs imports rooms at top
            RoomInventoryDialog, RoomPropertiesDialog)  # noqa: F401
        menu = QMenu()
        a_dims = menu.addAction("Show dimensions")
        a_dims.setCheckable(True)
        a_dims.setChecked(self.show_dims)
        a_props = menu.addAction("Properties…")
        a_inv = menu.addAction("Inventory…")
        a_ren = menu.addAction("Rename…")
        a_copy = menu.addAction("Copy room")
        menu.addSeparator()
        a_del = menu.addAction("Delete room")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen is a_dims:
            self.show_dims = not self.show_dims
            self.update()
        elif chosen is a_copy:
            v = self._view()
            if v is not None:
                v.win.room_clipboard = self._copy_spec()
                v.win.status(f"Copied room '{self.name}' — with the Room "
                             "Name tool active, right-click a blank spot "
                             "to paste.")
        elif chosen is a_props:
            dlg = RoomPropertiesDialog(self, self._view())
            if dlg.exec() == QDialog.DialogCode.Accepted:
                dlg.apply()
                self.prepareGeometryChange()
                self.update()
                v = self._view()
                if v is not None:
                    v.win._update_totals()    # include / name may have changed
        elif chosen is a_inv:
            RoomInventoryDialog(self, self._view()).exec()
        elif chosen is a_ren:
            self._rename()
        elif chosen is a_del and self.scene() is not None:
            self.clear_walls()           # release walls (they stay on canvas)
            self.scene().removeItem(self)
        e.accept()


def _wall_endpoints_match(w, a: QPointF, b: QPointF, tol: float = 1.0) -> bool:
    return ((QLineF(w.p1, a).length() <= tol and QLineF(w.p2, b).length() <= tol)
            or (QLineF(w.p1, b).length() <= tol
                and QLineF(w.p2, a).length() <= tol))


def _wall_spans_segment(w, a: QPointF, b: QPointF) -> bool:
    """True when wall `w`'s body runs along and contains the segment a->b
    (both ends project within the wall's length, ~collinear with it)."""
    u, length = w.unit(), w.length()
    if length < 1e-6:
        return False
    for p in (a, b):
        vx, vy = p.x() - w.p1.x(), p.y() - w.p1.y()
        s = vx * u.x() + vy * u.y()
        if not (-0.6 <= s <= length + 0.6
                and abs(vy * u.x() - vx * u.y()) <= 1.5):
            return False
    return True


def _wall_along_segment(scene, a: QPointF, b: QPointF):
    """The wall whose body runs along (and spans) the segment a->b -- i.e.
    the longer wall that carries a room edge.  None if there isn't one.  When
    several walls span it, the geometrically smallest is chosen so the pick is
    deterministic (scene.items() order is not) and save/load round-trips."""
    cands = [w for w in scene.items()
             if isinstance(w, WallItem) and not w.is_open
             and _wall_spans_segment(w, a, b)]
    if not cands:
        return None
    return min(cands, key=lambda w: (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()))


def walls_cover_room(walls, room) -> bool:
    """True when `walls` form a complete loop along every edge of the
    room's perimeter -- so moving exactly those walls moves the whole
    room, even if extra (coincident) walls also touch the boundary."""
    if not room.corners:
        return False
    n = len(room.corners)
    for i in range(n):
        a, b = room.corners[i], room.corners[(i + 1) % n]
        if not any(_wall_spans_segment(w, a, b) for w in walls):
            return False
    return True


def duplicate_wall(scene, w):
    """A standalone copy of wall `w` (same type + openings), added to the scene
    and bound to no room.  Used when grouping a room duplicates its walls."""
    nw = WallItem(QPointF(w.p1), QPointF(w.p2), w.wall_type)
    scene.addItem(nw)
    for op in w.openings:
        try:
            nop = OpeningItem(nw, op.kind, op.code, op.s)
        except ValueError:
            continue
        nop.door_type, nop.swing = op.door_type, op.swing
        nw.openings.append(nop)
    nw.rebuild()
    return nw


def synthesize_room_edge(scene, a: QPointF, b: QPointF):
    """Create a new wall along a->b for a room's own copy of a shared/party
    wall.  It takes the carrier's type but NOT its openings -- a door/window
    belongs to one wall only; this plain copy opens its body for it instead
    (so there are never two doors or windows on top of each other)."""
    src = _wall_along_segment(scene, a, b)
    nw = WallItem(QPointF(a), QPointF(b),
                  src.wall_type if src is not None else "interior")
    scene.addItem(nw)
    nw.rebuild()
    return nw


def bind_room_walls(scene, room, settle=True):
    """Bind `room`'s edge loop, backing every perimeter edge with exactly one
    item, in priority order:

      1. a real ownable wall whose endpoints match the edge (bound directly);
      2. else, if a neighbour-owned exact wall or a longer/party wall spans
         the edge, a room-owned copy is synthesized (keeps adjacent rooms
         decoupled);
      3. else an OpenWall -- a dashed gap that keeps the loop closed but is
         not a built wall.

    Corner geometry (including the extra corners created when a wall's end is
    pulled away, opening a side) comes from reloop_open_room via refresh; this
    just attaches a wall/open-wall to each edge.  Idempotent: a previously
    synthesized copy or OpenWall is reused, so the count does not grow; open
    walls that closed up are removed.  Pass settle=False from refresh_rooms."""
    if not room.corners:
        return
    old_open = [w for w in room.walls if w.is_open]
    room.clear_walls()
    corners = room.corners
    n = len(corners)
    # sort candidates by geometry so the per-edge pick is deterministic
    # (scene.items() order is not), which keeps save/load + undo round-trips
    # byte-stable
    band_walls = sorted(room.bounding_walls(),
                        key=lambda w: (w.p1.x(), w.p1.y(),
                                       w.p2.x(), w.p2.y(), w.wall_type))
    reused_open = set()
    for i in range(n):
        a, b = corners[i], corners[(i + 1) % n]
        if QLineF(a, b).length() < MIN_WALL_LEN:
            continue
        match = next((w for w in band_walls
                      if not w.is_open and w.group() is None
                      and _wall_endpoints_match(w, a, b)), None)
        if match is not None:                            # 1. share this wall
            room.bind_wall(match)
            continue
        span = _wall_along_segment(scene, a, b)           # 2. share party wall
        if span is not None and span.group() is None:
            # a longer/neighbour-owned wall runs along this edge -- SHARE it
            # (the shared-wall model: one wall borders several rooms) rather
            # than synthesizing a private duplicate.
            room.bind_wall(span)
            continue
        ow = next((w for w in old_open if w not in reused_open    # 3. open edge
                   and _wall_endpoints_match(w, a, b)), None)
        if ow is None:
            ow = OpenWall(QPointF(a), QPointF(b), room)
            scene.addItem(ow)
        else:
            reused_open.add(ow)
        room.bind_wall(ow)
    for w in old_open:                       # drop open edges that closed up
        if w not in reused_open and not w.rooms and w.scene() is not None:
            scene.removeItem(w)
    if settle:
        rebuild_all_walls(scene)


def reloop_open_room(room):
    """Rebuild an OPEN room's corner loop from its bound real walls when
    flood-fill can't enclose it.  Each real wall is matched (using the last
    known corners for order) to a perimeter edge; the loop is then the walls'
    current endpoints in order, with extra corners + dashed open segments
    inserted wherever consecutive walls no longer meet.  Returns
    (path, area, corners) or None."""
    prev = room.corners
    # include open walls: a body-slid side carries its dashed gap, so the open
    # edge must follow the open wall's CURRENT position, not the stale corners
    walls = [w for w in room.walls if w.length() > 1e-6]
    if not prev or not walls:
        return None
    n = len(prev)
    used, segs = set(), []
    for i in range(n):
        a, b = prev[i], prev[(i + 1) % n]
        best, best_d, orient = None, 1e18, None
        for w in walls:
            if id(w) in used:
                continue
            d1 = QLineF(w.p1, a).length() + QLineF(w.p2, b).length()
            d2 = QLineF(w.p2, a).length() + QLineF(w.p1, b).length()
            d, o = (d1, (w.p1, w.p2)) if d1 <= d2 else (d2, (w.p2, w.p1))
            if d < best_d:
                best_d, best, orient = d, w, o
        if best is not None and best_d <= QLineF(a, b).length() + 2 * JOIN_TOL:
            used.add(id(best))
            segs.append((QPointF(orient[0]), QPointF(orient[1])))   # wall ends
        else:
            segs.append(None)                                       # open edge
    pts = []
    for i in range(n):
        a, b = prev[i], prev[(i + 1) % n]
        s, e = segs[i] if segs[i] is not None else (a, b)
        if not pts or QLineF(pts[-1], s).length() > 0.6:
            pts.append(s)
        if QLineF(s, e).length() > 0.6:
            pts.append(e)
    if len(pts) > 1 and QLineF(pts[0], pts[-1]).length() <= 0.6:
        pts.pop()
    # keep collinear gap corners (a shortened wall leaves a collinear open
    # segment); only exact near-duplicates were already dropped above
    if len(pts) < 3:
        return None
    return (room_path_from_corners(pts), poly_area_sqft(pts), pts)


def detach_wall_from_room(scene, wall):
    """Unlock `wall`'s corners so the user can drag its endpoints.  The wall
    stays part of the room; pulling a corner away from the neighbouring wall
    opens that side (a dashed OpenWall bridges the gap)."""
    if not wall.rooms:
        return
    wall._corners_unlocked = True
    wall.setZValue(wall.zValue() + 1)    # above locked neighbours at corners
    wall.update()


def room_path_from_corners(corners) -> QPainterPath:
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(c) for c in corners]))
    path.closeSubpath()
    return path


def path_area_sqft(path: QPainterPath) -> float:
    poly = path.toFillPolygon()
    pts = [poly[i] for i in range(poly.count())]
    return poly_area_sqft(pts) if len(pts) >= 3 else 0.0


def simplify_corners(poly) -> list:
    """Clean corner list from a boolean-result polygon: drop the closing
    duplicate, merge near-duplicates, and drop collinear points."""
    pts = [QPointF(poly[i]) for i in range(poly.count())]
    if len(pts) > 1 and QLineF(pts[0], pts[-1]).length() < 0.5:
        pts.pop()
    dedup = []
    for p in pts:
        if not dedup or QLineF(dedup[-1], p).length() > 0.5:
            dedup.append(p)
    n = len(dedup)
    if n < 3:
        return dedup
    corners = []
    for i in range(n):
        a, b, c = dedup[(i - 1) % n], dedup[i], dedup[(i + 1) % n]
        cross = ((b.x() - a.x()) * (c.y() - b.y())
                 - (b.y() - a.y()) * (c.x() - b.x()))
        if abs(cross) > 1.0:           # a real corner, not collinear filler
            corners.append(b)
    return corners if len(corners) >= 3 else dedup


def interior_point(poly) -> QPointF:
    """A point strictly inside a (possibly concave) polygon."""
    rule = Qt.FillRule.OddEvenFill
    c = poly.boundingRect().center()
    if poly.containsPoint(c, rule):
        return c
    br = poly.boundingRect()
    for iy in range(1, 12):
        for ix in range(1, 12):
            p = QPointF(br.left() + br.width() * ix / 12.0,
                        br.top() + br.height() * iy / 12.0)
            if poly.containsPoint(p, rule):
                return p
    return c


def room_walled(scene, room) -> bool:
    """True while the room's region is still enclosed by walls -- a flood
    fill from inside it doesn't escape to the canvas edge."""
    pts = []
    if room.corners:
        pts.append(interior_point(QPolygonF(room.corners)))
    pts.append(room.anchor)
    return any(detect_room(scene, p) is not None for p in pts)
