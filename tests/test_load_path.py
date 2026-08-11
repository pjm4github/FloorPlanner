"""P2.1 -- the load path: v1-v4 converts, v5 loads clean.

The first user-visible phase. Opening a legacy plan now WELDS the user's
geometry, which the application has never done before (see the corrected F5 in
docs/CODE_REVIEW_v2.md), so the report, the dirty flag and the never-touch-the-
original guarantee are load-bearing rather than courtesies.
"""
import json
import math
from pathlib import Path

import pytest

from floorplanner.design.importer import conversion_report, import_legacy
from floorplanner.design.validate import check

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _areas(fp, win):
    return {r.name: r.area_sqft for r in win.scene.items()
            if isinstance(r, fp.RoomItem)}


def _open(win, name, interactive=False):
    """Open a corpus file through the real entry point, so the dirty flag and
    the undo baseline are exercised, not just the importer."""
    p = EXAMPLES / name
    win.load_path(str(p))
    return p


# ------------------------------------------------------- legacy -> v5 (accept)
def test_planc1_converts_to_the_repaired_geometry(fp, win):
    """THE acceptance: M Bath 182.0 sf, Hall 61.5 sf, 4 ends moved, dirty."""
    _open(win, "planc1.json")
    areas = _areas(fp, win)
    assert areas["M Bath"] == pytest.approx(182.0, abs=0.1)
    assert areas["Hall"] == pytest.approx(61.5, abs=0.1)
    assert win._conversion["ends_moved"] == 4
    assert win._provenance["endpoints_welded"] == 4
    assert win._is_dirty(), "a converted plan must not read as saved"


def test_conversion_reports_ends_moved_not_weld_ops(fp, win):
    """The user sees 4, not 31. `weld_ops` is a cross-check, and reporting it
    as damage overstated the geometry actually changed by ~6x."""
    _open(win, "planc1.json")
    rep = win._conversion
    assert (rep["weld_ops"], rep["ends_moved"]) == (31, 4)
    text = conversion_report(rep, 3)
    assert "4 wall ends moved" in text
    assert "31 junctions checked" in text
    assert "31 wall ends" not in text


def test_the_legacy_file_on_disk_is_never_modified(fp, win):
    """The user can decline the conversion by closing without saving."""
    before = (EXAMPLES / "planc1.json").read_bytes()
    _open(win, "planc1.json")
    assert (EXAMPLES / "planc1.json").read_bytes() == before


def test_converted_document_is_valid(fp, win):
    """The repaired document passes every invariant, including the deep three
    -- I11 and I14 are the two that caught planc1's corruption in the first
    place."""
    design, _rep = import_legacy(_load("planc1.json"))
    assert check(design.to_dict(), deep=True) == []


def test_import_does_not_mutate_its_input(fp):
    src = _load("planc1.json")
    import_legacy(src)
    assert src == _load("planc1.json")


def test_area_basis_stays_centerline(fp):
    """A conversion must not restate every area in the same breath as moving
    four wall ends. inside_face is the better number and becomes an opt-in at
    Phase 5, with its own visible moment."""
    design, _ = import_legacy(_load("planc1.json"))
    assert design.to_dict()["settings"]["area_basis"] == "centerline"


# ------------------------------------------------------------- v5 loads clean
def test_v5_opens_clean_and_not_dirty(fp, win):
    """Opening a v5 file must not dirty it. If this fails, suspect P1.1
    round-trip fidelity (Design.from_dict(x).to_dict() == x), not this path."""
    _open(win, "symmetricP1.json")
    assert win._conversion is None, "a v5 file must not be converted"
    assert not win._is_dirty(), "a v5 file opened dirty"


def test_v5_round_trip_fidelity_is_the_dependency(fp):
    """The guarantee above rests on the model, so pin it where it lives."""
    from floorplanner.design.model import Design
    for name in ("symmetricP1.json", "planc1.v5.json"):
        doc = _load(name)
        assert Design.from_dict(doc).to_dict() == doc


