# 0072 — ruling: the export menu, and `fp2pdf.py` arrives with four faults `fp2dxf.py` was fixed for five days ago

**On Patrick's own request** — wire `floorplanner/export/fp2pdf.py` into the
app, group the File menu's exports, merge its CLI switches, and give it an
options + Save-As dialog. **His instruction is the authority (`ca3c6b7`); quote
it in the report per [`0069`](0069-report.md) §4.**

**[`0071-report.md`](0071-report.md) is read and NOT ruled here** — it is a
strong report on its face (the A/B answered [`0070`](0070-ruling.md) §4's open
question, the fix is one site, the receipt was checked to discriminate). It gets
its own ruling; say the word.

**Read from the tree:** `fp2pdf.py` entire, `fp2dxf.py`'s loader and hygiene
comments, `export/__init__.py`, `mainwindow._build_menus`, `planio.export_dxf*`,
`app.py`'s `main()`, all four requirements files, `tests/test_fp2dxf.py`'s
header.

---

## 1. THE CENSUS — four exports, two groups, and a `▸` that is only text

**The File menu as built (`mainwindow.py:258-300`):**

```
New plan / Open…
Import rooms from CSV… / Import from image (PNG)… / Export rooms to CSV…   <- export #1, filed with the IMPORTS
────────────
Save / Save As… / Export legacy v4… / Export ▸ Chief Architect (DXF)…      <- exports #2, #3, filed with SAVE
────────────
Load template room… / Save template room…
```

**Three exports, in two unrelated groups, and neither group is about
exporting.** Patrick is right that this wants collecting.

> **The `▸` in "Export ▸ Chief Architect (DXF)…" is literal text inside a flat
> `QAction`.** [`0050-report.md`](0050-report.md) said so itself at the time —
> *"one flat File-menu entry, not a nested submenu — the `▸` is only in the
> label text"* — flagged, never ruled. **Patrick's request closes a gap Code
> named against itself and nobody answered.**

## 2. `fp2pdf.py` REPEATS FOUR FAULTS THIS PROJECT RULED OUT OF `fp2dxf.py` — measured, all four

**`tests/test_fp2dxf.py`'s own header records that `fp2dxf` shipped with the
first of these, that [`0038`](0038-ruling.md) §2–§3 found it, and that it was
fixed. `fp2pdf.py` lands five days later, in the same package, with the same
four.**

### (1) A THIRD wall-thickness table — and it disagrees in four of seven rows

```python
# floorplanner/export/fp2pdf.py:41
DEFAULT_THICKNESS = {"exterior": 6.5, "interior": 4.5, "partition": 3.5,
                     "railing": 3.0, "fence": 1.5, "hedge": 24.0, "retaining": 8.0}
# floorplanner/design/validate.py:17  -- THE NORMATIVE TABLE (D73)
STD_T =              {"exterior": 6.0, "interior": 4.5, "partition": 3.5,
                      "railing": 2.0, "fence": 2.0, "hedge": 18.0, "retaining": 8.0}
```

| type | `STD_T` | `fp2pdf` | |
|---|---:|---:|---|
| **exterior** | **6.0** | **6.5** | ✗ |
| interior | 4.5 | 4.5 | ✓ |
| partition | 3.5 | 3.5 | ✓ |
| **railing** | **2.0** | **3.0** | ✗ |
| **fence** | **2.0** | **1.5** | ✗ |
| **hedge** | **18.0** | **24.0** | ✗ |
| retaining | 8.0 | 8.0 | ✓ |

> ### THIS SHEET'S OWN TITLE BLOCK SAYS *"All dimensions to overall wall faces."*
>
> **The faces are drawn from this table.** Every exterior overall dimension on
> every sheet is **0.5″ wide**, on a document whose stated purpose is transmittal
> to a receiving designer who *"converts to their own convention."* **D73 is
> this defect with two tables. This makes three**, and the wrong one is the one
> printing numbers a builder reads.

