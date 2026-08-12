---
# permanent key, independent of GitHub
id: 72
title: "_gen_assets.py writes the asset tree AT IMPORT, so it cannot be tested normally"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
closed_by: null
rank: 73
related: [70, 71]
state_source: measurement
github_issue: null
---

# D72 — `_gen_assets.py` writes the asset tree at import

## The fault

**The module does its work at import.** There is no `if __name__ == "__main__":`
guard and no entry function: the `FURNISHINGS` loop, the manifest write, the
groups write and the icon write are all at module level, so **`import
_gen_assets` regenerates `assets/`**.

## How it surfaced — a test could not import the code it was testing

[D70](0070-the-asset-generator-writes-a-corrupt-svg.md)'s regression tests need
`svg_error`. They cannot `import _gen_assets` to get it, because that would
**rewrite the asset tree as a side effect of running the suite**. So the test
**compiles the function out of the source text**:

```python
src = GEN.read_text(encoding="utf-8")
start = src.index("def svg_error(")
end = src.index("\ndef ", start + 1)
exec(compile(... src[start:end] ...), ns)
```

**That workaround is correct and the underlying shape is the fault.** It is
brittle by construction — it depends on the function's position in the file and
on the next `def` following it — and it exists only to route around the import.

**And the next person will either not notice, or will regenerate the tree from a
test run.** A suite that silently rewrites tracked assets is one CRLF churn away
from a dirty tree nobody can explain, and this repository has already had the
census bitten twice by the working tree ([D51](0051-the-census-depends-on-the-working-tree.md)).

## Why it is worth fixing beyond the test

**It bears directly on the census's cost-of-one-new-item question**
([`handoff/0010-census-furnishings.md`](../handoff/0010-census-furnishings.md)).
Any tool that wants to *add* a furnishing — an AI authoring path, a script, a
test fixture — must today either shell out to the whole generator or import it
and accept a full tree rewrite. **There is no way to ask this module a question
without making it do all of its work.**

## The fix, and it is small

**A generator's work belongs behind a main guard or in a function.** Move the
module-level body into `main()` (or `write_assets()`), call it under
`if __name__ == "__main__":`. Helpers — `svg`, `svg_error`, `R` and friends —
then become importable, and D70's test drops its `exec` workaround for a plain
import.

**Nothing about the generated output changes**, which makes the receipt easy: the
assets must be **byte-identical** before and after.

## Ruling

*(Open — filed 2026‑08‑11.)* **Filed, not fixed.** Small, low-risk, and the
receipt is a byte comparison.
