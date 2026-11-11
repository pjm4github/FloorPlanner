"""#3 (0294 sec4), his order 2026-11-10: the End-On dialog's Elevation tab
draws EITHER gable end of an ordinary roof -- 0 (p1) or 1 (p2) -- and the blue
end-marker in the plan indicates which. `RoofItem.gable_elevation(end=...)`
picks the end (falling back off a hip to a drawable live gable end); the tab's
selector drives it and moves the dot (restored on close). These cover the
per-end selection on top of the single-end tests in test_gable_elevation.py.
"""
import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls


def _gable(scene, span=100.0):
    """A plain gable roof, ridge along x at y=100: p1=(0,100) is end 0,
    p2=(400,100) is end 1; both ends gabled, marker at end 1 (the default)."""
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                  ridge_h_in=150.0, overhang_in=0.0, span_in=span)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _end_wall(scene, x, code="3648", s=100.0):
    """An exterior wall across the ridge at `x` (x=0 -> p1/end 0, x=400 ->
    p2/end 1), perpendicular to the ridge and spanning the eaves width."""
    w = WallItem(QPointF(x, 0), QPointF(x, 200), "exterior")
    w.floor = DEFAULT_FLOOR
    if code is not None:
        w.openings.append(fp.OpeningItem(w, "window", code, s))
    scene.addItem(w)
    return w


# -- the model: either end, by index -------------------------------------

def test_each_end_draws_its_own_wall(scene):
    """A window wall at the p1 end only: end 0 shows it, end 1 is the bare
    gable -- a valid triangle with no windows -- and each reports its index."""
    rf = _gable(scene)
    _end_wall(scene, x=0, code="3648", s=100.0)      # at end 0 (p1)

    e0 = rf.gable_elevation(end=0)
    assert e0["end"] == 0
    assert len(e0["windows"]) == 1
    assert e0["windows"][0]["w_in"] == pytest.approx(36.0)

    e1 = rf.gable_elevation(end=1)
    assert e1["end"] == 1
    assert e1["windows"] == []                        # no wall at p2
    assert e1["width_in"] > 0.0 and e1["ridge_in"] > 0.0   # still a drawable gable


def test_each_end_finds_the_wall_at_that_end(scene):
    """With a window wall at BOTH ends, each end selects its own wall."""
    rf = _gable(scene)
    _end_wall(scene, x=0, code="3030", s=100.0)       # end 0
    _end_wall(scene, x=400, code="6040", s=100.0)     # end 1
    w0 = rf.gable_elevation(end=0)["windows"]
    w1 = rf.gable_elevation(end=1)["windows"]
    assert w0[0]["w_in"] == pytest.approx(30.0)        # 3030 at end 0
    assert w1[0]["w_in"] == pytest.approx(60.0)        # 6040 at end 1


def test_a_hip_end_falls_back_to_a_drawable_gable(scene):
    """Asking for an end that is a HIP (not a live gable) falls back to the
    other, drawable gable end rather than returning nothing."""
    rf = _gable(scene)
    rf.gable = [True, False]                           # end 1 is a hip now
    _end_wall(scene, x=0, code="3648", s=100.0)        # the only gable end
    e = rf.gable_elevation(end=1)                      # 1 is the hip
    assert e is not None
    assert e["end"] == 0                               # fell back to the live gable
    assert len(e["windows"]) == 1


def test_gable_end_wall_returns_the_requested_end_index(scene):
    """`_gable_end_wall(gable, axis, end=...)` returns `(wall, end)` with the
    end index matching the request when that end is a live gable."""
    rf = _gable(scene)
    w0 = _end_wall(scene, x=0, code="3030", s=100.0)
    w1 = _end_wall(scene, x=400, code="6040", s=100.0)
    gable = [True, True]
    axis = (1.0, 0.0)                                  # ridge runs along +x
    wall0, end0 = rf._gable_end_wall(gable, axis, end=0)
    wall1, end1 = rf._gable_end_wall(gable, axis, end=1)
    assert (wall0, end0) == (w0, 0)
    assert (wall1, end1) == (w1, 1)


# -- his order 2026-11-11: doors AND windows, and every wall under the gable --

