"""0345 C4 -- the plan watcher and its single-pass validator.

The watcher loop runs against a TEMP folder (`tmp_path`), never the real watch
folder under the intake tree. The 3D panel is skipped (PLAN_WATCH_NO_3D) so the
tests do not depend on a GPU -- the composite report PNG is still non-blank
(header + plan), which is what "a non-blank PNG" means here. Each pass boots the
app in a child process, so these are `slow` (run by the full gate, skipped by
--quick).
"""
import json
import os
import sys
import time

import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QImage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))
import plan_watch                                   # noqa: E402

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def _no_3d(monkeypatch):
    monkeypatch.setenv("PLAN_WATCH_NO_3D", "1")      # inherited by the child


def _good_doc():
    """A known-good v5 plan, built by the app itself (so it is schema- and
    invariant-clean by construction): one concept room on the default floor."""
    from floorplanner.mainwindow import MainWindow
    from floorplanner.rooms import make_concept_room
    w = MainWindow()
    make_concept_room(w.scene, "RM", 120, 120, QPointF(100, 100))
    return w.design_document()


def _write(build, name, obj):
    p = os.path.join(build, f"{name}.json")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(obj if isinstance(obj, str) else json.dumps(obj, indent=1))
    return p


def _one_pass(build, name):
    plan_watch.run_watch(build, poll_interval=0.05, debounce=0.1,
                         heartbeat_interval=0.1, stop_after_passes=1,
                         deadline=time.time() + 150)
    with open(os.path.join(build, name, "latest.result.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _nonblank(img, samples=60):
    img = img.convertToFormat(QImage.Format.Format_RGB32)
    seen = set()
    for i in range(samples):
        seen.add(img.pixel((i * 101) % img.width(), (i * 57) % img.height()) & 0xFFFFFF)
    return len(seen) > 1


# -- a known-good plan: PASS + a non-blank PNG + latest.result.json ------------
def test_known_good_plan_passes_with_a_non_blank_png(tmp_path):
    build = str(tmp_path)
    _write(build, "good", _good_doc())
    res = _one_pass(build, "good")
    assert res["verdict"] == "PASS", res
    assert not res["step1_schema"] and not res["step2_invariants"]
    assert not res["step4_round_trip"]
    png = os.path.join(build, "good", f"{res['pass']:04d}.report.png")
    assert os.path.exists(png), "report PNG missing"
    img = QImage(png)
    assert not img.isNull() and _nonblank(img), "report PNG is blank"
    assert os.path.exists(os.path.join(build, "good", "latest.result.json"))
    assert os.path.exists(os.path.join(build, "watcher.alive"))


# -- a dangling vertex reference: FAIL, and the finding names it ---------------
def test_dangling_vertex_fails_with_the_finding_named(tmp_path):
    doc = _good_doc()
    victim = doc["vertices"][-1]["id"]               # a vertex the room references
    doc["vertices"] = [v for v in doc["vertices"] if v["id"] != victim]
    build = str(tmp_path)
    _write(build, "dangling", doc)
    res = _one_pass(build, "dangling")
    assert res["verdict"] == "FAIL"
    findings = (res["step1_schema"] + res["step2_invariants"]
                + res["step3_open"] + res["step4_round_trip"])
    assert any(victim in f for f in findings), (victim, findings[:6])


# -- not JSON at all: FAIL, not a crash ---------------------------------------
def test_non_json_fails_without_crashing(tmp_path):
    build = str(tmp_path)
    _write(build, "broken", "}{ this is not json at all")
    res = _one_pass(build, "broken")
    assert res["verdict"] == "FAIL"
    assert any("JSON" in f.upper() for f in res["step1_schema"])
    assert res["traceback"] is None, "a non-JSON input must not raise"


# -- the converged handshake: move on a match ---------------------------------
def test_converged_moves_the_file_on_a_match(tmp_path):
    build = str(tmp_path)
    _write(build, "conv", _good_doc())
    res = _one_pass(build, "conv")
    assert res["verdict"] == "PASS"
    with open(os.path.join(build, "conv.converged"), "w", encoding="utf-8") as fh:
        fh.write(res["sha256"])
    reason = plan_watch.run_watch(build, poll_interval=0.05, debounce=0.1,
                                  heartbeat_interval=0.1, deadline=time.time() + 15)
    assert reason == "converged: conv", reason
    assert os.path.exists(os.path.join(build, "done", "conv.final.json"))
    assert os.path.exists(os.path.join(build, "done", "conv.final.png"))
    assert not os.path.exists(os.path.join(build, "conv.json")), "input not moved"
    assert os.path.exists(os.path.join(build, "watcher.stopped"))


# -- the converged handshake: refuse on a mismatch ----------------------------
def test_converged_refuses_on_a_mismatch(tmp_path):
    build = str(tmp_path)
    _write(build, "conv", _good_doc())
    _one_pass(build, "conv")
    with open(os.path.join(build, "conv.converged"), "w", encoding="utf-8") as fh:
        fh.write("deadbeef" * 8)                      # a sha that never passed
    plan_watch.run_watch(build, poll_interval=0.05, debounce=0.1,
                         heartbeat_interval=0.1, deadline=time.time() + 4)
    assert os.path.exists(os.path.join(build, "conv.converged.refused"))
    assert os.path.exists(os.path.join(build, "conv.json")), "input wrongly moved"
    assert not os.path.exists(os.path.join(build, "done", "conv.final.json"))


# -- STOP stops the loop cleanly ----------------------------------------------
def test_stop_file_stops_the_loop(tmp_path):
    build = str(tmp_path)
    open(os.path.join(build, "STOP"), "w").close()
    t0 = time.time()
    reason = plan_watch.run_watch(build, poll_interval=0.05, debounce=0.1,
                                  heartbeat_interval=0.1, deadline=time.time() + 10)
    assert reason == "STOP file"
    assert time.time() - t0 < 5, "STOP should be prompt"
    assert os.path.exists(os.path.join(build, "watcher.stopped"))
