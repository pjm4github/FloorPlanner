---
# permanent key, independent of GitHub
id: 68
title: "The 3D view renders every level, not the active floor"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: 2026-08-11
closed_by: null
rank: 69
related: [11, 67, 50]
state_source: report
github_issue: null
---

# D68 — The 3D view renders every level, not the active floor

## The report and the want

**Reported 2026‑08‑11:** the 3D view renders **every level** regardless of which
one the user is editing. **Wanted: the active floor only, by default.**

## The site is exact, and the parameter already exists

`build_model(doc, levels=None, furnishings=True, …)` — **`levels` has been a
parameter all along**, and both CLI entry points already pass it:

| call site | passes `levels` |
|---|---|
| `fp3d.py:899` — the `fp3d` CLI | **yes**, `levels=a.level` (`--level`) |
| `fp3dq.py:348` — the Qt Quick 3D CLI | **yes**, `levels=a.level` |
| **`MainWindow.show_3d_view`** — the in-app popup | **NO — `build_model(doc)`, no argument at all** |

**So this was not a missing capability; it was one call site not using it.**

**A CORRECTION TO THIS RECORD'S FIRST DRAFT:** it named `fp3d.py:824` as the
offending site. That line is inside a **docstring example**, not a live call. The
real one is `MainWindow.show_3d_view`. The record is corrected rather than
rewritten, because a record that quietly fixes its own citation teaches nobody.

**`active_floor` is VIEW STATE** (kept out of `serialize()` so a floor switch is
neither undoable nor dirtying), so the popup must read it from the window, not
from the document.

## THE BOUNDARY THIS SETTLES — a build_model parameter, not a view filter

> **A toggle that changes WHICH GEOMETRY EXISTS is a `build_model` parameter. A
> toggle that changes what is DRAWN from geometry already built is view-side.**

**Floor scope is the first kind.** Recorded in
[`../../floorplanner/viewer/VIEWER_NOTES.md`](../../floorplanner/viewer/VIEWER_NOTES.md)
§1 beside the seam it protects, because **there are two renderers and both import
`build_model` unchanged** — a filter written into either shell would scope one
renderer and not the other. `furnishings=False` is the established precedent.

## Reachability

**Both viewers were unreachable from the UI until D53** — `show_3d_view` had two
call sites, both blank-canvas right-clicks, and on a plan that fills the canvas
it could not be opened at all. It has a View menu entry now, which is what makes
this defect meetable by a user in the first place.

## THE FIX, AND WHAT IT REMOVES

`show_3d_view` passes the active floor. **Two traps are handled at the site:**

1. **The floor is read from the WINDOW, not from `doc`** — `active_floor` is
   deliberately view state, kept out of `serialize()` so a floor switch is
   neither undoable nor dirtying, so the document does not carry it. Looking
   there is the wrong path a fixer would take.
2. **THE ID IS NOT THE NAME.** `build_model(levels=…)` filters by level **id**
   (`L1`, `L2`); `active_floor` is the level **name** (`default`, `second`).
   Passing the name straight through matches nothing and renders an **empty
   model** with a note nobody reads — **a silent blank window, worse than the
   defect**. The mapping is done at the call site and a floor with no matching
   level falls back to the whole document rather than to nothing.

### It removes a reachable capability, and that is acceptable HERE and only here

**Rendering all floors at once was reachable and now is not**, until
[D69](0069-an-auxiliary-control-panel-on-the-3d-view.md)'s panel restores the
choice. **This is not the parasitic-reach mistake being made deliberately, and
the difference is that the capability was BROKEN.**

**D11's z collapse means every floor currently renders at ONE HEIGHT.** "See the
whole building" has never actually worked — it produced a pile, not a building.
**What is removed is a misleading view, not a working one.** The
parasitic-reach rule exists to make you budget for what rests on a fault; what
rested on this one was an image that lied.

**And the escape exists meanwhile:** the `fp3d` and `fp3dq` CLIs keep `--level`
and can still render everything, for anyone who needs it before the panel lands.

**Receipt:** `test_the_3d_view_renders_only_the_active_floor` asserts the
**resolved ids**, so it fails both ways — if the filter is dropped (every level)
and if it is wrong (none). **Fail-first, mutation verified:** dropping the filter
makes it fail; restored, it passes.

## Ruling

*(Closed 2026‑08‑11 — completed.)* Fixed rather than deferred, on the reviewer's
ruling that one argument is not worth a record's overhead to carry. The active
floor is the **default**; D69's panel is how a user asks for more.
