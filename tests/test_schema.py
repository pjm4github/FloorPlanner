"""P0.7: the vendored v5 validator (floorplanner.design.validate) accepts the
clean design corpus and still rejects the intentionally-corrupt fixture.

planc1.v5.json is the "does not launder its input" fixture -- schema-valid but
referentially corrupt on purpose. If check() ever stops failing it, the
validator has been weakened into a rubber stamp.
"""
import json
from pathlib import Path

import pytest

from floorplanner.design.validate import check, schema_errors

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
CORRUPT = "planc1.v5.json"


def _design_files():
    out = []
    for p in sorted(EXAMPLES.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("format") == "floorplanner-design":
            out.append(p)
    return out


DESIGN_FILES = _design_files()
CLEAN_FILES = [p for p in DESIGN_FILES if p.name != CORRUPT]


def test_corpus_discovered():
    # guard: the glob actually found the fixtures, so a rename can't silently
    # empty the corpus and make the parametrized tests vacuously pass
    names = {p.name for p in DESIGN_FILES}
    assert {"symmetricP1.json", "site_demo.json", CORRUPT} <= names


@pytest.mark.parametrize("path", CLEAN_FILES, ids=lambda p: p.name)
def test_clean_design_validates(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert schema_errors(doc) == [], f"{path.name} fails the JSON Schema"
    assert check(doc) == [], f"{path.name} fails a referential invariant"


def test_corrupt_fixture_passes_schema_but_fails_I6():
    doc = json.loads((EXAMPLES / CORRUPT).read_text(encoding="utf-8"))
    assert schema_errors(doc) == []            # it IS schema-valid
    errs = check(doc)
    assert any(e.startswith("I6") for e in errs), \
        "the corrupt fixture no longer fails I6 -- has check() been laundered?"
