"""D74's own lesson, applied to the shower-identity check itself (handoff
0034-ruling.md SS2): the fixture's camera fits the WHOLE MODEL (a 348in x
138in room, walls included), which is not the distance a person actually
works at when looking at three fixtures inside it. `fp3d.py`'s CLI has no
camera-distance flag -- `make_view()` always fits the whole model -- so this
script builds the view the normal way and then re-points the camera at the
FURNISHINGS' own bounding box instead of the room's.

    python docs/evidence/shower_glance_working_distance.py

Writes `shower-glance-working-distance-after.png` beside this file, against
whatever artwork is currently checked out -- run it again after any future
redraw of these three symbols for a fresh after-shot at the SAME camera.
`shower-glance-working-distance-before.png` is the one-time companion,
rendered once against the pre-redraw artwork (`git show
main:assets/furnishings/{shower,walk_in_shower,glass_shower}.svg`, copied
over the working tree, rendered, then `git checkout --` to restore) and
committed as a fixed historical reference; it is not reproduced by this
script and does not need to be.

Run standalone, directly, not from inside another script -- GL rendering
needs a real display, not QT_QPA_PLATFORM=offscreen (D77/D78's own finding:
offscreen cannot create a GL context on this machine, and `--shot` would
silently write nothing while still printing success).
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PLAN = ROOT / "fixtures" / "shower-glance-check.json"


def load_fp3d():
    spec = importlib.util.spec_from_file_location(
        "fp3d_working_distance", ROOT / "floorplanner" / "viewer" / "fp3d.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    fp3d = load_fp3d()
    doc = json.loads(PLAN.read_text("utf-8"))
    model = fp3d.build_model(doc)

    furn = [m for m in model.meshes if m.name.startswith("furnishings:")]
    assert furn, "no furnishing meshes -- is this still the right fixture?"
    import numpy as np
    fv = np.vstack([m.verts for m in furn])
    flo, fhi = fv.min(axis=0), fv.max(axis=0)
    f_ctr = (flo + fhi) / 2.0
    f_span = float(max(fhi - flo)) or 100.0
    print(f"furnishings-only bbox: {flo.round(1).tolist()} .. "
         f"{fhi.round(1).tolist()}  span={f_span:.1f}in")

    whole_lo, whole_hi = model.bbox
    whole_ctr = (whole_lo + whole_hi) / 2.0

    from PyQt6.QtWidgets import QApplication, QMainWindow
    import pyqtgraph as pg
    app = QApplication(sys.argv[:1])
    win = QMainWindow()
    win.setWindowTitle("D74-style working-distance check -- shower identity")
    body = fp3d.Plan3DWidget(model)
    win.setCentralWidget(body)
    win.resize(1200, 820)
    win.show()

    # re-point the pivot at the furnishings' own centroid (vertices were
    # already shifted by -whole_ctr when the view was built) and close the
    # distance to fit just their span, not the room's
    rel_ctr = f_ctr - whole_ctr
    body.view.opts["center"] = pg.Vector(rel_ctr[0], rel_ctr[1], rel_ctr[2])
    body.view.setCameraPosition(distance=f_span * 1.4, elevation=28, azimuth=-60)

    for _ in range(3):
        app.processEvents()
    out = Path(__file__).resolve().parent / "shower-glance-working-distance-after.png"
    body.view.grabFramebuffer().save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
