# 0300 — report: PR #104 merged — the floor dialog derives the base from the floor below

**Landed:** PR #104 · a1fc628 · 2026-11-05 · AMBER · his word "The derived-floor-base branch looks good - you can merge that"; merged by fast-forward

**Code, 2026‑11‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
Orthogonal to the 1½-storey arc (P1–P5); its own branch off `main`.

## 1. WHAT LANDED

`main` fast-forwarded to **`a1fc628`**. His question after P1 (0299), answered and
built: the floor-specification dialog should pick the base from the floor below,
not have it typed.

* **`FloorLevelsDialog` (`dialogs.py`):** a storey sits on the one beneath it, so
  its **base is DERIVED** from the floor below (that floor's elevation + height)
  and shown **read-only**. A **"Sits on the floor below"** checkbox, on by
  default, unticks to a custom base — a basement (a negative base), a split
  level, a deliberate gap. The **lowest floor** has no floor below, so its base
  (the building's datum) stays editable and the checkbox is hidden. One number to
  edit per storey (the height); the base follows.
* **`levels.py`:** `_floor_below_top` computes the floor-below's top (the real
  storey directly below by elevation; a reference floor is not one).
  `set_floor_levels` now **re-derives the stack ABOVE the edited floor** — every
  storey whose base equalled the floor-below's top follows it up, bottom-up by
  elevation — so a lower floor's height change carries the floors above it; a
  floor given a custom base is left in place. The edited floor itself is never
  re-derived (it is what was asked). **No schema change:** stacking is inferred
  from the elevations, so nothing new is stored.

## 2. WHY

The base and the floor-below's top could silently disagree when the base was
hand-typed — the 120-vs-96 ambiguity on his wiscaway file (0299's heads-up; it
turned out L1 was 10 ft, so 120 was right, but the dialog gave no way to see
that). Deriving the base makes the stack gap-free and overlap-free by
construction, which the 3D compose (and P1's storey-above bound) already assume.

## 3. TESTS

`tests/test_levels_elevation.py`: the dialog derives a read-only base and returns
it, the opt-out frees it, the lowest floor keeps an editable base, and a lower
floor's height change carries the stack above while a custom-base floor is not
carried. The existing dialog/undo tests stay green. Full gate GREEN (full mode,
2022 passed).
