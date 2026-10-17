"""0260-report.md: THE COMPOSE COST (0237-report.md sec0, parked as the
adjacency memo; his word: "Go ahead with the cost tranche from the patch.
Also make sure that when editing and moving roof sections that all walls,
doors and windows as well as interior furnishings are all excluded from the
intersection calculation.")

Three things pinned: the clip is a function of the roofs ALONE (walls,
openings, rooms and furnishings on the scene change nothing about it and
are never walked by it); the arrangement cuts a cell only by the lines of
roofs whose domain can reach it, and every promoted fixture's clip is the
same ground as before; and the cost no longer doubles per roof.
"""
import json
import time
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner import roofclip
from floorplanner.design.bridge import apply_design_to_scene
from floorplanner.roofs import RoofItem, sync_roof_clips

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def _seam_lines(segments):
    """The seams as LINES with the length drawn along each -- `{line: length}`
    with the line keyed by its unit direction (sign made canonical) and its
    offset, rounded -- the same whichever way a seam is cut into pieces."""
    import math
    out = {}
    for x0, y0, x1, y1 in segments:
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        if ln < 1e-6:
            continue
        ux, uy = dx / ln, dy / ln
        if ux < 0 or (abs(ux) < 1e-9 and uy < 0):
            ux, uy = -ux, -uy
        off = x0 * (-uy) + y0 * ux                 # signed distance of the line from the origin
        key = (round(ux, 3), round(uy, 3), round(off, 1))
        out[key] = round(out.get(key, 0.0) + ln, 1)
    return out


def _roofs(scene):
    return [it for it in scene.items() if isinstance(it, RoofItem)]


def _clip_signature(scene):
    """Every roof's visible region (its area) and seams, rounded."""
    sig = {}
    for rf in _roofs(scene):
        region = rf._clip_region
        pts = None
        if region is not None:
            pts = round(region.area(), 3)       # the ground, not its partition
        seams = sorted((round(a.x(), 2), round(a.y(), 2), round(b.x(), 2), round(b.y(), 2))
                       for a, b in rf._seams)
        sig[(round(rf.p1.x(), 1), round(rf.p1.y(), 1), rf.floor)] = (pts, seams)
    return sig


# ---------------------------------------------------------------------------
# the clip sees roofs and nothing else
# ---------------------------------------------------------------------------

def test_the_clip_is_a_function_of_the_roofs_alone(fp, scene, make_room, monkeypatch):
    """Two crossing roofs; then the same two with 200 walls carrying
    openings, 40 furnishings and a room added around them: the clip is the
    same geometry, and nothing but `RoofItem` is ever handed to the
    composer."""
    a = RoofItem(QPointF(0, 100), QPointF(400, 100), span_in=[100.0, 100.0])
    b = RoofItem(QPointF(200, -50), QPointF(200, 250), span_in=[80.0, 80.0],
                 eaves_h_in=96.0, ridge_h_in=120.0)
    for rf in (a, b):
        scene.addItem(rf)
    sync_roof_clips(scene)
    before = _clip_signature(scene)
    assert any(v[0] is not None for v in before.values()), "the two roofs clip each other"

    handed = []
    real = roofclip.compose_building

    def spy(roofs_and_elevations, diag=None):
        handed.extend(type(rf).__name__ for rf, _ in roofs_and_elevations)
        return real(roofs_and_elevations, diag=diag)
    import floorplanner.roofs as roofs_mod
    monkeypatch.setattr(roofs_mod, "compose_building", spy)

    for i in range(200):
        w = fp.WallItem(QPointF(i * 6, 600), QPointF(i * 6 + 5, 720 + (i % 7) * 30), "interior")
        scene.addItem(w)
        if i % 2 == 0:
            w.openings.append(fp.OpeningItem(w, "window" if i % 4 else "door", "2448" if i % 4 else "3280", 60.0))
    for i in range(40):
        scene.addItem(fp.make_furnishing("sofa", QPointF(i * 90, 900)))
    make_room(scene, 1000, 1000, 240, 240, "Den")
    fp.rebuild_all_walls(scene)
    # 0281: the roofs did not change, so the compose's by-value cache
    # answers -- nothing at all is handed to the composer -- with the same
    # clip; that the walls cannot reach the clip is the cache's premise
    sync_roof_clips(scene)
    assert _clip_signature(scene) == before
    assert handed == [], "the roofs did not change: no compose"
    # and a recompose forced past the cache is handed roofs alone
    scene._compose_memo = None
    sync_roof_clips(scene)
    assert _clip_signature(scene) == before
    assert handed and set(handed) == {"RoofItem"}, handed


