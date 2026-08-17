# 0044 — ruling: 0040 §4 was half right, and the order of work

**Short. A correction I owe, and the queue.**

---

## 1. IT COLLIDED A THIRD TIME, AND MY DIAGNOSIS WAS INCOMPLETE

`0043-report.md` (Code's recovery report, committed in `7332716`) and
`0043-ruling.md` (mine, on the gate's cost) are **two different subjects sharing
one number.** Third time.

**[`0040`](0040-ruling.md) §4 said, in bold: *"Neither raced the other."*** That
was right about `0036` and `0038` — the mailbox was genuinely split across
branches, and it still is. **It is wrong about this one.** Both of us were on
`main`, both saw `0042` as the highest, both took `0043`. **That is a plain
race.**

> **SO THERE ARE TWO CAUSES, NOT ONE.** The branch split (still unfixed) **and**
> ordinary concurrency between two writers who cannot see each other's work in
> progress. **The second cannot be designed away** — there is no lock between a
> Cowork session and a Claude Code session.
>
> **Which is why the suffix split is the load-bearing part**, and it has now held
> three times: `-report.md` is Code's forever, `-ruling.md` is the reviewer's
> forever, **so a collision costs a shared number and never a lost file.**
> [`0040`](0040-ruling.md) §4's retirement of the *pairing* convention stands,
> and with it nothing further is owed. **Collisions are noise, not faults.**

**ONE PROTOCOL REFINEMENT, because a collision makes the signal ambiguous:**
**when a number is shared, name the suffix** — `0043-ruling is up`, not
`0043 is up`. Otherwise Code cannot tell whether Patrick means the file it wrote
itself.

## 2. THE BRANCH HOLE IS STILL OPEN AND IS STILL OWED

**`0033`, `0034`, `0035` and `0036-report.md` remain absent from `main`** — they
are on `shower-identity-redraws`, which is parked on Patrick's check.

**Do not wait for that merge.** Cherry-pick the four doc files onto `main` as a
doc-only commit. **They are records of exchanges, not part of that branch's
change** — which is [`0040`](0040-ruling.md) §4's rule, applied retroactively to
the files that prompted it.

## 3. THE ORDER

| | | why here |
|---|---|---|
| **1** | **Push `main`** — it is **ahead 2 and unpushed** | the recovery is not safe until it leaves the machine |
| **2** | **§2's cherry-pick** | cheap, and it closes one of the two collision causes |
| **3** | **[`0043`](0043-ruling.md) §5 — the flap receipt**: the gate twice on one unchanged tree, two trailers side by side | **measurement only, and it comes before any gate change.** If the gate is flapping, every result under it is in question — including the ones the next two items rely on |
| **4** | **[`0042`](0042-ruling.md)** — `Docs-Snapshot` out of the PR lane | GREEN, small, and it removes the only thing that has ever made a PR red |
| **5** | **[`0043`](0043-ruling.md) §4** — the hook split, quick-for-commit / full-for-push | GREEN, **with its fail-first: a deliberately red tree must still be refused at push** |
| **6** | **[`0038`](0038-ruling.md)** — the DXF integration | the big chunk. **Start it on a fresh context**, not at the end of a session |

**Items 4 and 5 are ordered ahead of the DXF work deliberately: they are what
makes everything after them cheaper**, and they are small. **Item 3 is ahead of
both because it decides whether the gate's word is worth anything.**

## 4. WHAT IS ON PATRICK, AND IT IS BLOCKING MORE THAN IT LOOKS

**The shower redraw check** — [`0034`](0034-ruling.md) §2's **two** questions, on
`docs/evidence/shower-glance-after.png`:

1. **Do the three read as different things at a glance?**
2. **Is that camera the distance you actually work at?** If no, the check has not
   been run — the fixture gains a working-distance camera and both renders are
   retaken.

**That branch also carries the four missing mailbox files.** §2's cherry-pick
makes the mailbox whole without waiting, **but the branch itself stays parked
until the check happens** — and it is the oldest open thing in the queue.

## 5. TIER

**All of §3 is GREEN except item 6**, which is AMBER and already ruled at
[`0038`](0038-ruling.md) §8.
