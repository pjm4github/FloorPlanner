"""The Export submenu and the PDF plan set action -- 0072-ruling.md §4/§5,
unblocked and built per 0116-ruling.md.

`fp2pdf.py`'s own module-level receipts (the four hygiene fixes) live in
`tests/test_fp2pdf.py` and are not repeated here; this covers the app-side
wiring: the menu re-parent, `PDFExportOptionsDialog`, and
`win.export_pdf_path` -- the same shape `test_fp2dxf.py`'s own "the menu
wiring" section covers for DXF.
"""
import importlib.util

import pytest
from PyQt6.QtWidgets import QDialog, QMenu

pytestmark = pytest.mark.io


def _file_menu(win):
    return next(m for m in win.menuBar().findChildren(QMenu)
               if m.title().replace("&", "") == "File")


def _export_menu(win):
    m_file = _file_menu(win)
    a = next(a for a in m_file.actions() if a.text().replace("&", "") == "Export")
    return a.menu()


# ---------------------------------------------------------------------------
# the menu shape -- 0072-ruling.md §4's own diagram
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_file_menu_has_one_export_submenu(fp, win):
    m_file = _file_menu(win)
    export_actions = [a for a in m_file.actions()
                      if a.text().replace("&", "") == "Export"]
    assert len(export_actions) == 1
    assert export_actions[0].menu() is not None


@pytest.mark.gui
def test_the_export_submenu_carries_all_four_in_order(fp, win):
    labels = [a.text().replace("&", "") for a in _export_menu(win).actions()]
    assert labels == ["Rooms as CSV…", "Chief Architect (DXF)…",
                      "PDF plan set…", "Legacy v4…"]


@pytest.mark.gui
def test_the_dxf_label_carries_no_literal_arrow(fp, win):
    """0050-report.md flagged this against itself and it was never ruled
    until now: the old label was `"Export ▸ Chief Architect (DXF)…"`, the
    arrow baked into plain text rather than being the menu widget's job."""
    labels = [a.text() for a in _export_menu(win).actions()]
    assert not any("▸" in t for t in labels)


@pytest.mark.gui
def test_the_two_import_actions_are_not_moved(fp, win):
    """He asked about exports. Not touched, not renamed."""
    m_file = _file_menu(win)
    labels = [a.text().replace("&", "") for a in m_file.actions()
             if not a.isSeparator() and a.menu() is None]
    assert "Import rooms from CSV…" in labels
    assert "Import from image (PNG)…" in labels


# ---------------------------------------------------------------------------
# reportlab missing -> disabled with a reason, not a crash (D40)
# ---------------------------------------------------------------------------

def test_pdf_action_is_enabled_when_reportlab_is_present(fp, win):
    pytest.importorskip("reportlab")
    a_pdf = next(a for a in _export_menu(win).actions()
                if "PDF" in a.text())
    assert a_pdf.isEnabled()


def test_pdf_action_is_disabled_with_a_reason_when_reportlab_is_absent(
        fp, monkeypatch):
    """Tests it with the import actually blocked, not by reading the code
    (0072-ruling.md §6's own instruction, reused from `test_fp2pdf.py`)."""
    real_find_spec = importlib.util.find_spec

    def _blocked(name, *a, **kw):
        if name == "reportlab":
            return None
        return real_find_spec(name, *a, **kw)

    monkeypatch.setattr(importlib.util, "find_spec", _blocked)
    w2 = fp.MainWindow()
    try:
        a_pdf = next(a for a in _export_menu(w2).actions()
                    if "PDF" in a.text())
        assert not a_pdf.isEnabled()
        assert "reportlab" in a_pdf.toolTip()
    finally:
        w2.close()


# ---------------------------------------------------------------------------
# PDFExportOptionsDialog
# ---------------------------------------------------------------------------

def test_options_dialog_defaults_title_from_the_argument_not_RESIDENCE(fp, qapp):
    doc = {"levels": [{"id": "L1", "name": "Main", "kind": "storey"}]}
    dlg = fp.PDFExportOptionsDialog(doc, "MyHouse")
    try:
        assert dlg.ed_title.text() == "MyHouse"
        assert dlg.ed_title.text() != "RESIDENCE"
    finally:
        dlg.close()


def test_options_dialog_offers_one_checkbox_per_storey_level_not_site(fp, qapp):
    doc = {"levels": [{"id": "L1", "name": "Main", "kind": "storey"},
                      {"id": "L2", "name": "Upper", "kind": "storey"},
                      {"id": "S1", "name": "Site", "kind": "site"}]}
    dlg = fp.PDFExportOptionsDialog(doc, "T")
    try:
        assert len(dlg.level_checks) == 2
        assert {cb.text() for cb in dlg.level_checks} == {"Main", "Upper"}
    finally:
        dlg.close()


