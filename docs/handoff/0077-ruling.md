# 0077 — ruling: accepted — and the type-safe coercer is not type-safe for the input it was built for

**On [`0076-report.md`](0076-report.md).** Four items built, gated GREEN at
`collected=816`, nothing AMBER touched. **Three of the four carry a real
revert-and-confirm differential** — [`0068`](0068-ruling.md) §3's standard, met
without being asked again.

**Read from the tree:** `coerce_setting` and both its call sites, `_JsonSettings`,
`_ensure_settings_file`, `fp2pdf._load_std_thickness`, `tests/test_fp2pdf.py`,
`requirements-dev.txt`, and the CI install step.

---

## 1. ACCEPTED, AND THE DIFFERENTIALS ARE REAL

`0075` §3's idempotence guard reverted → RED → restored → GREEN. The
`SystemExit` fix and the `reportlab` guard, each reverted in turn, each receipt
confirmed RED. **And the `reportlab` test forces the missing-import path through
`monkeypatch` on `builtins.__import__` rather than leaning on this machine
happening to lack it — which is [`0072`](0072-ruling.md) §6's instruction
followed to the letter.**

**`_JsonSettings` does what it was chosen for.** `setValue("shuffle", False)` →
`value("shuffle") is False`. The hazard [`0075`](0075-ruling.md) exists to kill
is dead **in that store**.

## 2. THE FINDING — IT IS ALIVE IN THE NEW COERCER, TEN LINES AWAY

```python
def coerce_setting(key, val, default):
    """...from a loaded document, OR ANY OTHER UNTYPED SOURCE..."""
    if isinstance(default, bool):
        return bool(val)              # <-
```

**Measured:**

```
bool("false") = True
bool("0")     = True
```

> ### THE FUNCTION WHOSE JOB IS *"DO NOT BLINDLY COERCE"* BLINDLY COERCES THE ONE TYPE THIS WHOLE THREAD IS ABOUT.
>
> `shuffle`, `auto_coalesce`, `auto_weld`, `auto_bind` — and `shuffle` turns all
> three joining passes off (`editing_enabled`). **A settings source that hands
> back text inverts the editor's joining behaviour globally and silently**,
> which is the sentence [`0074`](0074-ruling.md) §3 and
> [`0075`](0075-ruling.md) §1 were both written to prevent.

**IT IS A LOADED GUN, NOT A FIRED ONE, AND THE DISTINCTION IS THE RULING.**
Today `DEFAULT_SETTINGS` has no string keys and the plan file is JSON, so every
`val` arrives already typed. **Nothing is broken now.** But:

* the docstring **invites** untyped input, in its own words;
* it is exported in `__all__`;
* **[`0073`](0073-ruling.md) §3's `--settings` chain and
  [`0074`](0074-ruling.md) §2's three-rung resolver are both still unbuilt, both
  will handle values from files and flags, and both will reach for the function
  named "coerce a settings value."**

**OWED, GREEN, and it is a branch and a test.** Either the bool branch parses
text explicitly (`"true"/"false"/"1"/"0"`, warn on anything else, the same
`warnings.warn` the other branches already use), **or** the docstring stops
claiming "any other untyped source" and a separate parser owns text. **My
preference is the first** — the second leaves a trap with a sign on it.
**Receipt:** `coerce_setting("shuffle", "false", True) is False`. **RED today.**

## 3. THE ONE ITEM WITH NO DIFFERENTIAL — in a report that has three

§1 states it plainly rather than hiding it: *"Not run against the unfixed code
directly (the fix and its test landed together)."* **Credit for saying so.**

**The concrete risk that admission leaves open** is that `coerce_setting` is
correct and a loader still runs the old `float()` — the unit tests pass, the
loader stays broken. **I checked it: `planio.py:213` and `bridge.py:1090` both
call `coerce_setting`, and the duplicated branch is gone from both.**

> **So the fix is right — but I established that, not the suite.** The one thing
> a reviewer reading a diff can do is exactly what a fail-first receipt exists
> to make unnecessary. **One revert of one call site closes it**, and it costs
> the same as the three reverts already in this commit.

## 4. FIRST-RUN MATERIALISATION — A DECISION AGAINST PATRICK'S OWN WORDS, SETTLED IN A PARENTHESIS

**Patrick:** *"if it doesnt exist then it creates a **default version**."*

**`_ensure_settings_file` writes `{"version": 1}` and nothing else**, justified
as *"`0074-ruling.md` sec5: that would pin today's defaults into every user's
file forever."*

**[`0074`](0074-ruling.md) §5 does not say that.** It names the pinning
consequence and prescribes the mitigation — *"the created file carries a
`version` key, and the read path treats an absent key as 'use the code
default'"*. **It never says the defaults should be withheld. My §5 was
ambiguous; the citation is to a sentence that does not exist.**

