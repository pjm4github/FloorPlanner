"""P1.4 `design_from_scene()` and P1.5 `apply_design_to_scene()` -- the scene
<-> v5 `Design` bridge.

Corpus is LEGACY FILES ONLY (`examples/planc1.json`, `examples/sample_plan.json`
and fixture-built scenes), because `symmetricP1.json` / `site_demo.json` are v5
and have no loader until P2.1.

P1.4 pins three properties, matching the three rules the walk is built on: areas
agree with `project_from_scene()`; the walk is level-scoped BY CONSTRUCTION; and
the 9" weld is a check that never edits the emitted geometry.

P1.5 pins the mirror: `scene -> Design -> scene -> Design` is identical at the
second `Design`, and the things that would break it -- coalesce moving geometry,
rooms being re-detected, openings not inverting exactly.
"""
import json
import math
import warnings
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import (
    apply_design_to_scene, design_from_scene, scene_identity_report,
)
from floorplanner.design.validate import check, schema_errors

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
    to []: walls claimed by an outline whose sides disagree (I6), and Hall and
    M Bath overlapping (I11).

    17 -> 13 AT P3.5, and the four that went were never real claims. planc1's
    four divider walls stop 1.5" short of the corridor wall, so each is a
    DANGLING STUB, and the face walk enters a stub and comes straight back out.
    The old tracer kept those excursions in the outline -- which is how Hall and
    M Bath each carried 21 corners, several of them at the free end of a wall
    nowhere near the room. `bridge._prune_spurs` drops them, so the walls only a
    spur ever touched are no longer claimed by a room that does not name them.
    Same fault classes, same collapse, same areas; four fewer bogus claims."""
    _load(fp, win, "planc1.json")
    doc, _rep = _walk(win)
    errs = check(doc, deep=True)

    kinds = {e.split()[0] for e in errs}
    assert kinds == {"I6", "I11"}, f"unexpected fault classes: {sorted(kinds)}"
    assert sum(e.startswith("I6") for e in errs) == 13
    assert [e for e in errs if e.startswith("I11")] == \
        ["I11 rooms 'Hall' and 'M Bath' overlap"]

    # The corruption carried here is the SCENE's, and it is worse than the
    # file's. On disk the two rooms at least differ (Hall 243.5 sf / 18 corners,
    # M Bath 591.6 sf / 24 corners). Load re-detects rooms, the 1.5" divider gap
    # means neither anchor is separately enclosed, and BOTH resolve to the one
    # merged region -- so they come out as the same loop (21 vertices before
    # P3.5's spur pruning, 13 after; identical either way, which is the fault).
    # I11 is firing on an exact coincidence, not a partial overlap. Repairing
    # that belongs at P2.1.
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
    # 4, not 5: the count moved to the 0.6" floor the importer's `ends_moved`
    # uses, so planc1's fifth "move" -- a 0.001" float nudge -- is no longer a
    # gap by the schema's own definition of one vertex. The four real 1.5"
    # divider gaps are unaffected, which is the point of a floor this small.
    assert rep["unwelded_ends"] == 4

    # y = 655.528 is the short end; 654.0 is where a weld would put it
    ys = {round(v["y"], 3) for v in doc["vertices"]}
    assert 655.529 in ys, "the unwelded ends were silently welded"


def test_unwelded_ends_warns_and_strict_raises(fp, win):
    """The finding is surfaced, and `strict=True` escalates it -- the hook
    P1.6's `--verify-design` pulls."""
    _load(fp, win, "planc1.json")
    # MATCH CHANGED AT GATE 3, one line: the old phrase was "disagrees with
    # itself as it arrived", which the reword deleted because it is false for a
    # v5 plan -- the scene does not disagree with itself, it DECOMPOSES the
    # document's shared corners into items that then sit near each other. The
    # assertion still pins that the finding is surfaced; only the words it
    # quotes moved, and it now quotes the stable half of the sentence.
    with pytest.warns(UserWarning, match="join tolerance of a neighbour"):
        design_from_scene(win)
    with pytest.raises(ValueError, match="wall end"):
        design_from_scene(win, strict=True)


