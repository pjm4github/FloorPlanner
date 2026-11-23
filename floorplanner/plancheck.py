"""Check plan for problems -- a persistent, plan-wide overlay of red boxes at
every design problem on the active floor (Patrick, 2026-11).

The console already carries the unwelded-end warning (`design_from_scene`'s
`_warn_unwelded`). This is the AT-A-GLANCE half that warning asked for: run
"Check plan", and every problem the validator can place gets a red box drawn
on the plan at once -- the fifteen referential invariants (`validate.check`,
located by `design.locate`, the same resolver the "Malformed design file"
report uses) AND the unwelded wall ends the warning itself counts (a replay
of `legacy.weld_endpoints`, the same measurement the walk's `_weld_delta`
makes -- an end sitting within the 9" join tolerance of a neighbour without
being welded to it, which catches the end-to-body T-junction gaps that the
vertex-pair `near_vertex_gaps` behind "Edit > Review wall gaps..." does not).
"Clear" takes the boxes down; "Show/hide" toggles them without recomputing.

SCOPE: the active floor only (Patrick). `check`/`near_vertex_gaps` see the
WHOLE document, so the scan still knows about other floors -- their count
rides the status line -- but a box is drawn only for a problem on the floor
being edited, because that is the floor whose geometry is visible. Switch
floor and run it again to box the next floor's problems.

The markers are plain `QGraphicsRectItem`s and nothing else:

  * NOT serialised. `snapshot()`, `design_from_scene`, `serialize()` and the
    PDF/DXF exports all walk the scene by `isinstance` of a MODELLED type
    (WallItem, RoomItem, ...). A bare rect is none of them, so it never
    enters a document, never dirties the plan, and never prints.
  * FLOOR-AWARE for free. Each marker carries the `floor` it was computed on,
    so `config.apply_floor_visibility` and `_apply_floor_stacking` hide, show
    and band it exactly as they do that floor's walls -- the boxes vanish when
    you leave the floor and come back when you return, with no coupling to
    the floor-switch path (those passes only ever call the generic
    `setVisible` / `setEnabled` / `setZValue` / `setOpacity`, all safe on a
    rect).
  * CLICK-THROUGH. They accept no mouse buttons, so a box over a wall does
    not stop you selecting or dragging the wall underneath it.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPen


@dataclass(frozen=True)
class ProblemSpot:
    """A placeable design problem: the floor it is on (a NAME, what the app
    switches floors by), a plan rectangle `(x0, y0, x1, y1)` in inches around
    it, a human label, and a kind tag (`"invariant"` or `"gap"`)."""
    floor: str | None
    rect: tuple
    label: str
    kind: str


def _unwelded_ends(scene):
    """Each wall end the runtime weld WOULD move, as `((x, y), floor)` in scene
    inches -- the finding behind `design_from_scene`'s unwelded-end warning.

    Replays `weld_endpoints` on a COPY (it mutates in place), exactly as the
    walk's `_weld_delta` does, and reports the end's ORIGINAL position. One
    pass over every floor's walls with the `floor` key set, so the weld stays
    within a floor just as the walk's per-level call does; the caller filters
    to the active floor. An end moved more than `WELD_TOL` (0.6", below which
    two coordinates ARE one vertex) is the gap."""
    import copy
    import math

    from floorplanner.design.legacy import WELD_TOL, weld_endpoints
    from floorplanner.walls import WallItem

    if scene is None:
        return []
    raw = [{"p1": [w.p1.x(), w.p1.y()], "p2": [w.p2.x(), w.p2.y()],
            "floor": getattr(w, "floor", None)}
           for w in scene.items() if isinstance(w, WallItem)]
    probe = copy.deepcopy(raw)
    weld_endpoints(probe)                      # mutates probe; raw is untouched
    out = []
    for orig, welded in zip(raw, probe, strict=True):
        for k in ("p1", "p2"):
            if math.dist(tuple(orig[k]), tuple(welded[k])) > WELD_TOL:
                out.append(((orig[k][0], orig[k][1]), orig["floor"]))
    return out


def problem_spots(win):
    """Every placeable design problem, split for the active floor.

    Returns `(spots, other_floors, unplaceable)`:
      * `spots`        -- ProblemSpots ON the active floor (what gets boxed),
      * `other_floors` -- how many problems sit on other floors,
      * `unplaceable`  -- how many messages named nothing the document holds
                          (so `locate` could not place them).
    """
    from floorplanner.design.bridge import design_from_scene
    from floorplanner.design.locate import locate
    from floorplanner.design.validate import check

    rep = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")        # the scan is the report now
        doc = design_from_scene(win, report=rep).to_dict()

    active = getattr(win, "active_floor", None)
    spots, other, unplaceable = [], 0, 0

    # -- the fifteen referential invariants, placed by the shared resolver ----
    for msg in check(doc, deep=True):
        sp = locate(doc, msg)
        if sp is None or not sp.rect:
            unplaceable += 1
            continue
        if sp.level is not None and sp.level != active:
            other += 1
            continue
        spots.append(ProblemSpot(sp.level, tuple(sp.rect), msg, "invariant"))

    # -- the unwelded wall ends: EXACTLY what the console warning counts -------
    for (x, y), floor in _unwelded_ends(getattr(win, "scene", None)):
        if floor is not None and floor != active:
            other += 1
            continue
        spots.append(ProblemSpot(
            floor, (x, y, x, y),
            'unwelded wall end within 9" of a neighbour', "gap"))

    return spots, other, unplaceable


class PlanCheckOverlay:
    """The red boxes themselves, owned by one scene. Add with `show_spots`,
    take down with `clear`, toggle with `set_visible`."""

    #: breathing room each side of a problem's own rectangle, in inches
    PAD_IN = 6.0
    #: the least a box spans, so a single vertex is not an invisible dot
    MIN_BOX_IN = 12.0
    #: above walls, rooms, roofs -- the GapReviewDialog marker's own band
    ZVALUE = 10_000

    def __init__(self, scene):
        self.scene = scene
        self.items = []
        self._visible = True

    @property
    def active(self) -> bool:
        """True while any box is on the scene."""
        return bool(self.items)

    def clear(self):
        for it in self.items:
            try:
                self.scene.removeItem(it)
            except RuntimeError:               # already gone
                pass
        self.items = []

    def _box(self, rect) -> QRectF:
        x0, y0, x1, y1 = rect
        r = QRectF(QPointF(x0, y0), QPointF(x1, y1)).normalized().adjusted(
            -self.PAD_IN, -self.PAD_IN, self.PAD_IN, self.PAD_IN)
        if r.width() < self.MIN_BOX_IN:
            grow = (self.MIN_BOX_IN - r.width()) / 2.0
            r.adjust(-grow, 0, grow, 0)
        if r.height() < self.MIN_BOX_IN:
            grow = (self.MIN_BOX_IN - r.height()) / 2.0
            r.adjust(0, -grow, 0, grow)
        return r

    def show_spots(self, spots):
        """Replace any current boxes with one per spot, honouring the live
        show/hide state."""
        self.clear()
        for sp in spots:
            pen = QPen(QColor(220, 30, 30), 2.0)
            pen.setCosmetic(True)              # 2px at any zoom
            it = self.scene.addRect(self._box(sp.rect), pen)
            it.setZValue(self.ZVALUE)
            it.setToolTip(sp.label)
            it.setAcceptedMouseButtons(Qt.MouseButton.NoButton)   # click-through
            it.setVisible(self._visible)
            # the floor it was computed on, so apply_floor_visibility and the
            # stacking pass manage it exactly like that floor's walls. A plain
            # tag the rest of the app can read but never mistakes for a model.
            if sp.floor is not None:
                it.floor = sp.floor
            it._fp_plan_marker = True
            self.items.append(it)

    def set_visible(self, on: bool):
        self._visible = bool(on)
        for it in self.items:
            it.setVisible(self._visible)