> ### A FILE CONTAINING ONLY `{"version": 1}` IS NOT "A DEFAULT VERSION" OF ANYTHING A USER CAN OPEN AND EDIT.
>
> And the English genuinely is ambiguous — *"a default version"* can mean *an
> initial file* or *a file containing the defaults*. **Two readings, two
> different files, and one was chosen inside a parenthesis.**
> **[`0062`](0062-report.md) §4 set this project's standard and was praised for
> it: name the third answer and argue it in the open.**

**Patrick's call, one line.** **My reading: he wants a file he can look at**, so
materialise the `DEFAULT_SETTINGS` keys **and** the `version` marker — the
version key is what a future default change migrates on, which is the entire
reason to have one.

## 5. THE `fp2dxf` COUPLING — AND MY WORDING CAUSED IT

To borrow seven numbers, `fp2pdf.py` now **execs the whole 23 KB DXF exporter
by path at module scope**, and needed a `sys.modules` registration to get
someone else's `@dataclass` to resolve. That module then by-path execs
`validate.py`. **Import `fp2pdf` and two unrelated modules run.**

| | |
|---|---|
| import-time work, two modules deep | the D72 class this project already has a record for |
| **the PDF exporter now depends on the DXF exporter** | backwards for a package whose own docstring is about running *"without dragging in"* anything |
| a `sys.modules` hack for a dataclass in a file it does not use | **the workaround is the evidence the shape is wrong** |

**[`0072`](0072-ruling.md) §4 said: *"Reuse it; do not transcribe it — a second
copy of the loader would be the same disease one level up."*** **That was right
about the TABLE and wrong about the LOADER**, and Code paid for the difference.
**A by-path loader is five lines of plumbing, not a fact about the world; two
copies of it are not D73. Seven thickness numbers in two places are.**

**OWED, GREEN:** a **leaf** module — `floorplanner/export/_stdt.py`, no imports,
no dataclasses — by-path loaded from both exporters, **and the load moved off
module scope** (lazy, exactly as `reportlab` now is). **Receipt: `fp2pdf`
imports with `fp2dxf.py` absent.**

## 6. TWO SMALLER ONES

**`_JsonSettings` destroys a corrupt settings file.**

```python
try:    self._data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, ValueError): self._data = {}     # <- and the next setValue writes {} + one key
```

> **One truncated write — power loss, full disk — and the file reads as empty,
> then the next save overwrites it. The remembered API key is gone, silently.**
> `catalog.py`'s `except Exception: return ""` guarantees nobody hears about it.
> **A file that fails to parse is preserved (`.bad`) and reported once, not
> emptied.** GREEN.

**`reportlab` belongs in `requirements-dev.txt`, and this is not a preference.**
**Measured: CI installs `requirements-dev.txt`; `reportlab` is not in it; and
the only two tests that actually render a PDF — `test_convert_returns_a_result_and_prints_nothing`
and `test_main_round_trips_a_design_via_the_cli` — both `pytest.importorskip`.**

> **CI has never rendered a PDF and never will as things stand.** The exporter's
> only end-to-end receipts are skipped on every run, and `collected=816` was
> measured on a machine where it *was* installed — so the gate's own number
> depends on an unpinned optional dependency. **`0076` §5 left this open and was
> right to; here is the answer: dev yes, runtime no.** Optional at runtime is
> D40 and stays. **Required for the receipts, or the receipts are decorative.**

## 7. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§2 — the bool branch, and its RED-today test** | **GREEN.** First: it is the only item that is a defect rather than a shape |
| 2 | **§6 — `reportlab` into `requirements-dev.txt`** | **GREEN.** One line, and it turns two skipped tests into running ones |
| 3 | **§3 — the missing differential on the loader call sites** | **GREEN.** One revert |
| 4 | **§5 — the `_stdt.py` leaf, lazy-loaded** | **GREEN.** No behaviour change |
| 5 | **§6 — the corrupt-settings-file path** | **GREEN** |
| 6 | **§4 — materialisation** | **blocked on Patrick's one line**, then GREEN |
| 7 | **The read-back** ([`0074`](0074-ruling.md) §6 item 0) and everything AMBER | unchanged — **still owed before the chain, the checkbox, the menu or the dialog** |

**PATRICK — one line, and it unblocks §4:**

> **When the settings file is created for the first time, do you want to see
> your settings in it (every key at its default), or just a stub the app fills
> in as you change things?**

**The five manual checks (PR #34/#35/#36, the label, heading-vs-deviation) are
unchanged and still queued.** Nothing in this ruling adds a sixth.

**`0066` — item C — remains reserved and unwritten, no promise attached
([`0070`](0070-ruling.md) §8).**
