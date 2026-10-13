"""Annotations on the plan (0263-report.md, Patrick's four features):

* `TextAnnotationItem` -- a text placed on the plan (the Annotation tool;
  double-click to edit; drag to move).
* `DimensionItem` -- a measurement between two snapped points: ONE thin
  solid line parallel to what it measures, a "/" slash at each callout
  point, thin extension lines from the measured points, the length written
  above the line in feet-and-inches or inches (the plan's own choice,
  `SETTINGS["dimension_units"]`). Drag it to change its offset from the
  measured line; it stays parallel.
* `DatumItem` -- a marked point (one per level) the Measure tool snaps to,
  so a run of dimensions can share one end.
* `LeaderItem` (0270) -- a text with an ARROW to the thing it names: the
  Leader tool presses on the point (snapped as the Measure tool snaps),
  drags to where the text goes, then asks for the text. The text sits on a
  short shoulder off the line's end, away from the arrow. Movable as a
  whole; two knobs when selected (the tip, the text); double-click edits.

Every item carries `floor`, so `apply_floor_visibility` ghosts and hides
it with the level, and `kind`/`to_record`/`from_record` so the bridge
round-trips it as the document's `annotations` block (schema `$defs/
annotation`). The three Show-menu switches (`show_annotations`,
`show_dimensions`, `show_callouts`) are plan settings: `sync_annotation_
visibility` applies the first two to the items, the third is read by the
walls' and openings' own paint. Callouts (0264, 0265 -- his word) are the ITEMS' SESSION LABELS -- `W7`,
`V12`, `O3`, `R2`, `F4`, `RF1` (labels.py; adopted from the file's own
ids when a plan opens, so the two match) -- plus a name where one is set;
`callout_text(item)` writes them, with the file's id beside a label only
while the Malformed-design report is open and the two differ; drawn in
`callout_colour()`, a plan setting too (default blue), on every item of
the active floor, on when a plan is opened.
"""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainterPath, QPainterPathStroker, QPen
from PyQt6.QtWidgets import QGraphicsItem, QInputDialog

from floorplanner.config import (
    FLOOR_GHOST, SETTINGS, WALL_Z, active_floor, floor_display_mode,
)
from floorplanner.geometry import fmt_ftin, wall_snap, wall_snap_len

__all__ = [
    "TextAnnotationItem", "DimensionItem", "DimensionKnob", "DatumItem", "ANNOTATION_Z",
    "LeaderItem", "LeaderKnob",
    "callout_colour", "callouts_shown", "document_id", "session_label", "callout_text",
    "CALLOUT_PX", "callout_font", "draw_callout",
    "set_report_open", "format_length",
    "sync_annotation_visibility",
    "annotation_items", "datum_on", "nearest_datum", "MEASURE_SNAP_IN",
]

ANNOTATION_Z = WALL_Z + 3            # above walls, openings and roof grips
INK = QColor(20, 20, 20)
SELECT_INK = QColor(0, 122, 255)
DIM_OFFSET_IN = 18.0                 # a new dimension's line sits this far off what it measures
DIM_TICK_IN = 4.0                    # the "/" slash, half-length in plan inches
DIM_EXT_GAP_IN = 2.0                 # the extension line starts this far off the measured point
DATUM_R_IN = 6.0
MEASURE_SNAP_IN = 6.0                # a measure's end catches an item within this (one grid step)


def callout_colour() -> QColor:
    """The plan's callout ink (Show > Item callouts colour): a hex string
    in the settings, blue when it is missing or malformed."""
    c = QColor(str(SETTINGS.get("callout_color", "#005AC8")))
    return c if c.isValid() else QColor(0, 90, 200)


def callouts_shown() -> bool:
    return bool(SETTINGS.get("show_callouts", True))


#: 0265: while the Malformed-design report is open, a callout whose session
#: label does not match the file's id shows both, so the report's zoom lands
#: on something the screen also says
REPORT = {"open": False}


def set_report_open(on: bool):
    REPORT["open"] = bool(on)


def session_label(item) -> str:
    """The item's session label (`W7`, `V12`, `O3`, `R2`, `F4`, `RF1` --
    labels.py), minted on first read; "" for a thing without one."""
    return str(getattr(item, "uid", "") or "")


