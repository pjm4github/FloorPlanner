"""Plan IO: open, save, export, and the scene<->document bridges (P2.5).

Lifted VERBATIM out of `MainWindow` as a mixin, so `win.serialize()`,
`win.snapshot()`, `win.load_data(...)` and `win._is_dirty()` -- all called
directly by the suite -- resolve unchanged.

The three payloads, kept distinct on purpose:
  * `snapshot()`   -- the canonical v5 document; undo and the dirty flag (P2.3)
  * `design_document()` -- what gets WRITTEN: snapshot plus provenance,
    unmodelled settings and active_floor (P2.2)
  * `serialize()`  -- the legacy v4 dict, now only for File > Export legacy v4
"""
import copy
import json

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
from floorplanner.model import (  # serialization bridge (aliased)
    DEFAULT_FLOOR, FILE_VERSION, Floor, Furnishing, Opening as OpeningModel,
    Project, Room as RoomModel, Wall as WallModel,
)
from floorplanner.design.bridge import (          # P1.4/P1.5 scene <-> design
    apply_design_to_scene, design_from_scene,
)
from floorplanner.design.canonical import canonicalize
from floorplanner.design.importer import (       # P2.1 legacy -> v5
    conversion_report, import_legacy,
)
from floorplanner.design.model import Design
from floorplanner.design.template import (        # P4.4 one-room templates
    merge_room_document, room_subdocument, template_offset_to,
    template_room_name,
)
from floorplanner.design.validate import check
from floorplanner.design.bridge import rebase_weld_baseline
from floorplanner.design.verify import rebase  # P1.6 shadow mode
from floorplanner.dialogs import *  # noqa: F401
from floorplanner.view import *  # noqa: F401
from floorplanner.macro import *  # noqa: F401


