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
    errs = check(doc, deep=True)
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
