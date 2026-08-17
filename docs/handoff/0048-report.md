# 0048 — report: `Docs-Snapshot` out of the `pull_request` lane, item 4 done

**Per [`0044`](0044-ruling.md) §3 item 4, authorised at [`0047`](0047-ruling.md)
§3.** `Docs-Snapshot` no longer runs when `GITHUB_EVENT_NAME == "pull_request"`;
it is unchanged everywhere else.

---

## 1. WHERE THE SKIP LIVES, AND WHY NOT INSIDE `_snapshot_head()`

A new `_snapshot_check()` wraps `_snapshot_head()` in `tools/gate.py` and is
the only thing `main()` and `_docs()` call now. It checks
`GITHUB_EVENT_NAME`, prints a `Docs-Snapshot: skipped -- pull_request lane
(0042-ruling.md: ...)` line and returns `(0, "skipped")` in that lane;
otherwise it calls `_snapshot_head()` unchanged and returns its real result.

**Deliberately not a change to `_snapshot_head()` or `_snapshot_checkout_base()`
themselves** — 0042 §4 said "do not lose [the `HEAD^2` fix] in the move," and
0047 §3 repeated it as a condition, not a preference. Putting the skip at the
two call sites instead means every existing `tests/test_gate.py` case that
drives those two functions directly — the `HEAD^2` merge-ref logic, the
shallow-fetch label, the four RED/GREEN control pairs from D78 — still
exercises the real logic, unchanged, and all ten passed without edits.

## 2. THE TWO CONTROLS THIS MOVE OWES, PER 0042 §4 / 0047 §3

Both new, both against one shared fixture (`_stale_marker_repo`: a real linear
two-commit repo, second commit carrying a marker that cites neither `HEAD`
nor `HEAD~1` — the same shape `test_TWO_commits_behind_is_RED` already uses
against `snapshot_verdict` directly, driven here through `_snapshot_check()`
instead):

* **`test_the_pull_request_lane_skips_the_check_EVEN_WHEN_STALE`** — the
  positive control for the skip itself: with `GITHUB_EVENT_NAME=pull_request`
  set, the deliberately-stale repo returns `(0, "skipped")`, not `(1,
  "stale")`. Without this, "the PR lane doesn't fail" could just as well mean
  a check nobody broke yet.
* **`test_OUTSIDE_the_pull_request_lane_a_stale_marker_still_goes_RED`** —
  the negative control 0042 §4 named by name: the identical repo, env var
  unset, still returns `(1, "stale")`. Proves the skip is scoped to the one
  lane, not a blanket disable — push-to-`main` and a local session both look
  like this.

`python -m pytest tests/test_gate.py -v`: **13 passed** (the 8 pre-existing
D78 cases untouched, the 2 new ones above, plus the census/marker sanity
tests). Full gate re-run after: GREEN, `collected=736` (was 734 — the two new
tests).

## 3. END-TO-END CHECK, NOT ONLY THE UNIT TESTS

```
GITHUB_EVENT_NAME=pull_request python tools/gate.py --docs   # first line:
  Docs-Snapshot: skipped -- pull_request lane (0042-ruling.md: ...)

GITHUB_EVENT_NAME=pull_request python tools/gate.py --deep   # census line:
  Gate-Census: collected=736 ruff=clean vacuous=0 end_assign=0 snapshot=skipped
  Gate-Verdict: GREEN
```

Both CI jobs that run the snapshot check (`docs`, which calls `--docs`, and
`deep`, which calls `--deep`) go through `main()`/`_docs()`, so this is the
same code path CI will actually execute — not just the two functions in
isolation. No `.github/workflows/ci.yml` trigger edit was needed:
`GITHUB_EVENT_NAME` is already exported by GitHub Actions to every step, and
`_snapshot_check()` reads it directly. Two comments added there anyway, on
the `docs` and `deep` jobs, so a reader of the workflow file doesn't have to
find this report to know why a PR run shows no snapshot line, and so the
`deep` job's `fetch-depth: 0` comment (which used to justify itself by "on a
PR, that check needs...") doesn't go stale now that the PR case it named no
longer runs the check at all — depth 0 is still needed, now for the `push`
case's `HEAD~1` resolution.

## 4. ONE PRE-EXISTING FINDING, UNRELATED, NOT FIXED HERE

`python tools/gate.py --docs` prints `Docs-Verdict: RED` **regardless of this
change** — 30 unresolved doc references (`Ref-Audit`), including
`docs/CODE_REVIEW_v2.md` and `docs/DESIGN_MODEL_v5.md` pointing at
`docs/design-schema.v5.json` / `docs/_superseded/`, neither of which
resolves. Confirmed identical with and without `GITHUB_EVENT_NAME=pull_request`
set, so it is not a symptom of this move — the `docs` job's CI status was
already red on this before today's work, on an axis this item didn't touch.
Flagging rather than fixing: out of 0044/0047's scope, and a ref-audit sweep
is its own task.

## 5. TIER

**GREEN**, per [`0047`](0047-ruling.md) §7. Item 4 of [`0044`](0044-ruling.md)
§3 done. Item 5 (the hook split, with 0047 §4's four controls) is next.
