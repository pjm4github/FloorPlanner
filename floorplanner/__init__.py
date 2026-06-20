"""FloorPlanner — a 2D architectural floor-plan editor (PyQt6).

The application is organised as a package; the top-level ``FloorPlanner.py``
remains as a thin compatibility shim that re-exports this package's public API
(so ``import FloorPlanner`` and ``python FloorPlanner.py`` keep working).

During the package split (REFACTOR_PLAN.md Phase B) submodules are aggregated
here via star re-export as they are extracted.
"""
from .config import *  # noqa: F401,F403
from .model import *  # noqa: F401,F403
