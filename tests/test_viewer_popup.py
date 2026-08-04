"""The in-app 3D popup (side task, not migration work).

THE ACCEPTANCE IS READ-ONLY DISCIPLINE: opening the 3D view renders the
current plan and changes nothing -- not the dirty flag, not the scene, and
not the edit-path report channel. A viewer that can dirty a document is a
viewer nobody can trust mid-edit.
"""
import warnings

import pytest
from PyQt6.QtCore import QPointF, QTimer
from PyQt6.QtWidgets import QApplication

import FloorPlanner as fp

pytestmark = pytest.mark.gui


def _close_modal_soon(tries=40):
    """Close the popup from OUTSIDE, the way a user does.

    The dialog is genuinely modal -- `exec()` spins its own event loop and
    does not return until the dialog closes -- so a test that just calls
    `show_3d_view()` would hang forever. Scheduling the close before the call
    exercises the real modal path instead of adding a test-only escape hatch
    to production code."""
    state = {"left": tries}

    def _tick():
        w = QApplication.activeModalWidget()
        if w is not None:
            w.close()
            return
        state["left"] -= 1
        if state["left"] > 0:
            QTimer.singleShot(10, _tick)     # not up yet
    QTimer.singleShot(0, _tick)


def _plan(win):
    corners = [QPointF(0, 0), QPointF(240, 0), QPointF(240, 180),
               QPointF(0, 180)]
    for i in range(4):
        win.scene.addItem(fp.WallItem(corners[i], corners[(i + 1) % 4],
                                      "exterior"))
    fp.rebuild_all_walls(win.scene)
    res = fp.detect_room(win.scene, QPointF(120, 90))
    room = fp.RoomItem("Living", QPointF(120, 90), res[0], res[1],
                       corners=res[2])
    win.scene.addItem(room)
    fp.bind_room_walls(win.scene, room)
    op = fp.OpeningItem(room.walls[0], "door", "3280",
                        room.walls[0].length() / 2)
    room.walls[0].openings.append(op)
    fp.rebuild_all_walls(win.scene)
    return room


def _counts(win):
    walls = sum(1 for it in win.scene.items() if isinstance(it, fp.WallItem))
    rooms = sum(1 for it in win.scene.items() if isinstance(it, fp.RoomItem))
    return walls, rooms


def test_the_3d_view_changes_nothing(win, tmp_path):
    """The acceptance, asserted on all four surfaces at once.

    Run against a genuinely SAVED plan, because that is the state where a
    stray dirty flag actually costs the user something: it turns a document
    that is safely on disk into one the app claims has unsaved changes, and
    the next close prompts about work that was never done."""
    _plan(win)
    win._commit_if_changed()                 # settle the debounce
    win.save_path(str(tmp_path / "plan.json"))
    assert not win._is_dirty()               # precondition: saved == clean
    before_doc = win.snapshot()
    before_counts = _counts(win)
    before_status = win.statusBar().currentMessage()

    _close_modal_soon()
    with warnings.catch_warnings():
        warnings.simplefilter("error")       # ANY warning fails the test
        win.show_3d_view()

    assert not win._is_dirty(), "the 3D view dirtied the document"
    assert win.snapshot() == before_doc, "the 3D view changed the document"
    assert _counts(win) == before_counts, "the 3D view changed the scene"
    # the status line may carry one of the VIEWER's own messages (this box has
    # no GPU, so the renderer legitimately may not come up) but must never
    # carry an EDIT-path report -- that channel belongs to the gesture that
    # changed something, and nothing here did
    msg = win.statusBar().currentMessage()
    assert msg == before_status or msg.startswith("3D view"), (
        f"the 3D view spoke in the edit channel: {msg!r}")


