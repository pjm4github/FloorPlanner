"""P1.4 -- `design_from_scene()`: the live scene walked into a v5 `Design`.

Corpus is LEGACY FILES ONLY (`examples/planc1.json`, `examples/sample_plan.json`
and fixture-built scenes), because `symmetricP1.json` / `site_demo.json` are v5
and have no loader until P2.1.

Three properties are pinned here, matching the three rules the walk is built on:
areas agree with `project_from_scene()`; the walk is level-scoped BY
CONSTRUCTION; and the 9" weld is a check that never edits the emitted geometry.
"""
import json
import math
import warnings
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import design_from_scene
from floorplanner.design.validate import check

pytestmark = [pytest.mark.io, pytest.mark.rooms]

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _area_sf(pts):
    """Shoelace area in square feet -- the same basis both sides of every
    comparison here, so a mismatch is a real disagreement, not a unit slip."""
    n = len(pts)
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
                   for i in range(n))) / 2.0 / 144.0


def _walk(source, **kw):
    """`design_from_scene` as a dict, with the weld warning silenced -- the
    tests that care about the weld assert on the report, not the warning."""
    rep = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d = design_from_scene(source, report=rep, **kw)
    return d.to_dict(), rep


def _room_areas(doc):
    v = {x["id"]: (x["x"], x["y"]) for x in doc["vertices"]}
    return {r["name"]: _area_sf([v[e["v"]] for e in r["outline"]])
            for r in doc["rooms"]}


def _project_areas(project):
    """The room areas `project_from_scene()` reports, read off the
    perimeter_corners it mirrors into each room's properties."""
    return {r.name: _area_sf(r.properties["perimeter_corners"])
            for r in project.rooms if r.properties.get("perimeter_corners")}


def _load(fp, win, name):
    win.load_data(json.loads((EXAMPLES / name).read_text(encoding="utf-8")))
    return win


# ---------------------------------------------------------------- the corpus
@pytest.mark.parametrize("name", ["planc1.json", "sample_plan.json"])
def test_room_areas_match_project_from_scene(fp, win, name):
    """THE acceptance: every room's outline area agrees with what the v4 walk
    reports for the same scene, to 0.1 sf."""
    _load(fp, win, name)
    doc, _rep = _walk(win)
    got, want = _room_areas(doc), _project_areas(win.project_from_scene())

    assert set(want) <= set(got), f"rooms lost by the walk: {set(want) - set(got)}"
    for room, sf in want.items():
        assert abs(got[room] - sf) < 0.1, \
            f"{name}: {room} {got[room]:.2f} sf != project's {sf:.2f} sf"


def test_sample_plan_is_clean(fp, win):
    """A well-formed legacy plan walks to a document with NO invariant errors
    and nothing for the weld check to report."""
    _load(fp, win, "sample_plan.json")
    doc, rep = _walk(win)
    assert check(doc, deep=True) == []
    assert rep["unwelded_ends"] == 0
    assert rep["open_edges"] == 0
    assert rep["rooms_without_outline"] == 0


def test_planc1_reports_its_real_faults(fp, win):
    """planc1 carries the same referential faults as its v5 fixture, and the
    walk must REPORT them rather than repair them on the way past.

    Asserted as what it actually reports (per the P1.4 acceptance), not forced
    to []: 17 walls are claimed by an outline whose sides disagree (I6), and
    Hall and M Bath overlap (I11)."""
    _load(fp, win, "planc1.json")
    doc, _rep = _walk(win)
    errs = check(doc, deep=True)

    kinds = {e.split()[0] for e in errs}
    assert kinds == {"I6", "I11"}, f"unexpected fault classes: {sorted(kinds)}"
    assert sum(e.startswith("I6") for e in errs) == 17
    assert [e for e in errs if e.startswith("I11")] == \
        ["I11 rooms 'Hall' and 'M Bath' overlap"]

    # The corruption carried here is the SCENE's, and it is worse than the
    # file's. On disk the two rooms at least differ (Hall 243.5 sf / 18 corners,
    # M Bath 591.6 sf / 24 corners). Load re-detects rooms, the 1.5" divider gap
    # leaks the flood-fill, and BOTH anchors resolve to the one merged region --
    # so they come out as the same 21-vertex loop. I11 is firing on an exact
    # coincidence, not a partial overlap. Repairing that belongs at P2.1.
    loops = {r["name"]: [e["v"] for e in r["outline"]] for r in doc["rooms"]}
    assert set(loops["Hall"]) == set(loops["M Bath"])
    areas = _room_areas(doc)
    assert abs(areas["M Bath"] - areas["Hall"]) < 0.1
    assert abs(areas["Hall"] - 243.5) < 0.1


# ------------------------------------------------------- the weld is a check
def test_weld_is_a_check_not_an_edit(fp, win):
    """The 9" weld never touches the emitted geometry.

    planc1 has four divider walls stopping 1.5" short of the corridor wall.
    They are REPORTED (`unwelded_ends`) and left exactly where the scene has
    them -- welding here would silently move a user's walls at P2.2's save."""
    _load(fp, win, "planc1.json")
    doc, rep = _walk(win)
    assert rep["unwelded_ends"] == 5          # 4 x 1.5" gaps + 1 x 0.001" nudge

    # y = 655.528 is the short end; 654.0 is where a weld would put it
    ys = {round(v["y"], 3) for v in doc["vertices"]}
    assert 655.529 in ys, "the unwelded ends were silently welded"


def test_unwelded_ends_warns_and_strict_raises(fp, win):
    """The finding is surfaced, and `strict=True` escalates it -- the hook
    P1.6's `--verify-design` pulls."""
    _load(fp, win, "planc1.json")
    with pytest.warns(UserWarning, match="disagrees with itself"):
        design_from_scene(win)
    with pytest.raises(ValueError, match="wall end"):
        design_from_scene(win, strict=True)


