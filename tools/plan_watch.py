"""tools/plan_watch.py -- the PLAN WATCHER (0345).

Watches ONE folder (`fixtures/incoming/build/` by default). When a top-level
`<name>.json` appears or changes -- debounced, size-stable, and only when its
sha256 differs from the last pass -- it runs ONE validation pass in a CHILD
PROCESS (`tools/plan_validate.py`) with a 90 s timeout, so a crash or hang
cannot take the watcher down. It never boots Qt itself (the child owns all the
app work); it only orchestrates and writes results.

Per pass it writes, into `<build>/<name>/`:
    <NNNN>.plan.json / <NNNN>.result.json / <NNNN>.report.png   (the child)
    latest.result.json   -- the child's result, placed LAST by atomic rename,
                            so its appearance means the pass is complete; the
                            reviewer polls this and nothing else.
and, in `<build>/`:
    loop.log         -- one line per pass
    watcher.alive    -- heartbeat (time + PID), every 5 s
    .counter         -- the zero-padded pass counter, continued across restarts

Convergence / stop (0345 sec4): the reviewer writes `<name>.converged` holding
the plan's sha256; if the watcher's last pass for that sha was PASS it MOVES the
input to `done/<name>.final.json`, copies the last report as `done/<name>.final.png`,
writes `watcher.stopped`, and exits; on a mismatch it writes
`<name>.converged.refused` and keeps running. A `STOP` file or Ctrl-C stops it
cleanly. 300 passes for any one name is the runaway cap.

C1: it writes only under the build folder, never edits an input (the one move
is the converged handshake), and never touches git.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BUILD = os.path.join(ROOT, "fixtures", "incoming", "build")
VALIDATE = os.path.join(ROOT, "tools", "plan_validate.py")
CHILD_TIMEOUT = 90
RUNAWAY = 300


def _git_head():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip() or "?"
    except OSError:
        return "?"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _errcount(result):
    return (len(result.get("step1_schema", []))
            + len(result.get("step2_invariants", []))
            + len([f for f in result.get("step3_open", []) if not f.startswith("status:")])
            + len(result.get("step4_round_trip", []))
            + len(result.get("step6_render", [])))


def _failure_card(path, name, pass_num, reason):
    """A header-only PNG for a pass the child could not finish (timeout/crash).
    Qt is imported lazily and offscreen so the watcher itself stays Qt-free."""
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtGui import QColor, QFont, QImage, QPainter
        from PyQt6.QtWidgets import QApplication
        QApplication.instance() or QApplication([])
        img = QImage(2400, 240, QImage.Format.Format_RGB32)
        img.fill(QColor(255, 255, 255))
        p = QPainter(img)
        p.fillRect(0, 0, 2400, 240, QColor(254, 242, 242))
        p.setPen(QColor(15, 23, 42))
        p.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        p.drawText(24, 50, f"{name}   ·   pass {pass_num:04d}   ·   {time.strftime('%Y-%m-%d %H:%M:%S')}")
        p.setPen(QColor(185, 28, 28))
        p.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        p.drawText(24, 110, "FAIL")
        p.setPen(QColor(51, 65, 85))
        p.setFont(QFont("Arial", 15))
        p.drawText(24, 150, reason[:260])
        p.end()
        img.save(path)
    except Exception:                                   # noqa: BLE001
        pass                                             # the result.json is the source of truth


def _run_pass(build, name, plan_path, pass_num, git_head):
    """Spawn the child validator; return (result_dict, child_wrote_files:bool)."""
    out_dir = os.path.join(build, name)
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{pass_num:04d}"
    result_path = os.path.join(out_dir, f"{stem}.result.json")
    env = dict(os.environ)
    try:
        subprocess.run([sys.executable, VALIDATE, plan_path, out_dir, str(pass_num), git_head],
                       cwd=ROOT, capture_output=True, text=True, timeout=CHILD_TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        card = os.path.join(out_dir, f"{stem}.report.png")
        _failure_card(card, name, pass_num, f"child timed out after {CHILD_TIMEOUT}s")
        res = {"pass": pass_num, "name": name, "verdict": "FAIL",
               "sha256": _sha256(plan_path), "git_head": git_head,
               "step3_open": [f"child timed out after {CHILD_TIMEOUT}s"],
               "step1_schema": [], "step2_invariants": [], "step4_round_trip": [],
               "step5_scene": {}, "step6_render": [], "duration_s": CHILD_TIMEOUT,
               "step_seconds": {}, "traceback": "TimeoutExpired"}
        with open(result_path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
        return res, False
    if os.path.exists(result_path):
        try:
            with open(result_path, encoding="utf-8") as fh:
                return json.load(fh), True
        except (ValueError, OSError):
            pass
    # child crashed without a readable result
    card = os.path.join(out_dir, f"{stem}.report.png")
    _failure_card(card, name, pass_num, "child crashed without writing a result")
    res = {"pass": pass_num, "name": name, "verdict": "FAIL",
           "sha256": _sha256(plan_path), "git_head": git_head,
           "step3_open": ["child crashed without writing a result"],
           "step1_schema": [], "step2_invariants": [], "step4_round_trip": [],
           "step5_scene": {}, "step6_render": [], "duration_s": None,
           "step_seconds": {}, "traceback": "child exited without a result file"}
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    return res, False


def _publish(build, name, pass_num, result):
    """loop.log line + latest.result.json by atomic rename (written LAST)."""
    out_dir = os.path.join(build, name)
    stem = f"{pass_num:04d}"
    sha8 = (result.get("sha256") or "--------")[:8]
    with open(os.path.join(build, "loop.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{pass_num:04d}  {time.strftime('%Y-%m-%d %H:%M:%S')}  {sha8}  "
                 f"{result.get('verdict', 'FAIL')}  errors={_errcount(result)}\n")
    src = os.path.join(out_dir, f"{stem}.result.json")
    latest = os.path.join(out_dir, "latest.result.json")
    tmp = latest + ".tmp"
    shutil.copyfile(src, tmp)
    os.replace(tmp, latest)                              # appearance == pass complete


def _heartbeat(build):
    tmp = os.path.join(build, "watcher.alive.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} pid={os.getpid()}\n")
    os.replace(tmp, os.path.join(build, "watcher.alive"))


def _stop(build, reason):
    with open(os.path.join(build, "watcher.stopped"), "w", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} pid={os.getpid()}\n{reason}\n")


def _converge(build, name, last):
    """Handle `<name>.converged` (0345 sec4). Returns 'moved' | 'refused' | None."""
    marker = os.path.join(build, f"{name}.converged")
    try:
        want = open(marker, encoding="utf-8").read().strip()
    except OSError:
        return None
    if last is None or last["sha256"] != want or last["verdict"] != "PASS":
        why = ("no pass yet" if last is None
               else f"last sha {last['sha256'][:8]} / {last['verdict']} != converged "
                    f"sha {want[:8]} / PASS")
        with open(os.path.join(build, f"{name}.converged.refused"), "w", encoding="utf-8") as fh:
            fh.write(why + "\n")
        os.remove(marker)
        return "refused"
    done = os.path.join(build, "done")
    os.makedirs(done, exist_ok=True)
    shutil.move(os.path.join(build, f"{name}.json"),
                os.path.join(done, f"{name}.final.json"))     # the ONE input move (C1)
    report = os.path.join(build, name, f"{last['pass']:04d}.report.png")
    if os.path.exists(report):
        shutil.copyfile(report, os.path.join(done, f"{name}.final.png"))
    os.remove(marker)
    return "moved"


def _load_latest(build, name):
    """Recover the last pass's result for `name` across a restart."""
    try:
        with open(os.path.join(build, name, "latest.result.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def run_watch(build=DEFAULT_BUILD, poll_interval=0.5, debounce=1.0,
              heartbeat_interval=5.0, runaway=RUNAWAY, deadline=None,
              stop_after_passes=None):
    """The watch loop. Returns the stop reason. `deadline` (epoch seconds),
    `stop_after_passes`, and short `debounce`/`poll_interval` make it testable
    against a temp folder."""
    os.makedirs(build, exist_ok=True)
    git_head = _git_head()
    counter_path = os.path.join(build, ".counter")
    try:
        counter = int(open(counter_path).read().strip())
    except (OSError, ValueError):
        counter = 0
    last = {}            # name -> last result dict
    passes = {}          # name -> pass count this run
    pending = {}         # name -> (size, time_size_first_seen)
    total_passes = 0
    last_beat = 0.0
    # recover each name's last result (sha / verdict) across a restart, so the
    # sha-skip and the converged handshake survive one
    for fn in os.listdir(build):
        p = os.path.join(build, fn)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "latest.result.json")):
            rec = _load_latest(build, fn)
            if rec is not None:
                last[fn] = rec
    _heartbeat(build)
    reason = None
    try:
        while True:
            if deadline is not None and time.time() >= deadline:
                reason = "deadline"
                break
            if os.path.exists(os.path.join(build, "STOP")):
                reason = "STOP file"
                break
            now = time.time()
            if now - last_beat >= heartbeat_interval:
                _heartbeat(build)
                last_beat = now

            for fn in sorted(os.listdir(build)):
                if not fn.endswith(".json") or fn.endswith(".tmp"):
                    continue
                path = os.path.join(build, fn)
                if not os.path.isfile(path):
                    continue
                name = fn[:-5]

                if os.path.exists(os.path.join(build, f"{name}.converged")):
                    outcome = _converge(build, name, last.get(name))
                    if outcome == "moved":
                        reason = f"converged: {name}"
                        _stop(build, reason)
                        return reason
                    continue

                try:
                    size = os.path.getsize(path)
                except OSError:
                    continue
                prev = pending.get(name)
                if prev is None or prev[0] != size:
                    pending[name] = (size, now)
                    continue
                if now - prev[1] < debounce:
                    continue                             # size not held still long enough
                try:
                    sha = _sha256(path)
                except OSError:
                    continue
                if last.get(name) and last[name].get("sha256") == sha:
                    continue                             # same content as last pass

                counter += 1
                with open(counter_path, "w", encoding="utf-8") as fh:
                    fh.write(str(counter))
                result, _ = _run_pass(build, name, path, counter, git_head)
                _publish(build, name, counter, result)
                last[name] = result
                passes[name] = passes.get(name, 0) + 1
                total_passes += 1
                pending.pop(name, None)
                _heartbeat(build)
                last_beat = time.time()
                if passes[name] >= runaway:
                    reason = f"runaway cap ({runaway}) for {name}"
                    break
                if stop_after_passes is not None and total_passes >= stop_after_passes:
                    reason = f"stop_after_passes ({stop_after_passes})"
                    break
            if reason:
                break
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        reason = "Ctrl-C"
    _stop(build, reason or "exit")
    return reason or "exit"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    build = argv[0] if argv else DEFAULT_BUILD
    reason = run_watch(build)
    sys.stderr.write(f"plan_watch stopped: {reason}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
