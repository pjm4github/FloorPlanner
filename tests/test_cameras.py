"""0313: plan CAMERAS -- a placeable viewpoint that opens an ELEVATION of the
wall it faces. The item finds the wall its aim ray crosses, projects it straight
on with its doors and windows located, and round-trips through the design.
"""
import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.cameras import CameraItem, DEFAULT_CAMERA_CEILING_IN
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls


def _wall(scene, p1, p2, kind="exterior"):
    w = WallItem(QPointF(*p1), QPointF(*p2), kind)
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    return w


def test_a_camera_finds_the_wall_it_aims_at(scene):
    """A camera below a horizontal wall, aimed up (-y, 270°), hits that wall."""
    w = _wall(scene, (0, 100), (200, 100))
    cam = CameraItem(QPointF(100, 160), rotation=270.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    assert cam.faced_wall() is w


def test_a_camera_aiming_at_open_space_faces_no_wall(scene):
    """Aimed away from every wall (down, +y, 90°), it faces nothing."""
    _wall(scene, (0, 100), (200, 100))
    cam = CameraItem(QPointF(100, 160), rotation=90.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    assert cam.faced_wall() is None
    assert cam.elevation() is None


def test_a_camera_takes_the_nearest_wall(scene):
    """Two parallel walls ahead: the camera elevation is of the NEARER one."""
    near = _wall(scene, (0, 100), (200, 100))
    _wall(scene, (0, 40), (200, 40))                 # farther up
    cam = CameraItem(QPointF(100, 160), rotation=270.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    assert cam.faced_wall() is near


def test_the_elevation_locates_doors_and_windows(scene):
    """A wall carrying a window and a door: the faced wall's face has each in its
    own list, to scale, with the window on its sill and the door on the floor.
    (No room around the camera, so the elevation is the single faced wall.)"""
    w = _wall(scene, (0, 100), (200, 100))
    w.openings.append(fp.OpeningItem(w, "window", "3648", 60.0))    # 36x48, sill default
    w.openings.append(fp.OpeningItem(w, "door", "3280", 140.0))     # 32x80, on the floor
    cam = CameraItem(QPointF(100, 160), rotation=270.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    e = cam.elevation()
    assert e is not None
    assert len(e["faces"]) == 1                           # one wall, no room
    face = e["faces"][0]
    assert face["width_in"] == pytest.approx(200.0)
    assert [o["kind"] for o in face["windows"]] == ["window"]
    assert [o["kind"] for o in face["doors"]] == ["door"]
    win = face["windows"][0]
    assert win["w_in"] == pytest.approx(36.0) and win["h_in"] == pytest.approx(48.0)
    assert win["sill_in"] == pytest.approx(fp.DEFAULT_SILL_IN)
    door = face["doors"][0]
    assert door["w_in"] == pytest.approx(32.0) and door["h_in"] == pytest.approx(80.0)
    assert door["sill_in"] == pytest.approx(0.0)          # on the floor
    assert door["head_in"] == pytest.approx(80.0)
    # the ceiling clears the tallest opening
    assert e["height_in"] >= 80.0


def test_the_elevation_centre_offsets_are_from_the_wall_middle(scene):
    """`centre_in` is each opening's offset from its wall's centre -- a window at
    s=60 on a 200" wall is 40" left of centre (its sign set by the camera's view)."""
    w = _wall(scene, (0, 100), (200, 100))
    w.openings.append(fp.OpeningItem(w, "window", "3030", 60.0))     # s=60 -> -40 from centre
    cam = CameraItem(QPointF(100, 160), rotation=270.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    e = cam.elevation()
    assert abs(e["faces"][0]["windows"][0]["centre_in"]) == pytest.approx(40.0)


def test_default_ceiling_when_no_room(scene):
    """With no room under the camera, the elevation top is the standard ceiling."""
    _wall(scene, (0, 100), (200, 100))
    cam = CameraItem(QPointF(100, 160), rotation=270.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    assert cam.elevation()["height_in"] == pytest.approx(DEFAULT_CAMERA_CEILING_IN)


def test_a_room_camera_shows_the_faced_wall_and_both_returns(fp, scene, make_room):
    """A camera inside a walled room, aimed at the far wall, elevations THAT wall
    and names the two side walls that turn toward it as left/right returns; the
    near wall behind the camera is not a face. The room's ceiling sets the top."""
    room = make_room(scene, 0, 0, 200, 100, "DEN")
    room.properties["ceiling_height_in"] = 108.0
    cam = CameraItem(QPointF(100, 55), rotation=270.0)    # centre, aimed up (-y)
    scene.addItem(cam)
    e = cam.elevation()
    assert e is not None
    assert e["room_name"] == room.name
    assert e["height_in"] == pytest.approx(108.0)         # the room's ceiling
    assert len(e["faces"]) == 1                           # the single far wall
    assert e["left_return"] is not None and e["right_return"] is not None
    # the two returns are the room's side walls (distinct, labelled)
    assert e["left_return"]["label"] != e["right_return"]["label"]


def test_room_elevation_spans_a_faced_wall_broken_by_a_doorway(fp, scene):
    """A far wall made of two coplanar segments split by a doorway (as the DINING
    room is in wiscaway: W47+W57). The elevation lays BOTH across the view, left
    to right, and calls out the two side walls as returns -- one plane, not one
    segment."""
    def _w(a, b):
        w = fp.WallItem(QPointF(*a), QPointF(*b), "interior")
        scene.addItem(w)
        return w
    wA = _w((0, 0), (78, 0))             # top-left segment (far wall), carries a door
    _w((78, 0), (180, 0))                # top-right segment (far wall)
    _w((180, 0), (180, 100))             # right side -> right return
    _w((180, 100), (0, 100))             # near wall (behind the camera)
    _w((0, 100), (0, 0))                 # left side -> left return
    wA.openings.append(fp.OpeningItem(wA, "door", "3080", 40.0))
    fp.rebuild_all_walls(scene)
    centre = QPointF(90, 50)
    res = fp.detect_room(scene, centre)
    assert res is not None
    room = fp.RoomItem(fp.unique_room_name(scene, "DEN"), centre,
                       res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    cam = CameraItem(QPointF(90, 60), rotation=270.0)            # in the room, aimed up
    scene.addItem(cam)
    e = cam.elevation()
    assert e is not None
    assert [fc["width_in"] for fc in e["faces"]] == [pytest.approx(78.0),
                                                     pytest.approx(102.0)]
    assert sum(len(fc["doors"]) for fc in e["faces"]) == 1       # the doorway, in the first
    assert e["left_return"] is not None and e["right_return"] is not None
    # the near wall behind the camera is not drawn as a face
    assert len(e["faces"]) == 2


def test_a_camera_record_round_trips(scene):
    """`to_record`/`from_record` preserve the camera's position and aim."""
    cam = CameraItem(QPointF(72.0, 48.0), rotation=135.0, floor=DEFAULT_FLOOR, name="front")
    rec = cam.to_record("cam1", DEFAULT_FLOOR)
    # 0316: a camera that has never been labelled (no _uid) stores no `uid` --
    # the walk reads the label, it never mints one, so this record is unchanged
    assert rec == {"id": "cam1", "level": DEFAULT_FLOOR,
                   "pos": [72.0, 48.0], "rotation": 135.0, "name": "front"}
    back = CameraItem.from_record(rec, DEFAULT_FLOOR)
    assert back.pos().x() == pytest.approx(72.0)
    assert back.pos().y() == pytest.approx(48.0)
    assert back.rotation() == pytest.approx(135.0)
    assert back.name == "front"


def test_cameras_round_trip_through_the_document(fp, scene):
    """A placed camera serializes into the `cameras` block, validates against the
    v6 schema, and comes back on load with its position and aim."""
    from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
    from floorplanner.design.validate import schema_errors
    scene.addItem(CameraItem(QPointF(72.0, 48.0), rotation=135.0, floor=DEFAULT_FLOOR))
    out = design_from_scene(scene).to_dict()
    assert schema_errors(out) == []
    assert len(out["cameras"]) == 1
    assert out["cameras"][0]["pos"] == [72.0, 48.0]
    assert out["cameras"][0]["rotation"] == pytest.approx(135.0)
    scene.clear()
    apply_design_to_scene(scene, out)
    cams = [it for it in scene.items() if isinstance(it, CameraItem)]
    assert len(cams) == 1
    assert cams[0].pos().x() == pytest.approx(72.0)
    assert cams[0].rotation() == pytest.approx(135.0)


def test_no_cameras_means_no_block(fp, scene):
    """The `cameras` block is optional -- a plan with none omits the key."""
    from floorplanner.design.bridge import design_from_scene
    _wall(scene, (0, 0), (100, 0))
    assert "cameras" not in design_from_scene(scene).to_dict()


@pytest.mark.gui
def test_show_cameras_toggle_hides_and_shows(win):
    """View ▸ Show cameras hides every camera and shows them again."""
    cam = CameraItem(QPointF(50, 50))             # floor defaults to the active one
    win.scene.addItem(cam)
    assert cam.isVisible()
    win.a_show_cameras.setChecked(False)          # fires _set_cameras_visible
    assert not cam.isVisible()
    win.a_show_cameras.setChecked(True)
    assert cam.isVisible()


@pytest.mark.gui
def test_place_camera_menu_starts_the_tool(win):
    """View ▸ Place camera puts the window in the camera tool."""
    from floorplanner.config import TOOL_CAMERA, TOOL_SELECT
    win.set_tool(TOOL_SELECT)
    win.set_tool(TOOL_CAMERA)
    assert win.tool == TOOL_CAMERA
    assert win._tool_actions[TOOL_CAMERA].isChecked()


# -- 0315: show the furnishings / cabinetry against the faced wall ------------

def _room_with_items(fp, scene, items):
    """A 180x100 room (far wall split by a doorway) with `items` = [(kind,(x,y))]
    placed; returns (room, camera-aimed-up). Mirrors the split-wall fixture."""
    from floorplanner.items import FurnishingItem

    def _w(a, b):
        w = fp.WallItem(QPointF(*a), QPointF(*b), "interior")
        scene.addItem(w)
        return w
    wA = _w((0, 0), (78, 0))
    _w((78, 0), (180, 0))
    _w((180, 0), (180, 100))
    _w((180, 100), (0, 100))
    _w((0, 100), (0, 0))
    wA.openings.append(fp.OpeningItem(wA, "door", "3080", 40.0))
    fp.rebuild_all_walls(scene)
    centre = QPointF(90, 50)
    res = fp.detect_room(scene, centre)
    room = fp.RoomItem(fp.unique_room_name(scene, "KIT"), centre,
                       res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    for kind, pos in items:
        it = FurnishingItem(kind, QPointF(*pos))
        scene.addItem(it)
    cam = CameraItem(QPointF(90, 60), rotation=270.0)
    scene.addItem(cam)
    return room, cam


def test_is_casework_splits_cabinets_from_furniture():
    """Built-in cabinets are casework (cabinetry); free-standing pieces are not."""
    from floorplanner.catalog import is_casework
    assert is_casework("base_cab_36") and is_casework("wall_cab_36")
    assert is_casework("vanity_24") and is_casework("kitchen_island")
    assert not is_casework("sofa") and not is_casework("bed_queen")


def test_toggles_off_show_no_items(fp, scene):
    """With both switches off the elevation carries no furnishings at all."""
    _room, cam = _room_with_items(fp, scene, [("base_cab_36", (120, 12)),
                                              ("sofa", (40, 14))])
    assert cam.show_furnishings is False and cam.show_cabinetry is False
    assert cam.elevation()["furnishings"] == []


def test_cabinetry_toggle_shows_only_casework(fp, scene):
    """Show cabinetry draws the base cabinet (casework), not the sofa."""
    _room, cam = _room_with_items(fp, scene, [("base_cab_36", (120, 12)),
                                              ("sofa", (40, 14))])
    cam.set_show_cabinetry(True)
    items = cam.elevation()["furnishings"]
    assert [it["casework"] for it in items] == [True]
    base = items[0]
    assert base["sill_in"] == pytest.approx(0.0)          # base cabinet on the floor
    assert base["head_in"] == pytest.approx(36.0)


def test_furnishings_toggle_shows_only_free_standing(fp, scene):
    """Show furnishings draws the sofa, not the base cabinet."""
    _room, cam = _room_with_items(fp, scene, [("base_cab_36", (120, 12)),
                                              ("sofa", (40, 14))])
    cam.set_show_furnishings(True)
    items = cam.elevation()["furnishings"]
    assert [it["casework"] for it in items] == [False]
    assert items[0]["name"] == "Sofa"


def test_a_wall_cabinet_sits_at_its_mounting_height(fp, scene):
    """A wall cabinet draws elevated off the floor (its elevation_in ~54\")."""
    _room, cam = _room_with_items(fp, scene, [("wall_cab_36", (120, 6))])
    cam.set_show_cabinetry(True)
    wc = cam.elevation()["furnishings"][0]
    assert wc["sill_in"] == pytest.approx(54.0)
    assert wc["head_in"] == pytest.approx(84.0)


def test_an_item_away_from_the_wall_is_not_shown(fp, scene):
    """A piece in the middle of the room (against no wall) is not drawn."""
    _room, cam = _room_with_items(fp, scene, [("dining_table", (90, 50))])
    cam.set_show_furnishings(True)
    assert cam.elevation()["furnishings"] == []


def test_content_switches_round_trip(fp, scene):
    """The two switches serialize, validate, and reload with the camera."""
    from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
    from floorplanner.design.validate import schema_errors
    scene.addItem(CameraItem(QPointF(72, 48), rotation=0.0,
                             show_furnishings=True, show_cabinetry=True))
    out = design_from_scene(scene).to_dict()
    assert schema_errors(out) == []
    assert out["cameras"][0]["show_furnishings"] is True
    assert out["cameras"][0]["show_cabinetry"] is True
    scene.clear()
    apply_design_to_scene(scene, out)
    cam = [it for it in scene.items() if isinstance(it, CameraItem)][0]
    assert cam.show_furnishings and cam.show_cabinetry


def test_the_glyph_grows_a_badge_per_active_switch(scene):
    """Turning a switch on adds a badge and enlarges the glyph's bounds."""
    cam = CameraItem(QPointF(0, 0))
    scene.addItem(cam)
    plain = cam.boundingRect()
    assert cam._badges() == []
    cam.set_show_furnishings(True)
    assert len(cam._badges()) == 1
    cam.set_show_cabinetry(True)
    assert len(cam._badges()) == 2
    cam.set_show_house_side(True)                 # 0317: a third switch, a third badge
    assert len(cam._badges()) == 3
    assert cam.boundingRect().height() > plain.height()


# -- 0317: the whole-house-side elevation (a camera outside a room) ------------
def _house(scene):
    """The DEN house: a 180x100 rectangle whose y=0 wall is split into two
    exterior segments (78 + 102) at a doorway; a room detected inside."""
    def _w(p1, p2, kind="exterior"):
        w = WallItem(QPointF(*p1), QPointF(*p2), kind)
        w.floor = DEFAULT_FLOOR
        scene.addItem(w)
        return w
    wA = _w((0, 0), (78, 0))                       # the side a camera above faces...
    _w((78, 0), (180, 0))                          # ...split into two segments
    _w((180, 0), (180, 100))
    _w((180, 100), (0, 100))
    _w((0, 100), (0, 0))
    wA.openings.append(fp.OpeningItem(wA, "door", "3080", 40.0))
    fp.rebuild_all_walls(scene)
    centre = QPointF(90, 50)
    res = fp.detect_room(scene, centre)
    assert res is not None
    room = fp.RoomItem(fp.unique_room_name(scene, "DEN"), centre,
                       res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


def test_outside_a_room_without_the_switch_reads_one_wall(scene):
    """A camera above the house, switch OFF: the single wall its aim ray hits."""
    _house(scene)
    cam = CameraItem(QPointF(90, -60), rotation=90.0, floor=DEFAULT_FLOOR)   # above, aimed down
    scene.addItem(cam)
    assert not cam.show_house_side
    e = cam.elevation()
    assert e is not None and len(e["faces"]) == 1
    assert e["left_return"] is None and e["right_return"] is None


def test_the_house_side_switch_elevations_the_whole_side(scene):
    """Switch ON: BOTH exterior segments of the side it faces, left->right, and
    neither the far wall of the house nor the two side (return) walls."""
    _house(scene)
    cam = CameraItem(QPointF(90, -60), rotation=90.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    cam.set_show_house_side(True)
    e = cam.elevation()
    assert e is not None
    widths = sorted(fc["width_in"] for fc in e["faces"])
    assert widths == [pytest.approx(78.0), pytest.approx(102.0)]
    assert len(e["faces"]) == 2                    # not the far wall, not the sides


def test_inside_a_room_the_house_side_switch_is_a_no_op(scene):
    """The switch only widens an OUTSIDE view -- inside a room the room elevation
    stands whether it is on or off."""
    _house(scene)
    cam = CameraItem(QPointF(90, 40), rotation=270.0, floor=DEFAULT_FLOOR,
                     show_house_side=True)         # inside the room, aimed up
    scene.addItem(cam)
    e = cam.elevation()
    assert e is not None and len(e["faces"]) == 2  # the room's far wall, two segments


def _two_storey_house(fp, scene):
    """A 300x180 TWO-STOREY house (L1 at 0, L2 at 108) with a gable roof on L2;
    rooms detected on each floor. Sets the floor roster -- the caller restores
    it. Returns nothing; the camera is placed by the test."""
    from floorplanner.config import set_floor_state
    from floorplanner.roofs import RoofItem

    def w(a, b, floor):
        wi = WallItem(QPointF(*a), QPointF(*b), "exterior")
        wi.floor = floor
        scene.addItem(wi)
        return wi

    def storey(floor):
        s1 = w((0, 0), (150, 0), floor)                 # front, split in two
        s2 = w((150, 0), (300, 0), floor)
        w((300, 0), (300, 180), floor)
        w((300, 180), (0, 180), floor)
        w((0, 180), (0, 0), floor)
        return s1, s2

    def detect(floor, name):
        set_floor_state(active=floor)
        fp.rebuild_all_walls(scene)
        res = fp.detect_room(scene, QPointF(150, 90))
        r = fp.RoomItem(fp.unique_room_name(scene, name), QPointF(150, 90),
                        res[0], res[1], corners=res[2])
        r.floor = floor
        scene.addItem(r)
        fp.bind_room_walls(scene, r)

    set_floor_state(active="L1", elevations={"L1": 0.0, "L2": 108.0})
    a1, _b1 = storey("L1")
    a1.openings.append(fp.OpeningItem(a1, "door", "3680", 75.0))
    detect("L1", "L1R")
    storey("L2")
    detect("L2", "L2R")
    set_floor_state(active="L2")
    rf = RoofItem(QPointF(150, 0), QPointF(150, 180),
                  eaves_h_in=108.0, ridge_h_in=168.0, span_in=[150.0, 150.0])
    rf.floor = "L2"
    scene.addItem(rf)
    set_floor_state(active="L1")


def test_the_full_elevation_is_a_hidden_surface_projection_to_the_gable(fp, scene):
    """0318 (compositional rework): outside a house with a gable roof, the
    house-side elevation is a composite of 2-D PIECES (mode house_elev) -- walls
    and roof faces, each a flat polygon with a depth, painted far -> near. The
    gable wall climbs above a single storey toward the ridge, a roof face is
    drawn, and the camera-facing openings ride on their walls."""
    from floorplanner.config import active_floor, floor_elevations, set_floor_state
    saved_active, saved_elevs = active_floor(), floor_elevations()
    try:
        _two_storey_house(fp, scene)
        cam = CameraItem(QPointF(150, -90), rotation=90.0, floor="L1",
                         show_house_side=True)                 # above, aimed at a gable end
        scene.addItem(cam)
        e = cam.elevation()
        assert e is not None and e.get("mode") == "house_elev"
        pieces = e["pieces"]
        assert pieces, "the composited pieces are non-empty"
        assert any(pc["kind"] == "roof" for pc in pieces), "a roof face is drawn"
        assert any(pc["kind"] == "wall" for pc in pieces), "walls are drawn"
        assert e["floor_abs_in"] == pytest.approx(0.0)        # datum = the lowest foot
        # the gable climbs well above a plain one-storey wall (toward the ridge)
        top = max(z for pc in pieces for (_u, z) in pc["outline"])
        assert top >= 150.0, top
        assert e["height_in"] >= 150.0
        assert e["faces"], "the caption still lists the camera-facing walls"
        kinds = {o["kind"] for pc in pieces if pc["kind"] == "wall"
                 for o in pc["openings"]}
        assert "door" in kinds, "the L1 front door is drawn"
    finally:
        set_floor_state(active=saved_active, elevations=saved_elevs)


def test_a_roof_overhang_is_its_own_geometry_and_degeneracy_is_guarded(fp, scene):
    """0318 tweak: the elevation eave overhang is the roof's OWN parameters --
    `overhang_in` * the true slope -- not a drawn-in constant. A roof that stores
    an overhang drops its fascia below the eaves height and projects the soffit
    past the wall; one that stores 0 sits flush. A near-vertical stub side (a
    half-gable's degenerate span) carries no eave, so an overhang set there can
    never blow the extent up."""
    from floorplanner.config import active_floor, floor_elevations, set_floor_state
    from floorplanner.roofs import RoofItem
    saved_active, saved_elevs = active_floor(), floor_elevations()
    try:
        _two_storey_house(fp, scene)
        rf = next(it for it in scene.items() if isinstance(it, RoofItem))
        cam = CameraItem(QPointF(150, -90), rotation=90.0, floor="L1",
                         show_house_side=True)
        scene.addItem(cam)

        def roof_min_z(e):
            return min(z for pc in e["pieces"] if pc["kind"] == "roof"
                       for (_u, z) in pc["outline"])

        # the roof sits on L2 (datum 108), eaves 108 above it -> abs eaves 216
        rf.overhang_in = [0.0, 0.0]                        # stored 0 -> flush
        flush = cam.elevation()
        assert roof_min_z(flush) == pytest.approx(216.0)   # the eaves height itself

        rf.overhang_in = [16.0, 16.0]                      # slope 0.4 -> drop 6.4in
        over = cam.elevation()
        assert roof_min_z(over) < 216.0 - 1.0              # fascia dropped below eaves
        assert over["width_in"] > flush["width_in"] + 1.0  # soffit projects past wall

        # a half-gable stub side (span 1in, slope ~60): the guard gives it no eave,
        # so a 16in overhang there projects nothing rather than dropping off-drawing
        rf.span_in = [150.0, 1.0]
        rf.overhang_in = [16.0, 16.0]
        assert cam.elevation()["height_in"] < 400.0        # extent stays bounded
    finally:
        set_floor_state(active=saved_active, elevations=saved_elevs)


def test_the_house_side_draws_only_the_camera_facing_openings(fp, scene):
    """0318: a window on the FAR wall (its camera-facing side is indoors) must not
    appear -- the elevation sees only the near side. Openings ride on their front
    wall piece; the far wall is never a face, so its window never enters."""
    from floorplanner.config import active_floor, floor_elevations, set_floor_state
    saved_active, saved_elevs = active_floor(), floor_elevations()
    try:
        _two_storey_house(fp, scene)
        # a window on the BACK wall (y = 180), the side turned AWAY from a camera
        # placed below the house (large y) and aimed up at the near (y = 0) wall.
        back = next(w for w in scene.items()
                    if isinstance(w, WallItem) and w.floor == "L1"
                    and abs(w.p1.y() - 180) < 1 and abs(w.p2.y() - 180) < 1)
        back.openings.append(fp.OpeningItem(back, "window", "3048", 150.0))
        cam = CameraItem(QPointF(150, -90), rotation=90.0, floor="L1",
                         show_house_side=True)              # above, aimed (+y) at the y=0 wall
        scene.addItem(cam)
        e = cam.elevation()
        assert e is not None and e.get("mode") == "house_elev"
        labels = {fc.get("label") for fc in e["faces"]}
        assert getattr(back, "uid", "") not in labels, "the far wall is not a face"
        # the near front wall's door still shows among the wall pieces' openings
        kinds = {o["kind"] for pc in e["pieces"] if pc["kind"] == "wall"
                 for o in pc["openings"]}
        assert "door" in kinds
    finally:
        set_floor_state(active=saved_active, elevations=saved_elevs)


def test_the_house_side_switch_round_trips(fp, scene):
    """The switch serializes, validates against the v6 schema, and reloads."""
    from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
    from floorplanner.design.validate import schema_errors
    scene.addItem(CameraItem(QPointF(72, 48), rotation=0.0, show_house_side=True))
    out = design_from_scene(scene).to_dict()
    assert schema_errors(out) == []
    assert out["cameras"][0]["show_house_side"] is True
    scene.clear()
    apply_design_to_scene(scene, out)
    cam = [it for it in scene.items() if isinstance(it, CameraItem)][0]
    assert cam.show_house_side