**`export/__init__.py` — the package's own front door — already says what to
do:** *"Where a fact genuinely belongs to the rest of the app (**wall
thickness**, the schema), the module loads the ONE file that owns it BY PATH
(`importlib`)."* **`fp2dxf._load_std_thickness()` is that function, twenty
lines away. Reuse it; do not transcribe it** — a second copy of the loader would
be the same disease one level up.

### (2) `raise SystemExit` inside `convert()`

`fp2pdf.py:541`. **[`0038`](0038-ruling.md) §4 "ONE" ruled this out, and
`fp2dxf.py:468` carries the reason in a comment:** *"A NORMAL EXCEPTION, NOT
`raise SystemExit` … `SystemExit` inside a Qt call stack is not [catchable]."*
**Patrick is asking for exactly the Qt call stack that comment is about.**

### (3) `print()` inside `convert()`, and no result object

`fp2pdf.py:552,554` print the sheet list and the output path from inside
`convert()`, which returns a bare `Path`. **[`0043`](0043-report.md) measured
this fixed for `fp2dxf`: printing confined to the CLI entry point, `convert()`
returning warnings and summary on a `ConvertResult`.** `planio.export_dxf_path`
then *"only has to surface them instead of printing them."*

> **Patrick asked for a completion dialog. As written there is nothing to put in
> it, and the sheet list goes to a console a GUI does not have.**

### (4) `reportlab` imported at module top, and in no requirements file

`from reportlab.lib.pagesizes import landscape` runs at import. **`reportlab`
appears in none of `requirements.txt`, `-dev`, `-viewer`, `pyproject.toml`.**
And `planio.py:52` imports its sibling exporter **at module level**:

```python
from floorplanner.export.fp2dxf import convert as convert_to_dxf
```

> ### COPY THAT LINE FOR PDF AND THE APPLICATION STOPS STARTING FOR ANYONE WITHOUT `reportlab`.
>
> **[D40](../defects/0040-a-missing-optional-dependency-must-degrade-not.md):
> a missing optional dependency must degrade, not die.** `app.py`'s own
> `set_3d_surface_format()` is the seam, in its own words — *"a missing optional
> dependency is a fact to report, not a fault"* — and **`requirements-viewer.txt`
> is the packaging precedent, verbatim: *"optional; the editor runs without
> it."***

**Also, one line, same class:** `json.loads(a.design.read_text())` — no explicit
encoding. [`0043`](0043-report.md)'s fourth hygiene item.

## 3. THE CLI ASK PRESUPPOSES SOMETHING THAT DOES NOT EXIST

> *"The command line switches in fp2pdf.py will need to be merged with existing
> floorplanner command line options."*

**Measured: there are none.** `FloorPlanner.py` has no `argparse`. The
application's entire command line is one line in `app.py`:

```python
if "--verify-design" in sys.argv:
    sys.argv.remove("--verify-design")
```

**There is nothing to merge into.** The ask is not a merge — it is *"give the
editor a command line,"* and that carries its own unruled questions: does a
plan path on `argv` open it; does `-o` mean **headless** export (and does this
Qt app run headless at all); where does `--verify-design` sit in a real parser;
does the GUI even want `--set` once §2(1) is fixed.

> **SPLIT, NOT BUNDLED. Ordering it inside the menu task is precisely how a
> GREEN item goes RED mid-flight** — `ROADMAP.md` stop-condition (a), *"a
> measurement changes the item's scope."* **It is RED until it has its own
> ruling, and Code does not start it.** `fp2pdf`'s own `main()` keeps working
> as a standalone `python -m` entry point meanwhile, which is what
> `export/__init__.py` says these modules are for.

## 4. THE SUBMENU — the two decisions Patrick did not make, ruled so nothing is guessed

He named three: **Rooms as CSV, DXF, PDF.**

* **"Export legacy v4…" joins them.** It is an export, it is currently filed
  under Save, and leaving one export outside an Export menu rebuilds the
  problem. **Ruled: four entries.**
* **The two Import actions do NOT move.** He asked about exports. **Not
  touched, not renamed** — scope creep into a menu he did not mention is how a
  check question stops being answerable.

**The shape:**

```
File
  …
  Save / Save As…
  ────────────
  Export ▸   Rooms as CSV…
             Chief Architect (DXF)…
             PDF plan set…
             Legacy v4…
```

