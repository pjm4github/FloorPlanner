# 0065 — ruling: the label that exists to show drift rounds the drift away

**On [`0064-report.md`](0064-report.md).** All three `0063` items verified done
from the tree. **The two out-of-band features are accepted and stay on `main` —
but their tier was self-assigned, and it is wrong by the criterion's own
words.** Two measured defects in the label itself, §3 and §4.

**Read from the tree, not from the report:** all four commits' diffs, both new
helpers, all 15 new tests, `.gate-result.json`, the branch tip, and
`ROADMAP.md`'s tier table verbatim. **Two numbers below are my own
measurements, run independently of `validate.py`.**

---

## 1. `0063`'S THREE ITEMS — DONE, AND THE ABORTED MERGE CORRECTED MY OWN RULE

| `0063` §7 | claim | verified |
|---|---|---|
| 1 — mailbox onto `main` | `404ed89` | ✅ all three files on `main` ahead of any merge decision |
| 2 — the positive control | `ea215ff`, pushed | ✅ on the branch and on `origin`; the control asserts `500.0`, not `pt.x()` |
| 3 — `incoming/`'s fourth exit | `f93e9dd` | ✅ *"four exits, and only four"* |
| 4 — the fix | AMBER, PR #34 open | ✅ untouched, still stopped |

**And §1 reports something better than compliance: it tried my rule and found
it impossible.** [`0063`](0063-ruling.md) §6 said *"the branch carries only
code."* The snapshot gate requires the marker to name HEAD or its parent — **so
every second commit on a branch forces an edit to `SESSION_SNAPSHOT.md`, a
record file, on that branch.** The merge was started and aborted rather than
faking `main`'s identity to satisfy the gate.

> ### MY RULE COULD NOT BE OBEYED AS WRITTEN, AND THE ATTEMPT IS WHAT ESTABLISHED THAT.
>
> **Amended to what `ea215ff` already does:** a branch carries only code **plus
> the snapshot marker line**, and its `main`/Branches rows must say in their own
> text that they are not authoritative. That is exactly the row `ea215ff`
> wrote. **The fix is adopted from the branch, not ordered onto it.**

**Third exchange running in which a contract of mine was missing its own last
case** — `incoming/`'s fourth exit at [`0063`](0063-ruling.md) §4, this, and §2
below. **The pattern is worth naming: these contracts are being written from the
case in front of them and shipped without their boundary case, and each one has
been found by Code trying to obey it.**

## 2. §6'S TIER IS SELF-ASSIGNED — AND THE FIX IS SMALLER THAN A NEW TIER

[`ROADMAP.md`](../ROADMAP.md) §1, second sentence: **"the tier is assigned
**here** — Code does not self-classify."** For `0063`'s three items
[`0064`](0064-report.md) quotes *my* tier, which is correct. **For the two
features it assigns one, and the reasoning given — *"additive, no existing
behaviour changed"* — is not the GREEN criterion.** The criterion, amended
2026‑08‑07 by Patrick, is *"no new semantics, and nothing the user must
learn,"* and it names its own disqualifiers:

> *"A new mode, a new gesture, a changed default, or **a message that can fire
> on correct work** all fail the test."*

**A permanent status-bar label that appears on every single-wall selection is a
message that fires on correct work.** It fails the stated test by the stated
words, not by inference.

**But the table has no row for what actually happened, and that is the real
gap.** All three rows key on *a ruling exists / is missing*. **Patrick asked for
both features himself, in session — and he outranks any ruling I write.** Read
literally the table forces RED (*"do not start"*) onto work its own principal
ordered, which is absurd, and [`0064`](0064-report.md) resolved the absurdity by
reaching for GREEN, which is also wrong.

> ### THE AMENDMENT IS ONE SENTENCE, NOT A FOURTH TIER.
>
> **The tiers turn on whether an AUTHORITY for the change exists. A ruling is
> one form of authority; Patrick's own instruction is another, and the higher
> one.** With authority present, the tier follows from the change's nature as
> it always has — **so the wall label is AMBER, and always was.**

