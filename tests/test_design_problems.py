"""The "Malformed design file" report takes you there (Patrick, 2026-10-07:
*"I want to be able to click on the error items and have the tool take me
to the point on the design and zoom in"*).

`design.locate` resolves a `check()` message's subjects against the opened
document, Qt-free; `problems.DesignProblemsDialog` lists every violation
and, on selection, has the window switch level and fit the view there.
"""
import copy
import json
import pathlib

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design import validate
from floorplanner.design.locate import Spot, locate, subjects

pytestmark = pytest.mark.io

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _doc():
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0, "height_in": 96.0},
                   {"id": "L2", "name": "upper", "elevation_in": 100.0, "height_in": 96.0}],
        "vertices": [
            {"id": "v1", "level": "L1", "x": 0.0, "y": 0.0},
            {"id": "v2", "level": "L1", "x": 240.0, "y": 0.0},
            {"id": "v3", "level": "L1", "x": 240.0, "y": 180.0},
            {"id": "v4", "level": "L1", "x": 0.0, "y": 180.0},
            {"id": "v5", "level": "L2", "x": 600.0, "y": 600.0},
            {"id": "v6", "level": "L2", "x": 840.0, "y": 600.0},
        ],
        "walls": [
            {"id": "w1", "left": "r1", "right": None, "level": "L1", "v1": "v1", "v2": "v2", "type": "exterior",
             "openings": [{"id": "o1", "kind": "door", "code": "3680",
                           "anchor": {"from": "v1", "offset_in": 100.0}},
                          {"id": "o2", "kind": "window", "code": "2440",
                           "anchor": {"from": "v2", "offset_in": 12.0}}]},
            {"id": "w2", "left": "r1", "right": None, "level": "L1", "v1": "v2", "v2": "v3", "type": "exterior"},
            {"id": "w3", "left": "r1", "right": None, "level": "L1", "v1": "v3", "v2": "v4", "type": "exterior"},
            {"id": "w4", "left": "r1", "right": None, "level": "L1", "v1": "v4", "v2": "v1", "type": "exterior"},
            {"id": "w5", "level": "L2", "v1": "v5", "v2": "v6", "type": "exterior"},
        ],
        "rooms": [{"id": "r1", "level": "L1", "name": "Den", "category": "interior",
                   "placement": {"state": "placed", "rotation": 0.0, "extracted_from": None},
                   "outline": [{"v": "v1", "wall": "w1"}, {"v": "v2", "wall": "w2"},
                               {"v": "v3", "wall": "w3"}, {"v": "v4", "wall": "w4"}]}],
        "furnishings": [{"id": "f1", "level": "L1", "kind": "sofa", "pos": [120.0, 90.0]}],
        "groups": [], "roofs": [],
    }


# --------------------------------------------------------------------------
# locate -- Qt-free
# --------------------------------------------------------------------------
def test_subjects_are_the_validators_own_id_rule():
    msg = "I6  wall w89 sides ['r20'] != outline users ['r13', 'r20']"
    assert subjects(msg) == validate._invariant_key(msg)[1] == ("r13", "r20", "w89")
    assert subjects("I11 rooms 'Kitchen' and 'Hall' overlap") == ("Hall", "Kitchen")


@pytest.mark.parametrize("message, rect, level", [
    ("I3  wall w2 degenerate", (240.0, 0.0, 240.0, 180.0), "default"),
    ("I10 orphan vertex v3", (240.0, 180.0, 240.0, 180.0), "default"),
    # from=v1, offset 100, a 36in door: 100..136 along w1
    ("I7  opening o1 runs off wall w1 (x)", (0.0, 0.0, 240.0, 0.0), "default"),
    ("I7  openings o1/o2 overlap on w1", (0.0, 0.0, 240.0, 0.0), "default"),
    ("I5  room r1 -> missing vertex v9", (0.0, 0.0, 240.0, 180.0), "default"),
    ("I11 rooms 'Den' and 'Nowhere' overlap", (0.0, 0.0, 240.0, 180.0), "default"),
    ("I8  furnishing f1 -> missing room r9", (120.0, 90.0, 120.0, 90.0), "default"),
    ("I3  wall w5 degenerate", (600.0, 600.0, 840.0, 600.0), "upper"),
])
def test_a_message_is_placed_on_the_design_it_names(message, rect, level):
    spot = locate(_doc(), message)
    assert spot is not None
    assert spot.rect == pytest.approx(rect) and spot.level == level


def test_an_opening_alone_is_placed_on_its_span_not_the_whole_wall():
    spot = locate(_doc(), "I7  opening o1 is odd")
    assert spot.rect == pytest.approx((100.0, 0.0, 136.0, 0.0))
    spot = locate(_doc(), "I7  opening o2 is odd")             # from v2: 12in in, 24 wide
    assert spot.rect == pytest.approx((240.0 - 12.0 - 24.0, 0.0, 240.0 - 12.0, 0.0))