def test_clean_scene_neither_warns_nor_raises(fp, win):
    """strict=True is silent on a scene that agrees with itself, so P1.6 can
    leave it on for the whole suite."""
    _load(fp, win, "sample_plan.json")
    with warnings.catch_warnings():
        warnings.simplefilter("error")        # any warning fails the test
        design_from_scene(win, strict=True)


# -------------------------------------------------- level-scoped BY CONSTRUCTION
def _two_floor_scene(fp, win, make_room):
    """A room on `ground` and a geometrically IDENTICAL room on `upper`.

    Identical on purpose: overlapping coordinates are exactly what a walk that
    leaked across levels would fuse into one vertex table (defect 12)."""
    win.floors = [fp.Floor("ground"), fp.Floor("upper")]
    win.active_floor = "ground"
    win._sync_floor_state()
    make_room(win.scene, 100, 100, 120, 96, name="Below")
    win.active_floor = "upper"
    win._sync_floor_state()
    make_room(win.scene, 100, 100, 120, 96, name="Above")
    return win


def test_walk_is_level_scoped(fp, win, make_room):
    """No wall, room or vertex ever references another level's ids, and the two
    identical rooms stay two rooms with disjoint geometry."""
    _two_floor_scene(fp, win, make_room)
    doc, _rep = _walk(win)

    assert [lv["name"] for lv in doc["levels"]] == ["ground", "upper"]
    assert {r["name"] for r in doc["rooms"]} == {"Below", "Above"}

    level_of = {v["id"]: v["level"] for v in doc["vertices"]}
    for w in doc["walls"]:
        assert level_of[w["v1"]] == level_of[w["v2"]] == w["level"]
    for r in doc["rooms"]:
        for e in r["outline"]:
            assert level_of[e["v"]] == r["level"]

    # the coincident corners did NOT weld into shared vertices
    by_level = {}
    for r in doc["rooms"]:
        by_level[r["level"]] = {e["v"] for e in r["outline"]}
    (a, b) = by_level.values()
    assert not (a & b), "two levels share a vertex -- the walk leaked"
    assert check(doc, deep=True) == []


def test_empty_level_survives_the_walk(fp, win, make_room):
    """A floor with no items still emits its level -- which is why the roster
    comes from `MainWindow.floors` and is never derived from the scene."""
    win.floors = [fp.Floor("ground"), fp.Floor("attic")]
    win.active_floor = "ground"
    win._sync_floor_state()
    make_room(win.scene, 100, 100, 120, 96, name="Below")
    doc, _rep = _walk(win)
    assert [lv["name"] for lv in doc["levels"]] == ["ground", "attic"]
    assert {r["level"] for r in doc["rooms"]} == {doc["levels"][0]["id"]}


# ------------------------------------------------------------ fixture scenes
def test_fixture_scene_walks_clean(fp, scene, make_room, first_furnishing):
    """A scene built by the fixtures -- no MainWindow, no file -- walks to a
    valid document. Exercises the bare-QGraphicsScene source."""
    room = make_room(scene, 60, 60, 144, 120, name="Study")
    f = fp.FurnishingItem(first_furnishing, QPointF(120, 110))
    scene.addItem(f)
    fp.rebuild_all_walls(scene)

    doc, rep = _walk(scene)
    assert check(doc, deep=True) == []
    assert rep["unwelded_ends"] == 0
    assert [r["name"] for r in doc["rooms"]] == ["Study"]
    assert len(doc["walls"]) == 4
    assert doc["furnishings"][0]["room"] == doc["rooms"][0]["id"]
    assert abs(_room_areas(doc)["Study"] - room.area_sqft) < 0.1


def test_openings_are_reanchored_to_a_named_end(fp, scene, make_room):
    """v4's absolute `s` becomes {from, offset_in}; the opening lands back at
    the same place on the wall."""
    make_room(scene, 0, 0, 240, 120, name="Hall")
    # the 240"-long top wall, named unambiguously: the left wall also touches
    # y = 0 but is only 120" long, which would change the expected offset
    wall = next(w for w in scene.items()
                if isinstance(w, fp.WallItem)
                and w.p1.y() == 0 and w.p2.y() == 0)
    door = fp.OpeningItem(wall, "door", "3280", 100.0)
    wall.openings.append(door)
    fp.rebuild_all_walls(scene)

    doc, _rep = _walk(scene)
    ops = [o for w in doc["walls"] for o in w["openings"]]
    assert len(ops) == 1
    op = ops[0]
    assert op["kind"] == "door" and op["code"] == "3280"
    assert op["anchor"]["from"] in ("v1", "v2")
    assert op["hinge"] in ("v1", "v2", "none")
    assert op["swings_toward"] in ("left", "right")
    # near edge of a 32" opening centred at s=100 sits 84" from the near end
    assert math.isclose(op["anchor"]["offset_in"], 84.0, abs_tol=0.01)
    assert check(doc, deep=True) == []


def test_groups_are_not_emitted_yet(fp, scene, make_room):
    """Groups do not serialize today (defect 3). Emitting a guess would make
    characterization test 3 pass for the wrong reason; both close at P4.5."""
    make_room(scene, 0, 0, 240, 120, name="Hall")
    doc, _rep = _walk(scene)
    assert doc["groups"] == []


def test_document_is_schema_valid(fp, win):
    """Belt and braces: the walk's output validates against the packaged v5
    JSON Schema, not just the referential invariants."""
    from floorplanner.design.validate import schema_errors
    _load(fp, win, "sample_plan.json")
    doc, _rep = _walk(win)
    assert schema_errors(doc) == []
