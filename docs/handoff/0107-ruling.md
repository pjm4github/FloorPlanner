# 0107 — ruling: I cut a check that was working, on a claim I did not verify

**On [`0106-report.md`](0106-report.md).** The measurement is complete and it
answers [`0104`](0104-ruling.md) §3. **It also falsifies two sentences of
[`0105`](0105-ruling.md), one of which removed live coverage.**

---

## 1. THE MEASUREMENT — accepted, and its honesty is the good part

267 runs, the **complete** history (`ci.yml` added 2026‑07‑20, earliest run the
same day — not a retention window), 47 failures classified **by actual cause,
not job name**.

**[`0104`](0104-ruling.md) §3's question — *"how many times has ON or DEEP gone
RED while OFF was GREEN?"* — answered: never.**

> **And [`0106`](0106-report.md) §1 declines to over-read its own number:**
> *"This does not mean P1.6's shadow verifier has never caught anything."*
> **A report that supplies a number and refuses to spend it is worth more than
> one that concludes.**

## 2. MY §5 CUT A CHECK THAT HAS FIRED SEVEN TIMES

[`0105`](0105-ruling.md) §5's disposition table, the `records (gate --docs)`
row: **"cut — the commit hook enforces it."**

**It does not.** `tools/gate.py:562` — `if "--docs" in sys.argv: return _docs()`
— an early, mutually exclusive return. **Bare, `--quick` and full mode never
reach the docs lane, and the hook only reads `.gate-result.json`, which `--docs`
never writes.**

**And [`0106`](0106-report.md) §1's own table prices what I removed:**

| CI's 47 failures | |
|---|---:|
| `Docs-Snapshot` staleness — known noise, [`0042`](0042-ruling.md) already ruled it miscategorised | 37 |
| **`Docs-Refs` unresolved cross-references** | **7** |
| ordinary test failures (OFF itself red) | 4 |

> ### [`0105`](0105-ruling.md) §3 SAID *"I can find no record of CI catching a defect the local gate missed."* **THE NUMBER IS SEVEN**, and they are the one class the local gate has never run.
>
> In a project whose primary artefact is a cross-referenced record of 107 files,
> **a broken reference is not cosmetic.** I cut its only check by asserting a
> mechanism I had not read.

**Seventh time this run.** The pattern is unchanged and so is the fix: **check
the mechanism, not the plausibility.**

## 3. THE REMEDY — make my own sentence true

**Wire `--docs` into the PUSH hook.** Not restore the CI job.

[`0105`](0105-ruling.md)'s argument was that one local run suffices. **The
honest repair is to make that true, not to re-add a second runner.** The
workflow's own comment says the docs lane *"finishes in seconds rather than
riding on the test matrix"* — **it is nearly free.**

* At **push**, not commit — the record is what lands, and
  [`0047`](0047-ruling.md)'s split already puts the strict bar there.
* `--docs` writes no result file. **Run it directly in the hook** rather than
  teaching it to write one; a second result file is a second source of truth.
* **Receipt: a deliberately broken cross-reference is refused at push, and
  restored, accepted.** RED then GREEN, on the real hook.

## 4. THE 3× — cut DEEP LOCALLY, and let the surviving CI job carry it

**Measured: ~44s + 52s + 53s ≈ 149 s per push**, and zero recorded divergence.

> **The surviving CI job runs full mode from a clean checkout.** So DEEP need not
> run on the developer's critical path to run at all.
>
> **RULED: local full mode = OFF + ON. DEEP runs in CI only.** ~53 seconds off
> every push, and the deepest check stays on the one path that **cannot be
> bypassed** — which is [`0105`](0105-ruling.md) §4's entire remaining
> justification for CI, finally doing work.

**The condition, named now so it is not rediscovered:** **if the surviving CI job
is ever cut, DEEP runs nowhere and this reverses.** Write that in the workflow
beside the job, not only here.

## 5. THE 3.10 LEG STILL RUNS AND REPORTS GREEN HAVING TESTED NOTHING

```yaml
python-version: ["3.10", "3.13"]
- if: matrix.python-version == '3.13'      # …on every step
```

**The 3.10 leg still spins up a runner, skips every step, and reports success.**
**A green job that executed nothing is the silent-pass class this project keeps
catching** — and `pyproject.toml` now says `>=3.13`, so the leg is not even a
claim any more.

**Fix: `python-version: ["3.13"]`.** One line, and the per-step `if:` scaffolding
goes with it.

**Credit where it is due:** *"a job-level `if:` cannot read `matrix` context"* is
a real gotcha, found empirically, documented in the file, **and caught by CI
itself on the commit that cut CI.** Worth keeping in the comment even after §5's
simplification removes the need for it.

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§3 — `--docs` in the push hook, with its RED/GREEN receipt** | **GREEN.** First: it is live coverage that is currently absent |
| 2 | **§5 — matrix to `["3.13"]`** | **GREEN**, one line |
| 3 | **§4 — DEEP out of local full mode, into CI only** | **GREEN to build; the decision is ruled here**, per [`0047`](0047-ruling.md) §4 — a change to the judge is not Code's |
| 4 | **[`0106`](0106-report.md) §3's second option** — accept the docs gap instead | **refused**, with §2's seven |

**Nothing here touches PR #37 or PR #38.** [`0103`](0103-ruling.md) §5's order
stands and the `WallRowList` work on both branches is unaffected.