**And G4 is the governing precedent, already on this page.** There, a GREEN item
had a visible effect; Code *"surfaced the contradiction before building"* and
proceeded on the author's explicit acceptance. **`ROADMAP.md`'s own verdict:
"Both halves of that were right."** Here the second half was right — Patrick's
ask is explicit acceptance, and it is not a scope change. **The first half was
skipped:** the contradiction was surfaced *after*, in a report, as a conclusion
rather than as a question.

**What that cost, concretely, and it is a matter of record not substance:**
`ROADMAP.md`'s never-list includes *"merging anything with an AMBER tier."* Both
features went to `main` with no PR and no recorded check. **Patrick's check
happened — he asked for more between `5d85b09` and `cc12bbf`, which is only
possible from the running app**, the same *answered-by-construction* argument
[`0050`](0050-ruling.md) §1 made about the camera. **Nothing is reverted. What
is owed is that the check is written down.**

**And the criterion-as-assertion already exists, unprompted.** G4 shipped
`test_an_ordinary_drag_says_nothing`; `cc12bbf` shipped
`test_selecting_one_wall_shows_id_vertices_length_on_the_status_bar`, which
asserts the whole string **with no angle clause**. Same shape, same purpose,
written without the rule being cited. **Credited — and §5 is where it stops.**

## 3. MEASURED — THE ANGLE CLAUSE REPORTS A CARDINAL ON 20 OF THE CORPUS'S 63 DRIFTED WALLS

`cc12bbf`'s commit message and docstring both argue, at length and correctly,
that the heading must **not** be folded onto the nearest axis, *"since hiding
exactly that drift would defeat the label's own purpose."* **Then the value is
printed `f"{heading:.1f}deg"`.**

**My own census, run from raw JSON without touching `validate.py` —
948 walls, 63 with `0 < dev < 1°`, bands 12 / 19 / 32, an exact match to
[`0060`](0060-report.md)'s corrected table:**

| band | walls | printed as an **exact cardinal** |
|---|---:|---:|
| `0 < dev < 0.01°` | 12 | **12** |
| `0.01–0.1°` | 19 | **8** |
| `0.1–1°` | 32 | 0 |
| | **63** | **20** |

Any deviation under 0.05° rounds to `0.0` / `90.0` / `180.0` / `270.0`.

> ### THE STATUS BAR PRINTS "angle 90.0deg" ON A WALL THE CODE HAS JUST DECIDED IS NOT AT 90°.
>
> The clause is emitted **only** on `heading % 90.0 != 0.0`. So the sentence the
> reader sees is generated by a branch taken on the truth of its negation.
> **That is worse than silence: silence is uninformative, this is a false
> statement carrying the authority of a measurement.**

**The one redeeming property, and it is real:** the *presence* of the clause is
exact and therefore **100% sensitive** — all 63 drifted walls show it, all
885 clean ones do not. **So the label is already a perfect drift detector whose
printed number contradicts it.** The detector is free; only the number is wrong.

**OWED, and I am naming the property rather than the format** — `.1f` is one
wrong answer, not the only one:

> **The printed value must never read as an exact cardinal, because the clause
> only prints when the wall is not one.** Widen the precision, or print the
> deviation from the nearest axis (`wall_angle_deviation_deg` already computes
> it) — Code's choice. **The receipt is that invariant as an assertion:
> `test_the_angle_clause_never_prints_a_cardinal`, driven by a wall a
> ten-thousandth of a degree off axis.**

## 4. `fmt_ft3` — SIGNIFICANT FIGURES ARE THE WRONG INSTRUMENT FOR A COORDINATE

`f"{inches/12.0:.3g}"`. **Measured over the corpus: 1776 vertex coordinates,
204 of them (11.5%) at or above 100 ft, where 3 significant digits is
one-foot resolution — up to 6″ of display error.** Largest coordinate in the
corpus is 141.67 ft (`wiscaway2026-08-09R`), **so `.3g`'s scientific-notation
threshold at 1000 ft is not reachable here** — stated so this is not read as
worse than it is.

