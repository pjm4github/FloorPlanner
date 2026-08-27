# 0116 — ruling: the Export menu — [`0072`](0072-ruling.md) §4–§5 unblocked, with every prerequisite now measured DONE

**Patrick, 2026‑08‑25**, re-raising the one feature he asked for that never got
built: collect the File menu's exports into one section, and add **Export PDF
Drawings** wired to `fp2pdf.py` with a Save As dialog.

**Already ruled at [`0072`](0072-ruling.md) §4–§5 (2026‑08‑22) and stalled
behind the PR queue, which is now empty. This unblocks it; nothing is re-ruled.**

---

## 1. THE PREREQUISITES ARE ALL DONE — measured today

| [`0072`](0072-ruling.md) §6 step 1 required | state |
|---|---|
| `convert()` raises `ValueError`, not `SystemExit` | ✅ `fp2pdf.py:592` |
| `ConvertResult`, no `print()` in `convert()` | ✅ `:573` |
| `reportlab` deferred, module always importable | ✅ `:71` |
| the thickness table from `_stdt.py`, not a copy | ✅ `:46` |

**So the wiring that was AMBER-behind-fixes is now AMBER-ready.**

## 2. THE SHAPE — as ruled, two reminders

**The menu** ([`0072`](0072-ruling.md) §4): a real `m_file.addMenu("&Export")`
submenu — **Rooms as CSV… / Chief Architect (DXF)… / PDF plan set… / Legacy
v4…** — the literal `▸` removed from the DXF label, **existing slots keep their
names** (re-parent, not rewrite), the two Import actions untouched. **The census
first: every test, macro and doc that names a File-menu path.**

**The PDF action** ([`0072`](0072-ruling.md) §5): copy `export_dxf` /
`export_dxf_path`'s two-method shape **except the dialog** — PDF is one file, so
**`QFileDialog.getSaveFileName`**, not the DXF folder picker. Interactive method
shows the dialog; `_path` method converts, catches `ValueError`/`OSError`,
surfaces `ConvertResult`'s sheets + warnings in the completion dialog, returns
the result for tests. Title defaults from the document's name, not
`"RESIDENCE"`. **No thickness override control** (§5's D73 reason stands).
**`reportlab` missing → the menu item disabled with a reason, not a crash** —
and its test blocks the import, per [`0072`](0072-ruling.md) §6.

**Options dialog fields:** title, subtitle, author, assembly note, dim note,
level selection, include-concept. The `--settings`/precedence machinery
([`0073`](0073-ruling.md) §3) is **not** in scope here — the dialog's own fields
are rung 4 and suffice for a first delivery.

## 3. TIER AND ORDER

| | | |
|---|---|---|
| 0 | the menu-path census | **GREEN**, no code |
| 1 | the Export submenu re-parent | **AMBER** |
| 2 | Export PDF Drawings + Save As + completion dialog | **AMBER**, same branch |

**One PR, one check:**

> **Open your own plan. File ▸ Export ▸ PDF plan set… — does the Save As dialog
> land where you expect, and does the PDF that opens look like your drawing?
> Then glance at the menu: are all four exports in one place?**

**Nothing else is in flight, so this is the only branch** — the
single-AMBER-at-a-time rule from [`0111`](0111-ruling.md) §5 holds.
