"""The dormer preview for the properties dialog (PyQt6): the GABLE END in
elevation, seen from outside, drawn TO SCALE from the values in the dialog.

It shows the roof line, the level's floor and the ceiling line, the wall the
user drew under the face (when there is one), and every window and door in
that wall at its own sill and head -- and, under it, the two SIDE walls the
same way, with the host roof's line across each. LOOK-ONLY (Patrick, 0356):
openings are edited on the wall in the plan. An opening ABOVE the ceiling line is
legitimate -- the gable rises above it -- and is drawn like any other; an
opening the roof line cuts is drawn in red. Stacked openings are simply two
openings. Every number is `dormer_geometry`'s: `face_profile` and
`face_openings`, already computed by `DormerKind.evaluate`.
"""

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget

_INK = QColor(31, 41, 55)
_DIM = QColor(71, 85, 105)
_WALL = QColor(241, 245, 249)
_GLASS = QColor(205, 225, 245)
_DOOR = QColor(226, 214, 196)
_BAD = QColor(185, 28, 28)
_CEILING = QColor(234, 120, 20)       # the knee-line orange


def _fmt(x, places=1):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


class DormerFaceView(QWidget):
    """Three elevations: the gable end on top, the two sides under it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._derived = None
        self.setMinimumSize(420, 380)
        self.setAccessibleName("Dormer gable end and side elevations")

    def sizeHint(self):
        return QSize(520, 520)

    def set_data(self, values, derived, context=None):
        del values, context
        self._derived = derived
        self.update()

    # -- what to draw --------------------------------------------------------
    def panels(self):
        """[(title, panel)] -- plain data, so a test can read what would be
        painted without painting it. A panel: `wall` and `roof` point lists
        `(across, z)`, `host` (a line or None), `openings`, `has_wall`,
        `flip` (draw across-coordinates right to left), `face_mark` (a side
        panel, whose face/gable end is labelled)."""
        d = self._derived
        if not d or not d.get("face_profile"):
            return []
        prof = d["face_profile"]
        out = [("Gable end", {
            "wall": prof["wall"], "roof": prof["roof"], "host": None,
            "openings": d.get("face_openings") or [],
            "has_wall": bool(d.get("face_wall")), "flip": False,
            "face_mark": False,
            "label": f"ridge {_fmt(prof['peak'][1])} in"})]
        # left cheek on the LEFT, right cheek on the RIGHT (Patrick, 0358)
        for side in ("left", "right"):
            info = (d.get("sides") or {}).get(side)
            if not info:
                continue
            sp = info["profile"]
            out.append((f"{side.capitalize()} side", {
                "wall": sp["wall"], "roof": sp["roof"], "host": sp["host"],
                "openings": info["openings"], "has_wall": bool(info["wall"]),
                # each cheek is its OWN exterior view: the face/gable end sits
                # at the panel's OUTER edge (left cheek's face at the left,
                # right cheek's at the right), so the faces point outward and
                # the host ends meet in the middle. `face_mark` labels it.
                "flip": side == "right",
                "face_mark": True,
                "label": f"top {_fmt(sp['top'])} in"}))
        return out

    # -- drawing -------------------------------------------------------------
    def _text(self, p, size, bold=False):
        f = QFont(p.font())
        f.setPointSizeF(size)
        f.setBold(bold)
        p.setFont(f)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        panels = self.panels()
        if not panels:
            p.setPen(QPen(_DIM))
            self._text(p, 10)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No dormer to draw with these values")
            p.end()
            return
        ceiling = self._derived.get("ceiling_in")
        z_hi = max([z for _t, pn in panels for _x, z in pn["roof"] + pn["wall"]]
                   + [o["head_in"] for _t, pn in panels for o in pn["openings"]]
                   + [1.0])
        w, h = float(self.width()), float(self.height())
        sides = panels[1:]
        top_h = h * (0.58 if sides else 1.0)
        self._panel(p, QRectF(0, 0, w, top_h), *panels[0], ceiling, z_hi)
        for i, (title, pn) in enumerate(sides):
            cell = QRectF(i * w / len(sides), top_h, w / len(sides), h - top_h)
            self._panel(p, cell, title, pn, ceiling, z_hi)
        p.end()

    def _panel(self, p, cell, title, pn, ceiling, z_hi):
        ops = pn["openings"]
        xs = ([x for x, _z in pn["roof"] + pn["wall"]]
              + [o[k] for o in ops for k in ("x0", "x1")])
        x_lo, x_hi = min(xs), max(xs)
        m_l, m_r, m_t, m_b = 12.0, 58.0, 26.0, 24.0
        w = max(cell.width() - m_l - m_r, 10.0)
        h = max(cell.height() - m_t - m_b, 10.0)
        k = min(w / max(x_hi - x_lo, 1.0), h / max(z_hi, 1.0))
        pad = (w - (x_hi - x_lo) * k) / 2.0
        oz = cell.top() + m_t + h
        flip = pn["flip"]

        def q(x, z):
            along = (x_hi - x) if flip else (x - x_lo)
            return QPointF(cell.left() + m_l + pad + along * k, oz - z * k)

        right_edge = cell.left() + m_l + pad + (x_hi - x_lo) * k
        if pn["has_wall"]:
            p.setPen(QPen(_INK, 1.2))
            p.setBrush(QBrush(_WALL))
        else:
            p.setPen(QPen(_DIM, 1.0, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolygon(QPolygonF([q(x, z) for x, z in pn["wall"]]))

        p.setPen(QPen(_INK, 1.6))
        p.drawLine(q(x_lo, 0.0), q(x_hi, 0.0))
        self._text(p, 8)
        if ceiling is not None and ceiling < z_hi:
            p.setPen(QPen(_CEILING, 1.2, Qt.PenStyle.DashLine))
            p.drawLine(q(x_lo, ceiling), q(x_hi, ceiling))
            y = q(x_lo, ceiling).y()
            lx = right_edge + 4
            p.drawText(QRectF(lx, y - 8, max(cell.right() - lx - 2, 40.0), 16),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       f"ceiling {_fmt(ceiling)}")
        if pn["host"]:
            p.setPen(QPen(_DIM, 1.4, Qt.PenStyle.DashDotLine))
            p.drawLine(q(*pn["host"][0]), q(*pn["host"][1]))

        for o in ops:
            bad = o["through_roof"] or o["overlaps"] or o["off_wall"]
            p.setPen(QPen(_BAD if bad else _INK, 1.6 if bad else 1.1))
            p.setBrush(QBrush(_DOOR if o.get("kind") in ("door", "gate", "cased")
                              else _GLASS))
            box = QRectF(q(o["x0"], o["head_in"]), q(o["x1"], o["sill_in"])).normalized()
            shape = o.get("shape", "rect")
            if shape == "round":
                p.drawEllipse(box)
            elif shape == "octagon":
                cx, cy = box.width() * 0.2929, box.height() * 0.2929
                p.drawPolygon(QPolygonF([
                    QPointF(box.left() + cx, box.top()),
                    QPointF(box.right() - cx, box.top()),
                    QPointF(box.right(), box.top() + cy),
                    QPointF(box.right(), box.bottom() - cy),
                    QPointF(box.right() - cx, box.bottom()),
                    QPointF(box.left() + cx, box.bottom()),
                    QPointF(box.left(), box.bottom() - cy),
                    QPointF(box.left(), box.top() + cy)]))
            else:
                p.drawRect(box)
            if box.width() > 34 and box.height() > 22:
                p.setPen(QPen(_BAD if bad else _DIM))
                self._text(p, 7.5)
                label = str(o.get("code") or "")
                if o.get("kind") != "door":
                    label += f"\nsill {_fmt(o['sill_in'])}"
                p.drawText(box, Qt.AlignmentFlag.AlignCenter, label.strip())

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_INK, 2.4))
        p.drawPolyline(QPolygonF([q(x, z) for x, z in pn["roof"]]))

        p.setPen(QPen(_INK if pn["has_wall"] else _DIM))
        self._text(p, 8.5, bold=True)
        note = "" if pn["has_wall"] else "  (no wall drawn)"
        p.drawText(QRectF(cell.left(), cell.top() + 4, cell.width(), 18),
                   Qt.AlignmentFlag.AlignCenter,
                   f"{title}{note}  -  {pn['label']}")

        # a side view's face/gable end, labelled so its exterior orientation
        # reads without ambiguity (Patrick, 0358)
        if pn.get("face_mark"):
            fxp = q(pn["wall"][0][0], 0.0).x()     # y0 of the cheek: its face
            p.setPen(QPen(_DIM))
            self._text(p, 7.5, bold=True)
            p.drawText(QRectF(fxp - 24, oz + 3, 48, 13),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                       "face")
