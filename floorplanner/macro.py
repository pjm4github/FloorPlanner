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
                                       ^+Z redo.
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
    # Window Room.  The legacy 1-6 digits are still accepted for old macros.
    _TOOL_CODES = {"S": TOOL_SELECT, "E": TOOL_WALL_EXT, "I": TOOL_WALL_INT,
                   "D": TOOL_DOOR, "W": TOOL_WINDOW, "R": TOOL_ROOM}
    _DIGIT_TOOLS = [TOOL_SELECT, TOOL_WALL_EXT, TOOL_WALL_INT,
                    TOOL_DOOR, TOOL_WINDOW, TOOL_ROOM]
    _TOOL_NAMES = {"select": TOOL_SELECT, "extwall": TOOL_WALL_EXT,
                   "intwall": TOOL_WALL_INT, "door": TOOL_DOOR,
                   "window": TOOL_WINDOW, "room": TOOL_ROOM}
    _CARET_METHODS = {"Z": "undo", "Y": "redo", "+Z": "redo",
                      "X": "cut_selected", "C": "copy_selected",
                      "V": "paste_clipboard", "G": "group_selected",
                      "+G": "ungroup_selected", "N": "clear_plan"}
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
            return self._caret(raw[1:], i)
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

    def _caret(self, key, i):
        key = key.upper()
        if key in self._ARROWS:                  # ^LEFT = fine (1") nudge
            dx, dy = self._ARROWS[key]
            self.win.nudge_selected(dx, dy, fine=True)
            return i
        if key == "S":
            if not self.win.current_path:
                raise ValueError("no current file — use 'SAVE path'")
            self.win.save_path(self.win.current_path)
            return i
        if key == "O":
            raise ValueError("use 'OPEN path' in a macro")
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
        hits = list(self.win.scene.items(QPointF(self._num(x), self._num(y))))
        self.win.scene.clearSelection()
        # prefer an editable item (furnishing / wall / group) over a room,
        # whose label can sit on top of what you meant to grab
        pick = next((it for it in hits
                     if isinstance(it, (FurnishingItem, WallItem, GroupItem))),
                    None)
        if pick is None:
            pick = next((it for it in hits if it.flags()
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
    _CARET_KEYS = {Qt.Key.Key_C: "C", Qt.Key.Key_V: "V", Qt.Key.Key_X: "X",
                   Qt.Key.Key_Z: "Z", Qt.Key.Key_Y: "Y", Qt.Key.Key_G: "G",
                   Qt.Key.Key_A: "A", Qt.Key.Key_N: "N", Qt.Key.Key_S: "S"}
    _ARROW_KEYS = {Qt.Key.Key_Left: "LEFT", Qt.Key.Key_Right: "RIGHT",
                   Qt.Key.Key_Up: "UP", Qt.Key.Key_Down: "DOWN"}
    _TOOL_CODES = {TOOL_SELECT: "S", TOOL_WALL_EXT: "E", TOOL_WALL_INT: "I",
                   TOOL_DOOR: "D", TOOL_WINDOW: "W", TOOL_ROOM: "R"}

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
        self.b_replay = QPushButton("Replay")
        self.b_saveas = QPushButton("Save As…")
        self.b_cancel = QPushButton("Cancel")
        self.b_start.clicked.connect(self.start)
        self.b_pause.clicked.connect(self.toggle_pause)
        self.b_stop.clicked.connect(self.stop)
        self.b_replay.clicked.connect(self.replay)
        self.b_saveas.clicked.connect(self.save_as)
        self.b_cancel.clicked.connect(self.cancel)
        self.edit.selectionChanged.connect(self._sync_buttons)
        self.edit.textChanged.connect(self._sync_buttons)

        row = QHBoxLayout()
        for b in (self.b_start, self.b_pause, self.b_stop, self.b_replay,
                  self.b_saveas, self.b_cancel):
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
        elif et == QEvent.Type.KeyPress:
            # de-dupe: one physical key press can reach this filter more than
            # once — Qt propagates an unaccepted key up the parent chain, and a
            # popup/dialog re-dispatches it.  Skip a repeat of the same event
            # object, or (for real events) the same (timestamp, key, mods); a
            # KeyRelease resets this so genuine repeats still record.
            ts = ev.timestamp()
            sig = (ts, ev.key(), ev.modifiers())
            if ev is self._last_key_ev or (ts and sig == self._last_key_sig):
                return
            self._last_key_ev = ev
            self._last_key_sig = sig
            in_modal = (QApplication.activePopupWidget() is not None
                        or QApplication.activeModalWidget() is not None)
            # only capture modal keystrokes for a PUP-opened menu/dialog;
            # tool-driven dialogs (door/window size, room name) already record
            # their value via on_opening/on_room, so don't double-capture them
            if in_modal and self._modal_line:
                self._emit_modal_key(ev)
            elif not in_modal and self._belongs_to_main(obj):
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
            self._append("^" + ("+" if shift else "") + self._CARET_KEYS[key])

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
