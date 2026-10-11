"""Headless 3D look at a design with Qt's 2D painter -- a stand-in for
`fp3d.py --shot`, which needs a real display (D77). Builds the fp3d model
(Qt-free), projects every triangle orthographically from an azimuth and
elevation, sorts by depth (painter's algorithm) and fills it: walls grey,
roofs brown, lit by face normal; an optional plan window zooms on a corner.

    python render3d.py design.json out.png [azim elev] [x0 x1 y0 y1]
"""
import importlib.util
import json
import math
import os
import pathlib
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF  # noqa: E402
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF, QGuiApplication  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fp3d_render", REPO / "floorplanner" / "viewer" / "fp3d.py")
fp3d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fp3d
spec.loader.exec_module(fp3d)

app = QGuiApplication([])
design, out = sys.argv[1], sys.argv[2]
azim, elev = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (-60.0, 25.0)
window = [float(v) for v in sys.argv[5:9]] if len(sys.argv) > 8 else None

doc = json.loads(pathlib.Path(design).read_text(encoding="utf-8"))
model = fp3d.build_model(doc, furnishings=False, floors=False)

ca, sa = math.cos(math.radians(azim)), math.sin(math.radians(azim))
ce, se = math.cos(math.radians(elev)), math.sin(math.radians(elev))


def project(x, y, z):
    """World (x, y_world = -plan_y, z) -> screen (u, v) and depth d."""
    # rotate about z by azimuth, then tilt by elevation; camera looks along +d
    rx = x * ca - y * sa
    ry = x * sa + y * ca
    u = rx
    v = ry * se + z * ce
    d = -ry * ce + z * se
    return u, v, d


tris = []
for mesh in model.meshes:
    if mesh.name == "roofs":
        base = (205, 133, 63)
    elif mesh.name.startswith("walls"):
        base = (190, 190, 196)
    else:
        continue
    v = mesh.verts
    for tri in mesh.faces:
        pts = [(float(v[i, 0]), float(v[i, 1]), float(v[i, 2])) for i in tri]
        if window and not any(window[0] <= p[0] <= window[1] and -window[3] <= p[1] <= -window[2] for p in pts):
            continue
        (ax_, ay, az), (bx, by, bz), (cx, cy, cz) = pts
        nx, ny, nz = ((by - ay) * (cz - az) - (bz - az) * (cy - ay),
                      (bz - az) * (cx - ax_) - (bx - ax_) * (cz - az),
                      (bx - ax_) * (cy - ay) - (by - ay) * (cx - ax_))
        ln = math.hypot(nx, ny, nz) or 1.0
        light = abs(0.3 * nx + 0.5 * ny + 0.81 * nz) / ln
        shade = 0.55 + 0.45 * light
        proj = [project(*p) for p in pts]
        depth = sum(p[2] for p in proj) / 3.0
        tris.append((depth, [(p[0], p[1]) for p in proj], tuple(int(c * shade) for c in base)))
if not tris:
    sys.exit("nothing in the window")
tris.sort(key=lambda t: t[0])
us = [p[0] for t in tris for p in t[1]]
vs = [p[1] for t in tris for p in t[1]]
W, H = 1400, 1000
margin = 30
sx = (W - 2 * margin) / max(1e-6, max(us) - min(us))
sy = (H - 2 * margin) / max(1e-6, max(vs) - min(vs))
s = min(sx, sy)
img = QImage(W, H, QImage.Format.Format_RGB32)
img.fill(QColor(255, 255, 255))
p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
for _, poly, col in tris:
    qp = QPolygonF([QPointF(margin + (u - min(us)) * s, H - margin - (v - min(vs)) * s) for u, v in poly])
    p.setBrush(QColor(*col))
    p.setPen(QPen(QColor(40, 40, 40, 70), 0.5))
    p.drawPolygon(qp)
p.end()
img.save(out)
print("wrote", out, "tris", len(tris), "notes", model.notes[:3], "info", model.info[:3])
