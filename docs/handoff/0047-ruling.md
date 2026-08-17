# 0047 — ruling: all three authorised, and the hook split needs FOUR controls, not one

**On [`0046-report.md`](0046-report.md)'s held items.** Short.

---

## 1. THE FLAP IS REFUTED, AND THAT MATTERS MORE THAN THE THREE ITEMS

**[`0046`](0046-report.md) §2: no flap.** Two full-gate runs on one unchanged
tree, identical.

**So Patrick's *"it seems to be flapping"* was the SLOWNESS, not
nondeterminism** — and [`0043`](0043-ruling.md) §1 measured that at **92.6
seconds of test time, the same 727 tests three times.** **The impression was
real; the cause was the other one.**

> **Recorded because a refuted suspicion is a result.** Had this not been
> measured, the hook split below would have been built on a gate nobody trusted,
> and any failure afterwards would have been blamed on the change.
> **[`0044`](0044-ruling.md) §3 put it before the gate changes for exactly this
> reason, and that ordering paid.**

## 2. ITEM 1 — PUSH. AUTHORISED, and it did not need asking

**`main` is 3 ahead of `origin/main`**, all gate-GREEN.

**The autonomy policy already covers it**, verbatim: *"Code commits, **pushes**
and merges GREEN-tier work without asking."*

**Code was more cautious than the policy requires here, and that is the right
error to make** — but it should not become the habit. **A GREEN push is not a
decision.** *(Items 2 and 3 are a different case; see §4.)*

## 3. ITEM 2 — THE CI LANE MOVE. AUTHORISED as ruled at [`0042`](0042-ruling.md)

`Docs-Snapshot` out of `pull_request`; kept on push-to-`main` and in the local
full gate. **Do not lose [`0027`](0027-ruling.md) §4's control in the move: a
deliberately stale marker must still go RED wherever the check now runs.**

## 4. ITEM 3 — THE HOOK SPLIT. AUTHORISED, and [`0043`](0043-ruling.md) §7's SINGLE control is not enough

**Code was right to hold this one.** The hook is the thing that protects
everything else, **and a change to a guard is indistinguishable from removing it
unless both of its answers are demonstrated.**

**[`0043`](0043-ruling.md) §7 asked for one control. It needs four**, because the
split creates two events and each has a pass and a fail:

| | tree / result state | at COMMIT | at PUSH |
|---|---|---|---|
| 1 | **no result at all** | **REFUSED** | **REFUSED** |
| 2 | **`--quick` result, GREEN** | **allowed** | **REFUSED** |
| 3 | **full result, GREEN, fresh** | allowed | **allowed** |
| 4 | **any result, RED** | **REFUSED** | **REFUSED** |

**Row 2 is the whole change and row 2 is the one that can silently be wrong.**
If a quick result is accepted at push, the guard is gone and every gate after it
is a claim rather than a gate — **the exact failure `settings.json` says three of
four incidents were.**

> **AND `gate.py`'s OWN DISTINCTION MUST SURVIVE:** *"you did not run it"* and
> *"you ran it and it failed"* are different, and rows 1 and 4 must produce
> **different messages**, not merely both refuse.

**All four demonstrated in the commit that makes the change.** Not "to follow" —
a guard whose controls are deferred is a guard that shipped untested.

## 5. THE ORDER IS 1 → 2 → 3, AND ITEM 3 LANDS ALONE

**Push first** (three commits exist on one machine only). **Then the CI lane
move**, which is independent. **Then the hook split, in its own commit with its
four controls** — it must be revertible without taking anything else with it.

**Then [`0038`](0038-ruling.md)'s DXF integration on a fresh context**, unchanged
from [`0044`](0044-ruling.md) §3 item 6.

## 6. A NOTE ON WHAT NEEDS ASKING

**Code's instinct — "push and infrastructure edits are not inferred from a GREEN
tier" — is half right, and the half that is right is worth keeping.**

* **A push of GREEN work is covered by the policy. It does not need asking.**
* **A change to the GATE or the HOOK is different in kind**, not because of its
  tier but because **it changes what "GREEN" is worth afterwards.** Holding those
  for a word was correct.

> ### THE LINE: AUTONOMY COVERS WORK THE GATE JUDGES. IT DOES NOT COVER CHANGES TO THE JUDGE.
>
> **That is not a new rule — it is what "a green signal is only evidence about
> what it measures" implies when the signal itself is the thing being edited.**

## 7. TIER

**All three GREEN.** Item 3's receipt is §4's four controls; item 2's is
[`0027`](0027-ruling.md) §4's stale-marker control, carried over.
