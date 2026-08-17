"""D70/D71 catch a symbol that fails to PARSE or DRAWS NOTHING. Neither asks
whether what it draws can become a recognisable 3D solid -- `glass_shower`
draws plenty of ink and still extrudes to nothing (all strokes, no closed
fill), and nothing in the suite says so before this file.

THREE PREDICATES, per handoff/0029-ruling.md SS2 (from 0016 SS5d), each
reading `fp3d.extrudability()` -- the ONE production function, so a gate test
and a census can never each derive "fragmented" or "has a region" their own
way and drift:

  1. every catalog symbol has at least one closed FILLED shape (FAILS)
  2. the body is one CONNECTED region, not N fragments (FAILS, `boat_trailer`
     exempted -- its form is `vehicle`, the fix is the loft design already in
     VIEWER_NOTES.md SS5, not a redraw)
  3. a REPORTED census of items with a body but no internal region (REPORTS,
     does not fail -- `box`/`slab` forms are legitimately featureless)

`fp3d.py` is loaded BY PATH, not through `floorplanner`, so this stays
Qt-free exactly as `test_viewer_model.py` already does (VIEWER_NOTES SS1).
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.furnishings

ROOT = Path(__file__).resolve().parent.parent
FURN_DIR = ROOT / "assets" / "furnishings"


def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_extrudability", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load_fp3d()


@pytest.fixture(scope="module")
def manifest():
    return json.loads((FURN_DIR / "manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def census(fp3d, manifest):
    """{id: (filled_count, body_fragments, has_region)} for the whole catalog
    -- computed once per test run and shared by all three predicates below,
    so the (cheap but not free) SVG parse happens 95 times, not 285."""
    out = {}
    for spec in manifest:
        parts, vb = fp3d.svg_outlines(str(FURN_DIR / spec["file"]))
        out[spec["id"]] = fp3d.extrudability(parts, vb)
    return out


# --------------------------------------------------------------------------
# predicate 1 -- at least one closed filled shape
# --------------------------------------------------------------------------
def test_every_symbol_has_a_closed_filled_shape(census):
    """`glass_shower` WAS drawn entirely in strokes (`fill="none"`), so
    `svg_outlines` found nothing to extrude -- confirmed directly, not
    inferred, and it was the one item still on the box-fallback list. Fixed
    2026-08-16 (handoff 0029/0032's redraw): its boundary is now one filled
    rect, the conventional plan-symbol shape (solid outline, a swing arc for
    the door) rather than four boundary lines with a gap. This predicate
    would have caught the original state before the render did; it now
    guards against a regression back to it."""
    empty = sorted(k for k, (filled, _frags, _region) in census.items()
                   if filled == 0)
    assert empty == [], (
        f"symbol(s) with no closed filled shape at all: {empty}")


# --------------------------------------------------------------------------
# predicate 2 -- the body is one connected region
# --------------------------------------------------------------------------
# EXEMPTIONS, each with its own reason -- an exemption without a stated
# reason is how a known finding becomes an ignored one (0029-ruling.md SS5).
FRAGMENTED_EXEMPT = {
    "boat_trailer": (
        "ruled: form is `vehicle`, the one generator 0015-ruling.md did not "
        "retire; the fix is the loft design already in "
        "floorplanner/viewer/VIEWER_NOTES.md SS5, not a redraw of this "
        "open-frame symbol (0025-ruling.md SS5, 0029-ruling.md SS5)"),
    "bicycle": (
        "ruled: 0013-ruling.md SS3 -- \"stays as it is ... a bicycle IS "
        "thin, and a 24x68 box says something far more wrong\" (D79)"),
    "motorcycle": (
        "D79: `vehicle` form, the same population 0012-ruling.md measured "
        "at 3 of 10 built cleanly; likely owner is the vehicle loft, same "
        "as `boat_trailer`, not a redraw of this symbol"),
    "garden_tractor": (
        "D79: `vehicle` form, the same population 0012-ruling.md measured "
        "at 3 of 10 built cleanly; likely owner is the vehicle loft, same "
        "as `boat_trailer`, not a redraw of this symbol"),
    "riding_mower_snow": (
        "D79: `vehicle` form, the same population 0012-ruling.md measured "
        "at 3 of 10 built cleanly; likely owner is the vehicle loft, same "
        "as `boat_trailer`, not a redraw of this symbol"),
    "drill_press": (
        "D79: found building this predicate, not `vehicle` form and no "
        "disposition yet -- column/base sit 9.6% of the viewBox apart, a "
        "real gap, not rounding noise"),
    "water_softener": (
        "D79: found building this predicate, not `vehicle` form and no "
        "disposition yet -- the two tanks sit 5.4% of the viewBox apart, a "
        "real gap, not rounding noise"),
}


def test_every_symbol_body_is_one_connected_region(census):
    """`boat_trailer` extrudes six disconnected slabs and no trailer -- what
    an open-frame plan symbol gives a solid extruder, ruled a `vehicle`-form
    problem, not this predicate's to fix.

    `body_fragments` counts CONNECTED COMPONENTS among the top-level rings'
    bounding boxes (`fp3d.extrudability`'s own docstring has the tolerance
    and why it is not a scalar threshold), not a raw ring count -- a chair's
    seat plus a separate backrest rect is two top-level rings and a
    perfectly ordinary `beside` body, not a fragmented one; measured
    directly, `dining_chair`/`toilet`/`office_chair` and five others with
    two-plus top-level rings all resolve to one component and are not here.

    THE 3% TOLERANCE ITSELF WAS INSPECTED, NOT ASSUMED (0034-ruling.md SS4):
    the closest-pair bounding-box gap was measured for every catalog item
    with two or more top-level shapes, as a percentage of the viewBox's
    smaller dimension. Nothing sits between roughly 1% and 3% -- the
    closest item still called connected is `jointer` at 2.75%, the closest
    still called disconnected is `water_softener` at 8.33%. A margin that
    wide means the exemption list below is not an artifact of where the
    line happens to sit.

    SEVEN ITEMS ARE EXEMPTED, `boat_trailer` plus six found building this
    predicate (0034-ruling.md SS5, filed as D79) -- each by name, each with
    its own stated reason, so the gate is honest about what it is not yet
    enforcing rather than silently loosened."""
    frags = {k: n for k, (_filled, n, _region) in census.items() if n > 1}
    unexempt = {k: n for k, n in frags.items() if k not in FRAGMENTED_EXEMPT}
    assert not unexempt, f"fragmented body, not exempted: {unexempt}"
    assert set(frags) <= set(FRAGMENTED_EXEMPT), (
        "an exemption exists for an item the census no longer flags -- "
        "remove the now-unnecessary exemption")


# --------------------------------------------------------------------------
# predicate 3 -- a reported census, not a gate
# --------------------------------------------------------------------------
def test_report_symbols_with_a_body_but_no_internal_region(census, capsys):
    """DOES NOT FAIL. `box`/`slab` forms are legitimately featureless (a
    trashcan, a nightstand), and a hard failure there would be wrong --
    0029-ruling.md SS2 row 3 is explicit that this row REPORTS.

    Printed so `pytest -s` (or a failure elsewhere in the run) always carries
    the current list; the number is also asserted against the catalog size
    so a census that silently returned nothing would still be caught."""
    no_region = sorted(k for k, (filled, frags, region) in census.items()
                       if filled > 0 and frags <= 1 and not region)
    print(f"\nbody, no internal region ({len(no_region)} of {len(census)}):")
    print(no_region)
    assert 0 < len(no_region) < len(census), (
        "a census reporting nothing, or everything, is not reporting -- "
        "check the instrument before trusting either extreme")
