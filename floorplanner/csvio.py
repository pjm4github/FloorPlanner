"""Room CSV import / export (P2.5).

Lifted VERBATIM out of `MainWindow` as a mixin, so `win._import_rooms(...)` --
which the tests call directly -- resolves unchanged.
"""
import csv

from PyQt6 import sip  # noqa: F401
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

try:
    from PyQt6.QtSvg import QSvgGenerator
except ImportError:
    QSvgGenerator = None

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import *  # noqa: F401
from floorplanner.rooms import *  # noqa: F401
from floorplanner.items import *  # noqa: F401
from floorplanner.dialogs import *  # noqa: F401
from floorplanner.view import *  # noqa: F401
from floorplanner.macro import *  # noqa: F401


class CsvIOMixin:
    def import_rooms_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import rooms from CSV", "",
            "CSV files (*.csv);;All files (*)")
        if path:
            self._import_rooms(path)

    def _import_rooms(self, path: str, interactive: bool = True):
        """Create walled rooms from a CSV with the columns
        Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes (Type, locations and
        Notes optional).  X_ft/Y_ft are the room's perimeter width and
        length; X_loc/Y_loc place its BOTTOM-LEFT corner, measured in
        feet from the canvas's bottom-left corner.  Rooms without a
        location go to the first clear spot on the canvas.

        The canvas grows (never shrinks) so every room fits, up to
        MAX_CANVAS_IN; a room whose size/location needs more than that is
        rejected as a likely typo."""
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise ValueError("Empty CSV file.")
                rows = [{(k or "").strip().lower(): (v or "").strip()
                         for k, v in row.items()} for row in reader]
        except (OSError, csv.Error, ValueError) as ex:
            if interactive:
                QMessageBox.critical(self, "Import failed", str(ex))
            self.status(f"Import failed: {ex}")
            return
        margin = 2.0 * FOOT
        max_in = MAX_CANVAS_IN

        # -- pass 1: parse + validate every row (no placement yet) --------
        specs, errors = [], []
        for i, row in enumerate(rows, start=2):     # 1 = header line
            name = row.get("name", "")
            try:
                if not name:
                    raise ValueError("missing Name")
                w_in = parse_feet(row["x_ft"])
                h_in = parse_feet(row["y_ft"])
                if w_in < 36.0 or h_in < 36.0:
                    raise ValueError("rooms must be at least 3' x 3'")
                xl, yl = row.get("x_loc_ft", ""), row.get("y_loc_ft", "")
                if xl and yl:
                    xl_in, yl_in, located = parse_feet(xl), parse_feet(yl), True
                elif xl or yl:
                    raise ValueError("give both X_loc_ft and Y_loc_ft, "
                                     "or neither")
                else:
                    xl_in = yl_in = None
                    located = False
                far_w = (xl_in + w_in) if located else w_in
                far_h = (yl_in + h_in) if located else h_in
                if far_w > max_in or far_h > max_in:
                    raise ValueError(
                        f"exceeds the {max_in / FOOT:g}' canvas limit "
                        "(check for a typo)")
            except (KeyError, ValueError) as ex:
                errors.append(f"line {i} ({name or '?'}): {ex}")
                continue
            specs.append({"name": name, "w": w_in, "h": h_in,
                          "located": located, "xl": xl_in, "yl": yl_in,
                          "type": row.get("type", ""),
                          "notes": row.get("notes", "")})

        # -- grow the canvas so every room fits (grow only, capped) -------
        # located rooms drive both dimensions; auto-placed rooms only need
        # the height to be tall enough to hold them (width grows afterwards)
        req_w = max([s["xl"] + s["w"] + margin
                     for s in specs if s["located"]], default=0.0)
        req_h = max([s["yl"] + s["h"] + margin
                     for s in specs if s["located"]]
                    + [s["h"] + 2 * margin
                       for s in specs if not s["located"]], default=0.0)
        new_w = min(max(SETTINGS["canvas_w_in"], req_w), max_in)
        new_h = min(max(SETTINGS["canvas_h_in"], req_h), max_in)
        resized = (new_w > SETTINGS["canvas_w_in"]
                   or new_h > SETTINGS["canvas_h_in"])
        if resized:
            SETTINGS["canvas_w_in"], SETTINGS["canvas_h_in"] = new_w, new_h
            self._apply_canvas()

        # -- pass 2: build the rooms (canvas height is now final) ---------
        canvas = canvas_rect()
        imported = 0
        for s in specs:
            w_in, h_in = s["w"], s["h"]
            if s["located"]:
                left = wall_snap_len(s["xl"])
                top = wall_snap_len(canvas.bottom() - s["yl"] - h_in)
            else:
                left, top = self._free_spot(w_in, h_in)
            corners = [QPointF(left, top), QPointF(left + w_in, top),
                       QPointF(left + w_in, top + h_in),
                       QPointF(left, top + h_in)]
            for j in range(4):
                p1, p2 = corners[j], corners[(j + 1) % 4]
                if not self._wall_exists(p1, p2):
                    self.scene.addItem(WallItem(QPointF(p1), QPointF(p2),
                                                "interior"))
            rebuild_all_walls(self.scene)
            centre = QPointF(left + w_in / 2, top + h_in / 2)
            res = detect_room(self.scene, centre)
            if res is None:
                errors.append(f"{s['name']}: no enclosed area detected "
                              "(overlapping another room?)")
                continue
            room = RoomItem(unique_room_name(self.scene, s["name"]), centre,
                            res[0], res[1], corners=res[2])
            if s["type"]:
                room.properties["room_type"] = next(
                    (t for t in ROOM_TYPES if t.lower() == s["type"].lower()),
                    s["type"])
            if s["notes"]:
                room.properties["notes"] = s["notes"]
            self.scene.addItem(room)
            bind_room_walls(self.scene, room)
            imported += 1

        # -- grow width for any auto-placed room parked past the edge -----
        walls = [it for it in self.scene.items() if isinstance(it, WallItem)]
        right = max([p.x() for it in walls for p in (it.p1, it.p2)],
                    default=0.0)
        if right + margin > canvas.right():
            grow_w = min(right + margin, max_in)
            if grow_w > SETTINGS["canvas_w_in"]:
                SETTINGS["canvas_w_in"] = grow_w
                self._apply_canvas()
                resized = True

        note = ""
        if resized:
            c = canvas_rect()
            note = (f" Canvas resized to {c.width() / FOOT:g}' × "
                    f"{c.height() / FOOT:g}'.")
        self.status(f"Imported {imported} room(s) from {path}"
                    + (f" — {len(errors)} row(s) skipped." if errors else ".")
                    + note)
        self._import_errors = errors      # inspectable (and testable)
        if errors and interactive:
            QMessageBox.warning(self, "Import finished with problems",
                                "\n".join(errors[:20]))

    def export_rooms_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export rooms to CSV", "rooms.csv",
            "CSV files (*.csv);;All files (*)")
        if path:
            self._export_rooms(path)

    def _export_rooms(self, path: str, interactive: bool = True):
        """Write every room as a CSV row in the same format the importer
        reads (Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes), so a plan's
        rooms round-trip.  Sizes/locations come from the room perimeter
        (wall centrelines); locations are the bottom-left corner in feet
        from the canvas's bottom-left corner, lengths in decimal feet."""

        def ft(v: float) -> str:
            return f"{v / 12.0:g}"

        canvas = canvas_rect()
        rooms = sorted((it for it in self.scene.items()
                        if isinstance(it, RoomItem)),
                       key=lambda r: r.name.lower())
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(["Name", "Type", "X_ft", "Y_ft",
                             "X_loc_ft", "Y_loc_ft", "Notes"])
                for r in rooms:
                    if r.corners:
                        xs = [c.x() for c in r.corners]
                        ys = [c.y() for c in r.corners]
                    else:                   # no traced perimeter: use the
                        rect = r.interior_rect()      # flood region box
                        xs = [rect.left(), rect.right()]
                        ys = [rect.top(), rect.bottom()]
                    wr.writerow([
                        r.name,
                        r.properties.get("room_type", ""),
                        ft(max(xs) - min(xs)),
                        ft(max(ys) - min(ys)),
                        ft(min(xs)),
                        ft(canvas.bottom() - max(ys)),
                        " ".join(str(r.properties.get("notes", ""))
                                 .split()),
                    ])
        except OSError as ex:
            if interactive:
                QMessageBox.critical(self, "Export failed", str(ex))
            self.status(f"Export failed: {ex}")
            return
        self.status(f"Exported {len(rooms)} room(s) to {path}")

    def _wall_exists(self, p1: QPointF, p2: QPointF) -> bool:
        for it in self.scene.items():
            if isinstance(it, WallItem) and (
                    (QLineF(it.p1, p1).length() < 0.6
                     and QLineF(it.p2, p2).length() < 0.6)
                    or (QLineF(it.p1, p2).length() < 0.6
                        and QLineF(it.p2, p1).length() < 0.6)):
                return True
        return False

    def _free_spot(self, w_in: float, h_in: float):
        """Top-left corner (snapped) of a canvas spot where a w x h room
        won't touch existing walls or rooms (24" clearance)."""
        margin = 24.0
        canvas = canvas_rect()
        occupied = []
        for it in self.scene.items():
            if isinstance(it, WallItem):
                occupied.append(it.boundingRect())
            elif isinstance(it, RoomItem):
                occupied.append(it.path.boundingRect())
        step = max(SETTINGS["wall_snap_in"], 12.0)
        y = canvas.top() + margin
        while y + h_in + margin <= canvas.bottom():
            x = canvas.left() + margin
            while x + w_in + margin <= canvas.right():
                cand = QRectF(x - margin / 2, y - margin / 2,
                              w_in + margin, h_in + margin)
                if not any(cand.intersects(r) for r in occupied):
                    return x, y
                x += step
            y += step
        # canvas full: park it to the right of everything
        right = max([r.right() for r in occupied], default=canvas.left())
        return wall_snap_len(right + margin), canvas.top() + margin
