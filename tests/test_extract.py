"""PNG -> floor plan extraction (fp_extract.py): wall detection, plan build,
and the end-to-end CLI."""
import json
import os
import subprocess
import sys

import pytest
from PyQt6.QtGui import QColor, QImage, QPainter, QPen

pytestmark = pytest.mark.extract

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_plan_png(path, w=600, h=400, line=6):
    """A clean synthetic plan: outer rectangle + one interior wall."""
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    p.setPen(QPen(QColor("black"), line))
    p.drawRect(40, 40, w - 80, h - 80)            # outer walls
    p.drawLine(w // 2, 40, w // 2, h - 40)        # one interior wall
    p.end()
    assert img.save(str(path), "PNG")
    return path


def test_detect_walls_on_clean_plan(qapp, tmp_path):
    import fp_extract as FX
    png = _make_plan_png(tmp_path / "plan.png")
    gray = FX.load_gray(str(png))
    assert gray.shape == (400, 600) and gray.dtype.itemsize == 1
    assert gray.flags["OWNDATA"]                  # not a view into a freed buf

    walls = FX.detect_walls(gray, 128, 24, 3, 40)
    horiz = [w for w in walls if w[1] == w[3]]
    vert = [w for w in walls if w[0] == w[2]]
    assert len(horiz) == 2                         # top + bottom
    assert len(vert) == 3                          # left, middle, right
    assert len(walls) == 5


def test_build_plan_scales_to_real_width(fp, qapp, tmp_path):
    import fp_extract as FX
    FP = fp                                        # use the conftest app/module
    png = _make_plan_png(tmp_path / "plan.png")
    gray = FX.load_gray(str(png))
    walls = FX.detect_walls(gray, 128, 24, 3, 40)
    win, info = FX.build_plan(FP, walls, gray.shape[1], gray.shape[0],
                              width_ft=30)
    try:
        assert info["walls"] == 5
        wall_items = [it for it in win.scene.items()
                      if isinstance(it, FP.WallItem)]
        assert len(wall_items) == 5
        # the outer span should be ~30 ft wide (360"), within a few inches
        xs = [c for w in wall_items for c in (w.p1.x(), w.p2.x())]
        assert (max(xs) - min(xs)) == pytest.approx(360, abs=8)
    finally:
        win.close()


def test_build_plan_rooms_detectable(fp, qapp, tmp_path):
    # the extracted walls enclose two rooms; the app can detect them
    import fp_extract as FX
    FP = fp                                        # use the conftest app/module
    png = _make_plan_png(tmp_path / "plan.png")
    gray = FX.load_gray(str(png))
    walls = FX.detect_walls(gray, 128, 24, 3, 40)
    win, _ = FX.build_plan(FP, walls, gray.shape[1], gray.shape[0],
                           width_ft=30)
    from PyQt6.QtCore import QPointF
    try:
        # a point inside the left half should resolve to an enclosed room
        res = FP.detect_room(win.scene, QPointF(110, 120))
        assert res is not None
        assert res[1] > 50                         # a sane area in sq ft
    finally:
        win.close()


def test_gui_import_from_image_adds_walls(fp, win, tmp_path):
    png = _make_plan_png(tmp_path / "plan.png")
    n = win.import_from_image(str(png), width_ft=30, interactive=False)
    assert n == 5
    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 5
    assert getattr(win, "_wall_ghost", None) is None   # preview ghost cleared


def test_gui_import_ghost_overlay_shows_and_clears(fp, win, tmp_path):
    from PyQt6.QtWidgets import QGraphicsPathItem
    import fp_extract as FX
    png = _make_plan_png(tmp_path / "plan.png")
    gray = FX.load_gray(str(png))
    h, w = gray.shape
    segs = FX.scene_segments(FX.detect_walls(gray, 128, 24, 3, 40), w, h,
                             width_ft=30)
    win._show_wall_ghost(segs)
    assert [it for it in win.scene.items()
            if isinstance(it, QGraphicsPathItem)]      # one preview overlay
    win._clear_wall_ghost()
    assert not [it for it in win.scene.items()
                if isinstance(it, QGraphicsPathItem)]


def test_start_image_import_places_backdrop(fp, win, tmp_path):
    png = _make_plan_png(tmp_path / "plan.png")
    item = win.start_image_import(str(png))
    assert isinstance(item, fp.ReferenceImageItem)
    assert item.scene() is win.scene
    assert item.inches_per_pixel() > 0


def test_reference_image_calibrate_sets_scale(fp, win, tmp_path):
    from PyQt6.QtCore import QPointF
    # the synthetic plan's outer box spans image px x=40..560 (520 px wide)
    item = win.start_image_import(str(_make_plan_png(tmp_path / "plan.png")))
    ipp0 = item.inches_per_pixel()
    p1 = item.mapToScene(QPointF(40 * ipp0, 200 * ipp0))
    p2 = item.mapToScene(QPointF(560 * ipp0, 200 * ipp0))
    item.calibrate(p1, p2, 360.0)                 # tell it 520 px == 30 ft
    assert item.inches_per_pixel() == pytest.approx(360.0 / 520.0, abs=1e-4)


def test_reference_image_corner_scale(fp, win, tmp_path):
    item = win.start_image_import(str(_make_plan_png(tmp_path / "plan.png")))
    w0, _ = item._size_in()
    item.set_inches_per_pixel(item.inches_per_pixel() * 2)
    w1, _ = item._size_in()
    assert w1 == pytest.approx(2 * w0)


def test_extract_from_reference_adds_walls(fp, win, tmp_path):
    from PyQt6.QtCore import QPointF
    item = win.start_image_import(str(_make_plan_png(tmp_path / "plan.png")))
    ipp0 = item.inches_per_pixel()
    item.calibrate(item.mapToScene(QPointF(40 * ipp0, 200 * ipp0)),
                   item.mapToScene(QPointF(560 * ipp0, 200 * ipp0)), 360.0)
    n = win.extract_from_reference(item, interactive=False)
    assert n == 5
    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 5


def test_extracted_walls_snap_to_6in_grid(fp, win, tmp_path):
    item = win.start_image_import(str(_make_plan_png(tmp_path / "plan.png")))
    step = fp.SETTINGS["wall_snap_in"]             # 6"
    segs = item.wall_segments()
    assert segs
    for x0, y0, x1, y1 in segs:
        for c in (x0, y0, x1, y1):
            assert c == pytest.approx(round(c / step) * step)


def test_reference_image_crop_reduces_walls(fp, win, tmp_path):
    from PyQt6.QtCore import QPointF, QRectF
    item = win.start_image_import(str(_make_plan_png(tmp_path / "plan.png")))
    before = len(item.wall_segments())
    ipp = item.inches_per_pixel()
    crop = QRectF(item.mapToScene(QPointF(35 * ipp, 35 * ipp)),
                  item.mapToScene(QPointF(305 * ipp, 365 * ipp)))
    assert item.crop_to_scene_rect(crop)          # keep the left half
    assert len(item.wall_segments()) < before


@pytest.mark.slow
def test_fp_extract_cli_end_to_end(qapp, tmp_path):
    png = _make_plan_png(tmp_path / "plan.png")
    out = tmp_path / "plan.json"
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    proc = subprocess.run(
        [sys.executable, "fp_extract.py", "--in", str(png), "--out", str(out),
         "--width-ft", "30"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env=env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"], result["errors"]
    assert result["counts"]["walls"] == 5

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["format"] == "floorplanner-json"
    assert len(data["walls"]) == 5
