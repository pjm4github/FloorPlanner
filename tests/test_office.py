"""The office (0340): a desk with a computer on it, a task chair, and the
two as a set -- `cabinet_geometry.py`, its kinds, and the 3D model."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings

ROOT = Path(__file__).resolve().parents[1]
OFFICE = ("desk", "office_chair", "office_set")


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_office_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _parts(kind, **over):
    return cg.cabinet_parts(_st(kind, **over))


def _by_name(parts):
    return {p.name: p for p in parts}


def _box(p):
    xs = [x for x, _f in p.quad]
    fs = [f for _x, f in p.quad]
    return min(xs), max(xs), min(fs), max(fs)


@pytest.mark.parametrize("kind", OFFICE)
def test_it_fills_its_footprint_stands_on_the_floor_and_names_each_part_once(kind):
    st = _st(kind)
    parts = cg.cabinet_parts(st)
    w, d = cg.footprint(st)
    xs = [x for p in parts for x, _f in p.quad]
    fs = [f for p in parts for _x, f in p.quad]
    assert (min(xs), max(xs)) == pytest.approx((-w / 2, w / 2))
    assert min(fs) == pytest.approx(0.0) and max(fs) <= d + 1e-9
    assert min(p.z0 for p in parts) == 0.0
    assert len({p.name for p in parts}) == len(parts)
    mats = cg.resolve_materials(st)
    assert all(p.role in mats for p in parts)


def test_a_desk_is_a_top_at_its_height_with_drawers_facing_the_sitter():
    parts = _by_name(_parts("desk"))
    assert parts["top"].z1 == 30.0 and parts["top"].z0 == 30.0 - cg.DESK_TOP_T
    assert _box(parts["top"]) == (-30.0, 30.0, 0.0, 30.0)
    drawers = [p for n, p in parts.items() if n.startswith("drawer-r-")]
    assert len(drawers) == 3
    assert all(_box(p)[3] > 27.0 for p in drawers), "fronts on the sitter's side"
    assert all(p.z1 <= parts["top"].z0 for p in drawers)
    assert "panel-l" in parts and "pedestal-l" not in parts
    both = _by_name(_parts("desk", pedestal="both"))
    assert "pedestal-l" in both and "pedestal-r" in both
    none = _by_name(_parts("desk", pedestal="none"))
    assert "panel-l" in none and "panel-r" in none
    assert not [n for n in none if n.startswith("drawer-")]


def test_the_computer_stands_on_the_desk_and_faces_the_sitter():
    parts = _by_name(_parts("desk"))
    top = 30.0
    for name in ("monitor-foot", "keyboard", "mouse"):
        assert parts[name].z0 == pytest.approx(top), name
    screen, case = parts["monitor-screen"], parts["monitor-case"]
    assert _box(screen)[3] > _box(case)[3], "the screen is on the sitter's side"
    assert _box(parts["keyboard"])[2] > _box(case)[3], "keyboard in front of it"
    assert case.z1 > top + 15.0
    assert len(parts["mouse"].quad) > 4


@pytest.mark.parametrize("computer,names,absent", [
    ("none", (), ("monitor-case", "keyboard", "laptop-base")),
    ("laptop", ("laptop-base", "laptop-lid", "laptop-screen"), ("keyboard",)),
    ("dual", ("monitor-1-case", "monitor-2-case", "keyboard", "mouse"),
     ("monitor-case",)),
])
def test_what_is_on_the_desk_is_a_parameter(computer, names, absent):
    parts = _by_name(_parts("desk", computer=computer))
    for n in names:
        assert n in parts
    for n in absent:
        assert n not in parts
    if computer == "dual":
        a, b = _box(parts["monitor-1-case"]), _box(parts["monitor-2-case"])
        assert a[1] <= b[0], "side by side, not overlapping"


def test_a_taller_desk_lifts_the_computer_with_it():
    parts = _by_name(_parts("desk", height_in=42.0))
    assert parts["top"].z1 == 42.0 and parts["keyboard"].z0 == 42.0


def test_a_chair_has_a_five_star_base_a_seat_at_19_and_a_back_to_40():
    parts = _by_name(_parts("office_chair"))
    assert sum(1 for n in parts if n.startswith("leg-")) == 5
    assert sum(1 for n in parts if n.startswith("caster-")) == 5
    assert parts["seat"].z1 == cg.CHAIR_SEAT_Z == 19.0
    assert max(p.z1 for n, p in parts.items() if n.startswith("back-")) == 40.0
    assert parts["column"].z1 <= parts["seat"].z0
    assert _box(parts["back-c"])[2] == 0.0, "the back is at f = 0"
    assert "arm-l-pad" in parts and "arm-r-pad" in parts
    bare = _by_name(_parts("office_chair", arms=False))
    assert not [n for n in bare if n.startswith("arm-")]
    assert _st("office_chair", width_in=40.0)["width_in"] == 24.0, "one size"


def test_the_chair_colour_is_its_upholstery():
    assert cg.resolve_materials(_st("office_chair"))["upholstery"].startswith(
        "sheen_matte#")
    red = cg.resolve_materials(_st("office_chair", colour="red"))
    assert red["upholstery"] != cg.resolve_materials(
        _st("office_chair"))["upholstery"]


def test_the_set_is_a_desk_with_the_chair_drawn_up_facing_it():
    st = _st("office_set")
    parts = _by_name(cg.cabinet_parts(st))
    assert _box(parts["top"]) == (-27.0, 27.0, 0.0, cg.SET_DESK_D)
    back = _box(parts["chair-back-c"])
    seat = _box(parts["chair-seat"])
    assert back[3] == pytest.approx(36.0), "the chair's back is away from the desk"
    assert seat[2] < cg.SET_DESK_D, "the seat tucks under the edge"
    assert parts["chair-arm-l-pad"].z1 < parts["top"].z0, "arms clear the top"
    ped = _box(parts["pedestal-r"])
    chair_x = [x for n, p in parts.items() if n.startswith("chair-")
               for x, _f in p.quad]
    assert max(chair_x) <= ped[0] + 1e-9, "the chair clears the drawers"
    assert "monitor-case" in parts and "keyboard" in parts
    left = _by_name(cg.cabinet_parts(_st("office_set", pedestal="left")))
    lx = [x for n, p in left.items() if n.startswith("chair-") for x, _f in p.quad]
    assert min(lx) >= _box(left["pedestal-l"])[1] - 1e-9
    assert cg.footprint(_st("office_set", width_in=72.0)) == (72.0, 36.0)


@pytest.mark.parametrize("kind", OFFICE)
def test_each_has_a_dialog_definition_that_stores_only_changes(kind):
    definition = registry.get(kind)
    assert definition.title == "Fixture Properties" and definition.specs()
    assert definition.to_state({}) == {}
    derived, findings = definition.evaluate({}, {})
    assert derived is not None and not F.blocks(findings)
    assert definition.summary({}, derived, {})
    keys = {s.key for s in definition.specs()}
    assert ("computer" in keys) is (kind != "office_chair")
    assert ("arms" in keys) is (kind != "desk")


# -- in the 3D model -----------------------------------------------------------
def _doc(kind, state=None):
    fu = {"id": "f1", "level": "L1", "kind": kind, "room": "r1",
          "pos": [0.0, 0.0], "rotation": 0.0}
    if state is not None:
        fu["state"] = state
    return {"version": 6, "vertices": [], "walls": [],
            "rooms": [{"id": "r1", "level": "L1", "name": "Office",
                       "outline": [], "properties": {}}],
            "levels": [{"id": "L1", "name": "First", "elevation_in": 0.0}],
            "furnishings": [fu]}


@pytest.mark.parametrize("kind", OFFICE)
def test_it_builds_from_parts_in_known_materials_wound_outward(fp3d, kind):
    model = fp3d.build_model(_doc(kind), floors=False)
    meshes = [m for m in model.meshes if m.name.startswith("furnishings:")]
    assert kind in model.stats["cabinet_kinds"]
    assert "furnishings:unknown" not in {m.name for m in meshes}
    for m in meshes:
        a, b, c = (m.verts[m.faces[:, i]] for i in range(3))
        assert float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) > 0.0, m.name
    v = np.vstack([m.verts for m in meshes])
    spec = fp3d.load_catalog()[0][kind]
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(spec["width_in"])
    assert v[:, 2].min() == pytest.approx(0.0)


def test_the_desk_computer_is_in_the_model_and_can_be_taken_off(fp3d):
    with_pc = fp3d.build_model(_doc("desk"), floors=False)
    without = fp3d.build_model(_doc("desk", {"computer": "none"}), floors=False)

    def top(model):
        return max(float(m.verts[:, 2].max()) for m in model.meshes
                   if m.name.startswith("furnishings:"))
    assert top(without) == pytest.approx(30.0)
    assert top(with_pc) > 45.0
    assert any("screen_glass" in m.name for m in with_pc.meshes)
