"""Parametric furnishings: a furnishing whose shape follows parameters stored
with it in the plan (the furnishing record's `state`).

Layers, each usable without the one after it:

    params, findings      what a parameter is, what a validation result is
    registry              kind -> its definition
    stair_geometry        the stair calculator (no imports; the viewer loads
                          it by path)
    stairs                the STAIRS kind: parameters, validation, summary
    dialog, stair_view    PyQt6 -- imported only when a dialog is opened

Importing this package imports NO Qt.
"""
from floorplanner.parametric import registry, stair_geometry, stairs  # noqa: F401
from floorplanner.parametric.findings import Finding  # noqa: F401
from floorplanner.parametric.registry import get, is_parametric  # noqa: F401
