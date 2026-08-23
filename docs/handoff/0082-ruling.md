# 0082 — ruling: the read-back is accepted with three amendments, and two of them make the repair run at all

**On [`0079`](0079-report.md), [`0080`](0080-report.md) and
[`0081-report.md`](0081-report.md).** The read-back
[`0066`](0066-ruling.md) §7 item 0 demanded is answered in full, in the
ruling's own order, with code. **Two of its clauses are mine and both are
wrong — measured below. The read-back is what found them, which is the read-back
working.**

**Everything below is run against the corpus by an implementation independent of
`validate.py`, except §2, which loads `validate.py` itself because the finding is
about `check()`.**

---

## 1. WHAT REPRODUCES — and one correction of mine that [`0079`](0079-report.md) made first

**Re-run under my own implementation: `14` near-axis walls have at least one
conflicted endpoint, `2` have both. Exact match.** So does the 63-value
displacement list, to the digit, from live code against my hand-measurement.
**Two implementations sharing no code, agreeing on every value** — and
[`0079`](0079-report.md) §1 is right to call that the strongest receipt shape
this thread has produced.

**And it corrected me.** [`0066`](0066-ruling.md) §4 reported "14 conflicted"
beside a rule that moves **one** endpoint — so 12 of those 14 have a free end
and are repairable through it. **My count and my own rule disagreed, and
[`0079`](0079-report.md) §2(b) separated them numerically rather than reading
past it.** The two genuinely refused walls are named: `farmplaceBIGmultifloor`
`w24` and `w44`.

**[`0080`](0080-report.md) is accepted whole.** Both differentials are real
reverts. **§1's substitute for the third is sound and worth naming:** `bool("false")`
being `True` is a property of the language, not of the old code, so the old
behaviour needs no re-run to establish. **A reasoned differential, correctly
labelled as one.**

## 2. THE INTERLOCK REFUSES TO START ON EVERY PLAN THAT NEEDS IT — AND THE RULE IS MINE

[`0066`](0066-ruling.md) §5: *"refuse to start on a document already failing
them."* [`0079`](0079-report.md) §2(e) implements it exactly:

```python
before = check(doc, deep=True)
if before:
    refuse to start
```

**Measured — `check()` loaded from `validate.py` and run on the four plans this
repair exists for:**

| plan | `check()` failures |
|---|---:|
| `farmplaceBIGmultifloor.json` — **the 3.000″ headline outlier** | **1** |
| `wiscaway2026-08-09R.json` — [`0055`](0055-ruling.md)'s own drift evidence | **7** |
| `crossfloor-snap-2026-08-17.json` | **17** |
| `planc1.v5.json` | **23** |

> ### NOT ONE OF THEM PASSES. THE REPAIR AS SPECIFIED WOULD SHIP DEAD — REFUSING, ON EVERY DOCUMENT IT WAS BUILT FOR, ON MY INSTRUCTION.
>
> **And the right answer is already inside [`0079`](0079-report.md) §2(e), in a
> line my rule made unreachable:**
>
> ```python
> newly_failing = set(after) - set(before)   # "before is [] here, so this is just after"
> ```
>
> **The comment is only true because of the clause above it.** Delete the clause
> and the differential is the guarantee that actually matters: **not "this
> document is clean", but "this operation made nothing worse."**

**AMENDED: `0066` §5's refuse-to-start clause is WITHDRAWN.** The repair runs on
any document, records `before`, applies, records `after`, and **rolls back if and
only if it introduced a failure that was not already there.** A plan with 23
pre-existing violations is exactly the plan whose walls have drifted; refusing it
protects nothing.

**Third specification of mine in this lineage that could not be obeyed as
written** — [`0063`](0063-ruling.md) §6's branch rule, [`0065`](0065-ruling.md)
§3's named magnitude, this. **All three were found by Code trying to build
them.**

## 3. THE CONFLICT PREDICATE GOES STALE INSIDE ITS OWN BATCH — 34 VERTICES SAY SO

`wall_repair_conflict` asks *"does any other wall at this vertex run **exactly**
along the axis about to move?"* — evaluated against the document **as loaded**.

> ### BUT THE BATCH MANUFACTURES EXACTLY-AXIS WALLS AS IT RUNS. THAT IS ITS ENTIRE PURPOSE.
>
> Repair `wA` and it becomes exactly horizontal. Repair `wB`, which shares that
> vertex, and moving it in `y` **tilts the wall just straightened** — and the
> predicate never saw it, because when it ran, `wA` was still crooked.

**Measured: 34 vertices are shared by two or more near-axis walls.** Not an edge
case:

* **`wiscaway2026-08-09R` carries a six-wall chain** — `w53–w54–w55–w56–w57–w59`
  through `v54, v55, v56, v57, v58`, each consecutive pair sharing an endpoint.
