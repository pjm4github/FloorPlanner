# 0079 — report: `0066` item 1 built; the read-back for item 2

**On [`0066-ruling.md`](0066-ruling.md).** §7 item 1 (the displacement
instrument) is built, gated GREEN. §7 item 0 (the read-back) is answered
below — item 2 (the repair itself) is not started; it stays AMBER and
blocked on this being ruled, exactly as ordered.

---

## 1. ITEM 1 — THE DISPLACEMENT INSTRUMENT, BUILT

`floorplanner/design/validate.py` gains `wall_orthogonality_displacement_in(deg,
length_in)` — `length_in * sin(radians(deg))`, the distance a wall's free
end moves if straightened onto its nearest axis. `wall_orthogonality()`'s
return shape becomes `(wall_id, level, type, deg, displacement_in)`; every
consumer updated (`dialogs.py`'s Edit ▸ report now prints both numbers per
wall, `tools/validate_design.py`'s worst-offenders table gains a column,
`docs/evidence/orthogonality_census.py` gains a sorted displacement
printout).

**Cross-checked against `0066` §1's own four-row table and §2's own 63-value
sorted list — exact match, to the value:**

```
Their implied displacement (inches, sorted):
  0.0004 0.0008 0.0008 0.0016 0.0016 0.0016 0.0028 0.0028 0.0030 0.0030
  0.0031 0.0034 0.0055 0.0057 0.0057 0.0064 0.0075 0.0131 0.0131 0.0132
  0.0142 0.0146 0.0158 0.0201 0.0273 0.0314 0.0320 0.0320 0.0320 0.0355
  0.0393 0.0409 0.0631 0.0779 0.1145 0.1334 0.1371 0.1489 0.1489 0.1636
  0.1752 0.1900 0.1936 0.2218 0.2680 0.2680 0.2680 0.3409 0.4066 0.4066
  0.4668 0.4816 0.5271 0.6970 0.8064 0.9978 1.0000 1.0000 1.0192 1.0192
  1.5807 1.7184 3.0000
```

