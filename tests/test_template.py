"""One-room templates (P4.4): section 4's Duplicate a room, Copy/Paste, and
File > Save / Load template room -- three workflows over ONE mechanism
(room -> one-room document -> floating room).
"""
import json
import warnings

import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.design.bridge import design_from_scene
from floorplanner.design.template import (
    merge_room_document, room_subdocument, template_offset_to,
)
from floorplanner.design.validate import check

pytestmark = pytest.mark.rooms


def _make(scene, x, y, w, h, name, skip=None):
    corners = [QPointF(x, y), QPointF(x + w, y),
               QPointF(x + w, y + h), QPointF(x, y + h)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        if skip and any((a == s[0] and b == s[1]) or (a == s[1] and b == s[0])
                        for s in skip):
            continue
        scene.addItem(fp.WallItem(a, b, "interior"))
    fp.rebuild_all_walls(scene)
    centre = QPointF(x + w / 2, y + h / 2)
    res = fp.detect_room(scene, centre)
    assert res is not None
    room = fp.RoomItem(fp.unique_room_name(scene, name), centre,
                       res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


def _walk(win):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return design_from_scene(win).to_dict()


def _rooms(win):
    return [r for r in win.scene.items() if isinstance(r, fp.RoomItem)]


# --------------------------------------------------------------------------
# the document half: subdocument + merge are pure dict operations
# --------------------------------------------------------------------------
def test_a_template_is_a_valid_one_room_design(win):
    room = _make(win.scene, 0, 0, 144, 120, "Den")
    tmpl = win.room_template(room)
    assert check(tmpl, deep=True) == [], check(tmpl, deep=True)
    assert len(tmpl["rooms"]) == 1 and len(tmpl["levels"]) == 1
    assert len(tmpl["walls"]) == 4
    assert tmpl["rooms"][0]["placement"]["state"] == "floating"
    # every reference resolves INSIDE the template (I2): that is what makes
    # the subset closed, and why a template is cut from a floating room
    vids = {v["id"] for v in tmpl["vertices"]}
    wids = {w["id"] for w in tmpl["walls"]}
    for w in tmpl["walls"]:
        assert w["v1"] in vids and w["v2"] in vids
    for e in tmpl["rooms"][0]["outline"]:
        assert e["v"] in vids
        assert e.get("wall") is None or e["wall"] in wids


def test_templating_a_placed_room_leaves_the_plan_byte_identical(win):
    # a placed room is cut out through the REAL ops (extract -> template ->
    # join), so the zero-offset round trip must return the document exactly
    a = _make(win.scene, 0, 0, 120, 120, "A")
    _make(win.scene, 120, 0, 120, 120, "B",
          skip=[(QPointF(120, 0), QPointF(120, 120))])
    before = win.snapshot()
    tmpl = win.room_template(a)
    assert check(tmpl, deep=True) == []
    assert a.placement_state == "placed", "the source must be re-joined"
    assert win.snapshot() == before, (
        "templating a placed room changed the plan -- the extract/join round "
        "trip is not neutral")


def test_a_template_of_a_placed_room_takes_only_its_own_share(win):
    # the party wall runs the full height of BOTH rooms; the template must
    # carry only the stretch along A's own edge (extract's copy-trim), and
    # the source plan keeps every wall it had
    a = _make(win.scene, 0, 0, 120, 240, "A")
    _make(win.scene, 120, 0, 120, 120, "B",
          skip=[(QPointF(120, 0), QPointF(120, 120))])
    n_before = sum(1 for w in win.scene.items() if isinstance(w, fp.WallItem))
    tmpl = win.room_template(a)
    assert len(tmpl["walls"]) == 4
    pos = {v["id"]: (v["x"], v["y"]) for v in tmpl["vertices"]}
    for w in tmpl["walls"]:                  # nothing sticks out past A
        for vid in (w["v1"], w["v2"]):
            x, y = pos[vid]
            assert -0.5 <= x <= 120.5 and -0.5 <= y <= 240.5
    assert sum(1 for w in win.scene.items()
               if isinstance(w, fp.WallItem)) == n_before


def test_merge_lands_the_room_floating_on_the_target_level(win):
    room = _make(win.scene, 0, 0, 120, 120, "Den")
    tmpl = win.room_template(room)
    base = win.design_document()
    merged = merge_room_document(base, tmpl, base["levels"][0]["id"],
                                 dx=600.0, dy=0.0, name="Copy")
    assert check(merged, deep=True) == [], check(merged, deep=True)
    names = [r["name"] for r in merged["rooms"]]
    assert names.count("Copy") == 1 and "Den" in names
    copy = next(r for r in merged["rooms"] if r["name"] == "Copy")
    assert copy["placement"]["state"] == "floating"
    assert copy["placement"]["extracted_from"] is None
    ids = [row["id"] for coll in ("vertices", "walls", "rooms", "furnishings")
           for row in merged.get(coll) or []]
    assert len(ids) == len(set(ids)), "the merge minted a colliding id"


def test_subdocument_refuses_a_placed_room(win):
    _make(win.scene, 0, 0, 120, 120, "Den")
    with pytest.raises(ValueError, match="not floating"):
        room_subdocument(_walk(win), "Den")


def test_offset_lands_the_centroid_on_the_point(win):
    room = _make(win.scene, 0, 0, 144, 120, "Den")
    tmpl = win.room_template(room)
    dx, dy = template_offset_to(tmpl, 500.0, 400.0)
    assert (72.0 + dx, 60.0 + dy) == pytest.approx((500.0, 400.0))


# --------------------------------------------------------------------------
# the workflows
# --------------------------------------------------------------------------
def test_duplicate_room_lands_a_floating_copy(win, first_furnishing):
    room = _make(win.scene, 0, 0, 144, 120, "Den")
    door = fp.OpeningItem(room.walls[0], "door", "3280",
                          room.walls[0].length() / 2)
    room.walls[0].openings.append(door)
    furn = fp.FurnishingItem(first_furnishing, QPointF(48, 48), 0)
    win.scene.addItem(furn)
    fp.rebuild_all_walls(win.scene)
    area, n_walls = room.area_sqft, len(room.walls)

    copy = win.duplicate_room(room, at=QPointF(600, 400))

    assert copy is not None and copy.name != "Den"
    assert copy.placement_state == "floating"
    assert copy.area_sqft == pytest.approx(area)
    assert len(copy.walls) == n_walls
    assert copy.anchor.x() == pytest.approx(600, abs=1)
    # the source survives unchanged, and the copy carries the door + furnishing
    src = next(r for r in _rooms(win) if r.name == "Den")
    assert src.placement_state == "placed"
    assert src.area_sqft == pytest.approx(area)
    assert sum(len(w.openings) for w in copy.walls) == 1
    furns = [f for f in win.scene.items() if isinstance(f, fp.FurnishingItem)]
    assert len(furns) == 2, "the duplicate must carry a copy of the furnishing"
    assert check(_walk(win), deep=True) == []


def test_copy_paste_round_trip(win):
    room = _make(win.scene, 0, 0, 120, 120, "Den")
    area = room.area_sqft
    win.room_clipboard = win.room_template(room)
    win.paste_room(QPointF(600, 300))
    rooms = _rooms(win)
    assert len(rooms) == 2
    pasted = next(r for r in rooms if r.name != "Den")
    assert pasted.placement_state == "floating"
    assert pasted.area_sqft == pytest.approx(area)
    assert check(_walk(win), deep=True) == []


@pytest.mark.io
def test_save_and_load_template_room(win, tmp_path):
    """THE P4.4 ACCEPTANCE: a one-room file validates against the schema and
    loads into an existing design as a floating room."""
    from floorplanner.design.validate import schema_errors
    from tests.conftest import dispose_window

    room = _make(win.scene, 0, 0, 144, 120, "Den")
    fp.extract_room(win.scene, room)             # Save is floating-only
    path = tmp_path / "den.room.json"
    win.save_template_path(str(path), room)

    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["format"] == "floorplanner-design" and doc["version"] == 5
    assert schema_errors(doc) == [], schema_errors(doc)
    assert check(doc, deep=True) == []
    assert len(doc["rooms"]) == 1

    # ...into an EXISTING design
    win2 = fp.MainWindow()
    try:
        _make(win2.scene, 0, 0, 240, 180, "Existing")
        before = len(_rooms(win2))
        loaded = win2.load_template_path(str(path), at=QPointF(600, 400))
        assert loaded is not None
        assert loaded.placement_state == "floating", (
            "an inserted template room must arrive floating")
        assert len(_rooms(win2)) == before + 1
        assert loaded.area_sqft == pytest.approx(120.0, abs=0.5)
        assert len(loaded.walls) == 4
        assert check(_walk(win2), deep=True) == []
        # ...and the design it landed in is untouched
        keep = next(r for r in _rooms(win2) if r.name == "Existing")
        assert keep.placement_state == "placed"
    finally:
        dispose_window(win2)


def test_a_template_inserts_repeatedly(win):
    room = _make(win.scene, 0, 0, 120, 120, "Den")
    tmpl = win.room_template(room)
    a = win.insert_room_template(tmpl, at=QPointF(400, 100))
    b = win.insert_room_template(tmpl, at=QPointF(400, 400))
    assert a is not None and b is not None and a.name != b.name
    assert len(_rooms(win)) == 3
    assert check(_walk(win), deep=True) == []
