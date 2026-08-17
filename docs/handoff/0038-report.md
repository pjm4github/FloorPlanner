# 0038 — report: §2's diagnosis does not hold — `_sync_floor_state()` already runs on load

**Per [`0037-ruling.md`](0037-ruling.md) §4 item 1 — "confirm §2 by inspection…
two lines, no fixture needed."** It is two lines, and they say the opposite of
what §2 concluded. GREEN, measurement only, per §6.

**Housekeeping first: [`0036-ruling.md`](0036-ruling.md) and this session's own
[`0036-report.md`](0036-report.md) are two different files sharing one
number** — a genuine collision, not a typo. Both are already committed and
cited elsewhere (this report, `SESSION_SNAPSHOT.md`, `handoff/README.md`), so
neither is renamed; renumbering after the fact would break more links than it
fixes. **Numbering continues forward from here** (this report is `0038`); if
it recurs, worth naming as its own finding later, not fixed retroactively now.

---

## 1. §2's CLAIM, AND THE LINE THAT REFUTES IT

§2 quoted `planio.py:236` (`set_floor_state(active=self.active_floor)`,
inside `apply_project_to_scene`, the LEGACY-format path) as evidence that "the
load path sets the active floor and nothing else," and concluded
`apply_floor_visibility` — reachable only through `_sync_floor_state()` — never
runs on load.

**`apply_project_to_scene` is not the path a v5 file takes.** `open_document`
(`planio.py:95-118`) calls `apply_design_to_scene` for any
`format == "floorplanner-design"` document — every real file this app writes
today. And `apply_design_to_scene` (`floorplanner/design/bridge.py:1265-1266`):

```python
if win is not None:
    win._sync_floor_state()
```

**This call has been there since 2026‑07‑26** (`git blame`, commit `2678ff5`)
— three weeks before Patrick's report, present the whole time. `win` is the
real `MainWindow` on every UI-driven open (`bridge.py:1079`:
`scene, win = (target, None) if isinstance(target, QGraphicsScene) else
(target.scene, target)` — `open_document` passes `self`, so `win is target`,
never `None`). **`_sync_floor_state()` sets `active`, `reference` AND
`show_others` together, then calls `apply_floor_visibility`** — exactly the
"complete recompute" §5 rules a fix must do. It already does it.

## 2. MEASURED ON PATRICK'S OWN PLAN, NOT INFERRED FROM READING

`fixtures/incoming/crossfloor-snap-2026-08-17.json`, loaded headless through
`MainWindow.open_document()` — the real method the UI calls, not a bypass:

```
default show_other_floors on a fresh MainWindow: False
AFTER load: show_others = False   active = default
of 45 upper walls:   visible=0   enabled=0
of 106 default walls: visible=106 enabled=106
```

**Correct in every particular**: the upper floor is fully hidden and
untouchable; the default floor is fully visible and interactive. A second run
with `show_other_floors` deliberately pre-set to `True` before the load
(simulating state carried over from a prior document in the same session) is
also correct — ghost mode, ALL 45 upper walls `visible=True, enabled=False`:
paints gray, cannot be grabbed. **Neither run reproduces anything Patrick
described.**

## 3. WHAT THIS DOES AND DOES NOT SETTLE

**Does not settle**: whether Patrick's actual symptom is real — only that the
specific mechanism §2 named is not its cause. `_sync_floor_state()`'s own
docstring says it is "called on init, load, and floor ops"; on THIS load path
it is telling the truth.

**Reopens [`0036-ruling.md`](0036-ruling.md) §3's own discriminator**, never
run: *does the saved document change across the gesture?* That test still
needs what neither ruling nor the intake file states — **`crossfloor-snap-2026-08-17.json`
has no `.txt` companion note**, so neither of `0036` §4's two questions (was
`show_others` on when it happened; did the wall stay moved after release) has
an answer on record. Per the intake's own standing rule, an untriaged file
gets named with its age in every handoff that passes through here: **it has
sat one handoff so far (this one), not yet two.**

**Does not touch**: `0035-ruling.md` §2's hypothesis A (a query path with no
floor filter) — genuinely unexamined here, and still the live hypothesis if
geometry turns out to have moved. The narrowed census `0037` §3 describes (Qt
-reachability paths, not `.floor`-filtered ones) is real work still owed if
the document diff shows a move.

## 4. WHY THIS IS WORTH LANDING EVEN THOUGH IT ANSWERS "NOT THIS"

**A wrong diagnosis, ruled on and left standing, is worse than one caught in
the same session.** §5 minted a general rule — *a derived property manually
re-applied is not derived, it is a cache; enumerate the writers of
`_FLOOR_STATE` and show each re-applies* — on the strength of a claim that
turns out not to hold for the path most files take. The rule may still be
worth keeping (see §5 below), but the instance it was built on was not real.

## 5. ONE THING §5'S RULE STILL GETS RIGHT, MEASURED SEPARATELY

`set_floor_state`'s bare form (no `_sync_floor_state` wrapper) IS called
directly at three sites — `levels.py:50` (inside `_sync_floor_state` itself,
not a bug), `planio.py:236` (`apply_project_to_scene`, legacy path — but that
function also calls `_sync_floor_state()` itself at `planio.py:313`, later in
the same method, so it too self-corrects), and `design/bridge.py:1134` (a
priming call inside `apply_design_to_scene`, ALSO followed by the real
`_sync_floor_state()` call at line 1265 later in the same function). **All
three bare calls are followed, in the same function, by the complete one.**
§5's enumeration is worth doing properly at some point — a fourth call site
that primes without a later full sync would be exactly this bug — but none of
the three found here is that case.

## Gate

No code changed. `python -m ruff check .` clean (nothing touched). No test
added — this is a read plus a live probe against an existing fixture, not a
new assertion; a regression test for "load fully syncs floor state" is a
reasonable follow-up if this line of investigation is picked back up, not
built here since the report is answering "is this the cause," not "build the
fix."