def document_id(item) -> str:
    """The item's document id as stamped by the last walk or the load
    (`doc_id`; a wall split at junctions carries every segment's, joined
    by "/"), else ""."""
    ids = getattr(item, "doc_id", None)
    if not ids:
        return ""
    return ids if isinstance(ids, str) else "/".join(ids)


#: 0267 (his screen): ONE size for every item annotation -- this many view
#: pixels whatever the zoom, whatever the item -- and one colour
CALLOUT_PX = 9.0


def callout_font(lod: float) -> QFont:
    """The item annotations' one font: `CALLOUT_PX` view pixels, so a
    wall's, a corner's, an opening's, a room's, a furnishing's and a
    roof's all read the same size at any zoom (`lod` is the painter's
    scale, scene inches to pixels)."""
    f = QFont()
    f.setPixelSize(max(2, int(round(CALLOUT_PX / max(lod, 1e-6)))))
    return f


def draw_callout(painter, lod: float, at: QPointF, text: str, align: str = "left"):
    """Draw one item annotation at `at` (the painter's own coordinates) in
    the one font and the one colour, never clipped: `align` "left" puts
    the text's left baseline at `at`, "center" its middle, "right" its
    right end. The painter's font and pen are left set to the callout's."""
    if not text:
        return
    f = callout_font(lod)
    painter.setFont(f)
    painter.setPen(QPen(callout_colour(), 0))
    fm = QFontMetricsF(f)
    w = fm.horizontalAdvance(text)
    x = at.x()
    if align == "center":
        x -= w / 2.0
    elif align == "right":
        x -= w
    painter.drawText(QPointF(x, at.y()), text)


def callout_text(item) -> str:
    """The callout: the SESSION LABEL always (his word), the file's id in
    brackets beside it only while the report is open and the two differ,
    and the name after when set."""
    from floorplanner import labels as _labels
    label = session_label(item)
    text = label
    if REPORT["open"]:
        did = document_id(item)
        if did and not _labels.matches(label, did):
            text = f"{label} ({did})"
    name = getattr(item, "name", None)
    return f"{text}  {name}" if (name and text) else (name or text)


def format_length(inches: float) -> str:
    """The measurement as the plan writes it: feet-and-inches (`fmt_ftin`)
    or inches, by `SETTINGS["dimension_units"]` (`ftin` | `in`)."""
    if SETTINGS.get("dimension_units", "ftin") == "in":
        v = round(float(inches), 2)
        return f"{v:g}\""
    return fmt_ftin(float(inches))


def _ink(item, base):
    mode = floor_display_mode(item.floor)
    if mode != "active":
        return QColor(FLOOR_GHOST)
    return SELECT_INK if item.isSelected() else base


class _AnnotationBase(QGraphicsItem):
    kind = ""

    def __init__(self, floor=None):
        super().__init__()
        self.floor = floor if floor is not None else active_floor()
        self.setZValue(ANNOTATION_Z)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def shown(self) -> bool:
        """The Show-menu switch for this item's kind."""
        return True


