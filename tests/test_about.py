"""Help ▸ About dialog and the OS-standard storage locations (designs
folder, settings file).  Path-writing tests run with Qt test mode so they
never touch the real user config directory."""

import pytest
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QLabel, QMenu

pytestmark = pytest.mark.io


def test_standard_paths_are_named_and_nested(fp):
    assert fp.designs_dir().name == "FloorPlanner"
    assert fp.settings_file().name == "floorplanner.ini"
    assert fp.settings_file().parent == fp.config_dir()


def test_help_menu_present(fp, qapp, win):
    titles = [m.title() for m in win.menuBar().findChildren(QMenu)]
    assert any("Help" in t for t in titles)


def test_about_dialog_lists_storage_locations(fp, qapp):
    dlg = fp.AboutDialog()
    text = " ".join(lab.text() for lab in dlg.findChildren(QLabel))
    assert "settings file" in text.lower()
    assert "designs" in text.lower()
    assert str(fp.designs_dir()) in text
    assert str(fp.settings_file()) in text
    assert hasattr(dlg, "btn_designs") and hasattr(dlg, "btn_config")


def test_api_key_round_trips_via_settings_file(fp, qapp):
    QStandardPaths.setTestModeEnabled(True)
    try:
        fp.save_api_key("sk-ant-unit-test")
        assert fp.load_saved_api_key() == "sk-ant-unit-test"
        assert fp.settings_file().exists()
    finally:
        fp.save_api_key("")
        QStandardPaths.setTestModeEnabled(False)
