"""D85 -- a roof's clickable shape used to cover only the ridge segment
itself, never the dashed eave/gable lines paint() also draws. For a roof
picked with a small span (or overhang), or a short ridge, most of what is
actually ON SCREEN sat outside `RoofItem.shape()` entirely -- reported live:
"had a little tiny roof (which I couldn't delete, by the way)", sharpened
on a second report with a screenshot and his own diagnosis: "I think the
dotted roof edges need to be selectable so that I can select the roof."
Fixed exactly that way -- `shape()`'s stroke now follows every line segment
paint() draws (ridge, both eaves, each gable end that is a gable), not the
ridge alone.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.gui


def _hits(win, pt: QPointF):
    return {type(it).__name__ for it in win.scene.items(pt)}


def test_a_thin_span_roof_is_still_selectable_on_its_eave_line(fp, win):
    """A long ridge, a SMALL span -- the reported shape: a tall, thin
    dashed sliver. Clicking the ridge's own centreline still works (it
    always did), but clicking squarely on one of the two eave lines --
    most of what actually reads on screen for a thin roof like this --
    must ALSO hit the roof now."""
    win.prepare_headless()
    ridge = RoofItem(QPointF(100, 0), QPointF(100, 400), span_in=6.0,
                     overhang_in=0.0)
    win.scene.addItem(ridge)

    assert "RoofItem" in _hits(win, QPointF(100, 200)), \
        "precondition: the ridge's own centreline must still be clickable"
    assert "RoofItem" in _hits(win, QPointF(94, 200)), \
        "the near eave line (span=6in to one side) is not selectable"
    assert "RoofItem" in _hits(win, QPointF(106, 200)), \
        "the far eave line (span=6in to the other side) is not selectable"


def test_a_short_ridge_is_still_selectable_on_its_eave_line(fp, win):
    """The other axis: a long span, a nearly-zero-length ridge -- his
    ORIGINAL report ("a little tiny roof")."""
    win.prepare_headless()
    ridge = RoofItem(QPointF(100, 100), QPointF(101, 100), span_in=150.0,
                     overhang_in=0.0)
    win.scene.addItem(ridge)

    assert "RoofItem" in _hits(win, QPointF(100.5, 100)), \
        "precondition: the (nearly-point) ridge itself must still be clickable"
    assert "RoofItem" in _hits(win, QPointF(100.5, -50)), \
        "the near eave line (span=150in) is not selectable"
    assert "RoofItem" in _hits(win, QPointF(100.5, 250)), \
        "the far eave line (span=150in) is not selectable"


def test_a_gable_end_line_is_selectable(fp, win):
    """The vertical (in plan) gable-end line at each ridge end -- drawn
    whenever that end's `gable` flag is true (the default, and the only
    state reachable through the UI today) -- must be clickable too, not
    just the two eave lines it connects."""
    win.prepare_headless()
    ridge = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=50.0,
                     overhang_in=0.0, gable=[True, True])
    win.scene.addItem(ridge)

    # the gable line at the p1 end runs from (0, -50) to (0, 50)
    assert "RoofItem" in _hits(win, QPointF(0, 0)), \
        "the gable-end line is not selectable"


def test_deleting_a_thin_roof_via_its_eave_line_click_works(fp, win):
    """The end-to-end shape of his report: select (via the part of the
    roof that actually reads on screen) then delete, and the roof is
    really gone."""
    win.prepare_headless()
    ridge = RoofItem(QPointF(100, 0), QPointF(100, 400), span_in=6.0,
                     overhang_in=0.0)
    win.scene.addItem(ridge)

    hit = next(it for it in win.scene.items(QPointF(94, 200))
              if isinstance(it, RoofItem))
    hit.setSelected(True)
    assert hit.scene() is not None
    win.scene.removeItem(hit)
    assert not any(isinstance(it, RoofItem) for it in win.scene.items())