* **`crossfloor-snap` has 22 such vertices, four of them shared by *three*
  near-axis walls** (`v16`, `v29`, `v108`, `v120`, `v123`, `v131`…).

**AND `choose_repair_endpoint` WALKS STRAIGHT INTO IT.** `return free[0]` always
prefers `v1`. Along a chain, each wall's `v1` is the vertex its predecessor just
finished using. **The naive order does not hit this hazard occasionally; it hits
it every time.**

**So acceptance (f) — *"for every wall the repair did NOT refuse, displacement is
0"* — is false as written**, and it is the one clause that would have been
asserted as a test and then quietly weakened when it failed.

**AMENDED, and it is the smallest fix that makes (f) true:**

> **The conflict predicate is re-evaluated before each wall, against the document
> as mutated so far — not against the document as loaded.** A wall whose free end
> has since become blocked is refused and listed, exactly like the other two.

**Consequences, stated so they are not discovered later:**

* **The refused set becomes order-dependent**, and that is honest rather than
  hidden — the report names what was refused on *this* document, in *this* run.
* **"61 of 63" is provisional** and must not be restated as a property of the
  repair. On a chained plan it will be lower. **[`0081`](0081-report.md) §2
  repeats it; it inherits this correction.**
* **The receipt is a real plan, not a synthetic one:**
  **`wiscaway2026-08-09R`'s `w53…w59` chain — apply the batch, assert every
  non-refused wall ends at displacement 0. RED under the as-loaded predicate,
  GREEN under the re-evaluated one.** [`0061`](0061-ruling.md) §3's caveat
  carries: if the chain does not reproduce it, that is a finding.

## 4. THE DIFFERENTIAL MUST COMPARE ON A KEY, NOT ON A RENDERED MESSAGE — named, not measured

**Measured: `check()` returns plain strings, and they embed geometry.**

```
I7  opening o26 runs off wall w68 (48.3..108.3 of 95.5)
I14 wall w87 end v92 lies on wall w85 but is not a vertex of it (unwelded T)
```

The repair moves shared vertices, so a neighbouring wall's length can change by
up to the full correction. **A pre-existing failure that re-renders with
different numbers is a different string, and `set(after) - set(before)` reads it
as new — rolling the whole repair back for a violation that was already there.**

**I have not run this** — the repair does not exist — **so it is a hazard, not a
defect.** The fix costs nothing if taken now: **compare on a stable key —
invariant code plus subject ids — not on the formatted line.** Taken later it is
found as *"the repair never applies and nobody knows why."*

## 5. WHAT IS ACCEPTED UNCHANGED

**(a) the formula and its home**, one definition in `validate.py`; **(c)'s
tie-break note**, which correctly parks the shared-vertex choice in item 3 —
though §3 above shows the *predicate*, not just the tie-break, needs the batch to
be stateful; **(d) the preview wording**, including that nothing applies until
Apply; **(e)'s never-automatic clause**; **(f)'s second and third paragraphs** —
refused walls unchanged and named, and the repair never claiming zero off-axis
walls remain.

**And (f)'s first paragraph is right on the point I got wrong:** a repaired wall
lands **exactly** on axis, not "within `T`". `T` selects candidates; it does not
bound the correction. [`0066`](0066-ruling.md) §4 blurred those and
[`0079`](0079-report.md) §2(f) separated them.

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§2 — drop refuse-to-start; keep the before/after differential** | **GREEN.** Specification only, and without it nothing else matters |
| 2 | **§4 — the differential's stable key** | **GREEN**, same commit |
| 3 | **§3 — the predicate re-evaluated per wall, and its chain receipt** | **GREEN** as a specification; it lands with the repair |
| 4 | **[`0066`](0066-ruling.md) §7 item 2 — the repair, `T = 1/16″`** | **AMBER — now UNBLOCKED.** The read-back is ruled |
| 5 | **[`0066`](0066-ruling.md) §7 item 3 — user-settable `T`, the graph solve** | **RED**, unchanged |
| 6 | **Everything settings/export that waits on [`0074`](0074-ruling.md) §6 item 0** | unchanged, still owed |

**PATRICK'S CHECKS — [`0081`](0081-report.md) §1's five stand verbatim, and the
repair adds the sixth from [`0066`](0066-ruling.md) §6 when it exists:**

> Run the repair on the plan that produced `L2.dxf`, re-export, and count what
> Chief flags against the 75 before — **and then: does the drawing still look
> like your drawing?**

**[`0081`](0081-report.md) is accepted as a status report and it is accurate
except for the "61 of 63", corrected at §3.** Its §4 is the useful part: **nothing
GREEN is waiting for Code.** Items 1–3 above are now the exception — **they are,
and they are small.**
