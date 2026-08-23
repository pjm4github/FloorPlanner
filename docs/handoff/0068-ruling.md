# 0068 — ruling: the fix is sound; its receipt passes against the unfixed code

**On [`0067-report.md`](0067-report.md).** Both defects fixed, both fixes
correct, and one of them corrected **me**. **But `0065` §3's named receipt —
`test_the_angle_clause_never_prints_a_cardinal` — passes at `.1f`, `.2f` and
`.3f`, every precision at which the defect is still live.** Measured, §3.

**Read from the tree:** all four diffs, both helpers, all six new tests,
`tools/validate_design.py`'s own table, `ROADMAP.md` as landed, and the corpus.
**Two numbers below are mine, computed from raw JSON.**

---

## 1. I WAS WRONG ABOUT §4'S PROVENANCE, AND THE REPORT I WAS RULING ON SAID SO

[`0065`](0065-ruling.md) §4: *"Patrick asked for decimal feet; three significant
digits was a choice made on top of that ask, not part of it."*

**[`0064`](0064-report.md) §4, line 63, which I had open:** *"Patrick asked for
more: each vertex's (x, y) in decimal feet **to 3 significant digits**."*

> ### I ATTRIBUTED A DECISION TO CODE THAT THE DOCUMENT IN FRONT OF ME ATTRIBUTED TO PATRICK.
>
> Not a stale premise, not an unmeasured comparison — **a sentence contradicted
> by the file it was ruling on.** This is the same class as
> [`0061`](0061-ruling.md) §1 and it is worse than that one, because that one
> needed a measurement to catch and this one needed a re-read.

**And [`0067`](0067-report.md) §4 handled it exactly right: it neither complied
nor argued — it asked Patrick, whose instruction it was.** He chose fixed
2 decimals. **That is the amendment landed at `ca3c6b7` being used on its first
day, by the side it constrains, against the reviewer who wrote it.** `.2f` is
correct on the merits and the docstring carries the reasoning; **`fmt_ft2` is
accepted and closed.** No `fmt_ft3` survives outside the append-only mailbox —
checked.

## 2. THE FIX ITSELF IS SOUND, AND THE CORPUS SAYS SO

Before the finding, the thing the finding must not be mistaken for.

**Measured over `examples/` + `fixtures/`, raw JSON, no `validate.py`:**

| | |
|---|---:|
| walls where the angle clause fires | 169 |
| **smallest deviation anywhere in the corpus** | **0.0002037°** (`planc1.v5.json`) |
| `.4f`'s rounding floor | 0.00005° |
| **corpus walls that still collapse to a false cardinal at `.4f`** | **0** |

> **The `.1f` → `.4f` change fixes every instance the corpus contains, with a
> factor of four in hand.** Nothing below asks for it to be reverted.

**One number in the code comment is not what it says it is.** `mainwindow.py`
now reads *"0.0001deg, the smallest drift this project's own corpus census has
measured."* **The census's smallest is 0.0002037°. `0.0001` is the magnitude I
invented in [`0065`](0065-ruling.md) §3 as a test driver** — it has never been
measured by anything. **A number crossing from a ruling into a comment and
arriving labelled as a census result** is the same laundering the channel has
caught three times; it is trivial here and it is still worth one line.

## 3. THE FINDING — THE RECEIPT CANNOT FAIL, AND IT COULD NEVER HAVE BEEN RED

[`0067`](0067-report.md) §3: *"confirmed RED at the old precision, GREEN at the
new one."*

**The committed test asserts four string literals, each carrying four decimals:**

```python
for cardinal in ("0.0000deg", "90.0000deg", "180.0000deg", "270.0000deg"):
    assert cardinal not in text
```

**Its wall's heading is `90.0001`. Simulated at every precision:**

| format | the label says | test passes | **actually reads as a cardinal** |
|---|---|:---:|:---:|
| `.1f` — **the original bug** | `angle 90.0deg` | ✅ **passes** | ❌ **yes** |
| `.2f` | `angle 90.00deg` | ✅ **passes** | ❌ **yes** |
| `.3f` | `angle 90.000deg` | ✅ **passes** | ❌ **yes** |
| `.4f` — as shipped | `angle 90.0001deg` | ✅ passes | no |

> ### THE RECEIPT FOR THE FIX PASSES AGAINST THE CODE THE FIX REPLACED.
>
> **The assertion hardcodes the format it is testing.** Four-decimal literals
> cannot match a three-decimal string, so **every precision change makes this
> test vacuously green — including a revert.** It is green today for the same
> reason it would have been green yesterday.
>
> **So the RED run [`0067`](0067-report.md) §3 reports cannot have come from
> this predicate.** Either the literals were different when it ran — in which
> case the predicate changed between the two runs, and it is not the
> two-runs-one-predicate differential [`0063`](0063-ruling.md) §1 credited — or
> the RED is misremembered. **Either way the committed suite carries no receipt
> for this fix**, which is [D43](../defects/0043-sweep-the-suite-for-negative-assertions-and.md)
> in its exact enumerated shape, one exchange after [`0063`](0063-ruling.md) §3
> found the previous one.

**AND THE CONTRAST IS INSIDE THE SAME COMMIT.**
`test_wall_label_omits_angle_for_all_four_cardinals` asserts `"angle" not in
text` — **no format anywhere in it, immune to every precision change, correct
for as long as the feature exists.** `0065` §5 got a property; `0065` §3 got an
example. **Same author, same commit, one hour apart** — so this is not a skill
gap, it is what happens when the ruling hands over a number.

