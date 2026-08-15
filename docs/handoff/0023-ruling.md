# 0023 — ruling: session continuity, and the reviewer's checkpoint is a QUESTION

**Patrick, 2026‑08‑15:** *"What happens when CoWork runs out of context? Is there
a special command that I should use to get CoWork in sync?"*

**Filed because the answer is "make the reviewer file what it is holding", and
answering that in chat would have been the joke telling itself.**

---

## 1. THE ASYMMETRY, STATED ONCE

**Code's state is partly in its head** — what it was mid-way through, which
approaches it had ruled out, why it chose the one it did. **None of that is on
disk until `checkpoint` puts it there.**

**Cowork's state is not.** A ruling is written to `docs/handoff/` in the same
turn the decision is made, so a dead reviewer loses **the conversation and
nothing else.** Recovery is a new session and one sentence:

> **`where do things stand?`**

Patrick's project instructions already carry the reading order — handoff
highest-first, the agreement, the snapshot, the register — so the orientation
needs no prompt beyond that. **Measured: it took one turn on 2026‑08‑15.**

**There is no `/clear` or `/compact` in Cowork** — those are Claude Code's, and
they do not apply here. **Nor is there a context readout the reviewer can quote**,
so neither party gets a warning. That is precisely why §2 is a discipline rather
than an alarm.

## 2. THE REVIEWER'S CHECKPOINT IS A QUESTION, NOT A COMMAND

> ### `anything unfiled?`
>
> **The only thing a Cowork death can cost is a decision made in conversation
> and not yet written.** That question flushes it. It is the exact analogue of
> `checkpoint` — it moves state from a head to the disk — and it is a question
> because the reviewer has nothing else to do.

**Ask it before a long gap, before ending a session, and any time the exchange
has run long without a file being written.** A correct answer is often *"nothing
— everything decided is in 00NN."*

**AND THE STANDING OBLIGATION IS THE REVIEWER'S, NOT PATRICK'S:** write the
ruling in the turn the decision is made, never hold it for a tidier one. **This
ruling exists because that guard slipped** — four findings sat in conversation
across three exchanges while their own argument was that such material
evaporates.

## 3. `checkpoint` → `/clear` → `resume from NNNN — and MMMM is up`

**Recorded because the last step is not obvious and was learned from a live
outage** (2026‑08‑15, Code ran out mid-checkpoint):

* **`checkpoint` frees no tokens.** It makes the state durable so that losing
  the context costs nothing. It is not a context command.
* **`/clear`, not `/compact`.** A compaction summary is **a second version of a
  record that already exists on disk**, and this project has measured what
  second versions do. Once the checkpoint is committed, a fresh context reading
  the report is better informed than a summary of the conversation that produced
  it.
* **`resume from NNNN — and MMMM is up` is ONE LINE DOING TWO JOBS.** *"resume
  from"* restores **where Code was**; *"is up"* delivers **what landed while it
  was down.** **The reviewer keeps ruling through an outage**, so a bare resume
  rejoins the flow already behind. Both halves, every time.

Pictured in [`channel-commands.svg`](channel-commands.svg) beside this file.

## 4. A RED GATE MAKES A TREE UNCHECKPOINTABLE — so checkpoint from GREEN

`.claude/hooks/verify_gate.py` blocks on `verdict != "GREEN"`, without exception.

> **A RED TREE CANNOT COMMIT ANYTHING — INCLUDING THE REPORT THAT WOULD EXPLAIN
> WHY IT IS RED.** There is no such thing as checkpointing broken work.

**So `checkpoint` is said EARLY, at a green gate, never at the limit.** The
standing rule *commit at every green gate* is what makes this cheap: the worst
case is losing one increment of reasoning rather than a session's.

**If context runs out while red anyway**, what survives is the branch's last
green commit plus the uncommitted working tree, and the next session re-derives
intent from `git diff`. **That is a recovery, not a checkpoint**, and it should
be named as one in whatever report follows.

## 5. CODE WATCHES ITS OWN CONTEXT — PATRICK CANNOT SEE IT

**Code can read `/context`. Patrick cannot.** Making the human the trigger for
something only the agent can measure is the same error as hand-ticking a status
board ([`0019`](0019-ruling.md)).

> **STANDING OBLIGATION ON CODE: when its context is filling, checkpoint at the
> next green gate and say so — without being asked.** `checkpoint` stays in
> Patrick's vocabulary as an override for when *he* wants to stop, not as the
> primary trigger.

## 6. `CLAUDE.md` DOES NOT POINT AT THE MAILBOX

Its *"Starting a session"* section sends a fresh session to
[`../SESSION_SNAPSHOT.md`](../SESSION_SNAPSHOT.md) **and does not mention
`docs/handoff/` at all** — three days after the channel contract made that
directory the primary work surface.

**Add it.** One line, naming the mailbox and the highest-number-is-current rule.
Until then, naming the report number in the resume phrase is what closes the gap.

## 7. PROJECT MEMORY STAYS EMPTY — DELIBERATELY

Cowork has a persistent project memory. **It holds nothing, and that is the
ruling, not an oversight.**

> **EVERY FACT ABOUT THIS PROJECT'S STATE IS DERIVABLE FROM THE REPOSITORY, AND
> A COPY IN MEMORY WOULD BE A SECOND VERSION OF THE RECORD** — the exact object
> this project has ruled against repeatedly, and one with no gate, no history
> and no way for Patrick to read it.

**If something is worth a new reviewer knowing, it goes in the repository where
both agents and Patrick can see it.** Memory is not a third channel.

## 8. TIER

**GREEN** — documentation and one `CLAUDE.md` line. No new semantics.

**Order:** behind [`0022`](0022-ruling.md). The evidence render and the AMBER
check come first; none of this blocks them.
