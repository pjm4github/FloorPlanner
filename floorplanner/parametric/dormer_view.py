"""The dormer preview for the properties dialog (PyQt6): the GABLE END in the
CENTRE with a SIDE elevation beside it -- the dormer's box unfolded about the
gable -- all drawn TO SCALE at ONE shared scale, so the level's floor and the
orange ceiling line run straight across the panels, and the row JUSTIFIED to the
TOP of the canvas (Patrick, 0360).

The gable end shows the roof line, the floor, the ceiling line, the wall the
user drew under the face (when there is one) and its windows and doors at their
sill and head. Each SIDE is a TRUE left projection: the cheek wall solid, the
host roof's line DASHED and labelled "host roof" -- the plane the dormer sits on
-- and the dormer's OWN roof as a HIDDEN dashed line (ridge at the top, front
rake hanging over the face by the overhang, back dying into the host roof). The
right side is drawn only when the
dormer is NOT symmetric; a symmetric dormer's right side is the left's mirror, so
it is dropped (Patrick, 0360). LOOK-ONLY (Patrick, 0356):
openings are edited on the wall in the plan. An opening ABOVE the ceiling line is
legitimate (the gable rises above it) and is drawn like any other; one the roof
line cuts is red. Every number is `dormer_geometry`'s (`face_profile`,
`face_openings`, `side_profile`, `side_openings`), computed by `DormerKind`.
"""

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget

_INK = QColor(31, 41, 55)
_DIM = QColor(71, 85, 105)
_REF = QColor(150, 160, 175)           # the dashed dormer-roof reference
_WALL = QColor(241, 245, 249)
_ROOFBAND = QColor(224, 226, 230)      # a shed's roof seen end-on, filled
_GLASS = QColor(205, 225, 245)
_DOOR = QColor(226, 214, 196)
_BAD = QColor(185, 28, 28)
_CEILING = QColor(234, 120, 20)        # the knee-line orange


def _fmt(x, places=1):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def _extent(points):
    xs = [x for x, _z in points]
    return (min(xs), max(xs)) if xs else (0.0, 1.0)


