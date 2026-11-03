"""Phase 4: the per-end overhang (`end_overhang_in`) in the 3D builder. A
gable end's rake overhang extends BOTH the ridge end and the eaves flat
along the axis, so the roof planes overhang the gable wall (a dormer's face
eave is the same thing at its own end). `fp3d.py` is loaded by path, as the
other viewer tests do; `RoofGeom` carries the field so the clipped path and
the compose agree with `RoofItem`.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_end_oh_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(end_oh=None, gable=(True, True)):
    roof = {"id": "rf1", "level": "L1", "ridge": [[0.0, 100.0], [200.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 150.0, "overhang_in": [0.0, 0.0],
            "span_in": [100.0, 100.0], "gable": list(gable), "marker_end": 1}
    if end_oh is not None:
        roof["end_overhang_in"] = end_oh
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [roof]}


def _verts(fp3d, doc):
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    mesh = next(m for m in model.meshes if m.name == "roofs")
    return {(round(float(x), 3), round(float(y), 3), round(float(z), 3))
            for x, y, z in mesh.verts.tolist()}


def test_a_gable_rake_extends_the_ridge_and_the_eaves_at_that_end(fp3d):
    plain = _verts(fp3d, _doc(None))
    raked = _verts(fp3d, _doc([36.0, 0.0]))
    # end 0 is ridge p1 = (0,100), the -x end in the world frame; a 36in rake
    # pushes it (and its two eave corners) out to x = -36, each at its own
    # height -- the ridge at 150, the eaves at 96.
    for p in [(-36.0, -100.0, 150.0), (-36.0, 0.0, 96.0), (-36.0, -200.0, 96.0)]:
        assert p in raked and p not in plain, p
    # the other end (x=200) is untouched -- its rake is 0
    assert (200.0, -100.0, 150.0) in raked and (200.0, -100.0, 150.0) in plain
    # nothing of the plain roof reached x = -36
    assert not any(abs(x + 36.0) < 1e-6 for x, _, _ in plain)


def test_roofgeom_carries_the_dormer_wall_span(fp3d):
    # DORMER_CONROLS.md control C threaded into the Qt-free twin, so fp3d can
    # stand the cheek walls at the wall line, not the eaves line
    RC = fp3d.ROOFCLIP
    base = {"ridge": [[0.0, 0.0], [100.0, 0.0]], "span_in": [60.0, 60.0],
            "overhang_in": [0.0, 0.0], "eaves_h_in": 96.0, "ridge_h_in": 150.0,
            "gable": [True, True]}
    assert RC.RoofGeom.from_record(base).wall_span_in == [60.0, 60.0]   # defaults to span
    g = RC.RoofGeom.from_record({**base, "wall_span_in": [40.0, 36.0]})
    assert g.wall_span_in == [40.0, 36.0]


def _dormer_doc(wall_span=None):
    dormer = {"id": "d", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [60.0, 60.0], "gable": [True, True], "marker_end": 0,
              "host": "h"}
    if wall_span is not None:
        dormer["wall_span_in"] = wall_span
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def test_pulling_the_dormer_wall_in_moves_the_3d_cheeks(fp3d):
    def max_wall_offset(doc):
        model = fp3d.build_model(doc, furnishings=False, floors=False)
        w = next((m for m in model.meshes if m.name == "walls:exterior"), None)
        if w is None:
            return 0.0
        # the dormer's own walls (face + cheeks) reach the wall span off its
        # ridge at x=200; above the host surface (~132), below the ridge (240)
        return max((abs(float(x) - 200.0) for x, y, z in w.verts.tolist()
                    if 159.0 <= -float(y) <= 241.0 and 135.0 < float(z) < 241.0),
                   default=0.0)
    on_eaves = max_wall_offset(_dormer_doc(None))        # walls on the eaves line (60)
    pulled = max_wall_offset(_dormer_doc([30.0, 30.0]))  # walls pulled in to 30
    assert on_eaves == pytest.approx(60.0, abs=1.0), on_eaves
    assert pulled == pytest.approx(30.0, abs=1.0), pulled


def test_the_dormer_footprint_truncates_at_the_eave(fp3d):
    # the roof footprint (what the 3D clip meshes) reaches only wall + overhang,
    # so a dormer with pulled-in walls truncates its roof at the eave
    RC = fp3d.ROOFCLIP
    base = {"ridge": [[200.0, 240.0], [200.0, 160.0]], "eaves_h_in": 180.0,
            "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0], "span_in": [60.0, 60.0],
            "gable": [True, True]}
    full = RC.footprint_polygon(RC.RoofGeom.from_record(base))
    assert max(abs(p.x() - 200.0) for p in full) == pytest.approx(60.0)
    pulled = RC.footprint_polygon(RC.RoofGeom.from_record({**base, "wall_span_in": [30.0, 30.0]}))
    assert max(abs(p.x() - 200.0) for p in pulled) == pytest.approx(30.0)


def test_roofgeom_the_qt_free_twin_extends_its_footprint_too(fp3d):
    # the clipped path (dormers, intersecting roofs) builds from RoofGeom's
    # footprint, so it must carry the field exactly as RoofItem does
    RC = fp3d.ROOFCLIP
    g = RC.RoofGeom.from_record(
        {"ridge": [[0.0, 100.0], [200.0, 100.0]], "span_in": [100.0, 100.0],
         "overhang_in": [0.0, 0.0], "eaves_h_in": 96.0, "ridge_h_in": 150.0,
         "gable": [True, True], "end_overhang_in": [36.0, 0.0]})
    a1, a2 = g._extended_ridge()
    assert round(a1.x(), 3) == -36.0 and round(a2.x(), 3) == 200.0
    xs = [round(p.x(), 3) for p in RC.footprint_polygon(g)]
    assert min(xs) == -36.0 and max(xs) == 200.0


def _dormer_oh_doc(overhang):
    # a gable dormer (cheek walls pulled in to 40 of a 60 span) with an eave
    # overhang, on a big host; the host surface under the overhang must be
    # rebuilt all the way to the cheek walls
    dormer = {"id": "d", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": overhang,
              "span_in": [60.0, 60.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h"}
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def _host_present(fp3d, doc, px, py, host_h):
    # is there a roof triangle at ~host-surface height over plan (px, py)?
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    mesh = next(m for m in model.meshes if m.name == "roofs")
    V, F = mesh.verts.tolist(), mesh.faces.tolist()
    wx, wy = px, -py                              # this file's world frame
    for a, b, c in F:
        A, B, C = V[a], V[b], V[c]
        d = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((B[1] - C[1]) * (wx - C[0]) + (C[0] - B[0]) * (wy - C[1])) / d
        l2 = ((C[1] - A[1]) * (wx - C[0]) + (A[0] - C[0]) * (wy - C[1])) / d
        l3 = 1.0 - l1 - l2
        if l1 < -1e-6 or l2 < -1e-6 or l3 < -1e-6:
            continue
        if abs(l1 * A[2] + l2 * B[2] + l3 * C[2] - host_h) < 1.5:
            return True
    return False


def test_the_host_projects_under_the_dormer_eave_overhang(fp3d):
    # Patrick, 2026-11 (view from underneath): "the host roof must project
    # all the way to the cheek walls. The cheek wall eaves are truncating the
    # host roof under the eaves. Fix that." The dormer stands only within its
    # cheek-wall box (x in 160..240 here); under its eave overhang (walls 40,
    # overhang 20 -> eave at x = 260) the host must still be meshed.
    RC = fp3d.ROOFCLIP
    host_geom = RC.RoofGeom.from_record(
        {"ridge": [[-40.0, 100.0], [440.0, 100.0]], "eaves_h_in": 96.0,
         "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0], "span_in": [170.0, 170.0],
         "gable": [True, True]})
    # a point under the +x cheek eave overhang (between wall x=240 and eave x=260)
    px, py = 250.0, 200.0
    host_h = RC.surface_height(host_geom, RC.Pt(px, py))
    assert _host_present(fp3d, _dormer_oh_doc([20.0, 20.0]), px, py, host_h)
    # and inside the cheek-wall box the dormer stands -- no host there
    assert not _host_present(fp3d, _dormer_oh_doc([20.0, 20.0]), 200.0, 200.0,
                             RC.surface_height(host_geom, RC.Pt(200.0, 200.0)))


def test_a_hip_end_ignores_the_rake(fp3d):
    # end 0 a hip: its own run governs; the rake does not apply, so the mesh
    # is identical with or without end_overhang on that end
    assert _verts(fp3d, _doc([36.0, 0.0], gable=(False, True))) == \
        _verts(fp3d, _doc(None, gable=(False, True)))
