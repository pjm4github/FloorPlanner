"""The 3D viewer's LIGHT SOURCES -- the renderer's piece of 0333 §3.

`build_model` (the furnishing lane) reports `model.lights`; `fp3dq` turns each
into a Qt Quick 3D point/spot light. The render itself cannot be checked here
(an offscreen Qt Quick 3D View3D draws blank without a GPU -- D77), so what is
pinned is the DATA CONTRACT and the pure transforms, which are Qt-free:

  * a light rides the SAME recentre + z-up->y-up remap the meshes take, so it
    sits where its fixture is (0333 §3, the one correctness property);
  * brightness scales from lumens by a single named factor (0333 §3.1);
  * a lens mesh is emissive in its own colour, every other mesh is not
    (0333 §3.4);
  * the `_pbr` finish lookup strips the `#rrggbb` a finish name may carry
    (0329 §4.1 / 0333 §3.5);
  * a plan with no light fixtures reports no lights, so the scene is unchanged
    (0333 §3.3).

Both modules load BY PATH, the way running `fp3dq.py` as a script loads them
(VIEWER_NOTES.md s1) -- importing `floorplanner.viewer.*` would drag in the
editor. `fp3dq`'s PyQt6 imports live inside its widget builder, so the module
and these helpers import with no Qt installed.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "floorplanner" / "viewer"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, VIEWER / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                     # @dataclass / fallback import
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load("fp3d", "fp3d.py")


@pytest.fixture(scope="module")
def fp3dq(fp3d):
    # fp3dq falls back to `from fp3d import ...`; `fp3d` is now in sys.modules.
    return _load("fp3dq_under_test", "fp3dq.py")


# -- the light transform: a light rides the SAME steps as the meshes ---------

def test_a_light_rides_the_same_recentre_and_remap_the_meshes_take(fp3dq):
    ctr = np.array([50.0, 10.0, 48.0])
    world = (120.0, -80.0, 90.0)                # fp3d world frame (x, -plan_y, z)
    light = {"pos": world, "colour": (1.0, 1.0, 1.0), "lumens": 800.0,
             "kind": "point", "cone_deg": 180.0}
    pos, _rgb, _b, _k, _c = fp3dq._light_to_qml(light, ctr)
    # exactly what a mesh vertex at the same world point becomes
    expect = fp3dq._to_qt3d(np.array([world]) - ctr)[0]
    assert pos == pytest.approx(tuple(float(x) for x in expect))


def test_a_light_at_the_model_centre_maps_to_the_origin(fp3dq):
    ctr = np.array([12.0, -34.0, 56.0])
    light = {"pos": (12.0, -34.0, 56.0), "colour": (1.0, 1.0, 1.0),
             "lumens": 800.0, "kind": "point", "cone_deg": 180.0}
    pos, _rgb, _b, _k, _c = fp3dq._light_to_qml(light, ctr)
    assert pos == pytest.approx((0.0, 0.0, 0.0))


def test_brightness_scales_from_lumens_by_the_named_factor(fp3dq):
    ctr = np.zeros(3)
    assert fp3dq.LUMENS_PER_BRIGHTNESS == 800.0
    for lm, want in ((800.0, 1.0), (1600.0, 2.0), (400.0, 0.5), (0.0, 0.0)):
        _p, _rgb, b, _k, _c = fp3dq._light_to_qml(
            {"pos": (0, 0, 0), "colour": (1, 1, 1), "lumens": lm,
             "kind": "point", "cone_deg": 180.0}, ctr)
        assert b == pytest.approx(want)


def test_kind_and_cone_pass_through(fp3dq):
    ctr = np.zeros(3)
    _p, _rgb, _b, kind, cone = fp3dq._light_to_qml(
        {"pos": (0, 0, 0), "colour": (1, 1, 1), "lumens": 800.0,
         "kind": "spot", "cone_deg": 60.0}, ctr)
    assert (kind, cone) == ("spot", 60.0)


def test_light_colour_is_carried_through(fp3dq):
    ctr = np.zeros(3)
    _p, rgb, _b, _k, _c = fp3dq._light_to_qml(
        {"pos": (0, 0, 0), "colour": (0.2, 0.4, 0.6), "lumens": 800.0,
         "kind": "point", "cone_deg": 180.0}, ctr)
    assert rgb == pytest.approx((0.2, 0.4, 0.6))


# -- the emissive lens -------------------------------------------------------

def test_a_lens_mesh_is_emissive_in_its_own_colour(fp3dq):
    assert fp3dq._emissive_rgb("furnishings:light_emit#ff8800") == pytest.approx(
        (1.0, 0x88 / 255.0, 0.0))


def test_a_lens_without_a_hash_falls_back_to_white(fp3dq):
    assert fp3dq._emissive_rgb("furnishings:light_emit") == (1.0, 1.0, 1.0)


def test_every_other_mesh_is_not_emissive(fp3dq):
    for name in ("furnishings:wood_oak", "furnishings:sheen_gloss#f2f2ee",
                 "walls", "floors:slab", "ceilings"):
        assert fp3dq._emissive_rgb(name) is None


# -- the _pbr finish lookup strips the colour suffix -------------------------

def test_pbr_strips_the_colour_suffix_before_the_catalog_lookup(fp3dq):
    mats = {"sheen_gloss": {"roughness": 0.12, "metalness": 0.1},
            "light_emit": {"roughness": 0.30, "metalness": 0.0}}
    assert fp3dq._pbr("furnishings:sheen_gloss#f2f2ee", mats) == (0.12, 0.1)
    assert fp3dq._pbr("furnishings:light_emit#ffe4bf", mats) == (0.30, 0.0)
    # a name without a suffix still resolves (the fix must not break it)
    assert fp3dq._pbr("furnishings:sheen_gloss", mats) == (0.12, 0.1)
    # an unknown finish still gets the default, not a crash
    assert fp3dq._pbr("furnishings:nope#abcdef", mats) == fp3dq.FURN_PBR_DEFAULT


# -- a plan with no lights is unchanged (0333 §3.3) --------------------------

def test_a_plan_with_no_light_fixtures_reports_no_lights(fp3d):
    model = fp3d.build_model({})
    assert model.lights == []
