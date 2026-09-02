# 0148 — report: R2c — Show roof / Edit roof

**Code, 2026‑09‑02, answering [`0145`](0145-ruling.md) §2 and
[`0146`](0146-ruling.md).**

---

## 1. WHAT'S BUILT

**Two checkable actions in the Roof menu**, `Show roof` and `Edit roof`,
invariant **Edit ⇒ Show**: unchecking Show forces Edit off (a hidden roof
cannot be the one being edited); checking Edit forces Show on. Both are
same-value-guarded setters (`MainWindow._set_show_roofs`/`_set_edit_roofs`,
mirroring `_set_shuffle`'s own shape exactly), so a load calling
`setChecked` to sync the UI never re-triggers the side effects.

**Three states, exactly as ruled:**

| state | render | input |
|---|---|---|
| hidden | `setVisible(False)` | Qt excludes an invisible item from `scene.items()` entirely — absent from every hit census, automatic or manual |
| shown, not editable | painted normally | `setEnabled(False)` stops Qt's own event dispatch; `RoofItem`/`RoofEndMarkerItem.shape()` ALSO empties out in this state, so manual scans (`RoomItem._outranked_at`, the ridge tool's own marker pre-check) miss it too — `setEnabled` alone is not enough, since only `shape()` governs a geometric `items(pos)` query |
| shown + editable | painted normally | full interactivity, unchanged from R2b |

A roof that stops being editable is deselected on the same pass, so no
stray selection outline survives a switch it can no longer be clicked to
clear.

**Persistence**: `show_roofs`/`edit_roofs` added to `DEFAULT_SETTINGS`
(default `True`/`True`, so every roof R1/R2/R2b already wrote stays
visible and editable without a migration at the *document* level) and
documented explicitly in the v5 schema's `settings` object (optional;
`additionalProperties: true` there already round-trips an unlisted key,
but explicit beats implicit). Round-trips through both the v5 bridge and
the legacy v1-v4 reader — one generic settings loop, no second path.

**A real gate this tripped, fixed properly, not around**: `DEFAULT_SETTINGS`
also drives the APP-LEVEL settings file (materialised in full, per
`0078-ruling.md`), and a dedicated test
(`test_changing_DEFAULT_SETTINGS_requires_a_version_bump`) exists
specifically to catch an edit to that dict landing without a version
bump — because full materialisation means an *existing* user's file has
no absent key left for a new default to fall through to. Bumped
`SETTINGS_VERSION` 1→2, wrote `_SETTINGS_MIGRATIONS`' first real row
(`_migrate_v1_to_v2`), and added the positive-control test the mechanism
never had: a genuine v1 file, migrated on load, both new keys present at
their defaults, rewritten to disk at version 2.

**The ridge-sketch tool** (menu action + toolbar button) disables itself
whenever `edit_roofs` is off — *"the roof sketch tools and marker only
operate with Edit ON."* Switching tool to it mid-way while a document has
Edit off is impossible via the UI; if `edit_roofs` turns off while the
ridge tool is already active, it reverts to Select. **The one exception,
handled directly**: a macro's bare `"G"` token reaches `TOOL_ROOF_RIDGE` by
calling `set_tool` directly, bypassing `QAction.isEnabled()` entirely — so
the force-on ("sketching the first ridge via the menu turns both switches
on") lives at the gesture itself (`view.py`'s `TOOL_ROOF_RIDGE` press
branch), not only at the action that ordinarily starts it.

## 2. THE RECEIPT — the differential named in the ruling

Headless, a wall and a roof sharing the same point:

```
Edit ON:  items at the ridge point = {RoofItem, WallItem}
Edit OFF: items at the ridge point = {WallItem}            # the roof vanished
Hidden:   items at the ridge point = {WallItem}             # same, by construction
```

*"the same click on a ridge selects the wall under it with Edit off and
the ridge with Edit on; hidden, the roof appears in no hit census at
all"* — confirmed exactly, both halves.

## 3. TESTS AND GATE

`tests/test_roof_visibility.py` (new, 14 tests, `gui`-marked): defaults,
backward compatibility for pre-R2c documents, both invariant directions,
the same-value no-op guard, all three states' paint+hit-test behavior
together, marker inheritance from its parent, the ridge tool's
enable/disable and its mid-tool revert, the macro-bypass force-on case,
and a full save/load round trip. `tests/test_config.py` (+1): the
settings-migration positive control above.

Full suite: **1116 passed**, 7 deselected (`perf` lane), 0 failures.
`ruff` clean. `python tools/gate.py` (full mode): **GREEN**.

## 4. DISPOSITION

**R2c is AMBER tier** ([`0145`](0145-ruling.md) §4's order: R2b → **R2c**
→ R3 → R3b → R4 → R5, one at a time) — built and gated GREEN, going to its
own branch and PR next, and Code stops there: no merge without Patrick's
own check. §2 above answers the differential headless; the PR is for him
to run by hand — toggle both switches on a real ridge, confirm painting
and clicking behave as the table above says at each of the three states.

**R3 does not start** until this merges.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
ridge/eaves horizontal repositioning (R4).
