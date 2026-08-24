# 0106 — report: the ON/DEEP-vs-OFF measurement `0104` ordered, and `0105`'s CI cuts built

**Answers `0104-ruling.md` §5 tier 2** (measure before any ruling on cutting
the 3×) **and builds `0105-ruling.md` §5** (the CI job cuts, ruled while this
was in flight).

---

## 1. THE MEASUREMENT — every CI run since the workflow began

**Source:** `gh run list --workflow=ci.yml --limit 500` (267 returned, no
truncation — `ci.yml` was added 2026-07-20 11:08 local, and the earliest run
is 2026-07-20T15:08:18Z, so this is the complete history, not a retention
window). `gh run view <id> --json jobs` and `--log-failed` for each of the
47 failures.

```
267 runs total: 216 success, 47 failure, 3 cancelled, 1 in-progress
```

**Of the 47 failures, classified by actual cause (not just job name):**

| cause | count | detail |
|---|---:|---|
| `Docs-Snapshot: RED` | 37 | all in `pytest deep invariants` (26) or `records (gate --docs)` (11) — every one of these 37 has its own `Gate-DEEP:` line reading `... OK` (or the equivalent OFF/ON line, for the docs job) — the pytest run itself was clean; only the snapshot marker was stale |
| `Docs-Refs` unresolved cross-references | 7 | all in `records (gate --docs)` — `Docs-Defects`/`Docs-Index`/`Docs-GitHub` all read clean in each; the `UNRESOLVED` list is what failed |
| base `Run tests` (OFF-equivalent step) failed | 4 | 2× `pytest (py3.10)`, 1× `pytest (py3.13)`, 1× `pytest (windows)` — OFF itself was red, so the `--verify-design` (ON) step never ran; not an ON/OFF divergence, an ordinary test failure at the time |

**Zero of the 47 failures show `Gate-ON` or `Gate-DEEP` reporting a `RED:`
invariant list while the corresponding OFF/base run was clean.** The
complete recorded answer to `0104` §3's question — *"How many times has ON
or DEEP gone RED while OFF was GREEN?"* — is **never**, across everything CI
has run.

**This does not mean P1.6's shadow verifier has never caught anything** —
only that nothing it has caught, in this window, showed up as CI-red while
the same run's OFF pass was CI-green. `0104` §3's own words still apply:
*"Do not cut it on the strength of it being slow. P1.6's shadow verifier is
the thing that catches document-model faults the unit tests do not."* This
report supplies the number; it does not decide what to do with it.

**Corroborates `0105` §3 independently**, which reached the same conclusion
by a different method (reading the workflow and citing `0042`'s own single
prior finding, git-topology noise): *"I can find no record of CI catching a
defect the local gate missed."* Measured here across the full run history
rather than the one incident `0042` named.

## 2. `0105`'s CUTS, BUILT

`.github/workflows/ci.yml`: four jobs disabled via job-level `if: false`
(the matrix leg via `if: matrix.python-version == '3.13'`), matching §5's
"disable, do not delete" — each carries a comment at the top of its job
block citing `0105-ruling.md` and why, so a reader does not have to
re-litigate it:

- `pytest (py3.10)` — the matrix leg, not the job (Linux py3.13 survives)
- `pytest (windows)`
- `pytest deep invariants (py3.13)`
- `records (gate --docs)`

**The surviving job** (`test`, py3.13) now runs `python tools/gate.py`
(bare, full mode — OFF + ON + DEEP + the snapshot-staleness check) in place
of its previous two separate pytest invocations, taking over what the now-cut
`deep` job covered. `fetch-depth: 0` added to its checkout (full mode's
snapshot check needs `HEAD~1`, same requirement the cut `docs`/`deep` jobs'
own comments already stated). The corpus-validation step
(`tools/validate_design.py`, not part of `gate.py`) is kept — not something
`0105` named for cutting, and it was real coverage.

`pyproject.toml`: `requires-python` raised `>=3.10` → `>=3.13` (§5: *"A repo
must not promise a version it no longer tests"*). One stale comment fixed to
match — `tests/test_viewer_popup.py`'s "read as TEXT, not tomllib" note
asserted this project still supports py3.10; reworded to state the history
instead of a now-false present-tense claim. The code itself (text-based
read) is unchanged — nothing needed the tomllib switch, so nothing was
switched.

## 3. ONE GAP `0105` DID NOT COVER — flagged, not re-decided

**`tools/gate.py`'s bare/full-mode run does NOT include the `--docs`-lane
checks** (`Docs-Defects` front-matter validation, `Docs-Index` drift check,
`Docs-Refs` cross-reference resolution, `Docs-GitHub` migration dry run) —
confirmed by reading `main()`: `--docs` is an early, mutually exclusive
return (`if "--docs" in sys.argv: return _docs()`), never reached by a bare
or `--quick`/full invocation. The commit/push hook only checks
`.gate-result.json`'s verdict from a quick-or-full run, so it has never
enforced the docs lane either.

**Consequence: with the CI `docs` job cut, nothing currently runs those four
checks anywhere — not CI, not the local hook.** `0105` §4 already measured
what CI's remaining value is (an unbypassable clean-checkout run) and named
the trade explicitly for the pytest-side jobs; this is the one piece of that
trade the ruling's disposition table did not price in, because `--docs` was
folded into "the commit hook enforces it" (§5's `records (gate --docs)` row)
without checking whether the hook actually does. It does not, today.

**Not acted on here** — `0105` §6 is explicit that a change to the judge is
"ruled here and not decided by Code." Two shapes a future ruling could take,
named without a recommendation: run `--docs` from the local hook too (a
second, cheap invocation before push), or accept the gap on the same
reasoning §3/§4 already gave for the pytest jobs (one agent, one machine,
nothing forgotten to run).

## 4. GATE

```
Docs-Snapshot: cut against b35d1b6, which is HEAD
Gate-Census: collected=864 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 857 passed, 7 deselected, 2 warnings  -> sum 864  OK
Gate-Verdict: GREEN (every sum reconciles against --collect-only)
```

Full trail: `tests/test_viewer_popup.py` unaffected (7 passed), `ruff check
.` clean repo-wide. `.github/workflows/ci.yml` validated by parsing it with
`yaml.safe_load` (no `actionlint` in this repo) — five jobs found, `if:`
values confirmed (`docs`/`windows`/`deep` → `False`, `test` →
`matrix.python-version == '3.13'`).
