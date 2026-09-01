"""The golden-file receipt for `fp2dxf` (handoff 0038-ruling.md SS7).

`fixtures/chief-export/sample_design.json` shipped in the handoff zip
alongside the `L1.dxf` / `L2.dxf` it produced -- but those were written by
the ORIGINAL `fp2dxf.py`, before its thickness table was rewired to read
`floorplanner.design.validate.STD_T` live (0038-ruling.md SS2-SS3). The
`L1.dxf` / `L2.dxf` (and their `.openings.json` sidecars) now committed
alongside the sample are the REGENERATED output of the current `convert()`
-- the differential receipt for that rewiring, per the ruling's own words:
"the regenerated golden files ARE the differential receipt ... regenerate
them in the same commit, and state the diff."

THE DIFF, stated once so it does not need re-deriving: only `exterior`
(6.5in -> 6.0in) and `railing` (3.0in -> 2.0in) wall faces moved --
`interior` (4.5in) and `partition` (3.5in) already agreed with `STD_T` and
are pixel-identical. The sample carries no `fence`/`hedge`/`retaining`
walls, so those three STD_T disagreements noted in 0038-ruling.md SS2 are
not exercised here. Both `.openings.json` sidecars are BYTE-IDENTICAL to
the original hand-off -- station spans are computed along the wall
centreline and never depended on thickness.

This test pins every decision fp2dxf.py's docstring and 0038-ruling.md SS3
make: a thickness change, a layer rename, a coordinate flip, a re-ordered
entity all turn it red. Qt-free by construction -- `fp2dxf` imports nothing
from `floorplanner` (see `floorplanner/export/__init__.py`), so this needs
no `fp`/`win` fixture, only a temp directory.

REGENERATED AGAIN, 0135-ruling.md's own door-symbol-by-type fix -- and the
diff caught something in the FIXTURE, not just the code: `sample_design.json`
itself carried two bogus `door_type` values, `"sliding"` and `"hinged"`,
neither a real `config.py:DOOR_TYPES` member. `oD2`'s `"sliding"` happened
to satisfy the OLD (dead) `door_type == "sliding"` check by coincidence, so
its slider geometry was already right; `oD1`/`uD1`'s `"hinged"` never
mattered to geometry (hinge/swings_toward carry that). Both corrected to
real catalog values (`SLIDER`, `LH`) in the same commit as the code fix --
this is the defect's own root cause, present in the golden fixture, not a
tangential cleanup. **THE DIFF:** `oD2`, `oD1`, `uD1`'s NOTES tag text
changed to the corrected type name; two new glass LINE entities appear on
`FP-WINDOWS` in both `L1.dxf` and `L2.dxf` (windows previously emitted gap
lines only); `oD2`'s own slider-panel geometry is UNCHANGED (the
coincidence above). Both `.openings.json` sidecars: only the `door_type`
field's text changed, stations untouched.

COMPARED AS TEXT, NOT RAW BYTES -- measured, not assumed. `convert()`
writes with `Path.write_text(..., encoding="utf-8")` and no `newline=`
argument, so on Windows every `\n` it emits becomes `\r\n` on disk; this
repo's `.gitattributes` (`* text=auto eol=lf`) then normalises the
COMMITTED copy back to bare `\n` on checkout. A byte-for-byte comparison
between a freshly generated file (CRLF, on Windows) and the checked-out
golden (LF, unconditionally, on every platform, per `eol=lf`) fails on
line endings alone with the content otherwise identical -- reproduced
directly: this suite went red immediately after a `git rebase` re-checked
out the fixtures. `.read_text()` applies universal-newline translation on
both sides, so the comparison is exactly what the golden-file test is
FOR (thickness, layer, coordinates, entity order) without being hostage
to a pre-existing, platform-dependent quirk in `convert()`'s own write
path that no defect has been filed against.
"""
import json
from pathlib import Path

import pytest

from floorplanner.export import fp2dxf
from floorplanner.export.fp2dxf import convert

pytestmark = pytest.mark.io

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "chief-export"
GOLDEN_LEVELS = ("L1", "L2")


def _regenerate(tmp_path):
    doc = json.loads((FIXTURE_DIR / "sample_design.json").read_text(encoding="utf-8"))
    result = convert(doc, tmp_path)
    return {p.stem: p for p in result.written}, result


