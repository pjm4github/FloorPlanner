---
# permanent key, independent of GitHub
id: 83
title: "Macro recording does not capture the tool already selected before recording started"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-09-02
closed: null
closed_by: null
rank: 83
related: []
state_source: row
github_issue: null
---

# D83 — macro recording does not capture the tool already selected before recording started

**Filed per Patrick's own report, 2026‑09‑02, in chat (not a numbered
ruling — noted for later per his own words: "Make a note of that and we
can come back to it later").**

## The finding

Patrick's own words: *"There is an issue with the start of the macro that
doesn't capture the first state of the selection (if I select a tool
prior to starting the macro, then start clicking on the canvas, the
current state isn't captured)."*

`MacroRecorderDialog.start()` (`macro.py`) begins recording from a blank
slate — it does not emit the CURRENT tool (`win.tool`) as the macro's
first token. `on_tool()` only records a tool CODE when `set_tool()` is
actually called WHILE recording is active (a transition), so a tool
already active at `start()` time is invisible to the recorded text. A
macro recorded this way replays starting in whatever the RUNNER's own
default tool is, not the tool the user was actually working in when they
began recording — so the first clicks after `start()` are interpreted
under the wrong tool on replay.

## Site

`floorplanner/macro.py`: `MacroRecorderDialog.start()` and `on_tool()`
(class starting ~line 640, `_TOOL_CODES` table). The fix is presumably to
emit `_TOOL_CODES[win.tool]` as the first recorded token inside `start()`
itself, mirroring how a fresh macro RUN implicitly begins in Select but a
RECORDING should capture whatever state it actually began in.

## Not investigated yet

No root-cause read beyond locating `start()`/`on_tool()`; no fix
attempted. Held per Patrick's own instruction ("we can come back to it
later") — not scheduled against any tranche.
