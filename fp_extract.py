#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Patrick Moran and Claude (Anthropic). See LICENSE.
"""
fp_extract.py -- extract a floor plan from a PNG image.

Detects the horizontal and vertical wall lines in a raster floor-plan image and
writes a FloorPlanner JSON plan you can open in the app (File > Open) or feed to
fp_macro.py.  It reads the PNG with PyQt6's QImage and finds walls with numpy --
no OpenCV/Pillow needed.

Scope / assumptions (v1): clean, **axis-aligned** plans with dark walls on a
light background (architectural line drawings, app screenshots).  It extracts
WALLS; open the result in FloorPlanner to name rooms (the app detects enclosed
areas) and add doors/windows/furniture.  Diagonal walls and photos of plans are
out of scope.

Scale: pixels map to inches via --width-ft (the real width of the drawing) or
--px-per-ft; with neither, the plan is scaled to fit the default canvas.

Examples
  # extract, scaling so the drawing is 40 ft wide, and save a preview
  python fp_extract.py --in plan.png --out plan.json --width-ft 40 --png out.png

  # a plan drawn with double-line walls: merge the two faces (~14 px apart)
  python fp_extract.py --in plan.png --out plan.json --merge 16
"""
import argparse
import json
import os
import sys

import numpy as np

FOOT = 12.0
_APP = None        # keep the QApplication alive for the process lifetime


# ---------------------------------------------------------------------------
# Image -> grayscale numpy array (via QImage, so no Pillow dependency)
# ---------------------------------------------------------------------------
def load_gray(path: str) -> np.ndarray:
    from PyQt6.QtGui import QImage

    img = QImage(path)
    if img.isNull():
        raise ValueError(f"could not read image: {path}")
    img = img.convertToFormat(QImage.Format.Format_Grayscale8)
    w, h = img.width(), img.height()
    bpl = img.bytesPerLine()                       # rows are padded to 4 bytes
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape(h, bpl)
    return arr[:, :w].copy()           # own the data; QImage buffer is freed


# ---------------------------------------------------------------------------
# Wall detection (rectilinear): dark runs per row/column, merged into segments
# ---------------------------------------------------------------------------
class _DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def _row_runs(row: np.ndarray, min_len: int):
    """Inclusive (start, end) pixel spans of consecutive True runs >= min_len."""
    edges = np.flatnonzero(np.diff(np.concatenate(
        ([0], row.view(np.int8), [0]))))
    out = []
    for s, e in zip(edges[0::2], edges[1::2], strict=False):
        if e - s >= min_len:
            out.append((int(s), int(e) - 1))
    return out


