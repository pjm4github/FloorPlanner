# 0132 — ruling: `R2` pair adopted as the tranche's "before" baseline; the re-check re-points at it

**Patrick, 2026‑08‑31:** *"I made some tweaks to the plan wiscaway2026-08-30R2.json
and then exported the pdf and put it in wiscaway2026-08-30R2g.pdf both in
incoming. Those can be used as the 'before' reference where that means
everything before the 131 ruling. I also deleted the png from that incoming
since it is old."*

---

## 1. THE PAIR, MEASURED

`fixtures/incoming/wiscaway2026-08-30R2.json`: **146 walls, 33 rooms, 15 rooms
with `show_dimensions` on, `wall_snap_in: 6.0` in the document's own settings —
and two levels, `L1` + `L2`.** The PDF (`…R2g.pdf`) is its export from the
pre-tranche code.

**The two-level structure is new** — every wiscaway fixture to date was
single-level. The tranche's receipts must not quietly assume one level:
station gathering, family classification, and per-family telescoping all run
per exported sheet, and the receipt should say which level(s) it asserts on.

## 2. DISPOSITION

* **`R2.json` supersedes `R1.json` as the tranche's check file.** The
  [`0129`](0129-ruling.md) §4 / [`0130`](0130-ruling.md) §3 re-check runs on
  the R2 export. `R1` stays where it is — its promoted tests keep running;
  nothing is deleted.
* **`R2g.pdf` is the before-PDF.** When the tranche lands: `R2g.pdf` →
  `docs/evidence/`, `R2.json` promoted out of `incoming/` with the tests that
  name it — same exit-1 path [`0127`](0127-ruling.md) §2 used for `R1`.
* Its document `wall_snap_in` is 6.0, so [`0129`](0129-ruling.md) §3(a)'s
  grid filter must reach that value **by reading the document, not by the
  6.0 default happening to match.** A receipt that passes either way proves
  nothing; assert the read.
* **The deleted `R2f` PNG voids [`0131`](0131-ruling.md) §3's evidence move
  for it** — the record must not point at a missing file. `0131`'s mapping
  stands as analysis; its disposition line is discharged as moot.

## 3. TIER

**GREEN — record only, no new work.** The tranche's build and check are as
[`0129`](0129-ruling.md)/[`0130`](0130-ruling.md) wrote them, now against R2.
PR #45's merge and the three ghost-branch deletions still do not wait.

**Carried:** [`0131`](0131-ruling.md) §2's room-label rounding question
(Patrick, one line); the `L2.dxf` Chief recount; the delta-snap sites;
D61-family.
