"""Defect 23 / P4.5 -- what `room_boolean("fragment")` actually BUILDS, and what
a group move does to it on each of the two semantics.

Standalone, not collected by the suite (`pytest.ini` has `testpaths = tests`).
Run it against either tree:

    python docs/evidence/defect23_fragment_probe.py

It replays the body of `tests/test_rooms.py::test_fragment_groups_each_piece_
with_its_own_walls` -- two overlapping corner-only rooms, `fragment`, then move
the Overlap fragment's group by (300, 300) and bake -- and prints:

  1. the fragment PRODUCT's vertex identity (scene side) against the document
     the walk emits, which is where the two disagree;
  2. per (group, room): `room_owns_walls` / `walls_cover_room`, and how many of
     the room's outline corners sit on that group's own wall vertices;
  3. every room's outline before and after the move, with the wall each edge
     names and where that wall now is;
  4. `open_edges()` after the move, and for each dashed edge, how many real
     scene walls actually span it;
  5. `check(doc, deep=True)` at each step, and whether `save_path` writes.

Recorded because the numbers, not the reasoning, are what survive: the same
discipline as `defect28-ownership.json` beside it.
"""
import json
import os
import sys
import tempfile
import warnings

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from PyQt6.QtCore import QPointF                        # noqa: E402
from PyQt6.QtWidgets import QApplication                # noqa: E402

_APP = QApplication.instance() or QApplication([])      # keep it alive

import FloorPlanner as fp                               # noqa: E402
from floorplanner.design.bridge import design_from_scene    # noqa: E402
from floorplanner.design.validate import check              # noqa: E402
from floorplanner.design.verify import rebase               # noqa: E402
from floorplanner.rooms import _wall_spans_segment          # noqa: E402


def _pt(p):
    return (round(p.x(), 3), round(p.y(), 3))


def _doc(win):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return design_from_scene(win).to_dict()


def _rooms(sc):
    return sorted([it for it in sc.items() if isinstance(it, fp.RoomItem)],
                  key=lambda r: r.name)


def _walls(sc):
    return [it for it in sc.items() if isinstance(it, fp.WallItem)]


def _groups(sc):
    return [it for it in sc.items() if isinstance(it, fp.GroupItem)]


