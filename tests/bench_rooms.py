#!/usr/bin/env python3
"""Micro-benchmark for room re-detection cost (the main editor hot path).

`rebuild_all_walls` -> `refresh_rooms` re-detects every room after any wall
edit.  This builds grids of rooms of growing size and times one
`rebuild_all_walls`, so we can track the cost as plans get larger.

Run:  python tests/bench_rooms.py [--profile]
"""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication, QGraphicsScene

_app = QApplication.instance() or QApplication([])
import FloorPlanner as FP


def build_grid(n, cell=120, off=120):
    """An n x n grid of walled, named rooms on a bare scene."""
    FP.SETTINGS.update(FP.DEFAULT_SETTINGS)
    FP.SETTINGS["canvas_w_in"] = n * cell + 2 * off
    FP.SETTINGS["canvas_h_in"] = n * cell + 2 * off
    sc = QGraphicsScene()
    for r in range(n + 1):
        y = off + r * cell
        sc.addItem(FP.WallItem(QPointF(off, y), QPointF(off + n * cell, y),
                               "interior"))
    for c in range(n + 1):
        x = off + c * cell
        sc.addItem(FP.WallItem(QPointF(x, off), QPointF(x, off + n * cell),
                               "interior"))
    FP.rebuild_all_walls(sc)
    for r in range(n):
        for c in range(n):
            ctr = QPointF(off + c * cell + cell / 2, off + r * cell + cell / 2)
            res = FP.detect_room(sc, ctr)
            if res is not None:
                room = FP.RoomItem(f"R{r}_{c}", ctr, res[0], res[1],
                                   corners=res[2])
                sc.addItem(room)
                FP.bind_room_walls(sc, room, settle=False)
    return sc


def main():
    print("grid  rooms  walls   rebuild_all_walls   per-room")
    for n in (2, 3, 4, 5, 6):
        sc = build_grid(n)
        rooms = sum(1 for it in sc.items() if isinstance(it, FP.RoomItem))
        walls = sum(1 for it in sc.items() if isinstance(it, FP.WallItem))
        t = time.perf_counter()
        FP.rebuild_all_walls(sc)
        dt = (time.perf_counter() - t) * 1000
        print(f"{n}x{n}  {rooms:4d}  {walls:4d}   {dt:8.1f} ms       "
              f"{dt / max(rooms, 1):.2f} ms")

    if "--profile" in sys.argv:
        import cProfile
        import io
        import pstats
        sc = build_grid(6)
        pr = cProfile.Profile()
        pr.enable()
        for _ in range(3):
            FP.rebuild_all_walls(sc)
        pr.disable()
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(10)
        print("\n--- cProfile (3x rebuild on 6x6, by tottime) ---")
        print("\n".join(s.getvalue().splitlines()[:18]))


if __name__ == "__main__":
    main()
