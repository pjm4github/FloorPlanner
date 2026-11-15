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

# PyQt6.QtCore is base PyQt6 (a hard dependency of the app), NOT the OPTIONAL
# Qt Quick 3D stack the module-level comment on Plan3DQuickWidget guards -- so
# the walk bridge (0328, Phase 2), which needs only QtCore, lives at module
# scope where it can be unit-tested, while every QtQuick3D / QtQuickWidgets
# import stays inside Plan3DQuickWidget.
from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal, pyqtSlot

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


def plan_to_qml_pose(px, py, wz, rot_deg, ctr, pitch_deg=0.0):
    """A FIRST-PERSON camera pose, from the plan to Qt Quick 3D.

    A plan point is (x, y-DOWN) in inches; `build_model` carries it to the
    fp3d world frame (x, -y, z-up); the widget then recentres every vertex by
    `- ctr` (the model's world-frame bbox centre) and `_to_qt3d` rotates z-up
    -> y-up as (x, y, z) -> (x, z, -y). The camera eye must ride the SAME two
    steps or it will not sit in the room:

        eye_world = (px, -py, wz)
        recentred = eye_world - ctr
        eye_qml   = (recentred.x, recentred.z, -recentred.y)
                  = (px - ctr[0], wz - ctr[2], py + ctr[1])

    AIM. A plan aim `rot_deg` is 0 = +x, measured in the y-down plane (the same
    convention CameraItem.rotation() uses). A Qt Quick 3D PerspectiveCamera at
    eulerRotation.y = 0 looks down -Z; rotating -Z about +Y by yaw gives the
    forward (-sin yaw, 0, -cos yaw). Requiring that equal the plan aim mapped
    into QML, (cos rot, 0, sin rot), solves to yaw = -rot - 90 (deg). Checked:
    rot 0 (+x) -> yaw -90 -> forward (1,0,0); rot 90 (plan +y / south) ->
    yaw 180 -> forward (0,0,1). `pitch_deg` is eulerRotation.x (0 = level).

    Returns (eyeX, eyeY, eyeZ, yaw_deg, pitch_deg), all floats, QML y-up."""
    ex = float(px) - float(ctr[0])
    ey = float(wz) - float(ctr[2])
    ez = float(py) + float(ctr[1])
    yaw_q = -float(rot_deg) - 90.0
    return ex, ey, ez, yaw_q, float(pitch_deg)


def qml_pose_to_plan(ex, ez, yaw_q, ctr):
    """The INVERSE of `plan_to_qml_pose` (0328, 3D-camera Phase 2): a QML camera
    eye/aim read back to the plan the view EDITS.

    `plan_to_qml_pose` is a pure rigid remap -- `ex = px - ctr[0]`,
    `ez = py + ctr[1]`, `yaw = -rot - 90` -- so it inverts exactly:

        px  = ex + ctr[0]
        py  = ez - ctr[1]
        rot = (-yaw - 90) mod 360

    `ey` (the eye's QML height) and pitch are NOT read back: eye height is fixed
    (Phase 2 walks in the plan XY plane, C1) and pitch stays view-local (the plan
    camera owns no pitch). As ARITHMETIC this round-trips to the identity; THROUGH
    a `CameraItem` it is only within the grid snap step, because `itemChange`
    snaps `setPos` to the 1-inch grid. Returns `(px, py, rot_deg)`."""
    px = float(ex) + float(ctr[0])
    py = float(ez) - float(ctr[1])
    rot = (-float(yaw_q) - 90.0) % 360.0
    return px, py, rot


