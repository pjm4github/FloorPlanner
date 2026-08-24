# 0105 — ruling: both reasons for cutting CI are false — and there is a better reason that survives

**Patrick:** *"1) The python version that is used on github is different than the
local version, 2) The headless testing on the CI system will not catch any QT
based errors … My Code agent is the only one doing integration work."*

**Measured against `.github/workflows/ci.yml`. Neither premise holds. The
conclusion might still.**

---

## 1. THE VERSIONS MATCH, AND ONE JOB IS HIS EXACT MACHINE

```yaml
pytest (py${{ matrix.python-version }})   ubuntu-latest   ["3.10", "3.13"]
pytest (windows)                          windows-latest  "3.13"
    # ONE PYTHON VERSION ON PURPOSE. The Linux matrix already covers the 3.10 …
```

**Local is 3.13** — every `.pyc` in the tree is `cpython-313`.

> ### THERE IS A `windows-latest` / **py3.13** JOB. THAT IS HIS MACHINE'S CONFIGURATION, DELIBERATELY, WITH THE REASONING IN THE FILE.
>
> It is D27 / `ROADMAP` G3 — *"the Windows CI leg"* — built for exactly this
> objection.

## 2. CI'S QT COVERAGE IS NOT WORSE THAN LOCAL — IT IS IDENTICAL

CI installs Qt runtime libraries and runs the same suite, `gui` marker included,
offscreen. **The local gate is offscreen too** — `conftest` owns the
`QApplication`, and `QT_QPA_PLATFORM=offscreen` is how every run happens here.

> **Neither catches on-screen behaviour. That is not a CI limitation; it is why
> the AMBER manual check exists**, and it already does.

**One real asymmetry, and it runs the other way:** [`0064`](0064-report.md) §4's
unicode-arrow crash is a **Windows cp1252 console** fault. **Linux CI would not
see it. The Windows job would.**

## 3. THE ARGUMENT THAT SURVIVES — duplication, not coverage

**Every CI job re-runs what the local gate already ran:** ruff, the suite, the
shadow modes, the deep gate, the corpus validation, the docs lane. **With one
agent on one machine, CI's usual job — catching what a contributor forgot to
run — has no contributor to catch.**

**And its failure record is bad.** [`0042`](0042-ruling.md): `Docs-Snapshot` was
*"the only check this project's CI has ever failed on when the code itself was
fine"* — a git-topology check wearing a CI job's clothes. **I can find no record
of CI catching a defect the local gate missed.**

## 4. WHAT IS ACTUALLY LOST — one thing, and it is real

**The local gate is a FILE ON DISK.** `.gate-result.json` is what the hook
reads. It is freshness-checked ([`0049`](0049-report.md)), but
**`git commit --no-verify` and `git push --no-verify` bypass the hook entirely**,
and nothing downstream would ever know.

> **CI is the only run that starts from a clean checkout and cannot be
> bypassed by the thing being checked.** That is its whole remaining value here,
> and it is not nothing.

## 5. RULED

**Cut the duplicates. Keep one.**

| job | disposition |
|---|---|
| `pytest (py3.10)` — Linux | **cut** — supports a Python nobody runs |
| `pytest (windows)` py3.13 | **cut** — duplicates local exactly |
| `pytest deep invariants` | **cut** — local full mode already runs DEEP |
| `records (gate --docs)` | **cut** — the commit hook enforces it |
| **`pytest (py3.13)` — Linux, full gate** | **KEEP** — §4's independent run |

**If 3.10 goes, `pyproject.toml`'s `requires-python = ">=3.10"` goes with it.**
**A repo must not promise a version it no longer tests** — that is the same
class as a comment claiming a census result it never measured
([`0077`](0077-ruling.md) §2).

**Disable, do not delete.** A workflow that is cut is one `if: false` or a
renamed file away from returning; a deleted one is archaeology. **Record why in
the file itself**, so the next reader does not re-litigate it.

## 6. TIER

**GREEN** — infrastructure, no behaviour, and [`0047`](0047-ruling.md) §4's line
holds: *"autonomy covers work the gate judges, not changes to the judge."*
**This is a change to the judge, which is why it is ruled here and not decided
by Code.**

**And it is reversible on one condition worth naming now: the moment a second
agent, a second machine, or a second person touches this repo, §3's argument
evaporates and the cut jobs come back.**
