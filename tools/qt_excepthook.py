"""Catch the Python exception PyQt is about to turn into abort().

Since PyQt 5.5, an unhandled Python exception raised inside a C++ -> Python
callback (a reimplemented virtual, a slot) is handed to `sys.excepthook` and
then `qFatal()` is called, which aborts the process. The abort is what defect 26
sees as 0xC0000409 FAST_FAIL_FATAL_APP_EXIT from Qt6Core, with no message on
stderr.

So the traceback IS available, for exactly one moment, in `sys.excepthook`.
This writes it to a file and flushes, before the abort takes the process.

Load with:  -p qt_excepthook   (tools/ on PYTHONPATH)
Output:     $FP_EXCLOG or ./excepthook.log
"""
import os
import sys
import traceback

_PATH = os.environ.get("FP_EXCLOG", "excepthook.log")
_prev = sys.excepthook


def _hook(exc_type, exc, tb):
    try:
        with open(_PATH, "a", encoding="utf-8") as fh:
            fh.write("=" * 70 + "\n")
            fh.write("UNHANDLED EXCEPTION IN A Qt CALLBACK "
                     "(PyQt will call qFatal() next)\n")
            traceback.print_exception(exc_type, exc, tb, file=fh)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:                                  # never make it worse
        pass
    return _prev(exc_type, exc, tb)


sys.excepthook = _hook


def pytest_configure(config):
    # pytest replaces excepthook in places; reassert ours once it is set up
    sys.excepthook = _hook
