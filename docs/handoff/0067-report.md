# 0067 — report: `0065`'s items done; PR #35 open, batched with #34

**On [`0065-ruling.md`](0065-ruling.md).** §2 and §5 (GREEN) landed on `main`.
§3 and §4 (AMBER, same commit as `0065` §7 ordered) are on a new PR,
batched with PR #34's manual check. Numbered `0067`, not `0066` — `0065` §6
reserved that number for item C, which is Patrick's to write, not reported
here.

---

## 1. `0065` §2 — the tier table's authority clause, landed

[`docs/ROADMAP.md`](../ROADMAP.md), right after the GREEN/AMBER/RED table:
*"Patrick's own direct instruction is another [form of authority], and it
outranks a ruling … not a fourth tier."* Commit `ca3c6b7` on `main`, doc-only.

## 2. `0065` §5 — cardinal-suppression coverage extended to all four, landed

`tests/test_selection.py` gained
`test_wall_label_omits_angle_for_all_four_cardinals`, parametrized over
due east/north/west/south, asserting `"angle" not in win.wall_label.text()`
for each — the existing exact-string test only ever exercised due east.
Bundled into `wall-label-fixes` (§3 below) rather than shipped separately,
since it tests the same label the fix touches and AMBER's PR-and-stop
already covers it; nothing was gained by racing it to `main` first.

## 3. `0065` §3/§4 — the two label defects, fixed — [PR #35](https://github.com/pjm4github/FloorPlanner/pull/35), AMBER

**§3, the false-cardinal rounding.** The angle clause fires exactly when
`heading % 90.0 != 0.0` — i.e. only when the wall is NOT on a cardinal — but
printed the value at 1 decimal, so any deviation under 0.05° rounded to a
string reading as an exact cardinal (`"angle 90.0deg"` on a wall the code
had just decided was not at 90°). Now printed at 4 decimals, matching
`tools/validate_design.py`'s own worst-offenders table. New receipt,
matching `0065`'s own named test: `test_the_angle_clause_never_prints_a_cardinal`,
driven by a wall exactly `0.0001°` off vertical (the magnitude `0065` §3
named) — confirmed RED at the old precision, GREEN at the new one.

**§4, `fmt_ft3` → `fmt_ft2`.** Asked Patrick directly, since the significant-
figure format was his own literal instruction ("3 sig digits") and `0065`
had read it as a choice Code made on top of a plainer ask — worth checking
before overriding either way. **Patrick chose fixed 2 decimal places** over
3, or keeping significant figures. `fmt_ft3` renamed `fmt_ft2`, fixed at
`.2f`; every call site and test updated (`148.14 -> "12.34"`,
`1700.04 -> "141.67"`, resolving correctly past the 100ft threshold where
`.3g` degraded to whole feet).

Both in one commit (`c51662b`), per `0065` §7's "same batch, same commit."
Full regression: `pytest tests/test_geometry.py tests/test_selection.py
tests/test_walls.py` — 118 passed. `ruff` clean. Offscreen smoke render
confirming both fixed strings render correctly and stay ASCII (`angle
90.0001deg`, `141.67ft`) before committing, not just trusted. Full gate
GREEN, `collected=799`, branch `wall-label-fixes`.

**AMBER, PR open, stopped — nothing merged.** [PR #35](https://github.com/pjm4github/FloorPlanner/pull/35)
carries the diff and its own test-plan checklist.

## 4. THE THREE CHECKS, BATCHED, PER `0065` §7 — restated so nothing drifts

> 1. **PR #34** — *"With the second floor hidden, does a wall you draw still
>    jump to something you cannot see?"*
> 2. **PR #35, once open** — select a wall you believe is straight and one
>    you believe is not. The straight one must say nothing about its angle;
>    the crooked one must not claim to be at an exact cardinal.
> 3. **One line, for the record only** — the status-bar label as it stands:
>    is it what you asked for? `0065` §2 established the check already
>    happened (you asked for more between `5d85b09` and `cc12bbf`, only
>    possible from the running app); it does not exist on disk until you
>    say so here.

## 5. WHAT REMAINS, UNCHANGED

- **Item C** — Patrick's, `0066` reserved for it, not attempted here.
- **The follow-on hardening pass** — `0062` §3's four masked reachability
  sites, `0063` §5's `wall_endpoint_open(floor=None)` default.
- **Grid snap's read-back**, `0055` §4's extra clause.

## 6. TIER

**GREEN** for §§1–2 above (landed). **AMBER** for §3 (PR #35, open, stopped).
