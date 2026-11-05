"""P1 (0297 §2 / 0293 §5 P1) receipts on the wiscaway R-file (L2 height 96).

Instruments `_wall_under_roofs` to log each wall piece's level, plan centroid,
z_hi and built-top, and derives:
  * L2 climbs (pieces built above their own top): 0 -> N
  * DOUBLED: L1 pieces that reach ABOVE L2's base where an L2 piece shares their
    plan position (L1 wall material in L2's space) -> 0
  * highest L1 top under an L2 piece -> <= L2 base
  * the 8048 L2 gable window is a VOID (ray across the wall thickness).

Run:  PYTHONPATH=. .venv/Scripts/python.exe docs/evidence/p1-stacked-climb/receipts.py fixtures/incoming/wiscawayL2-fix.json
"""
import importlib.util
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import numpy as np  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])

from pathlib import Path  # noqa: E402

root = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("fp3d_p1", root / "floorplanner" / "viewer" / "fp3d.py")
fp3d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fp3d
spec.loader.exec_module(fp3d)

doc = json.load(open(sys.argv[1]))
lv = {level["id"]: level for level in doc.get("levels", [])}
base = {k: float(v.get("elevation_in", 0.0)) for k, v in lv.items()}
L2_BASE = base.get("L2", 0.0)

rec = []
orig = fp3d._wall_under_roofs
import inspect  # noqa: E402
_ACCEPTS_ABOVE = "storey_above" in inspect.signature(orig).parameters


def wrap(corners_xy, z_lo, z_hi, terr, z_base, roofclip_mod, t,
         to_top=False, level=None, gable_dir=None, storey_above=None, **kw):
    pos = [corners_xy, z_lo, z_hi, terr, z_base, roofclip_mod, t, to_top, level, gable_dir]
    if _ACCEPTS_ABOVE:          # pre-P1 fp3d has no storey_above parameter
        pos.append(storey_above)
    parts = orig(*pos, **kw)
    cx = sum(x for x, _ in corners_xy) / len(corners_xy)
    cy = sum(y for _, y in corners_xy) / len(corners_xy)
    built = float(z_hi)
    for part in parts:
        v = np.asarray(part[0] if isinstance(part, tuple) else part.verts)
        if len(v):
            built = max(built, float(v[:, 2].max()))
    rec.append((level, cx, cy, float(z_hi), built))
    return parts


fp3d._wall_under_roofs = wrap
model = fp3d.build_model(doc, furnishings=False, floors=False)
fp3d._wall_under_roofs = orig


def climbs(lid):
    return [r for r in rec if r[0] == lid and r[4] > r[3] + 0.6]


def near(a, b):
    return abs(a[1] - b[1]) < 3.0 and abs(a[2] - b[2]) < 3.0


L1 = [r for r in rec if r[0] == "L1"]
L2 = [r for r in rec if r[0] == "L2"]
under = [r for r in L1 if any(near(r, s) for s in L2)]
doubled = [r for r in under if r[4] > L2_BASE + 0.6]
print("L2 climbs (0 -> N): %d" % len(climbs("L2")))
print("DOUBLED (L1 above L2 base where an L2 piece shares its plan): %d" % len(doubled))
print("highest L1 top under an L2 piece: %.1f   (L2 base %.1f)"
      % (max((r[4] for r in under), default=0.0), L2_BASE))

# the 8048 L2 gable window: a ray across the wall thickness (world y) through
# its centre must meet no triangle -- a void. w102 at plan (325..405, 864),
# sill L2_base+36, so z in (L2_base+36, L2_base+84); world y = -plan y.
ext = next(m for m in model.meshes if m.name == "walls:exterior")
verts, faces = ext.verts, ext.faces
zc = L2_BASE + 60.0
a = np.array([365.0, -864.0 - 12.0, zc])
b = np.array([365.0, -864.0 + 12.0, zc])
d = b - a
v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
e1, e2 = v1 - v0, v2 - v0
pv = np.cross(d, e2)
det = np.einsum("ij,ij->i", e1, pv)
ok = np.abs(det) > 1e-12
inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
tv = a - v0
u = np.einsum("ij,ij->i", tv, pv) * inv
q = np.cross(tv, e1)
ww = np.einsum("j,ij->i", d, q) * inv
tt = np.einsum("ij,ij->i", e2, q) * inv
hit = ok & (u >= -1e-9) & (ww >= -1e-9) & (u + ww <= 1 + 1e-9) & (tt >= 0) & (tt <= 1)
print("8048 window hits (0 = a void): %d" % int(hit.sum()))