def test_malformed_v5_is_reported_not_rewelded(fp, win):
    """A v5 file failing I14 is a bug in whatever wrote it. Report it; do NOT
    silently re-weld -- that asymmetry is the whole point of promoting 'welded'
    to a checked invariant."""
    # SPLIT a welded corner into two vertices 0.3" apart. Simply nudging the
    # shared vertex would not do it -- in v5 the corner IS one vertex, so
    # moving it moves both walls together and stays perfectly welded.
    doc = _load("symmetricP1.json")
    use = {}
    for w in doc["walls"]:
        for k in ("v1", "v2"):
            use[w[k]] = use.get(w[k], 0) + 1
    shared = next(vid for vid, c in use.items() if c >= 2)
    base = next(v for v in doc["vertices"] if v["id"] == shared)
    drift = base["x"] + 0.3
    doc["vertices"].append({**base, "id": "vDRIFT", "x": drift})
    w = next(w for w in doc["walls"] if shared in (w["v1"], w["v2"]))
    w["v1" if w["v1"] == shared else "v2"] = "vDRIFT"
    assert any(e.startswith("I14") for e in check(doc, deep=True))

    win.open_document(doc, interactive=False)
    assert "malformed" in win.statusBar().currentMessage().lower()
    # and the geometry is exactly as the file had it -- nothing welded back
    ends = [p for x in win.scene.items() if isinstance(x, fp.WallItem)
            for p in (x.p1, x.p2)]
    assert any(math.isclose(p.x(), drift, abs_tol=1e-6) for p in ends), \
        "the malformed file was silently re-welded"


# --------------------------------------------------- undo must not migrate
def test_undo_restore_does_not_convert(fp, win, make_room):
    """`load_data` is the undo-restore path as well as a plain apply, so it
    must never migrate: welding on every undo would be a repair, not a restore.

    Pinned with geometry a weld WOULD move -- a divider stopping 1.5" short."""
    sc = win.scene
    sc.addItem(fp.WallItem(fp.QPointF(0, 0), fp.QPointF(240, 0), "interior"))
    sc.addItem(fp.WallItem(fp.QPointF(120, 1.5), fp.QPointF(120, 200),
                           "interior"))
    fp.rebuild_all_walls(sc)
    snapshot = json.loads(json.dumps(win.serialize()))

    win.load_data(snapshot)                  # the undo path
    ys = sorted({round(w.p1.y(), 3) for w in sc.items()
                 if isinstance(w, fp.WallItem)}
                | {round(w.p2.y(), 3) for w in sc.items()
                   if isinstance(w, fp.WallItem)})
    assert 1.5 in ys, "the undo path welded the gap shut -- that is a repair"


# ------------------------------------------------ the concept-room fallback
def _two_rooms_one_face():
    """A minimal legacy plan whose DIVIDER IS MISSING: one 20'x8' enclosure,
    two room labels inside it, and a chair in each half.

    v4 never serialised open/archway edges, so a real file can name two rooms
    that share one enclosure. Both anchors resolve to the SAME traced face, and
    without the concept-room fallback the loser is silently dropped. planc1 no
    longer exercises this -- the weld pass closes its 1.5" gap, giving M Bath
    and Hall a face each -- so it needs its own fixture."""
    W, H = 240.0, 96.0
    walls = [{"type": "exterior", "p1": [0, 0], "p2": [W, 0], "openings": []},
             {"type": "exterior", "p1": [W, 0], "p2": [W, H], "openings": []},
             {"type": "exterior", "p1": [W, H], "p2": [0, H], "openings": []},
             {"type": "exterior", "p1": [0, H], "p2": [0, 0], "openings": []}]
    corners = [[0, 0], [W, 0], [W, H], [0, H]]
    return {
        "format": "floorplanner-json", "version": 3, "units": "inches",
        "settings": {}, "floors": [{"name": "default", "reference": False}],
        "walls": walls,
        "rooms": [
            {"name": "Kitchen", "anchor": [60, 48], "label_offset": [0, 0],
             "properties": {"perimeter_corners": corners}, "floor": "default"},
            {"name": "Dining", "anchor": [180, 48], "label_offset": [0, 0],
             "properties": {"perimeter_corners": corners}, "floor": "default"},
        ],
        "furnishings": [
            {"kind": "chair", "pos": [60, 48], "rotation": 0.0,
             "floor": "default"},
            {"kind": "chair", "pos": [180, 48], "rotation": 0.0,
             "floor": "default"},
        ],
    }


