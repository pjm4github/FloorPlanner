"""Multi-floor plans (Phase 1): per-item floor tagging, floor isolation in the
geometry hot paths, gray rendering/visibility, the menu/status ops, and the
undo/dirty separation of the active-floor view state."""
import json

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.rooms


def _rect(fp, scene, x, y, w, h, wall_type="interior"):
    cs = [QPointF(x, y), QPointF(x + w, y),
          QPointF(x + w, y + h), QPointF(x, y + h)]
    for i in range(4):
        scene.addItem(fp.WallItem(cs[i], cs[(i + 1) % 4], wall_type))
    fp.rebuild_all_walls(scene)


# --------------------------------------------------------------------------
# Per-item floor tagging + display mode
# --------------------------------------------------------------------------
def test_new_items_tag_active_floor(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    assert w.floor == fp.DEFAULT_FLOOR
    fp.set_floor_state(active="Upper")
    w2 = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    assert w2.floor == "Upper"


def test_floor_display_mode(fp):
    fp.set_floor_state(active="default", reference={"Ref"}, show_others=False)
    assert fp.floor_display_mode("default") == "active"
    assert fp.floor_display_mode("Ref") == "reference"
    assert fp.floor_display_mode("Other") == "hidden"
    fp.set_floor_state(show_others=True)
    assert fp.floor_display_mode("Other") == "ghost"


def test_apply_floor_visibility(fp, win):
    wd = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    win.scene.addItem(wd)
    win.floors = [fp.Floor("default"), fp.Floor("Upper")]
    win.active_floor = "Upper"
    win._sync_floor_state()                            # switch, then draw on Upper
    wu = fp.WallItem(QPointF(0, 200), QPointF(120, 200), "interior")
    win.scene.addItem(wu)
    win._sync_floor_state()
    assert not wd.isVisible() and not wd.isEnabled()    # other floor: hidden
    assert wu.isVisible() and wu.isEnabled()            # active: editable
    win.floors[0].reference = True
    win._sync_floor_state()
    assert wd.isVisible() and not wd.isEnabled()        # reference: visible, off


# --------------------------------------------------------------------------
# Floor isolation in the geometry hot paths
# --------------------------------------------------------------------------
def test_walls_do_not_coalesce_across_floors(fp, win):
    sc = win.scene
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    a.floor = "default"
    sc.addItem(a)
    b = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b.floor = "Upper"
    sc.addItem(b)
    fp.merge_all(sc)
    fp.rebuild_all_walls(sc)
    walls = [w for w in sc.items() if isinstance(w, fp.WallItem)]
    assert len(walls) == 2                              # same coords, no merge


def test_rooms_isolated_per_floor(fp, win):
    sc = win.scene
    _rect(fp, sc, 100, 100, 120, 96)                   # default floor
    r1 = fp.detect_room(sc, QPointF(160, 148))
    assert r1 is not None
    win.floors = [fp.Floor("default"), fp.Floor("Upper")]
    win.active_floor = "Upper"
    win._sync_floor_state()
    _rect(fp, sc, 100, 100, 120, 96)                   # same coords on Upper
    walls = [w for w in sc.items() if isinstance(w, fp.WallItem)]
    assert len(walls) == 8                             # 4 + 4, not merged
    r2 = fp.detect_room(sc, QPointF(160, 148))         # detect on the Upper floor
    assert r2 is not None
    assert r2[1] == pytest.approx(r1[1])               # same area, own walls


# --------------------------------------------------------------------------
# Serialization v4 (Qt round-trip) + active-floor persistence
# --------------------------------------------------------------------------
def test_serialize_round_trip_two_floors(fp, win, tmp_path):
    sc = win.scene
    _rect(fp, sc, 100, 100, 120, 96)
    win.floors = [fp.Floor("default"), fp.Floor("Upper")]
    win.active_floor = "Upper"
    win._sync_floor_state()
    _rect(fp, sc, 300, 100, 120, 96)
    data = json.loads(json.dumps(win.serialize()))
    assert data["version"] == 4
    assert {f["name"] for f in data["floors"]} == {"default", "Upper"}
    assert {w["floor"] for w in data["walls"]} == {"default", "Upper"}
    assert "active_floor" not in data                  # view state, not serialized
    p = tmp_path / "two.json"
    win.save_path(str(p))
    saved = json.loads(p.read_text())
    # P2.2: the file is v5 now, and the v5 ROOT is a closed schema, so the
    # remembered active floor moved from the top level into `settings` -- the
    # designated open bag. Same in-on-load / out-on-save arrangement as v4;
    # only its address changed, and it is still absent from serialize() above.
    assert saved["format"] == "floorplanner-design"
    assert saved["settings"]["active_floor"] == "Upper"   # the FILE remembers it
    win2 = fp.MainWindow()
    try:
        win2.load_path(str(p))
        assert win2.active_floor == "Upper"
        assert {f.name for f in win2.floors} == {"default", "Upper"}
    finally:
        win2.close()


# --------------------------------------------------------------------------
# Undo / dirty separation: switching is view state, roster edits are not
# --------------------------------------------------------------------------
def test_switch_floor_is_not_undoable_or_dirty(fp, win):
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    fp.rebuild_all_walls(win.scene)
    win.floors = [fp.Floor("default"), fp.Floor("Upper")]
    win._reset_undo()                                  # clean baseline
    before = win.serialize()
    n_undo = len(win._undo_stack)
    win.switch_floor("Upper")
    assert win.serialize() == before                   # snapshot unchanged
    assert len(win._undo_stack) == n_undo              # no undo step
    assert not win._is_dirty()                         # not dirty


def test_floor_roster_edit_is_dirty(fp, win):
    win._reset_undo()
    assert not win._is_dirty()
    win.new_floor_named("Upper")                       # add a floor
    assert win._is_dirty()                             # roster change -> dirty
    assert any(f.name == "Upper" for f in win.floors)


def test_delete_floor_removes_its_items(fp, win):
    sc = win.scene
    _rect(fp, sc, 100, 100, 120, 96)                   # default
    win.new_floor_named("Upper")                       # switches to Upper
    _rect(fp, sc, 100, 100, 120, 96)                   # Upper walls
    assert len([w for w in sc.items() if isinstance(w, fp.WallItem)]) == 8
    win.delete_floor("Upper")
    walls = [w for w in sc.items() if isinstance(w, fp.WallItem)]
    assert len(walls) == 4 and all(w.floor == "default" for w in walls)
    assert win.active_floor == "default"


def test_v3_file_loads_as_single_default_floor(fp, win):
    doc = {"format": fp.FILE_FORMAT, "version": 3, "units": "inches",
           "settings": {}, "walls": [
               {"type": "interior", "p1": [0, 0], "p2": [120, 0],
                "rooms": [], "openings": []}],
           "rooms": [], "furnishings": []}
    win.load_data(doc)
    assert [f.name for f in win.floors] == [fp.DEFAULT_FLOOR]
    assert win.active_floor == fp.DEFAULT_FLOOR
    walls = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    assert walls and all(w.floor == fp.DEFAULT_FLOOR for w in walls)


def test_refresh_rooms_cmd_spares_inactive_floor_rooms(fp, win, make_room):
    # defect 2 (P0.5): refresh_rooms_cmd tests room_walled against the ACTIVE
    # floor's walls, so a room parked on another floor looked unwalled and was
    # deleted. It must only consider active-floor rooms.
    den = make_room(win.scene, 0, 0, 120, 96, "Den")     # on default (active)
    assert den.floor == fp.DEFAULT_FLOOR
    win.new_floor_named("Upper")                          # switch active -> Upper
    assert win.active_floor == "Upper"
    win.refresh_rooms_cmd()
    rooms = [r for r in win.scene.items() if isinstance(r, fp.RoomItem)]
    assert any(r.name == "Den" and r.floor == fp.DEFAULT_FLOOR for r in rooms), \
        "refresh_rooms_cmd deleted an inactive-floor room"


def test_floor_display_stacking(fp, win):
    # P4.2: floors paint in z BANDS -- the ACTIVE floor's band is 0 (so a
    # newly drawn item lands on top with nothing to re-apply) and ghosts sit
    # on negative bands in the user's display order, arranged per floor via
    # Floors > <floor> > Move to front/back (display). The band rides as a
    # DELTA on each top-level item's z, so within-floor z machinery
    # (raise_to_front's running max) is untouched.
    from PyQt6.QtCore import QPointF
    sc = win.scene
    w_default = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    sc.addItem(w_default)
    win.new_floor_named("Mid")
    w_mid = fp.WallItem(QPointF(0, 24), QPointF(120, 24), "interior")
    sc.addItem(w_mid)
    win.new_floor_named("Top")
    w_top = fp.WallItem(QPointF(0, 48), QPointF(120, 48), "interior")
    sc.addItem(w_top)
    win.show_other_floors = True
    win._sync_floor_state()
    # active (Top) is band 0 -- strictly above both ghosts
    assert w_top.zValue() > w_mid.zValue()
    assert w_top.zValue() > w_default.zValue()
    # a NEW item on the active floor needs no re-sync to be on top
    w_new = fp.WallItem(QPointF(0, 72), QPointF(120, 72), "interior")
    sc.addItem(w_new)
    assert w_new.zValue() > w_mid.zValue()
    # ghosts follow the stack: default joined first, so it sits below Mid;
    # move default to the front (of the ghosts) and the order flips
    assert w_default.zValue() < w_mid.zValue()
    win.floor_display_front("default")
    assert w_default.zValue() > w_mid.zValue()
    assert w_top.zValue() > w_default.zValue()      # active still on top
    win.floor_display_back("default")
    assert w_default.zValue() < w_mid.zValue()
    # switching the active floor re-tops it, whatever the stack says
    win.switch_floor("default")
    assert w_default.zValue() > w_mid.zValue()
    assert w_default.zValue() > w_top.zValue()
    # within-floor z survived the banding round trips exactly
    assert w_mid.zValue() - w_mid._floor_band == pytest.approx(fp.WALL_Z)
    # the per-floor submenu carries the two display actions
    win._rebuild_floor_menu()
    subs = [a.menu() for a in win.m_floors.actions() if a.menu()]
    texts = [a.text() for a in subs[0].actions()]
    assert "Move to front (display)" in texts
    assert "Move to back (display)" in texts
