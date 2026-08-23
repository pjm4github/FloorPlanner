"""`fp2pdf`'s four hygiene fixes (0072-ruling.md sec2), the same class
`fp2dxf.py` was already fixed for five days earlier (0038-ruling.md):

  1. a THIRD wall-thickness table, disagreeing with the normative
     `floorplanner.design.validate.STD_T` in 4 of 7 rows -- now read live
     via `fp2dxf.py`'s own by-path loader, reused not transcribed.
  2. `raise SystemExit` inside `convert()` -- a Qt menu handler's
     `try/except Exception` around this call would never see it coming.
  3. `print()` inside `convert()`, and no result object -- now returns a
     `ConvertResult` (sheets written + warnings) and prints nothing.
  4. `reportlab` imported at module top, in no requirements file -- an
     unguarded import would stop the whole app starting for anyone
     without it (D40). Now deferred into `convert()`, raising `ValueError`
     with a reason if missing, so the MODULE itself always imports.

Qt-free by construction, like `fp2dxf.py` -- `fp2pdf` imports nothing from
`floorplanner` (`floorplanner/export/__init__.py`'s own docstring), so this
needs no `fp`/`win` fixture.
"""
import json
import re
from pathlib import Path

import pytest

from floorplanner.export import fp2pdf
from floorplanner.export.fp2pdf import ConvertResult, convert

pytestmark = pytest.mark.io

_MINIMAL_LEVEL = {"id": "L1", "name": "Main", "elevation_in": 0.0,
                  "height_in": 96.0, "kind": "storey", "reference": False}
_MINIMAL_META = {"title": "Test House", "subtitle": "", "author": "Tester",
                 "assembly_note": "note", "dim_note": "dim"}


def _rect_doc():
    """A v5 doc with one closed rectangle -- enough for `Sheet._frame()`,
    which needs at least one wall (empty-level PDF generation is a
    separate, pre-existing limitation, not part of this receipt)."""
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": [
            {"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 240, "y": 0},
            {"id": "v3", "x": 240, "y": 200}, {"id": "v4", "x": 0, "y": 200},
        ],
        "walls": [
            {"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
             "type": "exterior", "openings": []},
            {"id": "w2", "level": "L1", "v1": "v2", "v2": "v3",
             "type": "exterior", "openings": []},
            {"id": "w3", "level": "L1", "v1": "v3", "v2": "v4",
             "type": "exterior", "openings": []},
            {"id": "w4", "level": "L1", "v1": "v4", "v2": "v1",
             "type": "exterior", "openings": []},
        ],
        "rooms": [], "furnishings": [],
    }


# ---------------------------------------------------------------------------
# (1) the thickness table
# ---------------------------------------------------------------------------

def test_thickness_table_matches_std_t_not_a_transcribed_copy():
    """Not a test of the seven current numbers (0072 sec6's own instruction)
    -- compares against the real, independently-imported STD_T, so a future
    change to either table is caught by disagreement, not by both moving
    together."""
    from floorplanner.design.validate import STD_T
    assert fp2pdf.DEFAULT_THICKNESS == STD_T


# ---------------------------------------------------------------------------
# (2) SystemExit -> ValueError
# ---------------------------------------------------------------------------

def test_convert_raises_valueerror_not_systemexit_on_a_non_v5_doc(tmp_path):
    """pytest.raises(ValueError) does NOT catch SystemExit (it is not an
    Exception subclass) -- if the old bug were present this test would
    ERROR, not pass, which is the differential this receipt needs."""
    with pytest.raises(ValueError, match="v5"):
        convert({"format": "x"}, tmp_path / "out.pdf", _MINIMAL_META)


# ---------------------------------------------------------------------------
# (3) a result object, nothing printed
# ---------------------------------------------------------------------------

def test_convert_returns_a_result_and_prints_nothing(tmp_path, capsys):
    pytest.importorskip("reportlab")
    out = tmp_path / "out.pdf"
    result = convert(_rect_doc(), out, _MINIMAL_META)
    assert isinstance(result, ConvertResult)
    assert result.out == out
    assert result.sheets == ["sheet P1: Main"]
    assert result.warnings == []
    assert out.exists()
    captured = capsys.readouterr()
    assert captured.out == "", f"convert() printed: {captured.out!r}"


# ---------------------------------------------------------------------------
# (4) reportlab is optional -- the MODULE always imports, only an actual
# export attempt fails, with a reason
# ---------------------------------------------------------------------------

def test_module_imports_without_reportlab():
    """The regression this receipt exists for: `from reportlab... import`
    at module top would make the whole module (and anything that imports
    it, including the app's own menu wiring once built) fail to import at
    all without reportlab installed. Importing fp2pdf here, in a suite that
    does not require reportlab, already partly proves this; PAGE and
    DEFAULT_THICKNESS are computed with no reportlab symbol at module
    scope, checked directly."""
    src = Path(fp2pdf.__file__).read_text(encoding="utf-8")
    top = src.split("\ndef ", 1)[0]           # everything before the first def
    assert "import reportlab" not in top and "from reportlab" not in top, (
        "reportlab is imported at module top -- the module (and its "
        "importer) can no longer load without it installed")


def test_convert_degrades_to_a_valueerror_when_reportlab_is_missing(
        monkeypatch, tmp_path):
    """Forces the missing-dependency path regardless of whether reportlab
    happens to be installed in this environment -- 0072 sec6's own
    instruction: "test it with the import actually blocked, not by reading
    the code." """
    import builtins
    real_import = builtins.__import__

    def blocked(name, *a, **kw):
        if name == "reportlab" or name.startswith("reportlab."):
            raise ImportError("simulated: reportlab not installed")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ValueError, match="reportlab"):
        convert(_rect_doc(), tmp_path / "out.pdf", _MINIMAL_META)


# ---------------------------------------------------------------------------
# the fourth, smaller hygiene item: an explicit encoding on the CLI's read
# ---------------------------------------------------------------------------

def test_main_reads_the_design_file_with_an_explicit_encoding():
    """A source check, not a behavioural one: the platform-default-encoding
    failure this guards against (cp1252 misreading a UTF-8-saved design,
    0043-report.md's own fourth hygiene item for fp2dxf.py) is platform-
    dependent, so a specific poison byte sequence would not reliably
    reproduce it on every CI leg this suite runs on. What is checked is
    that the call site names its encoding at all."""
    src = Path(fp2pdf.__file__).read_text(encoding="utf-8")
    m = re.search(r"a\.design\.read_text\(([^)]*)\)", src)
    assert m is not None, "main() no longer reads a.design.read_text(...)"
    assert "encoding" in m.group(1), (
        "a.design.read_text() has no explicit encoding -- reads the "
        "platform default instead of the UTF-8 every design is written as")


def test_main_round_trips_a_design_via_the_cli(tmp_path):
    pytest.importorskip("reportlab")
    design_path = tmp_path / "design.json"
    design_path.write_text(json.dumps(_rect_doc()), encoding="utf-8")
    out_path = tmp_path / "out.pdf"
    fp2pdf.main([str(design_path), "-o", str(out_path),
                "--title", "Test House", "--author", "Tester"])
    assert out_path.exists()
