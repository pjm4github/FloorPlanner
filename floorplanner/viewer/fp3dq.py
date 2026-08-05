#!/usr/bin/env python3
"""
fp3dq.py -- the SAME viewer, on Qt Quick 3D instead of pyqtgraph.

    python fp3dq.py examples/symmetricP1.json
    python fp3dq.py examples/symmetricP1.json --no-ao --no-shadows
    python fp3dq.py --check          # just report whether the stack resolves

A spike, for comparing the two back ends.  It deliberately reuses `fp3d`'s
`build_model()` untouched: the point of the exercise is to find out whether the
geometry / presentation seam really holds when the renderer is replaced.

*** NOT YET RUN ANYWHERE.  Written without a PyQt6 install to test against. ***
Treat first-run failures as expected; `--check` reports what resolved.

What this buys over the pyqtgraph version
-----------------------------------------
Ambient occlusion, real-time shadow maps, physically-based materials, MSAA and
tone mapping are all properties of `SceneEnvironment` / `PrincipledMaterial` --
declarative settings rather than shaders we write.  That is the entire argument
for this path: the things fp3d.py cannot reach without hand-written GLSL are
configuration here.

What it costs
-------------
* Qt Quick 3D is QML.  The scene graph is declared in a .qml document, so the
  app grows a second language and a QML runtime alongside the widget tree.
* Geometry must be handed over as an interleaved vertex buffer through a
  QQuick3DGeometry subclass -- more ceremony than pyqtgraph's `vertexes=`/
  `faces=` numpy arrays, and non-indexed, so vertices are duplicated per face.
* Coordinates change hands: Qt Quick 3D is Y-up, so the model is rotated on the
  way in (see `_to_qt3d`).
* QQuickWidget composites through an offscreen texture.  It works from Qt 6.4,
  but a QQuickView in a window container is the more reliable embedding if it
  misbehaves -- hence `--container`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

try:                                  # imported as part of the package
    from .fp3d import build_model, load_catalog   # (same geometry core)
except ImportError:                   # ...or run as a loose script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from fp3d import build_model, load_catalog  # noqa: E402

# --------------------------------------------------------------------------
# QML scene.  A real document beside the module (packaged as package-data),
# not an inline string written to a temp file: the spike's one-file
# constraint is gone now that this is imported by the app, and a .qml on
# disk is what an editor, a linter and a stack trace can all see.
# --------------------------------------------------------------------------

QML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "scene.qml")


# --------------------------------------------------------------------------
# geometry hand-off
# --------------------------------------------------------------------------

def _to_qt3d(v):
    """z-up (ours) -> y-up (Qt Quick 3D).  (x, y, z) -> (x, z, -y)."""
    out = np.empty_like(v)
    out[:, 0] = v[:, 0]
    out[:, 1] = v[:, 2]
    out[:, 2] = -v[:, 1]
    return out


def _interleaved(verts, faces, rgba):
    """Non-indexed float32 buffer: pos(3) + normal(3) + colour(4), 40B stride.

    Qt Quick 3D lights the scene itself, so the colour written here is the
    material's BASE colour, not the pre-lit colour fp3d bakes.  That difference
    is the comparison in one line.
    """
    tri = verts[faces]                                   # (M, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    n = n / ln
    pos = _to_qt3d(tri.reshape(-1, 3)).astype(np.float32)
    nrm = _to_qt3d(np.repeat(n, 3, axis=0)).astype(np.float32)
    col = np.tile(np.asarray(rgba, dtype=np.float32), (len(pos), 1))
    buf = np.hstack([pos, nrm, col]).astype(np.float32)
    return buf, pos.min(axis=0), pos.max(axis=0)


def _make_geometry(QQuick3DGeometry, QByteArray, QVector3D, verts, faces, rgba):
    buf, lo, hi = _interleaved(verts, faces, rgba)
    A = QQuick3DGeometry.Attribute
    g = QQuick3DGeometry()
    g.setStride(40)
    g.setVertexData(QByteArray(buf.tobytes()))
    g.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
    g.addAttribute(A.Semantic.PositionSemantic, 0, A.ComponentType.F32Type)
    g.addAttribute(A.Semantic.NormalSemantic, 12, A.ComponentType.F32Type)
    g.addAttribute(A.Semantic.ColorSemantic, 24, A.ComponentType.F32Type)
    g.setBounds(QVector3D(*map(float, lo)), QVector3D(*map(float, hi)))
    g.update()
    return g


# Wall and floor surfaces are typed by the DOCUMENT, not by the catalog, so
# these two are viewer defaults and are NOT duplication of anything: no other
# file states them.  Driving them from the document's own finish strings is
# VIEWER_NOTES.md section 5 item 3, deliberately reserved until finishes
# actually vary.  They are not folded into assets/furnishings/materials.json
# because a wall surface is not a furnishing, and filing it under one would be
# a worse error than the duplication it would remove.
WALL_PBR = (0.92, 0.0)                      # roughness, metalness
FLOOR_PBR = (0.72, 0.0)
FURN_PBR_DEFAULT = (0.85, 0.0)


def _pbr(name, materials=None):
    """(roughness, metalness) for a mesh, from the CATALOG where it owns it.

    fp3d names each furnishing mesh `furnishings:<material>`, and the material
    is a catalog name whose properties live once in materials.json.  This
    function used to restate them by sniffing the mesh name for 'metal',
    'glass', 'porcelain', 'vehicle' -- a second definition of catalog data,
    and one that could not be corrected without editing the viewer."""
    if name.startswith("walls"):
        return WALL_PBR
    if name.startswith("floors"):
        return FLOOR_PBR
    mat = (materials or {}).get(name.split(":", 1)[-1])
    if isinstance(mat, dict):
        return (float(mat.get("roughness", FURN_PBR_DEFAULT[0])),
                float(mat.get("metalness", FURN_PBR_DEFAULT[1])))
    return FURN_PBR_DEFAULT


# --------------------------------------------------------------------------
# check / build
# --------------------------------------------------------------------------

def check():
    """Report whether the stack resolves, without opening a window."""
    ok = True
    try:
        import PyQt6.QtQuick3D as q3d
        print(f"  PyQt6.QtQuick3D          OK  ({q3d.__name__})")
        for n in ("QQuick3D", "QQuick3DGeometry"):
            print(f"    {n:22} {'OK' if hasattr(q3d, n) else 'MISSING'}")
            ok &= hasattr(q3d, n)
    except Exception as e:
        print(f"  PyQt6.QtQuick3D          MISSING -- {e}")
        ok = False
    try:
        from PyQt6.QtQuickWidgets import QQuickWidget  # noqa: F401
        print("  PyQt6.QtQuickWidgets     OK")
    except Exception as e:
        print(f"  PyQt6.QtQuickWidgets     MISSING -- {e}")
        ok = False
    try:
        from PyQt6.QtCore import QLibraryInfo, QLibraryInfo as LI
        qml = QLibraryInfo.path(LI.LibraryPath.QmlImportsPath)
        print(f"  QML imports path         {qml}")
        for mod in ("QtQuick3D", os.path.join("QtQuick3D", "Helpers")):
            p = os.path.join(qml, mod)
            print(f"    {mod:22} {'OK' if os.path.isdir(p) else 'MISSING'}")
            ok &= os.path.isdir(p)
    except Exception as e:
        print(f"  QML imports path         unknown -- {e}")
        ok = False
    print("\n  " + ("stack looks complete" if ok else
                    "incomplete -- pip install PyQt6 (full wheel includes "
                    "QtQuick3D); a minimal/stripped Qt may omit the QML "
                    "plugins even when the Python module imports"))
    return 0 if ok else 1


def model_status(model):
    """The one-line summary both entry points print / show."""
    s = model.stats
    return (f" {s['rooms']} rooms · {s['walls']} walls · "
            f"{s['openings']} openings · {s['triangles']:,} triangles"
            + (f" · !{len(model.notes)}" if model.notes else ""))


def Plan3DQuickWidget(model, ao=True, shadows=True, container=False,
                      parent=None):
    """The Qt Quick 3D scene for `model`, as a plain QWidget.

    Extracted from `main()` so the app can embed the same view it ships as a
    command-line tool -- one renderer, one QML document, no second
    implementation to drift.

    **Every Qt Quick 3D import is INSIDE this function, deliberately.** The
    stack is an optional dependency (`pip install -r requirements-viewer.txt`),
    so importing this module must stay free of it: `build_model`, `--dump`
    and `--obj` all run with none of it installed, and the editor must launch
    without it. A missing piece therefore raises `ImportError` from HERE,
    where a caller can catch it and say so, rather than at import time where
    it would take the whole app down.

    Raises `ImportError` if Qt Quick 3D is unavailable, and `RuntimeError` if
    the QML document fails to load (the caller reports either)."""
    from PyQt6.QtCore import QByteArray, QObject, QUrl, pyqtProperty
    from PyQt6.QtGui import QColor, QVector3D
    from PyQt6.QtQuick3D import QQuick3DGeometry
    from PyQt6.QtWidgets import QVBoxLayout, QWidget

    if model.bbox is not None:
        lo, hi = model.bbox
        ctr = (lo + hi) / 2.0
        span = float(max(hi - lo)) or 100.0
    else:
        ctr, span = np.zeros(3), 100.0

    class MeshEntry(QObject):
        """One mesh, as QML sees it."""

        def __init__(self, geom, color, alpha, rough, metal):
            super().__init__()
            self._g, self._c = geom, color
            self._a, self._r, self._m = alpha, rough, metal

        @pyqtProperty(QQuick3DGeometry, constant=True)
        def geom(self):
            return self._g

        @pyqtProperty(QColor, constant=True)
        def color(self):
            return self._c

        @pyqtProperty(float, constant=True)
        def alpha(self):
            return self._a

        @pyqtProperty(float, constant=True)
        def roughness(self):
            return self._r

        @pyqtProperty(float, constant=True)
        def metalness(self):
            return self._m

    class Cfg(QObject):
        """Scalars QML reads at load."""

        def __init__(self, distance, ao, shadows, status):
            super().__init__()
            self._d, self._ao = distance, ao
            self._s, self._t = shadows, status

        @pyqtProperty(float, constant=True)
        def distance(self):
            return self._d

        @pyqtProperty(bool, constant=True)
        def ao(self):
            return self._ao

        @pyqtProperty(bool, constant=True)
        def shadows(self):
            return self._s

        @pyqtProperty(str, constant=True)
        def status(self):
            return self._t

    # The catalog's materials, read the same way build_model reads them --
    # data files, no floorplanner import.
    _materials = load_catalog()[1]
    entries = []
    for m in model.meshes:
        if not len(m.faces):
            continue
        rough, metal = _pbr(m.name, _materials)
        rgba = (m.color[0], m.color[1], m.color[2], 1.0)
        g = _make_geometry(QQuick3DGeometry, QByteArray, QVector3D,
                           m.verts - ctr, m.faces, rgba)
        col = QColor.fromRgbF(*m.color[:3])
        alpha = m.color[3] if len(m.color) > 3 else 1.0
        entries.append(MeshEntry(g, col, float(alpha), rough, metal))

    cfg = Cfg(span * 1.25, ao, shadows, model_status(model))
    url = QUrl.fromLocalFile(QML_PATH)

    if container:
        from PyQt6.QtQuick import QQuickView
        view = QQuickView()
        view.rootContext().setContextProperty("planMeshes", entries)
        view.rootContext().setContextProperty("cfg", cfg)
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.setSource(url)
        holder = QWidget.createWindowContainer(view, parent)
        w = QWidget(parent)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(holder)
        surface = view
    else:
        from PyQt6.QtQuickWidgets import QQuickWidget
        w = QQuickWidget(parent)
        w.rootContext().setContextProperty("planMeshes", entries)
        w.rootContext().setContextProperty("cfg", cfg)
        w.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        w.setSource(url)
        surface = w

    errs = surface.errors() if hasattr(surface, "errors") else []
    if errs:
        raise RuntimeError("; ".join(e.toString() for e in errs))

    # KEEP THE PYTHON SIDE ALIVE. QML holds no Python reference to any of
    # this: the geometry, the mesh entries and the config object are reachable
    # only from here, so without this attribute they are collected out from
    # under a live scene and the view goes black (or takes the process with
    # it). The widget owns them for exactly as long as it exists.
    w._keep = (entries, cfg)
    return w


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("design", nargs="?", help="a v5 design JSON file")
    ap.add_argument("--check", action="store_true",
                    help="report whether Qt Quick 3D resolves, then exit")
    ap.add_argument("--container", action="store_true",
                    help="embed a QQuickView via createWindowContainer instead "
                         "of QQuickWidget (more reliable on some drivers)")
    ap.add_argument("--no-ao", action="store_true")
    ap.add_argument("--no-shadows", action="store_true")
    ap.add_argument("--no-furnishings", action="store_true")
    ap.add_argument("--level", action="append", default=None)
    a = ap.parse_args(argv)

    if a.check:
        print("Qt Quick 3D availability:")
        return check()
    if not a.design:
        ap.error("a design file is required (or use --check)")

    # ---- geometry: identical call to the pyqtgraph viewer's ---------------
    with open(a.design) as fh:
        doc = json.load(fh)
    model = build_model(doc, levels=a.level,
                        furnishings=not a.no_furnishings)
    print(f"{a.design}:{model_status(model)}")
    for n in model.notes:
        print(f"    - {n}")

    # ---- Qt: the SAME widget the app's 3D popup embeds --------------------
    from PyQt6.QtGui import QSurfaceFormat
    from PyQt6.QtQuick3D import QQuick3D
    from PyQt6.QtWidgets import QApplication, QMainWindow

    # must precede the QApplication, so it cannot move into the widget
    QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat(4))
    app = QApplication(sys.argv[:1])

    win = QMainWindow()
    win.setWindowTitle(f"FloorPlanner 3D (Qt Quick 3D) - {a.design}")
    try:
        body = Plan3DQuickWidget(model, ao=not a.no_ao,
                                 shadows=not a.no_shadows,
                                 container=a.container, parent=win)
    except RuntimeError as exc:
        print("")
        print("QML did not load:")
        print(f"    {exc}")
        print("")
        print("Run with --check to see which pieces resolved.")
        return 2
    win.setCentralWidget(body)
    win.resize(1200, 820)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
