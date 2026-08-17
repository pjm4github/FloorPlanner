# 0049 — report: the commit hook split, four controls, item 5 done

**Per [`0044`](0044-ruling.md) §3 item 5 / [`0043`](0043-ruling.md) §4,
authorised with [`0047`](0047-ruling.md) §4's FOUR controls (not one).**

---

## 1. WHAT CHANGED

`tools/gate.py`: `_write_result` now takes a `mode` (`"quick"` or `"full"`)
and writes it into `.gate-result.json`. `--quick` writes now (it used to
write nothing); `--deep` still writes nothing — CI's own job, never a local
development mode, unlocks neither event. Full mode (no flag) writes
`mode: "full"` as before.

`.claude/hooks/verify_gate.py`: matches `git push` (`PUSH_RE`) alongside the
existing `git commit` match. A `git commit` accepts either mode, GREEN and
fresh — unchanged from before, except a `--quick` result now also qualifies.
A `git push` additionally requires `mode == "full"`. A command naming both
(`git commit ... && git push`) is judged as a push — the stricter
requirement, so it is correct either way. The "gate and commit/push in one
call" block (`GATE_RUN_RE`) now fires for push too, with the pluralisation
bug (`f"{event}s"` → `"pushs"`) caught by the tests below before it shipped.

**Nothing that reaches `origin`, CI or a PR is gated on less than the full
3×-suite run.** The bar moved from every commit to every push; the twenty
private, never-pushed intermediate commits a session splits a change into
stop paying the full tax individually, and the one commit that actually
leaves the machine still does.

## 2. WHY THE MODE FIELD, NOT A SEPARATE FILE OR A SECOND HOOK

One result file, one hook, one new field — `.gate-result.json` already
carries the verdict the hook reads; adding what *kind* of run produced it is
the minimal change that lets one hook answer both questions ("did it run,
green, on this tree" and "was it strong enough for this event") without a
second code path to keep in sync with the first.

## 3. THE FOUR CONTROLS, PER 0047 §4's TABLE — all eight cells, plus three more

`tests/test_verify_gate_hook.py`, new, 18 tests, driving the hook as a real
subprocess against an isolated fixture repo (`_hook_repo`: a throwaway git
repo with the hook copied to `<repo>/.claude/hooks/verify_gate.py`, so the
hook's own `ROOT` computation — three `dirname`s up from its file location —
lands on the fixture, not on this actual repository; `RESULT` and
`git ls-files` are then genuinely isolated, never touching this repo's own
`.gate-result.json`):

| row | commit | push |
|---|---|---|
| no result | REFUSED ✓ | REFUSED ✓ |
| `--quick` GREEN | allowed ✓ | REFUSED ✓ |
| full GREEN, fresh | allowed ✓ | allowed ✓ |
| any RED (both modes) | REFUSED ✓ | REFUSED ✓ |

**Plus, beyond the table**, because 0047 §4 named them explicitly:

* "no result" and "RED result" produce different `stderr`, at both events
  (`gate.py`'s own "you did not run it" / "you ran it and it failed"
  distinction, now doubled across two events).
* a `--quick` GREEN refused at push produces a message that does **not**
  contain "RED" — refusing a real, passing, just-not-strong-enough result
  must not read like refusing a failure.
* freshness (unchanged logic) still refuses a stale result at **both**
  events, not only commit.
* a command naming both `commit` and `push` is gated as a push.
* the gate-and-commit-in-one-call block now also fires for gate-and-push.
* a command touching neither verb is untouched (`git status` passes through).

`python -m pytest tests/test_gate.py tests/test_verify_gate_hook.py -v`:
**31 passed** — the 13 from `0048`'s work plus these 18, none touched.

## 4. ONE BUG THE TESTS CAUGHT BEFORE IT SHIPPED

`f"{event}s"` for the shared "runs the gate AND {event}s" message pluralises
`"commit"` → `"commits"` correctly and `"push"` → `"pushs"` — not a word.
`test_running_the_gate_AND_pushing_in_one_call_is_blocked` failed on exactly
that string before an explicit `event_verb` (`"commits"` / `"pushes"`)
replaced the naive suffix. Left in the test as an explicit
`assert "pushs" not in r.stderr` so a regression here is loud, not merely a
typo nobody reads.

## 5. END-TO-END, NOT ONLY THE UNIT TESTS

```
python tools/gate.py            # writes mode: "full"
python tools/gate.py --quick    # writes mode: "quick"
```

Both confirmed by reading `.gate-result.json` directly after each run.

## 6. TIER

**GREEN**, per [`0047`](0047-ruling.md) §7. All three items 0047 authorised
are now done: push (`a1d35f7`), the CI-lane move (`6a22aee`), and this split.
[`0044`](0044-ruling.md) §3's remaining item — the DXF integration — starts
on a fresh context, unchanged from that ruling and repeated at
[`0047`](0047-ruling.md) §5.
