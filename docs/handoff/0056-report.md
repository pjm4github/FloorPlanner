# 0056 — report: the orthogonality report (item B), built — item C untouched

**Per [`0055-ruling.md`](0055-ruling.md) §4 — item B only, as instructed.**

---

## 1. WHAT WAS BUILT

**`floorplanner/design/validate.py`**, sibling to the existing room `report(d)`:

- `wall_angle_deviation_deg(a, b)` — degrees off the nearest axis-aligned
  angle, `[0, 45]`. A wall exactly on axis reads `0.0`; a perfect 45° bay
  and a join-artifact drift at the same angle read identically — this
  measures WHAT the geometry is, not WHY, matching `0055` §5's own refusal
  to settle that question.
- `wall_orthogonality(d)` — per-wall `(wall_id, level, type, deg)`, worst
  first. Skips a wall with a missing or coincident vertex pair (already an
  I2/I3 violation elsewhere) — this is a report about **valid** walls that
  are not quite straight, not a second copy of `check()`.
- `ORTHOGONALITY_BANDS` / `orthogonality_bands(rows)` — `0055` §2's own five
  bands (`>5°`, `1-5°`, `0.1-1°`, `0.01-0.1°`, `<0.01°`), zero-filled even
  when a band is empty. **Labels are ASCII** (`"> 5 deg"`, not `"> 5°"`) —
  the suite's console is cp1252, and a label that can appear inside an
  assertion diff must not be able to crash the failure message reporting it.

**Two surfaces, matching `0055`'s own "check() report or a menu item" —
built both, since the ruling asked for both:**

1. **`tools/validate_design.py`** (the corpus-census surface — `0055` §2's
   "nobody knows how many plans have this"): prints the band summary and up
   to 8 worst offenders after the existing room table.
2. **Edit ▸ "Wall orthogonality report…"** (the interactive surface —
   `"Chief complains about my walls"`): a new `OrthogonalityReportDialog` in
   `dialogs.py`, sibling to `GapReviewDialog`. Lists every wall over 0.01°,
   with a summary line. **No button changes a wall's angle** — item C is
   unruled and this dialog does not pre-empt it.

## 2. CROSS-CHECKED AGAINST THE RULING'S OWN NUMBERS, NOT JUST WRITTEN TO PASS

`0055` §2 states measured corpus figures from its own (uncommitted) probe:
*"`planc1.v5.json` carries 6 walls at 0.0666°; `symmetricP1.json` carries
2."* `tests/test_orthogonality.py::test_the_corpus_receipt_matches_0055s_own_measurement`
runs this implementation against both files and gets **6** and **2**,
matching — a second, independent instrument agreeing with the first, not
one restating the other's assertion.

**One thing NOT claimed as a match:** `0055`'s own line-level DXF counts
(494/134 lines) don't correspond 1:1 to a per-wall count — a DXF face pair
plus opening symbol lines multiplies one wall into several line entities.
This report operates on FloorPlanner's own wall list directly, which is a
different, arguably more useful, population than the exported drawing's
lines. Flagging the difference rather than letting the two numbers look
like they should agree and quietly not.

## 3. TESTS — 17, including the corpus receipt and both controls

`tests/test_orthogonality.py`: axis/diagonal table (0° and 45° together,
per the positive-control-for-zero rule — an instrument that always reports
0 can't be told apart from a broken one without a non-zero case beside it),
a small-drift case, a degenerate-wall case (reads 0, does not raise), a
direction-symmetry case, sort-order + missing-vertex-skip, an
all-axis negative control, band zero-fill, band bucketing, the two corpus
receipts above, and two dialog smoke tests (off-axis wall listed; clean
plan reports "axis-aligned"). `python -m ruff check .` clean. Full gate:
`collected=778 ruff=clean vacuous=0 end_assign=0 snapshot=current`;
OFF/ON/DEEP `771 passed, 7 deselected`; GREEN.

## 4. WHAT WAS NOT TOUCHED

**Item C (the repair) — not built, not authorised.** `0055` §4 is explicit:
*"C IS NOT AUTHORISED HERE... it needs its own ruling with the tolerance
argued, and B's census is the input to that argument."* Nothing here snaps,
moves, or rewrites a wall's angle. Grid snap (item A) is also untouched —
`0055` left it as already ruled, with one additional read-back clause
(does snapping cover an operation's output, or only cursor input) still
owed before that item starts.

## 5. TIER

**GREEN**, per `0055-ruling.md` §6 — pushed without a stop, per the
autonomy policy.
