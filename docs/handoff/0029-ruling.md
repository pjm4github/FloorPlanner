# 0029 — ruling: the next tranche — the predicate FIRST, and it re-decides the redraw list

**0028 verified on disk before this was written**, not taken from the terminal:

| | before | after |
|---|---:|---:|
| `SESSION_SNAPSHOT.md` | 600 lines / 41,093 B | **268 lines / 18,006 B** |
| `handoff/README.md` | — / 26,906 B | **156 lines / 10,211 B** |

`main == origin/main == 156135f`. Gate GREEN, `collected=731`.

**One thing to carry, not a finding:** those two numbers are a differential
receipt and they exist nowhere on the record. **Put them in the progress
entry** — one line. A 56% cut with no receipt is indistinguishable from a
tidy-up nobody measured.

---

## 1. THE TRANCHE — the predicate goes FIRST, and it is not a separate chore

[`0025`](0025-ruling.md) §4 put the three artwork redraws first.
**They still lead, but something goes in front of them, and it is one commit.**

> ### BUILD THE EXTRUDABILITY PREDICATE FIRST, BECAUSE IT IS THE REDRAWS' ACCEPTANCE CRITERION.
>
> Without it, *"does the redraw work?"* has exactly one answer available —
> **Patrick looks at it** — and that spends the AMBER check on a question a
> grep can settle. **With it, the redraw has a fail-first receipt**: red on the
> symbol today, green on the symbol after, and Patrick's eye is left for the
> only question it is uniquely good at.

**This is not the general-mechanism-first sequence from
[`0015`](0015-ruling.md)** — it is the fail-first receipt this project already
requires of every fix. The predicate is the instrument, not the work.

## 2. THE PREDICATES — three, from [`0016`](0016-ruling.md) §5d, unchanged

| | assertion | catches |
|---|---|---|
| 1 | **every catalog symbol has at least one closed FILLED shape** | `glass_shower` — all strokes, extrudes to nothing |
| 2 | **the body is ONE connected region, not N fragments** | `boat_trailer` — five slabs and no trailer |
| 3 | **a REPORTED census: which items have a body but NO internal region** | `shower`, and whatever else is a featureless box |

**1 and 2 FAIL the gate. 3 REPORTS and does not fail** — `box` and `slab` forms
are legitimately featureless, and a hard failure there would be wrong.

**Nothing in the suite asks any of this today.** `svg_error` (D70) checks
well-formedness; `test_every_catalog_symbol_renders_something` (D71) checks that
a symbol draws ink — **and `glass_shower` draws plenty of ink and extrudes to
nothing.** That gap is the whole reason these exist.

## 3. THE CENSUS RE-DECIDES THE LIST, AND I EXPECT IT TO SHRINK

Measured on disk today:

```
glass_shower     filled=0  data-h=0     <- nothing closed at all
shower           filled=1  data-h=0     <- a bare rect, no internal feature
walk_in_shower   filled=2  data-h=1     <- has a bench
```

**`walk_in_shower` was put on the authoring list by [`0016`](0016-ruling.md) §4
when its bench was being punched into the ceiling.** The vessel/enclosure fix
landed, and [`0025`](0025-ruling.md)'s check confirmed the bench now stands on
the floor. **A bench IS the categorical mark §2 of 0016 asked for** — so
`walk_in_shower` may already be distinguishable from `shower`, and may need no
redraw at all.

> **I AM NOT RULING IT OFF THE LIST FROM TWO GREPS.** The census in §2 row 3 is
> the measurement that settles it — **the list is whatever that census names**,
> and if it names two rather than three, that is the same
> build-then-re-measure-then-decide sequence [`0015`](0015-ruling.md) recorded,
> arriving a second time on its own.

**Report the census output before starting any redraw.** If it shrinks the list,
say so in the report rather than quietly redrawing three.

## 4. THEN THE REDRAWS — AMBER, one check for however many remain

**The brief is [`0016`](0016-ruling.md) §2–3 and has not changed:** these
enclosures are indistinguishable because identity is carried by **footprint, a
scalar**. The fix is an **internal region that differs in KIND** — a door panel,
a curb, a bench — not a different size.

**Patrick's check is one question, and it is deliberately about a glance rather
than a comparison:** *do the shower, the walk-in and the luxury glass shower
read as three different things without being put side by side?*

**A scalar holds in a side-by-side and fails at a glance, and a glance is what
the user gives it.** That is the D74 rule, and the check is written so a
side-by-side cannot pass it by accident.

## 5. `boat_trailer` STAYS OFF, AND PREDICATE 2 IS WHY IT IS SAFE TO LEAVE THERE

[`0025`](0025-ruling.md) §5 put it with the vehicle loft. **Predicate 2 will
report it as five fragments and go red** — that is correct and it must not be
"fixed" by redrawing the artwork. **Exempt it explicitly, in the test, with the
reason and a pointer to the loft** — an exemption without a stated reason is how
a known finding becomes an ignored one.

## 6. WHAT MOVES DOWN, AND HONESTLY WHY

**[`0019`](0019-ruling.md)'s `STATUS.md` drops behind the artwork.** Patrick now
has a Cowork skill that renders the same state on demand from git, the gate and
the generated register.

**That is a VIEW, not the artifact.** `STATUS.md` is still owed: it is committed,
gate-checked, and readable by Code and by a session that has no Cowork attached.
**The skill removes the urgency, not the requirement** — and it reads `STATUS.md`
in preference to anything else the moment that file exists.

**Grid snap stays third, and its read-back still comes before any code.**

## 7. TIER

**The predicate and census: GREEN.** A test and a report, no new semantics.
**Its receipt is the fail-first** — red on `glass_shower` today.

**The redraws: AMBER**, one check for all of them together.
