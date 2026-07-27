"""P1.6 -- `--verify-design` shadow mode.

The mechanism, not the discoveries: that shadow mode is off unless asked for,
that a corrupt-at-rest document does not fire it, that corruption INTRODUCED
after the baseline does, and that the deep three are gated as P1.2 designed.

The discoveries themselves are the whole suite running twice, which is the
acceptance and lives in CI, not here.

Several tests here deliberately END with a corrupt scene -- that is their
subject. Each declares it with a closing `V.rebase(...)`, the same "this state
is accepted" mechanism a corrupt legacy file uses at load. Without it they would
re-report their own fixture under `FP_VERIFY_DESIGN=deep` at teardown.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design import verify as V

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def on(monkeypatch):
    """Shadow mode on for this test only."""
    monkeypatch.setenv(V.ENV_VAR, "1")
    return True


def _rect(fp, scene, x, y, w, h, name):
    corners = [QPointF(x, y), QPointF(x + w, y),
               QPointF(x + w, y + h), QPointF(x, y + h)]
    r = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2),
                    fp.room_path_from_corners(corners),
                    fp.poly_area_sqft(corners), corners=corners)
    scene.addItem(r)
    return r


# ------------------------------------------------------------------ the switch
def test_off_by_default(fp, scene, monkeypatch):
    """No env var -> no work and no raising, so the suite runs unmodified."""
    monkeypatch.delenv(V.ENV_VAR, raising=False)
    assert V.verify_enabled() is False
    _rect(fp, scene, 0, 0, 120, 96, "A")
    _rect(fp, scene, 60, 48, 120, 96, "B")       # overlapping: I11 would fire
    assert V.verify(scene, "test") is None
    # this test cannot DECLARE its final state the way the others do -- with the
    # flag off, rebase() records {} -- and monkeypatch restores the env before
    # the fixture tears down. So leave nothing to find.
    scene.clear()


@pytest.mark.parametrize("val,enabled,deep", [
    ("", False, False), ("0", False, False), ("off", False, False),
    ("1", True, False), ("true", True, False),
    ("deep", True, True), ("all", True, True),
])
def test_flag_parsing(monkeypatch, val, enabled, deep):
    monkeypatch.setenv(V.ENV_VAR, val)
    assert V.verify_enabled() is enabled
    assert V.verify_deep() is deep


# -------------------------------------------------------------- baseline rules
def test_corrupt_at_rest_does_not_fire(fp, win, on):
    """planc1 opens with 17x I6 + 1x I11 and shadow mode must tolerate it.

    This is the rule that makes shadow mode usable at all: it reports what an
    operation BROKE, not what the file arrived broken."""
    win.load_data(json.loads((EXAMPLES / "planc1.json").read_text("utf-8")))
    base = getattr(win, V.BASELINE_ATTR)
    assert base["I6"] == 17 and base["I11"] == 1
    V.verify(win, "no-op")                       # must not raise
    win._commit_if_changed()                     # nor the real per-op hook


def test_introduced_corruption_raises(fp, win, on):
    """Corruption after the baseline is what shadow mode is for."""
    V.rebase(win)
    assert getattr(win, V.BASELINE_ATTR) == {}
    _rect(fp, win.scene, 0, 0, 120, 96, "A")
    _rect(fp, win.scene, 60, 48, 120, 96, "B")   # two placed rooms overlapping
    with pytest.raises(V.DesignVerificationError, match="I11"):
        V.verify(win, "test op", deep=True)
    V.rebase(win)                                # ends corrupt on purpose


def test_a_fault_that_does_not_grow_is_not_a_regression(fp, win, on):
    """Baseline semantics are per class and directional: equal is fine, and a
    DIFFERENT class rising is what fails."""
    _rect(fp, win.scene, 0, 0, 120, 96, "A")
    _rect(fp, win.scene, 60, 48, 120, 96, "B")
    V.rebase(win)                                # accept the overlap
    assert getattr(win, V.BASELINE_ATTR)["I11"] == 1
    V.verify(win, "unchanged", deep=True)        # same fault, no raise
    _rect(fp, win.scene, 12, 12, 120, 96, "C")   # a third overlapping room
    with pytest.raises(V.DesignVerificationError, match="I11"):
        V.verify(win, "worse", deep=True)
    V.rebase(win)                                # ends corrupt on purpose


def test_deep_invariants_are_gated(fp, win, on):
    """I11 is deep-only, so the per-operation hook cannot fire on it -- that is
    the P1.2 split, and it is what keeps the hot path affordable."""
    _rect(fp, win.scene, 0, 0, 120, 96, "A")
    _rect(fp, win.scene, 60, 48, 120, 96, "B")
    assert "I11" not in V.fault_profile(win, deep=False)
    assert V.fault_profile(win, deep=True)["I11"] == 1
    V.verify(win, "cheap")                       # cheap twelve: silent
    V.rebase(win)                                # ends corrupt on purpose


def test_deep_mode_promotes_every_check(fp, win, monkeypatch):
    """FP_VERIFY_DESIGN=deep runs all fifteen at EVERY quiescent point."""
    monkeypatch.setenv(V.ENV_VAR, "deep")
    V.rebase(win)
    _rect(fp, win.scene, 0, 0, 120, 96, "A")
    _rect(fp, win.scene, 60, 48, 120, 96, "B")
    with pytest.raises(V.DesignVerificationError, match="I11"):
        V.verify(win, "cheap call, deep flag")   # deep=False, promoted anyway
    V.rebase(win)                                # ends corrupt on purpose


# ------------------------------------------------- unwelded_ends is report-only
def test_unwelded_ends_warns_but_never_raises(fp, win, on):
    """The 9" join tolerance is a GESTURE, not a rule.

    The schema is explicit -- join_tol_in is "Never an invariant: a wall
    deliberately stopping 6" short of another is a legitimate design (a reveal,
    a pilaster gap), and nothing may silently close it." Raising here would fail
    a user for drawing a reveal. It is also decomposition-dependent, so it moves
    when the document does not."""
    V.rebase(win)
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(120, 6), QPointF(120, 200), "interior"))
    fp.rebuild_all_walls(sc)

    prof = V.fault_profile(win)
    assert prof.get("unwelded_ends"), "expected an unwelded end in this fixture"
    with pytest.warns(UserWarning, match="unwelded_ends rose"):
        V.verify(win, "drew a reveal")           # warns, does not raise
    # reported once, not on every subsequent check
    V.verify(win, "again")


def test_report_only_keys_are_named(fp):
    """Guard the list: adding an invariant to REPORT_ONLY silently disarms it."""
    assert V.REPORT_ONLY == ("unwelded_ends",)


# ------------------------------------------------------------------ integration
def test_apply_design_rebases(fp, win, on):
    """`apply_design_to_scene` is a LOAD -- it replaces the document, so its
    faults are the new document's. Without the rebase, rebuilding planc1 from a
    byte-identical Design reads as a regression, because Design walls are
    edge-granular and a split wall has more ends."""
    from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
    win.load_data(json.loads((EXAMPLES / "planc1.json").read_text("utf-8")))
    before = dict(getattr(win, V.BASELINE_ATTR))
    with pytest.warns(UserWarning):              # the walk's weld notice
        apply_design_to_scene(win, design_from_scene(win))
    after = getattr(win, V.BASELINE_ATTR)
    assert after["unwelded_ends"] > before["unwelded_ends"]
    V.verify(win, "post-apply")                  # must not raise


def test_save_verifies_deep(fp, win, on, tmp_path):
    """Save runs all fifteen before writing -- paid once, stakes highest."""
    V.rebase(win)
    _rect(fp, win.scene, 0, 0, 120, 96, "A")
    _rect(fp, win.scene, 60, 48, 120, 96, "B")
    with pytest.raises(V.DesignVerificationError, match="I11"):
        win.save_path(str(tmp_path / "p.json"))
    assert not (tmp_path / "p.json").exists(), "a corrupt plan was written"
    V.rebase(win)                                # ends corrupt on purpose
