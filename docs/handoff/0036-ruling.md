# 0036 — ruling: two faults in one sentence, and the one test that separates them

**Patrick, 2026‑08‑17:**

> **The Foyer and Lounge common wall on the Default floor snaps to (or shows a
> bleed through) of the right side of BR2 on the second floor.**

**That sentence contains TWO DIFFERENT FAULTS, and which one it is decides
whether [`0035`](0035-ruling.md)'s census is needed at all.**

---

## 1. SNAP AND BLEED-THROUGH ARE NOT THE SAME DEFECT

| | what it means | where it lives |
|---|---|---|
| **"snaps to"** | a geometry operation **consulted another floor** and **moved the wall** | the query paths and the floor tags — [`0035`](0035-ruling.md) §2 |
| **"bleed through"** | the wall did not move; **the other floor is being DRAWN** | `paint()` and the floor display mode |

**They look identical on screen and they share no code.**

## 2. A NON-ACTIVE FLOOR IS DRAWN BY DESIGN — measured, and it may be the whole answer

```python
def floor_display_mode(floor) -> str:
    """'active' | 'reference' | 'ghost' | 'hidden' for a floor name."""
    if floor == _FLOOR_STATE["active"]:   return "active"
    if floor in _FLOOR_STATE["reference"]: return "reference"
    return "ghost" if _FLOOR_STATE["show_others"] else "hidden"
```

**Four modes, not two.** With `show_others` on, **every non-active floor renders
as a ghost, deliberately**, and `WallItem`, `RoomItem`, `OpeningItem` and the
furnishings each check `floor_display_mode(...) != "active"` before painting
themselves that way.

> ### SO "BLEED THROUGH" MAY BE THE FEATURE WORKING.
>
> If `show_others` was on, BR2's wall **should** be visible. **The defect would
> then not be that it is drawn — it is that a ghost reads as solid enough to be
> mistaken for the active floor.** That is a legibility fault, and its fix is
> contrast, not filtering.
>
> **[D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md) already
> says an inactive floor is "drawn AND draggable" — the DRAWN half is by design.
> Only the draggable half is the defect.** Anyone reading D67 quickly will chase
> the wrong half.

## 3. THE DISCRIMINATOR — ONE TEST, AND IT RUNS FIRST

> ### DOES THE SAVED DOCUMENT CHANGE?
>
> **Save before the gesture, make the gesture, save after, compare the two
> files.**
>
> * **The wall's coordinates MOVED** → it is a real snap.
>   [`0035`](0035-ruling.md) §2's census is on, hypotheses A and B.
> * **The document is UNCHANGED** → nothing snapped. It is **paint**, and the
>   only remaining question is which display mode was set — which is one
>   inspection, not a census.

**This is the project's own instrument, reused:** `ungroup`'s plan-wide
`merge_all` moved scene items 80→78 while the **emitted document was
byte-identical**, which is what established that nothing was ever lost. **The
picture and the document disagree routinely, and the document is the one that
says whether geometry changed.**

**RUN THIS BEFORE THE CENSUS.** The census in [`0035`](0035-ruling.md) is
expensive and enumerates from a property; **this is two saves and a diff, and it
can retire two of the three hypotheses outright.**

## 4. WHAT THE INTAKE NOTE SHOULD SAY

The plan goes to [`fixtures/incoming/`](../../fixtures/incoming/README.md) with a
`.txt` of the same stem. **Patrick's sentence above is most of it.** The two
things it does not yet say, and both are one word:

1. **Was the second floor set to ghost, reference, or hidden** when it happened?
2. **Did the wall STAY moved** — did it look wrong only during the drag, or is it
   wrong now, after release?

**Question 2 is the discriminator in the form Patrick can answer without
saving anything**, and it should be in the note.

## 5. AND IF IT IS PAINT — the fix is not "hide the other floor"

**Ghosting exists so a user can align to the floor below**, which is the whole
point of a reference floor in drafting. **Removing it to fix a legibility
complaint would remove a feature to fix its presentation.**

**The fix would be that a ghost cannot be mistaken for the active floor** —
which is the categorical-channel rule again: *a ghost differing from an active
wall only by lightness is a scalar distinction, and a scalar holds in a
comparison and fails at a glance.*

**Not ruled here** — it is not yet known that this is paint. Stated so that a
paint outcome does not get "fixed" by deleting the ghost.

## 6. TIER AND ORDER

**§3's discriminator: GREEN, measurement only, and it goes FIRST** — ahead of
[`0035`](0035-ruling.md) §2's census, which does not start until the
discriminator says a snap actually occurred.

**Neither displaces [`0033`](0033-report.md)'s check.**
