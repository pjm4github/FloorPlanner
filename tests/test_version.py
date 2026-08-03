"""`code_version()` -- the status bar's answer to "which code is this window
actually running?" (the P4.2 mini-gate's stale-process lesson: a fix landed
on disk while an app launched earlier kept reproducing the old bug)."""
import re

import pytest

from floorplanner.config import APP_VERSION, code_version

pytestmark = pytest.mark.io


def test_code_version_names_the_checkout():
    cv = code_version()
    assert cv.startswith(f"v{APP_VERSION}")
    # dev and CI both run from a git checkout: a branch or a detached sha
    # must show. Outside a checkout the bare version is the honest answer.
    in_checkout = re.search(r"@ [0-9a-f]{7}", cv) or "detached" in cv
    assert in_checkout or cv == f"v{APP_VERSION}", cv


def test_code_version_is_launch_stable():
    # captured once at import -- two reads must agree (the label must not
    # drift to whatever lands on disk after launch)
    assert code_version() == code_version() == code_version()