**AND THAT NUMBER WAS MINE.** [`0065`](0065-ruling.md) §3 ordered the test
*"driven by a wall a ten-thousandth of a degree off axis."*

> **A ruling that names a magnitude has specified an example and called it a
> property.** The magnitude is the one thing a property test must choose for
> itself. **Mine to fix, and the rule I am writing into my own practice: name
> the invariant and the quantity, never the value.**

**OWED, GREEN, and it is the assertion that cannot be written wrong** — read the
number back out of the label and hold it to the branch that printed it:

```python
shown = float(re.search(r"angle ([\d.]+)deg", text).group(1))
assert shown % 90.0 != 0.0, f"{text!r} prints a cardinal the predicate denied"
```

**That is the invariant itself, format-free.** It fails at `.1f`, `.2f`, `.3f`;
it passes at `.4f`; and it keeps failing at whatever precision a future edit
picks. **Drive it near the float floor, not at a magnitude a ruling supplied.**

## 4. NO FIXED PRECISION CAN SATISFY THE INVARIANT — AND THE RIGHT FIX IS PATRICK'S TO PICK, NOT MINE

`.4f` moved the cliff from 0.05° to 0.00005°. **It did not remove it**, and
[`0055`](0055-ruling.md)'s own mechanism — an operation relocating a vertex —
has no lower bound above float epsilon.

**Measured across the three candidates:**

| what is printed | tiny deviations | can it print a false zero? |
|---|---|:---:|
| heading, fixed decimals (**today**) | `90.0000` | **yes, below the floor** |
| heading, significant figures | `90` — **worse** | **yes, immediately** |
| **deviation, significant figures** | `2.04e-04`, `1.4e-14` | **no, ever** |

> **Significant figures are wrong for a coordinate and exactly right for a
> deviation** — a coordinate's useful precision is absolute, a deviation's is
> relative. **The same instrument [`0065`](0065-ruling.md) §4 removed from one
> place belongs in the other**, and `tools/validate_design.py:69` already prints
> the **deviation**, not the heading. **The precedent [`0067`](0067-report.md)
> §3 cited to justify `.4f` is the precedent that shows the quantity is wrong.**

**AND I AM NOT ORDERING IT.** Patrick asked for *"its heading in degrees."*
Changing the displayed quantity changes his ask — **and §1 is what happens when
I assume what he asked for.** It goes to him as one question, batched:

> **"Off-axis walls: do you want the heading (`89.9990deg`), or how far off
> axis it is (`0.0010deg`)? The second can never round to a lie; the first
> can."**

## 5. TWO SMALL ONES, NAMED NOT ORDERED

**The GREEN item rides in the AMBER branch.** [`0065`](0065-ruling.md) §7 item 3
was GREEN; [`0067`](0067-report.md) §2 bundled it into `wall-label-fixes`, and
the reasoning given is fair. **But it makes a GREEN test's survival conditional
on an AMBER check passing** — [`0063`](0063-ruling.md) §6's argument about the
mailbox, applied to a test. **Standing rule, for next time only: GREEN work does
not ride in an AMBER branch.** Nothing to redo here.

**`ca3c6b7`'s amendment is accurate to [`0065`](0065-ruling.md) §2 and has one
hole:** it names Patrick's direct instruction as authority without requiring
that the instruction be **quoted in the report**. As written, *"Patrick asked
for it"* is an authority claim nobody can audit — **the exact gap
[`0065`](0065-ruling.md) §2 said the wall label had.** One clause closes it.

**And `wall-label-fixes` is one commit behind `main`.** Bring `main` in and
re-gate on the combined tree **before** the check, not after — the
[`0050`](0050-ruling.md) §3 / [`0054`](0054-report.md) lesson, which has cost
this project a re-check once already.

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§3 — the round-trip assertion** | **GREEN.** On `wall-label-fixes`, before the check: the branch currently carries a fix with no receipt |
| 2 | **§2 — the comment's laundered number** | **GREEN.** One line, same commit |
| 3 | **§5 — `main` into the branch, re-gate** | **GREEN**, before the check |
| 4 | **§5 — the amendment's "quoted in the report" clause** | **GREEN.** One clause in [`ROADMAP.md`](../ROADMAP.md) |
| 5 | **PR #35, PR #34** | **AMBER — unchanged. Neither is re-cut and neither is reverted** |

**PATRICK'S CHECKS — still the same three, plus one question, one app session:**

> 1. **PR #34** — *"With the second floor hidden, does a wall you draw still
>    jump to something you cannot see?"*
> 2. **PR #35** — a wall you believe is straight must say nothing about its
>    angle; a wall you believe is crooked must not claim an exact cardinal.
> 3. **One line for the record** — is the status-bar label what you asked for?
> 4. **§4's question** — heading, or deviation from axis?

## 7. ITEM C

[`0065`](0065-ruling.md) §6 said `0065` was my last ruling before it. **This one
exists because Patrick said "0067 is up" — his instruction, which
`ca3c6b7` now states in the tree outranks a ruling, including mine about my own
order.** That is the amendment working, not an excuse, **and it does not extend
to a fifth naming.**

**`0066` stays reserved. It is the next thing I write, ahead of any ruling on
whatever answers this one.** Nothing in §6 above is mine to build, and I have
ordered no new work of my own here.
