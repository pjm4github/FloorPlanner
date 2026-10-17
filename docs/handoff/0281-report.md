# 0281 — report: PR #94 merged on his word — Ctrl+Z ten times faster; nothing open on a branch

**Landed:** PR #94 · 1a0d5cf · 2026-10-17 · AMBER · checked by Patrick in the app: "undo works now, land #94"

**Code, 2026‑10‑17.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0280`](0280-report.md) kept the roofs' compose and clip traces by value
across the reload an undo is, on `undo-fast` (PR #94). His check:

> *"undo works now, land #94"*

Done as said: the branch landed on `main` at **`1a0d5cf`**, fast-forward
(one commit on `main`'s tip); [PR #94](https://github.com/pjm4github/FloorPlanner/pull/94)
MERGED; the branch deleted, local and remote.

## 1. WHAT LANDED

* Undo and redo reuse the roofs' compose and clip traces when the
  restored roofs are the same (by their values, not their objects): on his
  R1 plan, Ctrl+Z 3.6 s → 0.34 s, redo 1.7 s → 0.34 s.

## 2. THE DRAG-SPEED RUN, IN ONE PLACE

[`0275`](0275-report.md) measured it (3 fps on a drag, a roof's clip
trace recomputed in every paint); [`0276`](0276-report.md) cached the
traces and the wall dashes and found the settle walk re-arming itself
idle; [`0277`](0277-report.md) fixed the garage roof's dead knob;
[`0279`](0279-report.md) held the rooms through a drag and switched to
repainting only what changed, after an audit of every item's box and a
screen-staleness probe; [`0280`](0280-report.md) made undo fast. All on
`main` (PRs #91–#94). **Nothing is open on a branch.**

Named, not ordered: undo by command (P6.b — the reload and the two walks
that remain of an undo); DXF export of annotations; his backlog (0248's
items 8 and 9).

**Carried:** unchanged from [`0280`](0280-report.md).
