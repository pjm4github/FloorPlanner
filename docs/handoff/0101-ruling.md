# 0101 — ruling: the map is not built, it is discarded — and the seam already exists

**Patrick:** *"Is there a mapping that can be built?"*

**It is already made twice per report and thrown away both times.**
[`0100`](0100-ruling.md) §5's first read-back bullet is answered here so it need
not be re-derived.

---

## 1. THE TWO MAPS, MEASURED

```python
# bridge.py:646   inside design_from_scene's walk over the scene's WallItems
rec = {"id": nid("w"), "level": lid, "v1": v1, "v2": v2, ...}
#      ^ the WallItem and its emitted document id are both in hand, on this line

# canonical.py:63  the geometric renumber
wid = {w["id"]: f"w{i}" for i, w in enumerate(walls, 1)}
#      ^ pre-canonical id -> final id, built, used in place, discarded
```

> ### `WallItem` → `nid("w")` → `wid` → `w19`. **BOTH LINKS ARE COMPUTED ON EVERY REPORT. NEITHER IS RETURNED.**
>
> This is not new machinery and it is not a second id space —
> [`0100`](0100-ruling.md) §1's rule against unifying the two id spaces is
> untouched. **It is a composition of two dictionaries that already exist.**

## 2. THE SEAM IS ALREADY THERE, WITH A PRECEDENT

```python
def design_from_scene(source, floors=None, report=None, strict=False) -> Design:
    """... Pass a dict as `report` to receive the ..."""
```

**`design_from_scene` already takes an out-parameter dict for exactly this kind
of extra information.** The map comes back through it — **no new signature, no
new return type, and the callers that do not ask are unaffected.**

**Canonicalisation must be composed in, not skipped:** the walk's `nid("w")` is
pre-canonical, and the report shows the final id. **A map that stops at the
first link names walls the saved file does not have** — which is the fault
[`0098`](0098-ruling.md) recorded, one link earlier.

## 3. VALIDITY — the part that must be stated, not assumed

**The map is a snapshot of one walk.** Any edit invalidates it: a merge, a
weld, a split, a delete. **It is valid exactly as long as the dialog's own row
list is**, which is [`0100`](0100-ruling.md) §3's dead-reference question, and
the two are answered together or not at all.

**Hold the `WallItem` itself in the row, not its id.** A row that stores a
number has to look it up in a map that may be stale; a row that stores the item
either has a live item or a deleted one, and Qt can be asked which.

## 4. TIER

**GREEN** — this is a finding about existing code, not a change.
[`0100`](0100-ruling.md)'s read-back and tiers stand; this removes one unknown
from it.