**A real `m_file.addMenu("&Export")`, not a label containing "▸" — and the
literal `▸` comes out of the DXF label**, since the character is now the menu
widget's job. **Every existing slot keeps its name** (`export_rooms_csv`,
`export_legacy_v4`, `export_dxf`): this is a re-parent, not a rewrite.

**The census this owes before the edit:** every test, macro and doc that names a
File-menu path or triggers these actions by label. A menu re-parent that
silently breaks a macro is a user-visible regression wearing a refactor's
clothes.

## 5. THE DIALOG — copy `export_dxf`'s shape exactly, except in the one place it must not be copied

**`planio.export_dxf` / `export_dxf_path(outdir, interactive=True)` is the
pattern and it is already right:** the interactive method puts up the dialog and
nothing else; the `_path` method does the work, catches `ValueError`/`OSError`,
builds the report text, and **returns the result object so a test or macro can
read it without parsing dialog text.**

> ### THE ONE DIFFERENCE: **PDF IS A SINGLE FILE.**
>
> DXF prompts for a **folder** because `fp2dxf` writes a `.dxf`/`.openings.json`
> pair **per level**. `fp2pdf` writes **one PDF with one sheet per level**. So
> the PDF action uses **`QFileDialog.getSaveFileName`**, not
> `getExistingDirectory` — that is Patrick's "Save As type dialog", and copying
> the DXF precedent here would be copying it wrong.

**The options dialog carries:** title, subtitle, author, assembly note,
dimension note, level selection, include-concept. **Default the title from the
current document's name, not `"RESIDENCE"`.**

**It does NOT carry `--set` (thickness overrides).**

> **Once §2(1) is fixed the thicknesses come from `STD_T`. A GUI control that
> lets a user contradict the one table would re-open D73 through the front
> door** — and this time with a widget inviting it. **If `--set` survives at
> all it survives on the CLI, where §3 has not been ruled yet.**

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 0 | **§4's census** — callers of the four export slots, tests/macros naming a menu path, whether CI has `reportlab` | **GREEN.** No code |
| 1 | **§2's four fixes to `fp2pdf.py`, BEFORE any wiring** | **GREEN** — the module is not reachable from the app yet, so none of it is user-visible. **Each with its own receipt** (below) |
| 2 | **§4 — the Export submenu re-parent** | **AMBER.** It changes what the user sees |
| 3 | **§5 — the PDF action, options dialog, Save-As** | **AMBER** |
| 4 | **§3 — the application CLI** | **RED. Do not start.** Its own ruling |

**The receipts for step 1, named so they are not left to taste:**

* thickness — **a test that fails if the exporter's table diverges from
  `STD_T`**, mirroring `tests/test_fp2dxf.py`'s. Not a test that asserts the
  seven current numbers.
* `SystemExit` — `convert()` on a non-v5 document raises **`ValueError`**, and
  the test asserts the type.
* prints — `convert()` returns sheets-written + warnings and **prints nothing**;
  assert on captured stdout, not just on the return value.
* `reportlab` — **the app starts with the import blocked**, and the PDF entry is
  **disabled with a reason**. Test it with the import actually blocked, not by
  reading the code.

## 7. THE THING I CAN SEE FROM HERE THAT NOBODY INSIDE THE WORK CAN

**PR #34, PR #35 and PR #36 are all open, all AMBER, all stopped on one
fifteen-minute session with Patrick.** Steps 2 and 3 above would make it four.

> `ROADMAP.md` §1 opens: *"The bottleneck has never been review. It is unruled
> questions."* **That was true when it was written and it is not true now.**
> Every question in flight is ruled. **What is queued is Patrick's eyes**, four
> deep, on one person who is also the only person who can answer them.

**Not a stop condition, and I am not ordering a process change** — but step 1 is
GREEN and unblocked, so **build step 1 now and let steps 2–3 stack behind the
check session rather than racing more AMBER work onto the same queue.** If the
queue reaches five, that is worth its own ruling and I will write it.

**`0066` — item C — remains reserved and unwritten. No promise attached
(`0070` §8).**
