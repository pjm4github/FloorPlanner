"""Fast sanity checks: the module imports, the app builds, the canvas exists."""
import pytest

pytestmark = pytest.mark.smoke


def test_module_imports(fp):
    for sym in ("MainWindow", "WallItem", "RoomItem", "FurnishingItem",
                "GroupItem", "detect_room", "rebuild_all_walls"):
        assert hasattr(fp, sym), f"missing {sym}"


def test_mainwindow_builds(win):
    assert win.scene is not None
    assert win.view is not None


def test_canvas_rect_positive(fp):
    r = fp.canvas_rect()
    assert r.width() > 0 and r.height() > 0


def test_default_settings_present(fp):
    for key in ("wall_snap_in", "rotate_snap_deg",
                "canvas_w_in", "canvas_h_in"):
        assert key in fp.DEFAULT_SETTINGS
