"""R6.c, measured before it is built (0197-ruling.md sec5: "the roof tool
across levels"): what does the roof tool do TODAY when the level being
edited is not the only one with roofs and walls?

His fixture, `fixtures/wiscaway-2level-stacked-floor.json`, the upper level
active, "show other floors" off and on. Every route the roof tool takes
through the scene is driven by real mouse events on the view:

  1. the census -- which roofs of which level are visible, enabled, hittable;
  2. a ridge PRESS on a line of another level's ghosted roof;
  3. the ridge's start snap beside a wall end only the other level has;
  4. the EAVES PICK on a wall only the other level has;
  5. a DORMER press on ground only another level's roof covers;
  6. a roof selected on one level, then the level switched: is it still
     selected, do its grips show, does a grip drag edit it;
  7. a ridge awaiting its eaves pick, then the level switched;
  8. beside the roof tool, the same wall lookup in the Door tool.

A measurement; nothing is changed. Output kept as
`r6c-roof-tool-levels-probe.before.txt` (on `main`) and
`...after.txt` (with R6.c built).

    python docs/evidence/r6c_roof_tool_levels_probe.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QEvent, QPointF, Qt        # noqa: E402
from PyQt6.QtGui import QMouseEvent                 # noqa: E402
from PyQt6.QtWidgets import (                      # noqa: E402
    QApplication, QDialog, QInputDialog, QMessageBox,
)

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp                            # noqa: E402
from floorplanner.roofs import (                     # noqa: E402
    RoofEndMarkerItem, RoofGripItem, RoofItem, footprint_polygon, host_roof_at,
)

PLAN = os.path.join(ROOT, "fixtures", "wiscaway-2level-stacked-floor.json")
LOWER, UPPER = "default", "upper"
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton

QDialog.exec = lambda self: QDialog.DialogCode.Accepted     # no modal, headless
QInputDialog.getText = staticmethod(lambda *a, **k: (k.get("text", "3280"), True))
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)


def send(win, etype, p, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(p[0], p[1]))
    QApplication.sendEvent(vp, QMouseEvent(
        etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons,
        Qt.KeyboardModifier.NoModifier))


def drag(win, a, b):
    send(win, QEvent.Type.MouseButtonPress, a, LEFT, LEFT)
    send(win, QEvent.Type.MouseMove, b, NONE, LEFT)
    send(win, QEvent.Type.MouseButtonRelease, b, LEFT, NONE)


def click(win, a):
    send(win, QEvent.Type.MouseButtonPress, a, LEFT, LEFT)
    send(win, QEvent.Type.MouseButtonRelease, a, LEFT, NONE)


def fresh(show_others, floor=UPPER):
    win = fp.MainWindow()
    win.prepare_headless()
    win.load_path(PLAN)
    win.show_other_floors = show_others
    win.switch_floor(floor)
    win._sync_floor_state()
    win.view.fitInView(win.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    return win


def roofs(win, floor=None):
    return sorted((it for it in win.scene.items()
                   if isinstance(it, RoofItem) and (floor is None or it.floor == floor)),
                  key=lambda r: (r.floor, r.p1.x(), r.p1.y()))


def walls(win, floor):
    return [it for it in win.scene.items()
            if isinstance(it, fp.WallItem) and it.floor == floor]


def lonely_point_on(win, roof):
    """A point on one of `roof`'s drawn lines where the scene holds no roof,
    grip or marker of any OTHER roof, and no wall -- so whatever a press
    there meets, it meets because of `roof`. Chosen by GEOMETRY, not by
    whether `roof` answers the hit, since that answer is the measurement."""
    lines = (roof._drawn_lines() + list(roof._seams)) if roof.is_clipped() \
        else [(p, q) for _, p, q in roof._plan_lines()]
    for p, q in lines:
        for k in range(1, 40):
            t = k / 40.0
            pt = QPointF(p.x() + (q.x() - p.x()) * t, p.y() + (q.y() - p.y()) * t)
            hit = win.scene.items(pt)
            if any((isinstance(it, RoofItem) and it is not roof)
                   or isinstance(it, (RoofGripItem, RoofEndMarkerItem, fp.WallItem))
                   for it in hit):
                continue
            return pt
    return None


def lonely_wall_point(win, floor, other):
    """The midpoint of a wall of `floor` where no wall of `other` and no
    roof line is under the cursor."""
    for w in sorted(walls(win, floor), key=lambda w: -w.length()):
        m = QPointF((w.p1.x() + w.p2.x()) / 2.0, (w.p1.y() + w.p2.y()) / 2.0)
        hit = win.scene.items(m)
        if w in hit and not any(
                (isinstance(it, fp.WallItem) and it.floor == other)
                or isinstance(it, (RoofItem, RoofGripItem, RoofEndMarkerItem))
                for it in hit):
            return w, m
    return None, None


def blank_run(win, length=120.0):
    """A horizontal run where nothing at all is under the press."""
    r = win.scene.itemsBoundingRect()
    y = r.top() + 30.0
    while y < r.bottom():
        x = r.left() + 30.0
        while x + length < r.right():
            if not win.scene.items(QPointF(x, y)) and \
                    not win.scene.items(QPointF(x + length, y)):
                return (x, y), (x + length, y)
            x += 36.0
        y += 36.0
    return None, None


def main():
    for show in (False, True):
        print(f"\n== upper level active, show other floors = {show} ==")

        # ---- 1. the census
        win = fresh(show)
        for rf in roofs(win):
            print(f"   roof {rf.floor:8s} ridge@({rf.p1.x():.0f},{rf.p1.y():.0f})  "
                  f"visible={rf.isVisible()!s:5s} enabled={rf.isEnabled()!s:5s} "
                  f"hit shape empty={rf.shape().isEmpty()!s:5s} "
                  f"marker hit shape empty={rf.marker.shape().isEmpty()}")
        vis_w = {fl: sum(1 for w in walls(win, fl) if w.isVisible()) for fl in (LOWER, UPPER)}
        print(f"   walls visible by floor: {vis_w}")

        # ---- 2. a ridge press on a line of another level's ghosted roof
        ghost = next((rf for rf in roofs(win, LOWER) if rf.isVisible()), None)
        pt = lonely_point_on(win, ghost) if ghost is not None else None
        if pt is None:
            print("   2. (no lower roof line stands clear of everything else)")
        else:
            before = len(roofs(win))
            print(f"   2. the lower roof answers a hit query on its own ghosted line: "
                  f"{ghost in win.scene.items(pt)}")
            win.set_tool(fp.TOOL_ROOF_RIDGE)
            drag(win, (pt.x(), pt.y()), (pt.x() + 96.0, pt.y()))
            started = win.view._roof_awaiting_eaves is not None
            print(f"      ridge tool, press on the lower roof's ghosted line at "
                  f"({pt.x():.0f},{pt.y():.0f}), drag 96in: a ridge started = {started}; "
                  f"roofs {before} -> {len(roofs(win))}")
            a, b = blank_run(win)
            if a is not None:
                win.view.cancel_temp()
                n0 = len(roofs(win))
                drag(win, a, b)
                print(f"      control, the same drag on blank canvas at {a}: a ridge "
                      f"started = {win.view._roof_awaiting_eaves is not None}; "
                      f"roofs {n0} -> {len(roofs(win))}")
        win.close()

        # ---- 3. the start snap beside a wall end only the lower level has
        win = fresh(show)
        # (the two searches `_snap_start` makes, asked directly: a grid snap
        # can land on a wall end by itself, so where the snap LANDS proves
        # nothing about which level's wall drew it there)
        from floorplanner.walls import nearest_wall_body, nearest_wall_endpoint
        upper_ws = walls(win, UPPER)
        n_end = n_body = n_asked = 0
        for w in walls(win, LOWER):
            for q in (w.p1, w.p2):
                if any(abs(q.x() - u.x()) + abs(q.y() - u.y()) < 40
                       for uw in upper_ws for u in (uw.p1, uw.p2)):
                    continue
                near = QPointF(q.x() + 2.0, q.y() + 2.0)
                n_asked += 1
                n_end += nearest_wall_endpoint(win.scene, near, 10.0) is not None
                hit = nearest_wall_body(win.scene, near, 10.0)
                n_body += hit is not None and hit[0].floor != UPPER
        print(f"   3. start snap asked 2in from {n_asked} wall ends only the lower level has: "
              f"snapped to a wall END {n_end} times, to a lower wall's BODY {n_body} times")
        win.close()

        # ---- 4. the eaves pick on a wall only the lower level has
        win = fresh(show)
        win.set_tool(fp.TOOL_ROOF_RIDGE)
        lw, m = lonely_wall_point(win, LOWER, UPPER)
        a, b = blank_run(win)
        if lw is None or a is None:
            print(f"   4. (no lower-only wall is under the cursor: wall={lw is not None}, "
                  f"blank run={a is not None})")
        else:
            drag(win, a, b)
            pending = win.view._roof_awaiting_eaves
            click(win, (m.x(), m.y()))
            taken = pending is not None and win.view._roof_awaiting_eaves is None
            print(f"   4. ridge sketched on blank {a}-{b} (floor {getattr(pending, 'floor', None)}), "
                  f"eaves click on the lower-only wall at ({m.x():.0f},{m.y():.0f}): "
                  f"the pick was TAKEN = {taken}"
                  + (f", spans {[round(s, 1) for s in pending.span_in]}" if taken else ""))
        win.close()

        # ---- 5. a dormer press on ground only the lower level's roof covers
        win = fresh(show)
        win.set_tool(fp.TOOL_ROOF_DORMER)
        spot = None
        for rf in roofs(win, LOWER):
            poly = footprint_polygon(rf)
            xs, ys = [p.x() for p in poly], [p.y() for p in poly]
            y = min(ys) + 18.0
            while y < max(ys) and spot is None:
                x = min(xs) + 18.0
                while x < max(xs):
                    p = QPointF(x, y)
                    if host_roof_at(win.scene, p, LOWER) is rf \
                            and host_roof_at(win.scene, p, UPPER) is None:
                        spot = (rf, p)
                        break
                    x += 24.0
                y += 24.0
            if spot is not None:
                break
        if spot is None:
            print("   5. (every point a lower roof owns is also under an upper roof)")
        else:
            rf, p = spot
            n0 = len(roofs(win))
            drag(win, (p.x(), p.y()), (p.x() + 36.0, p.y()))
            print(f"   5. dormer tool, press at ({p.x():.0f},{p.y():.0f}) where only the lower "
                  f"roof ridge@({rf.p1.x():.0f},{rf.p1.y():.0f}) owns the ground "
                  f"(shown={rf.isVisible()}): roofs {n0} -> {len(roofs(win))}; "
                  f"status: {win.statusBar().currentMessage()!r}")
        win.close()

        # ---- 6. a roof selected, then the level switched
        win = fresh(show)
        rf = roofs(win, UPPER)[0]
        rf.setSelected(True)
        win.switch_floor(LOWER)
        grips = [g for g in rf.grips if g.isVisible()]
        print(f"   6. upper roof ridge@({rf.p1.x():.0f},{rf.p1.y():.0f}) selected, then the "
              f"level switched to '{LOWER}': visible={rf.isVisible()} enabled={rf.isEnabled()} "
              f"selected={rf.isSelected()} grips showing={len(grips)}")
        g = next((g for g in grips if g.kind == "eave_l"), None)
        if g is not None:
            span0 = list(rf.span_in)
            gp = g.scenePos()
            _, _, nx, ny = rf._axis()
            drag(win, (gp.x(), gp.y()), (gp.x() + nx * 48.0, gp.y() + ny * 48.0))
            print(f"      its eave grip dragged 48in from the lower level: span "
                  f"{[round(s, 1) for s in span0]} -> {[round(s, 1) for s in rf.span_in]}")
        win.close()

        # ---- 7. a ridge awaiting its eaves pick, then the level switched
        win = fresh(show)
        win.set_tool(fp.TOOL_ROOF_RIDGE)
        a, b = blank_run(win)
        if a is not None:
            drag(win, a, b)
            pending = win.view._roof_awaiting_eaves
            win.switch_floor(LOWER)
            still = win.view._roof_awaiting_eaves
            print(f"   7. ridge sketched on '{UPPER}', awaiting eaves, then the level switched: "
                  f"still awaiting = {still is not None}; the pending roof's floor "
                  f"{getattr(pending, 'floor', None)!r}, visible={pending.isVisible()}, "
                  f"in the scene={pending.scene() is not None}")
            lw = max(walls(win, LOWER), key=lambda w: w.length())
            m = QPointF((lw.p1.x() + lw.p2.x()) / 2.0, (lw.p1.y() + lw.p2.y()) / 2.0)
            click(win, (m.x(), m.y()))
            print(f"      then an eaves click on a '{LOWER}' wall: the pick was taken = "
                  f"{still is not None and win.view._roof_awaiting_eaves is None}; "
                  f"the roof's floor {getattr(pending, 'floor', None)!r}, "
                  f"spans {[round(s, 1) for s in pending.span_in]}")
        win.close()

        # ---- 8. beside the roof tool, the same wall lookup: the Door tool
        win = fresh(show)
        lw, m = lonely_wall_point(win, LOWER, UPPER)
        if lw is None:
            print("   8. (no lower-only wall is under the cursor)")
        else:
            n0 = sum(1 for it in win.scene.items() if isinstance(it, fp.OpeningItem)
                     and it.wall.floor == LOWER)
            win.set_tool(fp.TOOL_DOOR)
            click(win, (m.x(), m.y()))
            n1 = sum(1 for it in win.scene.items() if isinstance(it, fp.OpeningItem)
                     and it.wall.floor == LOWER)
            print(f"   8. Door tool, click on the lower-only wall at ({m.x():.0f},{m.y():.0f}) "
                  f"from the upper level: lower-level openings {n0} -> {n1}")
        win.close()


if __name__ == "__main__":
    main()
