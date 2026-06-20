"""Application entry point."""
import os
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from floorplanner.config import (APP_NAME, APP_VERSION, FONT_DIR, FONT_FAMILY,
                                 load_fonts)
from floorplanner.mainwindow import MainWindow


def main():
    # point Qt's own font lookup at the bundled fonts as well: platforms
    # without system font discovery (e.g. offscreen) read this during
    # QApplication startup, which silences the missing-font-dir warning
    if FONT_DIR.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(FONT_DIR))
    app = QApplication(sys.argv)
    # set only the application name (no org) so the standard AppConfig path
    # is .../FloorPlanner rather than .../FloorPlanner/FloorPlanner
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    load_fonts()
    app.setFont(QFont(FONT_FAMILY, 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
