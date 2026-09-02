# 0147 — report: R2b merged, D84 reclassified, R2c starting

**Code, 2026‑09‑02, answering [`0145`](0145-ruling.md) and
[`0146`](0146-ruling.md).**

---

## 1. R2b MERGED

[PR #50](https://github.com/pjm4github/FloorPlanner/pull/50) merged to
`main`, branch `roofs-r2b-end-on-marker` deleted (local and remote), per
[`0146`](0146-ruling.md)'s explicit authorization following Patrick's own
check: *"Yes the R H P looks fine."* **R2b is done.**

## 2. D84 RECLASSIFIED

Per [`0145`](0145-ruling.md) §1: Patrick's restatement — *"it uses 'ROOM'
instead of 'R'. that is a holdover from an earlier version of the
code"* — is the literal intent, not the preliminary "by design" read
[D84](../defects/0084-the-room-tool-records-a-verbose-room-name-x-y.md)
originally recorded. Reclassified `type:task` → `type:defect`, his quote
added to the record, **target key `"R"`** noted. **Still held for later
alongside D83, no build authorized** — [`0146`](0146-ruling.md)'s own
words: *"D83/D84 held."*

## 3. R2c — NEXT, BUILDING NOW

Per [`0145`](0145-ruling.md) §2 / [`0146`](0146-ruling.md): two checkable
switches in the Roof menu, **Show roof** and **Edit roof**, invariant
**Edit ⇒ Show**. Three states:

| state | render | input |
|---|---|---|
| hidden | absent from paint AND hit-testing | all to floor tools |
| shown, not editable | rendered, inert | every mouse/key event passes through to the floor tools as if no roof existed |
| shown + editable | rendered | the roof system captures canvas input; floor items stay visible, not editable |

Sketching the first ridge via the Roof menu turns both switches on. The
switch state persists per document (the `show_dimensions` precedent).
Receipt: a differential — the same click on a ridge selects the wall
under it with Edit off, the ridge with Edit on; hidden, the roof appears
in no hit census at all.

**AMBER tier, one gated tranche, R2c alone** — no R3/R3b/R4/R5 work starts
before this one's own check, per [`0145`](0145-ruling.md) §4's order:
R2b → **R2c** → R3 → R3b → R4 → R5.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
ridge/eaves horizontal repositioning (R4).
