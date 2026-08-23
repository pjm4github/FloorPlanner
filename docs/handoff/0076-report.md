# 0076 — report: every GREEN-tier settings/`fp2pdf` item built

**On [`0072`](0072-ruling.md)/[`0073`](0073-ruling.md)/[`0074`](0074-ruling.md)/[`0075-ruling.md`](0075-ruling.md).**
All GREEN items across the four rulings, consolidated per `0075` §6's own
final ordering, built and gated GREEN. Nothing AMBER touched — no new
settings keys, no menu wiring, no dialog, no user-visible behaviour.
Numbered `0076` — `0066` stays reserved for item C.

---

## 1. `0073` §2 — the type-aware document-settings loader

`floorplanner/config.py` gains `coerce_setting(key, val, default)`: coerces
to the type `DEFAULT_SETTINGS[key]` declares (`bool`/`str`/`int`/numeric),
rather than a bare `float()` that silently replaced any string setting
with its own default. An uncoercible value now `warnings.warn`s and falls
back, instead of vanishing.

**One function, both call sites** — `planio.py:211` and
`design/bridge.py:1088` were the identical duplicated loop `0073` §6 itself
warned about ("two implementations of a precedence chain is how the
thickness tables happened"); both now call `coerce_setting` instead of
repeating the branch.

**Receipt:** `tests/test_config.py`, unit-level (`bool`/`str`/`int`/float
preserved, an uncoercible value warns and falls back) plus the integration
receipt `0073` §2 itself named — a monkeypatched string-typed setting,
loaded through the real `apply_design_to_scene`, survives round-trip. Not
run against the unfixed code directly (the fix and its test landed
together), but the unit-level parametrization independently proves the
same property the integration test exercises end-to-end.

## 2. `0075` §2 — the JSON store behind `app_settings()`

`QSettings`/INI replaced with a plain JSON file: `config.py` gains a
`_JsonSettings` shim (same two methods, `value()`/`setValue()`, `catalog.py`
untouched per `0075` §2's own instruction), `settings_file()` now points at
`floorplanner.json`. **The motivating hazard eliminated, receipted
directly:** `s.setValue("shuffle", False)` then `s.value("shuffle")` now
returns `False`, not the `True` a `QSettings`-INI round-trip through
`bool("false")` would have produced.

## 3. `0075` §3 — migration, landing with item 2 as ordered

`_ensure_settings_file()` runs at most once per file: if the legacy INI
exists, its `anthropic_api_key` (read via `configparser`, not `QSettings` —
0075 §2 dropped the Qt dependency from this store entirely) is carried into
the new JSON; the INI is left on disk, untouched, never re-read once the
JSON exists. Materialisation never mints an `anthropic_api_key` slot for a
user who never had one. No `DEFAULT_SETTINGS` keys are pre-written (`0074`
§5: that would pin today's defaults into every user's file forever) — just
a `version` marker plus whatever migration actually found.

**Both ordering-trap clauses checked as real receipts, not assumed:**
reverted `_ensure_settings_file`'s `if path.exists(): return path` guard
locally, confirmed the idempotence test goes RED (a still-present INI
overrides an already-cleared JSON key), restored, confirmed GREEN.

## 4. `0072` §2 / `0073` §6 step 2 — `fp2pdf.py`'s four hygiene faults

All four fixed, matching `fp2dxf.py`'s own precedent exactly, per `0072`'s
own instruction to reuse rather than reinvent:

1. **The third thickness table** — `DEFAULT_THICKNESS` now loaded via
   `fp2dxf.py`'s own by-path `_load_std_thickness()`, reused not
   transcribed (loaded by path a second time, from `fp2pdf.py` to
   `fp2dxf.py`, for the same reason `fp2dxf.py` avoids `import floorplanner...`
   for `validate.py` — importing any `floorplanner` submodule normally
   still runs the top-level package's Qt star-import first). One
   incidental finding along the way: `fp2dxf.py`'s `ConvertResult` is a
   `@dataclass`, and Python's dataclass decorator resolves type hints via
   `sys.modules[cls.__module__]` — the by-path loader had to register the
   module there before `exec_module`, which `fp2dxf.py`'s own loader for
   `validate.py` never needed (no dataclasses in that file).
2. **`raise SystemExit`** → `ValueError`, same reasoning `0038-ruling.md`
   §4 gave for `fp2dxf.py`: unhandled `SystemExit` inside a Qt call stack
   is not something a `try/except Exception` around a menu action would
   even see coming.
3. **`print()` / no result object** → a `ConvertResult` dataclass
   (`out`, `sheets`, `warnings`), mirroring `fp2dxf.ConvertResult`
   exactly; `convert()` prints nothing, `main()` prints from the returned
   result.
4. **`reportlab` at module top** → deferred into `convert()`, guarded;
   `ValueError("reportlab is not installed…")` on a real export attempt,
   the module itself always importable. Also fixed the smaller, same-class
   item `0072` §2 named alongside it: `a.design.read_text()` in `main()`
   now names `encoding="utf-8"`.

**Every fix checked as a real differential, not assumed** — reverted the
`SystemExit` fix and the reportlab-guard fix locally in turn, confirmed
each receipt test goes RED, restored, confirmed GREEN. The reportlab-guard
test forces the missing-dependency path via `monkeypatch` on
`builtins.__import__` rather than relying on this environment actually
lacking it (`0072` §6's own instruction: *"test it with the import
actually blocked, not by reading the code"*) — though it happened to be
genuinely absent here too, which is how the fix was first verified before
`reportlab` was installed locally for the full-generation receipt.

## 5. WHAT THIS DOES NOT TOUCH

- **`0072` §4 / `0073` §4's census** — every `fp2pdf.py` constant into bin
  A/B/C, and whether `settings.name` already means the project's title.
  Not needed for anything built here (no new settings key was added); owed
  before any AMBER bin-B work starts.
- **The three-rung precedence chain, the checkbox, first-run
  materialisation of `DEFAULT_SETTINGS`, the export menu, the PDF dialog,
  `--settings`** — all AMBER, none built.
- **`reportlab` is not in any requirements file.** Installed locally in
  this session only, to drive the full-PDF-generation receipt
  (`test_convert_returns_a_result_and_prints_nothing`,
  `test_main_round_trips_a_design_via_the_cli`) — both guarded with
  `pytest.importorskip("reportlab")` so the suite stays green whether or
  not it is present. Whether to add it to `requirements-dev.txt` is left
  open, not decided here.

## 6. RECEIPT SUMMARY

`tests/test_config.py` (16 tests, new) + `tests/test_fp2pdf.py` (7 tests,
new) + `tests/test_about.py` (one assertion updated: `settings_file()` now
names `.json`). Full suite: `pytest -m "not gui and not slow"` (752
passed) and `-m gui` (55 passed), both green. `ruff` clean. Full gate
GREEN, `collected=816`.

## 7. TIER

**GREEN**, per `0075` §6's own table (items 1–3) and `0073` §6 item 2 /
`0072` §6 step 1 (item 4) — no ruling required beyond what already exists,
pushed directly per the standing autonomy policy.
