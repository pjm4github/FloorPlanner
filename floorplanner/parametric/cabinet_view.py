"""The cabinet preview for the properties dialog (PyQt6): a FRONT ELEVATION
and a plan inset, painted from the same parts the 3D viewer builds, in the
materials the cabinet's parameters and its room's style resolve to.

Nothing here is a picture of a cabinet: each rectangle is one part the
calculator returned -- a door, a rail, a pull -- so what the dialog shows is
what the 3D view and, later, the camera elevation will show.
"""
from PyQt6.QtCore import QPointF, QSize
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from floorplanner.parametric import cabinet_geometry as cg

_INK = QColor(31, 41, 55)
_DIM = QColor(71, 85, 105)
# materials the calculator names but does not define (they are the catalog's)
_OTHER = {"metal": (0.66, 0.68, 0.71), "porcelain": (0.93, 0.94, 0.95),
          "auto_trim": (0.11, 0.11, 0.12), "unknown": (0.85, 0.35, 0.55)}


def material_colour(name):
    """A QColor for a material name, including a "sheen#rrggbb" custom one."""
    name = str(name)
    if "#" in name:
        return QColor("#" + name.partition("#")[2])
    spec = cg.MATERIALS.get(name)
    rgb = spec["colour"][:3] if spec else _OTHER.get(name, _OTHER["unknown"])
    return QColor.fromRgbF(float(rgb[0]), float(rgb[1]), float(rgb[2]))


def _fmt(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def _font(painter, size, bold=False):
    f = QFont(painter.font())
    f.setPointSizeF(size)
    f.setBold(bold)
    painter.setFont(f)


class _PartsView(QWidget):
    """Parts projected onto one plane, painted back to front."""

    title = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._derived = None
        self.setMinimumSize(380, 200)

    def set_data(self, values, derived, context=None):
        self._derived = derived
        self.update()

    def _rows(self, derived):
        """[(depth key, [(u, v)] polygon, material)] in drawing units, v UP."""
        raise NotImplementedError

    def _caption(self, derived):
        return ""

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        p.setPen(QPen(_INK))
        _font(p, 8.5, bold=True)
        p.drawText(QPointF(8, 16), self.title)
        d = self._derived
        if not d or not d.get("parts"):
            p.end()
            return
        _font(p, 8)
        p.setPen(QPen(_DIM))
        p.drawText(QPointF(130, 16), self._caption(d))
        rows = sorted(self._rows(d), key=lambda r: r[0])
        us = [u for _k, poly, _m in rows for u, _v in poly]
        vs = [v for _k, poly, _m in rows for _u, v in poly]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        top, margin = 26.0, 14.0
        k = min((self.width() - 2 * margin) / max(u1 - u0, 1.0),
                (self.height() - top - margin) / max(v1 - v0, 1.0))
        if k <= 0:
            p.end()
            return
        ox = (self.width() - (u1 - u0) * k) / 2.0
        oy = top + (self.height() - top - margin + (v1 - v0) * k) / 2.0
        for _key, poly, material in rows:
            p.setPen(QPen(_INK, 0.6))
            p.setBrush(QBrush(material_colour(material)))
            p.drawPolygon(QPolygonF([QPointF(ox + (u - u0) * k, oy - (v - v0) * k)
                                     for u, v in poly]))
        p.end()


class CabinetFrontView(_PartsView):
    title = "Front elevation"

    def sizeHint(self):
        return QSize(460, 340)

    def _caption(self, d):
        w, _depth = d["footprint"]
        return (f"{_fmt(w)} in wide · {_fmt(d['height'])} in to the top"
                + (f" · {d['code']}" if d.get("code") else ""))

    def _rows(self, d):
        rows = []
        for part in d["parts"]:
            xs = [x for x, _f in part.quad]
            front = max(f for _x, f in part.quad)
            rows.append((front, [(min(xs), part.z0), (max(xs), part.z0),
                                 (max(xs), part.z1), (min(xs), part.z1)],
                         d["materials"].get(part.role, "unknown")))
        return rows


class CabinetPlanView(_PartsView):
    title = "Plan"

    def sizeHint(self):
        return QSize(460, 180)

    def _caption(self, d):
        w, depth = d["footprint"]
        return f"{_fmt(w)} x {_fmt(depth)} in · wall at the top"

    def _rows(self, d):
        # seen from above: the highest part is painted last; the wall (f = 0)
        # is at the top of the drawing, so v = -f
        return [(part.z1, [(x, -f) for x, f in part.quad],
                 d["materials"].get(part.role, "unknown")) for part in d["parts"]]


class CabinetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.front = CabinetFrontView(self)
        self.plan = CabinetPlanView(self)
        lay.addWidget(self.front, 2)
        lay.addWidget(self.plan, 1)
        self.setAccessibleName("Cabinet preview")

    def set_data(self, values, derived, context=None):
        self.front.set_data(values, derived, context)
        self.plan.set_data(values, derived, context)
