"""Shuffle mode (P4.3): the editing_modes flags — the effective-flag rule,
document emit/apply, the toolbar toggle, and the explicit-join exemption."""
import json

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene

pytestmark = pytest.mark.io


# --------------------------------------------------------------------------
# editing_enabled: shuffle implies the three auto_* passes off
# --------------------------------------------------------------------------
def test_shuffle_implies_every_auto_pass_off(fp):
    for flag in ("auto_coalesce", "auto_weld", "auto_bind"):
        assert fp.editing_enabled(flag), "defaults must read enabled"
    fp.SETTINGS["auto_weld"] = False
    assert not fp.editing_enabled("auto_weld")
    assert fp.editing_enabled("auto_coalesce"), "flags are independent"
    fp.SETTINGS["auto_weld"] = True
    fp.SETTINGS["shuffle"] = True
    for flag in ("auto_coalesce", "auto_weld", "auto_bind"):
        assert not fp.editing_enabled(flag), "shuffle implies all off"
        assert fp.SETTINGS[flag] is True, (
            "shuffle must not REWRITE the stored flags -- leaving shuffle "
            "restores exactly the passes the user had on")


# --------------------------------------------------------------------------
# emit / apply: the document's settings.editing block carries the live flags
# --------------------------------------------------------------------------
def test_editing_block_emits_from_live_settings(fp, win):
    fp.SETTINGS["shuffle"] = True
    fp.SETTINGS["auto_weld"] = False
    doc = design_from_scene(win).to_dict()
    ed = doc["settings"]["editing"]
    assert ed == {"shuffle": True, "auto_coalesce": True,
                  "auto_weld": False, "auto_bind": True}
    # each flag exists ONCE, inside `editing`, where the schema puts it
    for key in ed:
        assert key not in doc["settings"], f"{key} duplicated at the top level"


def test_editing_block_applies_on_load(fp, win):
    fp.SETTINGS["shuffle"] = True
    fp.SETTINGS["auto_bind"] = False
    doc = design_from_scene(win).to_dict()
    fp.SETTINGS.update(fp.DEFAULT_SETTINGS)          # back to defaults
    assert fp.SETTINGS["shuffle"] is False           # precondition
    apply_design_to_scene(win, doc)
    assert fp.SETTINGS["shuffle"] is True
    assert fp.SETTINGS["auto_bind"] is False
    assert fp.SETTINGS["auto_weld"] is True


# --------------------------------------------------------------------------
# the toolbar toggle
# --------------------------------------------------------------------------
def test_toolbar_toggle_flips_the_setting(fp, win):
    assert win.a_shuffle.isCheckable()
    assert not win.a_shuffle.isChecked()             # default off
    win.a_shuffle.setChecked(True)
    assert fp.SETTINGS["shuffle"] is True
    win.a_shuffle.setChecked(False)
    assert fp.SETTINGS["shuffle"] is False


def test_opening_a_shuffle_document_syncs_the_toggle(fp, win, tmp_path):
    fp.SETTINGS["shuffle"] = True
    doc = design_from_scene(win).to_dict()
    fp.SETTINGS["shuffle"] = False                   # a fresh session's state
    p = tmp_path / "shuffled.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    win.load_path(str(p))
    assert fp.SETTINGS["shuffle"] is True
    assert win.a_shuffle.isChecked(), (
        "the toolbar must show the loaded document's mode")


# --------------------------------------------------------------------------
# the explicit join is exempt: merge_wall(force=True)
# --------------------------------------------------------------------------
def _overlapping_pair(fp, scene):
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(60, 0), QPointF(180, 0), "interior")
    scene.addItem(a)
    scene.addItem(b)
    fp.rebuild_all_walls(scene)
    return a


def _wall_count(fp, scene):
    return sum(1 for it in scene.items() if isinstance(it, fp.WallItem))


def test_merge_wall_force_overrides_the_gate(fp, scene):
    a = _overlapping_pair(fp, scene)
    fp.SETTINGS["auto_coalesce"] = False
    fp.merge_wall(scene, a)
    assert _wall_count(fp, scene) == 2, "gated: nothing may merge"
    fp.merge_wall(scene, a, force=True)
    assert _wall_count(fp, scene) == 1, (
        "force=True is the EXPLICIT path (the join): it must merge even "
        "with auto_coalesce off")


def test_merge_gates_respect_shuffle(fp, scene):
    a = _overlapping_pair(fp, scene)
    fp.SETTINGS["shuffle"] = True                    # auto_coalesce stays True
    fp.merge_wall(scene, a)
    assert _wall_count(fp, scene) == 2, "shuffle implies auto_coalesce off"
    assert fp.merge_all(scene) == 0


# --------------------------------------------------------------------------
# the label-drag under shuffle: a MOVED room stays floating; a click that
# never moved still ends placed (P4.2's rule); the join stays explicit
# --------------------------------------------------------------------------
class _Ev:
    """Duck-typed scene mouse event (the test_wall_move._Ev pattern): the
    handlers are called directly, so only what they read is provided."""

    def __init__(self, pos=None, scene_pos=None):
        self._p, self._sp = pos, scene_pos

    def button(self):
        from PyQt6.QtCore import Qt
        return Qt.MouseButton.LeftButton

    def modifiers(self):
        from PyQt6.QtCore import Qt
        return Qt.KeyboardModifier.NoModifier

    def pos(self):
        return self._p

    def scenePos(self):
        return self._sp

    def accept(self):
        pass


def _make_room(fp, scene, x, y, w, h, name, skip=None):
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


