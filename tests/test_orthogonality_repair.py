"""The wall orthogonality REPAIR -- 0066-ruling.md item C, unblocked by
0082-ruling.md's three amendments to 0079-report.md's read-back:

  sec2 WITHDRAWS 0066 sec5's refuse-to-start clause (the repair now runs on
       any document, even one that already fails `check()`, and rolls back
       only on a violation that is genuinely NEW);
  sec3 requires the conflict predicate to be RE-EVALUATED before each wall,
       against the document as mutated so far in the same batch -- a stale,
       precomputed-up-front predicate misses a wall this same batch just
       straightened onto axis;
  sec4 requires the before/after differential to compare on a STABLE KEY
       (invariant code + subject ids), not the rendered message, because the
       repair changes a neighbouring wall's length and a pre-existing
       violation re-rendering with different numbers must not look new.

0084-ruling.md corrects two things `0083-report.md` got wrong by actually
running the built repair rather than re-deriving the spec:

  sec1 RESTORES `T = 1/16"` as the candidacy filter `0066-ruling.md` sec3
       ruled and `0083` dropped -- a near-axis wall AT OR ABOVE `T` is
       reported in `over_t`, never a candidate, regardless of conflict;
  sec2 ADDS an orthogonality post-condition: no wall's OWN deviation may
       end up worse than before the repair ran, even a wall the repair
       never chose to touch -- `check()`'s invariants never guarded this.

Item B (the report, `wall_orthogonality`/`orthogonality_bands`) is covered
in `test_orthogonality.py` and is not repeated here.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.design.validate import (
    REPAIR_T_IN,
    check,
    choose_repair_endpoint,
    repair_wall_orthogonality,
    wall_angle_deviation_deg,
    wall_orthogonality,
    wall_repair_conflict,
    _invariant_key,
)

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parent.parent


def _doc(vertices, walls, level="L1"):
    """A minimal but `check()`-able v5 document -- the same shape
    `test_topology_ops.py`'s `_design` helper builds, as a plain dict
    rather than a `Design` (the repair operates on the dict directly)."""
    return {
        "levels": [{"id": level, "name": "Level", "elevation_in": 0}],
        "vertices": vertices, "walls": walls,
        "rooms": [], "furnishings": [], "groups": [],
    }


def _v(vid, x, y, level="L1"):
    return {"id": vid, "level": level, "x": x, "y": y}


def _w(wid, v1, v2, level="L1", type_="interior", openings=None):
    row = {"id": wid, "v1": v1, "v2": v2, "level": level, "type": type_}
    if openings:
        row["openings"] = openings
    return row


def _deg_of(doc, wall_id):
    V = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    w = next(x for x in doc["walls"] if x["id"] == wall_id)
    return wall_angle_deviation_deg(V[w["v1"]], V[w["v2"]])


# ---------------------------------------------------------------------------
# wall_repair_conflict / choose_repair_endpoint -- 0079-report.md sec2(b)(c)
# ---------------------------------------------------------------------------

def test_an_isolated_near_axis_wall_conflicts_nowhere():
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0.5)],
        walls=[_w("w1", "v1", "v2")],
    )
    assert wall_repair_conflict(doc, "w1", "v1") is False
    assert wall_repair_conflict(doc, "w1", "v2") is False
    assert choose_repair_endpoint(doc, "w1") == "v1"


def test_a_shared_exactly_axis_neighbour_conflicts_one_end_only():
    """v1 carries an exactly-horizontal wall (w0); straightening w1 by
    moving v1's y would tilt it off axis -- v2 is free, so THAT is the
    endpoint chosen, exactly 0066-ruling.md sec4's own example."""
    doc = _doc(
        vertices=[_v("v0", -100, 0), _v("v1", 0, 0), _v("v2", 100, 0.5)],
        walls=[_w("w0", "v0", "v1"), _w("w1", "v1", "v2")],
    )
    assert wall_repair_conflict(doc, "w1", "v1") is True
    assert wall_repair_conflict(doc, "w1", "v2") is False
    assert choose_repair_endpoint(doc, "w1") == "v2"


def test_both_ends_conflicted_refuses_the_whole_wall():
    doc = _doc(
        vertices=[_v("v0", -100, 0), _v("v1", 0, 0),
                  _v("v2", 100, 0.5), _v("v3", 200, 0.5)],
        walls=[_w("w0", "v0", "v1"), _w("w1", "v1", "v2"),
               _w("w2", "v2", "v3")],          # exactly horizontal at v2 too
    )
    assert wall_repair_conflict(doc, "w1", "v1") is True
    assert wall_repair_conflict(doc, "w1", "v2") is True
    assert choose_repair_endpoint(doc, "w1") is None


