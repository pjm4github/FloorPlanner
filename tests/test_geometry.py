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


def test_grid_snap(fp):
    p = fp.grid_snap(QPointF(23, 7), step=12)
    assert (p.x(), p.y()) == (24, 12)


def test_wall_snap_len(fp):
    fp.SETTINGS["wall_snap_in"] = 6
    assert fp.wall_snap_len(16) == 18
    assert fp.wall_snap_len(11) == 12
