"""Reproduce: multiple roofs on one level, select one, drag an edge grip;
the app eventually locks up. For every roof x grip x offset, drag with real
mouse events (hold during the drag, compose at release, as the app does)
and time the release; count the clipper's rounds; stop a compose that
passes ROUND_CAP rounds and say where."""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from PyQt6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PyQt6.QtGui import QMouseEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
import FloorPlanner as fp  # noqa: E402
from floorplanner import roofclip  # noqa: E402
from floorplanner.roofs import RoofItem  # noqa: E402

PLAN = sys.argv[1]
ROUND_CAP = int(os.environ.get("ROUND_CAP", "400"))
OFFSETS = [int(v) for v in os.environ.get("OFFSETS", "-72,-48,-24,-12,-6,6,12,24,48,72").split(",")]
GRIPS = os.environ.get("GRIPS", "eave_l,eave_r,end_0,end_1,ridge").split(",")

import floorplanner.roofs as roofs_mod  # noqa: E402

state = {"rounds": 0, "reach": 0, "composes": 0}
_compose = roofclip.compose_building
_reach = roofclip._reach


class TooManyRounds(Exception):
    pass


def counting_compose(pairs, diag=None):
    d = {}
    state["composes"] += 1
    try:
        return _compose(pairs, diag=d)
    finally:
        state["rounds"] += len(d.get("rounds", []))


def counting_reach(*a, **k):
    state["reach"] += 1
    if state["reach"] > 200_000:                 # the hang guard
        raise TooManyRounds(state["reach"])
    return _reach(*a, **k)


roofs_mod.compose_building = counting_compose
roofclip._reach = counting_reach


def send(win, etype, p, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(p)
    QApplication.sendEvent(vp, QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                                           button, buttons, Qt.KeyboardModifier.NoModifier))


def fresh():
    win = fp.MainWindow()
    win.prepare_headless()
    win.load_path(PLAN)
    win.set_tool(fp.TOOL_SELECT)
    win._set_show_roofs(True)
    win._set_edit_roofs(True)
    win.view.fitInView(win.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    return win


win = fresh()
roofs = sorted((r for r in win.scene.items() if isinstance(r, RoofItem)),
               key=lambda r: (r.floor, r.p1.x(), r.p1.y()))
print(f"{os.path.basename(PLAN)}: {len(roofs)} roofs; floors {sorted({r.floor for r in roofs})}")
worst = []
for ri, _rf0 in enumerate(roofs):
    for kind in GRIPS:
        for off in OFFSETS:
            win = fresh()
            rfs = sorted((r for r in win.scene.items() if isinstance(r, RoofItem)),
                         key=lambda r: (r.floor, r.p1.x(), r.p1.y()))
            rf = rfs[ri]
            if rf.floor != win.active_floor:
                win.switch_floor(rf.floor)
                app.processEvents()
            rf.setSelected(True)
            app.processEvents()
            grip = next((g for g in rf.grips if g.kind == kind), None)
            if grip is None or not grip.isVisible():
                continue
            a = grip.scenePos()
            ux, uy, _, _ = rf._axis()
            if kind in ("eave_l", "eave_r"):
                b = QPointF(a.x() - uy * off, a.y() + ux * off)        # along the normal
            elif kind == "ridge":
                b = QPointF(a.x() - uy * off, a.y() + ux * off)
            else:
                b = QPointF(a.x() + ux * off, a.y() + uy * off)        # along the ridge
            state.update(rounds=0, reach=0, composes=0)
            t0 = time.perf_counter()
            try:
                left = Qt.MouseButton.LeftButton
                send(win, QEvent.Type.MouseButtonPress, a, left, left)
                send(win, QEvent.Type.MouseMove, b, Qt.MouseButton.NoButton, left)
                send(win, QEvent.Type.MouseButtonRelease, b, left, Qt.MouseButton.NoButton)
                app.processEvents()
                dt = time.perf_counter() - t0
                verdict = "ok"
            except TooManyRounds:
                dt = time.perf_counter() - t0
                verdict = "HANG GUARD: >200000 reach calls"
            except Exception as ex:                        # noqa: BLE001
                dt = time.perf_counter() - t0
                verdict = f"EXC {type(ex).__name__}: {ex}"
            worst.append((dt, state["rounds"], ri, kind, off, verdict))
            if verdict != "ok" or dt > 2.0 or state["rounds"] > 40:
                print(f"  roof[{ri}] {rf.floor} {kind} {off:+d}: {dt:.2f}s rounds={state['rounds']} composes={state['composes']} {verdict}", flush=True)
            win.close()
worst.sort(reverse=True)
print("slowest 5:", [(f"{d:.2f}s", r, i, k, o, v) for d, r, i, k, o, v in worst[:5]])
print("cases:", len(worst), "max rounds:", max(w[1] for w in worst) if worst else 0)
sys.stdout.flush()
os._exit(0)
