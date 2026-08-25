# 0109 — ruling: the walkthrough confirms the arithmetic and CHANGES one of [`0108`](0108-ruling.md)'s refusals

**Patrick's walkthrough:** grid 6″; `V1` at 5′-2½″ → 5′-0″; `V2` at 5′-8″ →
5′-6″; adjoining walls on the shared vertex move too; rooms touching the wall
recalculate.

---

## 1. THE ARITHMETIC IS `wall_snap`, EXACTLY — no new function

```
V1  62.50in -> nearest 6in -> 60.0in = 5ft 0in     ✓
V2  68.00in -> nearest 6in -> 66.0in = 5ft 6in     ✓
```

**Plain nearest-multiple, per coordinate, per endpoint** —
`round(p / step) * step`, which is `wall_snap()` unchanged.
**Confirms [`0108`](0108-ruling.md) §1: this is not the orthogonality repair, and
it needs none of its arithmetic.**

**His example also shows the length changing** — 5.5″ apart before, 6″ after.
**That is [`0108`](0108-ruling.md) §3's opening-runs-off refusal, arriving in his
own worked example.**

## 2. ROOMS RECALCULATE BY CONSTRUCTION — nothing to build

`rooms.py:293`: *"`path` / `area_sqft` / `corners` all **DERIVE** from the
outline (P3.5)"*, and the outline's corners **are** the `Vertex` objects the
walls hold. **Move the vertex and the room follows, with its area, with no code.**

**The one case that will look wrong and is not:** a room that **abuts** the wall
without sharing its vertices — a neighbour on the far face — **does not move, and
should not.** Only rooms that own the corner recalculate.

## 3. THE AMENDMENT — [`0108`](0108-ruling.md) §3's fourth refusal becomes a REPORT

[`0108`](0108-ruling.md) §3 said: **refuse** if any wall's deviation or grid
error increases, citing [`0083`](0083-report.md) §5's 4.679° neighbour.

**His walkthrough says the opposite, and he is right:**

> *"All of the adjoining walls that share the same vertex will also move."*

> ### THAT IS THE INTENT, NOT A HAZARD. He is cleaning a whole plan one wall at a time — a neighbour left temporarily crooked is the NEXT wall he selects, not a defect.
>
> **Refusing on it would block nearly every snap in a legacy plan**, because
> moving one end of a shared corner almost always tilts something that has not
> been cleaned yet. **The rule would make the feature useless on exactly the
> documents it exists for.**

**RULED, and the difference is silence, not movement:**

| | |
|---|---|
| **still REFUSE** | a degenerate (zero-length) wall · an opening running off its wall · a **new** `check()` violation on a stable key |
| **now REPORT, do not refuse** | a neighbour's angle or grid error getting worse — **named in the status line, with the wall, so he can see it and choose** |

**Undo remains one step for the whole action. A silent worsening is still
unacceptable; a visible one is his call.**

## 4. ONE MEASURED THING HE DID NOT ASK ABOUT

**He wrote his example in feet-and-inches. The status bar answers in both, on one
line:**

```
x 91'-10"   y 46'-2"        <- fmt_ftin      (mainwindow.py:721, cursor)
Wall W19: V31(127.00, 55.00)ft   <- fmt_ft2  (mainwindow.py:805, the wall)
```

> **The same quantity, two formats, six inches apart on the same bar.** And a
> 6″ grid reads as `0'-6"` in one and `0.50` in the other — **the first makes
> grid alignment obvious, the second makes it arithmetic.**

**Not changed here.** [`0067`](0067-report.md) §4 records that he **chose** fixed
2 decimals — but that choice was made against significant figures, **not against
the feet-inches format already sitting beside it.** **One line from him settles
it; his own example is the evidence I would cite.**

## 5. TIER

**The amendment: GREEN to record** — [`0108`](0108-ruling.md) is unbuilt, so this
is a specification change, not a rework. **The feature stays AMBER**, still
queued behind PR #37 and PR #38.
