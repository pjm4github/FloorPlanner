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
