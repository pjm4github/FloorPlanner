"""P0.7: the vendored v5 validator (floorplanner.design.validate) accepts the
clean design corpus and still rejects the intentionally-corrupt fixture.

planc1.v5.json is the "does not launder its input" fixture -- schema-valid but
referentially corrupt on purpose. If check() ever stops failing it, the
validator has been weakened into a rubber stamp.

The corpus also carries REAL PLANS that are not clean, which is a different
thing from a fixture built to be dirty. They are listed in KNOWN_UNCLEAN with
the fault each one carries, and they are excluded from the clean assertion
rather than from the corpus: a plan someone actually drew is the most valuable
input this validator has, and deleting it to keep a test green would throw away
the evidence. See docs/defects/0052-*.md.
"""
import json
from pathlib import Path

import pytest

from floorplanner.design.validate import check, schema_errors

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
CORRUPT = "planc1.v5.json"

# Real plans that carry a KNOWN, RECORDED fault. Not fixtures -- these are
# drawings, kept because a real plan is the most valuable input this validator
# has. Each entry names the record that owns the fault, and the record is what
# closes: when it does, the file comes off this list and the clean assertion
# picks it up automatically.
#
# NOT A PLACE TO PUT AN INCONVENIENT FAILURE. A file joins this list only with
# a defect record explaining what is wrong and why it is not being fixed here;
# `test_known_unclean_still_fails` below asserts each one really is unclean, so
# an entry that gets quietly fixed stops being tolerated and has to be removed.
KNOWN_UNCLEAN = {
    # farmplaceBIGmultifloor.json -- EXEMPT FROM THE CLEAN ASSERTION FOR
    # EXACTLY ONE FAULT: `I11 rooms 'Lounge' and 'Toi' overlap`, and only that
    # string. Every other invariant still binds this file, deep set included;
    # `test_clean_design_validates` is the only assertion it is out of, and
    # `test_known_unclean_still_fails` below asserts it is STILL schema-valid
    # and STILL trips exactly this code.
    #
    # WHAT IS ACTUALLY WRONG (D52): Toi is a WC fully ENCLOSED by Lounge. A
    # single-ring outline cannot express a hole, so the drawing carves the
    # closet out with a zero-width slit -- and I11's centroid is a VERTEX
    # AVERAGE, which for that slit ring lands inside the closet. Measured:
    # _pip(Toi centre, Lounge) False, edge crossings 0, _pip(Lounge "centre",
    # Toi) True. The rooms DO NOT OVERLAP; the true polygon intersection is
    # 0.0 sf. So this exemption tolerates a MISREPORT, not a real fault.
    #
    # WHAT THIS EXEMPTION RESTS ON: a REVIEWER RULING dated 2026-08-08, in
    # D52's Ruling section, and not on the 2026-08-07 "deferred as a feature"
    # note -- which was Code's, unratified, and is STRUCK. Overlapping rooms
    # are an UNMODELLED STATE, not a feature; calling them a feature would let
    # a reader treat the area double-count (D55) as intended.
    #
    # WHY THE FILE IS KEPT RATHER THAN REPAIRED: it is the only plan in the
    # tree that exercises overlapping rooms, and A1 (D47) has demonstrated
    # that overlap is a state the app genuinely reaches. Repairing the drawing
    # would delete the only evidence of a state the model cannot express.
    "farmplaceBIGmultifloor.json": "I11",
    # planc1TestV5.json -- EXEMPT FOR EXACTLY ONE FAULT: `I16 room r20 (WIC)
    # outline visits vertex v5 twice`. Added 2026-08-11 when I16 (D41's simple
    # ring, ruled at R-A) landed.
    #
    # WHY IT IS NOT RE-CUT LIKE symmetricP1. R-A ruled the corpus question in
    # one line: the clean reference gets fixed, THE CORRUPTION FIXTURES KEEP
    # THEIR INSTANCES, because the instances are the point of them. This file
    # is the v5 rendering of planc1 -- the same zero-width WIC spur that
    # planc1.v5.json carries, and planc1.v5.json is the fixture whose whole job
    # is to be referentially dirty while remaining schema-valid.
    #
    # WHAT IT WOULD COST TO "FIX" IT: the same edit made to symmetricP1 -- drop
    # the spur slots, retarget one wall, delete the orphaned wall and vertex.
    # Doing that would leave the tree with NO v5 example of a pinched ring
    # outside the deliberately-corrupt file, which is the state that made D41
    # hard to find in the first place.
    "planc1TestV5.json": "I16",
    # roundedMultifloor.json was on this list and CAME OFF IT on 2026-08-07,
    # when Patrick reshaped the two rooms so they no longer nest -- the list
    # working as intended: an entry leaves the moment its file is clean, and
    # `test_known_unclean_still_fails` below is what forces that.
}


