# 0073 — ruling: settings precedence for `fp2pdf` — and there is no settings FILE to add them to

**On Patrick's own instruction**, amending [`0072`](0072-ruling.md) §5. Quoted so
the authority is auditable ([`0069`](0069-report.md) §4's clause):

> *"The settings that are hard coded in that file should be overridden by the
> tool settings where available. For items that are not in the floorplanner
> settings file, those items should be added to the floorplanner settings file.
> After adding those settings then all settings from the fp2pdf file should be
> overloaded by the floorplanner settings file. When used standalone then the
> settings in the file itself can be used. There should be another command line
> switch added to the standalone application so that a settings file can be
> read into the application on the command line."*

**Accepted in full. [`0072`](0072-ruling.md) §5's "no GUI control for `--set`"
is NARROWED, not withdrawn — §4 below.** Three measured facts change how it must
be built, and one of them is a silent data-loss trap directly across the path.

---

## 1. THERE IS NO FLOORPLANNER SETTINGS FILE — the settings live IN THE PLAN

**Measured.** `SETTINGS` is a module-global dict in `config.py`, seeded from
`DEFAULT_SETTINGS`, edited in File ▸ Settings…, and — `config.py:56`, its own
comment — *"saved in the file."* It is written into the **plan document's
`settings` block** (`planio.py:386`, `bridge.py:887`) and read back on load.
**There is no application-level config file anywhere.**

> ### SO "ADD THEM TO THE FLOORPLANNER SETTINGS FILE" MEANS "ADD THEM TO THE v5 DOCUMENT SCHEMA."
>
> Every key added is carried by **every plan ever saved from now on**, and the
> schema is a contract this project has already had to defend twice (D24, D73).
> **That is not a reason to refuse — it is Patrick's call and it is made — but
> it is a schema change**, so `ROADMAP.md`'s GREEN criterion (*"no format or
> schema change"*) **excludes it from GREEN by its own words.** §6 tiers it
> accordingly.

## 2. THE TRAP — THE LOADER CANNOT CARRY A STRING, AND FAILS SILENTLY

**Both load paths do the identical thing** (`planio.py:211-219`,
`bridge.py:1088-1096`):

```python
for key, default in DEFAULT_SETTINGS.items():
    val = ...
    if isinstance(default, bool):
        SETTINGS[key] = bool(val); continue
    try:
        SETTINGS[key] = float(val)
    except (TypeError, ValueError):
        SETTINGS[key] = default          # <- SILENT
```

**Every non-bool setting is coerced to `float`, and anything that will not
float is replaced by the default with no error, no warning, no status line.**

The settings Patrick most obviously wants — **title, subtitle, author, assembly
note, dimension note** — are all strings.

> ### ADD THEM TO `DEFAULT_SETTINGS` AS THEY STAND AND THEY ARE DESTROYED ON EVERY LOAD.
>
> The user types a project title, saves, reopens — **and it is `"RESIDENCE"`
> again.** Nothing reports it. **This is the whole `except: use the default`
> family [D6](../defects/0006-8-except-valueerror-continue-silently-delete-an.md)
> was filed for, sitting on the exact path this instruction walks down.**

**AND THE PERVERSITY IS WORTH STATING, because it inverts the obvious move.**
`bridge.py:1100` keeps every setting the walk does not model:

```python
win._doc_settings = {k: v for k, v in settings.items()
                     if k not in WALK_SETTINGS and k != "active_floor"}
```

merged back on save at `planio.py:418`. **An UNREGISTERED key round-trips
intact. A key registered in `DEFAULT_SETTINGS` goes through the float coercion
and is annihilated.** **Registering a string setting today makes it strictly
worse than leaving it unknown.**

**OWED, and it comes before any new key:** the loader learns types — `str`
stays `str`, `bool` stays `bool`, numbers stay numbers — **and a value it cannot
coerce is reported, not swallowed.** **Receipt: a round-trip test that saves a
document with a string setting, reloads it, and asserts the string survived.**
RED today against a registered string key, GREEN after.

## 3. THE PRECEDENCE CHAIN — one rule, two faces

Patrick fixed three of the four rungs. **The fourth is mine to rule: an explicit
CLI flag against a `--settings` file.** Explicit wins — it is the more specific
and later statement of intent, and it is what every tool this project already
ships does.

| | embedded (the GUI) | standalone (`python -m …fp2pdf`) |
|---|---|---|
| **4 — highest** | the export dialog's own fields | an explicit CLI flag (`--title …`) |
| 3 | — | `--settings FILE` |
| 2 | the open document's `settings` block | the design document's own `settings` block |
| **1 — floor** | `fp2pdf.py`'s module constants | `fp2pdf.py`'s module constants |

> **The export dialog is to the GUI what the flags are to the CLI**, so this is
> one chain, not two — and *"when used standalone the settings in the file
> itself can be used"* falls out of rung 1 rather than needing a rule.

**AND ONE SIMPLIFICATION THAT MAKES ROW 2 FREE.** `fp2pdf` already takes the
design document as its positional argument, **and that document already carries
a `settings` block.** So standalone reads `design["settings"]` **by default**,
with `--settings OTHER.json` overriding it — **embedded and standalone then
resolve settings by the same code, from the same block, in the same order.**

**`--settings` accepts EITHER a full v5 document (its `settings` object is read)
OR a bare JSON object of setting keys.** **One format, not two.** A second
settings format is a second thickness table with a different name on it.

**If "the settings in the file itself" meant `fp2pdf.py`'s constants and not the
design's own block, say so and I will invert row 2 in one line** — but the
chain above delivers what was asked either way, and is strictly better when the
document has the values.

## 4. WHAT MOVES, WHAT DOES NOT — three bins, and the census must place every constant

**Not every hardcoded number is a setting.** The test, and it is one question:

> **Would two different plans ever legitimately want different values, and would
> the user expect it saved with the plan?**

| bin | what | disposition |
|---|---|---|
| **A — already owned** | `DEFAULT_THICKNESS` | **Read `STD_T` by path** (`fp2dxf._load_std_thickness`, reused not transcribed), honouring each wall's own `thickness_in` override first, exactly as `fp2dxf.wall_thickness()` does. **NOT added to the settings block** — it is available in the tool, which is Patrick's own *"where available"*. **A fourth copy is D73 a third time** |
| **B — genuine settings** | title, subtitle, author, assembly note, dimension note, page size, scale preference, include-concept | **Added to `DEFAULT_SETTINGS` and the schema** — but only after §2 |
| **C — presentation internals** | `GRAY_POCHE`, `GRAY_LT`, `DIM_LANE`, `TITLE_H`, tick geometry | **Stay module constants.** Drafting minutiae in a document contract are permanent and unremovable |

**[`0072`](0072-ruling.md) §5 said the dialog carries no `--set` control. That
stands and its reason is unchanged** — a widget that lets a user contradict
`STD_T` reopens D73 through the front door. **`--set` survives on the CLI only,
as a standalone escape hatch, and it does not gain a GUI.**

**AND CHECK BEFORE MINTING `title`.** `bridge.py:109`'s comment names an
existing document setting — *"anything else in a document's settings (e.g.
`name`)"*. **If `settings.name` already means the project's name, `title` must
read it rather than become a second one.** **Census it first. Minting a
duplicate identity key is the exact fault this ruling is otherwise about.**

