"""Furnishing catalog integrity and true-scale placement."""
import pytest
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

pytestmark = pytest.mark.furnishings


def test_catalog_nonempty(fp):
    assert len(fp.furnishing_catalog()) > 0


def test_specs_have_real_dimensions(fp):
    for s in fp.furnishing_catalog():
        assert s["width_in"] > 0 and s["depth_in"] > 0
        assert s["id"] and s["file"]


def test_item_placed_at_true_scale(fp, scene, first_furnishing):
    spec = fp.furnishing_spec(first_furnishing)
    it = fp.FurnishingItem(first_furnishing, QPointF(100, 100), 0)
    scene.addItem(it)
    assert it.w == pytest.approx(spec["width_in"])
    assert it.d == pytest.approx(spec["depth_in"])


def test_unknown_furnishing_falls_back(fp, scene):
    it = fp.FurnishingItem("does_not_exist_xyz", QPointF(0, 0), 0)
    scene.addItem(it)
    assert it.w > 0 and it.d > 0          # fallback footprint, never crashes


def test_groups_have_all_section(fp):
    groups = fp.furnishing_groups()
    names = [g["name"] for g in groups]
    assert "All" in names
    all_specs = next(g["specs"] for g in groups if g["name"] == "All")
    assert len(all_specs) == len(fp.furnishing_catalog())


# --------------------------------------------------------------------------
# D71 -- renderability, checked where Qt is already paid for
# --------------------------------------------------------------------------
# The generator (_gen_assets.py) stays Qt-free and only proves an SVG is
# WELL-FORMED XML (D70). This suite already builds a QApplication, so the
# stronger check -- does the symbol actually PAINT ANYTHING -- belongs here.
def _paints_something(renderer, side=48):
    """True if `renderer` draws at least one non-transparent pixel.

    `sip.voidptr.__getitem__` returns a length-1 `bytes` for each index, which
    is TRUTHY REGARDLESS OF VALUE (`bool(b'\\x00') is True`) -- indexing it
    directly made an earlier draft of this function report every pixel as
    painted, including a genuinely blank image. `bytes(ptr)` first converts to
    real `int`s. THE POSITIVE CONTROL BELOW CAUGHT THIS before it could make
    the real test vacuous."""
    img = QImage(side, side, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    painter = QPainter(img)
    renderer.render(painter, QRectF(0, 0, side, side))
    painter.end()
    ptr = img.bits()
    ptr.setsize(img.sizeInBytes())
    buf = bytes(ptr)
    # ARGB32 alpha is the high byte on little-endian (BGRA byte order); every
    # 4th byte starting at offset 3 is alpha -- confirmed against a known
    # opaque and a known transparent fill, not assumed from documentation.
    return any(buf[i] for i in range(3, len(buf), 4))


def test_the_positive_control__QSvgRenderer_isValid_is_NOT_ENOUGH(tmp_path):
    """MUST FAIL BEFORE THE REAL TEST IS TRUSTED (WORKING_AGREEMENT: every
    instrument is validated against a case known to be non-zero before its
    zero is believed).

    D71 was filed proposing `QSvgRenderer(...).isValid()` as the check that
    catches "well-formed XML that draws nothing" -- the class D70's plain XML
    parse structurally cannot see. MEASURED, and the premise was wrong:
    `isValid()` returns True for an SVG with no children at all, and for one
    whose only element is a tag Qt does not recognise. It only re-detects
    XML that fails to PARSE -- exactly what `svg_error` in the generator
    already refuses before writing, so using `isValid()` alone would make
    this test a second copy of D70's check, not new coverage.

    So the instrument is RENDER TO A BUFFER AND LOOK FOR A PAINTED PIXEL, not
    `isValid()`. This positive control proves it catches what `isValid()`
    misses, on two synthetic cases -- an empty `<svg/>` and one whose only
    child is a tag Qt's SVG module does not implement."""
    blanks = {
        "empty": '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 10 10"></svg>',
        "unrecognised tag only": '<svg xmlns="http://www.w3.org/2000/svg" '
                                 'viewBox="0 0 10 10"><notrealtag x="1"/></svg>',
    }
    for name, text in blanks.items():
        p = tmp_path / f"{name.replace(' ', '_')}.svg"
        p.write_text(text, encoding="utf-8")
        r = QSvgRenderer(str(p))
        assert r.isValid(), (
            f"PRECONDITION for {name}: must be well-formed, or this case "
            f"tests D70's check instead of D71's")
        assert not _paints_something(r), (
            f"{name}: isValid() alone would have called this fine -- the "
            f"render-and-look check is what actually catches it")

    # and the control's other arm: a real symbol must still pass, or the
    # check is too strict to ship
    real = tmp_path / "real.svg"
    real.write_text('<svg xmlns="http://www.w3.org/2000/svg" '
                    'viewBox="0 0 10 10"><rect x="1" y="1" width="5" '
                    'height="5"/></svg>', encoding="utf-8")
    assert _paints_something(QSvgRenderer(str(real)))


def test_every_catalog_symbol_renders_something(fp):
    """THE CHECK ITSELF, through the PRODUCTION accessor -- `furnishing_renderer`,
    not a `QSvgRenderer` built inline -- so this pins the file resolution and
    the shared-renderer cache the app actually uses, per D71's ruling.

    It would have caught D70's instance (a corrupt SVG made `isValid()` False
    too), and it catches the class D70's generator-side check structurally
    cannot: a symbol that is well-formed and blank."""
    catalog = fp.furnishing_catalog()
    assert len(catalog) >= 90, "PRECONDITION: run over the real catalog, not a stub"
    blank = []
    for spec in catalog:
        r = fp.furnishing_renderer(spec["id"])
        assert r is not None, f"{spec['id']}: no valid renderer at all"
        if not _paints_something(r):
            blank.append(spec["id"])
    assert not blank, f"symbol(s) that parse but draw nothing: {blank}"
