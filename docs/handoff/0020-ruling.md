# 0020 — ruling: the three things Patrick ever says

**Patrick, 2026‑08‑15:** *"Im just learning the syntax and methods to coordinate
these 2 agents efficiently."*

**The protocol has never been on disk, which is this ruling's own point against
itself: it has been living in chat, and chat is not the record.**

---

## 1. THE PR ALREADY EXISTS AT AN AMBER STOP — so it is never asked for

The tier table reads **"PR, then stop — Patrick's manual check is the merge
condition."** In that order. **Code opens the PR and then halts**, so by the time
a check is possible the PR is already open.

**What is blocked is the MERGE, not the PR.** *"Do the PR"* is never the right
sentence, because the thing it asks for has already happened.

## 2. THE THREE UTTERANCES, AND THERE ARE ONLY THREE

| when | say | to |
|---|---|---|
| a ruling exists on disk | **`NNNN is up`** | **Code** |
| a manual check passed | **`NNNN check passed:`** + what you saw | **Code** |
| a manual check failed, or you are unsure | **`NNNN check failed:`** + what you saw | **the reviewer** |

> ### `NNNN is up` MEANS EXACTLY ONE THING: A NEW FILE EXISTS ON DISK, GO READ IT.
>
> It is not a general *go*, it does not authorise a merge, and it never refers
> to a file Code has already read. **Same words every time, so Code never has to
> interpret Patrick** — the value is in the phrase being mechanical.

**Everything else is a question, and a question is not a signal.**

## 3. WHY A PASS GOES TO CODE AND A FAILURE COMES HERE — from what actually happened, twice

**Both paths are on the record, one feature apart:**

* **PR #27 — the check PASSED.** Code merged and recorded Patrick's words
  verbatim in [D74](../defects/0074-thickness-cannot-carry-wall-identity-and-the.md)
  and [`../progress/phase-5.md`](../progress/phase-5.md). **No ruling was
  needed; the ruling already existed and the check confirmed it.**
* **PR #26 — the check REFUTED the ruling.** *"Found by Patrick's manual check
  on PR #26"* is D74's opening line. **That is not a merge decision, it is a
  new finding**, and a finding needs a ruling before anyone builds against it.

> ### A PASSING CHECK CLOSES A LOOP. A FAILING CHECK OPENS A RECORD.
>
> They are different kinds of event, so they go to different places. **Sending a
> failure to Code invites it to fix what it thinks you meant**, which is the
> moment a measurement becomes an interpretation.

**"Unsure" routes with the failures.** A hesitation is a finding that has not
been articulated yet, and the cheapest place to articulate it is a ruling.

## 4. SAY WHAT YOU SAW, NOT "PASSED" — the verdict IS the record

**Patrick's check words are quoted verbatim throughout this repository** — D74's
*"cannot tell a fence from a railing at working zoom, and never will"*,
[`0014-ruling.md`](0014-ruling.md)'s *"the three seats are an artwork fix"*,
[`0015-ruling.md`](0015-ruling.md)'s retirement. **Not one of them is
paraphrased**, because the reasoning in the sentence outlives the feature it was
said about.

> **`0018 check passed` GIVES THE ARCHIVE NOTHING.** *"The bench sits on the
> floor, the roof is closed, the pool reads as water in a solid tub"* gives it
> the sentence a future session will quote. **The extra ten seconds is the
> record.**

**And a partial pass is stated as one** — *"one and three yes, two I could not
tell"* is a better record than a verdict rounded to pass or fail, and row 2 of
[`0018`](0018-ruling.md) §7 was designed expecting exactly that answer.

## 5. THE WHOLE LOOP, ONCE

1. **`NNNN is up`** → Code reads the ruling and builds.
2. Code opens the PR. **GREEN merges itself. AMBER stops.**
3. Patrick runs the check the ruling names.
4. **Passed** → `NNNN check passed: <what you saw>` → Code merges, records the
   words verbatim, re-cuts the state.
   **Failed or unsure** → tell the reviewer → next-numbered ruling → back to 1.

**Patrick never asks for a PR, never asks for a commit, and never relays a
report.** Those are Code's, and the pre-commit gate is the only bar on them.

## 6. TIER

**GREEN** — documentation of an existing practice. **Nothing here is new
behaviour**; it is the first time the behaviour has been written where both
agents can read it.