def test_two_rooms_one_face_keeps_both(fp):
    """The contest loser survives as a FLOATING CONCEPT room rather than being
    dropped. This is the only mechanism between that file shape and silent
    room loss."""
    design, rep = import_legacy(_two_rooms_one_face())
    doc = design.to_dict()

    assert {r["name"] for r in doc["rooms"]} == {"Kitchen", "Dining"}
    concept = [r for r in doc["rooms"] if r["category"] == "concept"]
    placed = [r for r in doc["rooms"] if r["category"] != "concept"]
    assert len(concept) == 1 and len(placed) == 1, "exactly one lost the face"

    c = concept[0]
    assert c["placement"]["state"] == "floating"
    assert c["placement"]["extracted_from"] == c["level"]
    assert c["nominal_size"]["width_in"] > 0
    assert all(e["wall"] is None for e in c["outline"]), "concept walls nothing"

    # sized from, and owning, the furnishing it carried
    carried = [f for f in doc["furnishings"] if f["room"] == c["id"]]
    assert len(carried) == 1
    assert rep["concept_rooms"][0]["furnishings_carried"] == 1
    x0 = min(v["x"] for v in doc["vertices"] if v["id"] in
             {e["v"] for e in c["outline"]})
    x1 = max(v["x"] for v in doc["vertices"] if v["id"] in
             {e["v"] for e in c["outline"]})
    assert x0 <= carried[0]["pos"][0] <= x1, "not sized around what it owns"

    assert check(doc, deep=True) == [], "the fallback must produce a VALID doc"


def test_concept_room_is_named_in_the_report(fp):
    """The user is told a room is now floating -- silently relocating one would
    be worse than dropping it loudly."""
    _design, rep = import_legacy(_two_rooms_one_face())
    text = conversion_report(rep, 3)
    assert "floating" in text
    assert rep["concept_rooms"][0]["room"] in text


# ------------------------------------------------------ defect 19, in-app arm
def test_extracted_walls_are_welded(fp, win, tmp_path):
    """Defect 19's in-app arm. `extract_from_reference` injects walls straight
    into the live scene, so P2.1's weld-on-open never sees them -- it needs its
    own weld pass or every extracted plan is born with open junctions."""
    from floorplanner.design.bridge import design_from_scene
    from tests.test_extract import _make_plan_png
    from PyQt6.QtCore import QPointF

    item = win.start_image_import(str(_make_plan_png(tmp_path / "plan.png")))
    ipp = item.inches_per_pixel()
    item.calibrate(item.mapToScene(QPointF(40 * ipp, 200 * ipp)),
                   item.mapToScene(QPointF(560 * ipp, 200 * ipp)), 360.0)
    assert win.extract_from_reference(item, interactive=False)

    rep = {}
    design_from_scene(win, report=rep)
    assert rep["unwelded_ends"] == 0, "extracted walls were left unwelded"


# ============================================================ P2.2: save v5
def _saved(win, tmp_path, name="out.json"):
    p = tmp_path / name
    win.save_path(str(p))
    return p, json.loads(p.read_text(encoding="utf-8"))


def test_save_writes_v5(fp, win, tmp_path, make_room):
    make_room(win.scene, 0, 0, 240, 120, name="Hall")
    _p, doc = _saved(win, tmp_path)
    assert doc["format"] == "floorplanner-design" and doc["version"] == 5
    assert check(doc, deep=True) == []


def test_save_reopen_is_clean_and_not_dirty(fp, win, tmp_path, make_room):
    """THE acceptance. Rests on P1.5's round-trip guarantees, since the save
    path IS design_from_scene."""
    make_room(win.scene, 0, 0, 240, 120, name="Hall")
    make_room(win.scene, 360, 0, 180, 120, name="Study")
    p, doc = _saved(win, tmp_path)
    assert check(doc, deep=True) == []

    win.load_path(str(p))
    assert win._conversion is None, "a v5 file must not be converted on open"
    assert not win._is_dirty(), "reopening our own save came up dirty"

    _p2, again = _saved(win, tmp_path, "out2.json")
    assert again == doc, "save -> reopen -> save is not a fixed point"


def test_converted_plan_saves_and_reopens_clean(fp, win, tmp_path):
    """The full user journey: open a corrupt legacy plan, accept the
    conversion with a Save, reopen -- clean, and no longer dirty."""
    win.load_path(str(EXAMPLES / "planc1.json"))
    assert win._is_dirty()
    p, doc = _saved(win, tmp_path)
    assert check(doc, deep=True) == []

    win.load_path(str(p))
    assert not win._is_dirty()
    areas = _areas(fp, win)
    assert areas["M Bath"] == pytest.approx(182.0, abs=0.1)
    assert areas["Hall"] == pytest.approx(61.5, abs=0.1)


