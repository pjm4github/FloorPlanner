"""P6.b -- the command classes at the SETTLED-GESTURE boundary, DORMANT.

Nothing here is wired: the point of landing the classes before the cutover is
that P6.d becomes a matter of swapping one trigger. These tests pin the shape
and, crucially, pin that the layer is NOT live -- because "dormant" is a claim
that decays silently if nothing asserts it.
"""
import pytest

from floorplanner.commands import GESTURE_COMMANDS, DragGesture, GestureCommand

pytestmark = pytest.mark.io


def test_the_command_layer_is_dormant():
    """P6.b lands the classes and wires NOTHING. Asserted, because a dormant
    layer that quietly becomes live is exactly the state the cutover exists to
    make deliberate -- and read-back 0008 measured that a command stack and the
    180 ms debounce cannot both be live without double-recording every step."""
    import floorplanner.mainwindow as mw
    src = open(mw.__file__, encoding="utf-8").read()
    assert "floorplanner.commands" not in src and "from .commands" not in src, \
        "mainwindow imports the command layer -- that is the CUTOVER (P6.d), " \
        "not P6.b, and it must be a deliberate step with Patrick's check"


def test_every_gesture_command_is_registered():
    """The roster and the classes must not drift. A test that sampled a few
    would pass while a new command went unregistered -- the census-by-spelling
    problem one layer up."""
    import floorplanner.commands as cmds
    defined = {v for v in vars(cmds).values()
               if isinstance(v, type) and issubclass(v, GestureCommand)
               and v is not GestureCommand}
    assert defined == set(GESTURE_COMMANDS), (
        f"GESTURE_COMMANDS is out of step with the module: "
        f"only-in-roster={set(GESTURE_COMMANDS) - defined}, "
        f"only-defined={defined - set(GESTURE_COMMANDS)}")


def test_no_sub_operation_commands_exist():
    """THE BOUNDARY, ASSERTED RATHER THAN DOCUMENTED.

    P6.1's original list named `MoveVertices`, `Extract` and `Join`. A command
    that undid to a mid-gesture state would restore something NO INVARIANT SET
    DESCRIBES -- mid-gesture the room is FLOATING and I12 governs where I14
    would. This fails the moment someone adds one back, which is the point:
    the argument lives in the plan, and this is what enforces it.
    """
    banned = {"MoveVertices", "Extract", "Join", "SplitWall", "WeldEnds",
              "MergeWall"}
    names = {c.__name__ for c in GESTURE_COMMANDS}
    assert not (names & banned), (
        f"{sorted(names & banned)} is a SUB-OPERATION, not a settled gesture. "
        f"See P6.1's re-cut in docs/V5_MIGRATION_PLAN.md.")


def test_the_drag_is_covered():
    """The commonest mutation in the app, and the one a menu-shaped list
    misses: the drag is not a MainWindow method, it lives in the items' event
    handlers. Leaving it out would be D53's seam again."""
    assert DragGesture in GESTURE_COMMANDS


def test_redo_is_a_noop_when_the_gesture_already_ran(fp, win):
    """`QUndoStack` calls `redo()` on PUSH as well as on a real redo, and by
    then the gesture has already happened -- the debounce is what tells us it
    settled. A subclass that re-applied on push would double-apply every
    gesture, so the contract is handled once in the base class and pinned here.
    """
    applied = []
    cmd = GestureCommand(win, {"before": 1}, {"after": 1}, "default", "test")
    win._restore_state = lambda state: applied.append(state)

    cmd.redo()                                   # the push
    assert applied == [], "redo() re-applied a gesture that had already run"

    cmd.undo()
    assert applied == [{"before": 1}]

    cmd.redo()                                   # a real redo
    assert applied == [{"before": 1}, {"after": 1}]


def test_a_gesture_command_records_the_floor_it_was_made_on():
    """D67: THE ACTIVE FLOOR IS PART OF THE SETTLED-GESTURE BOUNDARY.

    Selection is not currently scoped to the active floor -- a drag on the
    second floor can collect first-floor vertices and move both. A command
    recorded WITHOUT floor scope would replay that faithfully, and undo would
    undo it on both floors, at which point a selection bug has become a property
    of the command model.

    `floor` is REQUIRED, not defaulted: a command that forgot it would be
    indistinguishable from one made on the default floor, so the omission has to
    be loud. This asserts the constructor refuses without it -- the design
    requirement, not the fix, which is D67's and is not done.
    """
    import pytest as _pytest
    with _pytest.raises(TypeError):
        GestureCommand(None, {}, {})            # no floor -> refused

    cmd = GestureCommand(None, {}, {}, "second")
    assert cmd.floor == "second"


def test_every_gesture_command_inherits_the_floor_requirement():
    """Asserted across the ROSTER, not on a sample: a subclass that grew its own
    __init__ and dropped the floor would otherwise slip through."""
    import inspect
    for cls in GESTURE_COMMANDS:
        sig = inspect.signature(cls.__init__)
        assert "floor" in sig.parameters, (
            f"{cls.__name__} does not take `floor` -- D67's constraint is that "
            f"the settled-gesture boundary INCLUDES which floor it was made on")
