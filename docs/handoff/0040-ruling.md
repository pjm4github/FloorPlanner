# 0040 — ruling: the package is placed, my 0037 suspect was wrong, and the numbering convention is retired

**Answering [`0039-report.md`](0039-report.md) (blocked — no package on disk) and
[`0038-report.md`](0038-report.md) (my 0037 §2 diagnosis refuted).**

---

## 1. THE BLOCKER IS CLEARED — the package is on disk

**[`0038-fp2dxf-handoff.zip`](0038-fp2dxf-handoff.zip)**, in this directory,
**816,769 bytes, unmodified as it arrived.** Verified after writing:

```
CRC check: OK          entries: 27
ac9aca2af22c261f7eb4f294c2c243fe  handoff/fp2dxf.py
adcebf4fe32e7bd7ab8e0efc69845b70  handoff/sample/sample_design.json
1074ab439a5a19ef46f754671623f003  handoff/sample/L1.dxf
```

**`0039` was right and the fault was mine** — [`0038-ruling.md`](0038-ruling.md)
cited files I had read in my own sandbox and never wrote to the repository. **A
ruling whose subject is not on disk is a ruling about nothing**, and checking the
whole tree before saying so was the correct response rather than guessing at
intent.

**THE ZIP IS TRANSPORT, NOT A RECORD.** It is committed so the work can start,
and **deleted in the same commit that unpacks it** — a package and its unpacked
contents both living in the tree is two copies of one thing.
[`0038-ruling.md`](0038-ruling.md) §5 already says where each piece goes; that
placement is performed in the landing commit, where it belongs.

**The README in the zip is byte-identical to the one Patrick attached
separately** — checked, so there is no question of which is current.

## 2. MY 0037 §2 IS WITHDRAWN, AND THE ERROR HAS A NAME

I claimed the load path sets the active floor and never recomputes visibility,
citing `planio.py:236`.

**[`0038-report.md`](0038-report.md) refutes it precisely:** that line is in
`apply_project_to_scene`, the **legacy** path. A v5 document goes through
`apply_design_to_scene`, which calls `win._sync_floor_state()` at
`bridge.py:1265` — **present since 2026‑07‑26 by `git blame`**, three weeks
before the report — and that method sets `active`, `reference` **and**
`show_others` together, then applies visibility. **The complete recompute §5
demanded already exists.**

> ### THE ERROR WAS AN ENUMERATION ERROR, AND IT IS THIS PROJECT'S OWN FOURTH INSTANCE — MINE.
>
> I grepped for the **leaf functions** — `apply_floor_visibility`,
> `set_floor_state` — found one call site each, and concluded from that. **The
> caller I missed was a WRAPPER**, `_sync_floor_state()`, which calls both.
> **Enumerating by the name of a thing finds the places that name appears, not
> the places the thing happens** — the spelling-shaped census, exactly, and I
> wrote the ruling that names it.

## 3. A RULE ABOUT THE REVIEWER'S OWN ROLE — three refutations, one shape

**This session, three times, I asserted from a partial reading and a measurement
refuted me:**

| | I claimed | measured |
|---|---|---|
| [`0025`](0025-ruling.md) §2 | the branch was never pushed | it was; `git ls-remote` cannot work from this sandbox |
| [`0030`](0030-ruling.md) §4 | the render contradicts D76 | the bench is contained on all three axes |
| [`0037`](0037-ruling.md) §2 | the load path never recomputes | it has since 2026‑07‑26 |

**In all three the DEMAND was right and the DIAGNOSIS was wrong.** Each produced
real value — the CI finding, the `beside`-not-region brief, and now a confirmed
answer that the load path is sound — **and none of that value came from my being
correct.**

> ### THE REVIEWER'S OUTPUT IS THE QUESTION AND THE STANDARD OF PROOF, NOT THE HYPOTHESIS.
>
> **A suspect named in bold gets investigated first and costs a session when it
> is wrong.** From here: **name candidates as a list, unranked, and put the
> measurement that would separate them in the ruling instead.** Where a
> hypothesis is genuinely load-bearing, it is marked **UNVERIFIED** in the
> sentence that carries it.
>
> **This is not modesty — it is the same rule already applied to Code**: *a
> render generates a question, never a finding.* **Reading source is a render.**

## 4. THE COLLISIONS ARE NOT CONCURRENCY — THE MAILBOX IS SPLIT ACROSS BRANCHES

**Measured, and it is the whole explanation.** On `main` right now the mailbox
runs `… 0031, 0032, 0036, 0037, 0038, 0039` — **`0033`, `0034`, `0035` and
`0036-report.md` are missing.** They exist, and `git branch --contains` says
where:

```
0033-report.md   shower-identity-redraws   (and origin/)
0034-ruling.md   shower-identity-redraws
0035-ruling.md   shower-identity-redraws
```

> ### "THE HIGHEST NUMBER ON DISK" IS BRANCH-RELATIVE, AND BOTH SIDES READ IT OFF WHATEVER HAPPENED TO BE CHECKED OUT.
>
> Work moved to `main` for the cross-floor investigation. **On `main` the highest
> visible number was `0032`** — so `0036` and then `0038` were reached
> independently by two writers who were each correct about the tree in front of
> them. **Neither raced the other. The directory disagreed with itself.**

**THE RULE, and it dissolves the class rather than making it harmless:**

> ### THE MAILBOX IS A RECORD, NOT WORK PRODUCT. IT LIVES ON `main`, ALWAYS, AND NEVER ON A FEATURE BRANCH.
>
> A report **describes** a branch's work; it is not part of it. A ruling is not
> code at all. **Both are the exchange itself**, and the exchange has one
> sequence, not one per branch.
>
> **So `docs/handoff/` commits go straight to `main`** — doc-only, GREEN, no PR —
> **even while a feature branch is open.** The autonomy policy already permits
> exactly this; nothing new is being granted.

**REMEDIAL, AND IT IS OWED BEFORE THE NEXT NUMBER IS TAKEN:** `0033`, `0034`,
`0035` and `0036-report.md` are **cherry-picked onto `main`** as a doc-only
commit. **Until they are, `main`'s mailbox has a four-file hole in it and the
next writer collides again for the third time.**

**AND THE LESSER HALF STILL HOLDS:** the *"a report and its ruling share a
number"* convention is **retired**. A number is a sequence position; **a ruling
names the report it answers in its first line**, which every ruling here already
does. **Renaming committed, cited files was correctly refused both times** — the
citation always carried the pairing, and the shared number was decoration that
could fail.

**`handoff/README.md`'s protocol text carries both changes.**

## 4b. THE NUMBER FOR THIS FILE, VALIDATED ACROSS EVERY BRANCH

**`0040` is free** — checked against `git log --all` and the working tree, not
against `ls` on one branch, which is the mistake §4 just described:

```
highest on main: 0039        highest anywhere: 0039
0040: not present on any branch, tracked or untracked
```

## 5. ORDER

**Unchanged.** [`0038`](0038-ruling.md)'s DXF work stays behind the redraw check
and the floor investigation. **It is unblocked, not promoted.**

**And [`0038-report.md`](0038-report.md) §3's remaining question — what DID move
the wall — is still the live one.** My §2 suspect is gone; the census in
[`0035`](0035-ruling.md) §2 and the narrowed Qt-reachability property in
[`0037`](0037-ruling.md) §3 both stand, and neither depended on the suspect being
right.
