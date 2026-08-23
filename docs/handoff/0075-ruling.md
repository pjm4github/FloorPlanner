# 0075 — ruling: JSON, not `configparser` — and `configparser` would have kept the bug

**On Patrick's own instruction**, quoted:

> *"Yes we can have the checkbox. Also instead of a PyQT6.QSettings lets use a
> python settings infrastructure. This should eliminate a string that reads
> "false" as a True in python. If we need a method that QSettings provides we
> can shim it into the code where needed."*

**Both accepted.** The format choice is not free, so §1 settles it by
measurement rather than taste, and §3 names a migration trap that loses a real
user's data if the two new behaviours land in the wrong order.

---

## 1. THE FORMAT — three candidates, and only one actually eliminates the hazard

**The stated goal is the test:** *eliminate a string that reads `"false"` as
`True`.*

| candidate | types on read | on the 3.10 leg | verdict |
|---|---|---|---|
| `configparser` (INI) | **strings.** `get()` → `str`; `"false"` is truthy unless you remember `getboolean()` | stdlib ✅ | **Rejected — it does not eliminate the hazard, it offers a way to avoid it** |
| `tomllib` (TOML) | real types ✅ | **3.11+.** `pyproject.toml` sets `requires-python = ">=3.10"` and **CI runs a 3.10 leg** (matrix `["3.10","3.13"]`). Reading needs `tomli`; **writing needs `tomli-w` on every version** | **Rejected — two new dependencies, on the D40 path we just argued about** |
| **`json`** | **real types.** `false` → `False`, `6.0` → `float`, `"x"` → `str` | **stdlib, 3.10 ✅** | **RULED** |

> ### `configparser` WOULD HAVE SHIPPED THE SAME BUG WITH A STDLIB BADGE ON IT.
>
> It stores `shuffle = false` and hands back the string `"false"`. The defect is
> **identical** to `QSettings`'; the only difference is which typed getter you
> must remember to call. **Patrick asked for the hazard eliminated, not
> relocated** — and a rule that depends on every future caller remembering
> `getboolean()` is the kind of discipline this project has watched fail four
> times.

**And `json` is not a new format here — it is the only one this project
already speaks.** Plans, the furnishing manifest, the openings sidecars,
`.gate-result.json`. **One format, not two.**

**Named, his call, one line:** the one thing JSON gives up is **comments and
comfortable hand-editing**. If a hand-editable file with annotations matters
more than a stdlib-only dependency tree, that is TOML and it costs `tomli` +
`tomli-w`. **I have ruled JSON; say so and I will re-rule it.**

## 2. THE SHIM — keep the seam, change what is behind it

**The entire current surface is two calls, both in `catalog.py`:**

```python
app_settings().value("anthropic_api_key", "")
app_settings().setValue("anthropic_api_key", key)
```

> **So `app_settings()` keeps its name and its two methods, and `catalog.py` is
> not touched at all.** The blast radius is `config.py` plus tests. **Do not
> refactor the callers to a nicer API** — a rename here buys nothing and costs
> a diff across a file that has no bug in it.

**Same method names, DIFFERENT GUARANTEE — and the guarantee is the whole
point, so it is asserted by a test, not by a docstring.** `value()` returns the
type that was stored. **[`0074`](0074-ruling.md) §3's round-trip test is now the
receipt that the replacement did what it was chosen for**, and it must include
the exact case that motivated it:

```python
s.setValue("shuffle", False)
assert s.value("shuffle") is False          # not "false", and not True
```

**`dialogs.py:376` shows the user `settings_file()`.** The path changes
(`floorplanner.ini` → `floorplanner.json`); that label is user-visible and comes
along.

## 3. THE MIGRATION TRAP — order these two wrong and a real user loses a real key

**`floorplanner.ini` exists on disk today and holds `anthropic_api_key`.** Two
new behaviours are landing at once: **first-run materialisation of defaults**
([`0074`](0074-ruling.md) §5) and **migration off the INI**.

> ### IF MATERIALISATION RUNS FIRST, IT WRITES AN EMPTY `anthropic_api_key`, THE JSON NOW EXISTS, MIGRATION SEES IT AND STANDS DOWN — AND THE KEY IS GONE.
>
> Silently, on first launch, for every existing user. **And `catalog.py`'s
> reader is `try: … except Exception: return ""`** — so nothing reports it. The
> user just finds themselves logged out of a thing they configured once, months
> ago.

