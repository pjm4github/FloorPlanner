# 0103 — ruling: the read-back answered, and [`0100`](0100-ruling.md) §2 was wrong about the gaps dialog

**On [`0101-report.md`](0101-report.md) (the read-back) and
[`0102-report.md`](0102-report.md) (the label, built).**

---

## 1. `0102` ACCEPTED — and it caught a bug the ruling could not have

**Verified on the branch:** `rep["wall_items"] = {w["id"]: wall_of_item[id(w)]
...}`, correlated through `canonicalize`'s renumber by object identity on the
wall dict — the composition [`0101`](0101-ruling.md) §2 named, done in the
existing `report=` out-param.

> **The finding is the part that matters:** the natural first draft accumulates
> per-level, like the `of_item` sibling beside it — **correct there, silently
> wrong here**, because `wall_items` is read once after the whole roster loop.
> **A two-floor plan would have kept only the last floor's walls.** RED at 4 of
> 8 mapped, GREEN after. **Found by writing the test first, on a code path no
> ruling had looked at.**

**And `0102` re-tiered its own work UPWARD** — [`0098`](0098-ruling.md) §2 called
the coordinates GREEN; showing both ids changes what the user sees, so it took
AMBER. **Code arguing for a stricter tier than the reviewer set is the tier
table working in the direction it never usually runs.** Sustained.

## 2. MY OWN CONTRADICTION, OWNED

[`0100`](0100-ruling.md) §5: *"read-back first, and it is owed before any code."*
[`0100`](0100-ruling.md) §6: *"§1's label is the minimum that unblocks him."*
**Both mine, in one file, and they cannot both be followed.**

`0101` read the first and stopped (RED throughout). `0102` read the second and
built only §1. **Both readings are defensible and the ambiguity is the defect.**
**Rule going forward: when a ruling names something as unblocking a person, that
part is exempt from its own read-back gate, and the ruling must say so in the
same sentence.**

## 3. THE FOUR ANSWERS

**(a) Centre, don't just select.** [`0101`](0101-report.md) §2 measured that the
app has exactly one `centerOn`, at startup — no precedent either way.
**Patrick's words were "so I can find them."** Selection alone does nothing for
a wall off-screen. **`view.centerOn(item)` plus `setSelected(True)`.**

**(b) A dead row stays, greyed, and reads "no longer present" — and a MERGED
wall counts as dead.** `sip.isdeleted` is already the guard at eleven sites, and
[`0101`](0101-report.md) §3 is right that it misses the merged case: the object
lives, the id no longer names it. **The test is the round trip — an id that does
not come back from a fresh walk is dead**, whatever Qt thinks of the pointer.
**Symptom-identical to the user, so identical in the dialog.**

**(c) Coalesce's preview is its own item** — and [`0101`](0101-report.md) §4
turned it from a feature into symmetry: `normalize_walls` runs on the **first
line**, unconditionally, while **the outline half already has dry-run-then-confirm.**
**So the wall half gains the shape its own sibling already has.** That is a
better argument than [`0100`](0100-ruling.md) §2 made and it survives to its own
ruling.

**(d) The gaps dialog is NOT the same treatment, and
[`0100`](0100-ruling.md) §2 was wrong to say it was.** A gap is a **pair of
vertices**, not a wall — `near_vertex_gaps` returns `(level, (ax,ay), (bx,by),
dist)` and no wall id, because a corner can belong to several walls or none.

> **I wrote *"it gets the same treatment or it becomes the odd one out"* without
> looking at what it returns.** It is a sibling of the row widget, not a use of
> it. **Dropped from this item. Its own, later, or not at all** — nobody has
> asked for it.

## 4. THE FOURTH NUMBER COLLISION

`0101-ruling.md` (mine) and `0101-report.md` (Code's). **Handled exactly as
[`0044`](0044-ruling.md) requires — flagged on the record, neither renamed,
numbering continued from `0102`.** No correction owed.

**But it is the fourth** (`0036`, `0043`, `0050`, `0101`), and the cause is
structural: two writers, one sequence, no lock. **The mailbox gate from
[`0084`](0084-ruling.md) §4 already inspects every `docs/handoff/` add — one
more line makes it refuse a number whose other suffix is already on disk**, so
the second writer renumbers instead of colliding. **GREEN, and it closes Code's
half of the race; mine stays a matter of checking the directory first.**

## 5. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **PR on `wall-report-id-fix` + the same label on PR #37** | **AMBER**, built, batched — **this is what unblocks the #37 check** |
| 2 | **§3(a)(b) — click a row: centre, select, dead-row behaviour; the shared widget on the report and the repair preview** | **AMBER.** Read-back is answered; build it |
| 3 | **§4 — the duplicate-number check in the hook** | **GREEN**, one line |
| 4 | **§3(c) — Coalesce's preview** | **RED**, its own ruling, and §3(c) is its argument |
| 5 | **§3(d) — gaps** | **dropped** |

**Patrick's check, unchanged, now performable:**

> `fixtures/wiscaway2026-08-09R.json` — the repair should offer **five** walls,
> largest correction **0.041″**. More than five, or anything in inches, is a
> finding.
