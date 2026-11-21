#!/usr/bin/env python
"""0360 stage 1 -- one example design + one review image per BUILDABLE row.

Evidence only (0360-ruling.md). NO product code lives here: it drives the
same `floorplanner` geometry the app uses and draws the A/B/C/D marks on the
captured images. Deterministic and re-runnable (stage 3 reuses it).

The case list is READ from docs/DORMER_EDGE_ORDERINGS.md (ID, ordering,
Buildable) -- this script carries no copy of the cases.

The four plan edges that position a dormer on its host roof, measured in plan
from the dormer ANCHOR (apex) toward the face, all positive:

    A  host roof eave (the fascia, overhang past the wall below)
    B  dormer eave over the dormer face
    C  dormer face wall
    D  wall on the level below, which the host roof sits on

Base design (same every case, 0360-ruling.md sec3): ONE level LV1, a plain
rectangular plan, ONE 12:12 gable roof on it (the host), ONE symmetric gable
dormer square to the host eave. Only the four distances change per case.

Usage:  python make_cases.py [--all | Wnn Wnn ...]
        (no args = the four stage-1 cases W01 W05 W09 W75)
"""
import json
import os
import re
import subprocess
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

import FloorPlanner  # noqa: E402
# the bundled repo font (assets/fonts) -- point the offscreen engine at it
# BEFORE QApplication, then register it, so labels render as real glyphs.
os.environ.setdefault("QT_QPA_FONTDIR", str(FloorPlanner.FONT_DIR))

from PyQt6.QtCore import QPointF, QRectF, Qt           # noqa: E402
from PyQt6.QtGui import (QColor, QFont, QImage, QPainter,  # noqa: E402
                         QPen)
from PyQt6.QtWidgets import QApplication, QGraphicsScene   # noqa: E402

_app = QApplication.instance() or QApplication([])
FloorPlanner.load_fonts()
_app.setFont(QFont(FloorPlanner.FONT_FAMILY, 10))
FONT = FloorPlanner.FONT_FAMILY

from floorplanner.config import DEFAULT_FLOOR             # noqa: E402
from floorplanner.design.bridge import design_from_scene  # noqa: E402
from floorplanner.items import make_furnishing            # noqa: E402
from floorplanner.parametric import dormer_geometry as dg  # noqa: E402
from floorplanner.roofs import RoofItem                   # noqa: E402
from floorplanner.rooms import RoomItem                   # noqa: E402
from floorplanner.walls import WallItem                   # noqa: E402
from PyQt6.QtGui import QPainterPath                       # noqa: E402

TABLE = os.path.join(ROOT, "docs", "DORMER_EDGE_ORDERINGS.md")
STAGE1 = ("W01", "W05", "W09", "W75")

# --- base host dimensions (chosen once; sec3) ------------------------------
# A 12:12 gable: slope 1.0, so a plan inch along the fall line is an inch of
# height -- the distances read straight off the surface. The half-span (ridge
# to the eave wall) is 192 in; every stage-1 distance (<= 120) and anchor
# (>= 72 in below the ridge) sits well inside it, and the ridge (288 in) clears
# every dormer ridge. The plan is 600 in along the ridge.
EAVES_H = 96.0                 # height at the EAVE WALL line (perp = span)
SPAN = 192.0                   # ridge -> eave wall, plan
RIDGE_H = EAVES_H + SPAN       # 12:12
RIDGE_X0, RIDGE_X1 = 0.0, 360.0   # a short ridge so the dormer reads large
RIDGE_Y = 0.0                  # ridge runs along x at y = 0; +y is downhill
CEIL = 96.0

# distance ladder (sec4): tied edges EXACTLY equal, separated edges >= 12 in.
CLOSE, STEP = 48.0, 24.0       # closest group = 48, each step out = +24

EDGE_COLOR = {"A": "#d62728", "B": "#1f77b4", "C": "#2ca02c", "D": "#ff7f0e"}
EDGE_NAME = {"A": "A host eave", "B": "B dormer eave",
             "C": "C face wall", "D": "D LV1 wall"}