## 5. THE SETTINGS DIALOG

`dialogs.py:624 SettingsDialog` — *"plan-wide preferences, saved in the plan
file"* — is where bin B belongs, **not** a second preferences surface bolted to
the export dialog. **The export dialog edits them for this export; File ▸
Settings… is where they persist.** Two widgets, one set of keys, and the
precedence table says which wins.

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 0 | **The census** — every constant in `fp2pdf.py` into bin A/B/C, plus whether `settings.name` exists and what it means | **GREEN.** No code. **[`0072`](0072-ruling.md) §6 step 0 absorbs this** |
| 1 | **§2 — the type-aware loader + its round-trip receipt** | **GREEN.** No new key, no user-visible change; it fixes a silent-loss path that already exists |
| 2 | **[`0072`](0072-ruling.md) §6 step 1 — `fp2pdf`'s four hygiene faults** | **GREEN**, unchanged |
| 3 | **§4 bin B — the new settings keys + `SettingsDialog` rows** | **AMBER.** A schema change and new UI. **Read-back first: the exact key list, types, defaults, and what an existing plan without them does** |
| 4 | **§3 — `--settings`, and the resolution order as ONE function** | **AMBER.** It changes what an export produces |
| 5 | **[`0072`](0072-ruling.md) §6 steps 2–3 — the submenu and the PDF action** | **AMBER**, unchanged |
| 6 | **[`0072`](0072-ruling.md) §3 — the application CLI** | **RED**, unchanged. `--settings` belongs to `fp2pdf`'s own parser, which exists; the *editor* still has none |

> **ONE FUNCTION, NOT TWO.** The resolution order in §3 is written **once** and
> both callers use it. **Two implementations of a precedence chain is how the
> thickness tables happened** — and the receipt is a test that drives all four
> rungs and asserts the winner at each.

**PATRICK'S CHECK, when it exists — one question, batched with the four already
waiting:**

> **"Set a project title and an assembly note, save, reopen, export a PDF —
> does the title block say what you typed?"**

**One open question, and it is one line to answer** — §3's last paragraph: *the
design document's own `settings` block, or `fp2pdf.py`'s constants, as the
standalone fallback?* **Code should not guess it; I have ruled the first and
flagged it.**

**`0066` — item C — remains reserved and unwritten, no promise attached
([`0070`](0070-ruling.md) §8).**