def test_provenance_survives_every_save(fp, win, tmp_path):
    """The audit trail's whole value is surviving the FIRST save -- the one the
    conversion report explicitly asks the user to make -- and every one after."""
    win.load_path(str(EXAMPLES / "planc1.json"))
    p, doc = _saved(win, tmp_path)
    assert doc["provenance"]["endpoints_welded"] == 4
    assert doc["provenance"]["migrated_from"]["format"] == "floorplanner-json"

    win.load_path(str(p))                       # reopen the v5 file...
    _p2, again = _saved(win, tmp_path, "again.json")
    assert again["provenance"] == doc["provenance"], "audit trail lost on re-save"


def test_unmodelled_fields_survive_a_round_trip(fp, win, tmp_path):
    """The scene cannot model everything the schema allows. Anything it has no
    home for is stashed on the item and re-emitted, or a save silently drops it
    -- measured on symmetricP1's Garage, which carries
    area_accounting: 'unconditioned'."""
    win.load_path(str(EXAMPLES / "symmetricP1.json"))
    _p, doc = _saved(win, tmp_path)
    garage = next(r for r in doc["rooms"] if r["name"] == "Garage")
    assert garage["area_accounting"] == "unconditioned"
    assert doc["settings"]["name"] == "Symmetric P1"


def test_opening_a_v5_file_reproduces_it_exactly(fp, win, tmp_path):
    """Canonical form is TOTAL: same ids AND same outline rotation, so a file
    the project wrote is reproduced byte-for-byte by opening and saving it.
    Without this a plan churns on every save cycle."""
    orig = _load("symmetricP1.json")
    win.load_path(str(EXAMPLES / "symmetricP1.json"))
    _p, doc = _saved(win, tmp_path)
    for key in ("levels", "vertices", "walls", "rooms", "furnishings"):
        assert doc[key] == orig[key], f"{key} churned on open->save"


def test_outline_rotation_is_canonical(fp):
    """Each outline starts at its lexicographically-least corner, orientation
    untouched. A cycle has no natural first element, so without this two
    producers emit the same loop from different corners -- identical polygon,
    unequal document."""
    from floorplanner.design.canonical import canonicalize
    doc = _load("symmetricP1.json")
    pos = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    for r in doc["rooms"]:
        loop = [pos[e["v"]] for e in r["outline"]]
        assert loop[0] == min(loop), f"{r['name']} does not start at its least"
    assert canonicalize(json.loads(json.dumps(doc))) == doc, "not a fixed point"


def test_canonical_form_is_rotation_insensitive(fp):
    """Rotating an outline in the input must not change canonical output --
    the guard that makes save-reopen a fixed point."""
    from floorplanner.design.canonical import canonicalize
    doc = _load("symmetricP1.json")
    spun = json.loads(json.dumps(doc))
    for r in spun["rooms"]:
        r["outline"] = r["outline"][1:] + r["outline"][:1]
    assert canonicalize(spun) == doc


# ------------------------------------------------------------ legacy export
def test_legacy_export_round_trips_through_the_old_loader(fp, win, tmp_path,
                                                          make_room):
    """File > Export legacy v4 keeps anyone from being stranded by the cutover:
    the export must load through the v4 path and come back the same plan."""
    make_room(win.scene, 0, 0, 240, 120, name="Hall")
    before = {r.name: round(r.area_sqft, 2) for r in win.scene.items()
              if isinstance(r, fp.RoomItem)}
    p = tmp_path / "legacy.json"
    win.export_legacy_v4_path(str(p))

    doc = json.loads(p.read_text(encoding="utf-8"))
    assert doc["format"] == "floorplanner-json" and doc["version"] == 4

    win2 = fp.MainWindow()
    try:
        win2.load_data(doc)                      # the OLD loader, no migration
        after = {r.name: round(r.area_sqft, 2) for r in win2.scene.items()
                 if isinstance(r, fp.RoomItem)}
        assert after == before
    finally:
        win2.close()


