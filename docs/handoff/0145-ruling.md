# 0145 — ruling: roof visibility/editability ruled as R2c; clip display as R3b; the macro notes on the record

**Patrick, 2026‑09‑02.** Reconciled against the tree as ordered: R1/R2 merged,
R2b on PR #50 (CI green, AMBER), D83/D84 filed — **and no visibility/
editability requirement exists anywhere in the committed record yet**
(measured: no such code, doc, or TODO on `main` or the PR branch). His
message is therefore the authoritative capture, quoted into this file.

---

## 1. MACRO NOTES — both filed, one question now answered

* **D83** (recording misses the tool selected before Start) — his restatement
  matches the filed record. **Held for later, his word.**
* **D84** was filed as "needs his own clarification." **He has now given it:**
  *"it uses 'ROOM' instead of 'R'. that is a holdover from an earlier version
  of the code."* — D84 reclassifies task→defect, his quote in the record,
  target key `"R"`. **Still held for later with D83; no build now.**

## 2. R2c — TWO SWITCHES IN THE ROOF MENU, RULED FROM HIS WORDS

Two checkable items, **in the Roof menu by themselves**: **Show roof** and
**Edit roof**, with the invariant **Edit ⇒ Show** (checking Edit checks Show;
unchecking Show unchecks Edit). Three states, exhaustive:

| state | render | input |
|---|---|---|
| hidden | roof absent from paint AND hit-testing — *"invisible… cant be touched"* | all to floor tools |
| shown, not editable | rendered, fully inert | **every mouse/key event reaches the floor tools exactly as if no roof existed** — the pass-through is total, his words: *"All mouse and keys activities are bypassed"* |
| shown + editable | rendered | **the roof system captures the canvas input**; floor items stay visible but not editable |

The roof sketch tools and marker only operate with Edit on (menu tools
disabled otherwise); **sketching the first ridge via the menu turns both
switches on** rather than silently drawing into a hidden layer. The switch
state **persists per document** (the workflow he describes — off most of the
time after design, toggled on to "see how it fits" — is per-plan state, the
`show_dimensions` precedent). **Receipt is a differential:** the same click
on a ridge selects the wall under it with Edit off and the ridge with Edit
on; hidden, the roof appears in no hit census at all.

## 3. R3b — THE CLIP LINE, after R3's plane geometry

*"When a room is 'clipped' by the roof… affected walls should show a dotted
line where any part of the roof is clipping the full height of the room
underneath."* This needs the roof-plane z over each wall run — geometry R3
builds anyway — so it lands as **R3b, its own gated tranche after R3**:
along each wall, the sub-span where plane height < the room's full wall-top
height draws dotted in plan. AMBER; his check on the 45° wing, where the
clip is real.

## 4. ORDER

R2b (PR #50) → **R2c** → R3 → **R3b** → R4 (owns held items 3/4) → R5.
One at a time stands. **PR #50 still waits on your own word, Patrick — the
drag/recompute check specifically**; "the macro recording looks good" is
recorded, but the snapshot shows that check unconfirmed and I will not read
approval into it.

**Carried:** room-label rounding ([`0131`](0131-ruling.md) §2); delta-snap
sites; D61-family; yard items; ridge/eaves repositioning (R4).
