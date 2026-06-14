"""Undo / redo: full-document snapshot history covering canvas operations.

The debounce QTimer that normally commits a snapshot never fires under the
headless test (no event loop), so tests call win._commit_if_changed()
directly to mark a discrete step -- exactly what the timer does live."""

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.io


def _nfurn(win, fp):
    return sum(isinstance(i, fp.FurnishingItem) for i in win.scene.items())


def _nwall(win, fp):
    return sum(isinstance(i, fp.WallItem) for i in win.scene.items())


def test_undo_redo_add_furnishing(fp, qapp, win):
    win.scene.addItem(fp.make_furnishing("sofa", QPointF(100, 100)))
    win._commit_if_changed()
    assert _nfurn(win, fp) == 1
    win.undo()
    assert _nfurn(win, fp) == 0
    win.redo()
    assert _nfurn(win, fp) == 1


def test_undo_buttons_reflect_history(fp, qapp, win):
    assert not win.a_undo.isEnabled()
    assert not win.a_redo.isEnabled()
    win.scene.addItem(fp.make_furnishing("sofa", QPointF(0, 0)))
    win._commit_if_changed()
    assert win.a_undo.isEnabled()
    assert not win.a_redo.isEnabled()
    win.undo()
    assert not win.a_undo.isEnabled()
    assert win.a_redo.isEnabled()


def test_multistep_undo_in_order(fp, qapp, win):
    win.scene.addItem(fp.make_furnishing("sofa", QPointF(0, 0)))
    win._commit_if_changed()                       # step 1
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    win._commit_if_changed()                       # step 2
    assert (_nfurn(win, fp), _nwall(win, fp)) == (1, 1)
    win.undo()                                     # undo the wall
    assert (_nfurn(win, fp), _nwall(win, fp)) == (1, 0)
    win.undo()                                     # undo the furnishing
    assert (_nfurn(win, fp), _nwall(win, fp)) == (0, 0)


def test_undo_restores_move(fp, qapp, win):
    f = fp.make_furnishing("sofa", QPointF(100, 100))
    win.scene.addItem(f)
    win._commit_if_changed()
    f.setPos(QPointF(300, 320))
    win.undo()
    moved = [i for i in win.scene.items() if isinstance(i, fp.FurnishingItem)]
    assert len(moved) == 1
    assert moved[0].pos().x() == pytest.approx(100, abs=1)
    assert moved[0].pos().y() == pytest.approx(100, abs=1)


def test_undo_restores_stair_config(fp, qapp, win):
    st = fp.make_furnishing("stairs", QPointF(60, 60))
    win.scene.addItem(st)
    win._commit_if_changed()
    st.flight, st.turn, st.direction = "half", "right", "down"
    st._recompute()
    win.undo()
    stairs = [i for i in win.scene.items() if isinstance(i, fp.StairItem)]
    assert stairs and stairs[0].extra_state()["flight"] == "full"


def test_new_change_clears_redo(fp, qapp, win):
    win.scene.addItem(fp.make_furnishing("sofa", QPointF(0, 0)))
    win._commit_if_changed()
    win.undo()
    assert win.a_redo.isEnabled()
    win.scene.addItem(fp.make_furnishing("armchair", QPointF(50, 50)))
    win._commit_if_changed()
    assert not win.a_redo.isEnabled()      # a fresh change drops the redo tail


def test_reset_undo_clears_history(fp, qapp, win):
    win.scene.addItem(fp.make_furnishing("sofa", QPointF(0, 0)))
    win._commit_if_changed()
    assert win.a_undo.isEnabled()
    win._reset_undo()
    assert not win.a_undo.isEnabled()
    assert not win.a_redo.isEnabled()


def test_undo_with_empty_history_is_noop(fp, qapp, win):
    win.undo()                              # must not raise
    win.redo()
    assert _nfurn(win, fp) == 0
