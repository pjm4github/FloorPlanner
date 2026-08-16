---
# permanent key, independent of GitHub
id: 75
title: "A recessed FLOOR feature is not representable -- an accepted limit of the vessel/enclosure split"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:limit
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-15
closed: null
closed_by: null
rank: 75
related: [74]
state_source: measurement
github_issue: null
---

# D75 — A recessed floor feature is not representable

## The limit

**Filed in the same commit as the fix it is a limit OF**, per
[`handoff/0018-ruling.md`](../handoff/0018-ruling.md) §5's own instruction —
*"the limit is stated when the split lands, not discovered later"* — on D44's
precedent.

`build_prism`'s region rule (handoff 0018 §4) now reads:

* **`form == "vessel"`**: a nested annotated region **may recess** — cut into
  the body's own cap, floor-to-rim (a tub's well, a spa's water surface).
* **`form == "enclosure"`**: a nested annotated region is **always a solid
  standing on the floor** — a bench, a stove.

**What this cannot express: a recess IN THE FLOOR of an enclosure** — a shower
pan sunk below the surrounding floor, a floor drain, a sunken threshold. An
enclosure's region rule has exactly one shape (floor-standing solid); there is
no mechanism for a region that goes *down* from the floor rather than *up* from
it.

**No such item exists in the catalog today.** Measured: every `enclosure`
item's regions (`walk_in_shower`'s bench, `sauna`'s heater) are already
correctly floor-standing, and no catalog entry names a sunken feature. This is
therefore an **accepted limit stated in advance**, not a gap discovered by a
failing case — the same shape as D44.

## Why it is a limit and not a gap

**A vessel's recess and an enclosure's sunken-floor feature are the SAME
geometric operation** (cut down from a reference surface) applied at
**different reference surfaces** — the vessel's rim, the enclosure's floor.
Building it would mean giving `enclosure` a THIRD region behaviour
(recess-from-floor, on top of solid-on-floor), which is exactly the kind of
speculative branch this project's channel-shaped and threshold-shaped mistakes
already warn against building **before a real item asks for one**.

## The trigger to reopen

**A catalog item is authored whose region should sink below its enclosure's
floor** — a shower pan, a floor drain, a sunken tub surround drawn as an
`enclosure` rather than a `vessel`. Until then, this stays filed rather than
built.

## Ruling

*(Open — filed 2026‑08‑15, alongside the vessel/enclosure split it limits.)*
**Accepted limit, `type:limit`, D44's precedent.** Not scheduled; reopens on the
trigger above.
