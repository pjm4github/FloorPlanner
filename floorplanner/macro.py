"""Headless macro runner + the macro recorder dialog (AI/script-driven
edits).  MainWindow is reached via a late import (macro<->window cycle)."""
import re

from PyQt6 import sip  # noqa: F401
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import *  # noqa: F401
from floorplanner.rooms import *  # noqa: F401
from floorplanner.items import *  # noqa: F401


# ---------------------------------------------------------------------------
# THE CTRL-SHORTCUT TABLE — one row per shortcut, shared by the RUNNER
# (token → MainWindow method) and the RECORDER (keystroke → token). ADDING A
# MENU SHORTCUT IS ONE ROW HERE and it records and replays; a design-guard
# test asserts every named method really exists on MainWindow.
#   token key : "<letter>" = Ctrl+letter, "+<letter>" = Ctrl+Shift+letter
#               (written in macros with a leading '^': ^G, ^+G)
#   "key"     : the Qt key the recorder matches while Ctrl is held
#   "method"  : the MainWindow method the runner calls; None = special
#               handling in `MacroRunner._caret` (^A drives the scene; ^S
#               saves to the current file; ^O / ^+S carry a file path)
#   "record"  : False for tokens an APP HOOK emits WITH their dialog value
#               (^O "path" via on_open, ^+S "path" via on_save_as) — the raw
#               keystroke must not also record, or a cancelled dialog would
#               leave a broken bare token in the macro
CARET_SHORTCUTS = {
    "Z":  {"key": Qt.Key.Key_Z, "method": "undo"},
    "+Z": {"key": Qt.Key.Key_Z, "method": "redo"},
    "Y":  {"key": Qt.Key.Key_Y, "method": "redo"},
    "X":  {"key": Qt.Key.Key_X, "method": "cut_selected"},
    "C":  {"key": Qt.Key.Key_C, "method": "copy_selected"},
    "V":  {"key": Qt.Key.Key_V, "method": "paste_clipboard"},
    "G":  {"key": Qt.Key.Key_G, "method": "group_selected"},
    "+G": {"key": Qt.Key.Key_G, "method": "ungroup_selected"},
    "N":  {"key": Qt.Key.Key_N, "method": "clear_plan"},
    "A":  {"key": Qt.Key.Key_A, "method": None},
    "S":  {"key": Qt.Key.Key_S, "method": None},
    "O":  {"key": Qt.Key.Key_O, "method": None, "record": False},
    "+S": {"key": Qt.Key.Key_S, "method": None, "record": False},
    "F":  {"key": Qt.Key.Key_F, "method": None, "record": False},
    "+F": {"key": Qt.Key.Key_F, "method": None, "record": False},
    "H":  {"key": Qt.Key.Key_H, "method": "toggle_shuffle", "record": False},
}
# hook-emitted tokens the recorder must not raw-record (see "record" above)
CARET_HOOK_TOKENS = {t for t, s in CARET_SHORTCUTS.items()
                     if not s.get("record", True)}


