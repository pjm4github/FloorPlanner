"""Undo / redo: full-document snapshot history covering canvas operations.

The debounce QTimer that normally commits a snapshot never fires under the
headless test (no event loop), so tests call win._commit_if_changed()
directly to mark a discrete step -- exactly what the timer does live."""

import json

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


# --------------------------------------------------------------------------
# P2.3: the snapshot payload is the CANONICAL v5 document
# --------------------------------------------------------------------------
def test_snapshot_is_a_canonical_v5_document(fp, qapp, win, make_room):
    from floorplanner.design.canonical import canonicalize
    make_room(win.scene, 0, 0, 144, 120, "Den")
    doc = win.snapshot()
    assert doc["format"] == "floorplanner-design" and doc["version"] == 5
    assert canonicalize(json.loads(json.dumps(doc))) == doc, "not canonical"


def test_snapshot_excludes_view_state(fp, qapp, win, make_room):
    """`active_floor`, `provenance` and unmodelled document settings are window
    state, not scene state. Keeping active_floor out is what stops a floor
    switch from becoming an undo step."""
    make_room(win.scene, 0, 0, 144, 120, "Den")
    win.floors = [fp.Floor("default"), fp.Floor("Upper")]
    win._sync_floor_state()
    before = win.snapshot()
    win.switch_floor("Upper")
    assert win.snapshot() == before, "switching floors changed the document"
    assert "active_floor" not in before["settings"]
    assert "provenance" not in before


def test_snapshot_is_granularity_invariant(fp, qapp, win):
    """THE reason P2.3's edge-granular restore is safe: the canonical document
    is a quotient over how the scene subdivides a wall run. One long wall and
    two collinear halves meeting at the same junction planarise to the SAME
    document, so scene wall-count is presentation, not document, state."""
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(0, 0), QPointF(480, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(240, 0), QPointF(240, 200), "interior"))
    fp.rebuild_all_walls(sc)
    whole = win.snapshot()

    sc.clear()                                   # same plan, drawn in halves
    sc.addItem(fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(240, 0), QPointF(480, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(240, 0), QPointF(240, 200), "interior"))
    fp.rebuild_all_walls(sc)
    assert win.snapshot() == whole


def test_undo_does_not_dirty_a_saved_plan(fp, qapp, win, make_room, tmp_path):
    """Dirty is defined on the canonical document, so a restore that changes
    only wall granularity must not read as an unsaved edit."""
    make_room(win.scene, 0, 0, 144, 120, "Den")
    win._commit_if_changed()          # the room is the baseline, not the empty
    win.save_path(str(tmp_path / "p.json"))   # scene MainWindow started with
    assert not win._is_dirty()
    it = fp.FurnishingItem(fp.furnishing_catalog()[0]["id"], QPointF(60, 60))
    win.scene.addItem(it)
    win._commit_if_changed()
    assert win._is_dirty()
    win.undo()
    assert not win._is_dirty(), "undo back to the saved plan still reads dirty"


def test_undo_keeps_the_reference_image(fp, qapp, win, make_room, tmp_path):
    """The backdrop retention deferred from P1.5. Undo restores through
    `apply_design_to_scene` now, and its `scene.clear()` would take the tracing
    image with it."""
    from tests.test_extract import _make_plan_png
    win.start_image_import(str(_make_plan_png(tmp_path / "bd.png")))
    n = sum(1 for i in win.scene.items()
            if isinstance(i, fp.ReferenceImageItem))
    assert n == 1
    make_room(win.scene, 0, 0, 144, 120, "Den")
    win._commit_if_changed()
    win.undo()
    assert sum(1 for i in win.scene.items()
               if isinstance(i, fp.ReferenceImageItem)) == 1, \
        "undo deleted the backdrop"


def test_closing_a_window_stops_its_dirty_timer(fp, qapp):
    """DEFECT 29. `close()` hid the window and left the 180 ms debounce
    running, so a closed window went on walking the WHOLE document -- snapshot,
    verify, and (before defect 26's guard) able to abort the process -- forever,
    for a window the user believes is gone.

    Built directly rather than through the `win` fixture, because the fixture
    now DESTROYS its window (defect 28) and would hide the app behaviour under
    test."""
    w = fp.MainWindow()
    try:
        w.scene.addItem(fp.make_furnishing("sofa", QPointF(100, 100)))
        qapp.processEvents()
        # the precondition, asserted rather than assumed: a test that never
        # started the timer would pass this whatever close() did
        assert w._dirty_timer.isActive(), "the edit did not start the debounce"
        undo_depth = len(w._undo_stack)

        w.close()

        assert not w._dirty_timer.isActive(), \
            "a closed window is still walking the document every 180 ms"
        qapp.processEvents()
        assert len(w._undo_stack) == undo_depth, \
            "the closed window committed a snapshot after closing"
    finally:
        from conftest import dispose_window
        dispose_window(w)


def test_undo_after_grouping_restores_the_plan(fp, qapp, win, make_room):
    """What P2.3 must preserve. The GROUP dissolving is expected until P4.5 --
    the bridge emits groups: [] because mapping a grouped wall onto its split
    segments is undefined while grouping still copies walls. Group survival is
    held by test_characterization::test_group_survives_roundtrip."""
    room = make_room(win.scene, 0, 0, 144, 120, "Den")
    win._reset_undo()
    before = win.snapshot()
    win.scene.clearSelection()
    for it in [room, *room.walls]:
        it.setSelected(True)
    win.group_selected()
    g = next(i for i in win.scene.items() if isinstance(i, fp.GroupItem))
    g.setPos(120, 60)
    g.bake()
    win.undo()
    assert win.snapshot() == before, "undo did not restore the pre-group plan"
