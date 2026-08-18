# 0060 — report: the band split, re-run; and 0037 §3's census, folded in

**On [`0059-ruling.md`](0059-ruling.md) §5's order: item 1 (the band split and
re-run), then item 3 (the cross-floor investigation, §4's comparison folded
in for free). Item 2 (item C's ruling) is explicitly Patrick's and not
attempted here.**

---

## 1. THE BAND SPLIT — the headline now reproduces from the printed table

`ORTHOGONALITY_BANDS`'s bottom band (`(0.0, 0.01, "< 0.01 deg")`, which
matched both `deg == 0.0` and `0.0 < deg <= 0.01`) is split into two, exactly
as `0059` §2 specified:

```
(0.01, 0.1,  "0.01-0.1 deg")
(0.0,  0.01, "0 < dev < 0.01 deg")     # exclusive of zero
(None, None, "on axis")                # deg == 0.0 exactly, matched separately
```

`orthogonality_bands()` now checks `deg == 0.0` first (routed to `"on axis"`)
before falling through to the range loop, which skips the sentinel row.
`tests/test_orthogonality.py`'s band-bucketing test updated to the new
labels; `pytest -m walls` (non-gui) — 15 passed.

**Also fixed, found while re-running both printers**: the new, longer label
(`"0 < dev < 0.01 deg"`, 19 chars) overflowed both consumers' hardcoded
column widths and ran into its neighbour — `docs/evidence/orthogonality_census.py`'s
per-plan table header and rows, and `tools/validate_design.py`'s single
design report. Both now size their column width from the longest label in
`ORTHOGONALITY_BANDS` rather than a fixed constant, so a future band-label
change can't silently misalign the table again.

**Re-run, full corpus, 16 files (8 skipped, same 8, same reasons as
`0058`):**

```
file                                              walls   >5   1-5  0.1-1 0.01-0.1  0<d<0.01  on axis
examples/farmplaceBIGmultifloor.json                109     1    5     3       1        0        99
examples/fiveRoomTest.json                           16     0    0     0       0        0        16
examples/planc1.v5.json                              83     0    0     0       2        4        77
examples/planc1TestV5.json                           82     0    0     0       2        4        76
examples/roundedMultifloor.json                     122     0    0     0       0        0       122
examples/sample_plan.v5.json                         10     0    0     0       0        0        10
examples/site_demo.json                              14     0    0     0       0        0        14
examples/symmetricP1.json                            79     0    0     0       2        0        77
fixtures/chief-export/sample_design.json             20     0    0     0       0        0        20
fixtures/d74-wall-decoration.json                     5     0    0     0       0        0         5
fixtures/fragment2room.json                          12     0    0     0       0        0        12
fixtures/incoming/crossfloor-snap-2026-08-17.json   151    36    8    21      12        4        70
fixtures/prism-check.json                             4     0    0     0       0        0         4
fixtures/shower-glance-check.json                     4     0    0     0       0        0         4
fixtures/wiscaway2026-08-08.json                    103     2    0     0       0        0       101
fixtures/wiscaway2026-08-09R.json                   134    53    1     8       0        0        72

TOTAL                                               948    92   14    32      19       12       779
```

`32 + 19 + 12 = 63` — **the table now produces its own headline.** No other
totals moved (`92`/`14`/`32` unchanged from `0058`; `779` is the old `791`
minus the `12` now broken out).

## 2. THE COMPARISON — `0059` §4, run: the two plans do not cleanly separate

`0059` §4 asked, unranked, whether the crossfloor plan's off-axis severity is
evidence for the cross-floor bug or just an artifact of it being the most
heavily edited plan in the corpus — "the separating measurement is cheap:
compare its off-axis rate against `wiscaway2026-08-09R`."

Run directly against `wall_orthogonality`/`orthogonality_bands` (not
estimated):

| | walls | off-axis (nonzero) | rate | **> 5° (the band `0059` called out)** | rate |
|---|---:|---:|---:|---:|---:|
| `crossfloor-snap-2026-08-17.json` | 151 | 81 | 53.6% | 36 | 23.8% |
| `wiscaway2026-08-09R.json` | 134 | 62 | 46.3% | **53** | **39.6%** |

**This corrects `0058`'s own framing, not just answers `0059`'s question.**
`0058` §1 called the crossfloor plan's 36 walls over 5° *"the highest count
in the corpus by a wide margin."* It is not: `wiscaway2026-08-09R` has 53 —
more, in both raw count and rate — despite carrying no reported cross-floor
symptom. On the specific metric `0059` flagged as the standout, **the plan
without the bug is worse than the plan with it.**

