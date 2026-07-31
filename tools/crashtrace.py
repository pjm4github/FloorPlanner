"""A pytest plugin that survives __fastfail: flush each phase to disk.

No cdb, no WER LocalDumps on this box, so the native stack is unavailable. What
IS available is knowing exactly which test and which PHASE was executing when
the process died -- written and flushed before the phase runs, so the last line
in the file is the last thing that started.

Load with:  -p crashtrace   (with this directory on PYTHONPATH)
Output:     $FP_CRASHLOG or ./crashtrace.log
"""
import os

_PATH = os.environ.get("FP_CRASHLOG", "crashtrace.log")
_fh = None


def _w(text):
    global _fh
    if _fh is None:
        _fh = open(_PATH, "w", buffering=1, encoding="utf-8")
    _fh.write(text + "\n")
    _fh.flush()
    os.fsync(_fh.fileno())


def pytest_runtest_logstart(nodeid, location):
    _w(f"START   {nodeid}")


def pytest_runtest_setup(item):
    _w(f"  setup {item.nodeid}")


def pytest_runtest_call(item):
    _w(f"  call  {item.nodeid}")


def pytest_runtest_teardown(item, nextitem):
    _w(f"  tear  {item.nodeid}")


def pytest_runtest_logfinish(nodeid, location):
    _w(f"END     {nodeid}")


def pytest_sessionfinish(session, exitstatus):
    _w(f"SESSION FINISH exit={exitstatus}")
