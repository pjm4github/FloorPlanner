# 0074 — ruling: the settings file already exists — and `0073` §1 was wrong to say it did not

**On Patrick's own instruction**, quoted so the authority is auditable:

> *"Lets add a settings file that is maintained in a default location for the
> floorplanner. Use a standard settings file format for each setting. When the
> app is loaded then the settings is read in (if it exists), if it doesn't exist
> then it creates a default version. When the user opens the settings menu and
> clicks Save then it updates the file on disk and, of course, updates the
> program settings."*

---

## 1. I WAS WRONG IN [`0073`](0073-ruling.md) §1, AND THE REFUTATION IS IN THE FILE I QUOTED FROM

[`0073`](0073-ruling.md) §1, in bold: *"**There is no application-level config
file anywhere.**"*

**`floorplanner/config.py`, thirty lines below the `DEFAULT_SETTINGS` dict I
quoted out of that same file:**

```python
def config_dir() -> Path:
    """Per-user config directory in the OS-standard location, created on
    demand (e.g. %APPDATA%/FloorPlanner on Windows, ~/.config/FloorPlanner
    on Linux, ~/Library/Application Support/FloorPlanner on macOS)."""

def settings_file() -> Path:
    """The app-wide settings file (INI) holding cross-session preferences…"""
    return config_dir() / "floorplanner.ini"

def app_settings() -> QSettings:
    """QSettings backed by settings_file() so preferences live in a real,
    standard-location INI file (not the Windows registry)."""
```

> ### I ASSERTED A NEGATIVE WITHOUT SEARCHING FOR IT, AND THE THING I DENIED WAS IN THE FILE ON MY SCREEN.
>
> Third correction of this kind in this run — [`0065`](0065-ruling.md) §4's
> provenance, [`0068`](0068-ruling.md) §1's re-read, this. **All three are the
> same move: a claim about what exists, stated from what I had already looked
> at rather than from a search.** `grep SETTINGS` is not `grep QSettings`, and
> I ran the first and reported on the second.

**AND IT CHANGES THE ANSWER, which is why it matters more than the apology:
most of what Patrick just asked for is already built.**

| his ask | state |
|---|---|
| a settings file in a **default location** | ✅ `config_dir()` — OS-standard, created on demand, with a documented `~/.floorplanner` fallback when Qt returns nothing |
| a **standard format** | ✅ **INI via `QSettings`**, and the docstring records the deliberate choice — *"a real, standard-location INI file (**not the Windows registry**)"* |
| **read at app load** | ❌ **not done.** `SETTINGS = dict(DEFAULT_SETTINGS)` at import; nothing reads the INI into it |
| **create a default version if absent** | ❌ `QSettings` writes nothing until a value is set |
| **Settings ▸ Save updates the file** | ❌ `SettingsDialog.apply()` writes the live dict; the plan carries it |

**Its one current user is `catalog.py`, storing `anthropic_api_key`**, and
`dialogs.py:376` already shows the user the path.

> **So this is ADOPTION of existing infrastructure, not construction. Building a
> second settings store beside `app_settings()` would be D73 with a new
> subject** — and this ruling exists mostly to say: **do not.**

## 2. THE ONLY HARD QUESTION — THE INI AND THE PLAN BOTH HOLD THESE KEYS

Every key in `DEFAULT_SETTINGS` is **already** persisted per-plan and reloaded
from the document on open (`planio.py:211`, `bridge.py:1088`). Putting the same
keys in the INI creates two stores for one fact.

**And the collision is not hypothetical. Measured, both loaders:**

```python
for key, default in DEFAULT_SETTINGS.items():
    val = project.settings.get(key, default)      # `default` = DEFAULT_SETTINGS[key]
```

> ### READ THE INI AT STARTUP AND CHANGE NOTHING ELSE, AND THE FIRST File ▸ Open SILENTLY DISCARDS EVERY PREFERENCE THE USER SET.
>
> The fallback is the **frozen code default**, not the user's file. A plan
> saved before a key existed has no value for it, so the loader reaches past
> the INI to `DEFAULT_SETTINGS`. **The user sets a 12″ snap, opens a plan, and
> is back to 6″ with nothing said** — [`0073`](0073-ruling.md) §2's silent
> substitution, in a second place, reached by a different road.

**THE RULE, and it follows from one principle:**

> **A saved document must open the way it was saved.**

| rung | source | when |
|---|---|---|
| **3 — wins** | the open document's `settings` block | the key is **present** in the document |
| 2 | `floorplanner.ini` | the document does not carry it |
| **1 — floor** | `DEFAULT_SETTINGS` | neither does |

**The INI is the default for a NEW plan and the fallback for an old one. It is
never an override of what a saved plan says** — otherwise opening last year's
drawing silently re-snaps and re-sizes it, and the corpus this project measures
stops meaning what it measured.

