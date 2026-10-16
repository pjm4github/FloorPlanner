"""0277-report.md: the dormer's back-end knob, on a dormer whose FACE stands
outside its host's footprint (Patrick, his garage in
wiscaway2026-10-13R1.json: "unresponsive when I try and click and drag on
the control knob near the top ridge where it joins the roof").

The knob sets the ridge height and the back end is derived where the ridge
meets the host. Its reach was measured from the face; a face 48in past the
host's eave line read a reach of 0.0 and every move was refused, silently.
It is now measured from where the ridge enters the host's footprint, and a
refusal says why in the status bar.

Same host as tests/test_roof_dormer.py: a ridge along x at y=100, 100in
spans, 12in overhang (footprint y -12..212), eaves 96, ridge 150.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofclip import Pt, entry_along, footprint_polygon, _contains
from floorplanner.roofs import GRIP_END_OFFSET_IN, RoofItem

pytestmark = pytest.mark.walls

HOST_SLOPE = (150.0 - 96.0) / 100.0                    # 0.54


def _host(scene, y=100.0):
    rf = RoofItem(QPointF(0, y), QPointF(400, y), eaves_h_in=96.0, ridge_h_in=150.0,
                  overhang_in=12.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _garage(scene, host, face_y=250.0):
    """A gable dormer whose face stands at `face_y` -- past the host's eave
    edge at y=212 when face_y > 212 -- its ridge running up-slope (-y)."""
    d = RoofItem(QPointF(200, face_y), QPointF(200, 140), eaves_h_in=116.0, ridge_h_in=136.0,
                 overhang_in=0.0, span_in=30.0, marker_end=0, host=host)
    d.floor = DEFAULT_FLOOR
    scene.addItem(d)
    return d


def test_entry_along_finds_where_a_ray_enters_the_footprint(scene):
    host = _host(scene)
    up = Pt(0.0, -1.0)
    assert entry_along(host, Pt(200, 150), up) == 0.0, "inside: no distance to enter"
    t = entry_along(host, Pt(200, 250), up)
    assert t == pytest.approx(38.0, abs=1e-5), "212 is the overhung eave edge (boundary-inclusive by 1e-6)"
    assert _contains(footprint_polygon(host), Pt(200, 250 - t))
    assert entry_along(host, Pt(200, 250), Pt(0.0, 1.0)) is None, "pointing away: never"


def test_the_face_outside_the_host_is_the_fixture(scene):
    host = _host(scene)
    d = _garage(scene, host)
    assert not _contains(footprint_polygon(host), Pt(d.p1.x(), d.p1.y()))
    assert d.p2.y() == pytest.approx(100.0 + (150.0 - 136.0) / HOST_SLOPE), \
        "its back end is still derived on the host, as in his file"


def test_the_back_end_knob_moves_a_dormer_whose_face_is_outside_its_host(scene):
    """The fault: refused at every move. Now the knob sets the ridge height
    where the cursor lands on the host's slope, and the back end follows."""
    host = _host(scene)
    d = _garage(scene, host)
    before = d.ridge_h_in
    d.drag_end(1, QPointF(200, 156 - GRIP_END_OFFSET_IN))     # on the grid, inside the host
    assert d.ridge_h_in != before, "the knob did nothing"
    assert d.ridge_h_in == pytest.approx(150.0 - HOST_SLOPE * 56.0)
    assert d.p2.y() == pytest.approx(156.0, abs=1e-6), "the back end lands where it was dragged"
    d.drag_end(1, QPointF(200, 120 - GRIP_END_OFFSET_IN))     # further up the slope
    assert d.ridge_h_in == pytest.approx(150.0 - HOST_SLOPE * 20.0)
    assert d.p2.y() == pytest.approx(120.0, abs=1e-6)


def test_the_knob_still_stops_at_the_hosts_crest(scene):
    """0195-ruling.md sec2's clamp is kept: past the host's ridge the height
    would fold back, so the end stops at the crest."""
    host = _host(scene)
    d = _garage(scene, host)
    d.drag_end(1, QPointF(200, 40 - GRIP_END_OFFSET_IN))      # 60in past the ridge
    assert d.p2.y() >= 100.0 - 1e-3
    assert d.ridge_h_in == pytest.approx(150.0, abs=1e-3)


def test_a_face_inside_the_host_behaves_as_before(scene):
    host = _host(scene)
    d = _garage(scene, host, face_y=190.0)
    d.drag_end(1, QPointF(200, 150 - GRIP_END_OFFSET_IN))
    assert d.ridge_h_in == pytest.approx(150.0 - HOST_SLOPE * 50.0)
    assert d.p2.y() == pytest.approx(150.0, abs=1e-6)


def test_a_refused_drag_says_why(win):
    """A knob that cannot follow the cursor reports it, not silence."""
    win.prepare_headless()
    sc = win.scene
    host = _host(sc)
    d = _garage(sc, host)
    far = _host(sc, y=2000.0)                 # a host the ridge never crosses
    d.host = far
    before = (d.ridge_h_in, QPointF(d.p2))
    d.drag_end(1, QPointF(200, 156 - GRIP_END_OFFSET_IN))
    assert (d.ridge_h_in, d.p2) == before
    assert "never crosses its host roof" in win.statusBar().currentMessage()
