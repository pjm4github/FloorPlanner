"""R5b -- dormers (0191-ruling.md, adopting 0190-report.md): a dormer is a
`RoofItem` with a `host`. Its back ridge end is DERIVED where its ridge
meets the host's plane (`roofclip.meet_along`) and still written; its two
cheeks and its face are derived plan lines; `compute_roof_clips` is
untouched -- 0190 sec0's own table is asserted here as the receipt; and
`roof_clip_spans` reads a roof's drawn territory (the one 2D change).

The geometry is 0190-report.md sec0's: a host ridge along x at plan y=100
(eaves 96 / ridge 150, span 100, 12in overhang) and a dormer on its south
slope, ridge up-slope at x=200 from the face at y=190, eaves 116 / ridge
136, span 30 either side. Closed form: the ridge meets the host plane at
y = 100 + (150 - 136) / 0.54 = 125.926; the eaves meet it at 162.963.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath
from PyQt6.QtWidgets import QGraphicsScene

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.canonical import canonicalize
from floorplanner.roofclip import RoofGeom, compute_roof_clips, meet_along, seam_length
from floorplanner.roofs import (
    DORMER_EAVES_ABOVE_CEILING_IN, RoofItem, dormer_defaults, host_roof_at,
    roof_clip_spans, snap_to_trace, upslope_direction,
)
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]
HOST_SLOPE = (150.0 - 96.0) / 100.0                    # 0.54
MEET_Y = 100.0 + (150.0 - 136.0) / HOST_SLOPE          # 125.926
EAVES_MEET_Y = 100.0 + (150.0 - 116.0) / HOST_SLOPE    # 162.963


def _room(scene, ceiling=96.0):
    path = QPainterPath()
    path.addRect(0, 0, 400, 200)
    room = RoomItem("Loft", QPointF(200, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling
    scene.addItem(room)
    return room


def _host(scene, eaves_h=96.0, ridge_h=150.0, overhang=12.0):
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=eaves_h,
                  ridge_h_in=ridge_h, overhang_in=overhang, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _dormer(scene, host, face=None, back=None,
            eaves_h=116.0, ridge_h=136.0, span=30.0):
    face = QPointF(200, 190) if face is None else face
    back = QPointF(200, 140) if back is None else back
    d = RoofItem(QPointF(face), QPointF(back), eaves_h_in=eaves_h, ridge_h_in=ridge_h,
                 overhang_in=0.0, span_in=span, marker_end=0, host=host)
    d.floor = DEFAULT_FLOOR
    scene.addItem(d)
    return d


def _pts(segs):
    return sorted({(round(p.x(), 3), round(p.y(), 3)) for s in segs for p in s})


# --------------------------------------------------------------------------
# the derived back end
# --------------------------------------------------------------------------
def test_meet_along_finds_the_closed_form_and_refuses_an_unreachable_height(scene):
    host = _host(scene)
    from floorplanner.roofclip import Pt
    t = meet_along(host, Pt(200, 190), Pt(0, -1), 136.0)
    assert t == pytest.approx(190.0 - MEET_Y, abs=1e-6)
    assert meet_along(host, Pt(200, 190), Pt(0, -1), 151.0) is None, \
        "above the host's own ridge: never met"
    assert meet_along(host, Pt(200, 190), Pt(0, -1), 100.0) is None, \
        "the host is already above this height at the origin"


def test_the_back_end_is_derived_where_the_ridge_meets_the_host(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host, back=QPointF(200, 140))       # sketched short
    assert d.p2.x() == pytest.approx(200.0)
    assert d.p2.y() == pytest.approx(MEET_Y, abs=1e-6)
    assert d.is_dormer() and d.host is host


def test_the_back_end_follows_an_edit_of_the_host(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    host.ridge_h_in = 160.0
    host.rebuild()
    assert d.p2.y() == pytest.approx(100.0 + (160.0 - 136.0) / 0.64, abs=1e-6)


def test_the_back_end_follows_an_edit_of_the_dormer(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    d.ridge_h_in = 126.0
    d.rebuild()
    assert d.p2.y() == pytest.approx(100.0 + (150.0 - 126.0) / HOST_SLOPE, abs=1e-6)


# --------------------------------------------------------------------------
# 0190-report.md sec0's table, as the receipt for "the clip is untouched"
# --------------------------------------------------------------------------
def test_the_clip_partitions_the_dormer_exactly_as_the_read_back_measured(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    assert host._clip_region is not None and d._clip_region is not None
    assert host._clip_region.area() == pytest.approx(86867.0, abs=1.0)
    assert d._clip_region.area() == pytest.approx(2733.0, abs=1.0)
    assert _pts(d._seams) == [(170.0, round(EAVES_MEET_Y, 3)),
                              (200.0, round(MEET_Y, 3)),
                              (230.0, round(EAVES_MEET_Y, 3))]
    assert d._clip_ext[0] == 0.0 and d._clip_ext[1] > 0.0, "the back end is joined"
    assert d.clip_warnings == []


def test_the_pure_clip_agrees_on_document_records(scene):
    host = RoofGeom.from_record({"id": "rf1", "ridge": [[0, 100], [400, 100]],
                                 "eaves_h_in": 96.0, "ridge_h_in": 150.0,
                                 "overhang_in": [12, 12], "span_in": [100, 100]})
    dormer = RoofGeom.from_record({"id": "rf2", "ridge": [[200, 190], [200, MEET_Y]],
                                   "eaves_h_in": 116.0, "ridge_h_in": 136.0,
                                   "overhang_in": [0, 0], "span_in": [30, 30],
                                   "marker_end": 0})
    per = compute_roof_clips([host, dormer])
    assert per[id(dormer)].region.area() == pytest.approx(2733.0, abs=1.0)
    assert seam_length(per[id(dormer)].seams) == pytest.approx(95.3, abs=0.2)


# --------------------------------------------------------------------------
# cheeks and face, in plan
# --------------------------------------------------------------------------
def test_a_dormer_draws_only_its_roof_lines(scene):
    """Patrick's look at the first dormer (2026-09-24): "It should show only
    the roof line" -- no cheek or face lines of its own. Clipped, its back
    end is joined, so the plan lines are the two eaves, the front gable
    line and the ridge; nothing else."""
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    kinds = [k for k, _, _ in d._plan_lines()]
    assert kinds.count("dash") == 3 and kinds.count("ridge") == 1
    assert not hasattr(d, "cheek_lines")


def test_a_selected_dormer_shows_all_five_grips(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    d.setSelected(True)
    assert {g.kind for g in d.grips if g.isVisible()} == set(d.grips[0].KINDS)


def test_the_back_end_grip_sets_the_ridge_height_from_the_host_plane(scene):
    """The knob where the ridge meets the roof (his words): dragging it
    along the ridge picks the meet point; the ridge height becomes the
    host's surface there and the derived back end lands on it. The grip
    sits GRIP_END_OFFSET_IN outside the end, so the cursor is read that
    much inward, and the point lands on the 6in grid."""
    from floorplanner.roofs import GRIP_END_OFFSET_IN
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    assert d.p2.y() == pytest.approx(MEET_Y, abs=1e-6)
    # ridge runs up-slope (-y); aim the meet at plan y=150 (a = 40 from the face)
    d.drag_end(1, QPointF(200, 150 - GRIP_END_OFFSET_IN))
    assert d.ridge_h_in == pytest.approx(150.0 - HOST_SLOPE * 50.0)     # 123
    assert d.p2.y() == pytest.approx(150.0, abs=1e-6)
    # too low to stand (host plane under the eaves): refused, unchanged
    d.drag_end(1, QPointF(200, 189 - GRIP_END_OFFSET_IN))
    assert d.ridge_h_in == pytest.approx(123.0)


def test_deleting_the_host_deletes_its_dormers(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    other = _host(scene)
    host.remove_with_dormers()
    left = [it for it in scene.items() if isinstance(it, RoofItem)]
    assert d not in left and host not in left and other in left


# --------------------------------------------------------------------------
# the territory fix (0191 sec1): fail-first on the read-back's second scene
# --------------------------------------------------------------------------
def test_a_wall_under_a_dormer_is_not_dashed_by_the_host_plane_beneath(scene):
    """Host eaves 80 over a 96in room: at y=185 the host plane is 90.5in.
    Without a dormer that wall dashes end to end (the control). With a
    dormer standing over it (its face beyond the trace at y=190), the
    dormer's territory owns that ground and the host's span is cut away.
    A wall straddling the dormer's edge dashes only OUTSIDE it."""
    _room(scene)
    host = _host(scene, eaves_h=80.0, overhang=12.0)
    wall = WallItem(QPointF(180, 185), QPointF(220, 185), "interior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)
    assert roof_clip_spans(scene, wall) == [(0.0, pytest.approx(40.0))], "control"
    d = _dormer(scene, host, face=QPointF(200, 190), back=QPointF(200, 180),
                eaves_h=110.0, ridge_h=130.0)
    assert d.p2.y() == pytest.approx(100.0 + 20.0 / 0.7, abs=1e-6)
    assert roof_clip_spans(scene, wall) == []
    edge = WallItem(QPointF(120, 185), QPointF(180, 185), "interior")
    edge.floor = DEFAULT_FLOOR
    scene.addItem(edge)
    assert roof_clip_spans(scene, edge) == [(0.0, pytest.approx(50.0))]


def test_a_lone_roof_dashes_exactly_as_before_the_territory_fix(scene):
    """No partner -> no region -> the spans are the raw per-roof answer,
    byte for byte (tests/test_roof_clip.py's own fixture numbers)."""
    _room(scene)
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=80.0,
                  ridge_h_in=132.0, overhang_in=0.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    wall = WallItem(QPointF(50, 0), QPointF(50, 200), "exterior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)
    assert rf._clip_region is None
    thresh = (132.0 - 96.0) / 0.52
    assert roof_clip_spans(scene, wall) == [
        (0.0, pytest.approx(100.0 - thresh)), (pytest.approx(100.0 + thresh), 200.0)]


# --------------------------------------------------------------------------
# the document: `host` end to end
# --------------------------------------------------------------------------
def test_host_round_trips_through_the_document_and_survives_canonical_renumbering(scene):
    _room(scene)
    host = _host(scene)
    _dormer(scene, host)
    doc = design_from_scene(scene).to_dict()
    recs = {r["id"]: r for r in doc["roofs"]}
    dormers = [r for r in recs.values() if r.get("host")]
    assert len(dormers) == 1 and dormers[0]["host"] in recs
    assert dormers[0]["ridge"][1][1] == pytest.approx(MEET_Y, abs=1e-6), \
        "the derived back end is WRITTEN"
    canon = canonicalize(json.loads(json.dumps(doc)))
    ids = {r["id"] for r in canon["roofs"]}
    assert all(r["host"] in ids for r in canon["roofs"] if r.get("host"))
    fresh = QGraphicsScene()
    rep = {}
    apply_design_to_scene(fresh, canon, report=rep)
    roofs = [it for it in fresh.items() if isinstance(it, RoofItem)]
    assert rep["roofs"] == 2 and "roofs_skipped" not in rep
    back = [it for it in roofs if it.is_dormer()]
    assert len(back) == 1 and back[0].host in roofs
    assert back[0].p2.y() == pytest.approx(MEET_Y, abs=1e-6)


def test_a_dangling_host_is_reported_and_the_record_skipped(scene):
    _room(scene)
    host = _host(scene)
    _dormer(scene, host)
    doc = canonicalize(design_from_scene(scene).to_dict())
    for r in doc["roofs"]:
        if r.get("host"):
            r["host"] = "rf99"
    fresh = QGraphicsScene()
    rep = {}
    apply_design_to_scene(fresh, doc, report=rep)
    assert rep["roofs"] == 1
    assert len(rep["roofs_skipped"]) == 1 and "rf99" in rep["roofs_skipped"][0]
    assert all(not it.is_dormer() for it in fresh.items() if isinstance(it, RoofItem))


def test_the_promoted_fixture_loads_with_its_dormer(scene):
    doc = json.loads((ROOT / "fixtures" / "dormer-gable-check.json").read_text())
    rep = {}
    apply_design_to_scene(scene, doc, report=rep)
    roofs = [it for it in scene.items() if isinstance(it, RoofItem)]
    dormers = [it for it in roofs if it.is_dormer()]
    assert rep["roofs"] == 2 and len(dormers) == 1
    assert dormers[0].p2.y() == pytest.approx(MEET_Y, abs=1e-3)


# --------------------------------------------------------------------------
# the tool's helpers
# --------------------------------------------------------------------------
def test_host_roof_at_reads_the_drawn_territory_and_skips_dormers(scene):
    _room(scene)
    host = _host(scene)
    d = _dormer(scene, host)
    assert host_roof_at(scene, QPointF(300, 185), DEFAULT_FLOOR) is host
    assert host_roof_at(scene, QPointF(200, 150), DEFAULT_FLOOR) is None, \
        "under the dormer the host has ceded the ground, and a dormer cannot host"
    assert host_roof_at(scene, QPointF(200, 400), DEFAULT_FLOOR) is None
    assert d.is_dormer()


def test_dormer_defaults_come_from_the_trace_ceiling_and_the_host_pitch(scene):
    _room(scene, ceiling=96.0)
    host = _host(scene, eaves_h=80.0)
    eaves_h, slope = dormer_defaults(scene, host, QPointF(300, 185))
    assert eaves_h == pytest.approx(96.0 + DORMER_EAVES_ABOVE_CEILING_IN)
    assert slope == pytest.approx(0.7)
    assert upslope_direction(host, QPointF(300, 185)) == pytest.approx((0.0, -1.0))
    assert upslope_direction(host, QPointF(300, 50)) == pytest.approx((0.0, 1.0))
    assert upslope_direction(host, QPointF(300, 100)) is None
    trace_y = 100.0 + (150.0 - 96.0) / 0.7
    snapped = snap_to_trace(scene, host, QPointF(300, trace_y + 4.0), 12.0)
    assert snapped is not None and snapped.y() == pytest.approx(trace_y)
    assert snap_to_trace(scene, host, QPointF(300, trace_y + 40.0), 12.0) is None