def test_the_warning_names_the_cause_and_says_it_once(fp, win):
    """DEFECT 22, the ergonomics half. The message used to say one thing for
    every case -- "expected on a plan loaded from a legacy file" -- which is
    true of the ends a file ARRIVES with and false of the ends an edit tears
    open. And it fired on every debounced snapshot, so a plan that opened clean
    produced a stream of warnings with a moving count, all blaming the file.

    A correct warning that misattributes is worse than none: it teaches people
    to ignore the channel that will one day be right."""
    import json
    import pathlib
    ex = pathlib.Path(__file__).resolve().parent.parent / "examples"
    win.open_document(json.loads((ex / "symmetricP1.json").read_text("utf-8")),
                      interactive=False)

    with warnings.catch_warnings():
        warnings.simplefilter("error")        # opened clean -> silent
        design_from_scene(win)

    # tear one corner open exactly as planc1's dividers are torn: pull a wall
    # 1.5" back ALONG ITS OWN AXIS off a shared corner, so its end now stops
    # short of the neighbour's body. That is inside the 9" join tolerance and
    # more than the 0.6" noise floor, which is what the counter counts.
    at = {}
    for it in win.scene.items():
        if isinstance(it, fp.WallItem):
            for a in ("p1", "p2"):
                at.setdefault((round(getattr(it, a).x(), 3),
                               round(getattr(it, a).y(), 3)), []).append((it, a))
    (w, a) = next(v[0] for v in at.values() if len(v) >= 2)
    u, p = w.unit(), getattr(w, a)
    back = 1.5 if a == "p1" else -1.5
    # DETACH the end -- a fresh corner, sharers left where they are. That is
    # the tear being built, and it is what `setattr(w, a, ...)` did here until
    # P4.5 retired the p1/p2 setters. Relocating instead would carry the
    # neighbour along and there would be no tear to warn about.
    w.detach_end(a, QPointF(p.x() + u.x() * back, p.y() + u.y() * back))

    with pytest.warns(UserWarning, match="NEW") as rec:
        design_from_scene(win)
    assert "not the legacy-load case" in str(rec[0].message),         "an edit-induced tear was blamed on the file"

    with warnings.catch_warnings():
        warnings.simplefilter("error")        # same state -> not repeated
        design_from_scene(win)


def test_a_legacy_plan_is_blamed_on_the_file_not_on_an_edit(fp, win):
    """The other side of the same split: what planc1 arrives with is the
    file's, and the message must go on saying so."""
    _load(fp, win, "planc1.json")
    with pytest.warns(UserWarning, match="OPENED with") as rec:
        design_from_scene(win)
    assert "legacy" in str(rec[0].message)


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


def test_ids_are_canonical_not_stacking_order(fp, scene, make_room):
    """Ids are minted in geometric order, so z-order cannot rewrite the
    document. Without this, `Bring to front` would change every id -- and the
    P1.5 round trip below could not hold, since rebuilding turns each split
    segment into its own item and reorders the walk."""
    make_room(scene, 0, 0, 240, 120, name="Hall")
    before, _ = _walk(scene)
    walls = [w for w in scene.items() if isinstance(w, fp.WallItem)]
    walls[0].setZValue(walls[0].zValue() + 50)     # bring one wall to the front
    after, _ = _walk(scene)
    assert before == after


# =============================================================== P1.5: apply
def _apply(target, doc, **kw):
    rep = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        apply_design_to_scene(target, doc, report=rep, **kw)
    return rep


@pytest.mark.parametrize("name", ["sample_plan.json", "planc1.json"])
def test_round_trip_is_identical_at_the_second_design(fp, win, name):
    """THE P1.5 acceptance: scene -> Design -> scene -> Design, identical.

    planc1 is included deliberately. A corrupt plan must round-trip as
    faithfully as a clean one -- if apply quietly repaired the Hall/M Bath
    collision, the second Design would be 'better' and the bridge would be
    lying about what it holds."""
    _load(fp, win, name)
    d1, _ = _walk(win)
    _apply(win, d1)
    d2, _ = _walk(win)
    assert d1 == d2


