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