def _design_files():
    out = []
    for p in sorted(EXAMPLES.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("format") == "floorplanner-design":
            out.append(p)
    return out


DESIGN_FILES = _design_files()
CLEAN_FILES = [p for p in DESIGN_FILES
               if p.name != CORRUPT and p.name not in KNOWN_UNCLEAN]
UNCLEAN_FILES = [p for p in DESIGN_FILES if p.name in KNOWN_UNCLEAN]


def test_corpus_discovered():
    # guard: the glob actually found the fixtures, so a rename can't silently
    # empty the corpus and make the parametrized tests vacuously pass.
    # sample_plan.v5.json joined at P2.4, when make_examples.py started writing
    # the v5 rendering alongside the frozen legacy sample_plan.json.
    names = {p.name for p in DESIGN_FILES}
    assert {"symmetricP1.json", "site_demo.json", "sample_plan.v5.json",
            CORRUPT} <= names


@pytest.mark.parametrize("path", CLEAN_FILES, ids=lambda p: p.name)
def test_clean_design_validates(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert schema_errors(doc) == [], f"{path.name} fails the JSON Schema"
    assert check(doc) == [], f"{path.name} fails a referential invariant"


@pytest.mark.parametrize("path", UNCLEAN_FILES, ids=lambda p: p.name)
def test_known_unclean_still_fails(path):
    """Every KNOWN_UNCLEAN file is schema-valid and STILL carries its fault.

    The exemption is only honest while it is still needed. If one of these gets
    repaired, this fails and the file has to come off the list -- so the list
    cannot quietly become a place where failures go to be forgotten.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert schema_errors(doc) == [], f"{path.name} fails the JSON Schema"
    errs = check(doc, deep=True, boundary=True)
    want = KNOWN_UNCLEAN[path.name]
    assert any(e.startswith(want) for e in errs), (
        f"{path.name} no longer fails {want} -- it may have been fixed. "
        f"Remove it from KNOWN_UNCLEAN so the clean assertion covers it again. "
        f"Now reports: {errs}")


def test_corrupt_fixture_passes_schema_but_fails_I6():
    doc = json.loads((EXAMPLES / CORRUPT).read_text(encoding="utf-8"))
    assert schema_errors(doc) == []            # it IS schema-valid
    errs = check(doc)
    assert any(e.startswith("I6") for e in errs), \
        "the corrupt fixture no longer fails I6 -- has check() been laundered?"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# P1.2: the deep=True flag gates the three O(n^2) checks (I5b, I11, I14)
# --------------------------------------------------------------------------
def _codes(errs):
    return {e.split()[0] for e in errs}


def test_deep_flag_gates_the_quadratic_checks():
    d = _load(CORRUPT)                          # trips I11 (a deep check) + I6
    codes = _codes
    deep, cheap = check(d, deep=True), check(d, deep=False)
    assert "I11" in codes(deep) and "I11" not in codes(cheap)   # gated out
    assert "I6" in codes(cheap)                 # always-on, still caught
    assert len(cheap) < len(deep)


def test_negative_I14_fires_on_a_drifted_shared_vertex():
    # a welded corner (one vertex shared by two walls) splits into two vertices
    # 0.3" apart -- a broken weld. I14 (deep) must catch it; deep=False must not.
    d = _load("symmetricP1.json")
    use = {}
    for w in d["walls"]:
        for k in ("v1", "v2"):
            use[w[k]] = use.get(w[k], 0) + 1
    shared = next(vid for vid, c in use.items() if c >= 2)
    base = next(v for v in d["vertices"] if v["id"] == shared)
    d["vertices"].append({**base, "id": "vDRIFT", "x": base["x"] + 0.3})
    w = next(w for w in d["walls"] if shared in (w["v1"], w["v2"]))
    w["v1" if w["v1"] == shared else "v2"] = "vDRIFT"
    assert any(e.startswith("I14") for e in check(d, deep=True)), "I14 must fire"
    assert not any(e.startswith("I14") for e in check(d, deep=False)), \
        "I14 is a deep check -- it must not run under deep=False"


def test_negative_I15_fires_when_an_outline_edge_crosses_a_wall_endpoint():
    """I15 OUTLINE COMPLETENESS, constructed rather than borrowed.

    A room's outline edge is stretched to run PAST an existing wall endpoint
    without naming it -- the state the record calls "a room edge crossing an
    unnamed T". Built by DELETING an outline slot whose vertex a wall still
    ends at, which is exactly what the fault looks like on disk: the wall is
    untouched, only the outline stops mentioning the corner.

    IT IS A BOUNDARY CHECK: it fires under `deep=False` when `boundary=True`
    and is silent otherwise, which is the opposite of I14 above and is asserted
    here so the two cannot be confused.
    """
    d = _load("symmetricP1.json")
    assert not [e for e in check(d, deep=True, boundary=True)
                if e.startswith("I15")]                        # precondition

    # find an outline slot whose vertex is a wall endpoint AND whose neighbours
    # stay collinear through it once it is dropped -- otherwise the edge does
    # not pass through the point and there is nothing to detect
    V = {v["id"]: v for v in d["vertices"]}
    ends = {w[k] for w in d["walls"] for k in ("v1", "v2")}
    target = None
    for r in d["rooms"]:
        ring = r["outline"]
        n = len(ring)
        for i in range(n):
            vid = ring[i]["v"]
            if vid not in ends:
                continue
            a = V[ring[(i - 1) % n]["v"]]
            b = V[ring[(i + 1) % n]["v"]]
            p = V[vid]
            cross = ((b["x"] - a["x"]) * (p["y"] - a["y"])
                     - (b["y"] - a["y"]) * (p["x"] - a["x"]))
            dot = ((p["x"] - a["x"]) * (b["x"] - a["x"])
                   + (p["y"] - a["y"]) * (b["y"] - a["y"]))
            ll = (b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2
            if abs(cross) < 1e-9 and 0 < dot < ll:
                target = (r, i, vid)
                break
        if target:
            break
    assert target, "no collinear outline corner at a wall end -- test is vacuous"
    room, idx, vid = target
    del room["outline"][idx]

    errs = check(d, deep=False, boundary=True)
    assert any(e.startswith("I15") and vid in e for e in errs), (
        f"I15 must fire on the dropped corner {vid} -- got {errs[:4]}")
    # and it is a BOUNDARY check: silent unless asked, because a mid-drag scene
    # legitimately has an outline edge running through a wall end it does not
    # name -- measured, that is what turned the gate red when I15 first landed
    # in the always-on lane (test_acceptance_shuffle_drag_across_the_plan)
    assert not [e for e in check(d, deep=True) if e.startswith("I15")],         "I15 must not run per-mutation -- a mid-drag transient is not a fault"


def test_i15_stays_in_the_cheap_lane(fp):
    """I15's place in the cheap twelve is a fact about ONE IMPLEMENTATION.

    Measured at `handoff/0006-readback-outline-invariants.md`: naive, every
    outline edge against every wall endpoint costs 36 ms on the largest corpus
    plan against the whole deep set's 49 -- honestly DEEP. Behind the grid index
    it is 0.917 ms against the cheap lane's 0.447 -- honestly CHEAP. A refactor
    to something clearer and slower would move a 40x cost into the per-mutation
    path with nothing objecting.

    SO THE WORK IS BOUNDED, AND COUNTED RATHER THAN TIMED. A wall-clock
    assertion flaps on a busy CI runner and would be disabled inside a month; a
    comparison count is deterministic and fails on exactly the change that
    matters.

    THE BOUND IS STATED AGAINST THE NAIVE COST, not against the measured one, so
    it has room for an honest implementation change and none for an accidental
    quadratic: `symmetricP1` has 80 walls and 20 rooms, so edges x endpoints is
    ~140 x 120 = 16,800 comparisons. Measured with the index: 10.
    """
    from floorplanner.design.validate import (check, i15_probes,
                                              reset_i15_probes)
    d = _load("symmetricP1.json")
    edges = sum(len(r["outline"]) for r in d["rooms"])
    endpoints = len({w[k] for w in d["walls"] for k in ("v1", "v2")})
    naive = edges * endpoints

    reset_i15_probes()
    check(d, deep=False, boundary=True)
    used = i15_probes()

    assert used > 0, "I15 did no work at all -- the counter is not wired"
    assert used < naive / 20, (
        f"I15 performed {used} point-on-segment comparisons; the naive bound is "
        f"{naive} and this check belongs in the cheap lane only while it stays "
        f"far below that. If the index was removed or defeated, I15 is now a "
        f"DEEP check and must be moved, not re-baselined.")


def test_negative_I6_fires_on_a_mislabelled_wall_side():
    # point a wall's `left` at a room whose outline does not name that wall
    d = _load("symmetricP1.json")
    w = d["walls"][0]
    users = {r["id"] for r in d["rooms"]
             for e in r["outline"] if e.get("wall") == w["id"]}
    wrong = next(r["id"] for r in d["rooms"] if r["id"] not in users)
    w["left"] = wrong
    assert any(e.startswith("I6") for e in check(d, deep=False)), \
        "I6 must fire on a wall side that disagrees with the room outlines"


def test_negative_I16_fires_on_a_pinched_ring():
    """I16 SIMPLE RING (D41, ruled at R-A as a NEW invariant, not a widening).

    I5b tests PROPER CROSSING and `_seg_cross` must not fire on the collinear
    edges two rooms legitimately share, so widening it would blur something
    that works. A ring visiting a vertex twice is a DEGENERACY -- the pinched
    loop, and the zero-width spur that goes out to a corner and straight back.

    Constructed on the RE-CUT symmetricP1, which is now clean of it: the spur
    R-A ordered removed is put back, and I16 must see it. That makes this test
    the guard on the re-cut as well -- if someone restores the old outline, it
    fails.

    IT IS A BOUNDARY CHECK, alongside I15, AND THAT WAS MEASURED. Landed
    always-on it turned the gate red on EIGHT tests, every one of them asserting
    that a CONVERTED LEGACY plan is clean -- `planc1.json` carries this very WIC
    spur in its v4 geometry and the importer reproduces it faithfully. The
    importer is not inventing a fault, it is carrying one, and a document that
    ARRIVES degenerate belongs in a boundary report rather than in a red
    conversion test. Different reason from I15's mid-drag transient, same
    conclusion.
    """
    d = _load("symmetricP1.json")
    assert not [e for e in check(d, deep=True, boundary=True)
                if e.startswith("I16")], \
        "precondition: symmetricP1 was re-cut and is clean of I16"

    room = next(r for r in d["rooms"] if r["name"] == "WIC")
    ring = [e["v"] for e in room["outline"]]
    # THE SHAPE IS PINNED, NOT THE IDS. The writer re-mints ids densely, so a
    # literal ring would pin the numbering rather than the re-cut -- and would
    # fail the next time an unrelated corner is added anywhere before it.
    assert len(ring) == 5 and len(set(ring)) == 5, (
        f"the re-cut left WIC a five-corner SIMPLE ring; this pins that shape "
        f"and is the guard on the re-cut itself: {ring}")

    # put the excursion back: out to a corner the ring already visits and
    # straight back -- the zero-width spur R-A ordered removed
    room["outline"].insert(1, {"v": ring[-1], "wall": None})
    errs = check(d, deep=False, boundary=True)
    assert any(e.startswith("I16") and room["id"] in e for e in errs), (
        f"I16 must fire on a ring that visits a vertex twice -- got {errs[:4]}")


# --------------------------------------------------------------------------
# 0139-ruling.md R1: the additive `roofs` block, version 5/6
# --------------------------------------------------------------------------

def _roof_doc(version=6, roofs=None):
    d = _load("sample_plan.v5.json")
    d["version"] = version
    if roofs is None:
        d.pop("roofs", None)
    else:
        d["roofs"] = roofs
    return d


_ONE_ROOF = [{
    "id": "rf1", "level": "L1",
    "ridge": [[0.0, 0.0], [240.0, 0.0]],
    "eaves_h_in": 96.0, "ridge_h_in": 132.0,
    "overhang_in": 12.0, "gable": [True, True],
}]


def test_a_version_5_document_with_no_roofs_key_is_still_valid():
    """The migration this schema change owes: nothing about an EXISTING
    document needs to change to keep validating. Every real corpus file
    already proves this via `test_clean_design_validates`; this pins the
    specific claim so it survives a future schema edit that narrows the
    version enum back down without anyone noticing."""
    doc = _roof_doc(version=5, roofs=None)
    assert schema_errors(doc) == []


def test_a_version_6_document_with_a_well_formed_roof_validates():
    doc = _roof_doc(version=6, roofs=_ONE_ROOF)
    assert schema_errors(doc) == []


def test_version_5_document_may_also_carry_roofs():
    """`roofs` is gated by nothing but its own presence -- the schema does
    not couple it to the version number. 0139-ruling.md's own intent
    ("`design_document()` writes 6 ... a loaded 5 is left as 5 unless
    re-saved") describes a WRITER convention, not a schema constraint;
    the READER (this validator) must accept either combination so an
    old-numbered file someone hand-edited, or a future migrator that adds
    roofs without touching the version key, is not rejected."""
    doc = _roof_doc(version=5, roofs=_ONE_ROOF)
    assert schema_errors(doc) == []


def test_version_7_is_rejected():
    doc = _roof_doc(version=7, roofs=None)
    assert schema_errors(doc) != []


@pytest.mark.parametrize("bad_roof", [
    {"id": "rf1", "level": "L1", "ridge": [[0, 0], [1, 1]],
     "eaves_h_in": 96, "ridge_h_in": 132},   # missing nothing -- baseline shape
])
def test_a_minimal_roof_with_only_the_required_fields_validates(bad_roof):
    doc = _roof_doc(version=6, roofs=[bad_roof])
    assert schema_errors(doc) == [], (
        "overhang_in/gable have schema defaults and must be OPTIONAL")


def test_a_roof_missing_a_required_field_is_rejected():
    incomplete = {"id": "rf1", "level": "L1",
                  "ridge": [[0, 0], [240, 0]], "eaves_h_in": 96}
    # ridge_h_in omitted
    doc = _roof_doc(version=6, roofs=[incomplete])
    assert schema_errors(doc) != []


def test_a_roof_with_an_unknown_property_is_rejected():
    """additionalProperties: false, matching every other object in this
    schema -- a typo'd key must not silently vanish."""
    roof = dict(_ONE_ROOF[0])
    roof["pitch_deg"] = 30.0   # pitch is DERIVED, never stored (0139 sec2)
    doc = _roof_doc(version=6, roofs=[roof])
    assert schema_errors(doc) != []


def test_a_roof_with_a_three_point_ridge_is_rejected():
    roof = dict(_ONE_ROOF[0])
    roof["ridge"] = [[0, 0], [120, 0], [240, 0]]
    doc = _roof_doc(version=6, roofs=[roof])
    assert schema_errors(doc) != []
