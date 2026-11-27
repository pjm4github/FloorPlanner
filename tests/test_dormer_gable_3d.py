"""A dormer's GABLE END must close in 3D even when its face sits on a house
wall (Patrick, 2026-11: the gable ends of his front dormers were open).

The wall there used to cap at the LOWEST roof -- the host it stands on -- so the
dormer gable above was left open, and `_dormer_face` yielded the gable to
`_on_a_wall` expecting a climb that never came. `_wall_under_roofs` now climbs a
wall piece inside a same-level dormer's territory to THAT dormer's surface,
closing the gable; a window in the wall stays a void (no dormer face is
generated, so the 0248 invariant holds). `fp3d.py` is loaded by path, like the
other viewer tests.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_gable_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(window):
    V = [{"id": "wa", "x": 160.0, "y": 240.0}, {"id": "wb", "x": 240.0, "y": 240.0}]
    ops = []
    if window:
        ops = [{"id": "o1", "kind": "window", "code": "2030",
                "anchor": {"from": "v1", "offset_in": 30.0}, "sill_in": 150.0}]
    wall = {"id": "w1", "level": "L1", "v1": "wa", "v2": "wb",
            "type": "exterior", "openings": ops}
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "d", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h"}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": V, "walls": [wall], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def _ext(model):
    return next(m for m in model.meshes if m.name == "walls:exterior")


def test_the_wall_climbs_to_close_the_dormer_gable(fp3d):
    ext = _ext(fp3d.build_model(_doc(window=False), furnishings=False, floors=False))
    # the wall at the dormer face (x=200, world y=-240) rises to the dormer
    # ridge (~240), far above where it would cap at the host roof there (~132)
    v = ext.verts
    near = v[(abs(v[:, 0] - 200.0) < 14.0) & (abs(v[:, 1] + 240.0) < 14.0)]
    assert len(near) and float(near[:, 2].max()) > 220.0, (
        f"the wall did not climb to close the gable: {float(near[:, 2].max()) if len(near) else None}")


def test_a_window_in_the_climbing_wall_stays_a_void(fp3d):
    model = fp3d.build_model(_doc(window=True), furnishings=False, floors=False)
    mesh = _ext(model)
    verts, faces = mesh.verts, mesh.faces
    # a ray across the wall thickness, through the window (x=200, z=165 in the
    # 150..180 opening), must meet no triangle -- the opening is a void
    a = np.array([200.0, -235.0, 165.0])
    b = np.array([200.0, -245.0, 165.0])
    d = b - a
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = a - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    q = np.cross(tv, e1)
    w = np.einsum("j,ij->i", d, q) * inv
    tt = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9) & (tt >= 0) & (tt <= 1)
    assert int(hit.sum()) == 0, "the window in the climbing wall is covered"
    # and the gable still closed above the window
    v = verts
    near = v[(abs(v[:, 0] - 200.0) < 14.0) & (abs(v[:, 1] + 240.0) < 14.0)]
    assert float(near[:, 2].max()) > 220.0


def _cross_level_doc():
    """A dormer drawn on the UPPER floor (L2) but hosted on a roof on the floor
    BELOW (L1), with an L2 wall under its face carrying a window. The dormer is
    anchored to the host's level, so it renders where it would if drawn on L1;
    the L2 wall climbs into it (same drawn level) and its window shows."""
    V = [{"id": "wa", "x": 160.0, "y": 240.0}, {"id": "wb", "x": 240.0, "y": 240.0}]
    wall = {"id": "w1", "level": "L2", "v1": "wa", "v2": "wb", "type": "exterior",
            "openings": [{"id": "o1", "kind": "window", "code": "2020",
                          "anchor": {"from": "v1", "offset_in": 30.0}, "sill_in": 60.0}]}
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "d", "level": "L2", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h"}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {},
            "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                        "height_in": 96.0, "kind": "storey", "reference": False},
                       {"id": "L2", "name": "upper", "elevation_in": 100.0,
                        "height_in": 196.0, "kind": "storey", "reference": False}],
            "vertices": V, "walls": [wall], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def test_a_cross_level_dormer_renders_and_shows_the_floor_below_window(fp3d):
    import numpy as np
    model = fp3d.build_model(_cross_level_doc(), furnishings=False, floors=False)
    ext = _ext(model)
    v = ext.verts
    # the dormer is anchored to its HOST's level (L1 elev 0), so its ridge is at
    # ~240 absolute even though it is drawn on L2 -- the L2 wall climbs to close
    # the gable there
    near = v[(abs(v[:, 0] - 200.0) < 14.0) & (abs(v[:, 1] + 240.0) < 14.0)]
    assert len(near) and float(near[:, 2].max()) > 220.0, (
        f"cross-level gable did not close: {float(near[:, 2].max()) if len(near) else None}")
    # the L2 wall's window (absolute 160..180) is a void in the climbing wall
    verts, faces = ext.verts, ext.faces
    a = np.array([200.0, -235.0, 170.0])
    b = np.array([200.0, -245.0, 170.0])
    d = b - a
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = a - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    q = np.cross(tv, e1)
    w = np.einsum("j,ij->i", d, q) * inv
    tt = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9) & (tt >= 0) & (tt <= 1)
    assert int(hit.sum()) == 0, "the floor-below window is covered in the cross-level gable"


def test_a_cantilever_roof_skirt_replaces_the_flat_floor(fp3d):
    """0360 stage 3 (inc 3), DORMER_EDGE_ORDERINGS notes 7b/7c: on a cantilever
    whose host eave sits BELOW the dormer (an S° row -- W09 is B > C > A > D, so
    the face is past the eave in plan and the overhang drops to the fascia 24in
    below the attic floor), the roof-skirt REPLACES the flat sec 8.4 cantilever
    floor with a sloped roof surface. `skirt_mode` off keeps the flat floor;
    `auto` (the default) and `on` draw the skirt. Loads the committed W09
    evidence fixture, built the same way the app builds a furnishing dormer."""
    import json
    w09 = ROOT / "docs" / "evidence" / "0360-dormer-orderings" / "W09.json"
    base = json.loads(w09.read_text(encoding="utf-8"))

    def names(mode):
        doc = json.loads(json.dumps(base))
        if mode is not None:
            doc["furnishings"][0]["state"]["skirt_mode"] = mode
        model = fp3d.build_model(doc, furnishings=True, floors=True)
        return [m.name for m in model.meshes]

    # default (auto) + explicit auto/on: the skirt stands in for the flat floor
    # (a second `roofs` mesh, no `dormer_floor`)
    for mode in (None, "auto", "on"):
        ns = names(mode)
        assert "dormer_floor" not in ns, mode
        assert ns.count("roofs") == 2, (mode, ns)
    # off: the flat sec 8.4 floor returns, and there is no skirt
    off = names("off")
    assert "dormer_floor" in off
    assert off.count("roofs") == 1


# --- 0380: the climb is gated on the dormer's TERRITORY, not its box alone,
# and the base-drop stops at a roof that already buries the base -------------

def _wall_col_z(model):
    """A function z(px, plan_y) -> (lowest, highest) wall surface at that column,
    by BARYCENTRIC interpolation at the column over every walls:* triangle that
    projects onto it (0380: NOT nearby-vertex, NOT max-z of a containing
    triangle, which over-reads a slanted triangle's far corner). World y =
    -plan y."""
    tris = []
    for m in model.meshes:
        if not m.name.startswith("walls:"):
            continue
        vv, ff = np.asarray(m.verts, float), np.asarray(m.faces, int)
        for a, b, c in ff:
            tris.append((vv[a], vv[b], vv[c]))

    def at(px, py):
        wy, zs = -py, []
        for p0, p1, p2 in tris:
            det = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
            if abs(det) < 1e-9:
                continue
            u = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (wy - p2[1])) / det
            v = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (wy - p2[1])) / det
            w = 1.0 - u - v
            if u < -1e-6 or v < -1e-6 or w < -1e-6:
                continue
            zs.append(u * p0[2] + v * p1[2] + w * p2[2])
        return (min(zs), max(zs)) if zs else (None, None)

    return at


def test_a_cheek_wall_uphill_of_the_valley_stands_to_the_host(fp3d):
    """0380 §3, O1/O2: `climb_dormer` returns a dormer only where a piece lies in
    its TERRITORY cells AND inside its grown wall box. Gating on the box alone
    (0379's tree) let a cheek wall UPHILL of the dormer's valley -- inside the
    box but past the roof's footprint -- be cut at the dormer plane buried in the
    host, leaving open air above it under the main roof. On W01 the cheek at
    x=120 must follow the HOST (149.5 at y=98, falling to the eave 116.5 at
    y=134), not flatten to the dormer eave (116.5, the box-alone fault). The
    committed W01 evidence fixture, built as the app builds a furnishing dormer;
    fail-first against 0379's box-only `climb_dormer`."""
    import json
    w01 = ROOT / "docs" / "evidence" / "0360-dormer-orderings" / "W01.json"
    doc = json.loads(w01.read_text(encoding="utf-8"))
    at = _wall_col_z(fp3d.build_model(doc, furnishings=True, floors=True))
    # 0380 §2 point table, x=120: the host underside, falling to the eave
    want = {98: 149.5, 104: 143.5, 110: 137.5, 116: 131.5,
            122: 125.5, 128: 119.5, 134: 116.5}
    for y, z in want.items():
        _lo, hi = at(120.0, float(y))
        assert hi == pytest.approx(z, abs=0.2), (y, hi, z)
    # the O2 pin: the uphill end stands to the host, NOT the dormer eave
    assert at(120.0, 98.0)[1] == pytest.approx(149.5, abs=0.2)


FROZEN = (Path.home() / "OneDrive" / "Documents" / "FloorPlanner"
          / "wiscaway-roof-build" / "readback-BR3-dormer-rake12.json")


@pytest.mark.skipif(not FROZEN.exists(),
                    reason="Patrick's frozen BR3 plan (a user file, never "
                           "committed); the lean-to corner of 0380 §4 lives on it")
def test_a_face_wall_over_a_lean_to_keeps_its_base(fp3d):
    """0380 §4, O1/O2: the base-drop (0375 §4 B) runs a face/cheek wall DOWN to
    the first roof BELOW its base only where the base stands over open air or a
    lower roof. Where any roof drawn over the piece is AT OR ABOVE the base, that
    roof already buries it: the base is closed and nothing drops. 0379's
    `roof_beneath` took the highest roof at-or-below the base and so skipped the
    roof burying it, dropping through. On Patrick's frozen BR3 plan, `rf4` is a
    lean-to drawn over the face strip at 139-143, above the wall base 134: the
    outer half of the face wall must KEEP its base at 134 (0379 dropped it to
    112.9). Given a HIPPED `rf4` instead, the hip is BELOW the base over the
    outer half, so there the base DOES drop (124.0 / 128.7 / 123.7) while the
    inner half, where the hip is above the base, stays -- the same rule, read
    both ways. The plan is a user file (skipped when absent); fail-first against
    0379's `roof_beneath`."""
    import json
    cols = [(803.0, 805.5), (810.0, 805.5), (942.0, 805.5)]
    base = json.loads(FROZEN.read_text(encoding="utf-8"))

    # lean-to (the plan as drawn): rf4 buries the base; nothing drops
    at = _wall_col_z(fp3d.build_model(base, furnishings=True, floors=True))
    for x, y in cols:
        assert at(x, y)[0] == pytest.approx(134.0, abs=0.3), (x, y, at(x, y))
    # the O2 pin: the frozen cheek at (799, 640) reads the host, 211.2
    assert at(799.0, 640.0)[1] == pytest.approx(211.2, abs=0.3)

    # hipped rf4: the outer half drops to the hip below the base
    doc = json.loads(json.dumps(base))
    for r in doc["roofs"]:
        if r["id"] == "rf4":
            r["ridge"] = [[833.0, 804.0], [911.5, 804.0]]
            r["hip_run_in"] = [36.0, 36.0]
            r["gable"] = [False, False]
    at2 = _wall_col_z(fp3d.build_model(doc, furnishings=True, floors=True))
    for (x, y), want in zip(cols, (124.0, 128.7, 123.7), strict=True):
        assert at2(x, y)[0] == pytest.approx(want, abs=0.5), (x, y, at2(x, y))