def test_what_the_document_does_not_hold_is_reported_not_guessed():
    spot = locate(_doc(), "I5  room r1 -> missing vertex v9")
    assert spot.found == ("r1",) and spot.missing == ("v9",)
    assert locate(_doc(), "I2  vertex v99 -> unknown level") is None
    assert locate({}, "I6  wall w1 sides") is None


def test_locate_is_qt_free():
    """It answers from the document dict alone, like the rest of `design/`."""
    import floorplanner.design.locate as mod
    src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
    assert "PyQt6" not in src and "Qt" not in src.replace("Qt-free", "")


# --------------------------------------------------------------------------
# the window goes there
# --------------------------------------------------------------------------
def _visible_rect(win):
    return win.view.mapToScene(win.view.viewport().rect()).boundingRect()


def test_zoom_to_spot_switches_level_and_fits_the_view(fp, win):
    win.prepare_headless()
    win.load_data(_doc())
    assert win.active_floor == "default"
    rect = win.zoom_to_spot(Spot("upper", (600.0, 600.0, 840.0, 600.0), ("w5",), ()))
    assert win.active_floor == "upper"
    vis = _visible_rect(win)
    assert vis.contains(QPointF(600.0, 600.0)) and vis.contains(QPointF(840.0, 600.0))
    assert rect.width() >= 240.0 and vis.width() < 2000.0, "fitted, not the whole canvas"
    # a single vertex is not fitted to a point: the view shows at least MIN_VIEW_IN
    from floorplanner.problems import MIN_VIEW_IN
    win.zoom_to_spot(Spot("default", (240.0, 180.0, 240.0, 180.0), ("v3",), ()))
    vis = _visible_rect(win)
    assert win.active_floor == "default"
    assert vis.contains(QPointF(240.0, 180.0))
    assert min(vis.width(), vis.height()) >= MIN_VIEW_IN


def test_opening_a_malformed_v5_file_lists_every_violation_and_each_row_goes_there(fp, win):
    """The report itself: a v5 file with two violations opens unchanged, the
    dialog lists both (not three run into one sentence), and selecting a
    row fits the view to the place it names."""
    doc = _doc()
    doc["walls"][0]["openings"][1]["anchor"] = {"from": "v1", "offset_in": 110.0}   # o2 overlaps o1
    doc["vertices"].append({"id": "v7", "level": "L2", "x": 700.0, "y": 700.0})     # orphan
    errs = validate.check(doc, deep=True, boundary=True)
    assert any(e.startswith("I7") for e in errs) and any(e.startswith("I10") for e in errs)
    win.prepare_headless()
    win.resize(1200, 800)
    win.open_document(copy.deepcopy(doc), interactive=True)
    dlg = win._problems_dialog
    assert dlg is not None and dlg.isVisible() and not dlg.isModal()
    assert dlg.messages == errs
    assert win.statusBar().currentMessage().startswith("This v5 file reports")
    row = next(i for i, m in enumerate(dlg.messages) if m.startswith("I10"))
    dlg.list.setCurrentRow(row)
    assert win.active_floor == "upper"
    assert _visible_rect(win).contains(QPointF(700.0, 700.0))
    assert "v7" in dlg.where.text() and "upper" in dlg.where.text()
    row = next(i for i, m in enumerate(dlg.messages) if m.startswith("I7"))
    dlg.list.setCurrentRow(row)
    assert win.active_floor == "default"
    assert _visible_rect(win).contains(QPointF(118.0, 0.0))
    dlg.close()


def test_a_clean_v5_file_opens_with_no_dialog(fp, win):
    win.prepare_headless()
    win.open_document(_doc(), interactive=True)
    assert getattr(win, "_problems_dialog", None) is None


def test_the_real_malformed_fixture_places_its_violation(fp, win):
    """`fixtures/wiscaway-2level-stacked-floor.json` is frozen with one real
    violation (fixtures/README.md: `I6 wall w90 ...`); the report places it."""
    doc = json.loads((ROOT / "fixtures" / "wiscaway-2level-stacked-floor.json").read_text(encoding="utf-8"))
    errs = validate.check(doc, deep=True, boundary=True)
    assert errs and errs[0].startswith("I6  wall w90")
    spot = locate(doc, errs[0])
    assert spot is not None and "w90" in spot.found and spot.missing == ()
    win.prepare_headless()
    win.open_document(doc, interactive=True)
    dlg = win._problems_dialog
    dlg.list.setCurrentRow(0)
    x0, y0, x1, y1 = spot.rect
    assert _visible_rect(win).contains(QPointF((x0 + x1) / 2, (y0 + y1) / 2))
    dlg.close()