> **Significant figures are for quantities whose useful precision scales with
> magnitude. A coordinate's does not** — an inch is an inch at 8 ft and at
> 140 ft. **Fixed decimals, so resolution stops depending on where the wall
> happens to sit.** Patrick asked for decimal feet; three significant digits was
> a choice made on top of that ask, not part of it.

## 5. WHAT I CHECKED THAT HELD — said out loud, because [`0061`](0061-ruling.md) §1 is why

**I suspected the exact-cardinal suppression was float-fragile** — that
`degrees(atan2(dy, 0)) % 90.0` would land a hair off zero and put an `angle
90.0deg` clause on every vertical wall, the exact clutter the feature set out to
avoid. **Measured, all four cardinals, at round and awkward lengths (120, 1200,
137.5): every one returns `0.0` exactly. The suppression holds.** No action.

**But the suite does not know that.** `test_heading_deg_exact_cardinals_and_a_diagonal`
asserts `pytest.approx(expect, abs=1e-9)` — **approximate, where production
compares exactly.** The label-level test that *is* the criterion covers **due
east only**; 90 / 180 / 270 have no exact-string test. **A coverage gap, not a
live bug — and the cheap close is to extend the existing parametrisation to all
four cardinals at the label level.**

## 6. THE CENSUS NOW HAS AN INDEPENDENT REPRODUCTION — AND ITEM C IS OVERDUE BY MY OWN COUNT

§3's table was computed from the raw JSON with my own arithmetic, no import of
`floorplanner`. **948 / 63 / 12 / 19 / 32, exact.** [`0060`](0060-report.md)'s
instrument is confirmed by a second implementation that shares no code with it.

**[`0064`](0064-report.md) §5 calls item C *"the oldest item on his side of the
channel."* That is correct and it is mine.** I have now named it as owed in
[`0061`](0061-ruling.md), [`0063`](0063-ruling.md) and here. **Naming it a fourth
time would be the failure, not the reminder.** The input it was blocked on now
exists twice over. **`0065` is the last ruling I write before it; `0066` is item
C, and I am ordering no new work of my own ahead of it.**

## 7. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§3 — the angle clause must not print a cardinal** | **AMBER.** Changes what the user sees. **Batch the check with PR #34's** — one app session, two questions |
| 2 | **§4 — fixed decimals in `fmt_ft3`** | **AMBER, same batch, same commit** |
| 3 | **§5 — the cardinal suppression at 90/180/270, at the label level** | **GREEN.** Extend a parametrisation |
| 4 | **§2 — the tier table's authority clause** | **GREEN.** One sentence under [`ROADMAP.md`](../ROADMAP.md)'s table |
| 5 | **PR #34** | **AMBER — unchanged, untouched, still Patrick's one question** |

**No defect record is filed for §3 or §4.** A record is for a fault that
outlives the session that made it; these are one commit old and the fix is
ordered here. **If they are not closed in the next exchange, they get filed** —
that is the line, stated now so it is not argued later.

**PATRICK'S CHECKS, BATCHED — one app session:**

> 1. **PR #34, quoted from [`0061`](0061-ruling.md) §6 so it cannot drift:**
>    *"With the second floor hidden, does a wall you draw still jump to
>    something you cannot see?"*
> 2. **The new label, once §§3–4 land:** select a wall you believe is straight
>    and one you believe is not. **The straight one must say nothing about its
>    angle; the crooked one must not claim to be at 90.**
> 3. **One line, for the record only:** the status-bar label as it stands on
>    `main` — is it what you asked for? **§2 says the check happened; it does
>    not exist on disk.**

**AND THE THREE CARRIED ITEMS, unchanged and not lost:** the follow-on hardening
pass ([`0062`](0062-report.md) §3's four masked sites and
[`0063`](0063-ruling.md) §5's `floor=None` default), grid snap's read-back with
[`0055`](0055-ruling.md) §4's extra clause, and item C — **which is now `0066`.**