def test_a_door_in_the_gable_end_sits_on_the_floor(scene):
    """A door in the gable-end wall is read AS a door -- on the floor (sill 0),
    its real height, kind 'door' -- not floated at the window sill default."""
    rf = _gable(scene)
    w = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")
    w.floor = DEFAULT_FLOOR
    w.openings.append(fp.OpeningItem(w, "door", "3680", 100.0))   # 36x80, centred
    scene.addItem(w)
    e = rf.gable_elevation(end=0)
    assert e["windows"] == []                      # doors are kept separate
    assert len(e["doors"]) == 1
    d = e["doors"][0]
    assert d["kind"] == "door"
    assert d["w_in"] == pytest.approx(36.0)
    assert d["h_in"] == pytest.approx(80.0)        # height is real, not 0
    assert d["sill_in"] == pytest.approx(0.0)      # on the floor
    assert d["head_in"] == pytest.approx(80.0)
    assert d["centre_in"] == pytest.approx(0.0, abs=0.5)


def test_a_door_and_a_window_go_to_their_own_lists(scene):
    """A gable-end wall carrying a door and a window puts each in its own list."""
    rf = _gable(scene)
    w = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")
    w.floor = DEFAULT_FLOOR
    w.openings.append(fp.OpeningItem(w, "door", "3680", 60.0))
    w.openings.append(fp.OpeningItem(w, "window", "3030", 150.0))
    scene.addItem(w)
    e = rf.gable_elevation(end=0)
    assert [o["kind"] for o in e["windows"]] == ["window"]
    assert [o["kind"] for o in e["doors"]] == ["door"]


def test_collinear_gable_segments_are_all_read(scene):
    """A gable end built from TWO collinear exterior segments (split by a tee or
    a drawn gap) shows the openings from BOTH walls -- not just one."""
    rf = _gable(scene)
    lo = WallItem(QPointF(0, 0), QPointF(0, 82), "exterior")       # lower segment
    lo.floor = DEFAULT_FLOOR
    lo.openings.append(fp.OpeningItem(lo, "window", "2430", 40.0))
    scene.addItem(lo)
    hi = WallItem(QPointF(0, 118), QPointF(0, 200), "exterior")    # upper segment
    hi.floor = DEFAULT_FLOOR
    hi.openings.append(fp.OpeningItem(hi, "door", "3080", 40.0))    # within the 82" segment
    scene.addItem(hi)
    e = rf.gable_elevation(end=0)
    assert len(e["windows"]) == 1 and len(e["doors"]) == 1     # one from each segment
    # both openings land inside the gable's half-width (not off the end)
    assert all(abs(o["centre_in"]) <= 100.0 for o in e["windows"] + e["doors"])


def test_both_storeys_under_the_gable_are_read(scene):
    """A two-storey gable end: the roof's OWN floor AND the floor above both
    stand under it, so an upper-storey window is read and LIFTED to its true
    height -- its floor-to-floor rise plus its own sill -- not floated at the
    ground-floor sill (his order 2026-11-11: both floors on the elevation)."""
    from floorplanner.config import set_floor_state
    set_floor_state(elevations={DEFAULT_FLOOR: 0.0, "upper": 96.0})
    rf = _gable(scene)                                   # on DEFAULT_FLOOR
    lo = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")   # ground gable wall
    lo.floor = DEFAULT_FLOOR
    lo.openings.append(fp.OpeningItem(lo, "window", "3648", 100.0))   # sill default 36
    scene.addItem(lo)
    hi = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")   # storey above, stacked
    hi.floor = "upper"
    hi.openings.append(fp.OpeningItem(hi, "window", "6048", 100.0))
    scene.addItem(hi)

    e = rf.gable_elevation(end=0)
    assert len(e["windows"]) == 2                        # both storeys are read
    by_w = {round(w["w_in"]): w for w in e["windows"]}
    assert by_w[36]["sill_in"] == pytest.approx(36.0)    # ground floor, at its own sill
    assert by_w[60]["sill_in"] == pytest.approx(96.0 + 36.0)         # lifted one storey
    assert by_w[60]["head_in"] == pytest.approx(96.0 + 36.0 + 48.0)


