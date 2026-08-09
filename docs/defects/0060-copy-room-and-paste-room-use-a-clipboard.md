---
# permanent key, independent of GitHub
id: 60
title: "Copy room and Paste room use a clipboard Ctrl+V cannot see"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 61
related: [53]
state_source: report
github_issue: null
---

# D60 — Copy room and Paste room use a clipboard `Ctrl+V` cannot see

## Symptom

There are **two clipboards**, and nothing connects them:

| store | written by | read by |
|---|---|---|
| `item_clipboard` | `cut_selected` / `copy_selected` (`Ctrl+X` / `Ctrl+C`) | `paste_clipboard` — **`Edit ▸ Paste`, `Ctrl+V`** |
| `room_clipboard` | the ROOM context menu's *Copy room* (`rooms.py:1270`) | `paste_room` (`mainwindow.py:1582`) — and nothing else |

So **`Ctrl+V` does not paste a room**, and *Copy room* has exactly one partner.
A user who copies a room and presses `Ctrl+V` gets either nothing or the wrong
thing — whatever was last cut or copied as items.

## Mechanism

They are different objects, not two paths to one. `room_clipboard` holds a
**one-room template DOCUMENT** (P4.4), so pasting it is `insert_room_template`
— the same operation as `File ▸ Load template room`, with a clipboard in place
of a file. `item_clipboard` holds a scene-item spec with an offset reference.
`paste_room` produces a **floating** room; `paste_clipboard` reproduces items
where they were, re-grouped.

**Neither is wrong on its own.** The gap is that they present to the user as one
idea — *copy this, paste it* — and behave as two.

## Evidence

Found while censusing the blank-canvas affordances at A1b
(`docs/evidence/d53-blank-canvas-routes.txt`), and **the asymmetry was made
worse by that pass before it was made better**:

* *Copy room* lives on the room's own context menu, which A1b made reachable
  **from the whole region** instead of only the label — so copying got easier.
* *Paste room* lived **only** on the blank-canvas menu, which A1b then stopped
  firing over a room — so pasting got harder, and on a plan filling the canvas
  became unreachable.

A1b closed the reach half by adding `Edit ▸ Paste room` (`Ctrl+Shift+V`), beside
`Paste`. **It deliberately did not merge the two stores.**

## Ruling

*(Open — filed, not answered, and deliberately out of A1b's scope.)*

Whether these should be one clipboard is a **design question about what copy
means in this application**, and it has real content on both sides:

1. **One clipboard, last-write-wins.** `Ctrl+V` pastes whatever was last
   copied, room or items. Simplest to explain; means a room copy silently
   discards an item copy.
2. **Two stores, two keys** — what A1b shipped. Honest about the two operations
   being different, at the cost of a second accelerator to learn.
3. **One clipboard holding a typed payload**, with `Ctrl+V` dispatching on the
   type. Best behaviour, most work, and it has to decide what a mixed
   selection — a room *and* some furnishings — means, which nothing currently
   does.

**(3) is the one that would also close the question A1b left standing**: `Copy
room` copies a room but not the furnishings standing in it, and no record has
ever asked whether it should.

## Receipt

*(Open.)* Acceptance depends on the choice. Common to all three: after copying a
room, **one documented gesture pastes it**, and the app does not silently
present the wrong clipboard's contents.