**Two implementations, one arriving from hand-measurement of the drawing
and one from live code, agreeing on all 63 values** — the strongest form of
receipt this thread has produced for a formula. (Corpus total is 960 walls,
not `0066`'s 960 — the two `w7off*` fixtures `0071` promoted account for the
difference from `0060`'s 948.)

**Receipt:** `tests/test_orthogonality.py`, the four-row table reproduced as
a parametrized test, plus a zero-on-axis control. Every existing consumer's
tuple-unpacking updated (one, `orthogonality_bands()`, would have raised
`ValueError` outright on a 5-tuple — caught before it shipped, not after).
Full suite (757 passed, `not gui and not slow`; 55 passed, `gui`), `ruff`
clean, full gate GREEN.

## 2. THE READ-BACK — item 2's six clauses, in `0066` §7's own order

### (a) The displacement formula and where it lives

Done in §1 above — `wall_orthogonality_displacement_in()`, beside
`wall_orthogonality()`, `floorplanner/design/validate.py`. One definition;
the repair, the preview, and the census all call it, none restate it.

### (b) The conflict predicate, as code

```python
def wall_repair_conflict(d, wall_id, endpoint_attr):
    """True if straightening `wall_id` by moving its `endpoint_attr`
    ('v1' or 'v2') would tilt another wall sharing that vertex.

    Straightening a near-horizontal wall changes only the moved
    endpoint's y (set equal to the other endpoint's y); a near-vertical
    wall, only x. So the conflict is exact: does any OTHER wall at that
    same vertex already run EXACTLY along the axis about to move?
    Moving y tilts an exactly-horizontal neighbour; moving x tilts an
    exactly-vertical one -- 0066-ruling.md sec4's own words, as a
    predicate."""
    V = {v["id"]: (v["x"], v["y"]) for v in d["vertices"]}
    w = next(x for x in d["walls"] if x["id"] == wall_id)
    a, b = V[w["v1"]], V[w["v2"]]
    dx, dy = b[0] - a[0], b[1] - a[1]
    moving_y = abs(dy) <= abs(dx)          # near-horizontal: y is the free coord
    vid = w[endpoint_attr]
    for other in d["walls"]:
        if other["id"] == wall_id or vid not in (other["v1"], other["v2"]):
            continue
        oa, ob = V[other["v1"]], V[other["v2"]]
        if moving_y and oa[1] == ob[1] and oa[0] != ob[0]:
            return True                     # an exactly-horizontal neighbour
        if not moving_y and oa[0] == ob[0] and oa[1] != ob[1]:
            return True                     # an exactly-vertical neighbour
    return False
```

**Measured against the corpus, and a distinction `0066` §4 states but does
not separate numerically:** run over all 63 near-axis walls' two candidate
endpoints, **14 have at least one conflicted endpoint — matching `0066`
§4's own count exactly.** Of those 14, only **2 have BOTH endpoints
conflicted** (fully refused, unrepairable this way); the other **12 have
exactly one free endpoint** and are still repaired through it, just without
a choice of which end moves. **So the practical count for this first
delivery is 61 of 63 repaired, 2 refused** — not 14 refused, which `0066`
§4's own sentence could be read as. **The two, named:** `farmplaceBIGmultifloor.json`
`w24` (0.9290°, 3.000″ — `0066` §1's own headline example) and `w44`
(0.0288°, 0.1145″).

### (c) Which endpoint moves, and why

```python
def choose_repair_endpoint(d, wall_id):
    """'v1', 'v2', or None (both ends conflict -- the whole wall is
    refused). The endpoint with NO conflict; if both are free, either --
    for an isolated wall the displacement is identical either way (moving
    v1's y to match v2's, or v2's to match v1's, moves the SAME distance).
    The tie-break only has teeth once a vertex is shared by more than one
    near-axis wall in the same batch, which is item 3's graph-solve, not
    this first delivery -- stated now so it needs no re-deriving there."""
    free = [a for a in ("v1", "v2") if not wall_repair_conflict(d, wall_id, a)]
    if not free:
        return None
    return free[0]
```

A wall with `choose_repair_endpoint(...) is None` is **refused**, listed,
and left untouched — same as a wall whose one free endpoint exists but the
resulting displacement it produces still gets applied (there is no second
refusal condition beyond conflict; `T` bounds which walls are CANDIDATES in
the first place, not whether a candidate is skipped).

### (d) The preview's exact wording

**Edit ▸ "Repair wall orthogonality…"** opens the existing report dialog's
sibling. Before Apply:

> **N wall(s) will be straightened** (largest correction: **X.XXX″**).
> **M wall(s) are refused** — both ends are shared with an already-exactly-
> axis wall — and are listed below, unchanged.
>
> Nothing is applied until you choose **Apply**.

List, one line per wall, split into two groups:

> `L1: wall w17 (interior) — will move 1.019″`
> `L1: wall w22 (interior) — refused (both ends conflict with an exactly-axis wall)`

After Apply, the status bar (matching `refresh_rooms_cmd`'s own convention):

> `Wall orthogonality repaired — N wall(s) straightened, M refused.`

### (e) The interlock's before/after check list

```python
before = check(doc, deep=True)
if before:
    refuse to start; report:
    "N invariant(s) already fail on this document -- the repair does not
     run on top of a plan that is already invalid. Fix those first."
    return

# ... apply the repair: for each eligible wall, move its chosen endpoint's
# vertex to the straightened position (one Vertex.relocated_to call per
# moved endpoint, P3.3's own shared-movement primitive -- so a vertex
# shared by an UNRELATED, already-orthogonal wall that is not itself
# near-axis still carries correctly, the same guarantee every other
# operation gets from moving vertices rather than rebinding coordinates)

after = check(doc, deep=True)
newly_failing = set(after) - set(before)     # before is [] here, so this is just `after`
if newly_failing:
    roll back the whole operation (discard the scene mutation entirely,
    nothing committed, nothing on the undo stack); report:
    "the repair would have introduced N new invariant violation(s) --
     nothing was changed."
    return

# else: let the normal settle/commit cycle capture this as ONE undo step,
# exactly as every other command already does (mainwindow.py's own
# `_commit_if_changed` -- no special-casing needed, the repair just must
# not force an intermediate commit between individual wall fixes)
```

**Never automatic** (`0066` §5): reachable only from this one menu item,
never from open, save, export, or any other operation's own settle path.

### (f) The acceptance, restated as `0066` §4's inequality, not zero

> **For every wall the repair did NOT refuse: after applying it,
> `wall_orthogonality_displacement_in(...)` is `0`.** (Straightening sets
> the moved coordinate exactly equal to the other endpoint's — not "under
> `T`", exactly on axis, because the repair is not the thing bounded by
> `T`; `T` decides which walls are *candidates* in the first place, per
> §3.)
>
> **For every wall the repair DID refuse: its displacement is unchanged
> from before the repair ran**, and it is named in the report.
>
> **The repair never claims zero off-axis walls remain.** A rectilinear
> loop whose runs do not sum to zero has a residual that must land
> somewhere (`0066` §4); refused walls are exactly where it lands, by
> construction, and the acceptance says so rather than promising a count
> the vertex graph cannot deliver on this first delivery.

## 3. WHAT IS STILL NOT STARTED

- **Item 2 itself** — the code above is a specification, not a diff.
  Nothing in `mainwindow.py`/`dialogs.py` implements the repair; it is
  AMBER and stays blocked until this read-back is ruled.
- **Item 3** — a user-settable `T`, and the real graph solve for the 14
  conflicted walls. Named, not attempted, per `0066` §7's own scoping.
- **`0066` §6's own receipt** — Patrick's Chief-complaint plan (`L2.dxf`'s
  source), before/after off-axis count in Chief. Cannot be produced until
  item 2 exists and Patrick runs it.

## 4. TIER

**§1: GREEN, done.** **§2 (this read-back): answered, RED-until-ruled per
`0066` §7's own table — item 2 does not start on this report alone.**