def test_apply_does_not_coalesce(fp, win):
    """`apply_project_to_scene` runs the merge sweep; this must not.

    Coalesce MOVES geometry -- it re-snaps the survivor's endpoints onto the 6"
    on-centre grid independently of their neighbours (walls.py:200-201, the
    corrected F5 mechanism). One pass and the second Design diverges from the
    first through no fault of the bridge. Pinned with an off-grid plan, where a
    re-snap would be unmissable."""
    win.floors = [fp.Floor("default")]
    win.active_floor = "default"
    win._sync_floor_state()
    # 205 x 101 at (7, 3): no corner sits on the 6" wall-snap grid
    for a, b in [((7, 3), (212, 3)), ((212, 3), (212, 104)),
                 ((212, 104), (7, 104)), ((7, 104), (7, 3))]:
        win.scene.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    fp.rebuild_all_walls(win.scene)
    d1, _ = _walk(win)
    _apply(win, d1)

    xs = {round(v["x"], 4) for v in _walk(win)[0]["vertices"]}
    ys = {round(v["y"], 4) for v in _walk(win)[0]["vertices"]}
    assert xs == {7.0, 212.0} and ys == {3.0, 104.0}, \
        "apply moved off-grid geometry -- coalesce (or a weld) ran"


def test_apply_does_not_redetect_rooms(fp, win):
    """Rooms take their corners, path and area from the stored outline.

    The guard has to survive a later rebuild too, not just apply itself: the
    room's detection memo is primed, so `rebuild_all_walls` leaves the stored
    outline alone instead of flood-filling over it."""
    _load(fp, win, "planc1.json")
    d1, _ = _walk(win)
    _apply(win, d1)

    rooms = {r.name: r for r in win.scene.items() if isinstance(r, fp.RoomItem)}
    # Hall and M Bath share one region in this plan; re-detection would give
    # them a different (and different-sized) outline than the document holds
    doc_rooms = {r["name"]: r for r in d1["rooms"]}
    for name, room in rooms.items():
        assert len(room.corners) == len(doc_rooms[name]["outline"])

    fp.rebuild_all_walls(win.scene)            # must not overwrite the outlines
    d2, _ = _walk(win)
    assert d1 == d2


def test_openings_invert_exactly(fp, win):
    """anchor -> s must exactly invert s -> anchor, on every opening in the
    corpus. An off-by-half-width would show up as a door sliding ~1" per
    save/load cycle once P2.2 makes this the save path."""
    _load(fp, win, "planc1.json")
    d1, _ = _walk(win)
    n = sum(len(w["openings"]) for w in d1["walls"])
    assert n >= 20, f"corpus got weaker: only {n} openings"

    rep = _apply(win, d1)
    assert rep["openings_failed"] == []
    d2, _ = _walk(win)
    for w1, w2 in zip(d1["walls"], d2["walls"], strict=True):
        assert w1["openings"] == w2["openings"]


def test_apply_sets_floor_from_the_level_not_the_global(fp, win, make_room):
    """Every item's `floor` is assigned from its level explicitly.

    The `active_floor()` global that constructors read lies during a load --
    that is why `mainwindow.py:1348` needs its band-aid. Here the active floor
    is deliberately set to the WRONG one before applying, so anything trusting
    the global lands on the wrong floor."""
    _two_floor_scene(fp, win, make_room)
    d1, _ = _walk(win)

    win.active_floor = "upper"                 # the global now disagrees with
    win._sync_floor_state()                    # every ground-floor item
    _apply(win, d1)

    lname = {lv["id"]: lv["name"] for lv in d1["levels"]}
    want = {r["name"]: lname[r["level"]] for r in d1["rooms"]}
    for r in win.scene.items():
        if isinstance(r, fp.RoomItem):
            assert r.floor == want[r.name]
    # and the walls/furnishings landed on their own levels too
    d2, _ = _walk(win)
    assert d1 == d2


