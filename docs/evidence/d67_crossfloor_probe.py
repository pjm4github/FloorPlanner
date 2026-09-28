"""D67 -- reproduce or refute (0197-ruling.md sec5): "grouping and dragging on
the second floor collects vertices belonging to the first, and the drag moves
both." Testimony since 2026-08-11, never reproduced; its three candidate
sites were named UNMEASURED. D67 names its own fixture and its own test:
one gesture on `examples/roundedMultifloor.json` -- drag across floors, undo,
compare floor 1 to pristine.

This probe runs every route a selection can take on the second floor --
the rubber band, select-all, a click where only a first-floor item lies, a
group -- with "show other floors" ON and OFF, then moves what was selected
(a mouse drag, an arrow nudge), and compares BOTH floors to pristine after
the move and again after undo. It also answers the question under D67's
third bullet directly: after a load, is any `Vertex` held by walls of two
floors? And, for every selected room, it asks the two calls `group_selected`
makes on a room's behalf whether either returns a wall of another floor.

Nothing here is a test and nothing is changed: a measurement, its output
kept beside it as `d67-crossfloor-probe.txt`.

    python docs/evidence/d67_crossfloor_probe.py
"""
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QPointF, QRectF          # noqa: E402
from PyQt6.QtWidgets import QApplication          # noqa: E402

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp                          # noqa: E402

PLAN = os.path.join(ROOT, "examples", "roundedMultifloor.json")
LOWER, UPPER = "default", "second"
BAND = QRectF(600.0, 0.0, 1200.0, 1200.0)          # the whole plan, both floors


def fingerprint(win):
    """{floor name: canonical geometry of that floor} off the snapshot --
    vertices, walls by their endpoints, rooms by their outline, furnishings."""
    doc = win.snapshot()
    name = {L["id"]: L["name"] for L in doc["levels"]}
    vx = {v["id"]: (round(v["x"], 4), round(v["y"], 4)) for v in doc["vertices"]}
    out = {n: {"vertices": [], "walls": [], "rooms": [], "furnishings": []}
           for n in name.values()}
    for v in doc["vertices"]:
        out[name[v["level"]]]["vertices"].append(vx[v["id"]])
    for w in doc["walls"]:
        out[name[w["level"]]]["walls"].append(
            (tuple(sorted((vx[w["v1"]], vx[w["v2"]]))), w.get("type")))
    for r in doc["rooms"]:
        out[name[r["level"]]]["rooms"].append(
            (r.get("name"), tuple(vx[e["v"]] for e in r.get("outline", []))))
    for f in doc.get("furnishings", []):
        out[name[f["level"]]]["furnishings"].append(
            (f.get("kind"), tuple(round(c, 4) for c in f.get("pos", [])),
             round(float(f.get("rotation", 0.0)), 4)))
    return {n: json.dumps({k: sorted(map(repr, v)) for k, v in g.items()},
                          sort_keys=True) for n, g in out.items()}


def fresh(show_others):
    win = fp.MainWindow()
    win.prepare_headless()
    win.load_path(PLAN)
    win.show_other_floors = show_others
    win.switch_floor(UPPER)
    win._sync_floor_state()
    win._commit_if_changed()
    win._reset_undo()
    return win


def by_floor(items):
    out = {}
    for it in items:
        f = getattr(it, "floor", None)
        out[f] = out.get(f, 0) + 1
    return out


def verdict(win, pristine, label):
    now = fingerprint(win)
    print(f"      {label}: floor 1 {'UNCHANGED' if now[LOWER] == pristine[LOWER] else 'MOVED'}, "
          f"floor 2 {'unchanged' if now[UPPER] == pristine[UPPER] else 'moved'}")
    return now