def _line_segments(mask: np.ndarray, min_len: int, merge: int,
                   max_thick: int):
    """Find near-horizontal wall segments in `mask` (bool, dark=True).

    Returns list of (x0, x1, cy): each a wall centreline at row cy spanning
    x0..x1.  Runs in rows within `merge` px that overlap in x are merged (this
    bridges anti-aliasing and, with a larger `merge`, the two faces of a
    double-line wall).  Groups thicker than `max_thick` px are dropped (filled
    blocks, hatching)."""
    items = []                                     # (y, x0, x1)
    for y in range(mask.shape[0]):
        for x0, x1 in _row_runs(mask[y], min_len):
            items.append((y, x0, x1))
    if not items:
        return []
    # bucket runs by row so we only compare runs in nearby rows
    by_row = {}
    for i, (y, _x0, _x1) in enumerate(items):
        by_row.setdefault(y, []).append(i)
    dsu = _DSU(len(items))
    for i, (y, x0, x1) in enumerate(items):
        for dy in range(1, merge + 1):
            for j in by_row.get(y + dy, []):
                _yj, xj0, xj1 = items[j]
                if min(x1, xj1) >= max(x0, xj0):   # overlap in x
                    dsu.union(i, j)
    groups = {}
    for i, (y, x0, x1) in enumerate(items):
        groups.setdefault(dsu.find(i), []).append((y, x0, x1))
    segs = []
    for g in groups.values():
        ys = [y for y, _a, _b in g]
        x0 = min(a for _y, a, _b in g)
        x1 = max(b for _y, _a, b in g)
        if max(ys) - min(ys) + 1 > max_thick:
            continue
        if x1 - x0 < min_len:
            continue
        segs.append((x0, x1, (min(ys) + max(ys)) // 2))
    return segs


def detect_walls(gray: np.ndarray, threshold: int, min_len: int,
                 merge: int, max_thick: int):
    """Detect axis-aligned walls.  Returns list of (x0, y0, x1, y1) in pixels."""
    mask = gray < threshold
    walls = []
    for x0, x1, cy in _line_segments(mask, min_len, merge, max_thick):
        walls.append((x0, cy, x1, cy))            # horizontal
    for y0, y1, cx in _line_segments(mask.T, min_len, merge, max_thick):
        walls.append((cx, y0, cx, y1))            # vertical (transposed back)
    return walls


# ---------------------------------------------------------------------------
# Scale pixels -> inches and build a plan with the app
# ---------------------------------------------------------------------------
def scale_in_per_px(walls, img_w, img_h, width_ft=None, px_per_ft=None):
    """Inches-per-pixel from --px-per-ft, --width-ft, or (default) fit to the
    canvas."""
    if px_per_ft:
        return FOOT / px_per_ft
    xs = [c for x0, y0, x1, y1 in walls for c in (x0, x1)] or [0, img_w]
    ys = [c for x0, y0, x1, y1 in walls for c in (y0, y1)] or [0, img_h]
    span_x = (max(xs) - min(xs)) or img_w or 1
    span_y = (max(ys) - min(ys)) or img_h or 1
    if width_ft:
        return (width_ft * FOOT) / span_x
    # default: fit the content into ~90% of the default canvas
    from FloorPlanner import CANVAS_H_DEFAULT, CANVAS_W_DEFAULT
    return min(CANVAS_W_DEFAULT * 0.9 / span_x,
               CANVAS_H_DEFAULT * 0.9 / span_y)


def scene_segments(walls, img_w, img_h, *, width_ft=None, px_per_ft=None,
                   snap_in=3.0, margin_in=24.0, min_wall_in=12.0):
    """Convert pixel wall segments to scene-inch (x0, y0, x1, y1) tuples:
    scaled, shifted to a margin from the origin, and snapped to a grid.  Shared
    by build_plan() and the GUI's File > Import from image."""
    if not walls:
        return []
    s = scale_in_per_px(walls, img_w, img_h, width_ft, px_per_ft)
    minx = min(c for x0, y0, x1, y1 in walls for c in (x0, x1))
    miny = min(c for x0, y0, x1, y1 in walls for c in (y0, y1))

    def to_scene(px, py):
        return (round(((px - minx) * s + margin_in) / snap_in) * snap_in,
                round(((py - miny) * s + margin_in) / snap_in) * snap_in)

    out = []
    for x0, y0, x1, y1 in walls:
        ax, ay = to_scene(x0, y0)
        bx, by = to_scene(x1, y1)
        if abs(ax - bx) + abs(ay - by) >= min_wall_in:
            out.append((ax, ay, bx, by))
    return out


def setup_app():
    """Create the offscreen QApplication and return the FloorPlanner module.
    Must run before load_gray() -- QImage needs the app's image plugins to
    decode a PNG."""
    global _APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication

    _APP = QApplication.instance() or QApplication(sys.argv[:1])
    import FloorPlanner as FP

    if FP.FONT_DIR.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(FP.FONT_DIR))
    _APP.setApplicationName(FP.APP_NAME)
    FP.load_fonts()
    _APP.setFont(QFont(FP.FONT_FAMILY, 10))
    return FP


def build_plan(FP, walls, img_w, img_h, *, width_ft=None, px_per_ft=None,
               wall_type="exterior", snap_in=3.0, margin_in=24.0,
               min_wall_in=12.0):
    """Lay the scaled walls into a FloorPlanner scene and return the
    (MainWindow, summary dict).  `setup_app()` must have been called first."""
    from PyQt6.QtCore import QPointF

    segs = scene_segments(walls, img_w, img_h, width_ft=width_ft,
                          px_per_ft=px_per_ft, snap_in=snap_in,
                          margin_in=margin_in, min_wall_in=min_wall_in)
    win = FP.MainWindow()
    for x0, y0, x1, y1 in segs:
        win.scene.addItem(
            FP.WallItem(QPointF(x0, y0), QPointF(x1, y1), wall_type))
    FP.rebuild_all_walls(win.scene)
    win._update_totals()
    win._commit_if_changed()
    return win, {"scale_in_per_px": scale_in_per_px(
        walls, img_w, img_h, width_ft, px_per_ft), "walls": len(segs)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="fp_extract.py",
        description="Extract a (rectilinear) floor plan from a PNG image.")
    ap.add_argument("-i", "--in", dest="infile", required=True,
                    help="input PNG (dark walls on a light background)")
    ap.add_argument("-o", "--out", dest="outfile",
                    help="FloorPlanner JSON to write")
    ap.add_argument("--png", help="write a preview PNG of the extracted plan")
    ap.add_argument("--width-ft", type=float,
                    help="real width of the drawing in feet (sets the scale)")
    ap.add_argument("--px-per-ft", type=float,
                    help="scale as pixels per foot (overrides --width-ft)")
    ap.add_argument("--threshold", type=int, default=128,
                    help="pixels darker than this are walls (0-255, def 128)")
    ap.add_argument("--min-wall-px", type=int, default=24,
                    help="ignore wall lines shorter than this many px (def 24)")
    ap.add_argument("--merge", type=int, default=3,
                    help="merge parallel wall lines within N px into one "
                         "centreline; raise to ~the wall thickness to collapse "
                         "double-line walls (def 3)")
    ap.add_argument("--max-thick-px", type=int, default=40,
                    help="drop dark blocks thicker than this many px (def 40)")
    ap.add_argument("--wall-type", choices=["exterior", "interior"],
                    default="exterior", help="type for extracted walls")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="suppress the JSON summary on stdout")
    args = ap.parse_args(argv)

    result = {"ok": True, "input": args.infile, "saved": None,
              "preview": None, "errors": []}
    try:
        FP = setup_app()                           # before load_gray (plugins)
        gray = load_gray(args.infile)
        h, w = gray.shape
        walls = detect_walls(gray, args.threshold, args.min_wall_px,
                             args.merge, args.max_thick_px)
        win, info = build_plan(
            FP, walls, w, h, width_ft=args.width_ft, px_per_ft=args.px_per_ft,
            wall_type=args.wall_type)
        result.update(info)
        result["image_size_px"] = [w, h]
        if args.outfile:
            win.save_path(args.outfile)
            result["saved"] = args.outfile
        if args.png:
            win.export_canvas(args.png)
            result["preview"] = args.png
        result["counts"] = win.scene_summary()["counts"]
    except Exception as ex:                               # noqa: BLE001
        result["ok"] = False
        result["errors"].append(f"{type(ex).__name__}: {ex}")

    if not args.quiet:
        print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