**So both loaders' `default` argument becomes the INI-resolved effective value,
not `DEFAULT_SETTINGS[key]`.** That is the whole change, and it is the one line
that must not be missed.

## 3. THE `QSettings` INI TYPING HAZARD — named, NOT executed

**An INI file has no types. `QSettings.value()` returns strings.**

```python
app_settings().setValue("shuffle", False)   # writes  shuffle=false
bool(app_settings().value("shuffle"))       # bool("false")  ->  True
```

> **Every boolean editing flag inverts on the first read** — `shuffle`,
> `auto_coalesce`, `auto_weld`, `auto_bind` — **and `shuffle` is the one that
> turns all three joining passes off** (`config.editing_enabled`). A silent
> global inversion of the editor's joining behaviour, from a settings file
> nobody suspects.

**I HAVE NOT RUN THIS. There is no PyQt6 on the bridge this review runs over**
(the same limit [`0070`](0070-ruling.md) §0 hit), so this is a **hazard I am
naming, not a defect I have measured** — the distinction
[`0061`](0061-ruling.md) §3 drew and I am holding myself to it.

**The receipt settles it either way, and it is owed before the keys land:** a
round-trip test **per type** — bool `False`, bool `True`, float, int, string —
written to `app_settings()`, read back, asserted **equal and of the right
type**. **If Qt handles it, the test costs nothing. If it does not, the test is
the only thing standing between this and a silent global inversion.**

## 4. WHAT "CLICKS SAVE" DOES — both, and one visible string becomes false

`SettingsDialog.apply()` writes the live `SETTINGS`; the plan carries it on the
next Save. **Patrick's instruction adds the INI, so Save writes both:** the INI
(the new user default) **and** the live dict (so the current plan still
responds, exactly as today). Anything less regresses per-plan canvas size.

**Two things the census must not sweep up:**

* **The dialog's own note reads `"Settings are saved with the plan."`** — a
  user-visible string that this change makes **false**. It becomes: saved with
  the plan **and** kept as your default.
* **`auto_bind` stays out of the dialog.** It is deliberately absent — *"a
  control would promise behaviour nothing enforces"*, ruled 2026‑08‑03, comment
  in place. **"All settings" does not mean this one.**

**Named, his call, one line to answer:** writing the INI on every Save means
bumping the canvas for one plan also changes the default for all new ones. **The
alternative is a "use as default for new plans" checkbox.** I have ruled the
simple version — **write both** — because it is what was asked; say the word if
the checkbox is wanted.

## 5. MATERIALISING THE DEFAULT FILE — one consequence, one line of protection

Writing every default on first run **pins today's defaults into every user's
file forever**: a later change to `DEFAULT_SETTINGS` reaches nobody, because the
key is already present and rung 2 answers before rung 1 ever runs.

**So the created file carries a `version` key**, and the read path treats an
**absent** key as *"use the code default"* rather than *"the file is complete."*
That is the migration point, written down before it is needed rather than
archaeologised later.

## 6. TIER AND ORDER

**A read-back comes first.** This touches a global store, two load paths, a
dialog and a user-visible string, and [`0073`](0073-ruling.md) §2's owed loader
change sits underneath it.

| | | |
|---|---|---|
| 0 | **Read-back** — the key list with **types**; which keys go in the INI and which are plan-only; what an existing plan without a key does at each rung; the `app_settings()` callers already live | **RED until answered.** No code |
| 1 | **§3 — the `QSettings` type round-trip test** | **GREEN.** It is a measurement, and it decides whether §2 is a two-line change or a trap |
| 2 | **[`0073`](0073-ruling.md) §2 — the type-aware document loader** | **GREEN**, unchanged, and it is the same problem: this project's settings paths coerce blindly in **three** places now |
| 3 | **§2 — the three-rung chain, both loaders' fallback re-pointed** | **AMBER.** It changes what an open document does |
| 4 | **§4/§5 — Save writes the INI, first-run materialisation, the note string** | **AMBER** |
| 5 | **[`0073`](0073-ruling.md), [`0072`](0072-ruling.md) — `fp2pdf` and the export menu** | unchanged; **rung 2 of `0073` §3 now resolves through this chain** rather than beside it |

> **ONE RESOLVER, NOT THREE.** [`0073`](0073-ruling.md) §3 ruled one precedence
> function for the exporter. **This is the same function with a rung added
> underneath it.** Three settings paths coercing values three ways is how this
> ruling's own §3 hazard exists at all.

**PATRICK'S CHECK, batched with the four already waiting:**

> **"Change the wall snap in Settings, quit, reopen the app — is it still your
> value? Then open an old plan saved at 6″ — does it come back at 6″?"**
>
> **Both halves matter: the first is the feature, the second is §2.**

**`0066` — item C — remains reserved and unwritten, no promise attached
([`0070`](0070-ruling.md) §8).**
