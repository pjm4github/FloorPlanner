# 0092 — ruling: the angle clause shows both — heading and deviation

**Patrick, 2026‑08‑23, answering [`0068`](0068-ruling.md) §4:** *"Take option
3."* — **both numbers.** The oldest open question on his side is closed.

---

## 1. THE FORMAT

```
Wall W7: V5(9.00, 32.42)ft -> V8(17.00, 32.42)ft  len 8.00ft  angle 269.0710deg (0.929deg off axis)
```

**ASCII only** — `deg`, not `°`. [`0064`](0064-report.md) §4's reason stands: the
unicode form is unencodable on this project's cp1252 console the moment it
appears in a failing assertion.

**Two numbers, two formats, and the split is the one this project has already
ruled twice:**

| | format | why |
|---|---|---|
| heading | **fixed decimals**, `.4f`, unchanged | an absolute bearing; its useful precision does not scale with its size |
| **deviation** | **significant figures**, `.3g` | a small quantity whose precision is relative — `0.929`, `0.000204`, `1.4e-14` |

[`0075`](0075-ruling.md) §1 rejected significant figures for a coordinate and
[`0073`](0073-ruling.md) §4 kept them for a deviation. **Same rule, third
instance: match the format to whether the quantity's useful precision is
absolute or relative.**

## 2. WHAT THIS RETIRES

[`0068`](0068-ruling.md) §3's false-cardinal cliff **stops being a precision
problem and becomes impossible.**

> A heading can still round to `90.0000` below `0.00005°`. **It is no longer a
> lie, because the clause now also says `(1.4e-05deg off axis)` beside it.**
> **The PAIR is what makes it honest — neither number alone is**, and that is
> the whole reason option 3 beats option 2.

**The receipt is [`0068`](0068-ruling.md) §3's round-trip assertion pointed at
the new number, and it is now satisfiable by construction:**

> **When the clause fires, the printed deviation must not parse as zero.**
> Parse it back out of the label and assert `float(shown) != 0.0`. **A
> significant-figure format cannot fail this for a nonzero value** — which is
> the point. Drive it near the float floor, not at a magnitude a ruling
> supplied ([`0068`](0068-ruling.md) §3's own rule).

**And it settles a disagreement between two surfaces:** Edit ▸ Wall
orthogonality report and `tools/validate_design.py` already speak in deviation.
**The status bar now speaks the same quantity about the same fault.**

## 3. SCOPE

**One format string, its two label tests, and the new round-trip test.** Nothing
else — not the report dialog, not the census, not `wall_orthogonality()`'s
return shape, which already carries both numbers since
[`0079`](0079-report.md) §1.

**Land it on `main` after [`0090`](0090-ruling.md)'s three merges**, not on the
`wall-label-fixes` branch — that branch is checked and merging as it stands.

## 4. TIER

**AMBER** — it changes what the user sees, one week after he checked the label
it changes. **Batch the check with PR #37's**, which is the next one due:

> **Select an off-axis wall. Does the bar tell you both which way it points and
> how far off it is — and does the second number never read zero?**

**Not urgent, not blocking [`0084`](0084-ruling.md) §6.** Slot it wherever it
fits before the next check session.