@pytest.mark.parametrize("level", GOLDEN_LEVELS)
def test_convert_reproduces_the_committed_dxf(level, tmp_path):
    written, _ = _regenerate(tmp_path)
    fresh = written[level].read_text(encoding="utf-8")
    golden = (FIXTURE_DIR / f"{level}.dxf").read_text(encoding="utf-8")
    assert fresh == golden, (
        f"{level}.dxf regenerated from sample_design.json no longer matches "
        f"the committed golden file -- a thickness change, a layer rename or "
        f"a coordinate flip. Regenerate deliberately and state the diff "
        f"(0038-ruling.md SS7) if this is an intended change.")


@pytest.mark.parametrize("level", GOLDEN_LEVELS)
def test_convert_reproduces_the_committed_openings_sidecar(level, tmp_path):
    doc = json.loads((FIXTURE_DIR / "sample_design.json").read_text(encoding="utf-8"))
    convert(doc, tmp_path)
    fresh = (tmp_path / f"{level}.openings.json").read_text(encoding="utf-8")
    golden = (FIXTURE_DIR / f"{level}.openings.json").read_text(encoding="utf-8")
    assert fresh == golden, f"{level}.openings.json drifted from the golden sidecar"


def test_the_sample_converts_clean_no_warnings(tmp_path):
    """Positive control for the two tests above: they would pass just as
    happily if `convert()` silently produced nothing. The sample is a known-
    good design (0038-ruling.md's own acceptance input), so it must emit
    both levels and zero warnings -- an opening overrun/overlap or a
    zero-length wall would otherwise hide inside a content-identical pass
    against a golden file that itself carried the same defect."""
    _, result = _regenerate(tmp_path)
    assert {p.stem for p in result.written} == set(GOLDEN_LEVELS)
    assert result.warnings == []
    assert result.skipped_levels == []


# --------------------------------------------------------------------------
# 0135-ruling.md -- one DXF symbol per catalog door_type, windows made real
# --------------------------------------------------------------------------

_LEVEL = {"id": "L1", "name": "Main", "elevation_in": 0.0, "height_in": 96.0,
          "kind": "storey", "reference": False}


