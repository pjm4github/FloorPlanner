"""Settings coercion (`coerce_setting`) and the app-wide settings store
(`app_settings`, migrated from a `QSettings` INI to plain JSON).

0073/0074/0075-ruling.md's GREEN items, per 0075 sec6: the JSON store
behind `app_settings()` with its per-type round-trip receipt, the INI-to-
JSON migration with its own fail-first receipt, and the document loader's
type-aware coercion (0073 sec2) -- all landing with no new settings keys
and no user-visible behaviour change yet (the three-rung precedence chain
and first-run materialisation are AMBER, not built here).
"""
import json

import pytest
from PyQt6.QtCore import QStandardPaths

pytestmark = pytest.mark.io


# ---------------------------------------------------------------------------
# coerce_setting -- the shared helper both settings loaders now call
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("default,val,expect", [
    (True, False, False),
    (False, True, True),
    (6.0, 12.0, 12.0),
    (6.0, 12, 12.0),
    ("RESIDENCE", "My House", "My House"),
    ("RESIDENCE", 42, "42"),          # a non-string value still becomes str
])
def test_coerce_setting_preserves_the_declared_type(fp, default, val, expect):
    got = fp.coerce_setting("k", val, default)
    assert got == expect
    assert type(got) is type(expect)


def test_coerce_setting_falls_back_and_warns_on_an_uncoercible_number(fp):
    with pytest.warns(UserWarning, match="k"):
        got = fp.coerce_setting("k", "not-a-number", 6.0)
    assert got == 6.0


def test_coerce_setting_never_lets_a_string_through_float(fp):
    """0073-ruling.md sec2's own failure mode: a string setting, coerced by
    a bare `float()`, silently became its own default on every load. This
    is the property test; the round-trip below is the integration receipt
    against the real document loader."""
    assert fp.coerce_setting("title", "My House", "RESIDENCE") == "My House"


# ---------------------------------------------------------------------------
# the document loader's own receipt -- 0073 sec2: "RED today against a
# registered string key, GREEN after"
# ---------------------------------------------------------------------------

def test_document_loader_preserves_a_string_setting_round_trip(fp, win, monkeypatch):
    """Register a string-typed setting, load a document carrying it through
    `apply_design_to_scene`, and the string must survive -- not be replaced
    by its own default via the coercion loop `planio.py`/`design/bridge.py`
    both run."""
    from floorplanner.design.bridge import apply_design_to_scene
    monkeypatch.setitem(fp.DEFAULT_SETTINGS, "test_title", "Untitled")
    doc = {
        "format": "floorplanner-design", "version": 5, "units": "inches",
        "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0, "kind": "storey", "reference": False}],
        "vertices": [], "walls": [], "rooms": [], "furnishings": [],
        "groups": [],
        "settings": {"test_title": "My House"},
    }
    apply_design_to_scene(win, doc)
    assert fp.SETTINGS["test_title"] == "My House"


def test_document_loader_falls_back_to_default_when_absent(fp, win, monkeypatch):
    from floorplanner.design.bridge import apply_design_to_scene
    monkeypatch.setitem(fp.DEFAULT_SETTINGS, "test_title", "Untitled")
    fp.SETTINGS["test_title"] = "stale from a previous load"
    doc = {
        "format": "floorplanner-design", "version": 5, "units": "inches",
        "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0, "kind": "storey", "reference": False}],
        "vertices": [], "walls": [], "rooms": [], "furnishings": [],
        "groups": [],
        "settings": {},
    }
    apply_design_to_scene(win, doc)
    assert fp.SETTINGS["test_title"] == "Untitled"


# ---------------------------------------------------------------------------
# the JSON settings store -- Qt test mode sandboxes config_dir() so none
# of this touches the real user config directory
# ---------------------------------------------------------------------------

@pytest.fixture
def sandboxed_config(qapp, tmp_path, monkeypatch):
    """Qt test-mode AppConfigLocation, redirected further to a fresh
    tmp_path per test so parallel/repeat runs never share state."""
    QStandardPaths.setTestModeEnabled(True)
    monkeypatch.setattr(QStandardPaths, "writableLocation",
                        staticmethod(lambda loc: str(tmp_path)))
    try:
        yield tmp_path
    finally:
        QStandardPaths.setTestModeEnabled(False)


def test_json_store_round_trips_every_type_it_is_asked_to(fp, sandboxed_config):
    """0075-ruling.md sec1/sec2's own motivating case, first: a stored
    `False` must read back `False`, not `True` -- the exact QSettings/
    configparser hazard this store exists to eliminate."""
    s = fp.app_settings()
    s.setValue("shuffle", False)
    assert fp.app_settings().value("shuffle") is False
    s.setValue("auto_weld", True)
    assert fp.app_settings().value("auto_weld") is True
    s.setValue("wall_snap_in", 6.0)
    assert fp.app_settings().value("wall_snap_in") == 6.0
    s.setValue("title", "My House")
    assert fp.app_settings().value("title") == "My House"


def test_json_store_default_when_key_absent(fp, sandboxed_config):
    assert fp.app_settings().value("never_set", "fallback") == "fallback"


def test_settings_file_is_created_as_json_on_first_use(fp, sandboxed_config):
    assert not fp.settings_file().exists()
    fp.app_settings().value("anything")
    assert fp.settings_file().exists()
    data = json.loads(fp.settings_file().read_text(encoding="utf-8"))
    assert data.get("version") == 1


# ---------------------------------------------------------------------------
# migration -- 0075 sec3's own three clauses and receipt
# ---------------------------------------------------------------------------

def test_migration_carries_the_api_key_from_the_legacy_ini(fp, sandboxed_config):
    """A populated INI, no JSON: startup must produce a JSON file carrying
    the migrated key. RED if migration runs after materialisation (or not
    at all), GREEN when it runs first."""
    legacy = fp.config_dir() / "floorplanner.ini"
    legacy.write_text("[General]\nanthropic_api_key=sk-ant-legacy\n",
                      encoding="utf-8")
    assert fp.load_saved_api_key() == "sk-ant-legacy"
    assert fp.settings_file().exists()
    assert legacy.exists(), "the legacy INI must be left on disk, unread again"


def test_materialisation_never_mints_an_api_key_slot(fp, sandboxed_config):
    """No legacy INI at all: first use must not invent an `anthropic_api_key`
    entry -- a file created for every user on first launch does not mint a
    slot for a secret (0075 sec3 clause 2)."""
    fp.app_settings().value("wall_snap_in")
    data = json.loads(fp.settings_file().read_text(encoding="utf-8"))
    assert "anthropic_api_key" not in data


def test_migration_is_idempotent_after_the_json_exists(fp, sandboxed_config):
    """Once the JSON exists, migration never runs again -- a still-present
    INI naming a DIFFERENT value must not override what the JSON already
    says (0075 sec3 clause 1's idempotence: clear the key later and it does
    not come back). The JSON is written directly here, bypassing the
    migration path, so this exercises `_ensure_settings_file`'s own
    `if path.exists(): return path` guard, not just two identical reads."""
    legacy = fp.config_dir() / "floorplanner.ini"
    legacy.write_text("[General]\nanthropic_api_key=sk-ant-original\n",
                      encoding="utf-8")
    fp.settings_file().write_text(
        json.dumps({"version": 1, "anthropic_api_key": ""}),
        encoding="utf-8")
    assert fp.load_saved_api_key() == "", \
        "an existing JSON file was overridden by the still-present legacy INI"
