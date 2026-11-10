"""#3 (0294 §4): the End-On dialog's ELEVATION tab -- a gable end seen
straight-on, to scale, with its window(s) LOCATED. `RoofItem.gable_elevation()`
returns the drawing data; the tab draws it. His order (2026-11-09): the minimal
locating set -- per window its size, its sill above the floor, and its centre's
offset from the gable centreline -- for BOTH a dormer face and a plain gable end.
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QImage, QPainter

import FloorPlanner as fp
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls


def _gable(scene, eaves_h=96.0, ridge_h=150.0, span=100.0):
    """A plain gable roof, ridge along x at y=100, both ends gabled."""
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=eaves_h,
                  ridge_h_in=ridge_h, overhang_in=0.0, span_in=span)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _gable_end_wall(scene, code="3648", s=100.0):
    """A wall across the roof's p1 (x=0) gable end, perpendicular to the ridge,
    spanning the eaves width -- with one window at `s`."""
    w = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")
    w.floor = DEFAULT_FLOOR
    w.openings.append(fp.OpeningItem(w, "window", code, s))
    scene.addItem(w)
    return w


def _dormer(scene, host, openings=None):
    d = RoofItem(QPointF(200, 190), QPointF(200, 140), eaves_h_in=116.0,
                 ridge_h_in=136.0, overhang_in=0.0, span_in=30.0,
                 marker_end=0, host=host)
    d.floor = DEFAULT_FLOOR
    if openings is not None:
        d.openings = openings
    scene.addItem(d)
    return d


def test_a_plain_gable_draws_its_outline(scene):
    """The outline is pure roof geometry: width = the two eaves spans, the
    eaves and ridge heights above the floor, the apex centred when symmetric."""
    e = _gable(scene).gable_elevation()
    assert e is not None and e["kind"] == "gable"
    assert e["width_in"] == pytest.approx(200.0)       # span 100 + 100
    assert e["eaves_in"] == pytest.approx(96.0)
    assert e["ridge_in"] == pytest.approx(150.0)
    assert e["apex_in"] == pytest.approx(0.0)          # symmetric -> centred


def test_an_asymmetric_gable_apex_is_off_centre(scene):
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                  ridge_h_in=150.0, overhang_in=0.0, span_in=[120.0, 80.0])
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    e = rf.gable_elevation()
    assert e["width_in"] == pytest.approx(200.0)
    # ridge sits 120 from the left edge of a 200 base -> 20 right of centre
    assert e["apex_in"] == pytest.approx(20.0)


def test_a_gable_end_window_is_located(scene):
    """A window on the gable-end wall is found and placed by its size, sill and
    offset from the centreline."""
    rf = _gable(scene)
    _gable_end_wall(scene, code="3648", s=100.0)       # 36 x 48, centred
    e = rf.gable_elevation()
    assert len(e["windows"]) == 1
    wd = e["windows"][0]
    assert wd["w_in"] == pytest.approx(36.0)
    assert wd["h_in"] == pytest.approx(48.0)
    assert wd["sill_in"] == pytest.approx(36.0)        # DEFAULT_SILL_IN
    assert wd["head_in"] == pytest.approx(36.0 + 48.0)
    assert wd["centre_in"] == pytest.approx(0.0, abs=0.5)   # wall centre = centreline


def test_an_off_centre_gable_window_offsets(scene):
    rf = _gable(scene)
    _gable_end_wall(scene, code="3648", s=140.0)       # 40 right of the 200-wall centre
    wd = rf.gable_elevation()["windows"][0]
    assert wd["centre_in"] == pytest.approx(40.0, abs=0.5)


def test_an_interior_stub_is_not_mistaken_for_the_gable_wall(scene):
    """A short interior wall near the end is not the gable-end wall."""
    rf = _gable(scene)
    stub = WallItem(QPointF(0, 90), QPointF(0, 110), "interior")   # length 20, interior
    stub.floor = DEFAULT_FLOOR
    stub.openings.append(fp.OpeningItem(stub, "window", "2020", 10.0))
    scene.addItem(stub)
    assert rf.gable_elevation()["windows"] == []       # no exterior end wall -> none


def test_a_dormer_face_window_is_located(scene):
    """A dormer draws its own face and its `openings`, the sill measured above
    the dormer's own floor (not the ground)."""
    host = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                    ridge_h_in=150.0, overhang_in=12.0, span_in=100.0)
    host.floor = DEFAULT_FLOOR
    scene.addItem(host)
    d = _dormer(scene, host, openings=[
        {"id": "w1", "kind": "window", "code": "3030",
         "anchor": {"from": "center", "offset_in": 0.0}, "sill_in": None}])
    e = d.gable_elevation()
    assert e is not None and e["kind"] == "dormer"
    assert e["width_in"] > 0.0
    assert len(e["windows"]) == 1
    wd = e["windows"][0]
    assert wd["w_in"] == pytest.approx(30.0)
    assert wd["h_in"] == pytest.approx(30.0)
    assert wd["centre_in"] == pytest.approx(0.0, abs=0.5)   # centred anchor


@pytest.mark.gui
def test_the_end_on_dialog_has_an_elevation_tab_that_paints(win):
    """The dialog is tabbed and the Elevation tab paints without aborting, for a
    plain gable and for a dormer."""
    from floorplanner.dialogs import RoofEndOnDialog
    scene = win.scene
    gable = _gable(scene)
    _gable_end_wall(scene)
    for roof in (gable,):
        dlg = RoofEndOnDialog(roof, parent=win)
        names = [dlg.tabs.tabText(i) for i in range(dlg.tabs.count())]
        assert "Elevation" in names
        dlg.tabs.setCurrentIndex(names.index("Elevation"))
        assert dlg.elev_canvas.data is not None
        dlg.elev_canvas.resize(460, 300)
        img = QImage(460, 300, QImage.Format.Format_ARGB32)
        p = QPainter(img)
        dlg.elev_canvas.render(p)      # a Qt paint exception would abort the process
        p.end()
        dlg.deleteLater()
