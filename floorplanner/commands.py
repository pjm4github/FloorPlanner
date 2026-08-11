"""P6.b — the command classes, at the SETTLED-GESTURE boundary.

**DORMANT BY DESIGN.** Nothing here is wired to a `QUndoStack`, no menu action
constructs one, and `MainWindow` does not import this module. Landing the
classes before the cutover is what makes P6.d a matter of swapping one trigger
rather than replacing a subsystem — measured at read-back 0008, which found that
the undo stack is driven by `scene.changed`, not by operations, so a command
layer and the debounce cannot both be live.

-- WHY THE BOUNDARY IS THE SETTLED GESTURE, AND NOT THE OPERATIONS INSIDE IT --

P6.1's original list named `MoveVertices`, `Extract` and `Join` as commands.
They are the *inside* of one gesture, not three gestures:

    A COMMAND THAT UNDID TO A MID-GESTURE STATE WOULD RESTORE SOMETHING NO
    INVARIANT SET DESCRIBES. MID-GESTURE THE ROOM IS FLOATING AND I12 GOVERNS
    WHERE I14 WOULD.

A placed room's label-drag IS `extract_room` -> move -> `join_room` (P4.2): six
sub-operations -- copy-trim, privatise vertices, translate, split landings, weld,
merge -- and the states between them are not documents. I12 exempts a floating
room from the very sharing I14 demands, so a stack that could stop between them
would offer the user a state the validator would reject if it were saved.

**The 180 ms debounce already draws that line** (`scene.changed` ->
`_mark_dirty` -> one-shot timer -> `_commit_if_changed`): one step per settled
gesture, whatever happened inside it. Phase 6 ADOPTS that boundary rather than
re-deciding it.

-- THE SHAPE, AND WHY IT IS STATE-BASED RATHER THAN OPERATION-BASED --

Each command carries the document BEFORE and AFTER its gesture, and applies one
or the other. That is what `snapshot()` + `_restore_state` already do, named per
gesture instead of per timer tick -- so the redo path is the code that is
already exercised on every undo today, rather than a second implementation of
every operation that would have to stay in step with it.

**The cost is a document per step and it is the SAME cost as today's stack**,
which holds exactly the same states; what changes is that a step is named, and
that `text()` can say what it was. An operation-inverse design would be cheaper
in memory and would require every gesture to grow a correct inverse -- which is
the thing this codebase has repeatedly measured itself not to have (D61, D62,
D65, D66: the join does something and no gesture un-does it).
"""
from PyQt6.QtGui import QUndoCommand


class GestureCommand(QUndoCommand):
    """One settled gesture, as a before/after pair of documents.

    `win` is the `MainWindow`; `before` and `after` are `snapshot()` documents.
    `redo()` is called by `QUndoStack` when the command is PUSHED as well as on
    a real redo, so the first call must be a no-op -- the gesture has already
    happened by the time the debounce settles and the command is built. That is
    the standard `QUndoCommand` contract and the trap in it; it is handled here
    once rather than in ten subclasses.
    """

    def __init__(self, win, before, after, text=""):
        super().__init__(text or self.__class__.__name__)
        self.win = win
        self.before = before
        self.after = after
        self._applied = True          # the gesture already ran -- see above

    def undo(self):
        self.win._restore_state(self.before)

    def redo(self):
        if not self._applied:
            self.win._restore_state(self.after)
        self._applied = False


# One class per SETTLED GESTURE, from the 14 public mutators that exist now
# (docs/evidence/phase6-readback-census.json). `Extract`/`Join`/`MoveVertices`
# are deliberately ABSENT -- they are inside DragGesture, and naming them as
# commands is the mistake the P6.1 re-cut exists to prevent.
class DeleteItems(GestureCommand):
    """`delete_selected`."""


class NudgeItems(GestureCommand):
    """`nudge_selected` -- arrow-key move."""


class AlignToGrid(GestureCommand):
    """`align_rooms_to_grid`."""


class DistributeRooms(GestureCommand):
    """`distribute_rooms`."""


class RedetectRooms(GestureCommand):
    """`refresh_rooms_cmd`."""


class RoomBoolean(GestureCommand):
    """`room_boolean` -- combine / intersect / subtract / fragment."""


class Group(GestureCommand):
    """`group_selected`."""


class Ungroup(GestureCommand):
    """`ungroup_selected`."""


class CoalesceAll(GestureCommand):
    """`coalesce_all_now` -- absent from the Phase 0 list entirely."""


class CutItems(GestureCommand):
    """`cut_selected`."""


class PasteItems(GestureCommand):
    """`paste_clipboard`."""


class DragGesture(GestureCommand):
    """THE DRAG -- absent from the Phase 0 list, and the commonest mutation in
    the application.

    It is not a `MainWindow` method: it lives in the items' event handlers,
    which is exactly why a menu-shaped list missed it. **A command layer that
    covered the menu and not the drag would leave the principal gesture outside
    undo**, which is D53's seam again -- two layers each correctly covered, and
    nothing covering what runs between them.

    One command for the whole drag, INCLUDING a room label-drag's
    extract -> move -> join, per the boundary argument in this module's
    docstring.
    """


#: Every gesture command, so a test can assert the set rather than a sample --
#: a list that drifts from the classes is the census-by-spelling problem in
#: miniature.
GESTURE_COMMANDS = (DeleteItems, NudgeItems, AlignToGrid, DistributeRooms,
                    RedetectRooms, RoomBoolean, Group, Ungroup, CoalesceAll,
                    CutItems, PasteItems, DragGesture)
