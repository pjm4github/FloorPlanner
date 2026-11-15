"""The stair preview for the properties dialog (PyQt6): a side elevation
drawn TO SCALE from the current `StairGeometry`, and a plan inset under it.

Nothing here is a stretched picture. Every riser and tread on screen is one
the calculation produced, so the drawing cannot show 13 risers while the
numbers beside it say 14. An L or U stair is drawn UNFOLDED along its line of
travel -- the landing laid flat between the two flights -- and says so.
"""
import math

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from floorplanner.parametric import stair_geometry as sg

_INK = QColor(31, 41, 55)
_DIM = QColor(71, 85, 105)
_STRINGER = QColor(205, 225, 245)
_FLOOR = QColor(226, 232, 240)
_HEADROOM = QColor(180, 83, 9)


def _fmt(x, places=3):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def _font(painter, size, bold=False):
    f = QFont(painter.font())
    f.setPointSizeF(size)
    f.setBold(bold)
    painter.setFont(f)


class StairElevationView(QWidget):
    """The side elevation, with its dimensions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._geom = None
        self._values = {}
        self.setMinimumSize(440, 280)
        self.setAccessibleName("Stair side elevation")

    def sizeHint(self):
        return QSize(560, 380)

    def set_data(self, values, geom, context=None):
        self._values = dict(values or {})
        self._geom = geom
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        g = self._geom
        if g is None or g.tread_count < 1:
            p.setPen(QPen(_DIM))
            _font(p, 10)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No stair to draw with these values")
            p.end()
            return

        segs = sg.developed_profile(g)
        S = max(s1 for _k, _s0, s1, _z0, _z1, _f in segs)
        H, h, d = g.total_rise, g.riser_height, g.tread_depth
        stub = 30.0                                   # upper floor shown past the top
        ml, mr, mt, mb = 78.0, 112.0, 30.0, 46.0
        s_lo, s_hi = -12.0, S + stub
        z_lo, z_hi = -4.0, H + 40.0
        k = min((self.width() - ml - mr) / (s_hi - s_lo),
                (self.height() - mt - mb) / (z_hi - z_lo))
        if k <= 0:
            p.end()
            return
        ox = ml - s_lo * k
        oy = self.height() - mb + z_lo * k

        def X(s):
            return ox + s * k

        def Y(z):
            return oy - z * k

        p.setClipRect(QRectF(0, 0, self.width(), self.height()))

        # where each flight starts along the developed line
        starts = {}
        for kind, s0, _s1, _z0, _z1, fi in segs:
            if kind == "riser" and fi not in starts:
                starts[fi] = s0

        # floors
        p.setPen(QPen(_INK, 1.0))
        p.setBrush(QBrush(_FLOOR))
        p.drawRect(QRectF(X(s_lo), Y(0.0), (S + 6.0 - s_lo) * k, 4.0 * k))
        p.drawRect(QRectF(X(S), Y(H), stub * k, 10.0 * k))

        # stringers
        p.setPen(QPen(_INK, 1.0))
        p.setBrush(QBrush(_STRINGER))
        drop = sg.STRINGER_DROP_IN
        for fi, f in enumerate(g.flights):
            if f.treads < 1:
                continue
            a = starts.get(fi, 0.0)
            zt = f.z0 + f.treads * h
            if f.z0 <= 1e-9:
                cut = min(drop * d / h, f.run)
                pts = [(a, f.z0), (a + f.run, zt),
                       (a + f.run, max(zt - drop, f.z0)), (a + cut, f.z0)]
            else:
                pts = [(a, f.z0), (a + f.run, zt), (a + f.run, zt - drop),
                       (a, f.z0 - drop)]
            p.drawPolygon(QPolygonF([QPointF(X(s), Y(z)) for s, z in pts]))

        # risers, treads, landing
        tread_t, nose = sg.TREAD_T_IN, sg.NOSING_IN
        for kind, s0, s1, z0, z1, _fi in segs:
            if kind == "riser":
                p.setPen(QPen(_INK, 1.0))
                p.drawLine(QPointF(X(s0), Y(z0)), QPointF(X(s0), Y(z1 - tread_t)))
            elif kind == "tread":
                p.setPen(QPen(_INK, 1.0))
                p.setBrush(QBrush(QColor(255, 255, 255)))
                p.drawRect(QRectF(X(s0 - nose), Y(z0), (s1 - s0 + nose) * k,
                                  tread_t * k))
            else:
                p.setPen(QPen(_INK, 1.0))
                p.setBrush(QBrush(_FLOOR))
                p.drawRect(QRectF(X(s0 - nose), Y(z0), (s1 - s0 + nose) * k,
                                  sg.LANDING_T_IN * k))
                p.setPen(QPen(_INK, 0.8, Qt.PenStyle.DashLine))
                for s in (s0 + 2.0, s1 - 2.0):
                    p.drawLine(QPointF(X(s), Y(z0 - sg.LANDING_T_IN)),
                               QPointF(X(s), Y(0.0)))

        # headroom line: the nosing line, raised by the profile's minimum
        head = sg.profile_for(self._values).min_headroom_in
        p.setPen(QPen(_HEADROOM, 1.0, Qt.PenStyle.DashLine))
        for fi, f in enumerate(g.flights):
            if f.treads < 1:
                continue
            a = starts.get(fi, 0.0)
            p.drawLine(QPointF(X(a), Y(f.z0 + h + head)),
                       QPointF(X(a + f.run), Y(f.z0 + (f.treads + 1) * h + head)))
        _font(p, 7.5)
        first = g.flights[0]
        if first.treads >= 1:
            stated = float(self._values.get("well_opening_in") or 0.0) > 0.0
            p.drawText(QPointF(X(0.0) + 4, Y(h + head) - 4),
                       f"{_fmt(head)} in min. headroom"
                       + ("" if stated else " — not checked"))

        # handrail / guard top, above the nosing line and the landing
        if any(sg.side_treatment(g, n)[1] for n in ("left", "right")):
            rail = g.rail_height
            p.setPen(QPen(_INK, 1.6))
            for fi, f in enumerate(g.flights):
                if f.treads < 1:
                    continue
                a = starts.get(fi, 0.0)
                z_a, z_b = f.z0 + h + rail, f.z0 + (f.treads + 1) * h + rail
                p.drawLine(QPointF(X(a), Y(z_a)), QPointF(X(a + f.run), Y(z_b)))
                p.drawLine(QPointF(X(a), Y(f.z0)), QPointF(X(a), Y(z_a)))
                p.drawLine(QPointF(X(a + f.run), Y(f.z0 + f.treads * h)),
                           QPointF(X(a + f.run), Y(z_b)))
            p.setPen(QPen(_HEADROOM, 1.0, Qt.PenStyle.DashLine))

        # dimensions
        p.setPen(QPen(_DIM, 1.0))
        _font(p, 8)
        xr = X(S + stub) + 14
        self._vdim(p, xr, Y(0.0), Y(H))
        p.drawText(QRectF(xr + 6, (Y(0.0) + Y(H)) / 2 - 22, mr - 22, 44),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"Total rise\n{_fmt(H)} in")
        yb = Y(0.0) + 4.0 * k + 14
        self._hdim(p, X(0.0), X(S), yb)
        run_text = (f"Total run {_fmt(g.total_run)} in" if g.landing is None
                    else f"Unfolded run {_fmt(S)} in  (flights "
                         f"{_fmt(g.total_run)} + landing {_fmt(g.stair_width)})")
        p.drawText(QRectF(X(0.0), yb + 3, max(X(S) - X(0.0), 240), 16),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, run_text)
        if g.landing_height is not None:
            xl = X(s_lo) - 12
            self._vdim(p, xl, Y(0.0), Y(g.landing_height))
            p.drawText(QRectF(2, (Y(0.0) + Y(g.landing_height)) / 2 - 22,
                              xl - 8, 44),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       f"Landing\n{_fmt(g.landing_height)} in")

        # unit rise / unit run, on a step near the middle of the longest flight
        fi = max(range(len(g.flights)), key=lambda i: g.flights[i].treads)
        f = g.flights[fi]
        kk = max(1, (f.treads + 1) // 2)
        a = starts.get(fi, 0.0)
        s_step = a + (kk - 1) * d
        z_step = f.z0 + (kk - 1) * h
        p.setPen(QPen(_DIM, 1.0))
        self._vdim(p, X(s_step) - 9, Y(z_step), Y(z_step + h))
        self._hdim(p, X(s_step), X(s_step + d), Y(z_step + h) - 9)
        _font(p, 7.5)
        p.drawText(QRectF(X(s_step) - 9 - 124, Y(z_step + h) - 2, 120, 14),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   f"Unit rise {_fmt(h)} in")
        p.drawText(QRectF(X(s_step) - 60, Y(z_step + h) - 9 - 17, 160, 14),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"Unit run {_fmt(d)} in")

        # caption
        p.setPen(QPen(_INK))
        _font(p, 8.5, bold=True)
        title = ("Side elevation" if g.landing is None
                 else "Side elevation — unfolded along the line of travel")
        p.drawText(QPointF(8, 16), title)
        _font(p, 8)
        p.setPen(QPen(_DIM))
        p.drawText(QPointF(8, 30),
                   f"{g.riser_count} risers · {g.tread_count} treads · "
                   f"{g.pitch_degrees:.1f}°")
        p.end()

    @staticmethod
    def _vdim(p, x, y0, y1):
        p.drawLine(QPointF(x, y0), QPointF(x, y1))
        for y in (y0, y1):
            p.drawLine(QPointF(x - 4, y + 3), QPointF(x + 4, y - 3))

    @staticmethod
    def _hdim(p, x0, x1, y):
        p.drawLine(QPointF(x0, y), QPointF(x1, y))
        for x in (x0, x1):
            p.drawLine(QPointF(x - 3, y + 4), QPointF(x + 3, y - 4))


class StairPlanView(QWidget):
    """The plan footprint, as the furnishing will draw it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._geom = None
        self._values = {}
        self.setMinimumSize(440, 130)
        self.setAccessibleName("Stair plan footprint")

    def sizeHint(self):
        return QSize(560, 170)

    def set_data(self, values, geom, context=None):
        self._values = dict(values or {})
        self._geom = geom
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        g = self._geom
        p.setPen(QPen(_INK))
        _font(p, 8.5, bold=True)
        p.drawText(QPointF(8, 16), "Plan footprint")
        if g is None or g.tread_count < 1:
            p.end()
            return
        _font(p, 8)
        p.setPen(QPen(_DIM))
        p.drawText(QPointF(120, 16),
                   f"{_fmt(g.footprint_length)} x {_fmt(g.footprint_width)} in")
        x0, y0, x1, y1 = g.bbox
        # drawn lying down: the first flight runs left to right
        top, margin = 24.0, 10.0
        k = min((self.width() - 2 * margin) / max(y1 - y0, 1.0),
                (self.height() - top - margin) / max(x1 - x0, 1.0))
        if k <= 0:
            p.end()
            return

        def P(x, y):
            # a quarter TURN, not a transpose: a transpose would mirror the
            # plan and show a left-turning stair turning right
            return QPointF(margin + (y - y0) * k, top + (x1 - x) * k)

        plan = sg.plan(g)
        p.setPen(QPen(_INK, 1.2))
        p.setBrush(QBrush(QColor(248, 250, 252)))
        for rx, ry, rw, rh in plan["rects"]:
            a, b = P(rx, ry), P(rx + rw, ry + rh)
            p.drawRect(QRectF(a, b).normalized())
        p.setPen(QPen(_INK, 0.7))
        for ax, ay, bx, by in plan["steps"]:
            p.drawLine(P(ax, ay), P(bx, by))
        line = [P(x, y) for x, y in plan["line"]]
        if self._values.get("direction") == "down":
            line.reverse()
        p.setPen(QPen(_INK, 1.4))
        for a, b in zip(line[:-1], line[1:], strict=False):
            p.drawLine(a, b)
        if len(line) >= 2:
            head, prev = line[-1], line[-2]
            ang = math.atan2(head.y() - prev.y(), head.x() - prev.x())
            for da in (math.radians(150), math.radians(-150)):
                p.drawLine(head, QPointF(head.x() + 7 * math.cos(ang + da),
                                         head.y() + 7 * math.sin(ang + da)))
        p.end()


class StairPreview(QWidget):
    """Elevation above, plan below -- what the dialog shows on its left."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.elevation = StairElevationView(self)
        self.plan = StairPlanView(self)
        lay.addWidget(self.elevation, 3)
        lay.addWidget(self.plan, 1)

    def set_data(self, values, geom, context=None):
        self.elevation.set_data(values, geom, context)
        self.plan.set_data(values, geom, context)
