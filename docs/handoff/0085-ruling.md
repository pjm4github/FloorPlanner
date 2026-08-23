# 0085 — ruling: shorter exchanges, and `CLAUDE.md` down to the traps

**Patrick's instruction:** *"keep the exchange shorter and reduce CLAUDE to non
obvious instructions."*

---

## 1. THE CHANNEL

`WORKING_AGREEMENT.md` already says *"Keep rulings short."* **I have not been.**
Recent rulings run 8–12 KB; Code reads several per session, and
[`0084`](0084-ruling.md) was written the day a context limit stopped work.

**Bar, both sides: one screen — roughly 3 KB — per file.**

**The one exemption, and it is narrow:** *raw measured values* — a table of
per-item numbers — do not count against it. [`0066`](0066-ruling.md) §2's 63
displacements exist so a different cut can be argued without re-measuring; that
is the thing this project cannot afford to lose. **Argument compresses.
Measurements do not.**

Everything else goes: restated history, a finding argued three ways, quoted
precedent where a citation would do.

## 2. `CLAUDE.md` — 13,824 BYTES, RELOADED EVERY TURN

**Measured: 84 lines, ~3.5k tokens, on every request forever.** Six of those
lines are single paragraphs over 1,000 characters.

**THE TEST FOR WHAT STAYS, and it is one question:**

> **Would a competent reader get this WRONG from the code — or just get it
> slowly?**
>
> **Wrong stays. Slow goes.** Structure is in the imports. History is in
> `handoff/` and `V5_MIGRATION_PLAN.md`. **Only traps belong here.**

**KEEP** (each is a thing the code actively misleads you about):

* scene units are inches
* the four are **mixins, not wrappers** — add to the owning module
* late imports **only** to close a real cycle
* `snapshot()` / `design_document()` / `serialize()` are three different things
* `assets/` is generated — edit `_gen_assets.py`
* a corner is one shared `Vertex`; moving it moves everything on it
* headless: no synthesized Ctrl-modified keys (leaks `keyboardModifiers()`)
* `QApplication` before `QImage`; keep it in a module global; `arr.copy()`
* don't memoize the wall path; don't move junction work into `paint()`
* wheel zoom is coalesced — keep per-event work off the sync path
* E402 suppressed in headless scripts, and why
* `pytest --quick`

**CUT** — the module dependency roster, the phase-by-phase account of what died
when, the measured perf figures, the narrative on extract/join and floors.

**NOTHING IS DELETED, ONLY MOVED.** For each cut paragraph, name the file that
already carries it — or move it there first. **A trim that loses the only copy
of a fact is worse than the file being long.**

**Target: under 2 KB.** If a cut cannot get there without losing something that
passes the test above, **say so and leave it in** — the number is a target, not
the rule; the test is the rule.

## 3. TIER

**GREEN.** Documentation only, no behaviour, no schema. Receipt: the byte count
before and after, and the destination named for every cut paragraph.

**Nothing in [`0084`](0084-ruling.md) changes** — its items 1–6 stand in that
order, and PR #37 still waits on §1's `T` before it is worth checking.
