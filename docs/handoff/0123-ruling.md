# 0123 — ruling: `0121`/`0122` accepted clean — tranche 2 is authorised to start

**On [`0121-report.md`](0121-report.md) and [`0122-report.md`](0122-report.md).**

## 1. ACCEPTED, SPOT-CHECKED

`cluster_stations` / `_rounded_stations` / `_door_symbol` / `Sheet.warnings`
all exist where claimed; **D81 and D82 carry `state: closed` with Patrick's
merge instruction quoted** ([`0069`](0069-report.md) §4's rule, satisfied);
the telescoping census reconciles (964 → 856, per-file numbers stated).

**And the one finding I came to write is already closed:** transcribing the
door vocabulary into `fp2pdf.py` makes a **third copy** (config, `_paint_door`,
`_door_symbol`) — the D73 shape — **and `tests/test_fp2pdf.py:307` already
asserts the copy against `config.DOOR_TYPES`' full vocabulary.** The drift
guard was built without being asked. Nothing owed.

**The naive-vs-fixed telescoping contrast** (10+10+10=30 ≠ 31 vs 10+11+10=31)
is a differential proven by arithmetic rather than revert — the
[`0080`](0080-report.md) §1 class, correctly labelled.

## 2. `0122`'s CONFIRMED-NOT-RE-DIAGNOSED — sustained

Patrick's 45° observation lands exactly on [`0119`](0119-ruling.md) §1's
measured gap. **Matching a new complaint to an existing record instead of
minting a fresh diagnosis is the record system paying for itself.**

## 3. TRANCHE 2 — START

Both prerequisites merged. Order stands, nothing re-ruled:

1. **`dim_row_along` refactor** ([`0119`](0119-ruling.md) §3) — **GREEN**,
   receipts are the existing dimension tests unchanged plus the telescoping
   census re-run identical.
2. **The room-driven angled lane** ([`0120`](0120-ruling.md) §2) — **AMBER,
   own branch.** Check as [`0120`](0120-ruling.md) §4 wrote it: dimensions ON
   for Wiscaway's 45° rooms → one readable lane with walls **and doors** in
   it; one room OFF → its edges leave the lane.

**Carried:** the `L2.dxf` Chief recount (item C's last line — Chief will be
open for the 45° check anyway; **do both in one sitting**), the two latent
delta-snap sites, D61-family.