**RULED, three clauses:**

1. **Migration runs FIRST, and only when the JSON does not exist.** That makes
   it idempotent: clear your key later and it does not come back.
2. **Materialisation NEVER writes `anthropic_api_key`.** A file created for
   every user on first launch does not mint a slot for a secret. Settings keys
   only.
3. **The INI is left on disk, unread.** Not deleted — deleting a user's file
   needs a better reason than tidiness, and if the migration is wrong, the
   original is still there to look at.

**Receipt:** a test with a populated INI and no JSON — run startup, assert the
key survives into the JSON **and** that the settings defaults are also present.
**RED if the order is wrong.**

## 4. THE CHECKBOX — semantics, because "add a checkbox" has four of them

**"Use as default for new plans", in `SettingsDialog`, below the existing rows.**

| | |
|---|---|
| **unchecked** (the default) | Save writes the live `SETTINGS` only — the current plan responds and carries it on the next Save. **Exactly today's behaviour.** The app settings file is untouched |
| **checked** | Save does that **and** writes the app settings file |
| **stickiness** | **NOT sticky. Unchecked every time the dialog opens.** It is an action modifier, not a preference — a remembered checkbox would make every later Save global, which is the surprise the checkbox exists to prevent |
| **which keys** | **Only the keys the dialog actually shows** — snap, rotation, canvas W/H, cost, auto-coalesce, auto-weld. **Not `auto_bind`**, which is deliberately absent (ruled 2026‑08‑03) |

> **A "save as default" that writes keys the dialog never displayed is writing
> values the user never saw.** That is the whole rule, and it is why the key
> list is the dialog's, not `DEFAULT_SETTINGS`'.

**And the note label changes again.** [`0074`](0074-ruling.md) §4 already
retired *"Settings are saved with the plan."* With the checkbox it becomes two
sentences, because there are now two destinations and the user is choosing
between them.

## 5. WHAT THIS DOES **NOT** FIX

**[`0073`](0073-ruling.md) §2 stands, untouched.** The document loader's

```python
try:    SETTINGS[key] = float(val)
except: SETTINGS[key] = default
```

throws types away on a path that **already had them** — the plan file is JSON
and always was. **Moving the app store to JSON does not touch it.** Two
independent coercion faults, two independent fixes:

| path | typed? | owed |
|---|---|---|
| app settings store | **fixed by construction** (this ruling) | §2's receipt |
| **document `settings` loader** | JSON in, floats out — **broken** | [`0073`](0073-ruling.md) §2 |
| exporter resolution chain | — | [`0073`](0073-ruling.md) §3, one function |

## 6. TIER AND ORDER — amending [`0074`](0074-ruling.md) §6

| | | |
|---|---|---|
| 0 | **Read-back** ([`0074`](0074-ruling.md) §6 item 0) — now also: the JSON key list **with types**, and the migration order of §3 | **RED until answered** |
| 1 | **§2 — the JSON store behind `app_settings()`, with the per-type round-trip test** | **GREEN.** Callers unchanged; no user-visible behaviour yet |
| 2 | **§3 — migration, with its own fail-first receipt** | **GREEN**, and it lands **with** item 1, never after |
| 3 | **[`0073`](0073-ruling.md) §2 — the document loader's types** | **GREEN**, unchanged |
| 4 | **[`0074`](0074-ruling.md) §2 — the three-rung chain** | **AMBER** |
| 5 | **§4 — the checkbox, the note label, first-run materialisation** | **AMBER** |
| 6 | **[`0072`](0072-ruling.md)/[`0073`](0073-ruling.md) — `fp2pdf`, the export menu** | unchanged, behind these |

**PATRICK'S CHECK — [`0074`](0074-ruling.md)'s two questions, plus one that only
matters because of §3:**

> 1. **Change the wall snap, tick "use as default", quit, reopen — is it your
>    value?** Then **change it again with the box UNTICKED, quit, reopen — is it
>    back to the default?** *(both halves; the second is what the checkbox is
>    for)*
> 2. **Open an old plan saved at 6″ — does it come back at 6″?**
> 3. **If you have an Anthropic key saved today: is it still there after the
>    first launch on the new build?**

**`0066` — item C — remains reserved and unwritten, no promise attached
([`0070`](0070-ruling.md) §8).**