class WalkBridge(QObject):
    """0328 (3D-camera Phase 2, Option B): the QML walk input, handed to Python.

    The ruling adopted Option B -- Python integrates the key/mouse deltas and
    `fpCamera` stays bound to `pose`; moving in the plan XY plane keeps the eye
    at 65in BY CONSTRUCTION (C1). QML calls `step(forward, strafe, dyaw, dpitch)`
    each input tick and `capture()` / `release()` on the capture gesture.

    C2 -- THE WRITE-BACK LEAVES QML FIRST. `step` only ACCUMULATES the deltas and
    arms a single `QTimer.singleShot(0)`; the CameraItem is moved (and the
    view-local pitch applied to `pose`) in `_flush`, on the next event-loop turn,
    OUTSIDE the QML signal handler. A synchronous move there would re-emit
    `pose.changed` and re-evaluate the QML camera bindings from inside the QML
    call that triggered it -- the 0xC0000409 re-entrancy shape. The pending
    deltas coalesce a burst of ticks into one move.

    `forward`/`strafe` are plan inches, `dyaw`/`dpitch` degrees. Yaw writes back
    to the plan camera (heading); pitch is VIEW-LOCAL (the plan camera has no
    pitch field) and only touches `pose`. The callbacks are wired by the widget
    (`set_walk_callbacks` / `set_view_pitch`)."""

    capturedChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._walk_cb = None          # (forward, strafe, dyaw) -> move CameraItem
        self._capture_cb = None
        self._release_cb = None
        self._pitch_cb = None         # (pitch_deg) -> apply to pose (view-local)
        self._pitch = 0.0
        self._captured = False
        self._pending = None          # [forward, strafe, dyaw, dpitch]
        self._scheduled = False

    @pyqtProperty(bool, notify=capturedChanged)
    def captured(self):
        return self._captured

    @pyqtSlot(float, float, float, float)
    def step(self, forward, strafe, dyaw, dpitch):
        if self._pending is None:
            self._pending = [0.0, 0.0, 0.0, 0.0]
        self._pending[0] += float(forward)
        self._pending[1] += float(strafe)
        self._pending[2] += float(dyaw)
        self._pending[3] += float(dpitch)
        if not self._scheduled:
            self._scheduled = True
            QTimer.singleShot(0, self._flush)

    def _flush(self):
        self._scheduled = False
        pend, self._pending = self._pending, None
        if pend is None:
            return
        forward, strafe, dyaw, dpitch = pend
        if dpitch and self._pitch_cb is not None:
            self._pitch = max(-89.0, min(89.0, self._pitch + dpitch))
            try:
                self._pitch_cb(self._pitch)
            except RuntimeError:
                self._pitch_cb = None
        if (forward or strafe or dyaw) and self._walk_cb is not None:
            try:
                self._walk_cb(forward, strafe, dyaw)
            except RuntimeError:
                self._walk_cb = None

    @pyqtSlot()
    def capture(self):
        if not self._captured:
            self._captured = True
            self.capturedChanged.emit()
        if self._capture_cb is not None:
            self._capture_cb()

    @pyqtSlot()
    def release(self):
        was = self._captured
        if was:
            self._captured = False
            self.capturedChanged.emit()
        self._pending = None          # drop the half-tick of a pending step
        if was and self._release_cb is not None:
            self._release_cb()


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
                      parent=None, yaw=0.0, pitch=0.0, zoom=1.0, fov=60.0,
                      first_person=False, cam_pose=None):
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
    from PyQt6.QtCore import QByteArray, QUrl
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

        def __init__(self, distance, ao, shadows, status, yaw=0.0, pitch=0.0, zoom=1.0,
                     fov=60.0, first_person=False):
            super().__init__()
            self._d, self._ao = distance, ao
            self._s, self._t = shadows, status
            self._yaw, self._pitch, self._zoom = float(yaw), float(pitch), float(zoom)
            self._fov = float(fov)
            self._fp = bool(first_person)

        @pyqtProperty(float, constant=True)
        def distance(self):
            return self._d

        # the viewpoint (0252-report.md): the orbit node's two angles and a
        # zoom factor, 0 / 0 / 1 for the home view
        @pyqtProperty(float, constant=True)
        def yaw(self):
            return self._yaw

        @pyqtProperty(float, constant=True)
        def pitch(self):
            return self._pitch

        @pyqtProperty(float, constant=True)
        def zoom(self):
            return self._zoom

        @pyqtProperty(float, constant=True)
        def fov(self):
            # the camera's vertical field of view: 60 (Qt's default, the
            # interactive view) or a shot's own -- a long lens, 25-30,
            # with the camera farther back, for a less distorted picture
            return self._fov

        @pyqtProperty(bool, constant=True)
        def ao(self):
            return self._ao

        @pyqtProperty(bool, constant=True)
        def shadows(self):
            return self._s

        @pyqtProperty(str, constant=True)
        def status(self):
            return self._t

        @pyqtProperty(bool, constant=True)
        def firstPerson(self):
            # the mode is fixed when the window opens: a first-person view
            # bound to a plan camera, or the orbit view. The POSE moves live
            # (see Pose); the MODE does not.
            return self._fp

        @pyqtProperty(bool, constant=True)
        def walk(self):
            # 0328 (Phase 2): this first-person view can be WALKED -- captured
            # for WASD + mouse-look, each step written back to the plan camera.
            # Tied to first-person mode; the orbit view never walks. The LIVE
            # capture state is `walkBridge.captured`, which the QML binds to.
            return self._fp

    class Pose(QObject):
        """The first-person camera pose in QML coordinates, pushed LIVE as the
        plan camera moves -- unlike Cfg's load-once scalars, every field has a
        NOTIFY so scene.qml re-renders on a set with no mesh rebuild. The
        first-person camera binds its position/eulerRotation to these."""

        changed = pyqtSignal()

        def __init__(self, ex=0.0, ey=0.0, ez=0.0, yaw=0.0, pitch=0.0):
            super().__init__()
            self._ex, self._ey, self._ez = float(ex), float(ey), float(ez)
            self._yaw, self._pitch = float(yaw), float(pitch)

        def _set(self, ex, ey, ez, yaw, pitch):
            self._ex, self._ey, self._ez = float(ex), float(ey), float(ez)
            self._yaw, self._pitch = float(yaw), float(pitch)
            self.changed.emit()

        @pyqtProperty(float, notify=changed)
        def eyeX(self):
            return self._ex

        @pyqtProperty(float, notify=changed)
        def eyeY(self):
            return self._ey

        @pyqtProperty(float, notify=changed)
        def eyeZ(self):
            return self._ez

        @pyqtProperty(float, notify=changed)
        def yaw(self):
            return self._yaw

        @pyqtProperty(float, notify=changed)
        def pitch(self):
            return self._pitch

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

    pose = Pose(*plan_to_qml_pose(*cam_pose, ctr)) if cam_pose is not None else Pose()
    walk_bridge = WalkBridge()

    cfg = Cfg(span * 1.25, ao, shadows, model_status(model), yaw, pitch, zoom, fov,
              first_person=first_person)
    url = QUrl.fromLocalFile(QML_PATH)

    if container:
        from PyQt6.QtQuick import QQuickView
        view = QQuickView()
        view.rootContext().setContextProperty("planMeshes", entries)
        view.rootContext().setContextProperty("cfg", cfg)
        view.rootContext().setContextProperty("pose", pose)
        view.rootContext().setContextProperty("walkBridge", walk_bridge)
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
        w.rootContext().setContextProperty("pose", pose)
        w.rootContext().setContextProperty("walkBridge", walk_bridge)
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
    w._keep = (entries, cfg, pose, walk_bridge)
    w._pose = pose
    w.walk_bridge = walk_bridge
    w._surface = surface                    # what a shot grabs (QQuickWidget or QQuickView)

    def set_camera_pose(px, py, wz, rot_deg, pitch_deg=None):
        """Push a new plan pose into the live first-person camera -- a handful
        of property writes, no mesh rebuild. `(px, py)` plan inches, `wz` the
        eye's world height, `rot_deg` the plan aim (0 = +x). Safe (no-op) on an
        orbit-mode widget, and after the window is torn down (a deferred push
        can land late, when the Pose is already gone).

        0328: `pitch_deg=None` PRESERVES the current view-local pitch -- the
        plan camera owns no pitch (Phase 2 keeps it view-local), so a plan-side
        feed (Phase 1's follow, or a walk's write-back echo) must not reset the
        angle the user is looking up/down at."""
        try:
            keep = pose.pitch if pitch_deg is None else pitch_deg
            pose._set(*plan_to_qml_pose(px, py, wz, rot_deg, ctr, keep))
        except RuntimeError:
            pass

    def set_view_pitch(pitch_deg):
        """0328 (Phase 2): set the VIEW-LOCAL pitch on `pose` alone, leaving eye
        and yaw. The walk's mouse-look writes pitch here (never to the plan
        camera). Safe (no-op) after teardown."""
        try:
            pose._set(pose.eyeX, pose.eyeY, pose.eyeZ, pose.yaw, float(pitch_deg))
        except RuntimeError:
            pass

    def set_walk_callbacks(step_cb=None, capture_cb=None, release_cb=None):
        """0328 (Phase 2): wire the walk bridge to the app. `step_cb(forward,
        strafe, dyaw)` moves the plan CameraItem (called DEFERRED, off the QML
        stack -- C2); `capture_cb`/`release_cb` take and drop the undo hold."""
        walk_bridge._walk_cb = step_cb
        walk_bridge._capture_cb = capture_cb
        walk_bridge._release_cb = release_cb
        walk_bridge._pitch_cb = set_view_pitch

    w.set_camera_pose = set_camera_pose
    w.set_view_pitch = set_view_pitch
    w.set_walk_callbacks = set_walk_callbacks
    return w


