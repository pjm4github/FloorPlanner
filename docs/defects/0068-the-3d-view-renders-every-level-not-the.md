---
# permanent key, independent of GitHub
id: 68
title: "The 3D view renders every level, not the active floor"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
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
| **`fp3d.py:824` — the IN-APP popup** | **NO — `build_model(self.snapshot())`, no argument at all** |

**So this is not a missing capability; it is one call site not using it.** The
fix is to pass the active floor from the app. It is small, and it is filed rather
than done because the reviewer ruled so.

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

## Ruling

*(Open — filed 2026‑08‑11.)* **Filed, not fixed.** Render the active floor **by
default**; the control panel ([D69](0069-an-auxiliary-control-panel-on-the-3d-view.md))
is how a user asks for more.
