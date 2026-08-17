"""Standalone exporters for FloorPlanner documents.

Nothing in here imports `floorplanner` -- same reason as `floorplanner/viewer/`
(see that package's own docstring): a module here reads a saved v5 document
directly and must stay usable from a plain `python -m` invocation or a test,
without dragging in the Qt-heavy editor package `floorplanner/__init__.py`
star-imports. Where a fact genuinely belongs to the rest of the app (wall
thickness, the schema), the module loads the ONE file that owns it BY PATH
(`importlib`), exactly as `floorplanner/viewer/fp3d.py` already does for the
furnishing catalog and `floorplanner.design.validate` -- never
`import floorplanner.design...`.
"""
