"""Furnishing catalog integrity and true-scale placement."""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.furnishings


def test_catalog_nonempty(fp):
    assert len(fp.furnishing_catalog()) > 0


def test_specs_have_real_dimensions(fp):
    for s in fp.furnishing_catalog():
        assert s["width_in"] > 0 and s["depth_in"] > 0
        assert s["id"] and s["file"]


def test_item_placed_at_true_scale(fp, scene, first_furnishing):
    spec = fp.furnishing_spec(first_furnishing)
    it = fp.FurnishingItem(first_furnishing, QPointF(100, 100), 0)
    scene.addItem(it)
    assert it.w == pytest.approx(spec["width_in"])
    assert it.d == pytest.approx(spec["depth_in"])


def test_unknown_furnishing_falls_back(fp, scene):
    it = fp.FurnishingItem("does_not_exist_xyz", QPointF(0, 0), 0)
    scene.addItem(it)
    assert it.w > 0 and it.d > 0          # fallback footprint, never crashes


def test_groups_have_all_section(fp):
    groups = fp.furnishing_groups()
    names = [g["name"] for g in groups]
    assert "All" in names
    all_specs = next(g["specs"] for g in groups if g["name"] == "All")
    assert len(all_specs) == len(fp.furnishing_catalog())