On overall off-axis rate the two are closer (53.6% vs 46.3%) but the
crossfloor plan is still the higher of the two, not matching — so even the
weaker, whole-corpus reading does not show the clean match `0059` §4
anticipated ("46% — the same rate").

**Answer to `0059` §4, stated plainly: the measurement does not separate the
two hypotheses, and where it points, it points away from the bug.** A plan
with no reported cross-floor symptom (`wiscaway2026-08-09R`) drifts *worse*
on the exact axis (`> 5°`) that made the crossfloor plan look like the
outlier. That is consistent with "both are simply large, heavily-edited
plans, and drift tracks edit history broadly" and inconsistent with
"off-axis severity is a symptom of the cross-floor bug." Two files is not a
census — this is a measurement, not a closing — but it does mean
orthogonality severity should not be treated as corroborating evidence for
`0037`'s open thread.

## 3. `0037` §3's CENSUS — every mouse/macro reachability path trusts Qt state, none check `.floor`

`0037` §3 asks for the paths that reach an item by Qt reachability (selection,
hit-testing, `items(pos)`, `collidingItems`, the drag's own pick) rather than
by `.floor`, given `0037` §2's finding that `apply_floor_visibility` has one
call site and a load leaves `show_others` stale.

**Every user-facing hit-test and selection path shares one root, and it does
not filter by `.floor`:**

| site | what it does | filters by `.floor`? |
|---|---|---|
| `items.py:1276` `hit_candidates()` | `scene.items(scene_pos)` — the shared candidate list every hit-test below is built on | **no** |
| `view.py:305` `PlanView.hit()` | 1×1-pixel viewport `items(pos)` + priority pick | no (inherits) |
| `view.py:309` `blank()` | `not self.items(pos)` | no (inherits) |
| `view.py:336` `_band_may_start()` | calls `hit()` | no (inherits) |
| `view.py:538` rubber-band select | `scene.items(area, IntersectsItemShape)` | **no** |
| `view.py:244` `_align_to_wall()` | `for w in sc.items(): ...` while drawing, to snap a new wall's free end | **no** |
| `macro.py:407` `_opening()` | `scene.items(pt)` filtered to `WallItem` | **no** |
| `macro.py:450` `_cmd_select()` | `hit_target(...)` then a second `items(pt)` scan | no (inherits) |
| `walls.py` (`nearest_wall_endpoint`, `nearest_wall_body`, `_compute_wall_junctions`, weld/coalesce) | the geometry hot paths | **yes, consistently** (`it.floor == active`) |
| `bridge.py:1266` `apply_design_to_scene` | calls `win._sync_floor_state()` | confirms `SESSION_SNAPSHOT.md`'s standing finding still holds |

**Not a reproduced bug — `0037` §6 scopes inspection to GREEN, a fix to
AMBER, and no fix is built here.** Currently masked: `apply_floor_visibility`
does run on load (`bridge.py:1266`), so today every non-active-floor item
genuinely is disabled by the time a user can click. The gap is structural,
in `0037` §5's own words: *"a derived property that must be manually
re-applied is not derived — it is cached, and every cache needs an
invalidation rule."* `hit_candidates()` and its callers are exactly that —
consumers of the Qt enabled/visible cache with **zero independent `.floor`
check** of their own, versus 100% of `walls.py`'s geometry hot paths, which
check `.floor` directly rather than trusting the cache. Any future write
path that touches an item without going through `_sync_floor_state` first —
a paste, `extract_room`/`join_room`, a macro-created item mid-script — would
leak a non-active-floor item into selection, a click hit-test, or
`_align_to_wall`'s snap target with nothing to catch it.

## 4. WHAT REMAINS, NAMED RATHER THAN ATTEMPTED

- **Item C's ruling** — still Patrick's, still RED, `0059` says so explicitly
  and it is not touched here.
- **`0036` §3's document diff on Patrick's own submitted plan** — `0037` §4
  item 2, still blocked on the two facts no ruling has yet captured (was
  `show_others` on; did the wall stay moved after release). Not run — outside
  what `0059` §5 ordered for this pass.
- **Hardening `hit_candidates()`/`items(pos)` with an explicit `.floor`
  check** is a fix to behaviour, AMBER per `0037` §6 — named as the shape a
  future fix would take, not built.

## 5. TIER

**GREEN — measurement and a documentation/formatting correction only.**
`0059` §5 item 1 (band split + re-run) and item 3 / `0037` §6 (reachability
census + the rate comparison) are both `GREEN, measurement only` by their own
rulings' tiers.
