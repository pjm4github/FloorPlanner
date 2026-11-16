"""tools/plan_validate.py -- ONE plan, ONE validation pass (0345).

Invoked as a CHILD PROCESS by tools/plan_watch.py, which owns the 90 s timeout,
the pass counter, the heartbeat and loop.log. This module validates a v5 plan
JSON through the app's OWN API only (0345 C3 -- no app change) and renders one
report PNG. It writes, into <out_dir>:

    <NNNN>.plan.json     a byte copy of the input this pass validated
    <NNNN>.result.json   the structured result (0345 sec2)
    <NNNN>.report.png    the report image (0345 sec3)

A raised exception is caught, its traceback recorded in the result, and a
header+findings PNG is still written (0345 sec3: "a plan that fails to load
still gets a PNG"). Exit code 0 means the pass completed and wrote its result
(PASS or FAIL); a non-zero exit means the pass could not even write a result,
and the watcher synthesises a FAIL.

CLI:  python tools/plan_validate.py <plan.json> <out_dir> <pass_num> <git_head>

Headless rules (CLAUDE.md): QT_QPA_PLATFORM=offscreen before PyQt; QApplication
before FloorPlanner; interactive=False on every app call (0345 C2); the 3D panel
is a SEPARATE process (fp3dq --shot), the only way D77 (offscreen Quick 3D draws
blank) is worked around, and its result is pixel-tested for blankness.
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import json          # noqa: E402
import subprocess     # noqa: E402
import time           # noqa: E402
import traceback      # noqa: E402

from PyQt6.QtCore import QRectF, Qt            # noqa: E402
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPixmap   # noqa: E402
from PyQt6.QtWidgets import QApplication        # noqa: E402

_app = QApplication.instance() or QApplication([])

import FloorPlanner as FP                       # noqa: E402,F401
from floorplanner.design import validate as dvalidate    # noqa: E402
from floorplanner.design import verify as dverify        # noqa: E402
from floorplanner.mainwindow import MainWindow           # noqa: E402
from floorplanner.rooms import RoomItem                  # noqa: E402
from floorplanner.viewer import fp3d                      # noqa: E402

PASS = "PASS"
FAIL = "FAIL"
REPORT_W = 2400


# -- small dict diff (step 4 wants WHAT differs, not just that it does) --------
def _diff(a, b, path=""):
    out = []
    if type(a) is not type(b):
        out.append(f"{path or '<root>'}: type {type(a).__name__} != {type(b).__name__}")
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: only after reopen")
            elif k not in b:
                out.append(f"{path}.{k}: only before reopen")
            else:
                out += _diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b, strict=False)):
            out += _diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(f"{path or '<root>'}: {a!r} != {b!r}")
    return out


# -- the 3D panel: a separate process, then a blankness pixel test -------------
def _shot_3d(plan_path, out_png):
    """Render the whole-house 3D view the way docs/make_gallery.py does
    (fp3dq --shot, own process). Returns (ok, reason)."""
    if os.environ.get("PLAN_WATCH_NO_3D"):
        return False, "skipped (PLAN_WATCH_NO_3D)"
    # fp3dq must render on the REAL platform, not inherit our offscreen (D77:
    # offscreen Quick 3D draws blank). On a true-headless host it then fails to
    # start and we fall back to the "3D not rendered" panel, which is correct.
    env = {k: v for k, v in os.environ.items() if k != "QT_QPA_PLATFORM"}
    try:
        r = subprocess.run(
            [sys.executable, "-m", "floorplanner.viewer.fp3dq", plan_path,
             "--shot", out_png, "--yaw", "35", "--pitch", "-22", "--zoom",
             "1.15", "--fov", "28", "--shot-delay", "1500"],
            cwd=ROOT, capture_output=True, text=True, timeout=60, env=env)
    except subprocess.TimeoutExpired:
        return False, "fp3dq timed out (60 s)"
    except OSError as e:
        return False, f"fp3dq did not start: {e}"
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-1:] or ["no output"]
        return False, f"fp3dq exit {r.returncode}: {tail[0][:200]}"
    if not os.path.exists(out_png):
        return False, "fp3dq wrote no file"
    img = QImage(out_png)
    if img.isNull():
        return False, "fp3dq output unreadable"
    if _is_blank(img):
        return False, "rendered blank (offscreen Quick 3D, D77)"
    return True, ""


def _is_blank(img, samples=40):
    """True when the image is essentially one flat colour -- the D77 blank."""
    img = img.convertToFormat(QImage.Format.Format_RGB32)
    w, h = img.width(), img.height()
    if w < 2 or h < 2:
        return True
    seen = set()
    for i in range(samples):
        x = (i * 2654435761) % w
        y = ((i * 40503) % h)
        seen.add(img.pixel(x, y) & 0xFFFFFF)
        if len(seen) > 3:
            return False
    return True


# -- per-level plan grabs, by the app's own scene ------------------------------
def _level_rect(win, level):
    rects = [it.sceneBoundingRect() for it in win.scene.items()
             if getattr(it, "floor", None) == level]
    if not rects:
        return None
    r = rects[0]
    for extra in rects[1:]:
        r = r.united(extra)
    return r.adjusted(-40, -40, 40, 40)


def _grab_level(win, level):
    win.switch_floor(level)
    _app.processEvents()
    rect = _level_rect(win, level)
    if rect is not None and rect.isValid():
        win.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        _app.processEvents()
    return win.view.grab()


# -- the report PNG ------------------------------------------------------------
def _draw_header(p, x, y, w, name, pass_num, verdict, findings, when):
    band_h = 190
    p.fillRect(x, y, w, band_h, QColor(248, 250, 252))
    green, red = QColor(21, 128, 61), QColor(185, 28, 28)
    p.setPen(QColor(15, 23, 42))
    p.setFont(QFont("Arial", 22, QFont.Weight.Bold))
    p.drawText(x + 24, y + 42, f"{name}   ·   pass {pass_num:04d}   ·   {when}")
    p.setFont(QFont("Arial", 30, QFont.Weight.Bold))
    p.setPen(green if verdict == PASS else red)
    p.drawText(x + 24, y + 92, f"{verdict}   ({len(findings)} finding(s))")
    p.setPen(QColor(51, 65, 85))
    p.setFont(QFont("Arial", 13))
    for i, f in enumerate(findings[:3]):
        p.drawText(x + 24, y + 124 + i * 22, ("• " + f)[:230])
    p.setPen(QColor(203, 213, 225))
    p.drawLine(x, y + band_h, x + w, y + band_h)
    return band_h


def _render_report(path, name, pass_num, verdict, findings, when,
                   level_pixmaps, shot_png, shot_reason):
    plan_h = 900 if level_pixmaps else 0
    shot_h = 1000
    total_h = 190 + plan_h + shot_h + 40
    img = QImage(REPORT_W, total_h, QImage.Format.Format_RGB32)
    img.fill(QColor(255, 255, 255))
    p = QPainter(img)
    try:
        y = 0
        y += _draw_header(p, 0, y, REPORT_W, name, pass_num, verdict, findings, when)
        if level_pixmaps:
            n = len(level_pixmaps)
            cw = REPORT_W // n
            for i, (lvl, pm) in enumerate(level_pixmaps):
                cx = i * cw
                p.setPen(QColor(100, 116, 139))
                p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                p.drawText(cx + 12, y + 26, f"level {lvl}")
                if pm is not None and not pm.isNull():
                    scaled = pm.scaled(cw - 24, plan_h - 56,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                    p.drawPixmap(cx + 12, y + 36, scaled)
            y += plan_h
        # the 3D band
        p.setPen(QColor(100, 116, 139))
        p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        p.drawText(12, y + 26, "3D view (whole house)")
        shot = QPixmap(shot_png) if shot_png and os.path.exists(shot_png) else QPixmap()
        if not shot.isNull():
            scaled = shot.scaled(REPORT_W - 24, shot_h - 56,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(12, y + 36, scaled)
        else:
            p.fillRect(12, y + 36, REPORT_W - 24, shot_h - 56, QColor(241, 245, 249))
            p.setPen(QColor(185, 28, 28))
            p.setFont(QFont("Arial", 18))
            p.drawText(QRectF(12, y + 36, REPORT_W - 24, shot_h - 56),
                       Qt.AlignmentFlag.AlignCenter,
                       f"3D not rendered: {shot_reason}")
    finally:
        p.end()
    img.save(path)


# -- one pass ------------------------------------------------------------------
def run_pass(plan_path, out_dir, pass_num, git_head):
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{pass_num:04d}"
    name = os.path.splitext(os.path.basename(plan_path))[0]
    t0 = time.time()
    result = {
        "pass": pass_num, "name": name, "git_head": git_head,
        "sha256": None, "verdict": FAIL,
        "step1_schema": [], "step2_invariants": [], "step3_open": [],
        "step4_round_trip": [], "step5_scene": {}, "step6_render": [],
        "duration_s": None, "step_seconds": {}, "traceback": None,
    }
    _marks = [("start", t0)]

    def mark(label):
        _marks.append((label, time.time()))
    plan_copy = os.path.join(out_dir, f"{stem}.plan.json")
    level_pixmaps, shot_png, shot_reason = [], None, "not attempted"
    try:
        with open(plan_path, "rb") as fh:
            raw = fh.read()
        import hashlib
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        with open(plan_copy, "wb") as fh:
            fh.write(raw)

        # step 1 -- JSON + packaged schema
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            result["step1_schema"] = [f"not valid JSON: {e}"]
            doc = None
        if doc is not None:
            try:
                result["step1_schema"] = list(dvalidate.schema_errors(doc))
            except Exception as e:                       # noqa: BLE001
                result["step1_schema"] = [f"schema check raised: {e}"]

        mark("step1_schema")
        # step 2 -- referential invariants, deep (run whenever the JSON parsed,
        # even if the schema failed -- a plan can be schema-imperfect yet load,
        # and the reviewer wants every finding and the render, not an early out)
        if doc is not None:
            try:
                result["step2_invariants"] = list(dvalidate.check(doc, deep=True))
            except Exception as e:                       # noqa: BLE001
                result["step2_invariants"] = [f"invariant check raised: {e}"]

        mark("step2_invariants")
        # step 3 -- boot + open, non-interactively (attempt whenever the JSON
        # parsed; a raise here just means the plan could not load -> win=None)
        win = None
        if doc is not None:
            try:
                win = MainWindow()
                win.resize(1400, 1000)
                win.load_path(plan_path)
                _app.processEvents()
                imp = list(getattr(win, "_import_errors", None) or [])
                bnd = list(getattr(win, "_boundary_findings", None) or [])
                status = ""
                try:
                    status = win.statusBar().currentMessage()
                except Exception:                        # noqa: BLE001
                    pass
                faults = dverify.fault_profile(win, deep=True)
                try:
                    dverify.verify(win, "plan_watch.step3", deep=True)
                except dverify.DesignVerificationError as e:
                    result["step3_open"].append(f"verify raised: {e}")
                for e in imp:
                    result["step3_open"].append(f"import error: {e}")
                for e in bnd:
                    result["step3_open"].append(f"boundary: {e}")
                if faults:
                    result["step3_open"].append(
                        "fault_profile: " + ", ".join(f"{k}={v}" for k, v in sorted(faults.items())))
                result["step3_open"].append(f"status: {status}" if status else "status: (empty)")
            except Exception as e:                        # noqa: BLE001
                result["step3_open"].append(f"open raised: {e}")
                win = None

        mark("step3_open")
        # step 4 -- round trip design_document() -> reopen -> snapshot() equal?
        # (whenever the plan loaded; fidelity is independent of step-3 findings)
        if win is not None:
            try:
                s0 = win.snapshot()
                doc_out = win.design_document()
                rt_path = os.path.join(out_dir, f"{stem}.roundtrip.tmp.json")
                with open(rt_path, "w", encoding="utf-8") as fh:
                    json.dump(doc_out, fh, indent=1)
                win2 = MainWindow()
                win2.load_path(rt_path)
                _app.processEvents()
                s1 = win2.snapshot()
                diffs = _diff(s0, s1)
                result["step4_round_trip"] = diffs[:40]
                os.remove(rt_path)
            except Exception as e:                        # noqa: BLE001
                result["step4_round_trip"] = [f"round trip raised: {e}"]

        mark("step4_round_trip")
        # step 5 -- facts from the LOADED scene + build_model
        if win is not None:
            try:
                scene = {"levels": {}}
                rooms = [it for it in win.scene.items() if isinstance(it, RoomItem)]
                by_level = {}
                for r in rooms:
                    by_level.setdefault(r.floor, []).append(
                        {"name": r.name, "area_sqft": round(r.area_sqft, 1)})
                for lvl, rr in by_level.items():
                    scene["levels"][lvl] = sorted(rr, key=lambda d: d["name"])
                if doc is not None:
                    model = fp3d.build_model(doc)
                    scene["model_stats"] = model.stats
                    scene["model_notes"] = list(model.notes)
                    scene["model_info"] = list(model.info)[:20]
                result["step5_scene"] = scene
            except Exception as e:                        # noqa: BLE001
                result["step5_scene"] = {"error": str(e)}

        mark("step5_scene")
        # verdict: PASS only when steps 1-4 are all clean
        steps_1_4_clean = (
            not result["step1_schema"] and not result["step2_invariants"]
            and not [f for f in result["step3_open"] if not f.startswith("status:")]
            and not result["step4_round_trip"])
        result["verdict"] = PASS if (doc is not None and steps_1_4_clean) else FAIL

        # step 6 -- render (always; 3D in its own process)
        if win is not None:
            try:
                levels = [lv["name"] for lv in (doc.get("levels") or [])] if doc else []
                for lvl in levels:
                    try:
                        level_pixmaps.append((lvl, _grab_level(win, lvl)))
                    except Exception as e:                # noqa: BLE001
                        level_pixmaps.append((lvl, None))
                        result["step6_render"].append(f"level {lvl} plan: {e}")
            except Exception as e:                        # noqa: BLE001
                result["step6_render"].append(f"plan render: {e}")
        shot_png = os.path.join(out_dir, f"{stem}.3d.tmp.png")
        ok, shot_reason = _shot_3d(plan_path, shot_png)
        if not ok:
            result["step6_render"].append(f"3D: {shot_reason}")
            shot_png = None
    except Exception:                                      # noqa: BLE001
        result["traceback"] = traceback.format_exc()
        result["verdict"] = FAIL

    # always render a PNG
    findings = (result["step1_schema"] + result["step2_invariants"]
                + [f for f in result["step3_open"] if not f.startswith("status:")]
                + result["step4_round_trip"] + result["step6_render"])
    if result["traceback"]:
        findings = ["raised -- see traceback"] + findings
    when = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        _render_report(os.path.join(out_dir, f"{stem}.report.png"), name, pass_num,
                       result["verdict"], findings, when, level_pixmaps,
                       shot_png, shot_reason)
    except Exception as e:                                 # noqa: BLE001
        result.setdefault("step6_render", []).append(f"report compose: {e}")
    finally:
        if shot_png and os.path.exists(shot_png):
            try:
                os.remove(shot_png)
            except OSError:
                pass

    mark("step6_render")
    for (_la, ta), (lb, tb) in zip(_marks, _marks[1:], strict=False):
        result["step_seconds"][lb] = round(tb - ta, 2)
    result["duration_s"] = round(time.time() - t0, 2)
    with open(os.path.join(out_dir, f"{stem}.result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 4:
        sys.stderr.write("usage: plan_validate.py <plan.json> <out_dir> <pass_num> <git_head>\n")
        return 2
    plan_path, out_dir, pass_num, git_head = argv
    run_pass(plan_path, out_dir, int(pass_num), git_head)
    return 0


if __name__ == "__main__":
    sys.exit(main())