def parse_table(path):
    """[{id, ordering, buildable, reason}] from the markdown table."""
    rows = []
    for ln in open(path, encoding="utf-8"):
        m = re.match(r"\|\s*(W\d\d)\s*\|\s*([^|]+?)\s*\|\s*(yes|no)\s*\|\s*([^|]*)\|",
                     ln)
        if m:
            rows.append({"id": m.group(1), "ordering": m.group(2).strip(),
                         "buildable": m.group(3) == "yes",
                         "reason": m.group(4).strip()})
    return rows


def distances(ordering):
    """{edge: plan distance from the anchor} from an ordering string such as
    'A > B > C > D' or 'A=B > C=D'. Farthest group first."""
    groups = [g.strip() for g in ordering.split(">")]
    n = len(groups)
    d = {}
    for i, g in enumerate(groups):
        val = CLOSE + (n - 1 - i) * STEP
        for edge in g.split("="):
            d[edge.strip()] = val
    return d


# --------------------------------------------------------------------------
# build one case in a bare scene
# --------------------------------------------------------------------------
def build_scene(tgt):
    """A scene holding the base house + the dormer for target distances `tgt`.
    Returns (scene, dormer, overhang, anchor_pt, face_pt)."""
    oh = tgt["A"] - tgt["D"]            # host eave overhang, faced side
    depth = tgt["C"]
    fo = tgt["B"] - tgt["C"]
    p_anchor = SPAN - tgt["D"]          # anchor perp from the ridge

    sc = QGraphicsScene()

    # the LV1 room + its four exterior walls (the eave walls at perp = span)
    x0, x1, y0, y1 = RIDGE_X0, RIDGE_X1, RIDGE_Y - SPAN, RIDGE_Y + SPAN
    path = QPainterPath()
    path.addRect(x0, y0, x1 - x0, y1 - y0)
    room = RoomItem("LV1", QPointF((x0 + x1) / 2.0, (y0 + y1) / 2.0), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = CEIL
    sc.addItem(room)
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        w = WallItem(QPointF(*a), QPointF(*b))
        w.floor = DEFAULT_FLOOR
        sc.addItem(w)

    rf = RoofItem(QPointF(RIDGE_X0, RIDGE_Y), QPointF(RIDGE_X1, RIDGE_Y),
                  eaves_h_in=EAVES_H, ridge_h_in=RIDGE_H,
                  overhang_in=[oh, 0.0], span_in=SPAN)
    rf.floor = DEFAULT_FLOOR
    sc.addItem(rf)

    st = {"form": "gable", "symmetric": True, "span_left_in": 60.0,
          "span_right_in": 60.0, "pitch_12": 10.0, "depth_in": depth,
          "face_overhang_in": fo, "anchored": True}
    ax, ay = (RIDGE_X0 + RIDGE_X1) / 2.0, RIDGE_Y + p_anchor
    d = make_furnishing("dormer", QPointF(ax, ay), 0.0, st, new=False)
    d.floor = DEFAULT_FLOOR
    sc.addItem(d)
    d._recompute()

    ux, uy = dg.ridge_direction(d.rotation())
    face_pt = (ax - ux * depth, ay - uy * depth)
    return sc, d, oh, (ax, ay), face_pt


def readback(d, oh):
    """The four distances read back from the built dormer, plus the host
    numbers and the app's face classification."""
    ctx = d.param_context()
    z, s = ctx["host_z_face_in"], ctx["host_slope"]
    eh, hr = ctx["host_eave_in"], ctx["host_ridge_in"]
    ext = dg.host_extent(z, s, hr, eh)
    eave_y = ext["eave_y"]
    depth, fo = d.params["depth_in"], d.params["face_overhang_in"]
    dD = depth - eave_y
    rb = {"A": dD + oh, "B": depth + fo, "C": depth, "D": dD}
    cls, _ok = dg.classify_face(d.params, z, s, eh)
    return rb, {"host_z_face": z, "host_slope": s, "host_eave_h": eh,
                "host_ridge_h": hr, "eave_y": eave_y,
                "dormer_ridge_h": dg.ridge_height(d.params),
                "face_class": cls}


def relations(rb):
    def rel(a, b):
        return "=" if abs(rb[a] - rb[b]) < 1e-6 else (">" if rb[a] > rb[b] else "<")
    return {f"{a}v{b}": rel(a, b) for a, b in
            (("A", "B"), ("A", "C"), ("A", "D"),
             ("B", "C"), ("B", "D"), ("C", "D"))}


def ordering_from_rb(rb):
    """The ordering string the read-back distances actually produce."""
    uniq = sorted({round(v, 3) for v in rb.values()}, reverse=True)
    groups = ["=".join(sorted(e for e in "ABCD" if abs(rb[e] - v) < 1e-6))
              for v in uniq]
    return " > ".join(groups)


# --------------------------------------------------------------------------
# the plan picture (scene render + the A/B/C/D overlay)
# --------------------------------------------------------------------------
def plan_png(sc, d, rb, oh, anchor_pt, face_pt, w=760, h=560):
    fx, fy = face_pt
    ax, ay = anchor_pt
    # local y of each edge in dg's FACE frame (+y uphill toward the anchor)
    eave_y = d.params["depth_in"] - rb["D"]
    local_y = {"C": 0.0, "B": -d.params["face_overhang_in"],
               "D": eave_y, "A": eave_y - oh}
    xext = d.params["span_left_in"] + d.params["eave_overhang_left_in"] + 24.0

    def to_plan(xl, yl):                       # dg FACE-frame local -> plan
        return dg.to_plan((fx, fy), d.rotation(), (xl, yl))

    # content bounds: the house + every mark
    pts = [(RIDGE_X0, RIDGE_Y - SPAN - oh), (RIDGE_X1, RIDGE_Y + SPAN + oh)]
    for e in "ABCD":
        pts.append(to_plan(-xext, local_y[e]))
        pts.append(to_plan(xext, local_y[e]))
    pts.append((ax, ay))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    M = 36.0                                   # a margin so nothing hugs the edge
    src = QRectF(min(xs) - M, min(ys) - M,
                 (max(xs) - min(xs)) + 2 * M, (max(ys) - min(ys)) + 2 * M)
    # expand to the image aspect so the render does not letterbox
    ar = w / h
    if src.width() / src.height() < ar:
        nw = src.height() * ar
        src.adjust(-(nw - src.width()) / 2.0, 0, (nw - src.width()) / 2.0, 0)
    else:
        nh = src.width() / ar
        src.adjust(0, -(nh - src.height()) / 2.0, 0, (nh - src.height()) / 2.0)
    scale = w / src.width()

    def px(pt):
        return QPointF((pt[0] - src.left()) * scale, (pt[1] - src.top()) * scale)

    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(QColor("#ffffff"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    sc.render(p, QRectF(0, 0, w, h), src, Qt.AspectRatioMode.IgnoreAspectRatio)

    # a dashed fall-line from the anchor through the marks, so the distances read
    ap = px((ax, ay))
    tail = px(to_plan(0.0, local_y["A"]))
    p.setPen(QPen(QColor("#888888"), 1, Qt.PenStyle.DashLine))
    p.drawLine(ap, tail)

    # the four edges: a line across the dormer, a bold letter at its left end
    fb = QFont(FONT, 13)
    fb.setBold(True)
    for e in "ABCD":
        col = QColor(EDGE_COLOR[e])
        p.setPen(QPen(col, 3))
        a = px(to_plan(-xext, local_y[e]))
        b = px(to_plan(xext, local_y[e]))
        p.drawLine(a, b)
        p.setFont(fb)
        p.drawText(QPointF(a.x() - 16, a.y() + 5), e)

    # the anchor
    p.setPen(QPen(QColor("#000000"), 2))
    p.setBrush(QColor("#000000"))
    p.drawEllipse(ap, 4, 4)
    p.setFont(QFont(FONT, 11))
    p.drawText(QPointF(ap.x() + 8, ap.y() - 6), "anchor")

    # a legend: edge name + distance from the anchor, color-keyed
    lx, ly, lh = 12, 14, 22
    p.fillRect(QRectF(4, 2, 220, 4 * lh + 6), QColor(255, 255, 255, 220))
    p.setFont(QFont(FONT, 12))
    for i, e in enumerate("DCBA"):          # closest to farthest
        yy = ly + i * lh
        p.setPen(QPen(QColor(EDGE_COLOR[e]), 4))
        p.drawLine(QPointF(lx, yy), QPointF(lx + 22, yy))
        p.setPen(QColor("#000000"))
        p.drawText(QPointF(lx + 30, yy + 5), f"{EDGE_NAME[e]} = {rb[e]:.0f}\"")
    p.end()
    return img


def shot_3d(json_path, out_png):
    """The whole-house 3D via fp3dq --shot, in its own process, looking at the
    DORMER (faced, +y plan) side so the face, its eave, the host eave and the
    LV1 wall read together -- yaw 25 puts the camera in front of the face (plan
    +y is world -y), not behind the ridge."""
    env = dict(os.environ)
    env.pop("QT_QPA_PLATFORM", None)           # fp3dq needs the real platform
    try:
        r = subprocess.run(
            [sys.executable, "-m", "floorplanner.viewer.fp3dq", json_path,
             "--shot", out_png, "--yaw", "25", "--pitch", "-14",
             "--zoom", "1.5", "--fov", "55", "--shot-delay", "1500"],
            capture_output=True, text=True, timeout=90, env=env)
    except subprocess.TimeoutExpired:
        return False, "fp3dq timed out"
    if not os.path.exists(out_png):
        return False, f"fp3dq wrote no file (exit {r.returncode}): {r.stderr[-200:]}"
    return True, ""


def caption_png(wid, ordering, rb, w=760, h=96):
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(QColor("#f4f4f4"))
    p = QPainter(img)
    p.setPen(QColor("#000000"))
    ft = QFont(FONT, 16)
    ft.setBold(True)
    p.setFont(ft)
    p.drawText(QPointF(16, 34), f"{wid}    {ordering}")
    p.setFont(QFont(FONT, 13))
    nums = "   ".join(f"{e}={rb[e]:.0f}\"" for e in "ABCD")
    p.drawText(QPointF(16, 70), nums)
    p.end()
    return img


def compose(plan_img, d3_img, cap_img, out_png):
    w = plan_img.width()
    h3 = d3_img.height() if d3_img is not None else 0
    total_h = plan_img.height() + h3 + cap_img.height()
    img = QImage(w, total_h, QImage.Format.Format_RGB32)
    img.fill(QColor("#ffffff"))
    p = QPainter(img)
    y = 0
    p.drawImage(0, y, plan_img)
    y += plan_img.height()
    if d3_img is not None:
        p.drawImage(0, y, d3_img.scaledToWidth(w))
        y += h3
    p.drawImage(0, y, cap_img)
    p.end()
    img.save(out_png)


def run(ids):
    rows = {r["id"]: r for r in parse_table(TABLE)}
    results = []
    for wid in ids:
        r = rows[wid]
        if not r["buildable"]:
            print(f"{wid}: unbuildable ({r['reason']}) -- not built")
            results.append({**r, "built": False})
            continue
        tgt = distances(r["ordering"])
        sc, d, oh, anchor_pt, face_pt = build_scene(tgt)
        rb, host = readback(d, oh)
        got = ordering_from_rb(rb)
        ok = (got.replace(" ", "") == r["ordering"].replace(" ", ""))
        # save the design json (loadable in the app)
        doc = design_from_scene(sc).to_dict()
        json_path = os.path.join(HERE, f"{wid}.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        # the picture
        plan_img = plan_png(sc, d, rb, oh, anchor_pt, face_pt)
        d3_png = os.path.join(HERE, f"{wid}_3d.png")
        okd, msg = shot_3d(json_path, d3_png)
        d3_img = QImage(d3_png) if okd else None
        cap = caption_png(wid, r["ordering"], rb)
        compose(plan_img, d3_img, cap, os.path.join(HERE, f"{wid}.png"))
        if os.path.exists(d3_png):           # intermediate; the composite keeps it
            os.remove(d3_png)
        d3note = "" if okd else f"  [3D FAILED: {msg}]"
        print(f"{wid}: {r['ordering']}  readback={got}  reproduces={ok}  "
              f"face={host['face_class']}{d3note}")
        print(f"     A={rb['A']:.0f} B={rb['B']:.0f} C={rb['C']:.0f} "
              f"D={rb['D']:.0f}  oh={oh:.0f} FO={rb['B']-rb['C']:.0f}  "
              f"host z_face={host['host_z_face']:.0f} slope={host['host_slope']:.2f}")
        results.append({**r, "built": True, "rb": rb, "host": host,
                        "reproduces": ok, "got": got})
    return results


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--all"]:
        rows = parse_table(TABLE)
        ids = [r["id"] for r in rows if r["buildable"]]
    elif args:
        ids = args
    else:
        ids = list(STAGE1)
    run(ids)