class PlanIOMixin:
    def load_data(self, data: dict, keep_backdrop: bool = False):
        """APPLY a document to the scene, exactly as given. Never migrates.

        This is the undo-restore path (`_restore_state`) as well as the plain
        "put this dict on the canvas" helper, so it must stay a faithful apply:
        routing it through P2.1's importer would make **every undo weld the
        geometry and re-trace every room**, which is a repair, not a restore.
        Opening a FILE is `open_document` -- that is where migration, the dirty
        flag and the conversion report live."""
        if data.get("format") == "floorplanner-design":
            apply_design_to_scene(self, Design.from_dict(data),
                                  keep_backdrop=keep_backdrop)
            return
        self.apply_project_to_scene(Project.from_dict(data), keep_backdrop)

    def open_document(self, data: dict, interactive: bool = True):
        """THE OPEN PATH (P2.1). Returns the conversion report, or None for a
        document that needed no conversion.

        Legacy v1-v4 `floorplanner-json` is welded, planarised and re-traced by
        `design.importer` -- the first time the app has ever moved a user's wall
        ends on open -- then marked dirty and reported. v5
        `floorplanner-design` is validated and applied as-is: no weld pass ever,
        and never dirty. A v5 file failing I14 is reported as MALFORMED rather
        than silently re-welded; that asymmetry is the point of promoting
        'welded' from a hopeful post-condition to a checked invariant."""
        self._conversion = None
        # GATE 3: which format a plan arrived in decides whether the bridge's
        # unwelded-ends warning has anything to say. A v5 document already
        # holds one vertex per corner, so an "unwelded end" seen on open is a
        # property of how the SCENE decomposes it -- and, measured, one that
        # Edit > Coalesce all walls now silences without changing a single
        # document coordinate. See `bridge._warn_unwelded`.
        # ON THE SCENE, not on the window: `design_from_scene` resolves its
        # argument to the QGraphicsScene before warning, and that is where the
        # warning's own baseline attribute lives too. Setting it on the window
        # reads fine and does nothing.
        self.scene._v5_source = data.get("format") == "floorplanner-design"
        if data.get("format") == "floorplanner-design":
            design = Design.from_dict(data)
            apply_design_to_scene(self, design)
            # provenance is written ONCE at import and never mutated; a v5 file
            # that carries one keeps it across a re-save (P2.2)
            self._provenance = data.get("provenance")
            # boundary=True adds I15 (outline completeness), which is a
            # DOCUMENT-BOUNDARY check by measurement: it fires on correct
            # mid-drag transients if run per mutation, so a load is exactly
            # where it belongs. CHECK YES, FIX NO (D49's amended shape) -- the
            # file opens unchanged and the user is told.
            errs = check(data, deep=True, boundary=True)
            if errs:
                bad = [e for e in errs if e.startswith("I14")]
                head = ("This v5 file is malformed: it is not welded at "
                        f"vertex_weld_in ({len(bad)} unwelded junction(s)). "
                        "It has been opened unchanged -- re-welding silently "
                        "is exactly what the invariant exists to prevent."
                        if bad else
                        f"This v5 file reports {len(errs)} invariant "
                        f"violation(s); it has been opened unchanged.")
                self._report(head + "  " + "; ".join(errs[:3]), interactive,
                             "Malformed design file")
            return None
        design, rep = import_legacy(data)
        apply_design_to_scene(self, design)
        # active_floor is VIEW state: the v4 file carries it, the v5 Design
        # deliberately does not (keeping it out is what stops a floor switch
        # dirtying the document). Carry it across by hand or the conversion
        # silently forgets which floor the user was editing.
        want = data.get("active_floor")
        if want and any(f.name == want for f in self.floors):
            self.active_floor = want
            self._sync_floor_state()
        self._conversion = rep
        self._provenance = design.to_dict().get("provenance")
        self._report(conversion_report(rep, int(data.get("version", 0))),
                     interactive, "Converted to the v5 format")
        return rep

    # the codes the SAVE boundary asks about. One tuple, because D59 widens
    # this to the cheap twelve by ADDING TO IT rather than by growing a second
    # call site beside `_write_plan`.
    BOUNDARY_ASK_CODES = ("I15",)

    def _boundary_ask(self, doc, interactive=True):
        """THE SAVE BOUNDARY: ask, do not refuse. Returns True to go on writing.

        D49's amended shape, applied to I15. **SAVE ASKS, IT DOES NOT REFUSE** --
        a deform-to-follow drag can transiently produce geometry the user has
        not finished with, and a hard refusal traps them with unsaveable work.
        The existing refusal in `_write_plan` above is a different and older
        decision about a different fault class, and this deliberately does not
        touch it.

        **AND THE REPORT MUST BE ACTIONABLE**, so it names the ROOM and the
        POINT rather than an id: `r15` and `v80` tell a user nothing, while
        "OFFICE at (1273.5, 315.0)" is somewhere they can look.

        WHY I15 IS ASKED HERE AT ALL, given the load check. Measured: the app
        produces violations itself -- `normalize_walls` writes seven across two
        corpus plans, attributed to `weld_scene` -- so a load-only check would
        miss exactly the files this application creates. Both boundaries, and
        the reason is a measurement rather than symmetry.

        Headless callers pass `interactive=False`: the findings land on
        `self._boundary_findings` and the save proceeds, the `_import_rooms`
        convention.
        """
        errs = [e for e in check(doc, deep=True, boundary=True)
                if e.startswith(self.BOUNDARY_ASK_CODES)]
        self._boundary_findings = errs
        if not errs:
            return True
        V = {v["id"]: v for v in doc.get("vertices", ())}
        R = {r["id"]: r for r in doc.get("rooms", ())}
        lines = []
        for e in errs[:6]:
            room = next((R[t]["name"] for t in e.split() if t in R), "?")
            pt = next((V[t] for t in e.split() if t in V), None)
            where = f"({pt['x']:.1f}, {pt['y']:.1f})" if pt else "?"
            lines.append(f"  • {room} at {where}")
        more = "" if len(errs) <= 6 else f"\n  … and {len(errs) - 6} more"
        text = (f"{len(errs)} room edge(s) run through a wall corner without "
                f"naming it:\n\n" + "\n".join(lines) + more +
                "\n\nThe plan can still be saved. Save anyway?")
        self.status(f"Outline completeness: {len(errs)} finding(s).")
        if not interactive:
            return True
        return QMessageBox.question(
            self, "Outline completeness", text,
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        ) == QMessageBox.StandardButton.Save

    def _report(self, text, interactive, title):
        """Tell the user. A modal hangs headless, so scripted/test callers pass
        interactive=False and read the status line (the `_import_rooms`
        convention)."""
        if interactive:
            QMessageBox.information(self, title, text)
        self.status(text)

    def _finish_open(self):
        """After `_reset_undo` has declared the loaded plan the clean baseline,
        re-dirty it if it was CONVERTED. The conversion only exists in memory --
        the legacy file on disk is untouched -- so the document must read as
        unsaved until the user accepts it with a Save."""
        if getattr(self, "_conversion", None):
            self._saved_state = None             # nothing on disk matches this

    def apply_project_to_scene(self, project: Project,
                               keep_backdrop: bool = False):
        for key, default in DEFAULT_SETTINGS.items():
            val = project.settings.get(key, default)
            if isinstance(default, bool):    # keep flags as bool (not 1.0/0.0)
                SETTINGS[key] = bool(val)
                continue
            try:
                SETTINGS[key] = float(val)
            except (TypeError, ValueError):
                SETTINGS[key] = default
        self._apply_canvas()
        # the reference image is a tracing backdrop, not plan data -- on undo
        # (keep_backdrop) detach it so scene.clear() doesn't delete it, then
        # re-add it afterwards.  New/Open clear it like everything else.
        backdrops = []
        if keep_backdrop:
            backdrops = [it for it in self.scene.items()
                         if isinstance(it, ReferenceImageItem)]
            for b in backdrops:
                self.scene.removeItem(b)
        self.scene.clear()
        for b in backdrops:
            self.scene.addItem(b)
        # restore the floor roster + active floor from the model, and prime the
        # runtime cache NOW so items created during this load default to the
        # right active floor (each item's floor is then overridden from the file).
        self.floors = [Floor(f.name, f.reference) for f in project.floors]
        self.active_floor = project.active_floor
        set_floor_state(active=self.active_floor)
        self._z_top = 0                  # bring-to-front counter resets per doc
        for wm in project.walls:
            wall = WallItem(QPointF(*wm.p1), QPointF(*wm.p2), wm.wall_type)
            wall.floor = wm.floor                 # load overrides the default tag
            self.scene.addItem(wall)
            for om in wm.openings:
                try:
                    op = OpeningItem(wall, om.kind, om.code, om.s)
                except ValueError as exc:
                    # DEFECT 6's "incl. on load" -- this is the v4 site, and it
                    # silently dropped the opening. It now files into the same
                    # vocabulary the v5 apply path has used since P1.5, which
                    # ends the asymmetry where a v5 load reported and a v4 load
                    # did not.
                    report_opening_failure(self.scene, wall, om.kind, om.code,
                                           om.s, f"{exc} (opening the plan)")
                    continue
                op.door_type = om.door_type
                op.swing = om.swing
                wall.openings.append(op)
            # no per-wall rebuild here: rebuild_all_walls below rebuilds every
            # wall once with a shared index (a per-wall rebuild is O(n) with
            # cascade, so on a big/duplicated plan the loop alone took minutes)
        # merge overlapping/duplicate walls (e.g. legacy v1/v2 party-wall pairs)
        # into single shared walls FIRST, so the rebuild runs on the reduced set
        # (welding is NOT done here: load is also the undo-restore path and
        # welding does not fully converge at messy junctions -> geometry would
        # drift on every undo.  Junctions weld on draw and via the manual sweep.)
        merge_all(self.scene)
        rebuild_all_walls(self.scene)
        missing = []
        for rm in project.rooms:
            anchor = QPointF(*rm.anchor)
            res = detect_room(self.scene, anchor)
            if res is None:
                # an open room (a wall was detached/moved away) won't flood-fill
                # -> rebuild it from the saved perimeter corners
                saved = (rm.properties or {}).get("perimeter_corners")
                if saved and len(saved) >= 3:
                    corners = [QPointF(c[0], c[1]) for c in saved]
                    res = (room_path_from_corners(corners),
                           poly_area_sqft(corners), corners)
                else:
                    # keep the room (so it survives a re-save); placeholder
                    path = QPainterPath()
                    path.addRect(QRectF(anchor.x() - 12, anchor.y() - 12,
                                        24, 24))
                    res = (path, 0.0, None)
                    missing.append(rm.name)
            name = unique_room_name(self.scene, rm.name)
            # perimeter_corners is READ above (the open-room fallback) and then
            # dropped: the live scene derives corners from the outline, so a
            # copy left in `properties` would be stale data nothing maintains --
            # exactly the class of bug this migration exists to kill.
            props = {k: v for k, v in (rm.properties or {}).items()
                     if k != "perimeter_corners"}
            room = RoomItem(name, anchor, res[0], res[1], props, res[2])
            room.floor = rm.floor                 # load overrides the default tag
            room.show_dims = rm.show_dimensions
            room.label_offset = QPointF(*rm.label_offset)
            self.scene.addItem(room)
            # bind this room's walls by geometry (works for both v2 plans,
            # which store coincident party walls, and legacy v1 plans)
            bind_room_walls(self.scene, room, settle=False)
            for w in room.walls:                  # a room's walls share its floor
                w.floor = room.floor              # (fixes synthesized/open edges)
        unknown = []
        for fm in project.furnishings:
            if furnishing_spec(fm.kind) is None:
                unknown.append(fm.kind or "?")
                continue
            item = make_furnishing(fm.kind, QPointF(*fm.pos), fm.rotation,
                                   fm.extra)
            item.floor = fm.floor                 # load overrides the default tag
            self.scene.addItem(item)
        # roster + active floor are restored; sync the runtime cache + visibility
        self._sync_floor_state()
        notes = []
        if missing:
            notes.append("Could not re-detect room(s): " + ", ".join(missing)
                         + " — check the walls around them.")
        if unknown:
            notes.append("Skipped unknown furnishing kind(s): "
                         + ", ".join(unknown) + ".")
        # R5, LOAD SURFACE: openings that could not be placed join the
        # open/conversion report rather than vanishing. Drained here so the
        # edit-path drain never picks up a load's entries and reports them as
        # something the user just did.
        failed = drain_opening_failures(self.scene)
        if failed:
            notes.append(f"{len(failed)} opening(s) could not be placed: "
                         + "; ".join(failed[:3])
                         + (f" (+{len(failed) - 3} more)" if len(failed) > 3
                            else ""))
        if notes:
            self.status("  ".join(notes))
        # P1.6: load DEFINES the baseline.  A plan opened from a corrupt legacy
        # file has faults at rest (planc1: 17x I6 + 1x I11) and shadow mode must
        # not fire on those -- only on corruption introduced afterwards.  Undo's
        # restore comes through here too, reinstating an already-verified state.
        rebase(self)
        # ...and the unwelded-ends baseline: whatever a legacy file arrives with
        # is the plan's arrival state, not a tear an edit made (defect 22)
        rebase_weld_baseline(self.scene)

    def project_from_scene(self) -> Project:
        """Walk the scene into the Qt-free domain model (model.Project).

        Open walls are skipped — they're regenerated from a room's open
        edges on load, not stored."""
        walls, rooms, furnishings = [], [], []
        for it in self.scene.items():
            if isinstance(it, FurnishingItem):
                furnishings.append(Furnishing(
                    kind=it.kind,
                    pos=(it.pos().x(), it.pos().y()),
                    rotation=it.rotation(),
                    extra=dict(it.extra_state()),
                    floor=getattr(it, "floor", DEFAULT_FLOOR),
                ))
            elif isinstance(it, WallItem):
                walls.append(WallModel(
                    wall_type=it.wall_type,
                    p1=(it.p1.x(), it.p1.y()),
                    p2=(it.p2.x(), it.p2.y()),
                    rooms=[r.name for r in it.rooms],
                    openings=[OpeningModel(op.kind, op.code, op.s,
                                           op.door_type, op.swing)
                              for op in it.openings],
                    floor=getattr(it, "floor", DEFAULT_FLOOR),
                ))
            elif isinstance(it, RoomItem):
                rooms.append(RoomModel(
                    name=it.name,
                    anchor=(it.anchor.x(), it.anchor.y()),
                    label_offset=(it.label_offset.x(), it.label_offset.y()),
                    show_dimensions=it.show_dims,
                    # P3.2: perimeter_corners is re-DERIVED here from the
                    # outline (same 2dp rounding the old live mirror used), so
                    # the legacy export stays byte-compatible. It is produced
                    # at serialization time and nowhere else.
                    properties=it.export_properties(),
                    floor=getattr(it, "floor", DEFAULT_FLOOR),  # alias the live dict
                ))
        # the roster MUST come from self.floors (an empty floor has no items to
        # derive it from); active_floor rides along but is dropped by to_dict.
        return Project(version=FILE_VERSION, units="inches",
                       settings=dict(SETTINGS), walls=walls, rooms=rooms,
                       furnishings=furnishings,
                       floors=[Floor(f.name, f.reference) for f in self.floors],
                       active_floor=self.active_floor)

    def snapshot(self, report=None) -> dict:
        """The CANONICAL v5 document, and the payload undo and the dirty flag
        are both defined on (P2.3).

        Deliberately NOT `design_document()`: `provenance`, unmodelled document
        settings and `active_floor` are window state, not scene state. Keeping
        `active_floor` out is what stops a floor switch from becoming an undo
        step -- the same reasoning that kept it out of `serialize()`.

        Canonical, so equality means "the same plan" rather than "the same
        bytes". That also makes the comparison granularity-invariant: whether
        the scene holds one long wall or three segments split at junctions, the
        walk planarises to the same document, so scene wall-count is
        PRESENTATION state and cannot spuriously dirty the plan."""
        return canonicalize(design_from_scene(self, report=report).to_dict())

    def design_document(self) -> dict:
        """The v5 document to WRITE (P2.2).

        `design_from_scene` reports what the scene holds; this adds back the
        three things the scene cannot hold but the file must carry:
        `provenance` (the conversion audit trail -- re-attached on EVERY save,
        because its whole value is surviving the save the conversion report
        asks the user to make), any document `settings` the walk does not model,
        and `active_floor`, which rides inside `settings` because the v5 root is
        a closed schema."""
        doc = design_from_scene(self).to_dict()
        if self._doc_settings:
            merged = dict(self._doc_settings)
            merged.update(doc["settings"])       # the walk's values win
            doc["settings"] = merged
        doc["settings"]["active_floor"] = self.active_floor
        if self._provenance:
            doc["provenance"] = self._provenance
        return doc

    def serialize(self) -> dict:
        """Plan -> the LEGACY v4 dict (`floorplanner-json`).

        DEMOTED AT P2.3 and on its way out. Its sole remaining caller is
        `export_legacy_v4_path` (File > Export legacy v4...), kept for ONE
        release so the v5 cutover strands nobody, and it dies with that menu
        item. Save writes v5 via `design_document()`; undo and the dirty flag
        are defined on `snapshot()`. **A new caller of this method is a bug** --
        an alive-but-orphaned serializer is how a format forks.

        Goes through the Qt-free model; Project.to_dict emits the arrays in a
        stable, z-independent order (sorted by geometry) so bring-to-front z
        changes never alter the snapshot — keeping undo/redo comparison
        correct."""
        return self.project_from_scene().to_dict()

    # -- one-room templates: duplicate / copy-paste / save-load (P4.4) --------
    def room_template(self, room) -> dict:
        """The one-room v5 template document for `room` — §4's *Duplicate a
        room*, and what File ▸ Save template room… writes.

        A FLOATING room is cut straight out of the walk: it already owns its
        walls and its own vertex namespace (I12), so the subset is closed.
        A PLACED room's walls are NOT wholly its own, and rather than inventing
        a second way to trim them (`_copy_spec`'s `bounding_walls` proximity +
        `_perimeter_span`, both deleted here) this cuts it out through the REAL
        ops: extract, template, join back. The zero-offset round trip is
        precisely the P4.2 label-CLICK path — press, no move, release — which
        every room click already performs, so it is proven rather than new."""
        from floorplanner.extract import extract_room, join_room  # late
        if getattr(room, "placement_state", "placed") == "floating":
            return room_subdocument(design_from_scene(self).to_dict(),
                                    room.name)
        extract_room(self.scene, room)
        try:
            return room_subdocument(design_from_scene(self).to_dict(),
                                    room.name)
        finally:
            join_room(self.scene, room)      # the plan comes back as it was

    def insert_room_template(self, tmpl: dict, at=None, name=None):
        """Fold a one-room template into THIS design as a floating room,
        centred on `at` (scene point) when given. Returns the new `RoomItem`.

        Document-level by construction: the template is merged into the
        current document and the result applied through the one apply path,
        so an inserted room arrives by exactly the route a loaded file does.
        It lands FLOATING — it has joined nothing yet — which is the same
        contract Extract gives and what makes an insert under shuffle behave
        like every other float."""
        base = self.design_document()
        lid = next((lv["id"] for lv in base.get("levels") or []
                    if lv["name"] == self.active_floor), None)
        dx = dy = 0.0
        if at is not None:
            dx, dy = template_offset_to(tmpl, at.x(), at.y())
        want = unique_room_name(self.scene,
                                name or template_room_name(tmpl))
        merged = merge_room_document(base, tmpl, lid, dx, dy, want)
        self.load_data(merged)
        return next((r for r in self.scene.items()
                     if isinstance(r, RoomItem) and r.name == want), None)

    def duplicate_room(self, room, at=None):
        """§4's *Duplicate a room* end to end: template it, insert the copy as
        a floating room. Nothing about the source changes."""
        return self.insert_room_template(self.room_template(room), at=at)

    def save_template_path(self, path: str, room):
        """Non-interactive template write (the `save_path` convention)."""
        tmpl = self.room_template(room)
        errs = check(tmpl, deep=True)
        if errs:
            raise ValueError("the room template is not a valid design: "
                             + "; ".join(errs[:3]))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tmpl, f, indent=1)

    def load_template_path(self, path: str, at=None):
        """Non-interactive template insert (the `load_path` convention)."""
        with open(path, "r", encoding="utf-8") as f:
            tmpl = json.load(f)
        if tmpl.get("format") != "floorplanner-design":
            raise ValueError("not a floorplanner design file")
        template_room_name(tmpl)            # raises unless it is ONE room
        return self.insert_room_template(tmpl, at=at)

    def selected_floating_room(self):
        """The single selected floating room, or None — what File ▸ Save
        template room… is enabled by (the ruled rule, and a structural one:
        only a floating room owns its walls outright)."""
        rooms = [it for it in self.scene.selectedItems()
                 if isinstance(it, RoomItem)
                 and getattr(it, "placement_state", "placed") == "floating"]
        return rooms[0] if len(rooms) == 1 else None

    def save_template_room(self):
        room = self.selected_floating_room()
        if room is None:
            QMessageBox.information(
                self, "Save template room",
                "Select a single FLOATING room first (right-click a room ▸ "
                "Extract room). Only a floating room owns its walls "
                "outright, so only it can be cut out whole.")
            return
        start = str(designs_dir() / f"{room.name}.room.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save template room", start,
            "Room template (*.json);;All files (*)")
        if not path:
            return
        try:
            self.save_template_path(path, room)
        except (OSError, ValueError) as ex:
            QMessageBox.critical(self, "Save template failed", str(ex))
            return
        self.status(f"Saved room template '{room.name}' to {path}")

    def load_template_room(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load template room", str(designs_dir()),
            "Room template (*.json);;All files (*)")
        if not path:
            return
        try:
            centre = self.view.mapToScene(
                self.view.viewport().rect().center())
            room = self.load_template_path(path, at=centre)
        except (OSError, ValueError, KeyError, TypeError) as ex:
            QMessageBox.critical(self, "Load template failed", str(ex))
            return
        self.status(f"Inserted template room '{room.name}' — it is FLOATING: "
                    "drag it by its name, then right-click it to join it "
                    "into the plan.")

    def open_plan(self):
        if not self._confirm_discard_changes("Open plan"):
            return
        start = self.current_path or str(designs_dir())
        path, _ = QFileDialog.getOpenFileName(
            self, "Open plan", start,
            "Floor plan JSON (*.json);;All files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.open_document(data)     # migrates a legacy file; reports
        except (OSError, ValueError, KeyError, TypeError) as ex:
            QMessageBox.critical(self, "Open failed", str(ex))
            return
        self.current_path = path
        self._reset_undo()               # opened document is the new baseline
        self._finish_open()              # ...unless it was CONVERTED -> dirty
        self._update_title()
        self.status(f"Opened {path}")
        rec = getattr(self, "_recorder", None)
        if rec is not None:              # macro recorder: File > Open with
            rec.on_open(path)            # its chosen file, as one ^O token

    def save_plan(self):
        if not self.current_path:
            self.save_plan_as()
            return
        self._write_plan(self.current_path)

    def save_plan_as(self):
        start = self.current_path or str(designs_dir() / "floorplan.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save plan", start,
            "Floor plan JSON (*.json);;All files (*)")
        if not path:
            return
        self._write_plan(path)
        if self.current_path == path:    # _write_plan sets it ONLY on success
            rec = getattr(self, "_recorder", None)
            if rec is not None:          # macro recorder: Save As with its
                rec.on_save_as(path)     # chosen file, as one ^+S token

    def _write_plan(self, path: str):
        # guarded: reached from the Save menu action, a Qt callback, where a
        # raise becomes abort() (defect 26). The REFUSAL TO WRITE IS UNCHANGED
        # -- "don't write a corrupt plan" is a deliberate decision this fix has
        # no business overruling. Only the fatality was the bug, and a refusal
        # the user can SEE was always the intent (defect 17's lesson).
        if not self._verify_or_report("save", deep=True):   # all fifteen
            self.status("Not saved: the plan has invariant violations "
                        "(see the message above).")
            return
        state = self.snapshot()
        on_disk = self.design_document()     # P2.2: the FILE is v5 now
        if not self._boundary_ask(on_disk, interactive=True):
            self.status("Not saved: cancelled at the outline-completeness "
                        "report.")
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(on_disk, f, indent=1)
        except OSError as ex:
            QMessageBox.critical(self, "Save failed", str(ex))
            return
        self.current_path = path
        self._saved_state = state            # plan now matches what's on disk
        self._update_title()
        self.status(f"Saved {path}")

    def export_legacy_v4(self):
        """File ▸ Export legacy v4… -- kept for ONE release so nobody is
        stranded by the v5 cutover."""
        start = self.current_path or str(designs_dir() / "floorplan-v4.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export legacy v4", start,
            "Floor plan JSON (*.json);;All files (*)")
        if path:
            self.export_legacy_v4_path(path)

    def export_legacy_v4_path(self, path: str):
        """Non-interactive legacy export. Writes what the OLD loader reads --
        `serialize()` is still the v4 walk, so this stays a straight dump plus
        the top-level `active_floor` v4 files carry."""
        state = self.serialize()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({**state, "active_floor": self.active_floor}, f, indent=2)
        self.status(f"Exported legacy v4 plan to {path}")
        return path

    def load_path(self, path: str):
        """Non-interactive open (no dialogs).  Raises on failure.

        Same conversion as File > Open, minus the modal: a converted legacy
        plan lands dirty and its report goes to the status line."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.open_document(data, interactive=False)
        self.current_path = path
        self._reset_undo()
        self._finish_open()
        self._update_title()

    def save_path(self, path: str):
        """Non-interactive save (no dialogs).  Raises on failure."""
        # guarded: reached from the Save menu action, a Qt callback, where a
        # raise becomes abort() (defect 26). The REFUSAL TO WRITE IS UNCHANGED
        # -- "don't write a corrupt plan" is a deliberate decision this fix has
        # no business overruling. Only the fatality was the bug, and a refusal
        # the user can SEE was always the intent (defect 17's lesson).
        if not self._verify_or_report("save", deep=True):   # all fifteen
            self.status("Not saved: the plan has invariant violations "
                        "(see the message above).")
            return
        state = self.snapshot()
        on_disk = self.design_document()     # P2.2: the FILE is v5 now
        # the boundary report runs here too -- non-interactively, so it records
        # and never blocks. A scripted save that silently skipped the check
        # would make the macro path quieter than the UI one, which is how a
        # class of fault comes to be invisible to exactly the tooling that
        # produces it most often.
        self._boundary_ask(on_disk, interactive=False)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(on_disk, f, indent=1)
        self.current_path = path
        self._saved_state = state
        self._update_title()

    def clear_plan(self):
        """Non-interactive New (no confirm dialog)."""
        self.scene.clear()
        self.current_path = None
        SETTINGS.update(DEFAULT_SETTINGS)
        self._apply_canvas()
        self.floors = [Floor(DEFAULT_FLOOR)]    # back to a single default floor
        self.active_floor = DEFAULT_FLOOR
        self._sync_floor_state()
        self._conversion = None          # a new plan was converted from nothing
        self._provenance = None
        self._doc_settings = {}
        self._reset_undo()

    def new_plan(self):
        if not self._confirm_discard_changes("New plan"):
            return
        self.scene.clear()
        self.current_path = None
        SETTINGS.update(DEFAULT_SETTINGS)
        self._apply_canvas()
        self.floors = [Floor(DEFAULT_FLOOR)]    # back to a single default floor
        self.active_floor = DEFAULT_FLOOR
        self._sync_floor_state()
        self._conversion = None          # a new plan was converted from nothing
        self._provenance = None
        self._doc_settings = {}
        self._reset_undo()

    def _is_dirty(self) -> bool:
        """True when the plan has edits not yet written to its file.

        Both sides are canonicalised before comparing. `snapshot()` already
        returns canonical form, so this is belt-and-braces today -- but defining
        equality ON canonical form is what survives any future producer that
        forgets to normalise, including whichever way P3.1's uid decision goes.
        Two documents describing the same plan must compare equal even when
        different code paths built them."""
        if self._saved_state is None:
            return True                  # converted-but-never-saved (P2.1)
        return self.snapshot() != canonicalize(copy.deepcopy(self._saved_state))

    def _confirm_discard_changes(self, title: str = "Unsaved changes") -> bool:
        """If there are unsaved edits, ask Save / Discard / Cancel.  Returns True
        when it's OK to proceed (saved or discarded), False to cancel."""
        if not self._is_dirty():
            return True
        btn = QMessageBox.warning(
            self, title,
            "This design has unsaved changes.\nSave them before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        if btn == QMessageBox.StandardButton.Save:
            self.save_plan()
            return not self._is_dirty()      # False if the Save dialog was cancelled
        return btn == QMessageBox.StandardButton.Discard

    def _update_title(self):
        if self.current_path:
            self.setWindowTitle(f"Floor Planner — {self.current_path}")
        else:
            c = canvas_rect()
            self.setWindowTitle(f"Floor Planner — canvas "
                                f"{fmt_ftin(c.width())} × "
                                f"{fmt_ftin(c.height())}")

    def export_canvas(self, path: str, rect: QRectF = None,
                      scale: float = 2.0) -> bool:
        """Render the scene (items only, no editor grid) to a PNG or SVG file,
        chosen by the path's extension.  `rect` defaults to the content box."""
        rect = QRectF(rect) if rect is not None else self._content_rect()
        if str(path).lower().endswith(".svg"):
            return self._export_svg(path, rect)
        return self._export_png(path, rect, scale)

    def _export_png(self, path, rect, scale) -> bool:
        img = QImage(max(1, int(rect.width() * scale)),
                     max(1, int(rect.height() * scale)),
                     QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.scene.render(p, QRectF(0, 0, img.width(), img.height()), rect)
        p.end()
        return bool(img.save(str(path)))

    def _export_svg(self, path, rect) -> bool:
        if QSvgGenerator is None:
            raise RuntimeError("QtSvg is unavailable -- cannot write SVG.")
        gen = QSvgGenerator()
        gen.setFileName(str(path))
        gen.setSize(QSize(max(1, int(rect.width())),
                          max(1, int(rect.height()))))
        gen.setViewBox(QRectF(0, 0, rect.width(), rect.height()))
        gen.setTitle("FloorPlanner canvas")
        gen.setDescription("Scene units are inches (1 unit = 1 inch). "
                           "Origin at the framed region's top-left.")
        p = QPainter(gen)
        self.scene.render(p, QRectF(0, 0, rect.width(), rect.height()), rect)
        p.end()
        return True

    def _content_rect(self) -> QRectF:
        """Bounding box of all walls/rooms/furnishings (or the canvas when
        empty), with a 1' margin — the region a snapshot should frame."""
        box = QRectF()
        for it in self.scene.items():
            if isinstance(it, (WallItem, RoomItem, FurnishingItem)):
                box = box.united(it.sceneBoundingRect())
        if box.isNull():
            box = canvas_rect()
        return box.adjusted(-FOOT, -FOOT, FOOT, FOOT)