# ---------------------------------------------------------------------------
# _invariant_key -- 0082-ruling.md sec4: code + subject ids, not the message
# ---------------------------------------------------------------------------

def test_invariant_key_ignores_the_rendered_geometry():
    a = "I7  opening o26 runs off wall w68 (48.3..108.3 of 95.5)"
    b = "I7  opening o26 runs off wall w68 (50.1..110.1 of 97.3)"
    assert _invariant_key(a) == _invariant_key(b)


def test_invariant_key_still_separates_different_subjects():
    a = "I14 wall w87 end v92 lies on wall w85 but is not a vertex of it (unwelded T)"
    b = "I14 wall w87 end v93 lies on wall w85 but is not a vertex of it (unwelded T)"
    assert _invariant_key(a) != _invariant_key(b)


def test_invariant_key_captures_i11s_quoted_room_names():
    """I11 names rooms, not ids ("rooms 'Kitchen' and 'Hall' overlap") --
    without pulling the quoted names in, every I11 violation would collapse
    onto one key regardless of which two rooms overlap."""
    a = "I11 rooms 'Kitchen' and 'Hall' overlap"
    b = "I11 rooms 'Bath' and 'Den' overlap"
    assert _invariant_key(a) != _invariant_key(b)


# ---------------------------------------------------------------------------
# repair_wall_orthogonality -- the interlock, sec2/sec4
# ---------------------------------------------------------------------------

def test_a_moved_wall_lands_exactly_on_axis_not_merely_within_tolerance():
    """0079-report.md sec2(f): the moved coordinate is SET EQUAL to the
    other endpoint's, not bounded by a tolerance. Displacement kept under
    0084-ruling.md sec1's restored `T` so this wall stays a candidate."""
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0.02)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is False
    assert [m[0] for m in res["moved"]] == ["w1"]
    assert _deg_of(res["doc"], "w1") == 0.0


def test_relocations_names_the_one_vertex_that_actually_moved():
    """The scene applier's whole input: which vertex, old point, new
    point -- `walls.close_gap`'s own (level, a, b) shape, so the same
    relocate-and-reweld path can serve both callers."""
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0.02)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = repair_wall_orthogonality(doc)
    assert res["relocations"] == [("L1", (0, 0), (0, 0.02))]


def test_a_refused_wall_is_named_with_its_unchanged_displacement():
    doc = _doc(
        vertices=[_v("v0", -100, 0), _v("v1", 0, 0),
                  _v("v2", 100, 0.02), _v("v3", 200, 0.02)],
        walls=[_w("w0", "v0", "v1"), _w("w1", "v1", "v2"),
               _w("w2", "v2", "v3")],
    )
    res = repair_wall_orthogonality(doc)
    assert res["moved"] == []
    assert [(r[0], r[4]) for r in res["refused"]] == [("w1", "conflict")]
    # NEVER CLAIMS ZERO REMAIN (0066-ruling.md sec4): the refused wall is
    # still off axis in the returned document.
    assert _deg_of(res["doc"], "w1") > 0.0


def test_a_deliberate_diagonal_is_never_a_candidate():
    """0066-ruling.md sec1's own argument for why the 45-degree bay is
    safe: it never enters the near-axis population at all."""
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 100)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = repair_wall_orthogonality(doc)
    assert res["moved"] == [] and res["refused"] == [] and res["over_t"] == []
    assert _deg_of(res["doc"], "w1") == 45.0


# ---------------------------------------------------------------------------
# 0084-ruling.md sec1: T restored as the candidacy filter
# ---------------------------------------------------------------------------

def test_a_near_axis_wall_at_or_above_T_is_reported_not_touched():
    """0084-ruling.md sec1: `0066-ruling.md` sec3's own table (auto-repairable
    under `T`, reported-not-touched at or above it) is restored. This wall's
    displacement (~0.1") is comfortably at or above `REPAIR_T_IN` (1/16") and
    comfortably within the near-axis population (well under 1 degree) -- so
    it must be reported in `over_t`, never moved, never refused."""
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0.1)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = repair_wall_orthogonality(doc)
    assert res["moved"] == [] and res["refused"] == []
    assert [w[0] for w in res["over_t"]] == ["w1"]
    assert res["over_t"][0][3] > REPAIR_T_IN
    assert _deg_of(res["doc"], "w1") > 0.0          # left exactly as it was


