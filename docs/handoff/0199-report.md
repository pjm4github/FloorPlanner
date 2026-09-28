# 0199 — report: PR #66 merged on his word; his R6 fixture, promoted; R6.a built — the plan view's multifloor roof rule and the whole-building 3D default; AMBER, stopped for his check

**Code, 2026‑09‑25, on [`0197-ruling.md`](0197-ruling.md) §3–§5.** First the
record, as 0197 §7 has it for every merge: Patrick's check of PR #66
passed — his words, *"yes the new menu is there and the save/reload keeps
the correct setting"* — and on that word `roofs-r6-0-d50` was landed on
`main` at `c1f64f3`, fast-forward, the branch deleted local and remote.
R6.0 is closed; D50 is closed. Then his gesture: *"OK I dropped a new
file in the incoming called 'wiscaway-2level-stacked-floor.json'."* That
file is promoted (§1) and R6.a is built on it (§2): branch
`roofs-r6a-display` off `main` at `c1f64f3`, PR #67 open, gate GREEN,
**stopped for his check** (§4).

## 1. THE FIXTURE — promoted under exit 1, with its census

`fixtures/wiscaway-2level-stacked-floor.json`, frozen as it arrived
(never opened-and-saved), its README row written. **The first
multifloor plan on disk with a roof on more than one level and a
non-zero elevation** — what 0197 §1 measured as absent from all five:

| level | elevation / height | walls | rooms (ceilings) | roofs |
|---|---|---|---|---|
| L1 `default` | 0″ / 96″ | 122 | 27 (96″, 120″) | 2 — ridge along x at y=510 and the 45° wing, both eaves 96″ / ridge 296″ |
| L2 `upper` | **100″ / 196″** | 44 | 9 | 4 — eaves 25″–96″, ridge 179″–235″ |

Schema PASS; **one invariant trips**, `I6 wall w90 sides ['r21'] !=
outline users ['r14', 'r21']` — a wall-to-room binding fault in the
drawing itself, older than this arc, named here and not repaired (the
intake rule: a file is never tidied on the way in). R6.0's receipt holds
on it: L2's 100″ survived his save and this load.

**Coverage, measured** (`roof_covers_floor`, §2): every roof covers rooms
on **both** levels — the L1 roofs run under the upper rooms in plan and
the L2 roofs over the lower ones — except one: **L1's 45° wing roof
covers no upper room.** That one exception is the fail-first control the
tests are built on.

## 2. R6.a — his two answers, built as ruled (0197 §4)

**Plan view.** `apply_roof_visibility` now shows a roof on another level
whenever it **covers this level's rooms**, regardless of "show other
floors" — ghosted, never editable (`paint()` already inks every
non-active floor's roof in `FLOOR_GHOST`; only whether it shows at all
changed). This level's roofs draw solid and editable as before. The
predicate, `roofs.roof_covers_floor(scene, roof, floor)`: the roof's
painted footprint (eaves and overhang) intersects a room on that floor
by more than `_COVER_MIN_IN` on both axes — **R4b's own coverage rule
reused** (`bound_eaves_height` decides which rooms a roof sits on by
the same overlap), so the display rule cannot disagree with the
machinery. The ruling named `roof_clip_spans` as the thing to reuse;
that function is per-wall and same-level, so the room-coverage overlap
is the nearer of the two and is what "which roof covers this room"
already meant in the code. Ghosting style: the roof's own ghost ink,
one line, no new style. The corollary holds by construction: an R3b
dash comes only from a same-level roof, and a same-level roof is always
drawn when roofs are shown.

**3D default.** `MainWindow.show_3d_view` calls `build_model(doc)` with no
`levels=` — the one call site, as ruled. D68's narrowing comment stays
above it as history with the reason it no longer applies; D68's boundary
rule (scope is a `build_model` parameter, never a mesh filter) is
untouched, and `levels=` remains for D69's panel. Nothing in D69 gates
this.

## 3. THE CHECK — receipts

`tests/test_r6a_display.py`, **6 tests** (`walls`), on his fixture: the
roster (L2 at 100″ / 196″) and the roof count per level; the coverage
facts of §1; on the lower plan with "show other floors" off, all four
upper roofs visible and disabled while their floor's own display mode
is `hidden`; on the upper plan the wing that covers nothing **stays
hidden** (the control — before R6.a it was hidden for the same reason,
and it still is) while L1's main roof shows ghosted, and the wing
appears only when ghosting is on; hiding roofs hides the covering
roofs too; and the predicate on a synthetic pair — a roof on `upper`
covering a room on `default`, none on its own floor, and a footprint
that merely grazes a room's edge (0.5″) not counting until it overlaps
by 10″. `tests/test_viewer_popup.py` +1 (`gui`): a spy around the real
`build_model` shows the popup, on a two-floor plan with the upper floor
active, builds with `levels` unset. **One D68-era test is rewritten, not
deleted**: `tests/test_load_path.py`'s
`test_the_3d_view_renders_only_the_active_floor` pinned the narrowing
this tranche removes; it is now
`test_the_3d_view_renders_the_whole_building`, keeping D68's
ids-are-not-names trap (the fixture with distinct ids and names) and
asserting the only filter value that cannot be a mis-mapped one — none.
Every other pre-existing floor, visibility and popup test passes
unmodified.

Full suite **1370 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 4. HIS CHECK

Open `fixtures/wiscaway-2level-stacked-floor.json`. With Floors ▸ "Show
other floors" **off**: on `default`, the four upper roofs draw ghosted
over the lower plan; on `upper`, L1's main roof draws ghosted and the
45° wing does not appear (it covers no upper room); turn ghosting on
and the wing appears. Then the 3D view: both storeys, the upper at
100″, all six roofs. **Two things to know before looking:** the roofs
are not yet composed across levels — an L2 roof and an L1 roof do not
clip each other (R6.b), so where L1's 296″-ridge roofs and the L2 roofs
overlap they interpenetrate in 3D; and L1's roofs have eaves at 96″
under L2's floor at 100″, so his own drawing has the big roofs rising
from the ground storey's wall top through the upper storey — R6.b will
compose exactly that.

## 5. NAMED

* Coverage is re-evaluated when the floor state syncs (a switch, the
  Show/Edit toggles, a roof edit); a room drawn under an upper roof
  after the fact ghosts that roof at the next sync, not the same frame.
* A covering roof is not clickable from the other level; R6.c owns the
  roof tool across levels.
* [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md)'s
  "only multifloor plan" line is still out of date (0197 §1); left for
  when D67 is next touched — which is the reproduction 0197 §5 orders
  before R6.c.

## 6. `fixtures/incoming/`, with ages

`README.md` only — his file left by exit 1 the day it arrived.

## 7. WHAT HAPPENS NEXT

His check (§4). On his word PR #67 merges, branch deleted in the
merge step. Then **R6.b**: composition over all live roofs of the
building in absolute height (0186 §4's principle: a roof's surface is
its level's elevation plus its own heights; the envelope/prune/under-
pass machinery over every live roof, not per level) — his fixture is
exactly the case. Then the D67 reproduction and the roof-elevation
measurement 0197 §5 orders, then R6.c.

**Carried:** unchanged from [`0198`](0198-report.md).
