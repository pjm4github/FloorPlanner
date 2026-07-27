"""The legacy corpus is FROZEN (P2.4).

The v5 cutover converts the app, the tooling and the shipped examples. It must
not convert the files the converter proves itself against -- an importer with no
real v1-v4 input left is an importer nothing tests.

This is a guard, not a feature test. It exists because "convert `examples/*.json`"
is exactly the kind of instruction a later task follows too literally, and the
damage would be invisible: every legacy test would still pass, against inputs
that had quietly become v5 and no longer exercise the importer at all.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

# name -> (format, version). Version is pinned too: sample_plan.json is the only
# v1 file in the repo, so it exercises a migration path nothing else does.
FROZEN = {
    "planc1.json": ("floorplanner-json", 3),
    "sample_plan.json": ("floorplanner-json", 1),
}


@pytest.mark.parametrize("name", sorted(FROZEN))
def test_legacy_corpus_stays_legacy(name):
    doc = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    fmt, ver = FROZEN[name]
    assert doc["format"] == fmt, (
        f"{name} was converted to {doc['format']}. It is a FROZEN legacy input: "
        f"planc1.json is the corruption fixture AND the importer's acceptance "
        f"input; sample_plan.json is the clean legacy input for the P1.4 bridge "
        f"tests. Converting either leaves the importer with nothing real to "
        f"prove itself against. Write the v5 rendering alongside instead "
        f"(the planc1.json / planc1.v5.json pairing).")
    assert doc["version"] == ver, f"{name} was migrated in place to v{doc['version']}"


def test_the_importer_still_has_real_legacy_input():
    """The invariant behind the file list: at least one genuine v1-v4 document
    survives in the corpus, permanently."""
    legacy = [p for p in EXAMPLES.glob("*.json")
              if json.loads(p.read_text(encoding="utf-8")).get("format")
              == "floorplanner-json"]
    assert len(legacy) >= 2, f"legacy corpus shrank to {[p.name for p in legacy]}"


# --------------------------------------------------------------------------
# P2.4: the macro `open` token now triggers a CONVERSION on a legacy file.
# It must collect and report, never raise a modal -- a QMessageBox in a macro
# or a test hangs forever headless.
# --------------------------------------------------------------------------
def _modal_failsafe(ms=2000):
    """Dismiss any modal that appears, and record it, so a regression here is a
    red X rather than a CI job running to its timeout.

    A modal `exec()` blocks the caller forever headless -- nothing can click OK
    -- so without this the test's failure mode is a HANG. Timers still fire
    inside a nested exec loop, which is exactly how `macro._modal_step` drives
    dialogs; the same mechanism dismisses one here. Returns a list that stays
    empty when the path is correctly non-modal."""
    seen = []

    def check():
        m = QApplication.activeModalWidget() or QApplication.activePopupWidget()
        if m is not None:
            seen.append(type(m).__name__)
            m.close()
    QTimer.singleShot(ms, check)
    return seen


def test_macro_open_of_a_legacy_plan_converts_without_a_modal(fp, win):
    """P2.1 built the non-modal path (`load_path` -> `open_document(
    interactive=False)`); this is the test that says so, rather than the claim.
    A QMessageBox here would hang every macro and every CI run."""
    modals = _modal_failsafe()
    res = win.run_macro(f'open "{EXAMPLES / "planc1.json"}"')
    assert modals == [], f"a modal opened during a macro: {modals}"
    assert res.get("errors") in (None, [], ()), res

    # converted: the report was COLLECTED (the _import_errors shape), not shown
    assert win._conversion is not None
    assert win._conversion["ends_moved"] == 4
    assert win._provenance["endpoints_welded"] == 4
    assert "wall ends moved" in win.statusBar().currentMessage()
    # ...and the document is dirty, so the user is asked before losing it
    assert win._is_dirty()


def test_macro_open_of_a_v5_plan_is_silent_and_clean(fp, win):
    """The other half: a v5 file is not converted, not reported, not dirty."""
    win.run_macro(f'open "{EXAMPLES / "symmetricP1.json"}"')
    assert win._conversion is None
    assert not win._is_dirty()


def test_macro_save_writes_v5(fp, win, make_room, tmp_path):
    make_room(win.scene, 0, 0, 144, 120, "Den")
    out = tmp_path / "macro.json"
    win.run_macro(f'save "{out}"')
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["format"] == "floorplanner-design" and doc["version"] == 5