# ---------------------------------------------------------------------------
# 0084-ruling.md sec2: the orthogonality post-condition
# ---------------------------------------------------------------------------

def test_a_move_that_would_worsen_another_wall_is_undone_and_refused():
    """`wA`'s only candidate endpoint (`v1`, chosen first -- both free, no
    conflict) is shared with `wB`, an ALREADY off-axis wall (~3 degrees,
    nowhere near `wA`'s own near-axis population, so it never gets a turn
    of its own). Moving `v1` to straighten `wA` measurably tilts `wB`
    further off axis -- `check()` sees no invariant violation, but the
    post-condition catches it: `wA` is refused, `v1` reverts, and `wB`'s
    degree in the returned document is EXACTLY what it was before the
    repair ran, not merely close to it."""
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0.02), _v("v3", 1000, -52.4)],
        walls=[_w("wA", "v1", "v2"), _w("wB", "v1", "v3")],
    )
    orig_b_deg = _deg_of(doc, "wB")
    assert orig_b_deg > 1.0                          # not near-axis; no turn of its own
    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is False
    assert res["moved"] == []
    assert len(res["refused"]) == 1
    wid, _lvl, _typ, _disp, reason = res["refused"][0]
    assert wid == "wA" and reason == "would worsen wB"
    assert _deg_of(res["doc"], "wB") == orig_b_deg
    # wA itself is exactly where it started -- the whole move was undone
    V = {v["id"]: (v["x"], v["y"]) for v in res["doc"]["vertices"]}
    assert V["v1"] == (0, 0)


def test_the_repair_runs_despite_a_pre_existing_violation_0066_refuse_to_start_withdrawn():
    """0082-ruling.md sec2: 0066 sec5's refuse-to-start clause is
    WITHDRAWN. A document that already fails `check()` (here, an opening
    hanging off the end of an unrelated wall) still gets its near-axis
    walls straightened -- refusing protects nothing."""
    doc = _doc(
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0.02),
                  _v("v3", 200, 0), _v("v4", 300, 0)],
        walls=[_w("w1", "v1", "v2"),
               _w("w2", "v3", "v4", openings=[{
                   "id": "o1", "kind": "window", "code": "3040",
                   "anchor": {"from": "v1", "offset_in": 90.0}}])],
    )
    before = check(doc, deep=True)
    assert before and before[0].startswith("I7")     # pre-existing, unrelated
    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is False
    assert [m[0] for m in res["moved"]] == ["w1"]
    assert _deg_of(res["doc"], "w1") == 0.0


def test_a_re_rendered_pre_existing_violation_does_not_trigger_rollback():
    """0082-ruling.md sec4's own hazard, reproduced: `w2` already carries
    an I7 violation. Straightening `w1` moves the vertex `w1` and `w2`
    share, which changes `w2`'s LENGTH (and so the numbers I7's message
    renders) without changing whether the opening is off the wall. `v3`'s
    own y is placed so a `w1` displacement just under 0084-ruling.md sec1's
    restored `T` still crosses a 1-decimal rounding boundary in `w2`'s
    printed length (50.0 -> 50.1) -- the stable key is unchanged, so this
    must NOT read as a new violation."""
    doc = _doc(
        vertices=[_v("vZ", -100, 0), _v("v1", 0, 0),
                  _v("v2", 100, 0.06), _v("v3", 100, 50.08)],
        walls=[
            _w("wZ", "vZ", "v1"),          # exactly horizontal: conflicts v1
            _w("w1", "v1", "v2"),          # near-horizontal: must move v2
            _w("w2", "v2", "v3", openings=[{        # exactly vertical
                "id": "o1", "kind": "window", "code": "3040",
                "anchor": {"from": "v1", "offset_in": 40.0}}]),
        ],
    )
    before = check(doc, deep=True)
    before_keys = {_invariant_key(m) for m in before}
    assert any(k[0] == "I7" for k in before_keys)

    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is False
    assert [m[0] for m in res["moved"]] == ["w1"]

    after = check(res["doc"], deep=True)
    after_keys = {_invariant_key(m) for m in after}
    assert before_keys == after_keys            # same fault, same key
    assert before != after                       # but the RENDERED numbers moved