class DormerFaceView(QWidget):
    """Three elevations in a row: the gable end centred, a side on each flank."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._derived = None
        self.setMinimumSize(560, 360)
        self.setAccessibleName("Dormer gable end and side elevations")

    def sizeHint(self):
        return QSize(740, 420)

    def set_data(self, values, derived, context=None):
        del values, context
        self._derived = derived
        self.update()

    # -- what to draw --------------------------------------------------------
    def panels(self):
        """[(title, panel)] in ROW order (left | gable | [right]). A panel:
        `wall` and `roof` point lists `(across, z)`, `host` (the host roof's
        line, dashed and labelled -- a side only, else None), `openings`,
        `has_wall`, `flip` (draw across right-to-left), `face_mark` (a side,
        whose face/gable end -- toward the centre -- is labelled).

        The right side is dropped when the dormer is symmetric (its right is
        the left mirrored), so a symmetric dormer reads as [left | gable]."""
        d = self._derived
        if not d or not d.get("face_profile"):
            return []
        prof = d["face_profile"]
        state = d.get("state") or {}
        shed = state.get("form") == "shed"
        gable = ("Front" if shed else "Gable end", {
            "wall": prof["wall"], "roof": prof["roof"], "host": None,
            "openings": d.get("face_openings") or [],
            "has_wall": bool(d.get("face_wall")), "flip": False,
            "face_mark": False, "roof_fill": shed,   # the shed's roof band, filled
            "label": f"ridge {_fmt(prof['peak'][1])} in"})
        # ONE side beside the face: a symmetric gable's right is the left
        # mirrored, and a symmetric SHED's two sides read the same trapezoid,
        # so both drop to [left | front]; a free (asymmetric) dormer shows both.
        symmetric = bool(state.get("symmetric", True))
        want = ("left",) if symmetric else ("left", "right")
        sides = {}
        for side in want:
            info = (d.get("sides") or {}).get(side)
            if not info:
                continue
            sp = info["profile"]
            sides[side] = (f"{side.capitalize()} side", {
                "wall": sp["wall"], "roof": sp["roof"], "host": sp["host"],
                "ridge": sp.get("ridge"),
                "openings": info["openings"], "has_wall": bool(info["wall"]),
                # the box unfolded about the gable: each cheek's face/gable end
                # sits toward the CENTRE -- left cheek's face on its right (so
                # flip), right cheek's on its left. Still each an exterior view.
                "flip": side == "left", "face_mark": True,
                "label": f"top {_fmt(sp['top'])} in"})
        return ([sides["left"]] if "left" in sides else []) + [gable] \
            + ([sides["right"]] if "right" in sides else [])

    # -- drawing -------------------------------------------------------------
    def _text(self, p, size, bold=False):
        f = QFont(p.font())
        f.setPointSizeF(size)
        f.setBold(bold)
        p.setFont(f)

    def _panel_x_extent(self, pn):
        pts = list(pn["wall"]) + list(pn["roof"])
        if pn.get("ridge"):                    # the ridge runs back past the wall
            pts += list(pn["ridge"])
        pts += [(o[k], 0.0) for o in pn["openings"] for k in ("x0", "x1")]
        return _extent(pts)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        row = self.panels()
        if not row:
            p.setPen(QPen(_DIM))
            self._text(p, 10)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No dormer to draw with these values")
            p.end()
            return
        ceiling = self._derived.get("ceiling_in")

        def panel_zs(pn):
            zs = [z for _x, z in list(pn["wall"]) + list(pn["roof"])]
            if pn.get("host"):                 # the host line is the reference
                zs += [z for _x, z in pn["host"]]
            if pn.get("ridge"):                # the dormer roof rises to the ridge
                zs += [z for _x, z in pn["ridge"]]
            zs += [o["head_in"] for o in pn["openings"]]
            return zs
        z_hi = max([z for _t, pn in row for z in panel_zs(pn)] + [1.0])

        W, H = float(self.width()), float(self.height())
        m_t, m_b = 30.0, 26.0                  # title / foot labels
        m_x = 10.0                             # a panel's side margin
        H_use = max(H - m_t - m_b, 10.0)

        n = len(row)
        if n == 3:
            fracs = [0.29, 0.42, 0.29]
        elif n == 2:
            fracs = [0.5, 0.5]
        else:
            fracs = [1.0]
        lefts, widths, acc = [], [], 0.0
        for fr in fracs:
            lefts.append(acc * W)
            widths.append(fr * W)
            acc += fr

        # ONE shared scale: fit the tallest panel vertically AND the widest
        # panel horizontally, so every panel is to-scale and comparable.
        exts = [self._panel_x_extent(pn) for _t, pn in row]
        k = H_use / z_hi
        for (lo, hi), cw in zip([e for e in exts], widths, strict=False):
            usable = max(cw - 2 * m_x, 10.0)
            if hi - lo > 1e-6:
                k = min(k, usable / (hi - lo))

        # JUSTIFY TO THE TOP: the drawing is k * z_hi tall; drop ONE floor
        # baseline that far below the top margin (never past the foot margin),
        # so a width-limited row rides the top of the canvas, not its middle.
        oz = m_t + min(z_hi * k, H_use)

        for i, (title, pn) in enumerate(row):
            cell = QRectF(lefts[i], 0.0, widths[i], H)
            p.save()
            p.setClipRect(cell)                # a panel stays in its own cell
            self._panel(p, cell, title, pn, ceiling, k, oz, m_x, exts[i])
            p.restore()
        p.end()

    def _panel(self, p, cell, title, pn, ceiling, k, oz, m_x, ext):
        x_lo, x_hi = ext
        usable = max(cell.width() - 2 * m_x, 10.0)
        pad = (usable - (x_hi - x_lo) * k) / 2.0
        x0 = cell.left() + m_x + pad
        flip = pn["flip"]

        def q(x, z, lo=x_lo, hi=x_hi):
            along = (hi - x) if flip else (x - lo)
            return QPointF(x0 + along * k, oz - z * k)

        # the wall
        if pn["has_wall"]:
            p.setPen(QPen(_INK, 1.2))
            p.setBrush(QBrush(_WALL))
        else:
            p.setPen(QPen(_DIM, 1.0, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolygon(QPolygonF([q(x, z) for x, z in pn["wall"]]))

        # the floor and the ceiling line (shared scale -> straight across)
        p.setPen(QPen(_INK, 1.6))
        p.drawLine(QPointF(cell.left() + m_x, oz),
                   QPointF(cell.right() - m_x, oz))
        self._text(p, 8)
        if ceiling is not None and ceiling * k < oz - cell.top():
            cy = oz - ceiling * k
            p.setPen(QPen(_CEILING, 1.2, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(cell.left() + m_x, cy),
                       QPointF(cell.right() - m_x, cy))
            if title == "Gable end":
                p.drawText(QRectF(cell.left() + m_x, cy - 15,
                                  cell.width() - 2 * m_x, 13),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                           f"ceiling {_fmt(ceiling)}")

        # the host roof's line -- the plane the dormer sits on -- dashed and
        # labelled, the reference the short cheek reads against (Patrick, 0360)
        if pn["host"]:
            a, b = q(*pn["host"][0]), q(*pn["host"][1])
            p.setPen(QPen(_REF, 1.4, Qt.PenStyle.DashLine))
            p.drawLine(a, b)
            mid = QPointF((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0)
            p.setPen(QPen(_DIM))
            self._text(p, 7)
            p.drawText(QRectF(mid.x() - 44, mid.y() - 15, 88, 12),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                       "host roof")

        # the dormer's OWN roof in this projection -- a HIDDEN line (dashed):
        # up the front rake (over the face by the overhang), back along the
        # ridge, down the host roof. The near cheek stands in front (Patrick).
        if pn.get("ridge"):
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_REF, 1.3, Qt.PenStyle.DashLine))
            p.drawPolyline(QPolygonF([q(x, z) for x, z in pn["ridge"]]))

        for o in pn["openings"]:
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

        # the wall's own roof line (the cheek eave / the gable rake), solid.
        # A shed's FRONT draws its roof as a FILLED BAND (the single plane seen
        # end-on, from the eaves up to the back ridge) behind the outline.
        if pn.get("roof_fill"):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_ROOFBAND))
            p.drawPolygon(QPolygonF([q(x, z) for x, z in pn["roof"]]))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_INK, 2.4))
        p.drawPolyline(QPolygonF([q(x, z) for x, z in pn["roof"]]))

        # the title
        p.setPen(QPen(_INK if pn["has_wall"] else _DIM))
        self._text(p, 8.5, bold=True)
        note = "" if pn["has_wall"] else "  (no wall)"
        p.drawText(QRectF(cell.left(), cell.top() + 4, cell.width(), 18),
                   Qt.AlignmentFlag.AlignCenter,
                   f"{title}{note}  -  {pn['label']}")

        # a side's face/gable end (toward the centre), labelled
        if pn.get("face_mark"):
            fxp = q(pn["wall"][0][0], 0.0).x()
            p.setPen(QPen(_DIM))
            self._text(p, 7.5, bold=True)
            p.drawText(QRectF(fxp - 24, oz + 3, 48, 13),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                       "face")
