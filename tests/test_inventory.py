"""Inventory tables: furnishing/house/total row builders, interior-vs-yard
classification, CSV export, and the InventoryDialog widget."""

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.furnishings


@pytest.fixture
def furnished_room(fp, scene, make_room, first_furnishing):
    """A 10' x 10' room with two furnishings inside and one out in the yard.
    Returns (scene, room)."""
    room = make_room(scene, 0, 0, 120, 120, "Living")
    kind = first_furnishing
    scene.addItem(fp.FurnishingItem(kind, QPointF(40, 40), 0))   # inside
    scene.addItem(fp.FurnishingItem(kind, QPointF(80, 80), 0))   # inside
    scene.addItem(fp.FurnishingItem(kind, QPointF(400, 400), 0))  # yard
    return scene, room


def test_classify_interior_vs_yard(fp, furnished_room):
    scene, _ = furnished_room
    interior, yard = fp.classify_furnishings(scene)
    assert len(interior) == 2
    assert len(yard) == 1


def test_cars_and_garage_items_are_yard(fp, scene, make_room,
                                        first_furnishing):
    make_room(scene, 0, 0, 120, 120, "Living")          # ordinary room
    garage = make_room(scene, 200, 0, 120, 120, "Garage")
    garage.properties["room_type"] = "Garage"
    # a car inside the living room -> yard (garage-category item)
    scene.addItem(fp.FurnishingItem("suv", QPointF(60, 60), 0))
    # a sofa inside the garage room -> yard (garage room)
    scene.addItem(fp.FurnishingItem(first_furnishing, QPointF(260, 60), 0))
    interior, yard = fp.classify_furnishings(scene)
    assert interior == []
    assert len(yard) == 2


def test_furnishing_rows_aggregate_with_total(fp, furnished_room):
    scene, _ = furnished_room
    interior, _ = fp.classify_furnishings(scene)
    rows, qty, cost = fp.furnishing_inventory_rows(interior)
    assert qty == 2
    assert rows[-1][0] == "TOTAL"
    assert rows[-1][1] == "2"
    # two of the same kind aggregate into a single line + the TOTAL row
    assert len(rows) == 2


def test_furnishing_rows_use_price(fp, scene, first_furnishing):
    it = fp.FurnishingItem(first_furnishing, QPointF(10, 10), 0)
    it.price = 250.0
    scene.addItem(it)
    rows, qty, cost = fp.furnishing_inventory_rows([it])
    assert cost == 250.0
    assert "$250" in rows[0][2]


def test_house_rows_list_rooms_and_walls(fp, furnished_room):
    scene, room = furnished_room
    rows, sqft = fp.house_inventory_rows(scene)
    assert sqft == pytest.approx(100.0, abs=0.5)
    assert any(r[0] == room.name for r in rows)
    assert any("wall" in r[0].lower() for r in rows)


def test_total_rows_have_grand_total(fp, furnished_room):
    scene, _ = furnished_room
    fp.SETTINGS["cost_per_sqft"] = 100.0
    rows = fp.total_inventory_rows(scene)
    grand = [r for r in rows if r[0] == "Grand total"]
    assert grand, "missing grand-total row"
    # 100 sq ft * $100 = $10,000 building (furnishings here are unpriced)
    assert "$10,000" in grand[0][3]


def test_inventory_tsv_is_tab_separated(fp):
    tsv = fp.inventory_tsv(["A", "B"], [["x", "$1,500"], ["y", "z"]])
    lines = tsv.splitlines()
    assert lines[0] == "A\tB"
    # commas are kept verbatim (no CSV quoting); columns split on tabs
    assert lines[1] == "x\t$1,500"


def test_inventory_dialog_table_and_copy(fp, qapp):
    rows = [["Sofa", "1", "$900", "$900"], ["TOTAL", "1", "", "$900"]]
    dlg = fp.InventoryDialog("T", fp.FURN_INV_HEADERS, rows)
    assert dlg.table.rowCount() == 2
    assert dlg.table.columnCount() == 4
    assert dlg.table.item(0, 0).text() == "Sofa"
    # TOTAL row is bold
    assert dlg.table.item(1, 0).font().bold()
    dlg._copy()
    from PyQt6.QtWidgets import QApplication
    clip = QApplication.clipboard().text()
    assert clip.splitlines()[0] == "Item\tQuantity\tUnit price\tLine total"
    assert "Sofa\t1\t$900\t$900" in clip


def test_room_inventory_dialog_builds_table(fp, qapp, scene, make_room):
    room = make_room(scene, 0, 0, 120, 120, "Den")
    dlg = fp.RoomInventoryDialog(room)
    assert dlg.table.rowCount() > 0
    assert dlg.headers == ["Field", "Value"]