def test_a_genuinely_new_violation_rolls_back_the_whole_repair():
    """`w2`'s free endpoint is forced onto `w3`'s body -- an I14 unwelded T
    that does not exist before the repair runs. `v2` starts 0.65" from
    `w3`'s line (outside the 0.6" weld tolerance: no pre-existing fault) and
    is moved 0.06" (under 0084-ruling.md sec1's restored `T`) to land at
    0.59" -- inside it. The whole operation must be discarded: `doc` comes
    back unchanged (not a like-valued copy -- the very same document), and
    both `moved`/`refused` are empty."""
    doc = _doc(
        vertices=[_v("v1", 100.59, -1000), _v("v2", 100.65, 0),
                  _v("v3", 100.59, -2000), _v("v4", 100, -50), _v("v5", 100, 50)],
        walls=[
            _w("w1", "v1", "v3"),          # exactly vertical: conflicts v1
            _w("w2", "v1", "v2"),          # near-vertical: must move v2
            _w("w3", "v4", "v5"),          # exactly vertical, spans v2's landing
        ],
    )
    assert check(doc, deep=True) == []
    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is True
    assert res["moved"] == [] and res["refused"] == []
    assert res["doc"] is doc
    assert all(code == "I14" for code, _ids in res["newly_failing"])


# ---------------------------------------------------------------------------
# 0082-ruling.md sec3: the conflict predicate goes stale inside its own
# batch -- a chain receipt, on a real corpus plan, not a synthetic one
# ---------------------------------------------------------------------------

CHAIN_WALLS = ["w53", "w54", "w55", "w56", "w57", "w59"]


@pytest.fixture(scope="module")
def wiscaway_doc():
    return json.loads((ROOT / "fixtures" / "wiscaway2026-08-09R.json")
                       .read_text(encoding="utf-8"))


def test_the_as_loaded_predicate_mistilts_the_chain_RED(wiscaway_doc):
    """THE BUG 0082 sec3 FOUND: decide every endpoint up front, against the
    document AS LOADED, then apply. `w53..w59` is a real six-wall chain
    (`v54..v58`), each pair sharing an endpoint -- straightening an early
    wall manufactures a new exactly-axis neighbour the stale predicate
    never sees, and a LATER wall in the chain ends up worse than it
    started, not on axis."""
    import copy
    doc = copy.deepcopy(wiscaway_doc)
    V = {v["id"]: v for v in doc["vertices"]}
    W = {w["id"]: w for w in doc["walls"]}
    candidates = [row for row in wall_orthogonality(doc) if 0 < row[3] <= 1.0]
    # every endpoint decided ONCE, against the untouched document
    decisions = {wid: choose_repair_endpoint(wiscaway_doc, wid)
                 for wid, *_rest in candidates}
    for wid, *_rest in candidates:
        ep = decisions[wid]
        if ep is None:
            continue
        w = W[wid]
        other_id = w["v2"] if ep == "v1" else w["v1"]
        a, b = V[w["v1"]], V[w["v2"]]
        moving_y = abs(b["y"] - a["y"]) <= abs(b["x"] - a["x"])
        moved_v, other_v = V[w[ep]], V[other_id]
        if moving_y:
            moved_v["y"] = other_v["y"]
        else:
            moved_v["x"] = other_v["x"]
    ends = {wid: round(_deg_of(doc, wid), 6) for wid in CHAIN_WALLS}
    # at least one chain wall the naive pass never refused still ends up
    # off axis -- the naive predicate silently made something worse
    assert any(deg > 0.0 for deg in ends.values()), ends


def test_the_re_evaluated_predicate_leaves_every_non_refused_chain_wall_on_axis_GREEN(
        wiscaway_doc):
    """The production repair, re-evaluating `choose_repair_endpoint` fresh
    before each wall against the document as mutated so far. `0066`
    sec4/`0079-report.md`'s own acceptance (f): every wall the repair did
    NOT refuse -- and was actually a candidate (0084-ruling.md sec1: some
    chain walls are at or above the restored `T` and are never touched at
    all) -- lands at EXACTLY 0."""
    res = repair_wall_orthogonality(wiscaway_doc)
    assert res["rolled_back"] is False
    moved_ids = {m[0] for m in res["moved"]}
    refused_ids = {r[0] for r in res["refused"]}
    over_t_ids = {o[0] for o in res["over_t"]}
    seen = 0
    for wid in CHAIN_WALLS:
        if wid in moved_ids:
            seen += 1
            assert _deg_of(res["doc"], wid) == 0.0, wid
        elif wid in refused_ids or wid in over_t_ids:
            seen += 1
    assert seen == len(CHAIN_WALLS)           # every chain wall accounted for
    assert moved_ids & set(CHAIN_WALLS)       # and at least one really moved