def test_apply_reports_an_opening_it_cannot_place(fp, scene, make_room):
    """An opening that will not fit is collected and surfaced, not dropped by a
    silent `except ValueError: continue` (the v4 path's 13 sites, replaced at
    P3.6). `strict=True` escalates it, as on the walk side."""
    make_room(scene, 0, 0, 240, 120, name="Hall")
    doc, _ = _walk(scene)
    v = {x["id"]: (x["x"], x["y"]) for x in doc["vertices"]}
    wall = max(doc["walls"],                   # the 240" run, unambiguously
               key=lambda w: math.dist(v[w["v1"]], v[w["v2"]]))
    wall["openings"] = [{"id": "o1", "kind": "door", "code": "9980",
                         "anchor": {"from": "v1", "offset_in": 0.0}}]

    rep = _apply(scene, doc)                   # 99" door in a 240" wall: fits
    assert rep["openings_failed"] == []
    assert sum(len(w.openings) for w in scene.items()
               if isinstance(w, fp.WallItem)) == 1

    wall["openings"][0]["code"] = "99980"      # 999" door fits nowhere
    rep = _apply(scene, doc)
    assert len(rep["openings_failed"]) == 1 and "o1" in rep["openings_failed"][0]
    with pytest.raises(ValueError, match="o1"):
        apply_design_to_scene(scene, doc, strict=True)


def test_apply_from_a_bare_scene_round_trips(fp, scene, make_room,
                                             first_furnishing):
    """The bare-QGraphicsScene path (no MainWindow, no floor roster)."""
    make_room(scene, 60, 60, 144, 120, name="Study")
    scene.addItem(fp.FurnishingItem(first_furnishing, QPointF(120, 110)))
    fp.rebuild_all_walls(scene)
    d1, _ = _walk(scene)
    _apply(scene, d1)
    d2, _ = _walk(scene)
    assert d1 == d2
    assert check(d2, deep=True) == []


def test_apply_accepts_a_design_object(fp, win):
    """`apply_design_to_scene` takes a `Design` as well as a plain dict, so P2.1
    can hand it the parsed document without a to_dict() detour."""
    from floorplanner.design.model import Design
    _load(fp, win, "sample_plan.json")
    d1, _ = _walk(win)
    _apply(win, Design.from_dict(d1))
    assert _walk(win)[0] == d1


def test_a_v5_plan_does_not_warn_about_its_own_decomposition(fp, win):
    """GATE 3: the opened-with warning is silent for a v5 plan, because there is
    nothing the user could do about it that would change the file.

    MEASURED on `planc1TestV5.json`, which opens with 5 such ends:
      * Edit > Coalesce all walls now takes the scene count 5 -> 0;
      * the document's own near-vertex gaps stay 4 -> 4;
      * the saved file is byte-identical, 62 vertices either way.
    The count describes how the SCENE decomposes the walls into items, and
    merging collinear runs removes the ends that would weld without moving a
    coordinate. A warning that a command can silence without repairing anything
    is worse than no warning.

    The legacy branch still warns -- there the ends really are the file's own
    unwelded coordinates and the command really does close them (pinned by
    `test_a_legacy_plan_is_blamed_on_the_file_not_on_an_edit`), and an EDIT that
    tears the network still warns (pinned by
    `test_the_warning_names_the_cause_and_says_it_once`)."""
    import json
    import pathlib
    ex = pathlib.Path(__file__).resolve().parent.parent / "examples"
    doc = json.loads((ex / "planc1TestV5.json").read_text(encoding="utf-8"))
    win.open_document(doc, interactive=False)

    rep = {}
    with warnings.catch_warnings():
        warnings.simplefilter("error")        # any warning fails the test
        design_from_scene(win, report=rep)
    # the finding is still COUNTED -- it is telemetry, not a secret
    assert rep["unwelded_ends"] == 5, \
        "the count itself must survive; only the user-facing warning is silent"


