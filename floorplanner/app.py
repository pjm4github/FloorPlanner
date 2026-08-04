"""Application entry point."""
import os
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from floorplanner.config import (APP_NAME, APP_VERSION, FONT_DIR, FONT_FAMILY,
                                 load_fonts)
from floorplanner.design.verify import ENV_VAR as VERIFY_ENV
from floorplanner.mainwindow import MainWindow


def main():
    # P1.6 shadow mode.  The flag just sets the env var the verifier reads, so
    # there is ONE switch however it was thrown -- and the test suite (which
    # cannot pass argv) turns it on the same way CI does.
    if "--verify-design" in sys.argv:
        sys.argv.remove("--verify-design")
        os.environ[VERIFY_ENV] = "1"
    # point Qt's own font lookup at the bundled fonts as well: platforms
    # without system font discovery (e.g. offscreen) read this during
    # QApplication startup, which silences the missing-font-dir warning
    if FONT_DIR.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(FONT_DIR))
    # Qt Quick 3D wants its surface format set BEFORE the QApplication exists,
    # so this cannot live in the 3D view itself -- it has to run here, in the
    # one place that is always earlier. It is guarded because the 3D stack is
    # an OPTIONAL dependency: without it the editor launches exactly as before
    # and only the 3D view is unavailable (it says so when asked). An
    # unguarded import here would make an optional extra mandatory, which is
    # the failure this whole seam exists to avoid.
    try:
        from PyQt6.QtGui import QSurfaceFormat
        from PyQt6.QtQuick3D import QQuick3D
        QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat(4))
    except ImportError:
        pass
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