def test_an_upper_storey_door_sits_on_its_own_floor(scene):
    """A door on the floor above sits on THAT storey's floor -- sill at the
    floor-to-floor rise, not 0 -- so it draws in the gable, not the ground."""
    from floorplanner.config import set_floor_state
    set_floor_state(elevations={DEFAULT_FLOOR: 0.0, "upper": 108.0})
    rf = _gable(scene)
    hi = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")
    hi.floor = "upper"
    hi.openings.append(fp.OpeningItem(hi, "door", "3680", 100.0))
    scene.addItem(hi)
    e = rf.gable_elevation(end=0)
    assert e["windows"] == []
    assert len(e["doors"]) == 1
    d = e["doors"][0]
    assert d["sill_in"] == pytest.approx(108.0)          # on the upper floor
    assert d["head_in"] == pytest.approx(108.0 + 80.0)


# -- the dialog: the selector and the blue dot ----------------------------

@pytest.mark.gui
def test_the_elevation_tab_switches_ends_and_the_dot_follows(scene):
    """The Elevation tab's selector lists both live gable ends; picking the
    other end redraws it and moves the blue end-marker to that ridge end;
    closing the dialog snaps the dot back to the roof's real marker end."""
    from floorplanner.dialogs import RoofEndOnDialog
    rf = _gable(scene)
    _end_wall(scene, x=0, code="3648", s=100.0)        # windows at end 0
    assert rf.marker_end == 1                          # marker at p2 (end 1)

    dlg = RoofEndOnDialog(rf)
    assert dlg.cb_elev_end is not None
    assert dlg.cb_elev_end.isEnabled()
    assert dlg.cb_elev_end.count() == 2
    # opens on the marker end (the dot is already there, so it has not moved)
    assert dlg._elev_end == 1
    assert dlg.elev_canvas.data["end"] == 1
    assert rf.marker.pos().x() == pytest.approx(rf.p2.x())

    other = dlg.cb_elev_end.findData(0)                # the "Other end" entry
    dlg.cb_elev_end.setCurrentIndex(other)             # fires _on_elev_end
    assert dlg._elev_end == 0
    assert dlg.elev_canvas.data["end"] == 0
    assert dlg.elev_canvas.data["windows"][0]["w_in"] == pytest.approx(36.0)
    # the blue dot followed to the p1 end
    assert rf.marker.pos().x() == pytest.approx(rf.p1.x())
    assert rf.marker.pos().y() == pytest.approx(rf.p1.y())

    dlg._restore_marker_dot()                          # as dialog close does
    assert rf.marker.pos().x() == pytest.approx(rf.p2.x())   # back to marker end
    assert rf.marker_end == 1                          # viewing never changed it
    dlg.deleteLater()


@pytest.mark.gui
def test_one_gable_end_disables_the_selector(scene):
    """A roof with a single live gable end offers one, disabled entry."""
    from floorplanner.dialogs import RoofEndOnDialog
    rf = _gable(scene)
    rf.gable = [True, False]                           # only end 0 is a gable
    dlg = RoofEndOnDialog(rf)
    assert dlg.cb_elev_end is not None
    assert dlg.cb_elev_end.count() == 1
    assert not dlg.cb_elev_end.isEnabled()
    assert dlg._elev_end == 0
    dlg.deleteLater()


@pytest.mark.gui
def test_a_dormer_has_no_end_selector(scene):
    """A dormer draws its single face -- there is no end to choose, so no
    selector is built."""
    from floorplanner.dialogs import RoofEndOnDialog
    host = RoofItem(QPointF(-40, 100), QPointF(440, 100), eaves_h_in=96.0,
                    ridge_h_in=300.0, overhang_in=0.0, span_in=[170.0, 170.0],
                    gable=[True, True], marker_end=1)
    host.floor = DEFAULT_FLOOR
    scene.addItem(host)
    d = RoofItem(QPointF(200, 240), QPointF(200, 160), eaves_h_in=180.0,
                 ridge_h_in=240.0, overhang_in=0.0, span_in=[40.0, 40.0],
                 wall_span_in=[40.0, 40.0], gable=[True, True], marker_end=0,
                 host=host, openings=[])
    d.floor = DEFAULT_FLOOR
    scene.addItem(d)
    dlg = RoofEndOnDialog(d)
    assert dlg._dormer
    assert dlg.cb_elev_end is None
    dlg.deleteLater()