# ================================ Gate 2: the app's own output needs no repair
def test_legacy_export_reopens_without_repair(fp, win, tmp_path):
    """GATE 2 FINDING (2026-07-27). Open planc1 -> save v5 -> export legacy v4
    -> reopen the export through the CONVERTING path. The reopen must report
    ZERO ends moved: the application's own output must never need repair.

    It reported 5. Cause: the importer welded the divider ends from y=655.529
    to y=654.0, but `split_params` then cut those same walls at the STORED,
    PRE-WELD room corners -- still recording 655.529 -- injecting a degree-2
    vertex 1.53" from the freshly welded end and leaving a 1.53" SLIVER wall,
    the exact ghost of the gap the weld had just closed. Nothing caught it:
    1.53 clears MIN_SPAN and clears vertex_weld_in, so I14 stayed silent and
    every area was right.

    P2.2 round-tripped only via `load_data` -- the faithful apply, which never
    welds -- so the export path was never taken through the converter. That is
    why this escaped, and why the test drives the FULL journey."""
    win.load_path(str(EXAMPLES / "planc1.json"))
    before = _areas(fp, win)
    win.save_path(str(tmp_path / "converted.v5.json"))

    v4 = tmp_path / "export.v4.json"
    win.export_legacy_v4_path(str(v4))
    assert json.loads(v4.read_text(encoding="utf-8"))["format"] == "floorplanner-json"

    win.load_path(str(v4))                      # the CONVERTING path
    assert win._conversion["ends_moved"] == 0, \
        "the app's own export needed repair on reopen"
    assert win._conversion["weld_ops"] == 0, "...and the weld found work to do"
    after = _areas(fp, win)
    assert set(after) == set(before)
    for name, sf in before.items():
        assert after[name] == pytest.approx(sf, abs=0.1), f"{name} changed"


def test_stored_corners_are_welded_with_the_walls(fp):
    """The fix, at its own level. Stored `perimeter_corners` are PRE-WELD data;
    leaving them stale is what produced the slivers above."""
    from floorplanner.design.importer import weld_room_corners
    walls = [{"p1": [0.0, 0.0], "p2": [100.0, 0.0]}]
    rooms = [{"properties": {"perimeter_corners": [
        [0.0, 1.53],          # 1.53" from a welded end -> snaps
        [50.0, 40.0],         # nowhere near an end -> left alone
    ]}}]
    assert weld_room_corners(walls, rooms) == 1
    pc = rooms[0]["properties"]["perimeter_corners"]
    assert pc[0] == [0.0, 0.0]
    assert pc[1] == [50.0, 40.0]


def test_no_sliver_walls_in_the_converted_document(fp):
    """No wall shorter than the gesture tolerance survives the conversion --
    a sub-2" wall on a converted plan is a weld artefact, not architecture."""
    import math
    design, _rep = import_legacy(_load("planc1.json"))
    doc = design.to_dict()
    v = {x["id"]: (x["x"], x["y"]) for x in doc["vertices"]}
    slivers = [(w["id"], round(math.dist(v[w["v1"]], v[w["v2"]]), 3))
               for w in doc["walls"]
               if math.dist(v[w["v1"]], v[w["v2"]]) < 2.0]
    assert slivers == [], f"weld-ghost slivers survived: {slivers}"


# --------------------------------------------------------------------------
# I15 at the two DOCUMENT BOUNDARIES (load reports, save asks)
# --------------------------------------------------------------------------
def test_i15_save_asks_and_still_writes(fp, win, tmp_path):
    """SAVE ASKS, IT DOES NOT REFUSE -- D49's amended shape, applied to I15.

    The producer is measured rather than constructed: `normalize_walls` writes
    I15 violations on `roundedMultifloor` (attributed to `weld_scene`), which is
    why a load-only check would miss exactly the files this application makes.

    THE ASSERTION IS BOTH HALVES. The findings must be recorded -- otherwise the
    check is not running -- AND the file must exist afterwards, because a
    refusal here would trap the user with unsaveable work. A test that only
    checked the report would pass on a refusal, which is the outcome the ruling
    forbids.
    """
    from floorplanner.walls import normalize_walls

    win.load_path(str(EXAMPLES / "roundedMultifloor.json"))
    assert not getattr(win, "_boundary_findings", []), \
        "precondition: this plan is clean of I15 as it arrives"

    normalize_walls(win.scene)
    out = tmp_path / "asked.json"
    win.save_path(str(out))                      # non-interactive: never blocks

    found = win._boundary_findings
    assert found and all(e.startswith("I15") for e in found), \
        f"normalize_walls must produce I15 findings here -- got {found}"
    assert out.exists(), "SAVE MUST NOT REFUSE -- the file has to be written"
    assert json.loads(out.read_text(encoding="utf-8"))["rooms"], \
        "the written file must be a real plan, not a stub"


