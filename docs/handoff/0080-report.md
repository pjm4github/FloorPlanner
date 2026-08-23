# 0080 — report: every GREEN item across `0077`/`0078` built

**On [`0077-ruling.md`](0077-ruling.md) / [`0078-ruling.md`](0078-ruling.md).**
`0078` §4's full table, items 1–7, built and gated GREEN. Item 8 (the
read-back and everything AMBER) is unchanged, still owed.

---

## 1. `0077` §2 — the bool branch parses text explicitly

`coerce_setting`'s bool branch was still `bool(val)` on anything not
already a `bool` — `bool("false") is True`, the exact hazard `0075`
eliminated from the app-settings store, alive again in the coercer whose
job is not to do that. Now: a real `bool` passes through, a string is
matched against `"true"/"1"` / `"false"/"0"` (case-insensitive), anything
else warns and falls back to the default.

**Receipt:** `coerce_setting("shuffle", "false", True) is False` and five
more token cases; an unrecognised token warns. Confirmed real — no revert
needed here, since `bool("false")` demonstrably being `True` today (before
this landed) already differentiates old from new behaviour by construction.

## 2. `0077` §6 — `reportlab` into `requirements-dev.txt`

One line, with the reasoning: dev/test only, per D40 — the app still runs
without it (`0072`'s guard, `0076`'s deferred import, both unchanged).
`test_convert_returns_a_result_and_prints_nothing` and
`test_main_round_trips_a_design_via_the_cli` now actually render a PDF on
every CI run instead of being silently `importorskip`'d — `0077` §6's own
finding that `collected=816` had never meant what it looked like it meant.

## 3. `0077` §3 — the missing differential

`0076` said plainly it had not reverted a loader call site to prove the
suite would catch a regression. Done: `design/bridge.py:1090`'s
`coerce_setting(...)` reverted to the old bare `float()`/`bool()` shape
locally, confirmed **both**
`test_document_loader_preserves_a_string_setting_round_trip` and
`test_document_loader_falls_back_to_default_when_absent` go RED
(`ValueError: could not convert string to float: 'Untitled'`), restored,
confirmed GREEN. `planio.py`'s own call site not separately reverted —
`0077` itself named this as "one revert... closes it."

## 4. `0077` §5 — `_stdt.py`, a leaf, lazy

New `floorplanner/export/_stdt.py`: nothing but the by-path loader for
`floorplanner.design.validate.STD_T`, no imports beyond the standard
library, no dataclasses. **Both** `fp2dxf.py` and `fp2pdf.py` now load
THIS file by path instead of `fp2pdf.py` execing the whole of `fp2dxf.py`
to borrow its loader — the `sys.modules` registration hack that coupling
needed (to satisfy `fp2dxf.py`'s own `ConvertResult` `@dataclass`) is
gone, because `_stdt.py` has nothing for a dataclass to trip over.

**Lazy, not module scope**, matching the shape `reportlab`'s deferred
import already has: `fp2dxf.STD_T` and `fp2pdf.DEFAULT_THICKNESS` (plain
module constants, computed at import) become `_std_t()` /
`_default_thickness()` (functions, cached after first call, computed on
first *use*). Every internal reference updated (`Ctx`'s
`default_factory`, `main()`'s `--set` validation in both files).

**Receipt:** `test_module_imports_with_fp2dxf_absent` — renames
`fp2dxf.py` aside on disk (restored in `finally`, whatever happens),
loads a throwaway copy of `fp2pdf.py` under a separate module name so the
real, already-imported `floorplanner.export.fp2pdf` is untouched, and
confirms it imports and still resolves the real `STD_T` via `_stdt.py`
alone. `fp2dxf.py` genuinely absent from disk during the assertion, not
merely unimported.

## 5. `0077` §6 — the corrupt-settings-file path

`_JsonSettings.__init__`'s old `except (OSError, ValueError): self._data
= {}` treated a truncated write (power loss, full disk) identically to a
file that simply doesn't exist yet — silently starting empty, and the
next `setValue` would have overwritten the corrupt file with `{}` plus one
key, unreported (`catalog.py`'s own `except Exception: return ""`
guarantees nobody would hear about it).

**Now:** `_ensure_settings_file` distinguishes "genuinely absent" from
"exists but will not parse." A file that will not parse is renamed aside
as `<name>.bad`, a `UserWarning` names it once, and a fresh file is
materialised in its place. **Migration from the legacy INI does NOT
re-run on quarantine-recovery** — a JSON existed here once, so the INI
stays dead exactly as ordinary idempotence (`0075` §3) already requires;
re-consulting it on every corruption would let a corrupted file become a
backdoor for resurrecting an intentionally-cleared key.

**Receipt:** reverted the quarantine branch locally (`_ensure_settings_file`
just returning the corrupt path unexamined), confirmed both the
quarantine test and the no-re-migration test go RED, restored, confirmed
GREEN.

## 6/7. `0078` §1/§2 — materialisation, `SETTINGS_VERSION`, the migration table, the pin

**§1**: `_ensure_settings_file` (via a new `_materialize_settings`) now
writes **every** `DEFAULT_SETTINGS` key at its default value, plus
`version` — Patrick's own words, *"I want to see the settings in the
file."* No exception list: `auto_bind` is in the file (the model has the
flag; the dialog hiding it is unrelated). `anthropic_api_key` is added
**only** when migration found a real one, per `0075` §3 clause 2,
unchanged.

**§2**: with full materialisation there are no absent keys left for a
future default change to reach an existing user through — `0074` §5's
mitigation is void the moment every key is written. `config.py` gains
`SETTINGS_VERSION` (`1`), an ordered `_SETTINGS_MIGRATIONS` table (empty:
there is no version 0 to migrate *from*, but the mechanism exists and is
tested before it is ever needed), and `_migrate_settings_data`, applied
on every load in `_JsonSettings.__init__` — a file whose `version` is
behind gets walked forward and written back; a file already current costs
one comparison.

**The pin, mechanical not remembered:**
`test_changing_DEFAULT_SETTINGS_requires_a_version_bump` hashes
`DEFAULT_SETTINGS`'s keys, types **and** values and asserts it against a
value pinned to `SETTINGS_VERSION == 1`. **Confirmed it actually
discriminates** — changed `DEFAULT_SETTINGS["wall_snap_in"]` to `12.0` in
a scratch check, the fingerprint changed (`1ed175834bdbb015` →
`04ac111f339c8f1f`); the real file was never touched.

## 8. WHAT THIS DOES NOT TOUCH

- **`0074` §6 item 0's read-back** and everything AMBER — the three-rung
  precedence chain, the "use as default" checkbox, the note-label
  rewrite, the export menu, the PDF options dialog, `--settings`. None
  built.
- **`0066` item 2** — the orthogonality repair itself, still blocked on
  `0079-report.md`'s read-back being ruled.

## 9. RECEIPT SUMMARY

`tests/test_config.py` grew from 23 to 28 tests (the boolean-text
parametrization, the pin, two corruption tests); `tests/test_fp2pdf.py`
grew by one (`test_module_imports_with_fp2dxf_absent`). Full suite:
`pytest -m "not gui and not slow"` (770 passed) and `-m gui` (55 passed),
both green — `collected` numbers now genuinely exercise PDF generation,
per `0077` §6. `ruff` clean. Full gate GREEN.

## 10. TIER

**GREEN**, per `0078` §4's own table for items 1–7 — no ruling required
beyond what already exists.
