"""Reference-image import, calibration and wall extraction (P2.5).

Lifted VERBATIM out of `MainWindow` as a mixin, so `win.start_image_import(...)`
and `win.extract_from_reference(...)` resolve unchanged.
"""
import os

from PyQt6 import sip  # noqa: F401
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

try:
    from PyQt6.QtSvg import QSvgGenerator
except ImportError:
    QSvgGenerator = None

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import *  # noqa: F401
from floorplanner.rooms import *  # noqa: F401
from floorplanner.items import *  # noqa: F401
from floorplanner.dialogs import *  # noqa: F401
from floorplanner.view import *  # noqa: F401
from floorplanner.macro import *  # noqa: F401


class ImageIOMixin:
    def import_from_image(self, path=None, *, width_ft=40.0, merge=3,
                          threshold=128, wall_type="exterior",
                          interactive=True):
        """File > Import from image: detect walls in a raster floor plan, show
        them as a blue ghost overlay, and add them on accept.  Pass
        interactive=False (with explicit params) to run headlessly."""
        if interactive and path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import plan from image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*)")
            if not path:
                return None
            dlg = ImageImportDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return None
            width_ft, merge, threshold = dlg.values()
        try:
            import fp_extract
            gray = fp_extract.load_gray(path)
            h, w = gray.shape
            walls_px = fp_extract.detect_walls(gray, threshold, 24, merge, 40)
            segs = fp_extract.scene_segments(walls_px, w, h, width_ft=width_ft)
        except Exception as ex:                       # noqa: BLE001
            if interactive:
                QMessageBox.critical(self, "Import failed", str(ex))
            return None
        if not segs:
            if interactive:
                QMessageBox.information(
                    self, "Import from image",
                    "No walls detected.  Try a cleaner image or adjust the "
                    "threshold / merge settings.")
            return None

        self._show_wall_ghost(segs)
        if interactive:
            ok = QMessageBox.question(
                self, "Import from image",
                f"Detected {len(segs)} wall(s), shown in blue on the canvas.\n"
                "Add them to the plan?") == QMessageBox.StandardButton.Yes
            self._clear_wall_ghost()
            if not ok:
                return None
        else:
            self._clear_wall_ghost()

        for x0, y0, x1, y1 in segs:
            self.scene.addItem(
                WallItem(QPointF(x0, y0), QPointF(x1, y1), wall_type))
        rebuild_all_walls(self.scene)
        self._update_totals()
        self._commit_if_changed()
        self.status(f"Imported {len(segs)} wall(s) from {os.path.basename(path)}"
                    " — click an enclosed area with the Room tool to name it.")
        return len(segs)

    def _show_wall_ghost(self, segs):
        """Draw the candidate walls as a translucent blue overlay and fit the
        view to them so the user can preview before accepting."""
        self._clear_wall_ghost()
        path = QPainterPath()
        for x0, y0, x1, y1 in segs:
            path.moveTo(QPointF(x0, y0))
            path.lineTo(QPointF(x1, y1))
        item = QGraphicsPathItem(path)
        pen = QPen(QColor(37, 99, 235, 170), 6.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        item.setPen(pen)
        item.setZValue(1_000_000)                     # above everything
        self.scene.addItem(item)
        self._wall_ghost = item
        self.view.fitInView(item.boundingRect().adjusted(-24, -24, 24, 24),
                            Qt.AspectRatioMode.KeepAspectRatio)

    def _clear_wall_ghost(self):
        item = getattr(self, "_wall_ghost", None)
        if item is not None:
            if item.scene() is not None:
                self.scene.removeItem(item)
            self._wall_ghost = None

    def start_image_import(self, path=None):
        """File > Import from image: drop the PNG on the canvas as a backdrop
        to move / scale / crop / calibrate, then Extract walls."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import plan from image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*)")
            if not path:
                return None
        img = QImage(path)
        if img.isNull():
            QMessageBox.critical(self, "Import failed",
                                 f"Could not read image:\n{path}")
            return None
        ipp = canvas_rect().width() * 0.7 / max(img.width(), 1)
        item = ReferenceImageItem(img, ipp)
        item.setPos(QPointF(canvas_rect().width() * 0.1,
                            canvas_rect().height() * 0.1))
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        self.view.fitInView(item.sceneBoundingRect().adjusted(-48, -48, 48, 48),
                            Qt.AspectRatioMode.KeepAspectRatio)
        self.status("Image placed — drag to move, drag a corner to scale, "
                    "right-click for Calibrate / Crop / Extract walls / "
                    "Remove.")
        return item

    def _finish_calibrate(self, item, pts):
        val, ok = QInputDialog.getDouble(
            self, "Calibrate scale",
            "Real distance between the two clicked points (feet):",
            10.0, 0.01, 100000.0, 2)
        if not ok or item is None:
            return
        item.calibrate(pts[0], pts[1], val * FOOT)
        self.status(f"Calibrated — that span is now {fmt_ftin(val * FOOT)}.")

    def extract_from_reference(self, item, interactive=True):
        """Detect walls in the (scaled/cropped) backdrop and add them, with a
        blue ghost preview when interactive."""
        segs = item.wall_segments()
        if not segs:
            if interactive:
                QMessageBox.information(
                    self, "Extract walls",
                    "No walls detected.  Calibrate/crop closer or adjust the "
                    "image, then try again.")
            return None
        self._show_wall_ghost(segs)
        if interactive:
            ok = QMessageBox.question(
                self, "Extract walls",
                f"Detected {len(segs)} wall(s), shown in blue.  Add them to "
                "the plan?") == QMessageBox.StandardButton.Yes
            self._clear_wall_ghost()
            if not ok:
                return None
        else:
            self._clear_wall_ghost()
        for x0, y0, x1, y1 in segs:
            self.scene.addItem(
                WallItem(QPointF(x0, y0), QPointF(x1, y1), "exterior"))
        # DEFECT 19, in-app arm.  Pixel-detected ends land near each other but
        # rarely on each other, and this path injects walls straight into the
        # live scene -- it never passes through a load, so P2.1's weld-on-open
        # never sees them, and per the corrected F5 nothing else welds either.
        # Without this every extracted plan is born with open junctions, which
        # is exactly what leaks room detection between spaces.
        weld_scene(self.scene)
        rebuild_all_walls(self.scene)
        self._update_totals()
        self._commit_if_changed()
        self.status(f"Added {len(segs)} wall(s) — right-click the image to "
                    "remove it, then name rooms with the Room tool.")
        return len(segs)
