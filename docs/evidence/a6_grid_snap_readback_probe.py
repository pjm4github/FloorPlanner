"""A6, grid snap by default -- the READ-BACK's measurements (ROADMAP.md A6:
"a read-back comes first ... the clause-by-clause reconciliation, EXISTS /
PARTIAL / ABSENT per clause"; ordered by Patrick 2026-10-03, angled walls
excepted).

What does each wall gesture do TODAY, with no modifier, with Shift and with
Ctrl -- and does the answer depend on the zoom? Every gesture is driven by
real mouse events on the view, each in a fresh window, at two zooms (0.25x
and 2x). "On grid" means both coordinates are multiples of the wall snap
step (6in by default).

    A  draw, from an on-grid start
    B  draw, from an existing wall end that is OFF the grid
    C  drag an end of an on-grid wall, and of an off-grid wall
    D  slide a wall's body: an on-grid wall, and an off-grid wall
    E  zoom: the start snap and the end's align-to-a-wall, same scene points
    F  two ends meeting: exactly coincident, 6in apart, 12in apart
    G  a shared corner: slide one wall, does the other follow
    H  the readout: what the status bar and the wall's own label say mid-draw

A measurement; nothing is changed. Output kept as
`a6-grid-snap-readback-probe.txt`.

    python docs/evidence/a6_grid_snap_readback_probe.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QEvent, QPointF, Qt        # noqa: E402
from PyQt6.QtGui import QMouseEvent                 # noqa: E402
from PyQt6.QtWidgets import QApplication            # noqa: E402

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp                            # noqa: E402

LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
MODS = (("none ", Qt.KeyboardModifier.NoModifier),
        ("Shift", Qt.KeyboardModifier.ShiftModifier),
        ("Ctrl ", Qt.KeyboardModifier.ControlModifier))
ZOOMS = (0.25, 2.0)
STEP = fp.SETTINGS["wall_snap_in"]


def window(zoom):
    win = fp.MainWindow()
    win.resize(1400, 1000)
    win.prepare_headless()
    win.view.resetTransform()
    win.view.scale(zoom, zoom)
    win.view.centerOn(QPointF(300.0, 230.0))
    return win


def send(win, etype, p, button, buttons, mods):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(p[0], p[1]))
    assert vp.rect().contains(pos), f"{p} is outside the viewport"
    QApplication.sendEvent(vp, QMouseEvent(
        etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons, mods))


def drag(win, a, b, mods=Qt.KeyboardModifier.NoModifier, release=True):
    send(win, QEvent.Type.MouseButtonPress, a, LEFT, LEFT, mods)
    send(win, QEvent.Type.MouseMove, b, NONE, LEFT, mods)
    if release:
        send(win, QEvent.Type.MouseButtonRelease, b, LEFT, NONE, mods)


def wall(win, a, b, kind="interior"):
    w = fp.WallItem(QPointF(*a), QPointF(*b), kind)
    win.scene.addItem(w)
    fp.rebuild_all_walls(win.scene)
    return w


def walls(win):
    return [it for it in win.scene.items() if isinstance(it, fp.WallItem)]


def pt(p):
    return f"({p.x():.2f},{p.y():.2f})"


def on_grid(p):
    return all(abs(v / STEP - round(v / STEP)) < 1e-6 for v in (p.x(), p.y()))


def grid(p):
    return "ON grid " if on_grid(p) else "OFF grid"


def draw(win, a, b, mods):
    before = set(map(id, walls(win)))
    win.set_tool(fp.TOOL_WALL_INT)
    drag(win, a, b, mods)
    new = [w for w in walls(win) if id(w) not in before]
    win.set_tool(fp.TOOL_SELECT)
    return new[0] if new else None


def main():
    print(f"wall snap step {STEP:g}in; JOIN_TOL {fp.JOIN_TOL:g}in; "
          f"rotate snap {fp.SETTINGS['rotate_snap_deg']:g} deg")

    print("\n== A. DRAW from an on-grid start (120,120), cursor released at (247,133) ==")
    for label, mods in MODS:
        for z in ZOOMS:
            win = window(z)
            w = draw(win, (120, 120), (247, 133), mods)
            print(f"   {label} zoom {z:<4}: start {pt(w.p1)} end {pt(w.p2)} {grid(w.p2)} "
                  f"length {w.length():.2f}")
            win.close()

    print("\n== B. DRAW from an existing wall end that is OFF the grid, (123,203); "
          "press at (124,204), release at (250,206) ==")
    for label, mods in MODS:
        for z in ZOOMS:
            win = window(z)
            wall(win, (123, 303), (123, 203))
            w = draw(win, (124, 204), (250, 206), mods)
            print(f"   {label} zoom {z:<4}: start {pt(w.p1)} {grid(w.p1)} end {pt(w.p2)} "
                  f"{grid(w.p2)}")
            win.close()

    print("\n== C. DRAG AN END: p2 of a horizontal wall, cursor to 35 right and 7 down ==")
    for name, a, b in (("on-grid wall (120,120)-(240,120) ", (120, 120), (240, 120)),
                       ("OFF-grid wall (123,203)-(243,203)", (123, 203), (243, 203))):
        for label, mods in MODS:
            win = window(2.0)
            w = wall(win, a, b)
            drag(win, b, (b[0] + 35, b[1] + 7), mods)
            dev = abs(w.p2.y() - w.p1.y())
            print(f"   {name} {label}: p1 {pt(w.p1)} p2 {pt(w.p2)} {grid(w.p2)}"
                  + (f"  -- the wall is now {dev:.0f}in off its axis over {w.length():.0f}in"
                     if 0 < dev < 12 else ""))
            win.close()

    print("\n== D. SLIDE THE BODY of a horizontal wall, cursor 20 down and 9 right ==")
    for name, a, b in (("on-grid wall (120,120)-(240,120) ", (120, 120), (240, 120)),
                       ("OFF-grid wall (123,203)-(243,203)", (123, 203), (243, 203))):
        for label, mods in (MODS[0], MODS[2]):
            win = window(2.0)
            w = wall(win, a, b)
            m = ((a[0] + b[0]) / 2.0, a[1])
            drag(win, m, (m[0] + 9, m[1] + 20), mods)
            print(f"   {name} {label}: p1 {pt(w.p1)} {grid(w.p1)} p2 {pt(w.p2)} {grid(w.p2)}")
            win.close()

    print("\n== E. ZOOM: the same scene points, two zooms ==")
    for z in ZOOMS:
        win = window(z)
        wall(win, (402, 60), (402, 150))           # a vertical wall, both ends open, x=402
        w = draw(win, (120, 240), (425, 243), Qt.KeyboardModifier.NoModifier)
        print(f"   zoom {z:<4}: draw (120,240)->(425,243) beside an open-ended wall at x=402: "
              f"end {pt(w.p2)} {grid(w.p2)}")
        win.close()
    for z in ZOOMS:
        win = window(z)
        wall(win, (123, 303), (123, 203))
        w = draw(win, (150, 221), (300, 221), Qt.KeyboardModifier.NoModifier)
        print(f"   zoom {z:<4}: press at (150,221), 32in from the wall end (123,203): "
              f"start {pt(w.p1)}")
        win.close()

    print("\n== F. TWO ENDS MEETING: a wall drawn toward the end (360,300) of a vertical wall ==")
    for gap, endx in (("exactly on it", 360), ("6in short    ", 354), ("12in short   ", 348)):
        win = window(2.0)
        other = wall(win, (360, 300), (360, 400))
        w = draw(win, (240, 300), (endx, 300), Qt.KeyboardModifier.NoModifier)
        shared = any(v is ov for v in (w._v1, w._v2) for ov in (other._v1, other._v2))
        print(f"   released {gap} at ({endx},300): end lands {pt(w.p2)}; "
              f"gap left {abs(360 - w.p2.x()):.0f}in; one shared corner = {shared}")
        win.close()

    print("\n== G. A SHARED CORNER: an L, its horizontal wall slid 24 down ==")
    win = window(2.0)
    a = wall(win, (120, 120), (240, 120))
    b = wall(win, (240, 120), (240, 240))
    fp.share_coincident_ends(win.scene, a.floor)
    drag(win, (180, 120), (180, 144))
    print(f"   horizontal {pt(a.p1)}-{pt(a.p2)}; the vertical's top end now {pt(b.p1)} "
          f"-- carried = {abs(b.p1.y() - a.p2.y()) < 1e-6 and abs(b.p1.x() - a.p2.x()) < 1e-6}")
    win.close()

    print("\n== H. THE READOUT, mid-draw: (120,120) dragged to cursor (247,133), not released ==")
    win = window(2.0)
    win.set_tool(fp.TOOL_WALL_INT)
    drag(win, (120, 120), (247, 133), release=False)
    w = win.view._temp_wall
    print(f"   the wall being drawn: end {pt(w.p2)}, length {w.length():.2f} "
          f"(its own painted label reads {fp.fmt_ftin(w.length())!r})")
    msg = win.statusBar().currentMessage().encode("ascii", "replace").decode()
    print(f"   status bar message: {msg!r}")
    print(f"   status bar coordinate label: {win.coord_label.text()!r}  "
          f"(cursor is at x {fp.fmt_ftin(247)}, y {fp.fmt_ftin(133)})")
    win.close()


if __name__ == "__main__":
    main()