class TextAnnotationItem(_AnnotationBase):
    """A text on the plan at `pos` (its anchor, the text's left baseline),
    rotated `rotation` degrees. Movable; double-click edits the text."""
    kind = "text"
    SIZE_PX = 14.0

    def __init__(self, pos: QPointF, text: str, rotation: float = 0.0, floor=None):
        super().__init__(floor)
        self.text = str(text)
        self.setPos(QPointF(pos))
        self.setRotation(float(rotation))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)

    def shown(self) -> bool:
        return bool(SETTINGS.get("show_annotations", True))

    def _font(self):
        f = QFont()
        f.setPixelSize(max(2, int(self.SIZE_PX / self._view_scale())))
        return f

    def _text_rect(self) -> QRectF:
        fm = QFontMetricsF(self._font())
        r = fm.boundingRect(self.text or " ")
        return QRectF(0.0, -r.height() * 0.8, max(r.width(), 6.0), r.height())

    def boundingRect(self) -> QRectF:
        return self._text_rect().adjusted(-4, -4, 4, 4)

    def shape(self) -> QPainterPath:
        p = QPainterPath()
        p.addRect(self._text_rect())
        return p

    def paint(self, painter, option, widget=None):
        painter.setFont(self._font())
        painter.setPen(QPen(_ink(self, INK), 0))
        painter.drawText(QPointF(0.0, 0.0), self.text)
        if self.isSelected():
            painter.setPen(QPen(SELECT_INK, 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._text_rect())

    def set_text(self, text: str):
        self.prepareGeometryChange()
        self.text = str(text)
        self.update()

    def mouseDoubleClickEvent(self, e):
        views = self.scene().views() if self.scene() else []
        parent = views[0] if views else None
        text, ok = QInputDialog.getText(parent, "Annotation", "Text:", text=self.text)
        if ok and text.strip():
            self.set_text(text.strip())
        e.accept()

    def to_record(self, rid: str, level: str) -> dict:
        rec = {"id": rid, "level": level, "kind": "text",
               "pos": [float(self.pos().x()), float(self.pos().y())], "text": self.text}
        if self.rotation():
            rec["rotation"] = float(self.rotation())
        return rec

    @classmethod
    def from_record(cls, rec: dict, floor):
        return cls(QPointF(*rec["pos"]), rec.get("text", ""), float(rec.get("rotation", 0.0)), floor)


class DimensionItem(_AnnotationBase):
    """A measurement from `a` to `b` (scene points, snapped by the tool),
    drawn `offset_in` off the measured line on its left side (negative =
    the right), parallel to it. The label is the distance |b - a|, in the
    plan's units, at `label_t` along the line. Dragging the body moves the
    line along the normal only.

    THE GADGET (0264, his spec): selected, the measure shows four red
    knobs -- 1 at `a` and 2 at `b` (the callout points: drag one and that
    point moves, snapping as the tool snaps; with Ctrl the measure ROTATES
    about the other knob, the angle snapping to the rotation step, the
    other callout kept at its length and orthogonal; with Shift free,
    no snap of either kind), 3 at the line's far end (drag it along the
    line: `b` slides along the measure's own direction, the length
    changes, nothing else), 4 on the label (drag it along the line: the
    label slides). The selection outline is the gadget itself, nothing
    boxed around it.

    Local coordinates are the scene's (the item sits at the origin, like a
    wall), so the record's points are the scene's own."""
    kind = "dimension"
    SIZE_PX = 12.0

    def __init__(self, a: QPointF, b: QPointF, offset_in: float = DIM_OFFSET_IN, floor=None,
                 label_t: float = 0.5):
        super().__init__(floor)
        self.a, self.b = QPointF(a), QPointF(b)
        self.offset_in = float(offset_in)
        self.label_t = min(0.95, max(0.05, float(label_t)))
        self._drag_from = None
        self.knobs = [DimensionKnob(self, k) for k in DimensionKnob.KINDS]

    def shown(self) -> bool:
        return bool(SETTINGS.get("show_dimensions", True))

    # -- geometry -------------------------------------------------------------
    def length(self) -> float:
        return math.hypot(self.b.x() - self.a.x(), self.b.y() - self.a.y())

    def _frame(self):
        """(ux, uy, nx, ny): along the measured line, and its left normal."""
        dx, dy = self.b.x() - self.a.x(), self.b.y() - self.a.y()
        ln = math.hypot(dx, dy) or 1.0
        ux, uy = dx / ln, dy / ln
        return ux, uy, -uy, ux

    def line_points(self):
        """The dimension line's two ends, in scene coordinates."""
        _, _, nx, ny = self._frame()
        o = self.offset_in
        return (QPointF(self.a.x() + nx * o, self.a.y() + ny * o),
                QPointF(self.b.x() + nx * o, self.b.y() + ny * o))

    def label_point(self) -> QPointF:
        p, q = self.line_points()
        t = self.label_t
        return QPointF(p.x() + (q.x() - p.x()) * t, p.y() + (q.y() - p.y()) * t)

    def label(self) -> str:
        return format_length(self.length())

    def _changed(self):
        self.prepareGeometryChange()
        for k in self.knobs:
            k.sync_position()
        self.update()

    def set_points(self, a: QPointF, b: QPointF):
        self.a, self.b = QPointF(a), QPointF(b)
        self._changed()

    def set_offset(self, offset_in: float):
        self.offset_in = float(offset_in)
        self._changed()

    def set_label_t(self, t: float):
        self.label_t = min(0.95, max(0.05, float(t)))
        self._changed()

    def _font(self):
        f = QFont()
        f.setPixelSize(max(2, int(self.SIZE_PX / self._view_scale())))
        return f

    def _label_angle(self) -> float:
        ux, uy, _, _ = self._frame()
        ang = math.degrees(math.atan2(uy, ux))
        if ang >= 90.0 or ang < -90.0:
            ang -= 180.0                  # never upside down; a vertical measure reads bottom to top
        return ang

    def _label_box(self) -> QRectF:
        """The label's rectangle in scene coordinates: the text's own box
        in the line's frame (above the line), turned with the line -- for
        the bounds and the hit test, tight around the text."""
        fm = QFontMetricsF(self._font())
        w, asc, desc = fm.horizontalAdvance(self.label()), fm.ascent(), fm.descent()
        lift = 3.0 / self._view_scale()
        c = self.label_point()
        a = math.radians(self._label_angle())
        ca, sa = math.cos(a), math.sin(a)
        xs, ys = [], []
        for lx, ly in ((-w / 2, -lift - asc), (w / 2, -lift - asc), (w / 2, -lift + desc), (-w / 2, -lift + desc)):
            xs.append(c.x() + lx * ca - ly * sa)
            ys.append(c.y() + lx * sa + ly * ca)
        pad = 2.0 / self._view_scale()
        return QRectF(min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad)

    def boundingRect(self) -> QRectF:
        p, q = self.line_points()
        xs = [self.a.x(), self.b.x(), p.x(), q.x()]
        ys = [self.a.y(), self.b.y(), p.y(), q.y()]
        rect = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        pad = DIM_TICK_IN + 2.0 / self._view_scale()
        return rect.adjusted(-pad, -pad, pad, pad) | self._label_box()

    def shape(self) -> QPainterPath:
        """The dimension LINE and the label, thickened enough to grab -- not
        a box around the whole thing, so a measurement across a room does
        not swallow the room's clicks."""
        p, q = self.line_points()
        path = QPainterPath()
        path.moveTo(p)
        path.lineTo(q)
        st = QPainterPathStroker()
        st.setWidth(max(6.0, 10.0 / self._view_scale()))
        out = st.createStroke(path)
        out.addRect(self._label_box())
        return out

    def paint(self, painter, option, widget=None):
        ink = _ink(self, INK)
        lod = self._view_scale()
        painter.setPen(QPen(ink, 0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        ux, uy, nx, ny = self._frame()
        p, q = self.line_points()
        # the extension lines, from just off each measured point past the line
        o = self.offset_in
        sgn = 1.0 if o >= 0 else -1.0
        for m in (self.a, self.b):
            s0 = QPointF(m.x() + nx * sgn * DIM_EXT_GAP_IN, m.y() + ny * sgn * DIM_EXT_GAP_IN)
            s1 = QPointF(m.x() + nx * (o + sgn * DIM_TICK_IN), m.y() + ny * (o + sgn * DIM_TICK_IN))
            painter.drawLine(s0, s1)
        # the one thin solid line
        painter.drawLine(p, q)
        # the slashes: a "/" at each callout point, 45 degrees to the line
        t = DIM_TICK_IN
        for m in (p, q):
            painter.drawLine(QPointF(m.x() + (ux - nx) * t, m.y() + (uy - ny) * t),
                             QPointF(m.x() - (ux - nx) * t, m.y() - (uy - ny) * t))
        # the label, parallel to the line, above it, at `label_t` along it
        f = self._font()
        painter.setFont(f)
        text = self.label()
        fm = QFontMetricsF(f)
        w = fm.horizontalAdvance(text)
        mid = self.label_point()
        ang = self._label_angle()
        painter.save()
        painter.translate(mid)
        painter.rotate(ang)
        painter.drawText(QPointF(-w / 2.0, -3.0 / lod), text)   # above the line, as a drawing does
        painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            for k in self.knobs:
                k.setVisible(bool(value))
        return super().itemChange(change, value)

    # -- the offset drag --------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_from = (QPointF(e.scenePos()), self.offset_in)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_from is not None:
            start, off0 = self._drag_from
            _, _, nx, ny = self._frame()
            d = (e.scenePos().x() - start.x()) * nx + (e.scenePos().y() - start.y()) * ny
            self.set_offset(off0 + d)
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_from = None
        super().mouseReleaseEvent(e)

    # -- the knobs' edits (0264) ----------------------------------------------------
    def _snap(self, sp: QPointF, free: bool) -> QPointF:
        """Where a dragged callout point lands: the tool's own snap (the
        datum, a corner, a jamb, a wall, else the grid), or the cursor
        itself when `free` (Shift)."""
        return _tool_snap(self, sp, free)

    def move_point(self, end: int, sp: QPointF, free: bool = False):
        """Knob 1 (`end` 0) or 2 (`end` 1): that measured point goes where the
        cursor is, snapped; the line follows, parallel to the new a-b."""
        p = self._snap(sp, free)
        if end == 0:
            self.set_points(p, self.b)
        else:
            self.set_points(self.a, p)

    def rotate_about(self, anchor_end: int, sp: QPointF, free: bool = False):
        """Ctrl on knob 1 or 2: the measure turns about the OTHER knob
        (`anchor_end`), its length kept, the angle snapped to the plan's
        rotation step unless `free`; the anchored callout keeps its length
        and stays orthogonal since the offset is unchanged."""
        anchor = self.b if anchor_end == 1 else self.a
        ln = self.length()
        if ln < 1e-9:
            return
        ang = math.atan2(sp.y() - anchor.y(), sp.x() - anchor.x())
        if not free:
            step = math.radians(max(1.0, float(SETTINGS.get("rotate_snap_deg", 15.0))))
            ang = round(ang / step) * step
        moved = QPointF(anchor.x() + math.cos(ang) * ln, anchor.y() + math.sin(ang) * ln)
        if anchor_end == 1:
            self.set_points(moved, self.b)
        else:
            self.set_points(self.a, moved)

    def slide_end(self, sp: QPointF):
        """Knob 3: `b` slides along the measure's own direction to where the
        cursor projects; the direction and the offset stay."""
        ux, uy, _, _ = self._frame()
        t = (sp.x() - self.a.x()) * ux + (sp.y() - self.a.y()) * uy
        t = max(1.0, wall_snap_len(t))
        self.set_points(self.a, QPointF(self.a.x() + ux * t, self.a.y() + uy * t))

    def slide_label(self, sp: QPointF):
        """Knob 4: the label slides along the line to where the cursor projects."""
        p, q = self.line_points()
        dx, dy = q.x() - p.x(), q.y() - p.y()
        ln2 = dx * dx + dy * dy
        if ln2 < 1e-9:
            return
        self.set_label_t(((sp.x() - p.x()) * dx + (sp.y() - p.y()) * dy) / ln2)

    def to_record(self, rid: str, level: str) -> dict:
        rec = {"id": rid, "level": level, "kind": "dimension",
               "pos": [float(self.a.x()), float(self.a.y())],
               "p2": [float(self.b.x()), float(self.b.y())],
               "offset_in": float(self.offset_in)}
        if abs(self.label_t - 0.5) > 1e-9:
            rec["label_t"] = float(self.label_t)
        return rec

    @classmethod
    def from_record(cls, rec: dict, floor):
        p2 = rec.get("p2") or rec["pos"]
        return cls(QPointF(*rec["pos"]), QPointF(*p2), float(rec.get("offset_in", DIM_OFFSET_IN)), floor,
                   float(rec.get("label_t", 0.5)))


def _tool_snap(item, sp: QPointF, free: bool) -> QPointF:
    """Where a dragged point lands: the Measure tool's own snap (the datum,
    a corner, a jamb, a wall, else the grid), or the cursor itself when
    `free` (Shift)."""
    if free:
        return QPointF(sp)
    views = item.scene().views() if item.scene() else []
    snap = getattr(views[0], "_measure_snap", None) if views else None
    if snap is None:
        return QPointF(sp)
    return snap(sp)[0]


class DimensionKnob(QGraphicsItem):
    """One of a selected measure's four knobs (0264): a small SOLID BLACK
    square of a fixed size in PIXELS, centred on its control point, shown
    only while the measure is selected (0266, his screen: the red boxes
    grew with the zoom and hid what they sat on). Dragging it calls the
    measure's own edit for its kind, with the modifiers read at the press:
    Ctrl rotates (knobs 1 and 2), Shift frees the snap."""

    KINDS = ("a", "b", "end", "label")
    SIZE_PX = 3.0              # drawn half-size, view pixels -- the same at every zoom
    HIT_PX = 8.0               # clickable half-size, view pixels
    INK = QColor(0, 0, 0)
    _TIPS = {
        "a": "Callout point 1 -- drag to move it (Ctrl: rotate the measure about point 2; Shift: free)",
        "b": "Callout point 2 -- drag to move it (Ctrl: rotate the measure about point 1; Shift: free)",
        "end": "The line's end -- drag along the line to change the length",
        "label": "The label -- drag along the line to slide it",
    }

    def __init__(self, dim, kind: str):
        super().__init__(dim)
        self.dim = dim
        self.kind = kind
        self.setZValue(1.0)
        self.setVisible(False)
        self._mods = Qt.KeyboardModifier.NoModifier
        self._dragging = False
        self.setToolTip(self._TIPS[kind])
        self.sync_position()

    def sync_position(self):
        self.prepareGeometryChange()
        d = self.dim
        if self.kind == "a":
            self.setPos(d.a)
        elif self.kind == "b":
            self.setPos(d.b)
        elif self.kind == "end":
            self.setPos(d.line_points()[1])
        else:
            self.setPos(d.label_point())

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _hit_half(self) -> float:
        return self.HIT_PX / self._view_scale()

    def boundingRect(self) -> QRectF:
        r = self._hit_half() + 1.0
        return QRectF(-r, -r, 2 * r, 2 * r)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        if self.isVisible():
            h = self._hit_half()
            path.addRect(QRectF(-h, -h, 2 * h, 2 * h))
        return path

    def paint(self, painter, option, widget=None):
        s = self.SIZE_PX / max(self._view_scale(), 1e-6)   # a fixed pixel size, on the point
        painter.setPen(QPen(self.INK, 0))
        painter.setBrush(QBrush(self.INK))
        painter.drawRect(QRectF(-s, -s, 2 * s, 2 * s))

    def apply_drag(self, sp: QPointF):
        free = bool(self._mods & Qt.KeyboardModifier.ShiftModifier)
        ctrl = bool(self._mods & Qt.KeyboardModifier.ControlModifier)
        if self.kind in ("a", "b"):
            end = 0 if self.kind == "a" else 1
            if ctrl:
                self.dim.rotate_about(1 - end, sp, free)
            else:
                self.dim.move_point(end, sp, free)
        elif self.kind == "end":
            self.dim.slide_end(sp)
        else:
            self.dim.slide_label(sp)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._mods = e.modifiers()
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.apply_drag(e.scenePos())
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.apply_drag(e.scenePos())
            e.accept()
        else:
            super().mouseReleaseEvent(e)


class LeaderItem(_AnnotationBase):
    """A leader (0270): a text with an arrow to the thing it names. `tip`
    is the arrow's point (the Leader tool snaps it as the Measure tool
    snaps); `anchor` is where the line ends and the text begins -- the text
    sits on a short horizontal shoulder from the anchor, on the side away
    from the tip. Drag the body to move the whole; select it for two knobs
    (the tip, snapped; the text end, free); double-click edits the text."""
    kind = "leader"
    SIZE_PX = 12.0               # the text, view pixels at any zoom
    ARROW_PX = 9.0               # the arrowhead's length, view pixels
    SHOULDER_PX = 10.0           # the shoulder under the text, view pixels
    DEFAULT_OFFSET_IN = 24.0     # a click without a drag: the text this far up and right

    def __init__(self, tip: QPointF, anchor: QPointF, text: str = "", floor=None):
        super().__init__(floor)
        self.tip = QPointF(tip)
        self.anchor = QPointF(anchor)
        self.text = str(text)
        self._drag = None
        self.knobs = [LeaderKnob(self, k) for k in LeaderKnob.KINDS]

    def shown(self) -> bool:
        return bool(SETTINGS.get("show_annotations", True))

    # -- geometry -------------------------------------------------------------
    def _font(self) -> QFont:
        f = QFont()
        f.setPixelSize(max(2, int(self.SIZE_PX / self._view_scale())))
        return f

    def _side(self) -> float:
        """+1: the text runs to the right of the anchor; -1: to the left."""
        return 1.0 if self.anchor.x() >= self.tip.x() else -1.0

    def shoulder_end(self) -> QPointF:
        lod = self._view_scale()
        return QPointF(self.anchor.x() + self._side() * self.SHOULDER_PX / lod, self.anchor.y())

    def _text_rect(self) -> QRectF:
        """The text's box in scene coordinates, on the shoulder."""
        lod = self._view_scale()
        fm = QFontMetricsF(self._font())
        w = max(fm.horizontalAdvance(self.text or " "), 6.0)
        h = fm.height()
        e = self.shoulder_end()
        x = e.x() + 2.0 / lod if self._side() > 0 else e.x() - 2.0 / lod - w
        return QRectF(x, e.y() - h * 0.8, w, h)

    def text_origin(self) -> QPointF:
        r = self._text_rect()
        return QPointF(r.left(), self.anchor.y())

    def _arrow(self):
        """The arrowhead's three corners: the tip and its base's two ends."""
        lod = self._view_scale()
        dx, dy = self.tip.x() - self.anchor.x(), self.tip.y() - self.anchor.y()
        ln = math.hypot(dx, dy) or 1.0
        ux, uy = dx / ln, dy / ln
        L = self.ARROW_PX / lod
        hw = L * 0.35
        bx, by = self.tip.x() - ux * L, self.tip.y() - uy * L
        return (QPointF(self.tip), QPointF(bx - uy * hw, by + ux * hw), QPointF(bx + uy * hw, by - ux * hw))

    def boundingRect(self) -> QRectF:
        r = QRectF(self.tip, self.anchor).normalized()
        r = r.united(self._text_rect()).united(QRectF(self.anchor, self.shoulder_end()).normalized())
        pad = self.ARROW_PX / self._view_scale() + 4.0
        return r.adjusted(-pad, -pad, pad, pad)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(self.tip)
        path.lineTo(self.anchor)
        path.lineTo(self.shoulder_end())
        st = QPainterPathStroker()
        st.setWidth(6.0 / self._view_scale())
        out = st.createStroke(path)
        out.addRect(self._text_rect())
        return out

    def paint(self, painter, option, widget=None):
        ink = _ink(self, INK)
        painter.setPen(QPen(ink, 0))
        painter.setBrush(QBrush(ink))
        painter.drawLine(self.tip, self.anchor)
        painter.drawLine(self.anchor, self.shoulder_end())
        painter.drawPolygon(*self._arrow())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setFont(self._font())
        painter.drawText(self.text_origin(), self.text)
        if self.isSelected():
            painter.setPen(QPen(SELECT_INK, 0, Qt.PenStyle.DashLine))
            painter.drawRect(self._text_rect())

    # -- edits ----------------------------------------------------------------
    def _changed(self):
        self.prepareGeometryChange()
        for k in self.knobs:
            k.sync_position()
        self.update()

    def set_points(self, tip: QPointF, anchor: QPointF):
        self.tip, self.anchor = QPointF(tip), QPointF(anchor)
        self._changed()

    def set_text(self, text: str):
        self.text = str(text)
        self._changed()

    def move_tip(self, sp: QPointF, free: bool = False):
        self.set_points(_tool_snap(self, sp, free), self.anchor)

    def move_anchor(self, sp: QPointF, free: bool = True):
        self.set_points(self.tip, QPointF(sp) if free else wall_snap(sp))

    def move_by(self, dx: float, dy: float):
        self.set_points(QPointF(self.tip.x() + dx, self.tip.y() + dy),
                        QPointF(self.anchor.x() + dx, self.anchor.y() + dy))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            for k in self.knobs:
                k.setVisible(bool(value))
        return super().itemChange(change, value)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = (e.scenePos(), QPointF(self.tip), QPointF(self.anchor))
            self.setSelected(True)
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            start, tip0, anchor0 = self._drag
            d = e.scenePos() - start
            self.set_points(tip0 + d, anchor0 + d)
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._drag is not None and e.button() == Qt.MouseButton.LeftButton:
            self._drag = None
            e.accept()
        else:
            super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        views = self.scene().views() if self.scene() else []
        parent = views[0] if views else None
        text, ok = QInputDialog.getText(parent, "Leader", "Text:", text=self.text)
        if ok and text.strip():
            self.set_text(text.strip())
        e.accept()

    # -- the document ---------------------------------------------------------
    def to_record(self, rid: str, level: str) -> dict:
        return {"id": rid, "level": level, "kind": "leader",
                "pos": [float(self.tip.x()), float(self.tip.y())],
                "p2": [float(self.anchor.x()), float(self.anchor.y())],
                "text": self.text}

    @classmethod
    def from_record(cls, rec: dict, floor):
        p2 = rec.get("p2") or rec["pos"]
        return cls(QPointF(*rec["pos"]), QPointF(*p2), rec.get("text", ""), floor)


class LeaderKnob(DimensionKnob):
    """A selected leader's two knobs (the measure's knob, re-pointed): the
    tip, dragged with the tool's snap (Shift frees), and the text end,
    dragged free."""

    KINDS = ("tip", "text")
    _TIPS = {
        "tip": "The arrow's point -- drag to move it (snaps to a corner, a jamb, a wall; Shift: free)",
        "text": "The text's end -- drag to move the text",
    }

    def sync_position(self):
        self.prepareGeometryChange()
        self.setPos(self.dim.tip if self.kind == "tip" else self.dim.anchor)

    def apply_drag(self, sp: QPointF):
        free = bool(self._mods & Qt.KeyboardModifier.ShiftModifier)
        if self.kind == "tip":
            self.dim.move_tip(sp, free)
        else:
            self.dim.move_anchor(sp, True)


class DatumItem(_AnnotationBase):
    """The level's datum: a crossed circle the Measure tool snaps to. One
    per level (placing another moves it)."""
    kind = "datum"

    def __init__(self, pos: QPointF, floor=None):
        super().__init__(floor)
        self.setPos(QPointF(pos))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

    def shown(self) -> bool:
        return bool(SETTINGS.get("show_dimensions", True))

    def boundingRect(self) -> QRectF:
        r = DATUM_R_IN + 2.0
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(_ink(self, INK), 0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        r = DATUM_R_IN
        painter.drawEllipse(QPointF(0, 0), r, r)
        painter.drawLine(QPointF(-r * 1.4, 0), QPointF(r * 1.4, 0))
        painter.drawLine(QPointF(0, -r * 1.4), QPointF(0, r * 1.4))

    def to_record(self, rid: str, level: str) -> dict:
        return {"id": rid, "level": level, "kind": "datum",
                "pos": [float(self.pos().x()), float(self.pos().y())]}

    @classmethod
    def from_record(cls, rec: dict, floor):
        return cls(QPointF(*rec["pos"]), floor)


_KINDS = {"text": TextAnnotationItem, "dimension": DimensionItem, "datum": DatumItem,
          "leader": LeaderItem}


def item_from_record(rec: dict, floor):
    """The item for a document `annotation` record, or None for a kind this
    build does not know."""
    cls = _KINDS.get(rec.get("kind"))
    return cls.from_record(rec, floor) if cls is not None else None


def annotation_items(scene, floor=None):
    return [it for it in scene.items() if isinstance(it, _AnnotationBase)
            and (floor is None or it.floor == floor)]


def datum_on(scene, floor):
    return next((it for it in scene.items() if isinstance(it, DatumItem) and it.floor == floor), None)


def nearest_datum(scene, p: QPointF, tol: float):
    d = datum_on(scene, active_floor())
    if d is None:
        return None
    if math.hypot(d.pos().x() - p.x(), d.pos().y() - p.y()) <= tol:
        return QPointF(d.pos())
    return None


def sync_annotation_visibility(scene):
    """Apply the Show-menu switches: an item whose kind is switched off is
    hidden whatever its floor says; otherwise the floor decides (the item's
    floor visibility was applied before this)."""
    if scene is None:
        return
    for it in annotation_items(scene):
        if not it.shown():
            it.setVisible(False)
        elif floor_display_mode(it.floor) == "hidden":
            it.setVisible(False)
        else:
            it.setVisible(True)
