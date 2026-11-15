# 0330 — ruling: the red cabinet test was the TEST's fault, not the product's — fixed in place; re-gate

**Reviewer (Cowork), 2026-11-14.** Patrick relayed that the gate is red on a
cabinet test. No report file names it; `.pytest_cache/v/cache/lastfailed`
(written 02:26Z) holds one cabinet entry:
`tests/test_cabinet_item.py::test_drawers_count_is_offered_only_for_an_all_drawer_front`.
**If the red test is a different one, say which, verbatim, in the next number.**

- **Cause, measured:** the test counted drawer fronts by looking for parts
  named exactly `drawer-N`. A room with no style defaults to SHAKER doors, and
  a five-piece drawer front is five parts (`drawer-2-stile-l`, ...). Only the
  short top drawer is a slab, so the count was 1 where the test wanted 3. The
  cabinet was right: it has three drawers. Reproduced in the pure calculator —
  old count 1 (shaker), 3 (slab), 1 (raised).
- **Fix:** the assertion now collects drawer NUMBERS (`{"1", "2", "3"}`),
  whatever the door style. One test file changed; no product code.
- **This is 0329 §1 doing its job:** that file was flagged "never run". It was
  wrong in one place.
- **Code:** re-gate. Anything else red comes back verbatim, as a report.