def _one_opening_doc(kind, door_type=None, hinge="v1", swings_toward="left"):
    """One 200" wall carrying a single opening -- enough for `emit_wall`,
    nothing else."""
    op = {"id": "o1", "kind": kind, "code": "3068",
          "anchor": {"from": "center", "offset_in": 0.0}}
    if kind in ("door", "gate"):
        op["door_type"] = door_type
        op["hinge"] = hinge
        op["swings_toward"] = swings_toward
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_LEVEL],
        "vertices": [{"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 200, "y": 0}],
        "walls": [{"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
                   "type": "exterior", "openings": [op]}],
        "rooms": [], "furnishings": [],
    }


def test_door_symbol_dispatch_is_exhaustive_over_the_real_catalog():
    """0135-ruling.md sec2's own receipt: dispatch is exhaustive over
    `config.py:DOOR_TYPES` itself -- fails the moment a new catalog type
    exists without a symbol here, rather than silently falling through to
    a generic swing the way `door_type == "sliding"` did."""
    from floorplanner.config import DOOR_TYPES
    for dt in DOOR_TYPES:
        symbol = fp2dxf._door_symbol("door", dt)
        assert symbol not in (None, "unknown"), (
            f"catalog door_type {dt!r} has no DXF symbol")


def test_door_symbol_flags_the_fixtures_own_former_bugs_as_unknown():
    """0135-ruling.md sec1's own finding, reproduced directly:
    `"sliding"` and `"hinged"` -- the two bogus values
    `sample_design.json` itself carried -- match nothing in the real
    catalog and must not be silently absorbed as a generic swing."""
    assert fp2dxf._door_symbol("door", "sliding") == "unknown"
    assert fp2dxf._door_symbol("door", "hinged") == "unknown"


def test_doorway_type_emits_no_arc_no_leaf():
    """0135-ruling.md sec2's own named receipt: DOORWAY emits zero arcs --
    the phantom swinging leaf D81's sibling defect gave every DOORWAY
    opening before this fix."""
    dxf = fp2dxf.DxfR12()
    ctx = fp2dxf.Ctx(doc=_one_opening_doc("door", "DOORWAY"))
    sidecar = {}
    fp2dxf.emit_wall(ctx, dxf, ctx.doc["walls"][0], sidecar)
    text = dxf.dumps()
    assert "\n0\nARC\n" not in text
    assert "DOORWAY" in text


def test_french_type_emits_exactly_two_arcs():
    """0135-ruling.md sec2's own named receipt: FRENCH emits two."""
    dxf = fp2dxf.DxfR12()
    ctx = fp2dxf.Ctx(doc=_one_opening_doc("door", "FRENCH"))
    sidecar = {}
    fp2dxf.emit_wall(ctx, dxf, ctx.doc["walls"][0], sidecar)
    text = dxf.dumps()
    assert text.count("\n0\nARC\n") == 2


def test_window_emits_a_glass_line_not_just_gap_lines():
    """0135-ruling.md sec2's own named receipt: window emits its glass
    line -- before this fix a window was bare gap-spanning lines and
    nothing else, indistinguishable from an unclassified opening."""
    dxf = fp2dxf.DxfR12()
    ctx = fp2dxf.Ctx(doc=_one_opening_doc("window"))
    sidecar = {}
    fp2dxf.emit_wall(ctx, dxf, ctx.doc["walls"][0], sidecar)
    text = dxf.dumps()
    # two gap lines (one per face) + one glass line at the centreline
    assert text.count("0\nLINE\n8\nFP-WINDOWS\n") == 3


def test_gate_still_gets_a_swing_leaf_and_arc():
    """Unchanged behaviour, confirmed: a gate is not a `door_type`-bearing
    kind, so it always gets the plain swing (matches the pre-0135 branch
    exactly, per 0135 sec2's "LH/RH, gate -- leaf+arc as today")."""
    dxf = fp2dxf.DxfR12()
    ctx = fp2dxf.Ctx(doc=_one_opening_doc("gate"))
    sidecar = {}
    fp2dxf.emit_wall(ctx, dxf, ctx.doc["walls"][0], sidecar)
    text = dxf.dumps()
    assert text.count("\n0\nARC\n") == 1


def test_convert_warns_on_an_unrecognized_door_type_but_still_renders(tmp_path):
    doc = _one_opening_doc("door", "sliding")   # the fixture's own former bug
    result = fp2dxf.convert(doc, tmp_path)
    assert len(result.written) == 1
    assert len(result.warnings) == 1
    assert "sliding" in result.warnings[0]
    assert "o1" in result.warnings[0]


def test_convert_r2_arc_count_matches_the_hand_verified_census(tmp_path):
    """0135-ruling.md sec1's own census on `wiscaway2026-08-30R2.json`: 9
    LH + 7 RH + 1 gate (one arc each) + 4 FRENCH (two arcs each) = 25
    arcs total, zero warnings -- every real door_type in the corpus
    dispatches to a real symbol."""
    doc = json.loads((Path(__file__).parent.parent / "fixtures" /
                      "wiscaway2026-08-30R2.json").read_text(encoding="utf-8"))
    result = fp2dxf.convert(doc, tmp_path)
    assert result.warnings == []
    total_arcs = sum(p.read_text(encoding="utf-8").count("\n0\nARC\n")
                     for p in result.written)
    assert total_arcs == 25


# --------------------------------------------------------------------------
# the menu wiring (File > Export > Chief Architect (DXF)...), planio.py
# --------------------------------------------------------------------------

def test_export_dxf_path_writes_a_dxf_per_level_and_reports_it(
        fp, win, tmp_path, make_room):
    """`win.export_dxf_path` is what the menu action calls (0038-ruling.md
    SS8). Non-interactive, the `_import_rooms`/`export_legacy_v4_path`
    convention -- no modal, headless-safe -- but it must still do everything
    the interactive path does: serialize the CURRENT scene through
    `design_document()` (not a fixture file) and write real DXF output."""
    make_room(win.scene, 0, 0, 240, 120, name="Den")
    result = win.export_dxf_path(str(tmp_path), interactive=False)
    assert result is not None
    assert len(result.written) == 1              # one active floor/level
    dxf = result.written[0]
    assert dxf.exists() and dxf.suffix == ".dxf"
    text = dxf.read_text(encoding="utf-8")
    assert "FP-WALLS" in text                     # the room's 4 walls landed
    assert (tmp_path / f"{dxf.stem}.openings.json").exists()
    assert "Wrote 1 file" in win.statusBar().currentMessage()


def test_export_dxf_path_reports_a_bad_outdir_without_a_modal(fp, win, tmp_path):
    """`convert()` raises on a genuine failure (0038-ruling.md SS4 "ONE": a
    `ValueError`, never `SystemExit`); the menu wiring must catch it exactly
    like every other IO failure in this mixin, not let it propagate out of a
    Qt slot (SESSION_SNAPSHOT SS5's segfault-with-no-traceback trap)."""
    # a file in place of the target directory makes the write fail with a
    # real OSError, headless and modal-free either way
    blocker = tmp_path / "blocked"
    blocker.write_text("x", encoding="utf-8")
    result = win.export_dxf_path(str(blocker / "sub"), interactive=False)
    assert result is None
    assert "failed" in win.statusBar().currentMessage().lower()
