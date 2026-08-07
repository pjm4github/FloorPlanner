---
# permanent key, independent of GitHub
id: 50
title: "A level's elevation is DESTROYED by a load/save round trip"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-07
closed: null
closed_by: null
rank: 51
related: []
state_source: row
github_issue: null
---

# D50 — A level's elevation is DESTROYED by a load/save round trip

## Symptom

Every level of every plan reports `elevation_in 0.0` and `height_in 96.0`, and a
non-zero value already present in a file does not survive being opened and saved.

Measured 2026-08-07 with the viewer's own reader, which is the reason this was
found at all:

    python floorplanner/viewer/fp3d.py <plan> --list-levels

    examples/farmplaceBIGmultifloor.json   L1 default  elev 0.0"  height 96.0"
                                           L2 second   elev 0.0"  height 96.0"
    a 3-floor plan built by the app        L1 Ground / L2 Upper / L3 Attic
                                           all elev 0.0"  height 96.0"
    the six other v5 examples              one level each, elev 0.0" height 96.0"

## Mechanism

**`model.Floor` has two fields — `name` and `reference`.** There is no elevation
anywhere in the editor's floor model, so there is nothing for a writer to read.
All three writers therefore emit literals:

    floorplanner/design/bridge.py:796     the scene walk
    floorplanner/design/bridge.py:976     the detect path
    floorplanner/design/importer.py:184   legacy import

**THE SCHEMA IS NOT AT FAULT.** `level` already carries `elevation_in` and
`height_in`; the document format has expressed this since v5 was vendored at
P0.7. The gap is entirely on the editor side of the bridge.

## Evidence

**The fault is DESTRUCTION, not absence — which is the F5 family, and the reason
this is a defect rather than an unbuilt feature.** `farmplaceBIGmultifloor.json`
L2 was hand-set to a real elevation and taken through `MainWindow.load_path` →
`save_path`:

    IN : [('default', 0.0, 96.0), ('second', 108.0, 108.0)]
    OUT: [('default', 0.0, 96.0), ('second',   0.0,  96.0)]

A file that already states a storey height loses it by being opened. Nothing
reports the loss: `check()` is clean either way, because a level with elevation
0.0 is perfectly valid.

Full measurement: `docs/evidence/viewer-floors-levels.txt`.

## Ruling

**The viewer is CORRECT and is not to be changed.** `fp3d` stacks levels by
`elevation_in`; every value it is given is 0.0, so every level renders at the
same height. That is the viewer faithfully rendering what the document says.

**A `--stack` flag is REFUSED** (2026-08-07). A rendering flag that invents a
number the document does not contain is a decision about the MODEL wearing a
renderer's clothes — and the moment elevations are real, the flag becomes a way
to disagree with them. `--explode` stays legitimate but waits: there is nothing
to space out until this record closes.

**This blocks Phase 7's Build Floor**, which must produce exactly this field. A
feature that creates storeys cannot be built on a model with no storey height.

## Receipt

*(Open.)* **Tier AMBER.** Acceptance is a `--list-levels` comparison across a
load/save round trip: set a level's `elevation_in` and `height_in`, open the
plan, save it, and read the levels back — the values must be the ones that went
in. The measurement above is the failing half of exactly that test.
