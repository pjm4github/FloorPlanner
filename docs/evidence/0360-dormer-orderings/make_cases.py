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

from floorplanner.annotations import TextAnnotationItem   # noqa: E402
from floorplanner.config import set_floor_state           # noqa: E402
from floorplanner.design.bridge import design_from_scene  # noqa: E402
from floorplanner.items import make_furnishing            # noqa: E402
from floorplanner.model import Floor                      # noqa: E402
from floorplanner.parametric import dormer_geometry as dg  # noqa: E402
from floorplanner.parametric.dormers import DORMER        # noqa: E402
from floorplanner.roofs import RoofItem                   # noqa: E402
from floorplanner.rooms import RoomItem                   # noqa: E402
from floorplanner.walls import WallItem                   # noqa: E402
from PyQt6.QtGui import QPainterPath                       # noqa: E402

# Two levels (Patrick, 2026-11-21): the dormer is a furnishing on the UPPER
# level LV2; the host roof + the house walls are on LV1 a storey below, and the
# dormer finds that host by looking one level down (`host_roof_at`).
LV1, LV2 = "LV1", "LV2"
LV1_ELEV, LV2_ELEV = 0.0, 108.0
# LV2 active so the dormer's own walls draw solid; LV1 shown as a ghost below.
set_floor_state(elevations={LV1: LV1_ELEV, LV2: LV2_ELEV},
                active=LV2, show_others=True)

TABLE = os.path.join(ROOT, "docs", "DORMER_EDGE_ORDERINGS.md")
STAGE1 = ("W01", "W05", "W09", "W75")

# --- base host dimensions (chosen once; sec3) ------------------------------
# A 12:12 gable: slope 1.0, so a plan inch along the fall line is an inch of
# height -- the distances read straight off the surface. The half-span (ridge
# to the eave wall) is 144 in; every buildable distance (<= 120, and D <= 96)
# sits inside it, so the anchor (perp = 144 - D >= 48) stays on the roof. The
# EAVE WALL height is the LV2 floor (108), so the roof bears on the LV1 walls
# and the dormer's own walls rise from the LV2 floor. The plan is 360 in along
# the ridge so the dormer reads large.
EAVES_H = 108.0                # height at the EAVE WALL line (perp = span) = LV2 floor
SPAN = 144.0                   # ridge -> eave wall, plan
RIDGE_H = EAVES_H + SPAN       # 12:12 -> 252
RIDGE_X0, RIDGE_X1 = 0.0, 360.0   # a short ridge so the dormer reads large
RIDGE_Y = 0.0                  # ridge runs along x at y = 0; +y is downhill
DORMER_PITCH = 7.0             # shallower than the host, so the dormer's eaves
#                                stay above the LV2 floor even low on the roof
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


def closest_to_farthest(rb):
    """The ordering string CLOSEST -> farthest (e.g. 'C < B < D < A') from the
    read-back distances, ties joined with '='."""
    uniq = sorted({round(rb[e], 3) for e in "ABCD"})          # ascending = closest
    groups = ["=".join(sorted(e for e in "ABCD" if abs(rb[e] - v) < 1e-6))
              for v in uniq]
    return " < ".join(groups)


# --------------------------------------------------------------------------
# build one case in a bare scene
# --------------------------------------------------------------------------
def _wall(sc, floor, a, b):
    w = WallItem(QPointF(*a), QPointF(*b))
    w.floor = floor
    sc.addItem(w)
    return w