def main():
    # ---- the question under the third bullet: a vertex shared across floors?
    win = fresh(True)
    holders = {}
    for it in win.scene.items():
        if isinstance(it, fp.WallItem):
            for v in (it._v1, it._v2):
                holders.setdefault(id(v), set()).add(it.floor)
    shared = sum(1 for s in holders.values() if len(s) > 1)
    doc = json.load(open(PLAN, encoding="utf-8"))
    pos = {}
    for v in doc["vertices"]:
        pos.setdefault((round(v["x"], 1), round(v["y"], 1)), set()).add(v["level"])
    print(f"vertices: {len(holders)} live Vertex objects; {shared} held by walls of "
          f"two floors; the document has {sum(1 for s in pos.values() if len(s) > 1)} "
          f"positions where a floor-1 and a floor-2 vertex coincide")
    win.close()

    for show in (True, False):
        print(f"\n== second floor active, show other floors = {show} ==")
        # ---- what each selection route picks up
        win = fresh(show)
        pristine = fingerprint(win)
        vis = by_floor(it for it in win.scene.items()
                       if it.isVisible() and hasattr(it, "floor"))
        ena = by_floor(it for it in win.scene.items()
                       if it.isEnabled() and hasattr(it, "floor"))
        print(f"   visible by floor {vis}; enabled by floor {ena}")
        win.view.select_in_rect(BAND)
        print(f"   rubber band over the whole plan selects {by_floor(win.scene.selectedItems())}")
        win.scene.clearSelection()
        win.run_macro("SELECTALL")
        print(f"   select-all selects                       {by_floor(win.scene.selectedItems())}")
        win.scene.clearSelection()
        # a first-floor furnishing's own position: nothing of floor 2 need be there
        f1 = next(it for it in win.scene.items()
                  if isinstance(it, fp.FurnishingItem) and it.floor == LOWER)
        c = f1.sceneBoundingRect().center()
        win.run_macro(f"SELECT {c.x():.0f} {c.y():.0f}")
        print(f"   SELECT on a floor-1 furnishing at ({c.x():.0f},{c.y():.0f}) selects "
              f"{by_floor(win.scene.selectedItems())}")
        win.scene.clearSelection()
        win.run_macro(f"S CLICK {c.x():.0f} {c.y():.0f}")
        print(f"   a mouse click there selects              {by_floor(win.scene.selectedItems())}")
        win.close()

        # ---- HIS GESTURE: band, group, drag -- then undo
        win = fresh(show)
        pristine = fingerprint(win)
        win.view.select_in_rect(BAND)
        n_sel = by_floor(win.scene.selectedItems())
        # THE MECHANISM: `group_selected` adds, for every selected room, its
        # `room_walls` and its `interior_walls()` -- which of those hands
        # it a wall of another floor?
        from floorplanner.rooms import room_walls
        for r in (it for it in win.scene.selectedItems() if isinstance(it, fp.RoomItem)):
            for label, walls in (("room_walls", room_walls(r)),
                                 ("interior_walls", r.interior_walls())):
                for w in walls:
                    if isinstance(w, fp.WallItem) and w.floor != r.floor:
                        print(f"   room '{r.name}' (floor {r.floor}): {label} returns a wall of "
                              f"floor '{w.floor}', ({w.p1.x():.0f},{w.p1.y():.0f})-"
                              f"({w.p2.x():.0f},{w.p2.y():.0f}) {w.wall_type}")
        win.group_selected()
        groups = [it for it in win.scene.items() if isinstance(it, fp.GroupItem)]
        members = by_floor(ch for g in groups for ch in g.childItems())
        print(f"   band {n_sel} -> group: {len(groups)} group(s), members by floor {members}")
        w2 = next(it for it in win.scene.items()
                  if isinstance(it, fp.WallItem) and it.floor == UPPER)
        m = QPointF((w2.p1.x() + w2.p2.x()) / 2, (w2.p1.y() + w2.p2.y()) / 2)
        win.run_macro(f"S CLICK {m.x():.0f} {m.y():.0f} DRAG {m.x() + 60:.0f} {m.y() + 36:.0f}")
        win._commit_if_changed()
        moved = verdict(win, pristine, "after the group drag")
        before, after = json.loads(pristine[LOWER]), json.loads(moved[LOWER])
        for kind in ("vertices", "walls", "rooms", "furnishings"):
            gone = sorted(set(before[kind]) - set(after[kind]))
            came = sorted(set(after[kind]) - set(before[kind]))
            if gone or came:
                print(f"         floor 1 {kind}: {len(gone)} changed")
                for g_, c_ in zip(gone[:2], came[:2], strict=False):
                    print(f"            {g_}  ->  {c_}")
        steps = len(win._undo_stack)
        while win._undo_stack:
            win.undo()
        verdict(win, pristine, f"after undo ({steps} step(s))")
        win.close()

        # ---- a single floor-2 wall standing over a floor-1 wall, dragged
        win = fresh(show)
        pristine = fingerprint(win)
        lower_ends = {(round(it.p1.x(), 1), round(it.p1.y(), 1)) for it in win.scene.items()
                      if isinstance(it, fp.WallItem) and it.floor == LOWER} | \
                     {(round(it.p2.x(), 1), round(it.p2.y(), 1)) for it in win.scene.items()
                      if isinstance(it, fp.WallItem) and it.floor == LOWER}
        over = next((it for it in win.scene.items()
                     if isinstance(it, fp.WallItem) and it.floor == UPPER
                     and (round(it.p1.x(), 1), round(it.p1.y(), 1)) in lower_ends
                     and (round(it.p2.x(), 1), round(it.p2.y(), 1)) in lower_ends), None)
        if over is None:
            print("   (no floor-2 wall has both ends over floor-1 vertices)")
        else:
            m = QPointF((over.p1.x() + over.p2.x()) / 2, (over.p1.y() + over.p2.y()) / 2)
            print(f"   a floor-2 wall with both ends over floor-1 vertices, "
                  f"({over.p1.x():.0f},{over.p1.y():.0f})-({over.p2.x():.0f},{over.p2.y():.0f}), dragged:")
            win.run_macro(f"S CLICK {m.x():.0f} {m.y():.0f} DRAG {m.x() + 48:.0f} {m.y() + 48:.0f}")
            win._commit_if_changed()
            verdict(win, pristine, "after the wall drag")
            steps = len(win._undo_stack)
            while win._undo_stack:
                win.undo()
            verdict(win, pristine, f"after undo ({steps} step(s))")
        win.close()

        # ---- band, then an arrow nudge
        win = fresh(show)
        pristine = fingerprint(win)
        win.view.select_in_rect(BAND)
        win.run_macro("RIGHT RIGHT DOWN")
        win._commit_if_changed()
        print("   band, then three arrow nudges:")
        verdict(win, pristine, "after the nudge")
        steps = len(win._undo_stack)
        while win._undo_stack:
            win.undo()
        verdict(win, pristine, f"after undo ({steps} step(s))")
        win.close()


if __name__ == "__main__":
    main()
