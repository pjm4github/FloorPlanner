# `fixtures/` — plans for MANUAL checks

**These are not the corpus.** `examples/` holds reference plans: they are
validated by `tests/test_schema.py`, frozen by `tests/test_corpus_freeze.py`,
and changing one needs a declared justification. Nothing here is any of that.

A file in this directory exists to be **opened by a human during a manual
check** — the AMBER gate at the end of a task. It may be deliberately dirty,
because the state a check needs to start from is often exactly the state the
invariants exist to complain about.

**Why it is not in `examples/`, stated once so it is not re-litigated.**
`tests/test_schema.py` parametrizes over a **filesystem glob** of
`examples/*.json`, so a plan dropped in there changes the collected test count
and — if it trips an invariant — turns the gate red and, through the commit
hook, **blocks every commit in the repository**. That is
[D51](../docs/defects/0051-the-census-depends-on-the-working-tree.md), and it
happened to `fragment2room.json` on 2026‑08‑08 before it was moved here.
This directory is outside both corpus tests by construction.

**So a file here may be edited freely.** No freeze, no justification, no
re-cut. If a manual check needs the plan changed, change it.

| file | what it is for |
|---|---|
| `wiscaway2026-08-08.json` | **Patrick's own plan**, moved here from `examples/` on 2026‑08‑08 because it is a working drawing, not a reference. It trips **one** invariant — `I7  opening o29 runs off wall w90 (68.0..116.0 of 72.0)`: a 48″ pocket door anchored 68″ along a 72″ wall, straddling the welded junction at `v90` so 4″ sits on `w90` and 44″ on `w91`. **That fault is the trigger for [D57](../docs/defects/0057-face-at-hands-walls-of-a-report-of.md)** — deleting a room and re-naming the enclosed space with the Room tool crashes the app, on this tree and on `main`. **Do not repair the door**: it is what reaches the broken branch. |
| `fragment2room.json` | **D47 / A1's manual check.** Two overlapping placed rooms, `A` (255.8 sf) and `B` (249.8 sf), overlapping by **81.0 sf** — the input `Rooms ▸ Fragment into pieces` exists to resolve. It trips `I11` **on purpose**: the overlap is the fixture. Fragmenting it gives three disjoint pieces totalling 424.5 sf, and that 505.5 → 424.5 drop is itself evidence the pieces do not overlap. Also the plan behind [D53](../docs/defects/0053-a-room-cannot-be-selected-by-clicking-its.md)'s click differential. |