class MacroRunner:
    """Drives a MainWindow from a space/newline-delimited macro string so an
    external program (or an AI) can edit a plan headlessly.

    A macro is a flat list of whitespace-separated tokens; '#' starts a
    line comment and double-quoted tokens may contain spaces (room names).
    Positions are in SCENE INCHES (1 unit = 1 inch); a value may also be
    written in feet like 10' or 10'6".

    Tokens
      Tool select   S E I D W R        Select / Exterior-wall / Interior-wall /
                                       Door / Window / Room  (also: TOOL <name>;
                                       legacy digits 1-6 still work)
      Shortcuts     ^N ^Z ^Y ^X ^C ^V ^G ^A ^S
                                       new / undo / redo / cut / copy / paste /
                                       group / select-all / save-to-current.
                                       Prefix '+' adds Shift: ^+G ungroup,
                                       ^+Z redo.  ^O "path" opens that file,
                                       ^+S "path" saves to it.  ^F "name"
                                       switches to that floor, BARE ^F to the
                                       default (the roster's first), and
                                       ^+F "name" creates a floor (switches if
                                       it exists, so replays repeat cleanly).
                                       In the app Ctrl+F pops the floor
                                       selector, Ctrl+Shift+F is New floor.
                                       ^H "on"/"off" sets shuffle mode
                                       absolutely (what the recorder emits
                                       for any flip); BARE ^H toggles.
                                       In the app Ctrl+H is the toggle.
                                       The full set lives in CARET_SHORTCUTS —
                                       one row records AND replays a shortcut.
      Arrow nudge   LEFT RIGHT UP DOWN          (^ prefix = fine 1" step)
      Keys          ESC DEL ENTER
      Mouse         CLICK x y | ^CLICK x y (Ctrl) | RCLICK x y | MOVE x y |
                    CLICK x1 y1 DRAG x2 y2  (press-drag-release; ^CLICK for a
                    Ctrl-drag) | DRAG x1 y1 x2 y2 | PRESS x y | RELEASE x y
      Place / edit  PLACE kind x y [rot] | WALL x1 y1 x2 y2 [ext|int] |
                    DOOR x y code | WINDOW x y code | ROOM name x y |
                    SELECT x y | SELECTALL | DESELECT | ROTATE deg |
                    MOVETO x y | DELETE | ZOOMFIT
      Context menu  PUP x y [UP DOWN LEFT RIGHT ENTER ESC HOME END TAB
                    BACKSPACE DELETE | TYPE "..."]  pop up the right-click
                    menu and drive it AND any dialog it opens; TYPE enters
                    text into the dialog's field (ENTER selects/accepts)
      Files / shot  OPEN path | SAVE path | NEW | SHOT path | WAIT

    `run()` returns {ok, steps, log, errors, counts}; a bad token is recorded
    in `errors` and skipped, so one mistake doesn't abort the whole macro.
    """

    # single-char tool codes (mnemonic): Select Exterior Interior Door
    # Window Room.  Roof ridge is "G" -- "R" is Room's already, so it
    # reuses the tool's own toolbar shortcut (mainwindow.py's `defs`
    # table) instead of a new mnemonic.  The legacy 1-6 digits are still
    # accepted for old macros; roof ridge has no digit form (it postdates
    # that convention).
    _TOOL_CODES = {"S": TOOL_SELECT, "E": TOOL_WALL_EXT, "I": TOOL_WALL_INT,
                   "D": TOOL_DOOR, "W": TOOL_WINDOW, "R": TOOL_ROOM,
                   "G": TOOL_ROOF_RIDGE}
    _DIGIT_TOOLS = [TOOL_SELECT, TOOL_WALL_EXT, TOOL_WALL_INT,
                    TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM]
    _TOOL_NAMES = {"select": TOOL_SELECT, "extwall": TOOL_WALL_EXT,
                   "intwall": TOOL_WALL_INT, "door": TOOL_DOOR,
                   "window": TOOL_WINDOW, "room": TOOL_ROOM,
                   "roofridge": TOOL_ROOF_RIDGE}
    # derived from THE TABLE — add rows there, never here
    _CARET_METHODS = {t: s["method"] for t, s in CARET_SHORTCUTS.items()
                      if s["method"]}
    _ARROWS = {"LEFT": (-1, 0), "RIGHT": (1, 0), "UP": (0, -1), "DOWN": (0, 1)}
    # keys that drive a popped-up menu / modal dialog after a PUP token
    _MENU_KEYS = {"UP": Qt.Key.Key_Up, "DOWN": Qt.Key.Key_Down,
                  "LEFT": Qt.Key.Key_Left, "RIGHT": Qt.Key.Key_Right,
                  "ENTER": Qt.Key.Key_Return, "ESC": Qt.Key.Key_Escape,
                  "HOME": Qt.Key.Key_Home, "END": Qt.Key.Key_End,
                  "TAB": Qt.Key.Key_Tab, "BACKSPACE": Qt.Key.Key_Backspace,
                  "DELETE": Qt.Key.Key_Delete}
    _MODAL_DELAY = 20          # ms between keys fed to a menu / modal dialog

    def __init__(self, win):
        self.win = win
        self.log = []
        self.errors = []
        self.steps = 0

    # -- public --------------------------------------------------------------
    def run(self, text: str) -> dict:
        toks = self._tokenize(text)
        i = 0
        while i < len(toks):
            raw = toks[i]
            i += 1
            try:
                i = self._dispatch(raw, toks, i)
                self.steps += 1
                self.log.append(f"ok  {raw}")
            except Exception as ex:                       # noqa: BLE001
                self.errors.append(f"{raw}: {ex}")
                self.log.append(f"ERR {raw}: {ex}")
            QApplication.processEvents()
        return {"ok": not self.errors, "steps": self.steps,
                "log": self.log, "errors": self.errors,
                "counts": self.win.scene_summary()["counts"]}

    # -- tokenizing / args ---------------------------------------------------
    @staticmethod
    def _tokenize(text: str):
        out = []
        for line in str(text).splitlines():
            line = line.split("#", 1)[0]
            for m in re.finditer(r'"([^"]*)"|(\S+)', line):
                out.append(m.group(1) if m.group(1) is not None else m.group(2))
        return out

    @staticmethod
    def _num(tok: str) -> float:
        return parse_feet(tok) if ("'" in tok or '"' in tok) else float(tok)

    def _take(self, toks, i, n):
        if i + n > len(toks):
            raise ValueError(f"expected {n} more argument(s)")
        return toks[i:i + n], i + n

    # -- dispatch ------------------------------------------------------------
    def _dispatch(self, raw, toks, i):
        cmd = raw.upper()
        if cmd == "CLICK":
            return self._do_click(toks, i, ctrl=False)
        if cmd == "^CLICK":
            return self._do_click(toks, i, ctrl=True)
        if raw.startswith("^"):
            return self._caret(raw[1:], toks, i)
        if len(cmd) == 1 and cmd in self._TOOL_CODES:
            self.win.set_tool(self._TOOL_CODES[cmd])
            return i
        if len(raw) == 1 and raw in "123456":           # legacy digit tools
            self.win.set_tool(self._DIGIT_TOOLS[int(raw) - 1])
            return i
        if cmd in self._ARROWS:                  # coarse nudge of the selection
            dx, dy = self._ARROWS[cmd]
            self.win.nudge_selected(dx, dy, fine=False)
            return i
        if cmd == "ESC":
            self.win.view.cancel_temp()
            return i
        if cmd == "ENTER":
            self._key(Qt.Key.Key_Return, text="\r")
            return i
        if cmd in ("DEL", "DELETE"):
            self.win.delete_selected()
            return i

        handler = getattr(self, f"_cmd_{cmd.lower()}", None)
        if handler is None:
            raise ValueError("unknown command")
        return handler(toks, i)

    def _caret(self, key, toks, i):
        key = key.upper()
        if key in self._ARROWS:                  # ^LEFT = fine (1") nudge
            dx, dy = self._ARROWS[key]
            self.win.nudge_selected(dx, dy, fine=True)
            return i
        if key == "S":
            if not self.win.current_path:
                # a recorded Ctrl+S with no file falls through to Save As in
                # the app, and the recorder emits the '^+S "path"' that
                # follows -- skip rather than fail the whole macro
                self.win.status("^S skipped: no current file")
                return i
            self.win.save_path(self.win.current_path)
            return i
        if key in ("O", "+S"):
            # ^O "path" / ^+S "path" -- what the recorder emits when
            # File > Open / Save As completes: the chosen file is part of
            # the token, so replay needs no dialog (the on_place/on_room
            # pattern)
            (path,), i = self._take(toks, i, 1)
            if key == "O":
                self.win.load_path(path)
            else:
                self.win.save_path(path)
            return i
        if key == "F":
            # ^F "name" -- what the recorder emits for ANY floor switch:
            # the RESULTING floor rides in the token, so replay is
            # deterministic however the user got there. BARE ^F (next token
            # names no existing floor, or is absent) returns to the DEFAULT
            # floor -- the roster's first, whatever it was renamed to.
            if i < len(toks) and self.win._floor(toks[i]) is not None:
                self.win.switch_floor(toks[i])
                return i + 1
            self.win.switch_floor(self.win.default_floor_name())
            return i
        if key == "+F":
            # ^+F "name" -- New floor. IDEMPOTENT on replay: a floor that
            # already exists is switched to rather than failing, so a
            # recorded session replays again and again (the mini-gate loop)
            (name,), i = self._take(toks, i, 1)
            if self.win._floor(name) is None:
                self.win.new_floor_named(name)
            else:
                self.win.switch_floor(name)
            return i
        if key == "H":
            # ^H "on"/"off" -- what the recorder emits for ANY shuffle flip
            # (toolbar click or Ctrl+H): the RESULTING state rides in the
            # token (the ^F pattern), so replay is absolute and idempotent.
            # BARE ^H toggles, for hand-written macros.
            if i < len(toks) and toks[i].lower() in ("on", "off"):
                self.win.set_shuffle_mode(toks[i].lower() == "on")
                return i + 1
            self.win.toggle_shuffle()
            return i
        if key == "A":
            self._select_all()
            return i
        meth = self._CARET_METHODS.get(key)
        if meth is None:
            raise ValueError("unknown shortcut")
        getattr(self.win, meth)()
        return i

    # -- input synthesis -----------------------------------------------------
    def _vpos(self, x, y):
        return self.win.view.mapFromScene(QPointF(x, y))

    def _mouse(self, etype, x, y, button, buttons,
               mods=Qt.KeyboardModifier.NoModifier):
        vp = self.win.view.viewport()
        pos = self._vpos(x, y)
        ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                         button, buttons, mods)
        QApplication.sendEvent(vp, ev)
        QApplication.processEvents()

    def _click(self, x, y, button=Qt.MouseButton.LeftButton,
               mods=Qt.KeyboardModifier.NoModifier):
        self._mouse(QEvent.Type.MouseButtonPress, x, y, button, button, mods)
        self._mouse(QEvent.Type.MouseButtonRelease, x, y, button,
                    Qt.MouseButton.NoButton, mods)

    def _drag(self, x1, y1, x2, y2, mods=Qt.KeyboardModifier.NoModifier):
        # press at the start, move (so the app sees a drag), release at the
        # end — the modifier rides every event so Ctrl-drags reproduce.
        left = Qt.MouseButton.LeftButton
        self._mouse(QEvent.Type.MouseButtonPress, x1, y1, left, left, mods)
        self._mouse(QEvent.Type.MouseMove, (x1 + x2) / 2, (y1 + y2) / 2,
                    Qt.MouseButton.NoButton, left, mods)
        self._mouse(QEvent.Type.MouseMove, x2, y2,
                    Qt.MouseButton.NoButton, left, mods)
        self._mouse(QEvent.Type.MouseButtonRelease, x2, y2, left,
                    Qt.MouseButton.NoButton, mods)

    def _key(self, key, mods=Qt.KeyboardModifier.NoModifier, text=""):
        view = self.win.view
        QApplication.sendEvent(
            view, QKeyEvent(QEvent.Type.KeyPress, key, mods, text))
        QApplication.sendEvent(
            view, QKeyEvent(QEvent.Type.KeyRelease, key, mods, text))
        QApplication.processEvents()

    def _select_all(self):
        self.win.scene.clearSelection()
        for it in self.win.scene.items():
            if isinstance(it, (WallItem, FurnishingItem, GroupItem)) \
                    and it.group() is None:
                it.setSelected(True)

    # -- command handlers (one per token) ------------------------------------
    def _cmd_tool(self, toks, i):
        (name,), i = self._take(toks, i, 1)
        self.win.set_tool(self._TOOL_NAMES[name.lower()])
        return i

    def _do_click(self, toks, i, ctrl):
        """CLICK / ^CLICK x y.  If the next token is DRAG, the click is the
        START of a drag (press at the click point, drag to the DRAG point,
        release) — so a Ctrl-drag reads ``^CLICK x1 y1 DRAG x2 y2``."""
        (x, y), i = self._take(toks, i, 2)
        x, y = self._num(x), self._num(y)
        mods = (Qt.KeyboardModifier.ControlModifier if ctrl
                else Qt.KeyboardModifier.NoModifier)
        if i < len(toks) and toks[i].upper() == "DRAG":
            (ex, ey), i = self._take(toks, i + 1, 2)   # DRAG end point only
            self._drag(x, y, self._num(ex), self._num(ey), mods)
        else:
            self._click(x, y, mods=mods)
        return i

    def _cmd_rclick(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._click(self._num(x), self._num(y), Qt.MouseButton.RightButton)
        return i

    def _cmd_move(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._mouse(QEvent.Type.MouseMove, self._num(x), self._num(y),
                    Qt.MouseButton.NoButton, Qt.MouseButton.NoButton)
        return i

    def _cmd_press(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._mouse(QEvent.Type.MouseButtonPress, self._num(x), self._num(y),
                    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        return i

    def _cmd_release(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        self._mouse(QEvent.Type.MouseButtonRelease, self._num(x), self._num(y),
                    Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton)
        return i

    def _cmd_drag(self, toks, i):
        # standalone 4-arg DRAG x1 y1 x2 y2 (a following DRAG after CLICK is
        # consumed by _do_click as a 2-arg continuation instead)
        (x1, y1, x2, y2), i = self._take(toks, i, 4)
        self._drag(*map(self._num, (x1, y1, x2, y2)))
        return i

    def _cmd_place(self, toks, i):
        kind = toks[i]
        (x, y), j = self._take(toks, i + 1, 2)
        i = j
        rot = 0.0
        if i < len(toks) and self._is_num(toks[i]):
            rot = self._num(toks[i])
            i += 1
        if furnishing_spec(kind) is None:
            raise ValueError(f"unknown furnishing '{kind}'")
        item = make_furnishing(kind, grid_snap(QPointF(self._num(x),
                                                       self._num(y))), rot)
        self.win.scene.addItem(item)
        return i

    def _cmd_wall(self, toks, i):
        (x1, y1, x2, y2), i = self._take(toks, i, 4)
        wtype = "exterior"
        if i < len(toks) and toks[i].lower() in (
                "ext", "exterior", "int", "interior"):
            wtype = "interior" if toks[i].lower().startswith("int") \
                else "exterior"
            i += 1
        w = WallItem(QPointF(self._num(x1), self._num(y1)),
                     QPointF(self._num(x2), self._num(y2)), wtype)
        self.win.scene.addItem(w)
        rebuild_all_walls(self.win.scene)
        return i

    def _cmd_door(self, toks, i):
        return self._opening(toks, i, "door")

    def _cmd_window(self, toks, i):
        return self._opening(toks, i, "window")

    def _opening(self, toks, i, kind):
        (x, y, code), i = self._take(toks, i, 3)
        pt = QPointF(self._num(x), self._num(y))
        wall = next((it for it in self.win.scene.items(pt)
                     if isinstance(it, WallItem)), None)
        if wall is None:
            raise ValueError(f"no wall at ({x}, {y})")
        w, _h = parse_wwhh(code)
        if w > wall.length():
            raise ValueError(f"{kind} too wide for the wall")
        s = min(max(round(wall.s_of(pt)), w / 2), wall.length() - w / 2)
        op = OpeningItem(wall, kind, code, s)
        wall.openings.append(op)
        rebuild_all_walls(self.win.scene)
        return i

    def _cmd_room(self, toks, i):
        (name, x, y), i = self._take(toks, i, 3)
        res = detect_room(self.win.scene, QPointF(self._num(x), self._num(y)))
        if res is None:
            raise ValueError("no enclosed area at that point")
        room = RoomItem(name, QPointF(self._num(x), self._num(y)),
                        res[0], res[1], corners=res[2])
        self.win.scene.addItem(room)
        bind_room_walls(self.win.scene, room)
        return i

    def _cmd_select(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        pt = QPointF(self._num(x), self._num(y))
        self.win.scene.clearSelection()
        # THE PRIORITY RULE LIVES IN ONE PLACE NOW (D53, 2026-08-08). This
        # function used to carry its own: "prefer an editable item (furnishing
        # / wall / group) over a room, whose label can sit on top of what you
        # meant to grab" -- written long before that record, for exactly its
        # reason, and quietly correct all along. `items.hit_target` GENERALISES
        # it, so this calls it rather than restating it. Two priority rules in
        # one codebase drift, and the drift presents as "sometimes clicking
        # picks the wrong thing", which is close to undebuggable.
        #
        # DIFFERENTIAL, since this is not a pure refactor: the old rule took
        # the FIRST hit (topmost by z) that was one of three types; the new one
        # ranks by TYPE first and uses z only to break ties within a type. Where
        # a wall paints over a furnishing, this now picks the furnishing. That
        # is the intended generalisation -- the specific item wins -- and it is
        # the same answer the UI gives, which it previously did not.
        pick = hit_target(self.win.scene, pt)
        if pick is not None and not (
                pick.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
            pick = next((it for it in self.win.scene.items(pt) if it.flags()
                         & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable),
                        None)
        if pick is not None:
            pick.setSelected(True)
        return i

    def _cmd_selectall(self, toks, i):
        self._select_all()
        return i

    def _cmd_deselect(self, toks, i):
        self.win.scene.clearSelection()
        return i

    def _cmd_rotate(self, toks, i):
        (deg,), i = self._take(toks, i, 1)
        deg = self._num(deg)
        for it in self.win.scene.selectedItems():
            if isinstance(it, FurnishingItem):
                it.setRotation((it.rotation() + deg) % 360.0)
        return i

    def _cmd_moveto(self, toks, i):
        (x, y), i = self._take(toks, i, 2)
        x, y = self._num(x), self._num(y)
        sel = [it for it in self.win.scene.selectedItems()
               if isinstance(it, (FurnishingItem, GroupItem))]
        if not sel:
            raise ValueError("nothing selected to move")
        base = sel[0]
        dx, dy = x - base.pos().x(), y - base.pos().y()
        for it in sel:
            it.setPos(it.pos().x() + dx, it.pos().y() + dy)
            if isinstance(it, GroupItem):
                it.bake()
        return i

    def _cmd_zoomfit(self, toks, i):
        self.win.zoom_fit()
        QApplication.processEvents()
        return i

    def _cmd_pup(self, toks, i):
        """PUP x y [nav/edit/TYPE...] — pop up the context (right-click) menu
        at a scene point, then drive it (and any modal dialog it opens) with
        the tokens that follow:

          nav/edit keys  UP DOWN LEFT RIGHT ENTER ESC HOME END TAB
                         BACKSPACE DELETE
          text           TYPE "..."   (typed into the active line edit)

        e.g. resize a door:  ``PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER``
        The tokens are consumed here (the menu/dialog is only open during this
        step); ENTER selects/accepts, ESC cancels.  A bare PUP just opens and
        cancels the menu."""
        (x, y), i = self._take(toks, i, 2)
        x, y = self._num(x), self._num(y)
        actions = []
        while i < len(toks):
            t = toks[i].upper()
            if t == "TYPE":
                if i + 1 >= len(toks):
                    break
                actions.append(("text", toks[i + 1]))
                i += 2
            elif t in self._MENU_KEYS:
                actions.append(("key", self._MENU_KEYS[t]))
                i += 1
            else:
                break
        self._popup(x, y, actions)
        return i

    def _popup(self, x, y, actions):
        # arm the key pump to run inside the menu/dialog modal loop(s), then
        # raise the context menu (which blocks in exec() until it all closes)
        self._modal_queue = list(actions)
        QTimer.singleShot(0, self._modal_step)
        vp = self.win.view.viewport()
        pos = self.win.view.mapFromScene(QPointF(x, y))
        ev = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos,
                               vp.mapToGlobal(pos))
        QApplication.sendEvent(vp, ev)
        QApplication.processEvents()

    def _modal_step(self):
        """Feed one queued action to the currently-active menu/dialog.  Runs
        from a timer so it threads through nested exec() loops; reschedules
        BEFORE sending (a key may open another modal that blocks here)."""
        popup = QApplication.activePopupWidget()
        modal = QApplication.activeModalWidget()
        if popup is None and modal is None:
            self._modal_queue = []                 # interaction ended
            return
        if not self._modal_queue:
            (popup or modal).close()               # nothing left -> cancel
            return
        kind, val = self._modal_queue.pop(0)
        QTimer.singleShot(self._MODAL_DELAY, self._modal_step)
        # a popup MENU handles nav keys itself (it may not hold Qt focus, esp.
        # on Windows), so target it directly; a modal DIALOG routes keys to its
        # text field — find it directly since focus may not be set the instant
        # the dialog opens
        if popup is not None:
            target = popup
        else:
            target = (modal.findChild(QLineEdit)
                      or QApplication.focusWidget() or modal)
        if kind == "key":
            self._send_key(target, val)
        else:
            for ch in val:
                self._send_key(target, self._char_key(ch), ch)
        QApplication.processEvents()

    @staticmethod
    def _char_key(ch):
        seq = QKeySequence(ch)
        return Qt.Key(seq[0].key()) if seq.count() else Qt.Key.Key_unknown

    @staticmethod
    def _send_key(widget, key, text=""):
        for et in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            QApplication.sendEvent(widget, QKeyEvent(
                et, key, Qt.KeyboardModifier.NoModifier, text))

    def _cmd_type(self, toks, i):
        # stand-alone TYPE "text" -> type into whatever currently has focus
        (text,), i = self._take(toks, i, 1)
        target = QApplication.focusWidget()
        if target is not None:
            for ch in text:
                self._send_key(target, self._char_key(ch), ch)
        return i

    def _cmd_open(self, toks, i):
        (path,), i = self._take(toks, i, 1)
        self.win.load_path(path)
        return i

    def _cmd_save(self, toks, i):
        (path,), i = self._take(toks, i, 1)
        self.win.save_path(path)
        return i

    def _cmd_new(self, toks, i):
        self.win.clear_plan()
        return i

    def _cmd_shot(self, toks, i):
        (path,), i = self._take(toks, i, 1)
        if not self.win.export_canvas(path):
            raise ValueError("export failed")
        return i

    def _cmd_wait(self, toks, i):
        for _ in range(3):
            QApplication.processEvents()
        return i

    @staticmethod
    def _is_num(tok: str) -> bool:
        try:
            MacroRunner._num(tok)
            return True
        except ValueError:
            return False


class MacroRecorderDialog(QDialog):
    """A non-modal window that records mouse/keyboard/tool actions performed
    in the FloorPlanner window as macro tokens, lets you edit them, replay a
    selected portion, and Save As a .fpm file.

    Workflow: **Start**, switch to the plan window and interact (draw walls,
    drop furnishings, copy/paste, nudge…), come back and **Stop**.  Select
    any part of the recorded text and **Replay** to watch it run; **Save As…**
    to keep it.  The grammar is the same as `MacroRunner` / `fp_macro.py`.
    """

    MOVE_THRESHOLD = 4.0          # scene inches; a shorter drag becomes a CLICK
    # derived from THE TABLE (CARET_SHORTCUTS) — add rows there, never here
    _CARET_KEYS = {s["key"]: t for t, s in CARET_SHORTCUTS.items()
                   if not t.startswith("+")}
    _ARROW_KEYS = {Qt.Key.Key_Left: "LEFT", Qt.Key.Key_Right: "RIGHT",
                   Qt.Key.Key_Up: "UP", Qt.Key.Key_Down: "DOWN"}
    _TOOL_CODES = {TOOL_SELECT: "S", TOOL_WALL_EXT: "E", TOOL_WALL_INT: "I",
                   TOOL_DOOR: "D", TOOL_WINDOW: "W", TOOL_ROOM: "R",
                   TOOL_ROOF_RIDGE: "G"}

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Macro Recorder / Debug")
        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self._recording = False
        self._paused = False
        self._press_scene = None
        self._press_moved = False
        self._press_tool = TOOL_SELECT
        self._press_ctrl = False
        self._type_buffer = ""           # printable run while a modal is open
        self._modal_line = False         # a PUP + its menu/dialog keys, 1 line
        self._last_key_ev = None         # de-dupe doubled key deliveries
        self._last_key_sig = None        # (timestamp, key, mods) of last press
        self._pending_press = None       # (key, mods): override awaiting echo
        self._replay_lines = []
        self._replay_idx = 0

        self.edit = QPlainTextEdit()
        self.edit.setFont(QFont("DejaVu Sans Mono", 10))
        self.edit.setPlaceholderText(
            "Recorded macro tokens appear here.  Edit freely; select a "
            "portion and click Replay to run just that part.")

        self.nl_check = QCheckBox("New line after each mouse action")
        self.nl_check.setChecked(True)
        self.status_lbl = QLabel("Idle.")

        self.b_start = QPushButton("Start")
        self.b_pause = QPushButton("Pause")
        self.b_stop = QPushButton("Stop")
        self.b_load = QPushButton("Load…")
        self.b_replay = QPushButton("Replay")
        self.b_saveas = QPushButton("Save As…")
        self.b_cancel = QPushButton("Cancel")
        self.b_start.clicked.connect(self.start)
        self.b_pause.clicked.connect(self.toggle_pause)
        self.b_stop.clicked.connect(self.stop)
        self.b_load.clicked.connect(self.load_from)
        self.b_replay.clicked.connect(self.replay)
        self.b_saveas.clicked.connect(self.save_as)
        self.b_cancel.clicked.connect(self.cancel)
        self.edit.selectionChanged.connect(self._sync_buttons)
        self.edit.textChanged.connect(self._sync_buttons)

        row = QHBoxLayout()
        for b in (self.b_start, self.b_pause, self.b_stop, self.b_load,
                  self.b_replay, self.b_saveas, self.b_cancel):
            row.addWidget(b)
        lay = QVBoxLayout(self)
        lay.addWidget(self.edit)
        lay.addWidget(self.nl_check)
        lay.addLayout(row)
        lay.addWidget(self.status_lbl)
        self.resize(600, 440)

        self._replay_timer = QTimer(self)
        self._replay_timer.timeout.connect(self._replay_step)
        self._sync_buttons()

    # -- button state --------------------------------------------------------
    def _sync_buttons(self):
        rec, replaying = self._recording, self._replay_timer.isActive()
        self.b_start.setEnabled(not rec and not replaying)
        self.b_stop.setEnabled(rec)
        self.b_pause.setEnabled(rec)
        self.b_pause.setText("Resume" if self._paused else "Pause")
        self.b_load.setEnabled(not rec and not replaying)
        self.b_replay.setEnabled(self.edit.textCursor().hasSelection()
                                 and not rec and not replaying)
        self.b_saveas.setEnabled(bool(self.edit.toPlainText().strip()))

    # -- record --------------------------------------------------------------
    def start(self):
        if self._recording:
            return
        self._recording = True
        self._paused = False
        self._press_scene = None
        self._last_key_ev = None
        self._last_key_sig = None
        self.win._recorder = self
        app = QApplication.instance()
        app.removeEventFilter(self)        # ensure exactly one installation
        app.installEventFilter(self)
        self.status_lbl.setText(
            "Recording…  Interact with the FloorPlanner window, then Stop.")
        self._sync_buttons()
        self.win.raise_()
        self.win.activateWindow()

    def stop(self):
        if not self._recording:
            return
        self._end_modal_line()             # close any open PUP line
        QApplication.instance().removeEventFilter(self)
        self.win._recorder = None
        self._recording = False
        self._paused = False
        self._press_scene = None
        self.status_lbl.setText(
            "Stopped.  Select macro text and Replay, or Save As….")
        self.raise_()
        self.activateWindow()
        self._sync_buttons()

    def toggle_pause(self):
        if not self._recording:
            return
        self._paused = not self._paused
        self.status_lbl.setText("Paused." if self._paused else "Recording…")
        self._sync_buttons()

    def cancel(self):
        self.stop()
        self._replay_timer.stop()
        self.close()

    def closeEvent(self, e):
        self.stop()
        self._replay_timer.stop()
        super().closeEvent(e)

    # -- replay --------------------------------------------------------------
    def replay(self):
        cur = self.edit.textCursor()
        text = (cur.selection().toPlainText() if cur.hasSelection()
                else self.edit.toPlainText())
        # step one recorded line at a time so the canvas updates visibly
        self._replay_lines = [ln for ln in text.splitlines() if ln.strip()]
        self._replay_idx = 0
        if not self._replay_lines:
            return
        self.status_lbl.setText("Replaying…")
        self.win.raise_()
        self._replay_timer.start(180)
        self._sync_buttons()

    def _replay_step(self):
        if self._replay_idx >= len(self._replay_lines):
            self._replay_timer.stop()
            self.status_lbl.setText("Replay complete.")
            self._sync_buttons()
            return
        line = self._replay_lines[self._replay_idx]
        self._replay_idx += 1
        res = self.win.run_macro(line)
        if res["errors"]:
            self.status_lbl.setText("Replay: " + "; ".join(res["errors"][:2]))

    # -- load ----------------------------------------------------------------
    def load_from(self):
        """Load a saved .fpm into the editor and SELECT IT WHOLE, so Replay
        is one click away -- the load-then-replay loop the P4.2 mini-gate
        runs (record once, replay against a fresh plan again and again)."""
        if self._recording or self._replay_timer.isActive():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Load macro", str(designs_dir()),
            "Macro files (*.fpm *.txt);;All files (*)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as fh:
                self.edit.setPlainText(fh.read())
        except OSError as ex:
            QMessageBox.critical(self, "Load failed", str(ex))
            return
        self.edit.selectAll()
        self.status_lbl.setText(f"Loaded {path} — click Replay to run it.")
        self._sync_buttons()

    # -- save ----------------------------------------------------------------
    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save macro", str(designs_dir() / "macro.fpm"),
            "Macro files (*.fpm *.txt);;All files (*)")
        if not path:
            return
        try:
            self._write_macro(path)
        except OSError as ex:
            QMessageBox.critical(self, "Save failed", str(ex))

    def _write_macro(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.edit.toPlainText())
        self.status_lbl.setText(f"Saved {path}")

    # -- hooks called by the instrumented app --------------------------------
    def on_tool(self, tool):
        if self._active():
            self._end_modal_line()
            code = self._TOOL_CODES.get(tool)
            if code:
                self._append(code)

    def on_place(self, kind, scene_pt):
        if self._active():
            self._end_modal_line()
            self._append(f"PLACE {kind} {round(scene_pt.x())} "
                         f"{round(scene_pt.y())}",
                         newline=self.nl_check.isChecked())

    def on_popup(self, scene_pt):
        # PUP keeps the menu's nav/text keys on the SAME line; the line is
        # ended (newline) when the modal closes and the next action arrives
        if self._active():
            self._end_modal_line()
            self._append(f"PUP {round(scene_pt.x())} {round(scene_pt.y())}")
            self._modal_line = True

    def on_opening(self, kind, scene_pt, code):
        # door/window size came from a dialog, not keystrokes — capture the
        # value into a self-contained DOOR/WINDOW token so replay needs no
        # dialog (the raw click for this tool is suppressed in _capture).
        if self._active():
            self._end_modal_line()
            tok = "DOOR" if kind == "door" else "WINDOW"
            self._append(f"{tok} {round(scene_pt.x())} {round(scene_pt.y())} "
                         f"{code}", newline=self.nl_check.isChecked())

    def on_open(self, path):
        # the file came from a modal QFileDialog the event stream cannot
        # see -- capture it into a self-contained "^O path" token, exactly
        # the on_opening/on_room pattern, so replay needs no dialog
        if self._active():
            self._end_modal_line()
            self._append(f'^O "{path}"', newline=True)

    def on_save_as(self, path):
        # File > Save As (or a first Ctrl+S falling through to it): the
        # chosen file rides in the token, same as on_open
        if self._active():
            self._end_modal_line()
            self._append(f'^+S "{path}"', newline=True)

    def on_shuffle(self, on):
        # a shuffle flip, from ANY route (toolbar click or Ctrl+H): the
        # RESULTING state rides in the token (the on_floor pattern), so
        # replay is absolute however the user flipped it. Row 37's fix --
        # before this, a replayed session that toggled shuffle replayed in
        # the wrong mode, silently.
        if self._active():
            self._end_modal_line()
            self._append(f'^H "{"on" if on else "off"}"', newline=True)

    def on_floor(self, name):
        # a floor switch, from ANY route. Through the blank-canvas POPUP the
        # PUP tokens already replay the switch, so the deterministic
        # equivalent rides the SAME LINE as a comment --
        #     PUP 200 300 DOWN ENTER # ^F "Top Floor"
        # -- every other route records the real token.
        if self._active():
            if self._modal_line:
                self._append(f'# ^F "{name}"')
                self._end_modal_line()
            else:
                self._end_modal_line()
                self._append(f'^F "{name}"', newline=True)

    def on_new_floor(self, name):
        # New floor: the typed name rides in the token (the dialog is modal;
        # the event stream cannot see it)
        if self._active():
            self._end_modal_line()
            self._append(f'^+F "{name}"', newline=True)

    def on_room(self, name, scene_pt):
        # room name came from a dialog — capture it into a ROOM token.
        if self._active():
            self._end_modal_line()
            tok = f'"{name}"' if " " in name else name
            self._append(f"ROOM {tok} {round(scene_pt.x())} "
                         f"{round(scene_pt.y())}",
                         newline=self.nl_check.isChecked())

    # -- live capture (application event filter) -----------------------------
    def _active(self) -> bool:
        return self._recording and not self._paused

    def eventFilter(self, obj, ev):
        if self._active():
            try:
                self._capture(obj, ev)
            except Exception:                          # noqa: BLE001
                pass                                   # capture never breaks UI
        return False                                   # never consume events

    def _capture(self, obj, ev):
        et = ev.type()
        if et == QEvent.Type.KeyRelease:
            self._last_key_ev = None       # a press/release pair completed
            self._last_key_sig = None
            self._pending_press = None
            return
        # KEY EVENTS FIRST, BY TYPE (P4.2): the canvas keyboard focus sits on
        # the VIEWPORT, and the old `obj is viewport` mouse branch came first
        # -- so every canvas keystroke fell into it and was dropped, which is
        # why recordings had mouse lines only. An event's disposition is its
        # TYPE's, never the receiving object's.
        if et in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
            self._capture_key(obj, ev)
            return
        if obj is self.win.view.viewport():
            if et == QEvent.Type.MouseButtonPress and \
                    ev.button() == Qt.MouseButton.LeftButton:
                self._press_scene = self.win.view.mapToScene(
                    ev.position().toPoint())
                self._press_moved = False
                self._press_tool = self.win.tool       # tool at press time
                self._press_ctrl = bool(ev.modifiers()
                                        & Qt.KeyboardModifier.ControlModifier)
            elif et == QEvent.Type.MouseMove and self._press_scene is not None \
                    and (ev.buttons() & Qt.MouseButton.LeftButton):
                self._press_moved = True
            elif et == QEvent.Type.MouseButtonRelease and \
                    ev.button() == Qt.MouseButton.LeftButton and \
                    self._press_scene is not None:
                end = self.win.view.mapToScene(ev.position().toPoint())
                # door/window/room clicks are recorded by their dedicated
                # hooks (with the dialog value), so skip the raw click here
                if self._press_tool not in (TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM):
                    self._emit_mouse(self._press_scene, end,
                                     self._press_moved, self._press_ctrl)
                self._press_scene = None
            elif et == QEvent.Type.ContextMenu:
                # a right-click context menu -> PUP x y (nav keys captured
                # below while the menu is open)
                sp = self.win.view.mapToScene(ev.pos())
                self.on_popup(sp)
    def _capture_key(self, obj, ev):
        # ShortcutOverride TOO (P4.2): a keystroke that matches a menu
        # QAction shortcut — Ctrl+G group, Ctrl+Shift+G ungroup, Del,
        # Ctrl+Z/X/C/V — is consumed by Qt's shortcut system and never
        # arrives as a KeyPress, so recordings silently lacked exactly
        # the plan-modifying shortcuts. ShortcutOverride is delivered to
        # this filter for EVERY keystroke, before matching, carrying the
        # same key and modifiers.
        #
        # de-dupe: one physical key press can reach this filter more than
        # once — ShortcutOverride precedes an unmatched key's KeyPress,
        # Qt propagates an unaccepted key up the parent chain, and a
        # popup/dialog re-dispatches it.  Skip a repeat of the same event
        # object, or (for real events) the same (timestamp, key, mods); a
        # KeyRelease resets this so genuine repeats still record.
        # ELIGIBILITY FIRST, STATE SECOND (P4.2, Patrick's Ctrl+G retest):
        # Qt delivers each key event at the QWindow level BEFORE the widget
        # level, and a QWindow never passes _belongs_to_main. The old order
        # set the de-dupe guards on that first, non-recordable delivery --
        # poisoning the widget-level delivery that follows, so a
        # shortcut-consumed chord (whose override is its only appearance)
        # recorded nothing. A delivery this filter will not emit from must
        # not touch the de-dupe state at all.
        in_modal = (QApplication.activePopupWidget() is not None
                    or QApplication.activeModalWidget() is not None)
        if not ((in_modal and self._modal_line)
                or (not in_modal and self._belongs_to_main(obj))):
            return
        et = ev.type()
        ts = ev.timestamp()
        sig = (ts, ev.key(), ev.modifiers())
        chord = (ev.key(), ev.modifiers())
        if et == QEvent.Type.ShortcutOverride and \
                self._pending_press == chord:
            # Qt synthesizes one ShortcutOverride per delivered press; a
            # second override of the SAME chord before any release is the
            # same physical keystroke arriving again -- one capture is it
            return
        if et == QEvent.Type.KeyPress and self._pending_press == chord:
            # the KeyPress echo of a ShortcutOverride already captured --
            # paired explicitly (programmatic and menu-dispatched events
            # carry timestamp 0, invisible to the sig de-dupe), and the
            # guards are PINNED to it so the same press object's further
            # propagation deliveries (viewport -> view -> window) skip too
            self._pending_press = None
            self._last_key_ev = ev
            self._last_key_sig = sig
            return
        if ev is self._last_key_ev or (ts and sig == self._last_key_sig):
            return
        self._last_key_ev = ev
        self._last_key_sig = sig
        if et == QEvent.Type.ShortcutOverride:
            self._pending_press = chord
        # modal keystrokes only for a PUP-opened menu/dialog; tool-driven
        # dialogs (door/window size, room name) already record their value
        # via on_opening/on_room, so don't double-capture them
        if in_modal:
            self._emit_modal_key(ev)
        else:
            self._emit_key(ev)

    def _emit_mouse(self, p1, p2, moved, ctrl):
        self._end_modal_line()
        # a click is "[^]CLICK x y"; a drag is the click START plus a DRAG end
        # point on the same line: "[^]CLICK x1 y1 DRAG x2 y2".  The '^' marks
        # the Ctrl modifier (e.g. Ctrl-drag a room name, or Ctrl+click toggle).
        x1, y1, x2, y2 = (round(p1.x()), round(p1.y()),
                          round(p2.x()), round(p2.y()))
        pre = "^CLICK" if ctrl else "CLICK"
        if moved and QLineF(p1, p2).length() >= self.MOVE_THRESHOLD:
            tok = f"{pre} {x1} {y1} DRAG {x2} {y2}"
        else:
            tok = f"{pre} {x1} {y1}"
        self._append(tok, newline=self.nl_check.isChecked())

    _MENU_KEY_TOKENS = {Qt.Key.Key_Up: "UP", Qt.Key.Key_Down: "DOWN",
                        Qt.Key.Key_Left: "LEFT", Qt.Key.Key_Right: "RIGHT",
                        Qt.Key.Key_Return: "ENTER", Qt.Key.Key_Enter: "ENTER",
                        Qt.Key.Key_Escape: "ESC", Qt.Key.Key_Home: "HOME",
                        Qt.Key.Key_End: "END", Qt.Key.Key_Tab: "TAB",
                        Qt.Key.Key_Backspace: "BACKSPACE",
                        Qt.Key.Key_Delete: "DELETE"}

    def _emit_modal_key(self, ev):
        # keystrokes while a PUP menu / modal dialog is open: named keys pass
        # through (no newline — stay on the PUP line); printable text is
        # buffered into a TYPE "..." run.
        tok = self._MENU_KEY_TOKENS.get(ev.key())
        if tok:
            self._flush_type()
            self._append(tok)
            return
        text = ev.text()
        if text and text.isprintable():
            self._type_buffer += text

    def _flush_type(self):
        if self._type_buffer:
            self._append(f'TYPE "{self._type_buffer}"')
            self._type_buffer = ""

    def _newline(self):
        if self.edit.toPlainText() and not self.edit.toPlainText().endswith("\n"):
            cur = self.edit.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End)
            cur.insertText("\n")
            self.edit.setTextCursor(cur)
            self.edit.ensureCursorVisible()

    def _end_modal_line(self):
        # close out a PUP line (flush any typed text, drop to a new line)
        if self._modal_line:
            self._flush_type()
            self._newline()
            self._modal_line = False

    def _emit_key(self, ev):
        self._end_modal_line()             # a modal closed -> end its line
        key, mods = ev.key(), ev.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        if key in self._ARROW_KEYS:
            self._append(("^" if ctrl else "") + self._ARROW_KEYS[key])
        elif key == Qt.Key.Key_Escape:
            self._append("ESC")
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._append("DEL")
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._append("ENTER")
        elif ctrl and key in self._CARET_KEYS:
            name = ("+" if shift else "") + self._CARET_KEYS[key]
            # only chords THE TABLE names record (Ctrl+Shift+C is nothing),
            # and hook-emitted tokens (^O, ^+S) are written by their app
            # hook WITH the chosen file -- a raw bare token here would
            # break replay, and a cancelled dialog would leave it stranded
            if name in CARET_SHORTCUTS and name not in CARET_HOOK_TOKENS:
                self._append("^" + name)

    def _belongs_to_main(self, obj) -> bool:
        """True if `obj` is the plan window or one of its children (not this
        recorder dialog), so we record canvas keystrokes but not text edits."""
        w = obj
        while w is not None:
            if w is self:
                return False
            if w is self.win:
                return True
            w = w.parent() if hasattr(w, "parent") else None
        return False

    def _append(self, token, newline=False):
        cur = self.edit.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        text = self.edit.toPlainText()
        sep = "" if (not text or text.endswith(("\n", " "))) else " "
        cur.insertText(sep + token + ("\n" if newline else ""))
        self.edit.setTextCursor(cur)
        self.edit.ensureCursorVisible()