# ---------------------------------------------------------------------------
# D48 (G2) -- the SCENE-level identity check.  `design_from_scene` welds on the
# way out, so a scene whose corners are not shared at all emits a document all
# fifteen invariants accept.  These two pin the instrument that looks at the
# difference: loud on the known-bad product, silent on a clean plan.
# REPORT-ONLY -- it gates nothing and no operation calls it.
# ---------------------------------------------------------------------------
def test_scene_identity_is_silent_on_a_clean_plan(fp, win):
    """A plan whose corners ARE shared reports nothing.

    The verdict is negative ("no split points"), so its precondition is
    asserted first -- and it is the precondition that matters here, because an
    EMPTY scene reports nothing just as loudly.  D43's own lesson, applied on
    the day it was measured.
    """
    _load(fp, win, "sample_plan.json")
    rep = scene_identity_report(win)

    # PRECONDITION -- there are ends to disagree about, and points to share.
    assert rep["ends"] > 0, "no wall ends: the verdict below would be vacuous"
    assert rep["points"] < rep["ends"], \
        "no point carries two ends: nothing here could be shared or split"

    assert rep["split"] == []
    assert rep["extra_vertices"] == 0


def test_scene_identity_reports_the_fragment_product(fp, win):
    """The known-bad case: `fragment` builds a wall loop per region with no
    dedup, so coincident corners are NOT the same `Vertex` (D47).

    The register's measurement is 20 distinct vertices on 10 geometric points.
    This asserts the SHAPE that measurement describes -- more vertices than
    points, at points shared by several walls -- rather than the two integers,
    which belong to D47's own probe and change when D47 lands.
    """
    _overlapping_rooms_for_identity(fp, win)
    win.room_boolean("fragment")

    rep = scene_identity_report(win)

    # PRECONDITION -- the product exists and has coincident corners at all.
    assert rep["ends"] > 0
    assert rep["points"] > 0

    assert rep["split"], "the fragment product's corners are not shared, " \
                         "so the check must report them"
    assert rep["extra_vertices"] > 0
    worst = rep["split"][0]
    assert worst["vertices"] > 1
    assert worst["walls"] > 1, "a split point should be claimed by several walls"

    # and the document the walk emits from that same scene is still clean --
    # which is the whole point of D48: check() never saw this.
    doc, _rep = _walk(win)
    assert check(doc, deep=True) == [], \
        "if this ever fails, the document check has grown teeth and D48's " \
        "premise needs re-reading"


def _overlapping_rooms_for_identity(fp, win):
    """Two 10x8 rooms overlapping by 4x4 -- the input `fragment` exists to
    resolve.  A local copy of test_rooms.py's helper: sharing it across test
    modules would couple two files that pin different properties, and the
    overlap is three lines."""
    sc = win.scene

    def mk(x, y, w, h, name):
        corners = [QPointF(x, y), QPointF(x + w, y),
                   QPointF(x + w, y + h), QPointF(x, y + h)]
        r = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2),
                        fp.room_path_from_corners(corners),
                        fp.poly_area_sqft(corners), corners=corners)
        sc.addItem(r)
        return r

    r1 = mk(0, 0, 120, 96, "Room 1")
    r2 = mk(72, 48, 120, 96, "Room 2")
    # The overlap is the POINT of this fixture, so declare it as the accepted
    # baseline for shadow mode -- otherwise the scene trips I11 "two placed
    # rooms overlap" at teardown, which would be true but useless: the overlap
    # was constructed here, not introduced by anything under test.
    from floorplanner.design.verify import rebase
    rebase(win)
    # the selection order `room_boolean` consumes. Without it the op has no
    # input and silently does nothing -- which is exactly how the first draft
    # of this fixture produced a scene with zero walls.
    win._sel_order = [r1, r2]
    return r1, r2


# -- D57: face_at handed _walls_of a report of the wrong shape -----------------

WISCAWAY = Path(__file__).resolve().parent.parent / "fixtures" / "wiscaway2026-08-08.json"


def _plan_with_a_straddling_opening(fp, win):
    """Load the plan that actually reaches `_walls_of`'s `if straddles:` branch.

    A REAL PLAN, deliberately. Three synthetic constructions were tried first --
    two welded collinear walls with the door overhanging the first; one long run
    with a door and then a T forced through the doorway; and both went through
    `rebuild_all_walls`, which re-seats the opening so no straddler survives to
    the walk. Building a straddler by hand builds the SYMPTOM. This plan has the
    cause: a 48" pocket door drawn on a continuous 210" run that a junction
    later landed inside.

    `rebase` because the plan carries a known I7 -- that fault IS the trigger,
    and shadow mode would otherwise fail the test for the very condition it
    exists to exercise (the same declaration `_overlapping_rooms` makes).
    """
    from floorplanner.design.verify import rebase
    win.load_path(str(WISCAWAY))
    rebase(win)
    return win.scene