def test_i15_load_reports_and_opens_the_file_unchanged(fp, win):
    """CHECK YES, FIX NO. The dirty fixture opens, is reported, and is not
    repaired on the way in -- `fixtures/wiscaway2026-08-09R.json` is retained
    BECAUSE it fails, so silently welding it would destroy the evidence."""
    from floorplanner.design.validate import check as _check

    path = Path(__file__).resolve().parent.parent / "fixtures" \
        / "wiscaway2026-08-09R.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    before = [e for e in _check(raw, deep=True, boundary=True)
              if e.startswith("I15")]
    assert before, "precondition: the fixture carries I15 violations"

    win.load_path(str(path))
    assert win.statusBar().currentMessage(), "the load said nothing at all"
    # not repaired: the bytes on disk are untouched
    assert json.loads(path.read_text(encoding="utf-8")) == raw


# --------------------------------------------------------------------------
# P6.a — the per-mutation invariant hook, off the snapshot path
# --------------------------------------------------------------------------
def test_shadow_mode_still_fires_without_the_snapshot_undo_path(fp, win,
                                                                monkeypatch):
    """P6.a's RULED RECEIPT: with the snapshot hook removed from that path,
    shadow mode still fires, proven by a deliberately corrupt mutation.

    WHY THIS TEST EXISTS AT ALL. Read-back 0008 measured that
    `_commit_if_changed` is not an undo function -- it is the application's only
    per-mutation invariant trigger, and Phase 6 retires the undo path it lives
    in. Retiring it naively would have taken `FP_VERIFY_DESIGN` down SILENTLY.
    So the hook now has its own name, `verify_settled`, and this asserts it is
    reachable WITHOUT the snapshot/undo machinery being involved.

    THE MUTATION IS DELIBERATELY CORRUPT, and the precondition is asserted
    first: an assertion that "the checker fired" is worthless if the scene was
    legal, and this is a negative-assertion's mirror -- it must establish that
    there was something to catch.
    """
    from PyQt6.QtCore import QPointF

    from floorplanner.design.verify import rebase

    sc = win.scene
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(120, 0), QPointF(120, 96), "interior")
    sc.addItem(a)
    sc.addItem(b)
    fp.rebuild_all_walls(sc)
    rebase(win)

    seen = []
    monkeypatch.setattr(win, "_verify_or_report",
                        lambda where, **kw: seen.append((where, kw)) or True)

    # the hook, called with NO snapshot and NO undo state -- the whole point
    win.verify_settled()
    assert seen, "verify_settled did not reach the shadow-mode reporter at all"
    assert seen[0][0] == "operation", (
        f"the hook must report at the 'operation' site, got {seen[0][0]!r}")

    # and it still carries a shared walk when one is offered, so P6.a did not
    # cost the saving that motivated inlining it in the first place
    seen.clear()
    doc, rep = {"marker": 1}, {"walk": 1}
    win.verify_settled(doc=doc, walk_report=rep)
    assert seen[0][1]["doc"] is doc and seen[0][1]["walk_report"] is rep, \
        "the shared walk must be passed through, not dropped"


def test_the_3d_view_renders_only_the_active_floor(fp, win, monkeypatch):
    """D68: the 3D popup renders the ACTIVE FLOOR, not every level.

    THE ID IS NOT THE NAME, and that is the trap this pins. `build_model`
    filters by level **id** (`L1`, `L2`); `active_floor` is the level **name**
    (`default`, `second`). Passing the name straight through matches nothing and
    renders an EMPTY model with a note nobody reads -- a silent blank window,
    worse than the defect. So the assertion is on the RESOLVED ids, and it fails
    both ways: if the filter is dropped (every level) and if it is wrong (none).
    """
    from pathlib import Path

    plan = Path(__file__).resolve().parent.parent / "examples" \
        / "roundedMultifloor.json"
    win.load_path(str(plan))

    doc = win.design_document()
    ids = {lv["id"] for lv in doc["levels"]}
    names = {lv["name"] for lv in doc["levels"]}
    assert len(ids) > 1, "precondition: this fixture must be multi-floor"
    assert not (ids & names), \
        "precondition: ids and names must differ, or this pins nothing"

    seen = {}

    def _capture(d, levels=None, **kw):
        seen["levels"] = levels
        raise ImportError                     # stop before any GL/QML work

    import floorplanner.viewer.fp3d as fp3d
    monkeypatch.setattr(fp3d, "build_model", _capture)
    try:
        win.show_3d_view()
    except ImportError:
        pass

    want = [lv["id"] for lv in doc["levels"]
            if lv["name"] == win.active_floor]
    assert seen.get("levels") == want, (
        f"the 3D view must be scoped to the active floor {win.active_floor!r} "
        f"-> {want}, got {seen.get('levels')!r}")
    assert seen["levels"], "an empty filter renders a BLANK view, not all floors"