# ---------------------------------------------------------------------------
# corpus receipts -- 0079-report.md sec2(b) / 0082-ruling.md sec1, matched
# to the digit against the ruling's own named walls
# ---------------------------------------------------------------------------

def test_farmplaces_near_axis_walls_are_all_over_t_per_0084():
    """0084-ruling.md sec1's own measured table: this file has 0 near-axis
    walls under the restored `T`, 4 at or above it -- including `w24`,
    0066 sec1's own 3.000-inch headline example, and `w44`
    (0079-report.md sec2(b)'s two conflict-refused walls under the OLD,
    dropped spec). Under the restored `T` neither is even a candidate:
    `w24` is untouchable for the RIGHT reason, size, not conflict."""
    doc = json.loads((ROOT / "examples" / "farmplaceBIGmultifloor.json")
                      .read_text(encoding="utf-8"))
    assert len(check(doc, deep=True)) == 1        # 0082 sec2's own table
    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is False
    assert res["moved"] == [] and res["refused"] == []
    over_t = {w[0]: round(w[3], 4) for w in res["over_t"]}
    assert over_t["w24"] == 3.0
    assert over_t["w44"] == 0.1145
    assert len(over_t) == 4                       # 0084 sec1's own count


@pytest.mark.parametrize("name", [
    "examples/farmplaceBIGmultifloor.json",
    "examples/planc1.v5.json",
    "examples/symmetricP1.json",
    "fixtures/wiscaway2026-08-09R.json",
])
def test_the_post_condition_holds_corpus_wide_no_wall_ends_up_worse(name):
    """0084-ruling.md sec2's own guarantee, checked against real plans, not
    just the synthetic case that found the exemption bug
    (`_worsened_wall`'s own docstring). For every wall in the document,
    its FINAL deviation must be no greater than its ORIGINAL one -- not
    only the walls this repair chose to move or refuse."""
    doc = json.loads((ROOT / name).read_text(encoding="utf-8"))
    orig = {wid: deg for wid, _lvl, _typ, deg, _disp in wall_orthogonality(doc)}
    res = repair_wall_orthogonality(doc)
    assert res["rolled_back"] is False
    after = {wid: deg for wid, _lvl, _typ, deg, _disp in wall_orthogonality(res["doc"])}
    worsened = {wid: (orig[wid], after[wid]) for wid in orig
                if after[wid] > orig[wid] + 1e-6}
    assert worsened == {}


# crossfloor-snap-2026-08-17.json is NOT referenced here on purpose: per
# fixtures/README.md (promoted out of the intake directory under
# 0061-ruling.md sec6's own "either-way naming") it is a MEASUREMENT SUBJECT
# only -- "no test names it, and none is owed" -- its repair-coverage finding
# is measured and reported by docs/evidence/orthogonality_repair_census.py
# instead, the same tier a census script already reads it at
# (`orthogonality_census.py`).


# ---------------------------------------------------------------------------
# the dialog -- Apply actually moves the scene's wall, not just the preview
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_apply_straightens_the_walls_scene_geometry_not_just_the_preview(win):
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(200, 0.02), "interior"))
    dlg = fp.OrthogonalityRepairDialog(win)
    try:
        assert dlg.listw.count() == 1
        assert dlg.b_apply.isEnabled()
        dlg._apply()
        walls = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
        assert len(walls) == 1
        assert walls[0].p1.y() == walls[0].p2.y()          # exactly on axis
        assert "1 wall(s) straightened" in win.statusBar().currentMessage()
    finally:
        dlg.close()


@pytest.mark.gui
def test_the_dialog_disables_apply_when_there_is_nothing_to_repair(win):
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(200, 0), "interior"))
    dlg = fp.OrthogonalityRepairDialog(win)
    try:
        assert not dlg.b_apply.isEnabled()
        assert "nothing to repair" in dlg.info.text()
    finally:
        dlg.close()


@pytest.mark.gui
def test_the_preview_row_names_both_ids_and_the_coordinates_0098_0100(win):
    """0098/0100-ruling.md: PR #37's own preview is the other surface that
    blocked Patrick's check -- a wall it names must be one he can find."""
    w = fp.WallItem(QPointF(0, 0), QPointF(1200, 0.02), "interior")
    win.scene.addItem(w)
    dlg = fp.OrthogonalityRepairDialog(win)
    try:
        text = dlg.listw.item(0).text()
        assert text.startswith(f"default: {w.uid} · w1 (interior) "
                               "at (0.00, 0.00) -> (100.00, 0.00)ft — "
                               "will move ")
    finally:
        dlg.close()
