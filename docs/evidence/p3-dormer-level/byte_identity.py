"""P3 (0293 §3): promoting a dormer -- an edit of its drawn `level` alone --
leaves `build_model` BYTE-IDENTICAL, because 3D reads the HOST's base, never the
dormer's level (0293 §2c). Promotes the dormer (host roof) from its level to the
one above and compares every mesh.

Run:  PYTHONPATH=. .venv/Scripts/python.exe docs/evidence/p3-dormer-level/byte_identity.py fixtures/incoming/little-dormer-test.json
"""
import copy
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
spec = importlib.util.spec_from_file_location("fp3d_p3e", root / "floorplanner" / "viewer" / "fp3d.py")
fp3d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fp3d
spec.loader.exec_module(fp3d)

doc = json.load(open(sys.argv[1]))
levels = {level["id"]: float(level.get("elevation_in", 0.0)) for level in doc.get("levels", [])}


def fingerprint(d):
    model = fp3d.build_model(d, furnishings=False, floors=True)
    h = hashlib.sha256()
    for mesh in sorted(model.meshes, key=lambda m: m.name):
        h.update(mesh.name.encode())
        h.update(np.ascontiguousarray(np.round(mesh.verts, 4)).tobytes())
        h.update(np.ascontiguousarray(mesh.faces).tobytes())
    return h.hexdigest()[:16]


rf = next(r for r in doc["roofs"] if r.get("host"))
above = min((e for e in levels.values() if e > levels[rf["level"]] + 1e-6), default=None)
to = next(k for k, e in levels.items() if e == above) if above is not None else rf["level"]
f1 = fingerprint(doc)
promoted = copy.deepcopy(doc)
next(r for r in promoted["roofs"] if r.get("host"))["level"] = to
f2 = fingerprint(promoted)
print("dormer %s: level %s -> %s" % (rf["id"], rf["level"], to))
print("build_model before:", f1)
print("build_model after: ", f2)
print("BYTE-IDENTICAL:", f1 == f2)