def test_the_wiscaway_fixture_is_still_dirty_in_exactly_the_way_that_matters():
    """THE FIXTURE IS RETAINED **BECAUSE** IT FAILS, and this is what says so.

    `fixtures/wiscaway2026-08-08.json` carries `I7 opening o29 runs off wall
    w90` -- a 48" pocket door straddling the welded junction at `v90`. That
    fault is the ONLY reason the plan reaches `_walls_of`'s `if straddles:`
    branch, and reaching that branch is the whole point of the D57 test below.
    Three synthetic scenes were tried and none of them got there.

    So the fixture is load-bearing, and a good-faith repair of the door would
    leave the D57 test GREEN WHILE EXERCISING NOTHING. This is the same shape
    as `KNOWN_UNCLEAN` in `test_schema.py` -- an exemption that names its fault
    and fails if the fault is fixed -- written here because `fixtures/` sits
    outside the corpus tests by construction, so that list cannot cover it.

    IF THIS TEST FAILS, DO NOT "FIX" IT. Either the door was repaired (restore
    it, or find another plan that reaches the branch and re-point both tests) or
    `check` changed. Laundering the fixture hides the trigger.
    """
    doc = json.loads(WISCAWAY.read_text(encoding="utf-8"))
    assert schema_errors(doc) == [], "the fixture must stay schema-VALID"
    errs = check(doc, deep=True)
    assert [e for e in errs if e.startswith("I7")], (
        f"wiscaway no longer trips I7 -- the D57 test's branch is now "
        f"unreachable and that test is vacuous. Now reports: {errs}")


@pytest.mark.geometry
def test_face_at_survives_an_opening_no_segment_can_hold(fp, win):
    """D57. FAIL-FIRST: before the fix this raises

        AttributeError: 'int' object has no attribute 'append'

    at `bridge.py:589`, because `face_at` passed `defaultdict(int)` where
    `_walls_of` needs `openings_failed` to be a LIST.

    IN THE APP THAT ABORTS THE PROCESS -- PyQt6 calls `qFatal` on an unhandled
    exception inside a Qt virtual, so the window vanishes with no traceback and
    the user reports "it crashed". This calls the production function directly,
    one level below the virtual, so the failure is an ordinary red rather than a
    dead runner: a receipt a silent abort can pass through is not a receipt.
    """
    sc = _plan_with_a_straddling_opening(fp, win)

    # PRECONDITION, established through the caller that WORKS: the scene really
    # does contain an opening no segment can hold. Without this the verdict
    # below is about a branch that was never entered.
    rep = {}
    design_from_scene(win, report=rep)
    assert rep["openings_failed"],         "no opening straddles a junction -- the branch under test is unreached"

    # THE VERDICT: detection must not raise. Returning None would be fine; the
    # defect is the AttributeError, not the answer.
    fp.detect_room(sc, QPointF(1059, 555))


@pytest.mark.geometry
def test_both_walls_of_callers_pass_the_same_report_shape(fp, win):
    """The cause, asserted directly rather than only through its symptom.

    `_walls_of` needs a report whose `openings_failed` is a LIST and whose
    `openings_failed_ids` is a SET. There were two spellings of that shape, one
    of them wrong; there is now ONE initialiser and both callers use it.

    Worth pinning rather than trusting: writing this test produced a THIRD
    hand-written spelling of the same dict, which promptly failed on a key it
    had not thought to include. That is the drift the single definition exists
    to stop.
    """
    from floorplanner.design.bridge import _new_walk_report
    rep = _new_walk_report()
    assert isinstance(rep["openings_failed"], list)
    assert isinstance(rep["openings_failed_ids"], set)

    report = {}
    design_from_scene(win, report=report)
    assert isinstance(report["openings_failed"], list)
    assert isinstance(report["openings_failed_ids"], set)
