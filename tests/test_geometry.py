"""Pure geometry / parsing helpers -- no Qt scene needed, so these are fast."""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.geometry


@pytest.mark.parametrize("text,inches", [
    (12, 144), (12.5, 150), ("12", 144), ("12'", 144),
    ("12'6", 150), ("12'6\"", 150), ("12'-6\"", 150),
    ("30\"", 30), ("0", 0),
])
def test_parse_feet_ok(fp, text, inches):
    assert fp.parse_feet(text) == pytest.approx(inches)


@pytest.mark.parametrize("bad", ["", "abc", "12x", "'", "12''"])
def test_parse_feet_rejects_junk(fp, bad):
    with pytest.raises(ValueError):
        fp.parse_feet(bad)


@pytest.mark.parametrize("code,wh", [
    ("3280", (32, 80)), ("10884", (108, 84)), ("192144", (192, 144)),
])
def test_parse_wwhh_ok(fp, code, wh):
    assert fp.parse_wwhh(code) == pytest.approx(wh)


@pytest.mark.parametrize("bad", ["32", "3280a", "0480", "3204", ""])
def test_parse_wwhh_rejects_junk(fp, bad):
    with pytest.raises(ValueError):
        fp.parse_wwhh(bad)


def test_fmt_ftin(fp):
    assert fp.fmt_ftin(144) == "12'-0\""
    assert fp.fmt_ftin(30.5) == "2'-6 1/2\""
    assert fp.fmt_ftin(0) == "0'-0\""


@pytest.mark.parametrize("inches,expect", [
    (0, "0.00"), (120, "10.00"), (148.14, "12.34"), (6, "0.50"),
    (1500, "125.00"), (1700.04, "141.67"),
])
def test_fmt_ft2(fp, inches, expect):
    """Decimal feet, FIXED at 2 decimals -- 0065-ruling.md sec4: resolution
    must not depend on magnitude, unlike the significant-figure format this
    replaced (which gave only 1ft resolution above 100ft; the last case
    here, 141.67ft, is past that threshold and still resolves to 2 places).
    No unit suffix -- callers append one, since a coordinate pair wants it
    once, not per axis."""
    assert fp.fmt_ft2(inches) == expect


@pytest.mark.parametrize("p1,p2,expect", [
    ((0, 0), (100, 0), 0.0),          # due east
    ((0, 0), (0, 100), 90.0),         # due north
    ((0, 0), (-100, 0), 180.0),       # due west
    ((0, 0), (0, -100), 270.0),       # due south -- NOT folded onto 90
    ((0, 0), (100, 100), 45.0),
])
def test_heading_deg_exact_cardinals_and_a_diagonal(fp, p1, p2, expect):
    h = fp.heading_deg(QPointF(*p1), QPointF(*p2))
    assert h == pytest.approx(expect, abs=1e-9)


def test_heading_deg_is_none_for_a_degenerate_pair(fp):
    p = QPointF(5, 5)
    assert fp.heading_deg(p, p) is None


def test_grid_snap(fp):
    p = fp.grid_snap(QPointF(23, 7), step=12)
    assert (p.x(), p.y()) == (24, 12)


def test_wall_snap_len(fp):
    fp.SETTINGS["wall_snap_in"] = 6
    assert fp.wall_snap_len(16) == 18
    assert fp.wall_snap_len(11) == 12
