"""D70 — the asset generator refuses to write a malformed SVG.

`_gen_assets.py` writes the artwork; nothing downstream validates it, and the
failure it produced was SILENT: a body passed as a bare string is joined
character by character, the generator reports success, and only the plan SYMBOL
is blank because only it reads the SVG. The catalog, the footprint and the 3D
mesh all read the manifest and look fine.

These tests exercise `svg_error` directly rather than shelling out to the
generator: the module writes assets at import, so importing it in-process would
regenerate the tree as a side effect of running the suite.
"""
from pathlib import Path

import pytest

pytestmark = pytest.mark.io

GEN = Path(__file__).resolve().parent.parent / "_gen_assets.py"


def _svg_error():
    """`svg_error` alone, without executing the module's write-everything body.

    The generator has no `if __name__ == "__main__"` guard -- it does its work
    at import -- so the function is compiled out of the source rather than
    imported. Restating it here instead would be a second definition of the
    predicate under test, which the working agreement forbids.
    """
    src = GEN.read_text(encoding="utf-8")
    start = src.index("def svg_error(")
    end = src.index("\ndef ", start + 1)
    ns = {}
    exec(compile("import xml.etree.ElementTree as ET\n" + src[start:end],
                 str(GEN), "exec"), ns)          # noqa: S102 - the code under test
    return ns["svg_error"]


def test_a_well_formed_symbol_passes():
    err = _svg_error()('<svg xmlns="http://www.w3.org/2000/svg" '
                       'viewBox="0 0 30 18"><rect x="1" y="1" width="8" '
                       'height="8"/></svg>')
    assert err is None


def test_the_bare_string_body_is_caught():
    """D70's exact cause: `"\n".join(body)` over a str joins CHARACTERS.

    Reproduced the way the generator would produce it, not by hand-writing
    broken XML -- otherwise the test pins a straw man rather than the defect.
    """
    body = '<rect x="1" y="1" width="28" height="16"/>'      # a str, not a list
    text = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 18">\n'
            + "\n".join(body) + "\n</svg>\n")
    assert "\n<\nr\ne\nc\nt" in text, "precondition: the join must have split it"
    assert _svg_error()(text) is not None, \
        "a character-per-line SVG must be rejected"


def test_a_truncated_element_is_caught():
    text = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 18">\n'
            '<rect x="1" y="1" width="28"\n</svg>\n')
    assert _svg_error()(text) is not None


def test_the_generator_refuses_rather_than_warning():
    """The ruling is REFUSE, not warn — so both writers must raise SystemExit
    and neither may write before validating. Asserted on the source, because
    running the generator would rewrite the asset tree."""
    src = GEN.read_text(encoding="utf-8")
    assert src.count("svg_error(") >= 3, \
        "svg_error must be called by both writers, not just defined"
    for gate in ("assets not written --", "icons not written --"):
        i = src.index(gate)
        assert "raise SystemExit(" in src[max(0, i - 200):i], \
            f"{gate!r} must be a refusal, not a warning"
    # the furnishing writer must validate BEFORE it writes
    assert src.index("if _malformed:") < src.index("for _path, _text in _pending:")
