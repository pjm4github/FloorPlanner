#!/usr/bin/env python3
"""D61 ITEM 2, THE CONSEQUENCE: does a DIVORCED outline corner follow a drag?

    python docs/evidence/d61_divorce_behaviour.py <plan.json>

`d61_normalize_outline_arrow.py` measured that `weld_scene` leaves outline
corners holding a `Vertex` object that no wall at that coordinate holds any
more -- 62 of 97 on Patrick's plan. That is a PARSE result about state. Whether
it matters is a RUN question, and this is the run.

`WallItem` gathers the outline edges a corner drag must carry with
`by_id.get(id(e.v))` (`walls.py:1979`) -- BY VERTEX IDENTITY. Reading that, a
divorced edge cannot be gathered. Reading is not measuring, so this drives the
real gesture through the view and reads the room's own geometry afterwards.

-- TWO ARMS, AND THE FIRST ONE IS THE POSITIVE CONTROL --

ARM A (control): the SAME gesture, same plan, on a corner that is NOT divorced.
The room MUST follow. If it does not, this probe is not measuring divorce -- it
is measuring a drag that does nothing, and arm B's "did not follow" would be
worth nothing. No verdict is reported from arm B unless arm A moved the room.

ARM B: a divorced corner. Does the room follow?

The measurement is the ROOM's own derived geometry (`corners`, `area_sqft`),
not an internal flag: what is at stake is whether the user's room follows the
user's wall.
"""
import json
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
PLAN = os.path.abspath(sys.argv[1])

from PyQt6.QtCore import QEvent, QPointF, Qt        # noqa: E402
from PyQt6.QtGui import QMouseEvent                  # noqa: E402
from PyQt6.QtWidgets import QApplication             # noqa: E402

app = QApplication([])
import FloorPlanner as fp                            # noqa: E402
import floorplanner.vertex as V                      # noqa: E402
import floorplanner.walls as W                       # noqa: E402

TOL = 0.05


def rooms_of(win):
    return [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]


def walls_of(win):
    return [i for i in win.scene.items() if isinstance(i, fp.WallItem)]


def survey(win):
    """Outline corners, each with the walls that HOLD its object and the walls
    whose end merely LIES on it."""
    ws = walls_of(win)
    out = {}
    for r in rooms_of(win):
        for e in r.outline:
            v = getattr(e, "v", None)
            if not isinstance(v, V.Vertex):
                continue
            rec = out.setdefault(id(v), {"v": v, "at": (v.x, v.y),
                                         "rooms": set(), "by_id": [],
                                         "by_point": []})
            rec["rooms"].add(r)
    for w in ws:
        for v, p in ((w._v1, w.p1), (w._v2, w.p2)):
            if id(v) in out:
                out[id(v)]["by_id"].append(w)
            for rec in out.values():
                if math.dist((p.x(), p.y()), rec["at"]) <= TOL:
                    rec["by_point"].append(w)
    return out


def open_plan():
    win = fp.MainWindow()
    win.resize(1400, 1000)
    win.show()
    win.load_path(PLAN)
    win.zoom_fit()
    win.set_tool(fp.TOOL_SELECT)
    app.processEvents()
    return win


def press_point(win, wall):
    """A point on the wall's BODY that the view actually hits.

    The midpoint is not it: on a real plan the middle of a long wall is very
    often a door, and `scene.itemAt` returns the `OpeningItem`. The first draft
    of this probe pressed there, selected the opening, and reported a wall that
    "did not move" -- which is precisely what the control existed to catch."""
    for f in (0.5, 0.35, 0.65, 0.2, 0.8, 0.12, 0.88, 0.28, 0.72):
        p = QPointF(wall.p1.x() + (wall.p2.x() - wall.p1.x()) * f,
                    wall.p1.y() + (wall.p2.y() - wall.p1.y()) * f)
        if win.scene.itemAt(p, win.view.transform()) is wall:
            return p
    return None


def drag_wall_body(win, wall, start_scene, dx_scene, dy_scene):
    """A real body drag: press a point ON the wall, move, release."""
    vp = win.view.viewport()
    mid = start_scene
    start = win.view.mapFromScene(mid)
    end = win.view.mapFromScene(QPointF(mid.x() + dx_scene, mid.y() + dy_scene))

    def send(t, pt, btn, btns):
        QApplication.sendEvent(vp, QMouseEvent(
            t, QPointF(pt), vp.mapToGlobal(QPointF(pt)), btn, btns,
            Qt.KeyboardModifier.NoModifier))
        app.processEvents()

    send(QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton,
         Qt.MouseButton.LeftButton)
    for k in (1, 2, 3):
        send(QEvent.Type.MouseMove,
             start + (end - start) * (k / 3.0),
             Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton)
    send(QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.LeftButton,
         Qt.MouseButton.NoButton)


