"""FloorPlanner — a 2D architectural floor-plan editor (PyQt6).

The application is organised as this package; the top-level ``FloorPlanner.py``
is a thin compatibility shim that re-exports this package's public API (so
``import FloorPlanner`` and ``python FloorPlanner.py`` keep working).

Submodules are aggregated here via star re-export in dependency order.
"""
from .config import *  # noqa: F401,F403
from .geometry import *  # noqa: F401,F403
from .catalog import *  # noqa: F401,F403
from .model import *  # noqa: F401,F403
from .walls import *  # noqa: F401,F403
from .rooms import *  # noqa: F401,F403
from .items import *  # noqa: F401,F403
from .dialogs import *  # noqa: F401,F403
from .view import *  # noqa: F401,F403
from .macro import *  # noqa: F401,F403
from .mainwindow import *  # noqa: F401,F403
from .app import *  # noqa: F401,F403
