"""JSON serialize/load and CSV room import/export round-trips."""
import json

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.io


def test_dirty_tracking_for_unsaved_changes(fp, win, tmp_path):
    sc = win.scene
    assert win._is_dirty() is False              # fresh blank plan is clean
    sc.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    fp.rebuild_all_walls(sc)
    assert win._is_dirty() is True               # an edit makes it dirty
    win.save_path(str(tmp_path / "p.json"))
    assert win._is_dirty() is False              # saving clears it
    sc.addItem(fp.WallItem(QPointF(0, 60), QPointF(120, 60), "interior"))
    fp.rebuild_all_walls(sc)
    assert win._is_dirty() is True               # a further edit -> dirty again
    win.clear_plan()
    assert win._is_dirty() is False              # New resets the clean baseline


def test_unchanged_scene_is_not_falsely_dirty(fp, win, make_room):
    # serialize() of a static scene is stable, so no false "unsaved" prompt
    make_room(win.scene, 0, 0, 144, 120, "Den")
    win._saved_state = win.serialize()
    assert win._is_dirty() is False


def test_json_roundtrip(fp, win, make_room, first_furnishing, counts):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)
    data = win.serialize()

    w2 = fp.MainWindow()
    try:
        w2.load_data(json.loads(json.dumps(data)))
        assert counts(w2.scene) == before
    finally:
        w2.close()


def test_settings_roundtrip(fp, win):
    fp.SETTINGS["wall_snap_in"] = 12
    data = win.serialize()
    fp.SETTINGS["wall_snap_in"] = 6
    win.load_data(json.loads(json.dumps(data)))
    assert fp.SETTINGS["wall_snap_in"] == 12


def test_csv_import_creates_room(fp, win, tmp_path):
    csv = tmp_path / "rooms.csv"
    csv.write_text(
        "Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes\n"
        "Den,Bedroom,12,10,5,5,cozy\n", encoding="utf-8")
    win._import_rooms(str(csv), interactive=False)
    assert win._import_errors == []
    rooms = [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]
    assert any(r.name == "Den" for r in rooms)


def test_csv_import_reports_bad_row(fp, win, tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes\n"
        ",Bedroom,12,10,,,\n", encoding="utf-8")     # missing Name
    win._import_rooms(str(csv), interactive=False)
    assert len(win._import_errors) == 1


def test_csv_import_grows_canvas_for_outside_room(fp, win, tmp_path):
    # a room located far beyond the default 100'x70' canvas
    csv = tmp_path / "big.csv"
    csv.write_text(
        "Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes\n"
        "Far,Garage,20,20,150,40,\n", encoding="utf-8")
    win._import_rooms(str(csv), interactive=False)
    assert win._import_errors == []
    c = fp.canvas_rect()
    # must now be wide enough to contain the room (X_loc 150' + 20' = 170')
    assert c.width() / fp.FOOT >= 170
    assert c.width() / fp.FOOT > 100        # actually grew past default
    rooms = [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]
    assert any(r.name == "Far" for r in rooms)


def test_csv_import_does_not_shrink_canvas(fp, win, tmp_path):
    csv = tmp_path / "small.csv"
    csv.write_text(
        "Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes\n"
        "Den,Bedroom,12,10,5,5,\n", encoding="utf-8")
    win._import_rooms(str(csv), interactive=False)
    c = fp.canvas_rect()
    assert c.width() / fp.FOOT == 100       # unchanged default
    assert c.height() / fp.FOOT == 70


def test_csv_import_rejects_typo_beyond_max(fp, win, tmp_path):
    csv = tmp_path / "typo.csv"
    csv.write_text(
        "Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes\n"
        "Oops,,9000,20,0,0,\n", encoding="utf-8")   # 9000' wide = typo
    win._import_rooms(str(csv), interactive=False)
    assert len(win._import_errors) == 1
    assert "limit" in win._import_errors[0]
    # canvas not blown up past the cap
    assert fp.canvas_rect().width() <= fp.MAX_CANVAS_IN
    assert not [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]


def test_csv_roundtrip(fp, win, tmp_path):
    src = tmp_path / "in.csv"
    src.write_text(
        "Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes\n"
        "Den,Bedroom,12,10,5,5,\n"
        "Shop,Shop,16,12,40,5,\n", encoding="utf-8")
    win._import_rooms(str(src), interactive=False)
    assert win._import_errors == []
    n_in = sum(isinstance(i, fp.RoomItem) for i in win.scene.items())

    out = tmp_path / "out.csv"
    win._export_rooms(str(out), interactive=False)

    w2 = fp.MainWindow()
    try:
        w2._import_rooms(str(out), interactive=False)
        n_out = sum(isinstance(i, fp.RoomItem) for i in w2.scene.items())
        assert n_out == n_in == 2
    finally:
        w2.close()
