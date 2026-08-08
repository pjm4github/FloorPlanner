---
# permanent key, independent of GitHub
id: 54
title: "A room label is sized from its NAME and clips its own area subtitle"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 55
related: [47]
state_source: report
github_issue: null
---

# D54 — A room label is sized from its NAME and clips its own area subtitle

## Symptom

Reported 2026‑08‑08 at the D47 manual check, on the fragment pieces: the labels
overflow their box. `A` renders as `…ft (floati`; the `Overlap` piece shows
`sq ft (floatin` with **no area number visible at all**, and a character bleeds
past the left edge of the neighbouring label.

**An operation whose entire product is new rooms should not produce rooms whose
area is unreadable.** Cosmetic, and explicitly **not blocking** the A1 merge.

## Mechanism

`RoomItem._label_rect()` (`rooms.py:762‑767`) sizes the box from **the name
only**, measured in the 14 px name font:

    w = max(fm.horizontalAdvance(self.name), 48.0) + 10.0

`paint()` then draws **two** strings into that one rect (`:817‑827`): the name
at `AlignTop` in the 14 px font, and a subtitle at `AlignBottom` in the **9 px
sub-font** —

    f"{self.area_sqft:.0f} sq ft" + (" (floating)" if floating else "")

`self._sub_font_metrics` exists and is cached one line above, and is **never
consulted when sizing the rect**. So the box is fitted to the shorter of the two
strings it must hold. `drawText(rect, …)` clips, and `AlignHCenter` centres
first — which is why the overflow is lost from **both ends** and the area number
at the front disappears rather than the tail merely truncating.

## Evidence

Measured 2026‑08‑08 by the same probe as [D53](0053-a-room-cannot-be-selected-by-clicking-its.md),
which reports label metrics alongside the click cases:
`docs/evidence/d53-click-selection-differential.json` (`labels`).

| room | tree | box width | subtitle | subtitle width | **overflow** |
|---|---|---:|---|---:|---:|
| `A` | main | 58.0 | `175 sq ft` | 81.0 | **+23.0** |
| `A` | branch | 58.0 | `175 sq ft (floating)` | 180.0 | **+122.0** |
| `B` | main | 58.0 | `169 sq ft` | 81.0 | **+23.0** |
| `B` | branch | 58.0 | `169 sq ft (floating)` | 180.0 | **+122.0** |
| `Overlap` | main | 108.0 | `81 sq ft` | 72.0 | **−36.0** (fits) |
| `Overlap` | branch | 108.0 | `81 sq ft (floating)` | 171.0 | **+63.0** |

**THE CLIPPING IS PRE-EXISTING, AND A1 IS WHAT MADE IT LEGIBLE AS A BUG.** A
one-character name has always produced a 58 px box, and `175 sq ft` has always
needed 81 — clipped by 23 px on `main` today, on any short-named room. What A1
changed is the *state*, not the label code (`rooms.py` is untouched by the
branch): the pieces are now **floating**, so the ` (floating)` suffix applies
and the overflow goes 23 → **122 px**, and `Overlap` crosses from fitting
(−36) to clipped (+63).

So this is not "A1 broke the labels". It is a latent sizing fault that a correct
change pushed past the point where a reader can no longer reconstruct the
missing text — which is the ordinary way a threshold bug is discovered, and the
reason the numbers are recorded on both trees rather than only the one where it
was noticed.

## Ruling

*(Open — cosmetic, unqueued.)* The fix is to size the rect from **both** strings,
each in its own font:

    w = max(fm.horizontalAdvance(self.name),
            sub_fm.horizontalAdvance(subtitle), 48.0) + 10.0

Two consequences to weigh before doing it, neither of which makes it hard:

* **`_label_rect()` is also the HIT AREA** (`shape()`, `rooms.py:775`), so
  widening the box widens the only part of a room that is clickable. That is
  arguably an improvement, but it is a change to selection behaviour and it
  belongs with [D53](0053-a-room-cannot-be-selected-by-clicking-its.md) rather than
  arriving as a side effect of a text fix.
* **The subtitle is state-dependent** (` (floating)` comes and goes), so the box
  would change width when a room is extracted or joined. Either accept that, or
  size for the widest form the room can take.

## Receipt

*(Open.)* Acceptance: on the fragment product, every piece's area number is
fully visible, and the measured `overflow_px` for all three pieces is **≤ 0**
— the same probe, the same plan, the `labels` block.