def test_the_suppression_is_scoped_to_the_one_message(win, monkeypatch):
    """The popup silences the walk's unwelded-ends line and NOTHING else.

    The read-only receipt above cannot see this: an inner blanket ignore
    satisfies its outer `simplefilter("error")` exactly as well as a narrow
    one does. So this test raises a DIFFERENT warning from inside the same
    call and requires it to survive -- a blanket suppression is
    `except ValueError: continue` wearing a different hat, and the walk's
    other reports are how the app tells the truth about a document."""
    _plan(win)
    real = win.design_document

    def _also_warns():
        warnings.warn("unrelated: something else the walk found",
                      stacklevel=2)
        return real()

    monkeypatch.setattr(win, "design_document", _also_warns)
    _close_modal_soon()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        win.show_3d_view()
    msgs = [str(w.message) for w in caught]
    assert any(m.startswith("unrelated:") for m in msgs), (
        f"an unrelated warning was swallowed by the suppression: {msgs}")


def test_it_degrades_when_the_optional_stack_is_missing(win, monkeypatch):
    """A missing optional dependency REPORTS; it never raises. Simulated by
    making the import fail, so the test is honest on a machine that has the
    stack installed as well as one that does not."""
    import builtins
    real = builtins.__import__

    def _no_quick3d(name, *a, **k):
        if "fp3dq" in name or "QtQuick3D" in name:
            raise ImportError("simulated: no Qt Quick 3D")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_quick3d)
    assert win.show_3d_view() is None        # returns, does not raise
    monkeypatch.undo()
    assert "requirements-viewer.txt" in win.statusBar().currentMessage()


def test_the_popup_uses_the_save_paths_producer(win, monkeypatch):
    """No second producer: the popup reads `design_document()`, the very
    method `_write_plan` writes. Pinned because a viewer quietly growing its
    own document walk is how two definitions of a plan begin."""
    _plan(win)
    seen = {}
    real = win.design_document

    def _spy():
        seen["called"] = seen.get("called", 0) + 1
        return real()

    monkeypatch.setattr(win, "design_document", _spy)
    _close_modal_soon()
    win.show_3d_view()
    assert seen.get("called") == 1, "the popup did not use design_document()"


def test_the_editor_launches_with_no_qtquick3d(monkeypatch):
    """SIMULATE the optional stack being absent and prove the startup path
    survives it -- the failure that would otherwise turn a missing extra into
    a dead editor.

    Exercised for real, not read off the source: the import is made to fail
    exactly as it would on a machine without Qt Quick 3D, and the startup
    call must RETURN (reporting False) rather than raise."""
    import builtins

    from floorplanner import app
    real = builtins.__import__

    def _no_quick3d(name, *a, **k):
        if "QtQuick3D" in name:
            raise ImportError("simulated: no Qt Quick 3D")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_quick3d)
    assert app.set_3d_surface_format() is False   # returns; does not raise
    monkeypatch.undo()
    # ...and with the stack present it really does set the format
    assert app.set_3d_surface_format() is True


def test_the_surface_format_precedes_the_qapplication():
    """The ordering half, which no runtime test can observe (running main()
    would build a second QApplication): Qt reads the default surface format
    at GUI init, so a call after the QApplication is silently too late."""
    import inspect

    from floorplanner import app
    src = inspect.getsource(app.main)
    call = src.index("set_3d_surface_format()")
    qapp = src.index("QApplication(sys.argv)")
    assert call < qapp, "the surface format must precede the QApplication"


def test_the_qml_document_ships_beside_the_module():
    """The scene graph is a real .qml on disk (not an inline temp file), and
    it is packaged -- a viewer whose QML is missing renders nothing."""
    from pathlib import Path

    from floorplanner.viewer import fp3dq
    p = Path(fp3dq.QML_PATH)
    assert p.is_file() and p.name == "scene.qml"
    assert "View3D" in p.read_text(encoding="utf-8")
    # read as TEXT, not via tomllib: this project supports py3.10, where
    # tomllib does not exist (caught by CI's 3.10 leg, not by the 3.13 box
    # it was written on -- which is exactly what that leg is for)
    root = Path(__file__).resolve().parent.parent
    toml = (root / "pyproject.toml").read_text(encoding="utf-8")
    line = next((ln for ln in toml.splitlines()
                 if ln.strip().startswith('"floorplanner.viewer"')), None)
    assert line is not None, "floorplanner.viewer has no package-data entry"
    assert "scene.qml" in line, line
