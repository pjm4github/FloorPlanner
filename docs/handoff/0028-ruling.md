# 0028 — ruling: do NOT fragment the snapshot. Enforce its own contract instead.

**Patrick, 2026‑08‑16:** *"SESSION_SNAPSHOT.md is getting really big. Should
that be fragmented so that we arent sending that back and forth to Claude? I
worried about token use."*

---

## 1. THE MEASUREMENT FIRST — the snapshot is THIRD

| bytes | ~tokens | file |
|---:|---:|---|
| 101,307 | ~20,200 | `V5_MIGRATION_PLAN.md` |
| 94,734 | ~20,750 | `WORKING_AGREEMENT.md` |
| **41,093** | **~8,050** | **`SESSION_SNAPSHOT.md`** |
| 30,843 | ~5,600 | `defects/INDEX.md` *(generated)* |
| **26,906** | **~5,365** | **`handoff/README.md`** |
| 22,507 | ~4,765 | `ROADMAP.md` |
| 13,908 | ~2,590 | `CLAUDE.md` |

**And the cost is paid ONCE PER SESSION, not per turn** — neither agent
re-sends a file it has already read. Eight thousand tokens once is real but it
is not the bill.

> **THE FASTEST-GROWING FILE IN THE READ PATH IS `handoff/README.md`, AND IT IS
> NOT CLOSE.** 15,292 bytes on 2026‑08‑14 → **26,906 today**. **+76% in two
> days**, because its pair table gains a dense paragraph **per exchange**.
> Nothing else in the repository grows per-message. **On the current slope it
> passes the snapshot inside a week.**

## 2. FRAGMENTING IS THE WRONG INSTRUMENT, AND THIS PROJECT HAS THE RECEIPT

**One file with one staleness marker became eight commits stale, and what fixed
it was a GATE ON THAT ONE MARKER.**

> **SPLIT IT INTO N FILES AND YOU HAVE N STALENESS SURFACES AND ONE GATE.**
> The `SNAPSHOT-HEAD` check asserts the marker and the `main` row in §1 carry
> the same hash. That works because there is one of each. **Fragmentation
> multiplies exactly the thing the gate was built to hold down**, and the
> failure it prevents is the one that already cost an archaeology pass.

**And a reader who must open five files to learn the state will read three.**

## 3. THE REAL DIAGNOSIS — the file stopped being what its own header says

Its second paragraph reads: *"an **index and a state marker**, not a second copy
of the record."* Measured against that, by section:

| lines | section | is it state? |
|---:|---|---|
| 21 | **§1 Where the work stands** | **YES — this is the state marker** |
| 104 | §0 Where the work is | head is state; the rest is narrative |
| 146 | The queue | **restates the rulings it links to** |
| 102 | §3 Rest of the queue | **restates the rulings it links to** |
| 73 | §5 The rules that bind | **a summary of `WORKING_AGREEMENT.md`** |
| 48 | §6 Things that waste your time | **YES — highest value per token in the repo** |
| 26 | §4 How to read the record | yes, and stable |
| 56 | header + gate box | mostly rationale, and it is load‑bearing |

**The genuinely volatile state is about 25 of 600 lines.** The file is not too
big for what it is — **it is doing three other jobs it already forbade itself.**

> ### AN INDEX THAT SUMMARISES THE THING IT INDEXES HAS STOPPED BEING AN INDEX.
>
> It is now a second version, with all of a second version's properties: it can
> disagree with its source, nothing checks that it doesn't, and a reader cannot
> tell from the page which one is authoritative. **This project has ruled on
> second versions repeatedly. This is one, in the file whose own header forbids
> it.**

## 4. THE RULING

**ONE — NO FRAGMENTATION.** One file, one marker, one gate.

**TWO — §5 BECOMES POINTERS.** The rules live in
[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md). §5 keeps **the names of the
rules and a link each** — enough to know a rule exists and where to read it,
which is what an index owes. **It stops carrying their reasoning.**

**THREE — THE QUEUE COLLAPSES TO ITS HEAD.** The current item, the next two, and
a link each to the ruling that owns them. **A ruling already states its own
order and tier** — [`0025`](handoff/0025-ruling.md) §4 does exactly this — so
the queue sections are restating files that are one click away and cannot go
stale.

**FOUR — §1, §4 and §6 ARE KEPT AS THEY ARE.** §1 is the state marker the gate
checks. §6 is the trap list, and **it is the single highest-value-per-token
thing in the repository** — every line is something that has already cost
someone hours.

**Target: about 200 lines.** Not a hard number; the test is whether every
remaining line is **state, a pointer, or a trap.**

## 5. AND THE ONE THAT ACTUALLY NEEDS THE CAP — `handoff/README.md`

**Its pair table gives each handoff a paragraph summarising the ruling it links
to.** That paragraph is **a second copy of a file sitting one click away** —
the same fault as §5, growing per exchange rather than per week.

> **ONE LINE PER PAIR: the number, and a single clause naming the subject.**
> Anyone who needs the reasoning opens the ruling, which is where the reasoning
> already is and where it cannot drift from itself.
>
> **The protocol prose at the top of that file stays** — it is the channel
> contract and it is not a copy of anything.

**Existing rows are re-cut in one pass**, not left as a two-standard table.

## 6. WHAT IS NOT RULED HERE

**`WORKING_AGREEMENT.md` at ~20,750 tokens and `V5_MIGRATION_PLAN.md` at
~20,200 are each two and a half times the snapshot**, and neither was asked
about. **The agreement is genuinely a rules corpus** — its size is its content,
and it is read by the reviewer rather than at every session start. **The plan is
frozen history** as of [`0019`](handoff/0019-ruling.md).

**Neither is a problem today. Both are named here so that "the snapshot is the
big one" does not become received wisdom** — it is third, and the file growing
fastest is the mailbox index.

## 7. TIER AND ORDER

**GREEN** — documentation only, no new semantics.

**Behind [`0027`](0027-ruling.md)**, which is unblocking a merge. **Ahead of
[`0025`](0025-ruling.md) §4's three items** only if Code is already in the
documents; otherwise it waits its turn. **It is housekeeping and must not
displace the artwork or grid snap.**
