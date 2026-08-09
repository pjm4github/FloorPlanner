---
# permanent key, independent of GitHub
id: 57
title: "face_at hands _walls_of a report of the WRONG SHAPE, so naming a room CRASHES the app"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 58
related: [25, 53]
state_source: report
github_issue: null
---

# D57 — `face_at` hands `_walls_of` a report of the wrong shape, and naming a room crashes

## Symptom

Reported 2026‑08‑08 by Patrick, against his own plan
(`fixtures/wiscaway2026-08-08.json`):

> delete the "Kitchen" room name, then select the room name tool, then left
> click on the enclosed space that was the kitchen

**The application dies. No dialog, no message, no traceback.**

## Mechanism

**Captured, not inferred** — `faulthandler` plus a `sys.excepthook` writing to a
flushed file, because the abort outruns stdout:

    File "floorplanner/view.py", line 419, in mousePressEvent
        res = detect_room(self.scene(), sp)
    File "floorplanner/rooms.py", line 51, in detect_room
        edges = face_at(scene, anchor, floor)
    File "floorplanner/design/bridge.py", line 970, in face_at
        walls = _walls_of(items, lid, nid, vt, defaultdict(int), src,
                          weld_check=False)
    File "floorplanner/design/bridge.py", line 589, in _walls_of
        rep["openings_failed"].append(
    AttributeError: 'int' object has no attribute 'append'

**`_walls_of` requires a report whose values are a LIST and a SET.**
`design_from_scene` builds exactly that (`bridge.py:789`), with a comment
explaining why both exist:

    "openings_failed": [], "openings_failed_ids": set()

**`face_at` passes `defaultdict(int)`** (`bridge.py:970`), so
`rep["openings_failed"]` is the integer `0` and `.append` raises. The sibling
line `rep["openings_failed_ids"].add(oid)` is broken the same way and would
raise next.

**AND THE ABORT IS WHY IT LOOKS LIKE A SEGFAULT.** PyQt6 terminates the process
on an unhandled Python exception inside a virtual override, so the traceback is
lost and the user sees the app vanish. Headless, with `sys.excepthook`
replaced, the same run survives and prints — which is the only reason this was
readable at all.

### Why it needs a malformed opening to fire

The broken line is inside `if straddles:` — the branch for an opening no wall
segment can hold. **A clean plan never reaches it**, which is why this has sat
in the tree unexercised. This plan reaches it because of the I7 below.

## Evidence

### The trigger: a 48″ door 44″ past the end of a 72″ wall

`fixtures/wiscaway2026-08-08.json` fails `check(deep=True)` with exactly one
error, and it is the trigger:

    I7  opening o29 runs off wall w90 (68.0..116.0 of 72.0)

Measured from the document:

| | |
|---|---|
| `w90` | interior, `v89`(1428, 660) → `v90`(1428, 732), **72.0″** |
| `w91` | `v90`(1428, 732) → `v91`(1428, 870), **138.0″** — collinear, and **shares `v90`** |
| `o29` | `door`, `POCKET`, code `4880` = **48″ wide**, anchored `from v1` at **67.999″** |
| so it occupies | y **728.0 … 776.0** |
| which is | **4.0″ on `w90`, 44.0″ on `w91`** |

**The door straddles a welded junction.** It was placed on what is geometrically
a continuous 210″ run at x=1428, which is now two walls meeting at `v90`. Both
belong to room `Util`, whose placement state is **floating**.

This is [D25](0025-a-gesture-can-create-a-door-straddles.md)'s family — *"a
gesture can create a door-straddles-junction scene state that the document can
only represent as…"* — which was **closed at P4.1b** with a gesture-time
message. This plan carries an instance anyway, so either the plan predates that
closure or a path reaches the state without the message. **Not diagnosed here**;
recorded so the question is on disk rather than assumed either way.

### It is PRE-EXISTING — and it refutes the prediction staked against it

The prediction was that this would **not** reproduce on `main`, on the theory
that an unnamed room's label rect is degenerate and therefore unclickable.
**Refuted, and plainly:**

| tree | result |
|---|---|
| branch `8a6751d` | crashes, `bridge.py:589` |
| `main` `bcffa08` | **crashes, identically** |
| `a1172be` (before D47/A1 landed at all) | **crashes, identically** |

Same file, same line, same exception on all three. Two reasons the label theory
could not apply: the room is **deleted**, not renamed — there is no room to
click — and the Room tool's naming route is handled in
`PlanView.mousePressEvent` **before any hit test**, so `shape()` never
participates.

**Three further hypotheses are refuted by the same trace**, and are recorded
because ruling them out was the point of taking it: it is not the label
graphics item's lifetime, not room-identity across a re-derivation, and not a
name-keyed lookup breaking on an empty string. It is also **not** the
`"None OR a room"` clause — that clause is on the *right*-click path and was
deleted at `8a6751d`, while this is a *left*-click and crashes on trees that
never had it.

**A related measurement, taken while confirming the above:** a room's name
**cannot be emptied through any UI route**. `RoomItem._rename` guards
`if ok and name.strip():` and `RoomPropertiesDialog.apply` guards `if name:`,
and the schema rejects `""` outright (`'' should be non-empty`). So "delete the
room name" is **delete the room** — the room menu's *Delete room*, which calls
`clear_walls()` then `removeItem(self)` and leaves the walls standing. That is
what makes the enclosed space nameable again, and it is the first step of the
repro.

## Ruling

*(Open — cause identified, nothing changed.)*

**Fix at the cause, and reuse one definition.** The report shape is currently
written out at `bridge.py:789` and got a second, wrong spelling at `:970`. A
`try/except` around the append, or coercing the value at the append site, would
leave the second definition in place to drift again — the disease this project
has named repeatedly. **Extract the report initialiser and have both call sites
use it**, so `face_at` cannot be handed a shape `_walls_of` does not accept.

**Two things the fix must not quietly do.** `face_at` currently *discards* its
report, so a straddling opening on the detection path will now be recorded and
then thrown away; whether detection should surface it is a separate decision.
And the underlying I7 in the plan is **not** fixed by any of this — the door is
still 44″ off its wall, and `check(deep)` will still say so.

**A receipt that a silent abort can pass through is not a receipt.** The
acceptance below therefore asserts the gesture *completes*, not merely that a
test does not fail: with the process aborting, a test that never runs its
assertions can look like a pass.

## WHICH INVARIANT I7 IS, AND WHETHER A BOUNDARY CHECK WOULD HAVE CAUGHT IT

**Asked directly, answered by measurement, and the answer is yes — with a
detail that makes it stronger than expected.**

    check(deep=True)  -> ['I7  opening o29 runs off wall w90 (68.0..116.0 of 72.0)']
    check(deep=False) -> ['I7  opening o29 runs off wall w90 (68.0..116.0 of 72.0)']

**I7 IS ONE OF THE CHEAP TWELVE, not one of the deep three.** (`validate.check`'s
own docstring: deep-only is I5b, I11, I14; always-on is I1–I10, I12, I13.)

So a document-boundary check would have surfaced this **before the user ever
reached the crash** — and it would **not have needed the deep set to do it**.
That is the part worth having: [D49](0049-i11-overlapping-placed-rooms-the-corruption-this.md)
is framed around running the DEEP set at load and save, and the cost objection
to it has always been the O(n²) sweep. **This instance is caught by the cheap
half**, which the O(n²) argument does not touch at all.

**This is direct, measured evidence for D49, and it is not a preference.** The
chain is: the plan was saved carrying an I7 → nothing said so → the fault sat in
the file → the user later clicked to name a room → the app died with no message.
A check at the save boundary breaks that chain at its first link, and a check at
the load boundary breaks it at the second. Recorded here and cited from D49 so
the argument lives with its evidence.

**What it does NOT establish**, because the boundary matters: it says a boundary
check would have *reported* this fault. It does not say the user would have
acted on the report, and it says nothing about the deep three, whose cost
argument is untouched by this instance.

## Receipt

**FIXED, 2026‑08‑08.** One definition: `_new_walk_report()` in `bridge.py`, used
by `design_from_scene` and by `face_at`. No `try/except` at the append — that was
forbidden and would have been wrong anyway, since it silences the crash and
leaves two spellings free to drift.

**FAIL-FIRST, on a plan that actually reaches `if straddles:`.** Three synthetic
constructions were tried first and **all three failed to reach the branch** —
`rebuild_all_walls` re-seats the opening, so a hand-built straddler does not
survive to the walk. Building one directly would have built the *symptom*. The
test therefore loads `fixtures/wiscaway2026-08-08.json`, which has the *cause*:

| | |
|---|---|
| before the fix | `AttributeError: 'int' object has no attribute 'append'`, with `rep = defaultdict(int, {'segments': 91, 'openings_failed': 0})` in the traceback |
| after | **2 passed** |

**And the precondition earned its keep**: the first draft of the test asserted a
straddler existed, and that assertion **failed** on all three synthetic scenes —
so without it the test would have gone green after the fix while exercising
nothing.

**The reported gesture, end to end** (`docs/evidence/d57-kitchen-crash.txt`):
load the plan, delete `KITCHEN`, Room tool, click the enclosed space →
**completes, and the room is named** — `Kitchen` is back in the room list.
Asserted by the room existing, not by the absence of a failure, because a
process that aborts runs no assertions and can look like a pass.

**`fixtures/wiscaway2026-08-08.json` still fails I7 afterwards** — verified. The
fix is to the crash, not to the plan; laundering the fixture would hide the
trigger.

*(The second half — that `face_at` discards the report it is now correctly
given — is [D58](0058-face-at-discards-the-walk-report-so-a.md), filed and not
fixed here.)*

### Original acceptance, for the record

* the reported gesture — load the plan, delete `KITCHEN`, Room tool, click the
  enclosed space — **completes and names the room**, asserted by the room
  existing afterwards, not by the absence of a failure;
* a test drives it through the real handler with an `excepthook` that records
  rather than aborts, so an abort is a red and not a silent green;
* `_walls_of` receives a report of one shape from both call sites, and that is
  asserted directly;
* `fixtures/wiscaway2026-08-08.json` still fails `I7` afterwards — the fix is to
  the crash, not to the plan, and laundering the fixture would hide the trigger.
