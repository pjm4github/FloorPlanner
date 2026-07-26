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
