"""0307 / his #1 -- the L2 attic knee line: the host roof's knee survives
BESIDE a dormer. Measures, per room, the host-knee and dormer-knee length
under the OLD all-or-nothing midpoint gate vs the NEW region clip in
`roofs.room_ceiling_break_lines`. Run headless:

    PYTHONPATH=. QT_QPA_PLATFORM=offscreen python docs/evidence/0307-l2-knee/receipts.py

His `wiscawayL2-fix.json` (L2 base 120, ceiling 216in abs) must be in
`fixtures/incoming/`. The headline: the two L2 attic rooms go host 14 -> 109
(the host knee recovered beside the dormer); `little-dormer-test.json` r3 is
unchanged (its test dormer is as wide as the little room)."""
import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp
import floorplanner.roofs as R
from floorplanner.config import floor_elevation
from floorplanner.roofs import RoofItem


def _seglen(p, q):
    return math.hypot(q.x() - p.x(), q.y() - p.y())


def _knee(scene, room, roofs, old):
    """`room_ceiling_break_lines` with the OLD midpoint gate (`old=True`) or the
    NEW region clip (`old=False`), returning `[(p, q, is_dormer)]`."""
    tr = R._room_trace(room)
    if tr is None:
        return []
    ceiling_abs = float(floor_elevation(room.floor)) + tr.ceiling
    margin = R._trace_margin_in(scene, room.floor)
    rooms = [tr]
    out = []
    for rf in roofs:
        h = ceiling_abs - float(floor_elevation(R._roof_datum_floor(rf)))
        join_ext = rf._clip_ext if rf.is_clipped() else (0.0, 0.0)
        region = rf._clip_region
        for p, q in R._trace_to_scene(rf, R._trace_lines_local(rf, h, join_ext)):
            dx, dy = q.x() - p.x(), q.y() - p.y()
            seg_len = math.hypot(dx, dy)
            if seg_len < R._CLIP_EPS_IN:
                continue
            ts = [0.0] + R._cut_params(p, q, rooms, margin) + [1.0]
            for t0, t1 in zip(ts, ts[1:], strict=False):
                if (t1 - t0) * seg_len < R._CLIP_EPS_IN:
                    continue
                tm = (t0 + t1) / 2.0
                mid = QPointF(p.x() + dx * tm, p.y() + dy * tm)
                if not tr.holds(mid, margin):
                    continue
                a = QPointF(p.x() + dx * t0, p.y() + dy * t0)
                b = QPointF(p.x() + dx * t1, p.y() + dy * t1)
                if old:
                    if region is not None and not region.contains(mid):
                        continue
                    out.append((a, b, rf.is_dormer()))
                else:
                    pieces = (region.clip_segment(a, b) if region is not None
                              else [(a, b)])
                    for c, d2 in pieces:
                        if _seglen(c, d2) < R._CLIP_EPS_IN:
                            continue
                        out.append((QPointF(c.x(), c.y()),
                                    QPointF(d2.x(), d2.y()), rf.is_dormer()))
    return out


def main():
    for fname in ("wiscawayL2-fix", "little-dormer-test"):
        win = fp.MainWindow()
        win.load_path(f"fixtures/incoming/{fname}.json")
        roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
        rooms = [it for it in win.scene.items() if isinstance(it, fp.RoomItem)]
        print(f"\n== {fname} ==  rooms={len(rooms)} roofs={len(roofs)}")
        for room in rooms:
            o = _knee(win.scene, room, roofs, old=True)
            n = _knee(win.scene, room, roofs, old=False)
            oh = sum(_seglen(a, b) for a, b, d in o if not d)
            nh = sum(_seglen(a, b) for a, b, d in n if not d)
            od = sum(_seglen(a, b) for a, b, d in o if d)
            nd = sum(_seglen(a, b) for a, b, d in n if d)
            tag = " CHANGED" if abs(oh - nh) > 0.5 or abs(od - nd) > 0.5 else ""
            print(f"  {room.floor} host:{oh:6.0f}->{nh:6.0f}  "
                  f"dormer:{od:6.0f}->{nd:6.0f}{tag}")


if __name__ == "__main__":
    main()
