# 0037 — ruling: a hidden floor that paints is a measurement, and it names a suspect

**Patrick, 2026‑08‑17, completing [`0036`](0036-ruling.md)'s two questions:**

> **The second floor is hidden. Wrong after release. Plus a bleed through of a
> "light gray" color from the second floor (one the first floor snaps).**

**All three answers are decisive, and the third is the one that cracks it.**

---

## 1. LIGHT GRAY IS NOT A GUESS — it is the ghost paint, and it names the state

```python
FLOOR_GHOST = QColor(176, 176, 176)     # flat gray for non-active floors

def floor_display_mode(floor):
    if floor == active:      return "active"
    if floor in reference:   return "reference"
    return "ghost" if _FLOOR_STATE["show_others"] else "hidden"
```

**A hidden floor paints NOTHING. A ghost floor paints flat gray at RGB 176.**
Patrick sees flat light gray.

> ### THEREFORE `_FLOOR_STATE["show_others"]` WAS **TRUE** WHILE PATRICK BELIEVED THE FLOOR WAS HIDDEN.
>
> This is not an inference from a symptom — **the colour IS the state**, because
> only one branch of that function produces it. **The user's belief and the
> runtime cache disagreed**, and everything else follows from that.

**And it also tells us what the items were NOT:** they were not tagged with the
active floor. **A mis-tagged item would have painted normally, not gray** — so
[`0035`](0035-ruling.md) §2's **hypothesis B is refuted for these items** by the
same observation. **The tags are right. The display state was wrong.**

## 2. THE SUSPECT — the load path sets the active floor and nothing else

**Two measurements, and they sit next to each other:**

```
levels.py:50   set_floor_state(active=…, reference=…, show_others=self.show_other_floors)
levels.py:55   apply_floor_visibility(self.scene)

planio.py:236  set_floor_state(active=self.active_floor)          # <- and that is all
```

**`set_floor_state` only updates the arguments it is given** — `reference` and
`show_others` are left holding **whatever the previous document, or the previous
session, put there.**

**And `apply_floor_visibility` has exactly ONE call site in the package,
`levels.py:55`.** The load path does not call it.

> ### SO AFTER A LOAD: the active floor is correct, `show_others` is STALE, and NO ITEM'S visible/enabled FLAGS HAVE BEEN RECOMPUTED.
>
> `apply_floor_visibility` is the only thing that sets
> `it.setVisible(mode != "hidden")` and **`it.setEnabled(mode == "active")`.**
> **If it never runs, items keep the flags they had before the load** — which
> can leave second-floor items both **drawn** and **ENABLED**.
>
> **Enabled is the word that matters.** An enabled item is reachable by a
> gesture, and that is
> [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md)'s
> *"drawn AND draggable"* arriving through the load path rather than the floor
> switch.

**ONE CAUSE, BOTH SYMPTOMS**, which is why it is worth stating before any census
runs.

## 3. WHAT THIS DOES *NOT* YET EXPLAIN — and I am not pretending otherwise

**The three snap helpers still exclude a ghost wall correctly:**
`nearest_wall_endpoint` and `nearest_wall_body` filter `it.floor == active`, and
a second-floor wall fails that test **whatever its visibility flags say.**

**So if the wall genuinely MOVED — and "wrong after release" says it did — a
path that is not one of those three consulted the hidden floor.**
[`0035`](0035-ruling.md) §2's **hypothesis A survives, and the census is still
owed** — but it is now much narrower:

> **Find the path that reaches a wall which is `enabled`, `visible`, and on a
> NON-ACTIVE floor.** Not "every query" — **the ones that filter by Qt state
> (selection, hit-testing, `items(pos)`, `collidingItems`, the drag's own
> pick) rather than by `.floor`.**

**That is the enumeration property**, and it is a different one from
[`0035`](0035-ruling.md)'s: *filters by Qt reachability instead of by floor.*
**A path that trusted `setEnabled` to have been applied is correct code defeated
by §2's missing call.**

## 4. THE ORDER, REVISED

1. **Confirm §2 by inspection** — does a load leave `show_others` stale and
   `apply_floor_visibility` uncalled? **Two lines, no fixture needed.**
2. **[`0036`](0036-ruling.md) §3's document diff, on Patrick's plan** — it is
   still the thing that proves geometry moved rather than merely painted.
3. **The narrowed census in §3**, only for whatever the diff shows actually
   moved.

**§1 and §2 cost nothing and may resolve the bleed-through entirely.**

## 5. TWO RULINGS ON THE FIX, BEFORE ANYONE WRITES IT

**ONE — the load path must recompute floor state COMPLETELY, not partially.**
Setting `active` and leaving `reference`/`show_others` from a previous document
is the defect. **A document's floor display state is part of the document's
state, and a load that restores half of it is worse than one that restores none**
— because half restores silently.

**TWO — `apply_floor_visibility` having ONE call site is the underlying fault,
not a detail.** Visibility and enablement are **derived** from
`floor_display_mode`, and a derived property with a single manual call site is
a property that is correct only where somebody remembered.

> **The general form, and it is the one to carry: A DERIVED PROPERTY THAT MUST
> BE MANUALLY RE-APPLIED IS NOT DERIVED — IT IS CACHED, AND EVERY CACHE NEEDS
> AN INVALIDATION RULE.** Either every path that changes floor state re-applies
> it, or it is applied where the state is read. **Enumerate the writers of
> `_FLOOR_STATE` and show that each one re-applies** — that is the receipt, and
> it is the same shape as *retire visibility before permission*: enumerate the
> consumers, do not assume them.

## 6. TIER

**Inspection and the document diff: GREEN, measurement only.**

**Any fix: AMBER** — it changes what is drawn and what a gesture can reach.
**Patrick's check is one question: with the second floor hidden, is it invisible
AND untouchable, on a freshly LOADED plan** — the load path being the case §2
says nobody covered.
