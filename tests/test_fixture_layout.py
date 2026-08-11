"""The three-tier plan layout, enforced rather than asserted.

    examples/           the frozen CLEAN corpus. Nothing imperfect enters it.
    fixtures/           CHARACTERISED failures, each named in fixtures/README.md
    fixtures/incoming/  UNCHARACTERISED intake. No test may reach it.

**A contract nobody checked is a comment.** `fixtures/incoming/README.md` says
no test may reference a file there and no parametrized test may sweep the
directory. That promise is worth exactly what enforces it, so this file is the
enforcement — and its central test is a POSITIVE CONTROL: it puts a deliberately
invalid plan in `incoming/` and fails if any corpus collector picks it up.

Why it matters, from the record: `tests/test_schema.py` parametrizes over a
filesystem glob, so a plan dropped in `examples/` changes the collected count
and, if it trips an invariant, turns the gate red and — through the commit hook
— blocks every commit in the repository. That is D51, and it has happened twice
(`fragment2room.json` 2026-08-08, `wiscaway2026-08-09R.json` 2026-08-09).
"""
import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.io

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "fixtures"
INCOMING = FIXTURES / "incoming"

# a plan that is invalid every way a plan can be: it names vertices that do not
# exist, so both the JSON Schema and the referential invariants have something
# to complain about. If a collector sweeps it up, something goes red.
BROKEN = {
    "format": "floorplanner-design",
    "version": 5,
    "units": "in",
    "levels": [{"id": "default", "name": "Default", "kind": "floor",
                "elevation_in": 0, "height_in": 96, "reference": None}],
    "vertices": [],
    "walls": [{"id": "w1", "level": "default", "v1": "vNOPE", "v2": "vGONE",
               "type": "interior", "thickness_in": 4.5, "openings": []}],
    "rooms": [], "furnishings": [], "groups": [],
    "settings": {}, "provenance": {},
}


def _collector():
    """`test_schema`'s own file discovery, loaded from source.

    Imported rather than re-implemented: the thing under test is what the
    REAL collector sweeps, and a copy of its glob would be a second definition
    that could drift away from the one that actually runs."""
    spec = importlib.util.spec_from_file_location(
        "_schema_probe", Path(__file__).with_name("test_schema.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_intake_directory_exists_with_its_contract():
    assert INCOMING.is_dir(), "fixtures/incoming/ is missing"
    readme = (INCOMING / "README.md").read_text(encoding="utf-8")
    assert "UNCHARACTERISED" in readme
    assert "No test may reference a file in" in readme


def test_no_corpus_collector_reaches_the_intake_directory():
    """THE POSITIVE CONTROL. A deliberately invalid plan is placed in
    `incoming/` and the real collector is re-run over it.

    The control is what makes this test worth having: asserting that a glob
    scoped to `examples/` does not see `fixtures/` would pass whether or not
    the directory existed and whether or not anything was in it. Putting a
    plan there that MUST be reported if it is seen turns a structural claim
    into a measured one.
    """
    INCOMING.mkdir(parents=True, exist_ok=True)
    planted = INCOMING / "_control_broken_plan.json"
    planted.write_text(json.dumps(BROKEN), encoding="utf-8")
    try:
        mod = _collector()
        swept = [p for p in mod.DESIGN_FILES]
        # the collector must have found the real corpus -- otherwise "it did
        # not pick up my file" is true of an empty sweep and means nothing
        assert len(swept) >= 3, f"collector found almost nothing: {swept}"
        assert planted.resolve() not in {p.resolve() for p in swept}
        assert not any(INCOMING in p.resolve().parents for p in swept)
        assert not any(FIXTURES in p.resolve().parents for p in swept)
        for p in swept:
            assert p.resolve().parent == EXAMPLES.resolve(), (
                f"a corpus collector reached outside examples/: {p}")
    finally:
        planted.unlink(missing_ok=True)


def test_no_test_references_a_file_in_the_intake_directory():
    """The other half of the contract, and it is a source question.

    `incoming/` may hold anything at any time, so a test naming a file there
    is a test that breaks when Patrick tidies up."""
    offenders = []
    for path in sorted(Path(__file__).parent.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        if "incoming" in text:
            offenders.append(path.name)
    assert offenders == [], (
        f"these tests reference fixtures/incoming/: {offenders}")
