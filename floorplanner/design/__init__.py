"""The v5 design model + validation (vendored at P0.7).

Currently holds the packaged JSON Schema and the validator. `check()` is pure
Python and safe to import at runtime; JSON-Schema validation lazy-imports
`jsonschema`, a dev/test dependency that is NOT shipped, so importing this
package never requires it.

`bridge.py` (the scene <-> design walk) is deliberately NOT re-exported here: it
is the only module in the package that imports Qt, and keeping it off this
surface means `model`/`topology`/`legacy`/`validate` stay importable without the
scene layer. Import it explicitly:
`from floorplanner.design.bridge import design_from_scene`.
"""
from floorplanner.design.model import (  # noqa: F401
    Design, Furnishing, Group, Level, Opening, OutlineEdge, Provenance, Room,
    Vertex, Wall,
)
from floorplanner.design.topology import (  # noqa: F401
    Face, enclosing_face, merge_collinear, planarize, split_edge, trace_faces,
)
from floorplanner.design.validate import (  # noqa: F401
    SCHEMA_PATH, check, load_schema, report, schema_errors,
)