def _label_drag(fp, room, dx, dy):
    """Drive the REAL handlers: press on the label, move (or not), release."""
    grab = room.mapToScene(room._label_rect().center())
    room.mousePressEvent(_Ev(pos=room._label_rect().center(), scene_pos=grab))
    if dx or dy:
        room.mouseMoveEvent(_Ev(scene_pos=QPointF(grab.x() + dx,
                                                  grab.y() + dy)))
    room.mouseReleaseEvent(_Ev(scene_pos=QPointF(grab.x() + dx,
                                                 grab.y() + dy)))


@pytest.mark.rooms
def test_shuffle_label_drag_leaves_the_moved_room_floating(fp, scene):
    a = _make_room(fp, scene, 0, 0, 120, 120, "A")
    b = _make_room(fp, scene, 120, 0, 120, 120, "B",
                   skip=[(QPointF(120, 0), QPointF(120, 120))])
    area_b = b.area_sqft
    fp.SETTINGS["shuffle"] = True
    _label_drag(fp, a, 0, 300)
    assert a.placement_state == "floating", (
        "shuffle: a moved room joins NOTHING automatically")
    assert b.area_sqft == pytest.approx(area_b), "the neighbour must not move"


@pytest.mark.rooms
def test_shuffle_label_click_still_ends_placed(fp, scene):
    a = _make_room(fp, scene, 0, 0, 120, 120, "A")
    fp.SETTINGS["shuffle"] = True
    _label_drag(fp, a, 0, 0)                        # press + release, no move
    assert a.placement_state == "placed", (
        "P4.2's rule stands under shuffle: a click must not leave a room "
        "afloat")


# --------------------------------------------------------------------------
# THE P4.3 ACCEPTANCE, as the task line states it: "With shuffle on, dragging
# a floating room across the plan leaves both unchanged; check() clean
# throughout (I11 exempts floating rooms)."
# --------------------------------------------------------------------------
@pytest.mark.rooms
def test_acceptance_shuffle_drag_across_the_plan(fp, win, first_furnishing):
    import warnings

    from floorplanner.design.validate import check

    def _clean(label):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc = design_from_scene(win).to_dict()
        errs = check(doc, deep=True)
        assert errs == [], f"check() not clean {label}: {errs}"

    sc = win.scene
    mover = _make_room(fp, sc, 0, 0, 120, 120, "Mover")
    anchor = _make_room(fp, sc, 240, 0, 144, 120, "Anchor")
    door = fp.OpeningItem(anchor.walls[0], "door", "3280",
                          anchor.walls[0].length() / 2)
    anchor.walls[0].openings.append(door)
    furn = fp.FurnishingItem(first_furnishing, QPointF(48, 48), 0)
    sc.addItem(furn)
    fp.rebuild_all_walls(sc)
    _clean("before anything")

    fp.SETTINGS["shuffle"] = True
    _label_drag(fp, mover, 0, 300)                   # shuffle: float it
    assert mover.placement_state == "floating"
    _clean("after the shuffle float")

    anchor_walls = sorted(
        (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()) for w in anchor.walls)
    area_m, walls_m = mover.area_sqft, len(mover.walls)
    # the plain label-drag deliberately does NOT carry furnishings (P4.2's
    # preserved trait -- carrying is the explicit Extract's), so on this path
    # the furnishing is PLAN-side state and "unchanged" means it stays put
    furn_pos = QPointF(furn.scenePos())

    # one gesture, stepped ACROSS the plan -- straight through Anchor's
    # footprint -- through the REAL handlers; nothing may merge, weld, bind
    # or move in passing at ANY step
    grab = mover.mapToScene(mover._label_rect().center())
    mover.mousePressEvent(_Ev(pos=mover._label_rect().center(),
                              scene_pos=grab))
    x, y = grab.x(), grab.y()
    for i, (dx, dy) in enumerate([(120, -300), (120, 0), (120, 0),
                                  (120, 0), (120, 0)]):
        x, y = x + dx, y + dy
        mover.mouseMoveEvent(_Ev(scene_pos=QPointF(x, y)))
        fp.rebuild_all_walls(sc)
        _clean(f"mid-drag step {i} (over the plan)")
        assert mover.placement_state == "floating"
        now = sorted((w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y())
                     for w in anchor.walls)
        assert now == anchor_walls, f"the PLAN moved at step {i}"
        assert mover.area_sqft == pytest.approx(area_m), "the room deformed"
        assert len(mover.walls) == walls_m
    mover.mouseReleaseEvent(_Ev(scene_pos=QPointF(x, y)))

    # released past the far side: still floating, both still unchanged
    assert mover.placement_state == "floating"
    assert sorted((w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y())
                  for w in anchor.walls) == anchor_walls
    assert mover.area_sqft == pytest.approx(area_m)
    assert len(anchor.walls[0].openings) == 1, "the door must survive"
    assert furn.scenePos().x() == pytest.approx(furn_pos.x())
    assert furn.scenePos().y() == pytest.approx(furn_pos.y()), (
        "the plan-side furnishing must not be dragged along")
    _clean("after release")


@pytest.mark.rooms
def test_explicit_join_still_joins_under_shuffle(fp, scene):
    a = _make_room(fp, scene, 0, 0, 120, 120, "A")
    _make_room(fp, scene, 120, 0, 120, 120, "B",
               skip=[(QPointF(120, 0), QPointF(120, 120))])
    fp.SETTINGS["shuffle"] = True
    fp.extract_room(scene, a)
    a._translate(0, 300)
    a._translate(0, -300)                           # back beside B
    fp.join_room(scene, a)
    assert a.placement_state == "placed"
    party = [w for w in scene.items() if isinstance(w, fp.WallItem)
             and abs(w.p1.x() - 120) < 0.5 and abs(w.p2.x() - 120) < 0.5]
    assert len(party) == 1, (
        f"the explicit join must merge coincident walls even under shuffle "
        f"(found {len(party)})")
