#!/usr/bin/env python3
"""`floorplanner.design.validate.STD_T`, loaded BY PATH -- a LEAF, and
deliberately empty of anything else: no imports beyond the standard
library, no dataclasses, nothing a by-path `exec_module` of a SIBLING file
could trip over.

0077-ruling.md sec5: `fp2pdf.py` used to borrow this loader by execing the
whole 23KB `fp2dxf.py` module by path just to reach its seven-line
loader -- which then itself by-paths `validate.py`, so importing `fp2pdf`
ran two unrelated modules, and `fp2dxf.py`'s own `ConvertResult`
`@dataclass` forced a `sys.modules` registration hack in `fp2pdf.py` to
make THAT work at all. **A by-path loader is five lines of plumbing, not
a fact about the world; two copies of it are not D73. Seven thickness
numbers in two places are** (0077 sec5's own words). Both exporters now
load THIS file by path -- never each other -- and only this file touches
`validate.py`.

Lazy by design, not module scope: nothing runs merely by importing this
file. `load_std_thickness()` execs `validate.py` fresh on every call (a
single small file; caching, if a caller wants it, is the caller's job --
see `fp2dxf.py`/`fp2pdf.py`'s own `_std_t()` wrappers)."""
import importlib.util
from pathlib import Path


def load_std_thickness() -> dict[str, float]:
    """`floorplanner.design.validate.STD_T`, by path -- not
    `from floorplanner.design.validate import STD_T`: importing ANY
    `floorplanner` submodule first runs `floorplanner/__init__.py`, which
    star-imports the whole Qt editor (measured at P5.2, D73's own text).
    `floorplanner/viewer/fp3d.py` solves the identical problem the same
    way."""
    path = Path(__file__).resolve().parent.parent / "design" / "validate.py"
    spec = importlib.util.spec_from_file_location("_stdt_validate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.STD_T)