def test_options_dialog_values_reports_None_when_every_level_is_checked(fp, qapp):
    doc = {"levels": [{"id": "L1", "name": "Main", "kind": "storey"}]}
    dlg = fp.PDFExportOptionsDialog(doc, "T")
    try:
        _meta, only_levels, _concept = dlg.values()
        assert only_levels is None
    finally:
        dlg.close()


def test_options_dialog_values_names_only_the_checked_levels(fp, qapp):
    doc = {"levels": [{"id": "L1", "name": "Main", "kind": "storey"},
                      {"id": "L2", "name": "Upper", "kind": "storey"}]}
    dlg = fp.PDFExportOptionsDialog(doc, "T")
    try:
        dlg.level_checks[1].setChecked(False)
        _meta, only_levels, _concept = dlg.values()
        assert only_levels == ["L1"]
    finally:
        dlg.close()


def test_options_dialog_has_no_thickness_override_control(fp, qapp):
    """0072-ruling.md §5: a GUI control that lets a user contradict STD_T
    would reopen D73 through the front door -- not offered here."""
    doc = {"levels": [{"id": "L1", "name": "Main", "kind": "storey"}]}
    dlg = fp.PDFExportOptionsDialog(doc, "T")
    try:
        assert not hasattr(dlg, "ed_thickness")
        assert not any("thick" in ch.__class__.__name__.lower()
                       for ch in dlg.findChildren(object))
    finally:
        dlg.close()


# ---------------------------------------------------------------------------
# win.export_pdf_path -- the menu wiring, non-interactive
# (mirrors test_fp2dxf.py's "the menu wiring" section)
# ---------------------------------------------------------------------------

_META = {"title": "Test House", "subtitle": "", "author": "Tester",
         "assembly_note": "note", "dim_note": "dim"}


def test_export_pdf_path_writes_a_pdf_and_reports_it(fp, win, tmp_path, make_room):
    pytest.importorskip("reportlab")
    make_room(win.scene, 0, 0, 240, 120, name="Den")
    out = tmp_path / "out.pdf"
    result = win.export_pdf_path(str(out), _META, interactive=False)
    assert result is not None
    assert out.exists()
    assert result.sheets
    assert f"Wrote {out}" in win.statusBar().currentMessage()


def test_export_pdf_path_reports_a_bad_path_without_a_modal(fp, win, tmp_path):
    """Same discipline as `export_dxf_path`'s own test: a real OSError,
    headless and modal-free, caught like every other IO failure in the
    mixin (SESSION_SNAPSHOT §5's segfault-with-no-traceback trap)."""
    pytest.importorskip("reportlab")
    blocker = tmp_path / "blocked"
    blocker.write_text("x", encoding="utf-8")
    result = win.export_pdf_path(str(blocker / "sub" / "out.pdf"), _META,
                                 interactive=False)
    assert result is None


def test_export_pdf_path_only_levels_restricts_the_sheets(fp, win, tmp_path,
                                                           make_room):
    pytest.importorskip("reportlab")
    make_room(win.scene, 0, 0, 240, 120, name="Den")
    doc = win.design_document()
    only = [doc["levels"][0]["id"]]
    out = tmp_path / "out.pdf"
    result = win.export_pdf_path(str(out), _META, only_levels=only,
                                 interactive=False)
    assert result is not None
    assert len(result.sheets) == 1


# ---------------------------------------------------------------------------
# win.export_pdf -- the full interactive flow
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_export_pdf_shows_options_then_save_as_then_writes(
        fp, win, tmp_path, make_room, monkeypatch):
    """`export_pdf()` is the INTERACTIVE entry point (matching
    `export_dxf()`'s own shape), so its successful completion pops a real
    `QMessageBox.information` -- a STATIC/native call that does not route
    through a Python-level `QDialog.exec` monkeypatch and hangs headless
    (the modal-hangs-headless trap). Blocked to a no-op here so the flow
    can run to completion without a user to click OK."""
    pytest.importorskip("reportlab")
    make_room(win.scene, 0, 0, 240, 120, name="Den")
    out = tmp_path / "chosen.pdf"

    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(fp.QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (str(out), "")))
    monkeypatch.setattr(fp.QMessageBox, "information",
                        staticmethod(lambda *a, **k: None))
    win.export_pdf()
    assert out.exists()


@pytest.mark.gui
def test_cancelling_the_options_dialog_writes_nothing(
        fp, win, tmp_path, make_room, monkeypatch):
    make_room(win.scene, 0, 0, 240, 120, name="Den")
    calls = []
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Rejected)
    monkeypatch.setattr(fp.QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: calls.append(1)))
    win.export_pdf()
    assert calls == []                        # Save-As never even opened