def grab_quick_view(widget):
    """The rendered image of a `Plan3DQuickWidget`: `grabFramebuffer()` on a
    QQuickWidget, `grabWindow()` on a container's QQuickView. Both need the
    scene to have rendered at least once -- the caller waits a few frames.
    Needs a real display (D77): under the offscreen platform the image
    comes back null, as the pyqtgraph viewer's does."""
    surface = getattr(widget, "_surface", widget)
    if hasattr(surface, "grabWindow"):
        return surface.grabWindow()
    return surface.grabFramebuffer()


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
    ap.add_argument("--shot", metavar="PATH",
                    help="render to PNG and exit (needs a real display; 0252-report.md)")
    ap.add_argument("--yaw", type=float, default=0.0,
                    help="orbit the view this many degrees about the vertical (0: the home view)")
    ap.add_argument("--pitch", type=float, default=0.0,
                    help="tilt the orbit this many degrees (0: the home view, -24 deg down)")
    ap.add_argument("--zoom", type=float, default=1.0,
                    help="camera distance as a multiple of the home distance")
    ap.add_argument("--fov", type=float, default=60.0,
                    help="camera field of view in degrees for --shot (60: the view's own; "
                         "25-30 with --zoom 1 or more for a less distorted picture)")
    ap.add_argument("--shot-delay", type=int, default=600,
                    help="milliseconds to let the scene render before the shot")
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
                                 container=a.container, parent=win,
                                 yaw=a.yaw, pitch=a.pitch, zoom=a.zoom, fov=a.fov)
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
    if a.shot:
        # let the scene render (AO and shadows take a frame or two), grab,
        # report, and leave the event loop
        from PyQt6.QtCore import QTimer
        result = {}

        def shoot():
            img = grab_quick_view(body)
            result["ok"] = (not img.isNull()) and img.save(a.shot)
            app.quit()

        QTimer.singleShot(a.shot_delay, shoot)
        app.exec()
        if result.get("ok"):
            print(f"  wrote {a.shot}")
            return 0
        print(f"  could not write {a.shot}: the scene rendered no image "
              f"(a real display is needed; see D77)")
        return 3
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