def try_arm(kind, normalize):
    """Pick a corner of `kind` ('plain' | 'divorced'), drag the wall at it, and
    report whether the room's own geometry followed."""
    win = open_plan()
    if normalize:
        W.normalize_walls(win.scene)
        app.processEvents()
    sv = survey(win)

    cand = None
    for rec in sv.values():
        divorced = not rec["by_id"] and bool(rec["by_point"])
        if kind == "divorced" and not divorced:
            continue
        if kind == "plain" and (divorced or not rec["by_id"]):
            continue
        movers = rec["by_point"] if divorced else rec["by_id"]
        hit = None
        for w in movers:
            if w.length() <= 12:
                continue
            p = press_point(win, w)
            if p is not None:
                hit = (w, p)
                break
        if hit is None:
            continue
        wall, press_at = hit
        room = next(iter(rec["rooms"]))
        cand = (rec, wall, room, press_at)
        break
    if cand is None:
        win.close()
        return {"arm": kind, "result": "NO CANDIDATE FOUND"}

    rec, wall, room, press_at = cand
    at = rec["at"]
    before_corners = [(round(p.x(), 3), round(p.y(), 3)) for p in room.corners]
    before_area = round(room.area_sqft, 2)
    before_pt = (rec["v"].x, rec["v"].y)
    wall_end_before = [(round(wall.p1.x(), 3), round(wall.p1.y(), 3)),
                       (round(wall.p2.x(), 3), round(wall.p2.y(), 3))]

    drag_wall_body(win, wall, press_at, 24.0, 24.0)
    app.processEvents()

    after_corners = [(round(p.x(), 3), round(p.y(), 3)) for p in room.corners]
    after_area = round(room.area_sqft, 2)
    wall_end_after = [(round(wall.p1.x(), 3), round(wall.p1.y(), 3)),
                      (round(wall.p2.x(), 3), round(wall.p2.y(), 3))]
    wall_moved = wall_end_before != wall_end_after
    room_moved = before_corners != after_corners

    # did the CORNER AT THIS POINT survive in the room, unmoved, while the wall
    # left it behind?  That is the stranding, stated positionally.
    still_there = any(math.dist(c, at) <= TOL for c in after_corners)

    out = {
        "arm": kind,
        "normalize_walls_run_first": normalize,
        "corner_at": [round(x, 3) for x in at],
        "room": room.name,
        "wall_holds_this_object": len(rec["by_id"]),
        "wall_ends_at_this_point": len(rec["by_point"]),
        "wall_end_before": wall_end_before,
        "wall_end_after": wall_end_after,
        "WALL_MOVED": wall_moved,
        "room_area_before": before_area,
        "room_area_after": after_area,
        "ROOM_FOLLOWED": room_moved,
        "corner_still_at_the_old_point_after": still_there,
        "corner_point_before": [round(x, 3) for x in before_pt],
        "corner_point_after": [round(rec["v"].x, 3), round(rec["v"].y, 3)],
    }
    win.close()
    return out


arm_a = try_arm("plain", normalize=False)
arm_b = try_arm("divorced", normalize=True)
control_ok = arm_a.get("WALL_MOVED") and arm_a.get("ROOM_FOLLOWED")

json.dump({
    "plan": os.path.basename(PLAN),
    "CONTROL": {
        "statement": ("ARM A drags a NON-divorced corner and the room must "
                      "follow; without that, ARM B's 'did not follow' is "
                      "evidence of nothing"),
        "verdict": "PASS" if control_ok else "FAIL",
    },
    "ARM_A_control_plain_corner": arm_a,
    "ARM_B_divorced_corner": arm_b,
    "VERDICT": ("not reportable -- control failed" if not control_ok else
                ("A DIVORCED CORNER DOES NOT FOLLOW ITS WALL"
                 if arm_b.get("WALL_MOVED") and not arm_b.get("ROOM_FOLLOWED")
                 else "a divorced corner followed anyway -- divorce is benign "
                      "on this path")),
}, sys.stdout, indent=1)
sys.stdout.write(chr(10))
