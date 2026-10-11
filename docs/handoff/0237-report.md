# 0237 — report: his `short-angle-roof.json` — a joined end's extension given ground in every roof's footprint, drawn across roofs it never reached; fixed on `roof-joined-domain`, D88; and what the lock-up measurement found before he redirected it

**Code, 2026‑10‑11.** No merge has happened since
[`0236`](0236-report.md). Two of his messages, in order.

## 0. THE REDIRECT, and what the first message's measurement had found

> *"I have consequently found another bug or infinite loop in the ROOF
> editor. When I edit multiple roofs on one level I have trouble
> selecting and editing them. The program eventually locks up when
> select and moving roof edges."*

Measured on `wiscaway2026-10-07R1.json` (his newest, 7 roofs on two
levels) and on his gable-end fixture, headless, with real mouse events:

* **No hang and no growth.** 224 grip drags (every roof × every grip ×
  near and far offsets), 64 select-drag-release cycles: every release
  completes; the clipper never passed 5 rounds; memory and item counts
  flat. Each release composes the whole building: **0.8–2.3 s on that
  plan**, every time.
* **The cost doubles with every roof on the level** — the thing that
  presents as a lock-up when more roofs are added: 9 roofs 0.75 s, 11:
  1.8 s, 12: 5.2 s, 13: 10.7 s, 14: 17.6 s, **15: 32 s per release**.
  Profiled at 12 roofs: 97 % is `_reach`, a BFS that asks the geometric
  `_adjacent` question of the same pair of pieces again and again — 2.3
  million calls for 165 thousand distinct pairs. A per-piece-list memo
  of that answer (no answer changes) takes 12 roofs from 5.2 s to 3.9 s
  and 15 from 32 to 24 s — a start, not the fix: the piece count itself
  (575 at 12 roofs, 1245 at 15) is the next term. **Parked as a patch**
  (`roofclip-adjacency-memo.patch`, not on any branch) when he
  redirected; it comes back as its own tranche.
* **"Trouble selecting":** on his plan a clipped roof's eave line that
  lies inside another roof's territory is not drawn and so not hittable
  (R4d, by design); its ridge always is. Nothing stole a click: with any
  roof selected, a click on another's ridge selected that one, 20 of 20.

Then:

> *"lets stop this test and look at the design that I dropped in the
> incoming directory called 'short-angle-roof.json' … The right short
> section on the first floor is being projected through the joining 45
> degree roof. Since the right short roof ends before intersecting the
> 45 degree roof it shouldn't project out to that roof. Let start the
> debug with this design and I'll add complexity and rules to the roof
> from here."*

## 1. THE MECHANISM — measured on his design

`L1`: `rf1` (ridge x 30–120, y 240) and `rf2` (x 354–426), both 96″/216″;
`rf3` at 45° off the east end. `L2` at 96″: `rf4`, ridge x 108–366 at
y 240, eaves 60″ and ridge 180″ over the level — **156″/276″ absolute,
standing over both short roofs' inner ends.**

Each short roof's inner end is therefore a JOINED end (under `rf4`, R4d),
and `compute_roof_clips` extended it to close the join — then gave that
extension ground in **every other live roof's footprint** (`for other in
live`). So `rf1`'s extension ran east under `rf4`, came out at `rf4`'s
far end, and was drawn across `rf3` wherever it stood above `rf3`'s
surface — **the fan across the 45° roof in his picture is `rf1`, not
`rf2`**; `rf2`'s ran west and was drawn over `rf1`. `rf2`'s reach was
1344″, the diagonal of `rf3`, a roof that merely contains `rf2`'s end
(80″ above its surface — 0184's open end with respect to it) and joins
nothing. Numbers: `rf1`'s visible cells reached x=759 and `rf2`'s x=30.

## 2. THE RULE — one word in the clipper

**A joined end's extension gets ground in its hosts' footprints and
nowhere else** — `for other in hosts`: the roofs whose footprint holds
the swallowed end, the ones it is converging with there. A roof the end
never entered gets none of it.

Why hosts and not only the joining host: the three-way junction
(R4g, `threeRidgeFloorplan.json`). There `rf2`'s end stands inside `rf3`
above its surface AND crosses `rf1`; its planes must run on over `rf3`
to their valley — and do, because `rf3` holds the end. My first cut
restricted ground to the host the end is *under*, and the R4g boundary
invariant caught it at the exact convergence (a 1.2″ jump). The rule
that satisfies both his plans is the hosts', said so in the code.

**Result on his design:** `rf1` draws within x 30–120, `rf2` within
354–426, `rf3` whole and unjoined, no warnings; the 45° roof's own
lines and its two small seams against `rf2`'s corner remain.

## 3. THE RECEIPT

* `fixtures/short-angle-roof.json`, promoted under exit 1 with his
  sentence as its row — *his base case for the roof rules to come*.
* `tests/test_roof_joined_domain.py`: the fixture is the plan he
  described (heights, which end is under what); each short roof's ground
  within its own footprint, **RED before the one-word change**; the
  three-way junction keeps its ground over a host the end stands inside.
* 185 roof, clip, trace, dormer, viewer and R6 tests unchanged. **D88
  filed, closed at the landing.**

## 4. TIER

**AMBER** — it changes what the plan and the 3D view draw. For his
check: his design on `default`, then the 3D view; the right short roof
stops at its gable, the left one too, the 45° roof carries nothing of
theirs.

## 5. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07, read for §0's
  measurement, not edited; no note; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check. Then his rules, on this fixture, one at a time; and the
compose cost (§0) as its own tranche.

**Carried:** unchanged from [`0236`](0236-report.md).
