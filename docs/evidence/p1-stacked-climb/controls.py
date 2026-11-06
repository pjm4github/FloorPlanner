"""P1 positive controls (0293 §5 P1):
  * dormer-test.json (one level, no storey above) builds byte-identical -- a
    fingerprint of every mesh's verts/faces, to compare BEFORE vs AFTER.
  * little-dormer-test.json: the gable pieces at x~60 and x~600 keep 235.5"
    UNLESS an L2 wall or room stands over them (then they stop at L2's base).

Run on P1 and on a stash of pre-P1 fp3d; the fingerprints must match for
dormer-test, and the gable report says which gables are bounded.
"""
import hashlib
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
spec = importlib.util.spec_from_file_location("fp3d_ctl", root / "floorplanner" / "viewer" / "fp3d.py")
fp3d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fp3d
spec.loader.exec_module(fp3d)


def fingerprint(doc):
    model = fp3d.build_model(doc, furnishings=False, floors=True)
    h = hashlib.sha256()
    for m in sorted(model.meshes, key=lambda m: m.name):
        h.update(m.name.encode())
        h.update(np.ascontiguousarray(np.round(m.verts, 4)).tobytes())
        h.update(np.ascontiguousarray(m.faces).tobytes())
    return h.hexdigest()[:16], sum(len(m.verts) for m in model.meshes)


dt = json.load(open(root / "fixtures" / "incoming" / "dormer-test.json"))
fp, nv = fingerprint(dt)
print("dormer-test.json fingerprint=%s  verts=%d" % (fp, nv))

# little-dormer gables: wrap to log each L1 piece's plan x and built-top
rec = []
orig = fp3d._wall_under_roofs
import inspect  # noqa: E402
_ab = "storey_above" in inspect.signature(orig).parameters


def wrap(corners_xy, z_lo, z_hi, terr, z_base, roofclip_mod, t,
         to_top=False, level=None, gable_dir=None, storey_above=None, **kw):
    pos = [corners_xy, z_lo, z_hi, terr, z_base, roofclip_mod, t, to_top, level, gable_dir]
    if _ab:
        pos.append(storey_above)
    parts = orig(*pos, **kw)
    cx = sum(x for x, _ in corners_xy) / len(corners_xy)
    built = float(z_hi)
    for part in parts:
        v = np.asarray(part[0] if isinstance(part, tuple) else part.verts)
        if len(v):
            built = max(built, float(v[:, 2].max()))
    rec.append((level, cx, built))
    return parts


fp3d._wall_under_roofs = wrap
fp3d.build_model(json.load(open(root / "fixtures" / "incoming" / "little-dormer-test.json")),
                 furnishings=False, floors=False)
fp3d._wall_under_roofs = orig
for xref in (60.0, 600.0):
    tops = [r[2] for r in rec if r[0] == "L1" and abs(r[1] - xref) < 30.0]
    print("little-dormer L1 gable at x~%.0f: highest built-top=%.1f  (pieces=%d)"
          % (xref, max(tops, default=0.0), len(tops)))
