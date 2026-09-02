---
# permanent key, independent of GitHub
id: 84
title: "The Room tool's verbose ROOM token: Patrick reads it as a holdover bug; needs his own clarification"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-09-02
closed: null
closed_by: null
rank: 84
related: []
state_source: row
github_issue: null
---

# D84 — the Room tool records a verbose `ROOM name x y` token; preliminary read says by design, needs Patrick's own clarification

**Filed per Patrick's own report, 2026‑09‑02, in chat (not a numbered
ruling — noted for later per his own words: "Make a note of that and we
can come back to it later").**

## The finding, in his words

*"The room control seems to have a special capability to capture the
state but it uses the wrong macro key, it uses 'ROOM' instead of 'R'.
That is a holdover from an earlier version of the code."*

## Preliminary read — likely not the bug as stated, needs his clarification

`R` (`_TOOL_CODES["R"]`) and `ROOM name x y` are **two different, both
intentional** tokens, not one mistakenly spelled two ways:

* `R` switches the ACTIVE TOOL to Room Name — recorded generically by
  `on_tool()`, the same hook every tool switch goes through (`S`, `E`,
  `I`, `D`, `W`, now `G` for roof ridge).
* `ROOM name x y` (`MacroRecorderDialog.on_room()`, `macro.py` ~line 912)
  is a SEPARATE hook that fires when a room actually gets NAMED — its own
  comment says why it exists: *"room name came from a dialog — capture it
  into a ROOM token"* — because the raw mouse/keyboard event stream the
  recorder otherwise watches cannot see what the user TYPED into that
  modal dialog. Without this hook, a recorded macro would carry the tool
  switch and the click but lose the room's actual name.

So `ROOM name x y` is not standing in for `R` — it is the room-NAMING
action, parallel to how `PLACE`/`DOOR`/`WINDOW`/`WALL` each record their
own action verb distinct from the tool-switch letter that precedes them.

**What is genuinely worth his clarification when we return to this:**
maybe the concern is that the ROOF tool has no equivalent rich token yet
(a sketched ridge + eaves pick + heights currently records as raw
`CLICK`/`DRAG` tokens, unlike a named room) — if so, this is really a
request for a `ROOF ...`-style summarising token, D83's sibling, not a
report that `ROOM` is spelled wrong. Left open rather than guessed at.

## Not investigated further

No code change attempted — Patrick's own instruction was to hold this for
later. This record exists so the discrepancy between his description and
what the code actually does is on record before memory of either fades.
