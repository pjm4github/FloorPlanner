"""The four-way crossing fault (0208-report.md sec4) -- reproduce or refute.

0208, on A6's build: *"Replaying `dragWallFuseStraggler.fpm` fourteen times
in one process, on `main`'s code: after its sixth line, three runs have the
horizontal wall whole and the vertical one split at (340.56, 270.03), and
the others the reverse."* Named, not fixed, no defect record; carried in
the queue since.

This probe replays the macro's first six lines (its `^O` line included,
so the plan is reloaded by the macro itself) N times and tallies the
WHOLE wall set after them -- every end of every wall, rounded to 1/100in
-- so any difference at all, not only the one 0208 described, is a second
state in the tally. Then it prints the walls around the crossing.

Configuration is by environment, so one script covers every way the
replay has been run:
  FRESH=1       a new MainWindow per run (default: one window, reused)
  SHOW=1        the window shown
  GEOM=WxH      the window geometry (default 1200x800, the macro's own --
                tests/test_extract_join.py's pin says so; 1400x1000 is the
                OTHER two macros' geometry and maps these clicks elsewhere)
  WAIT_MS=n     process events for n ms between lines, so the app's 180 ms
                settle timer may fire between gestures
  UPTO=n        how many lines to replay (default 6)
Run it under several PYTHONHASHSEED values as well: a `set` of strings
iterates differently per process.

Positive control, built in: the state after 0, 1, 2 ... lines is printed
first, so the instrument is seen to tell different wall sets apart before
its "one state" is believed.

    python docs/evidence/fourway_crossing_probe.py 14
"""
import hashlib
import os
import sys
from collections import Counter

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtTest import QTest                    # noqa: E402
from PyQt6.QtWidgets import QApplication          # noqa: E402

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp                          # noqa: E402

MACRO = os.path.join(ROOT, "examples", "dragWallFuseStraggler.fpm")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 14
UPTO = int(os.environ.get("UPTO", "6"))
WAIT = int(os.environ.get("WAIT_MS", "0"))
FRESH = os.environ.get("FRESH") == "1"
SHOW = os.environ.get("SHOW") == "1"
W, H = (int(v) for v in os.environ.get("GEOM", "1200x800").split("x"))

with open(MACRO, encoding="utf-8") as fh:
    LINES = [ln for ln in fh.read().splitlines() if ln.strip()]


def wall_set(win):
    return tuple(sorted(
        (round(w.p1.x(), 2), round(w.p1.y(), 2), round(w.p2.x(), 2), round(w.p2.y(), 2))
        for w in win.scene.items() if isinstance(w, fp.WallItem)))


def state_id(ws):
    return hashlib.sha1(repr(ws).encode()).hexdigest()[:8]


def window():
    win = fp.MainWindow()
    win.resize(W, H)
    if SHOW:
        win.show()
    return win


def replay(win, upto):
    for ln in LINES[:upto]:
        res = win.run_macro(ln)
        assert res["ok"], res
        if WAIT:
            QTest.qWait(WAIT)
    return wall_set(win)


def main():
    print(f"dragWallFuseStraggler.fpm, {len(LINES)} lines; window {W}x{H}"
          f"{' shown' if SHOW else ''}; {'fresh window per run' if FRESH else 'one window'};"
          f" wait {WAIT} ms; PYTHONHASHSEED={os.environ.get('PYTHONHASHSEED', 'random')}")
    win = window()
    print("control -- the state after each prefix (one run each):")
    for k in range(0, UPTO + 1):
        ws = replay(win, k)
        print(f"   {k} lines: {len(ws)} walls, state {state_id(ws)}")
    tally = Counter()
    for _ in range(N):
        if FRESH:
            win.close()
            win = window()
        tally[replay(win, UPTO)] += 1
    print(f"after {UPTO} lines, {N} runs: {len(tally)} distinct state(s)")
    for ws, n in tally.items():
        print(f"   {n} run(s): {len(ws)} walls, state {state_id(ws)}; around the crossing:")
        for w in ws:
            if (any(abs(c - 340) < 12 for c in (w[0], w[2]))
                    or any(abs(c - 270) < 12 for c in (w[1], w[3]))):
                print(f"      {w}")
    win.close()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
    os._exit(0)