# ---------------------------------------------------------------------------
# the arrangement: fewer pieces, the same ground
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "threeRidgeFloorplan.json", "threeRidgeShortRidgeFloorplan.json",
    "short-angle-roof.json", "short-angle-roofR2.json", "short-angle-roofR3.json",
    "single-floor-90-roof-gable-end-check.json", "dormer-gable-check.json",
    "wiscaway-2level-stacked-floor.json", "r6c-two-level-tool-check.json",
])
def test_every_promoted_roof_fixture_clips_to_the_same_ground(scene, name):
    """The regions' areas and the seams, against the record each fixture's
    own tests already pin: the cut-by-reach arrangement gives the same
    ground in fewer pieces. Measured against the full-cut arrangement by
    area (a coarser partition of the same region can differ in its vertex
    list, never in its area or its seams)."""
    doc = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    apply_design_to_scene(scene, doc)
    roofs = _roofs(scene)
    assert roofs
    sync_roof_clips(scene)
    sig = _clip_signature(scene)
    # the one invariant the construction needs, pinned directly: the cells
    # the arrangement starts from are pairwise disjoint (the first cut of
    # 0260 laid each roof's domain down as its own cells and let two roofs'
    # copies of the same ground be cut differently -- measured as a region
    # whose cells overlapped each other, 74,000 sq in of double area)
    from floorplanner.roofs import floor_elevation
    diag = {}
    roofclip.compose_building([(rf, floor_elevation(rf.floor)) for rf in roofs], diag=diag)
    cells = diag.get("cells0", [])
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            x = roofclip._convex_intersection(cells[i], cells[j])
            assert not x or roofclip._area(x) <= 0.5, (name, i, j, roofclip._area(x))
    # the reference: recorded under the full-cut arrangement (every line
    # on every cell) before 0260, by docs/evidence's capture of that day
    ref = json.loads((ROOT / "tests" / "data" / "roofclip_ground_0260.json").read_text(encoding="utf-8"))[name]
    assert len(ref) == len(sig)
    for rf in roofs:
        key = (round(rf.p1.x(), 1), round(rf.p1.y(), 1), rf.floor)
        want = ref[f"{key[0]},{key[1]},{key[2]}"]
        got_area, seams = sig[key]
        if want["area"] is None:
            assert got_area is None, (name, key)
        else:
            assert got_area == pytest.approx(want["area"], abs=0.05), (name, key)
        # the seams as GROUND, not as segments: a coarser arrangement draws
        # the same seam line in fewer, longer pieces, so compare each line's
        # drawn length
        got_lines, want_lines = _seam_lines(seams), _seam_lines(want["seams"])
        assert set(got_lines) == set(want_lines), (name, key)
        for line, length in want_lines.items():
            assert got_lines[line] == pytest.approx(length, abs=0.3), (name, key, line)


def test_the_compose_no_longer_doubles_per_roof(fp):
    """The probe's own shape (docs/evidence/roof_compose_cost_probe.py, which
    runs on his plan in the intake directory): the promoted two-level
    fixture plus ridges dropped across the existing ones, timed at each
    count. 0237 measured 0.75 s at 9 roofs and 32 s at 15 -- a
    doubling per roof. The ratio of the last step to the first is now
    bounded well under that curve's 40x; and 15 roofs compose in seconds,
    not half a minute, on a shared runner."""
    from collections import Counter

    from PyQt6.QtWidgets import QGraphicsScene
    scene = QGraphicsScene()
    doc = json.loads((FIXTURES / "wiscaway-2level-stacked-floor.json").read_text(encoding="utf-8"))
    apply_design_to_scene(scene, doc)
    extra = [((300, 540), (900, 540)), ((500, 330), (500, 740)), ((200, 600), (1100, 600)),
             ((600, 360), (600, 700)), ((350, 450), (1000, 450)), ((800, 330), (800, 740)),
             ((250, 680), (1150, 680)), ((950, 340), (950, 720))]
    floor = Counter(rf.floor for rf in _roofs(scene)).most_common(1)[0][0]
    times = []
    for a, b in extra:
        rf = RoofItem(QPointF(*a), QPointF(*b))
        rf.floor = floor
        scene.addItem(rf)
        t = time.perf_counter()
        sync_roof_clips(scene)
        times.append(time.perf_counter() - t)
    assert times[-1] < 12.0, times
    assert times[-1] / max(times[0], 1e-3) < 40.0, times
