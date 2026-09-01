"""P1.1: the Qt-free v5 dataclasses round-trip a design document byte-identically,
and the model module imports zero Qt."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from floorplanner.design.model import Design

pytestmark = pytest.mark.io

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
# planc1.v5.json is schema-valid (pinned at P0.7) and exercises shapes the other
# two don't -- the faithful migration, with wall: null open outline edges and a
# provenance block. Its referential invariants fail on purpose; that is a check()
# concern, not a round-trip one -- from_dict/to_dict must reproduce it verbatim.
DESIGN_FIXTURES = ["symmetricP1.json", "site_demo.json", "planc1.v5.json"]


@pytest.mark.parametrize("name", DESIGN_FIXTURES)
def test_round_trip_is_byte_identical(name):
    doc = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    rt = Design.from_dict(doc).to_dict()
    assert rt == doc                                   # same keys + values
    # and byte-identical when serialized in the same field order (stable emit):
    # this is what distinguishes "keeps a present null" from "omits an absent key"
    assert json.dumps(rt, ensure_ascii=False) == json.dumps(doc, ensure_ascii=False)


def test_roofs_round_trip_byte_identical():
    """0139-ruling.md R1: `roofs` is additive and version-6-only in intent,
    but no DESIGN_FIXTURES corpus file carries one yet (they all predate
    it), so this is the direct receipt rather than a corpus pass-through.
    A version-5 document with `roofs` present is still a document
    `Design` must round-trip faithfully -- the model layer does not
    enforce the version gate, the schema does (see test_schema.py)."""
    doc = {
        "format": "floorplanner-design", "version": 6, "units": "inches",
        "levels": [{"id": "L1", "name": "Main"}],
        "vertices": [], "walls": [], "rooms": [],
        "roofs": [{
            "id": "r1", "level": "L1",
            "ridge": [[0.0, 0.0], [240.0, 0.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 132.0,
            "overhang_in": 12.0, "gable": [True, True],
        }],
    }
    rt = Design.from_dict(doc).to_dict()
    assert rt == doc
    assert json.dumps(rt, ensure_ascii=False) == json.dumps(doc, ensure_ascii=False)


def test_roof_marker_end_round_trips_byte_identical():
    """R2b (0140-ruling.md): `marker_end` is additive over R1's own roof
    record -- present-and-set round-trips exactly, same discipline as
    every other optional-with-a-schema-default field."""
    doc = {
        "format": "floorplanner-design", "version": 6, "units": "inches",
        "levels": [{"id": "L1", "name": "Main"}],
        "vertices": [], "walls": [], "rooms": [],
        "roofs": [{
            "id": "rf1", "level": "L1",
            "ridge": [[0.0, 0.0], [240.0, 0.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 132.0,
            "overhang_in": 12.0, "gable": [True, True], "marker_end": 0,
        }],
    }
    rt = Design.from_dict(doc).to_dict()
    assert rt == doc


def test_roof_marker_end_absent_stays_absent():
    """A roof record written before R2b (R1/R2's own tests, real fixtures)
    has no `marker_end` key at all -- it must stay absent through the
    model layer, not silently materialise a default. The schema default
    (1) is an application/schema-level fallback (bridge.py, design-schema
    .v5.json), not something `Design` invents on the field's behalf."""
    doc = {
        "format": "floorplanner-design", "version": 6, "units": "inches",
        "levels": [{"id": "L1", "name": "Main"}],
        "vertices": [], "walls": [], "rooms": [],
        "roofs": [{
            "id": "rf1", "level": "L1",
            "ridge": [[0.0, 0.0], [240.0, 0.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 132.0,
        }],
    }
    rt = Design.from_dict(doc).to_dict()
    assert "marker_end" not in rt["roofs"][0]
    assert rt == doc


def test_roofs_absent_stays_absent_not_an_empty_list():
    """The same present-vs-absent distinction every other block already
    gets: a version-5 document with no `roofs` key at all must round-trip
    with `roofs` still absent, not silently materialise `"roofs": []`."""
    doc = {
        "format": "floorplanner-design", "version": 5, "units": "inches",
        "levels": [{"id": "L1", "name": "Main"}],
        "vertices": [], "walls": [], "rooms": [],
    }
    rt = Design.from_dict(doc).to_dict()
    assert "roofs" not in rt
    assert rt == doc


def test_present_null_vs_absent_are_distinguished():
    # the crux of byte-identity: a free wall keeps `left: null` (present), while a
    # room with no area_accounting keeps that key ABSENT -- not emitted as null
    doc = json.loads((EXAMPLES / "symmetricP1.json").read_text(encoding="utf-8"))
    d = Design.from_dict(doc)
    free_wall = next(w for w in d.walls if w.right is None or w.left is None)
    rt_wall = free_wall.to_dict()
    assert "left" in rt_wall and "right" in rt_wall     # present, even as null
    plain_room = next(r for r in d.rooms if "area_accounting" not in r.to_dict())
    assert "area_accounting" not in plain_room.to_dict()   # absent, not null


def test_model_imports_zero_qt():
    # Import model.py IN ISOLATION (not via floorplanner/__init__, which star-
    # imports the Qt scene layer) and assert it pulled in no PyQt6 module. If
    # model.py ever imports a floorplanner submodule or Qt, this fails.
    model_py = ROOT / "floorplanner" / "design" / "model.py"
    code = (
        "import sys, importlib.util as u;"
        f"spec=u.spec_from_file_location('_isolated_model', r'{model_py}');"
        "m=u.module_from_spec(spec); spec.loader.exec_module(m);"
        "qt=[n for n in sys.modules if n=='PyQt6' or n.startswith('PyQt6.')];"
        "assert not qt, 'model imported Qt: '+repr(qt);"
        "assert m.Design is not None"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout
