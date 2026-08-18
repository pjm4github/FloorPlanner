# 0057 — ruling: the instrument is accepted; its READING has not been reported

**On [`0056-report.md`](0056-report.md).** Item B built, item C untouched, gate
GREEN at `collected=778`.

---

## 1. ACCEPTED, AND FOUR THINGS WERE DONE RIGHT WITHOUT BEING ASKED

**ONE — IT CHECKED MY NUMBERS INSTEAD OF RESTATING THEM.**
[`0055`](0055-ruling.md) §4 quoted *"`planc1.v5.json` carries 6 walls at
0.0666°; `symmetricP1.json` carries 2"* from my own uncommitted probe.
`test_the_corpus_receipt_matches_0055s_own_measurement` runs a **different
implementation** against those files and gets **6** and **2**.

> **That is two independent instruments agreeing, not one asserting the other's
> claim.** A test that had simply hard-coded my numbers would have passed
> identically and proved nothing — **this project's own one-definition rule,
> applied to a receipt rather than to a predicate.**

**TWO — IT NAMED WHAT DOES *NOT* MATCH.** My DXF counts (494 / 134 lines) do not
correspond 1:1 to wall counts, because one wall becomes several line entities.
**Saying so is worth more than the agreement**: two numbers that look like they
should match and quietly do not is how a receipt starts lying.

**THREE — THE POSITIVE CONTROL FOR ZERO.** *"An instrument that always reports 0
can't be told apart from a broken one without a non-zero case beside it."*
**That is [`0022`](0022-ruling.md) §2's rule, applied unprompted, to a new
instrument.**

**FOUR — ASCII BAND LABELS**, because the suite's console is cp1252 and a label
that can appear inside an assertion diff must not be able to crash the failure
message reporting it. **A trap from `SESSION_SNAPSHOT` §6, avoided rather than
hit.**

## 2. BUT THE CENSUS HAS NOT BEEN RUN — and that WAS the deliverable

[`0055`](0055-ruling.md) §4 gave one reason for building B first:

> *"nobody knows how many plans have this … the corpus has been quietly drifting
> and no instrument has ever looked."*

**`tools/validate_design.py` now prints a band summary. [`0056`](0056-report.md)
does not say what it printed.** Two files were checked inside a test; **the
corpus was not.**

> ### AN INSTRUMENT BUILT AND NOT READ IS THE THING THIS PROJECT KEEPS FILING DEFECTS ABOUT.
>
> D71 exists because renderability was checkable and unchecked. D27 exists
> because CI could run the deep gate and did not. **B's whole justification was
> the reading, and the reading is the one thing not in the report.**

**OWED, AND IT IS ONE COMMAND PER PLAN:** run it over **every** file in
`examples/` and `fixtures/`, and report the **band table per plan** — the same
five bands, zero-filled.

**AND STATE THE TOTAL: how many walls in the shipped corpus are within 1° of
orthogonal without being on it.** That single number is
[`0055`](0055-ruling.md) §4's input to item C's tolerance argument, **and C
cannot be ruled without it.**

## 3. TWO CONNECTIONS NOBODY HAS MADE, AND THE FIRST IS ONE LINE

**ONE — THE GUIDE SHOULD SEND THE USER HERE BEFORE EXPORTING.**
`docs/guides/chief-architect-export.md` is where a person goes to get a plan into
Chief. **The orthogonality report is what tells them Chief will complain
before they find out from Chief.** One line in the guide's QC section, and the
loop between the two features closes.

**TWO — A QUESTION, NOT A RULING: should the EXPORT itself warn?**
`fp2dxf`'s `Ctx.warnings` already collects opening overruns and zero-length
walls. **Off-axis walls are the same shape of finding**, and the export is the
moment the user is about to hand the drawing to a tool that cares.

> **Not ruled, because it is scope this task did not carry** and because the
> right answer may be *no* — a warning that fires on every plan with a
> deliberate 45° bay is a warning people learn to ignore. **The §2 census is what
> decides it:** if most plans are clean, a warning is useful; if nearly all
> plans trip it, it is noise. **Another reason the census comes first.**

## 4. ONE SMALL PLACEMENT QUESTION

**The dialog is under `Edit ▸`. A report is not an edit.** Every other entry
under that menu changes the document; this one cannot, by design.

**Not worth a rework on its own** — but [`0054`](0054-report.md) already flagged
a flat-menu-label gap, so **if a menu pass happens, these travel together.**
Named here so it is not rediscovered.

## 5. ITEM C REMAINS RED, AND [`0056`](0056-report.md) WAS RIGHT TO LEAVE IT

*"No button changes a wall's angle."* **Correct, and the restraint is the point:**
a report that grew a Fix button would have pre-empted the tolerance argument
entirely, and the tolerance **is** the design.

**C's ruling waits on §2's census.** Item A — grid snap — also unchanged, with
its extra read-back clause still owed: **does snapping cover an operation's
output, or only cursor input?**

## 6. TIER

**§2's census: GREEN, measurement only.** **§3's guide line: GREEN.**
**Everything else here is a question or a note.**
