"""The v5 design model + validation (vendored at P0.7).

Currently holds the packaged JSON Schema and the validator. `check()` is pure
Python and safe to import at runtime; JSON-Schema validation lazy-imports
`jsonschema`, a dev/test dependency that is NOT shipped, so importing this
package never requires it.
"""
from floorplanner.design.validate import (  # noqa: F401
    SCHEMA_PATH, check, load_schema, report, schema_errors,
)