def main():
    win = fp.MainWindow()
    win.resize(1200, 800)
    sc = win.scene

    def mk(x, y, w, h, name):
        cs = [QPointF(x, y), QPointF(x + w, y),
              QPointF(x + w, y + h), QPointF(x, y + h)]
        r = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2),
                        fp.room_path_from_corners(cs), fp.poly_area_sqft(cs),
                        corners=cs)
        sc.addItem(r)
        return r

    r1 = mk(0, 0, 120, 96, "Room 1")
    r2 = mk(72, 48, 120, 96, "Room 2")
    rebase(win)                       # the constructed overlap is the baseline
    win._sel_order = [r1, r2]
    r1.setSelected(True)
    r2.setSelected(True)

    win.room_boolean("fragment")
    print("== 0. the originals are GONE; all three rooms are fragment's own ==")
    print("   Room 1 item still in scene:", r1.scene() is not None,
          " Room 2 item still in scene:", r2.scene() is not None)
    print("   rooms now:", [r.name for r in _rooms(sc)])

    print("\n== 1. the fragment PRODUCT: scene vertex identity vs the document ==")
    bypt = {}
    for w in _walls(sc):
        for a in ("p1", "p2"):
            bypt.setdefault(_pt(w.end_vertex(a).point()), set()).add(
                id(w.end_vertex(a)))
    for r in _rooms(sc):
        for e in r.outline:
            bypt.setdefault(_pt(e.v.point()), set()).add(id(e.v))
    print("   scene: %d geometric points carrying %d distinct Vertex objects"
          % (len(bypt), sum(len(s) for s in bypt.values())))
    for k in sorted(bypt):
        if len(bypt[k]) > 1:
            print("     point %-14s -> %d distinct vertices" % (k, len(bypt[k])))
    d = _doc(win)
    print("   document: %d vertices, %d walls, %d rooms"
          % (len(d["vertices"]), len(d["walls"]), len(d["rooms"])))
    print("   check(deep=True) on the product:", check(d, deep=True) or "CLEAN")

    print("\n== 2. does any fragment group OWN the room it encloses? ==")
    for g in _groups(sc):
        gw = {c for c in g.childItems() if isinstance(c, fp.WallItem)}
        vs = {id(w.end_vertex(a)) for w in gw for a in ("p1", "p2")}
        print("   group of %d walls, %d distinct corner vertices"
              % (len(gw), len(vs)))
        for r in _rooms(sc):
            if not (fp.walls_cover_room(gw, r) or fp.room_owns_walls(gw, r)):
                continue
            print("     vs %-8s room_owns_walls=%-5s walls_cover_room=%-5s "
                  "outline corners on this group's vertices %d/%d"
                  % (r.name, fp.room_owns_walls(gw, r),
                     fp.walls_cover_room(gw, r),
                     sum(1 for e in r.outline if id(e.v) in vs),
                     len(r.outline)))

    def outlines(when):
        print("\n== %s ==" % when)
        for r in _rooms(sc):
            print("   %-8s area=%-8s open_edges=%d"
                  % (r.name, round(r.area_sqft, 2), len(r.open_edges())))
            for e in r.outline:
                print("      corner %-14s names wall now at %s"
                      % (_pt(e.v.point()),
                         (_pt(e.wall.p1), _pt(e.wall.p2))
                         if e.wall is not None else None))

    outlines("3. outlines BEFORE the move")

    overlap = next(r for r in _rooms(sc) if r.name == "Overlap")
    g = next(gp for gp in _groups(sc) if fp.walls_cover_room(
        {c for c in gp.childItems() if isinstance(c, fp.WallItem)}, overlap))
    pre_open = {r.name: len(r.open_edges()) for r in _rooms(sc)}
    g.setPos(300, 300)
    g.bake()
    outlines("3. outlines AFTER the move (+300, +300) and bake")

    print("\n== 4. dashed open edges, and whether a real wall runs along them ==")
    print("   precondition, open_edges before the move:", pre_open)
    ws = _walls(sc)
    for r in _rooms(sc):
        cs = r.corners or []
        n = len(cs)
        opens = r.open_edges()
        for i, e in enumerate(r.outline):
            if e not in opens:
                continue
            a, b = cs[i], cs[(i + 1) % n]
            cov = [w for w in ws if _wall_spans_segment(w, a, b)]
            print("     %-8s draws (%g,%g)-(%g,%g) DASHED; scene walls that "
                  "actually span it: %d" % (r.name, a.x(), a.y(), b.x(), b.y(),
                                            len(cov)))

    print("\n== 5. the document, and whether a save is allowed ==")
    d = _doc(win)
    print("   check(deep=True):", check(d, deep=True) or "CLEAN")
    for r in sorted(d["rooms"], key=lambda r: r["name"]):
        print("     doc room %-8s edges with no wall: %d of %d"
              % (r["name"],
                 sum(1 for e in r["outline"] if not e.get("wall")),
                 len(r["outline"])))
    p = os.path.join(tempfile.gettempdir(), "defect23_fragment_probe.json")
    if os.path.exists(p):
        os.remove(p)
    try:
        win.save_path(p)
    except Exception as exc:                             # noqa: BLE001
        print("   save_path raised:", type(exc).__name__)
    print("   save wrote the file:", os.path.exists(p))
    if os.path.exists(p):
        saved = json.load(open(p))
        V = {v["id"]: (v["x"], v["y"]) for v in saved["vertices"]}
        for r in sorted(saved["rooms"], key=lambda r: r["name"]):
            print("     SAVED %-8s outline=%s"
                  % (r["name"], [V[e["v"]] for e in r["outline"]]))
        print("     SAVED wall segments:",
              sorted((V[w["v1"]], V[w["v2"]]) for w in saved["walls"]))
        os.remove(p)


if __name__ == "__main__":
    main()