def build_scene(tgt):
    """A scene holding the base house (LV1) + the dormer on LV2 + the dormer's
    own face and cheek walls on LV2. Returns (scene, dormer, overhang,
    anchor_pt, face_pt)."""
    oh = tgt["A"] - tgt["D"]            # host eave overhang, faced side
    depth = tgt["C"]
    fo = tgt["B"] - tgt["C"]
    p_anchor = SPAN - tgt["D"]          # anchor perp from the ridge

    sc = QGraphicsScene()

    # LV1: the room + four exterior walls (the eave walls at perp = span) + the
    # host roof. D (the wall below) is the faced LV1 wall at perp = span.
    x0, x1, y0, y1 = RIDGE_X0, RIDGE_X1, RIDGE_Y - SPAN, RIDGE_Y + SPAN
    path = QPainterPath()
    path.addRect(x0, y0, x1 - x0, y1 - y0)
    room = RoomItem("LV1", QPointF((x0 + x1) / 2.0, (y0 + y1) / 2.0), path, 100.0)
    room.floor = LV1
    room.properties["ceiling_height_in"] = LV2_ELEV - LV1_ELEV
    sc.addItem(room)
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        _wall(sc, LV1, a, b)

    rf = RoofItem(QPointF(RIDGE_X0, RIDGE_Y), QPointF(RIDGE_X1, RIDGE_Y),
                  eaves_h_in=EAVES_H, ridge_h_in=RIDGE_H,
                  overhang_in=[oh, 0.0], span_in=SPAN)
    rf.floor = LV1
    sc.addItem(rf)

    # LV2: the dormer furnishing (its host is the LV1 roof, a storey below).
    st = {"form": "gable", "symmetric": True, "span_left_in": 60.0,
          "span_right_in": 60.0, "pitch_12": DORMER_PITCH, "depth_in": depth,
          "face_overhang_in": fo, "anchored": True}
    ax, ay = (RIDGE_X0 + RIDGE_X1) / 2.0, RIDGE_Y + p_anchor
    d = make_furnishing("dormer", QPointF(ax, ay), 0.0, st, new=False)
    d.floor = LV2
    sc.addItem(d)
    d._recompute()

    ux, uy = dg.ridge_direction(d.rotation())
    face_pt = (ax - ux * depth, ay - uy * depth)

    # LV2: the dormer's OWN walls, drawn to match its face and cheeks (Patrick,
    # 2026-11-21) -- the user's upper-level walls that rise into the gable. The
    # face wall spans the side guides at the face; each cheek runs from the face
    # back along a guide to the anchor.
    gl, gr = dg.guides(d.params)
    def L(xl, yl):
        return tuple(dg.to_plan(face_pt, d.rotation(), (xl, yl)))
    _wall(sc, LV2, L(-gr, 0.0), L(gl, 0.0))            # face wall
    _wall(sc, LV2, L(gl, 0.0), L(gl, depth))           # left cheek
    _wall(sc, LV2, L(-gr, 0.0), L(-gr, depth))         # right cheek

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
    _derived, findings = DORMER.evaluate(d.params, ctx)
    fids = sorted({f.rule_id for f in findings})
    return rb, {"host_z_face": z, "host_slope": s, "host_eave_h": eh,
                "host_ridge_h": hr, "eave_y": eave_y,
                "dormer_ridge_h": dg.ridge_height(d.params),
                "face_class": cls, "findings": fids}


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
def plan_png(wid, sc, d, rb, oh, anchor_pt, face_pt, w=760, h=560):
    TOP = 150                      # a white band at the top for title + legend
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
    # expand to the render area's aspect (below the top band) so it does not
    # letterbox
    ar = w / (h - TOP)
    if src.width() / src.height() < ar:
        nw = src.height() * ar
        src.adjust(-(nw - src.width()) / 2.0, 0, (nw - src.width()) / 2.0, 0)
    else:
        nh = src.width() / ar
        src.adjust(0, -(nh - src.height()) / 2.0, 0, (nh - src.height()) / 2.0)
    scale = w / src.width()

    def px(pt):
        return QPointF((pt[0] - src.left()) * scale,
                       TOP + (pt[1] - src.top()) * scale)

    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(QColor("#ffffff"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    sc.render(p, QRectF(0, TOP, w, h - TOP), src, Qt.AspectRatioMode.IgnoreAspectRatio)

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

    # the top band: the case ID, the ordering CLOSEST -> FARTHEST, and the legend
    close_far = closest_to_farthest(rb)
    lx = 12
    p.setPen(QColor("#000000"))
    ft = QFont(FONT, 16)
    ft.setBold(True)
    p.setFont(ft)
    p.drawText(QPointF(lx, 26), wid)
    p.setFont(QFont(FONT, 12))
    p.drawText(QPointF(lx, 48), f"order, closest -> farthest:   {close_far}")
    ly, lh = 68, 20
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


def write_index(all_rows, results, path):
    """INDEX.md: every one of the 75 rows. Buildable rows carry the four
    read-back distances, the app's face classification and any findings, and a
    link to the PNG; unbuildable rows carry the table's reason and no link. The
    last column, `Patrick's check`, is left EMPTY for him."""
    by_id = {r["id"]: r for r in results if r.get("built")}
    out = [
        "# 0360 dormer edge-orderings — INDEX (all 75 rows)",
        "",
        "Read-back distances (plan inches from the anchor) for every BUILDABLE",
        "row, with the app's own face classification (`dg.classify_face`) and any",
        "findings the dormer raised; unbuildable rows show the table's reason and",
        "no image. Built on the LV2 base design (0361 §2). `Patrick's check` is",
        "left empty for him.",
        "",
        "| ID | Ordering | Build | A | B | C | D | Face (app) | Findings | Image | Patrick's check |",
        "| -- | -------- | ----- | -: | -: | -: | -: | ---------- | -------- | ----- | --------------- |",
    ]
    for r in all_rows:
        wid = r["id"]
        if not r["buildable"]:
            out.append(f"| {wid} | {r['ordering']} | no | | | | | | "
                       f"{r['reason']} | | |")
            continue
        res = by_id.get(wid)
        if res is None:
            out.append(f"| {wid} | {r['ordering']} | yes | | | | | | "
                       f"(not built this run) | | |")
            continue
        rb, host = res["rb"], res["host"]
        fnd = ", ".join(host["findings"]) or "—"
        ok = "" if res["reproduces"] else " ⚠REPRO"
        out.append(f"| {wid} | {r['ordering']}{ok} | yes | {rb['A']:.0f} | "
                   f"{rb['B']:.0f} | {rb['C']:.0f} | {rb['D']:.0f} | "
                   f"{host['face_class']} | {fnd} | [{wid}.png]({wid}.png) | |")
    io_open(path, "\n".join(out) + "\n")


def io_open(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


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
        # render the plan picture FIRST, before the annotations go in, so its
        # top band is the only in-image label; the annotations then ride the json.
        plan_img = plan_png(wid, sc, d, rb, oh, anchor_pt, face_pt)
        # text annotations (kind "text", the T tool) on LV2, so the plan FILE
        # itself carries the case id and the ordering -- not only the review PNG
        # (Patrick, 2026-11-21).
        cf = closest_to_farthest(rb)
        tx = RIDGE_X0 + 20.0
        sc.addItem(TextAnnotationItem(QPointF(tx, RIDGE_Y - SPAN + 30.0),
                                      f"{wid}   {r['ordering']}", 0.0, LV2))
        sc.addItem(TextAnnotationItem(QPointF(tx, RIDGE_Y - SPAN + 54.0),
                                      f"closest -> farthest:  {cf}", 0.0, LV2))
        # save the design json (loadable in the app), with the two levels
        floors = [Floor(name=LV1, elevation_in=LV1_ELEV,
                        height_in=LV2_ELEV - LV1_ELEV),
                  Floor(name=LV2, elevation_in=LV2_ELEV, height_in=96.0)]
        doc = design_from_scene(sc, floors=floors).to_dict()
        doc.setdefault("settings", {})["active_floor"] = LV2
        json_path = os.path.join(HERE, f"{wid}.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        # the 3D view and the composite
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
    # write INDEX.md only when this run covered EVERY buildable row, so a
    # partial run (e.g. one id) never clobbers the full index
    all_rows = parse_table(TABLE)
    buildable = {r["id"] for r in all_rows if r["buildable"]}
    built = {r["id"] for r in results if r.get("built")}
    if buildable <= built:
        write_index(all_rows, results, os.path.join(HERE, "INDEX.md"))
        print(f"wrote INDEX.md ({len(built)} built, "
              f"{len(all_rows) - len(buildable)} unbuildable)")
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
