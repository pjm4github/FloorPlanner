# 0064 — report: `0063`'s three GREEN items done; two out-of-band features landed

**On [`0063-ruling.md`](0063-ruling.md).** All three of its ordered GREEN
items are done. Nothing else from the queue was touched. Two unrelated
features landed on `main` directly at Patrick's in-session request, outside
the handoff queue entirely — reported here so the record has them, per this
channel's own rule that a change to `main`'s head gets written down.

---

## 1. `0063` §6 — the mailbox landed on `main`, doc-only

`0061-ruling.md`, `0062-report.md`, `0063-ruling.md` and their two
`handoff/README.md` rows are on `main` at `404ed89`, ahead of any merge
decision on the code they describe. The AMBER branch (`cross-floor-align-fix`)
was merged from `main` and then aborted once the merge revealed the branch's
own `SESSION_SNAPSHOT.md` copy would need faking `main`'s identity to satisfy
the snapshot gate — the branch keeps only code, per `0063` §6's own rule, and
reconciles at actual PR merge, not before.

## 2. `0063` §3 — the positive control, added and pushed to the branch

`tests/test_floors.py::test_align_to_wall_does_not_snap_to_a_hidden_floor`
now carries the pairing `0063` asked for: the original assertion (an open
end on a **hidden** floor must NOT be taken) plus a new second half — the
same geometry, an open end at the same offset on the **active** floor, MUST
still align. Without it the fail-first assertion was a pure negative,
indistinguishable from alignment having quietly stopped firing at all (D43's
own shape, per `0063` §3).

Commit `ea215ff` on `cross-floor-align-fix`, pushed. Full gate re-run GREEN,
`collected=779`. Posted as a PR #34 comment so the record of *why* it changed
sits next to the diff, not just in this file. **[PR #34](https://github.com/pjm4github/FloorPlanner/pull/34)
is still OPEN, still AMBER, still stopped for Patrick's manual check — the
one question, quoted from `0061-ruling.md` §6: *"with the second floor
hidden, does a wall you draw still jump to something you cannot see?"***
Nothing else in the fix changed.

## 3. `0063` §4 — `fixtures/incoming/README.md`'s fourth exit

Added: *"PROMOTED to `fixtures/` as a measurement subject … no test names
it, and none is owed."* `0063` §4 found the three-exit contract had no room
for `crossfloor-snap-2026-08-17.json`'s actual disposition — kept as a
census input (`docs/evidence/orthogonality_census.py` had already been
counting it before the promotion), not as a test fixture. Landed on `main`
at `f93e9dd`, alongside the snapshot re-cut that commit needed.

## 4. Outside the queue — two features, Patrick asked for directly in-session

Not part of any handoff exchange; recorded here because they moved `main`'s
head and this file's own rule (§5) says that gets written down regardless of
channel.

**`5d85b09`** — the selected wall's id and its two vertex ids on the status
bar. `WallItem` gained a `uid` property mirroring `Vertex.uid` exactly (lazy-
minted on first read, stable for the item's lifetime, session-local — not
the id a saved document assigns, which renumbers geometrically at export).
Shown only when exactly one wall is selected; updated from the existing
debounced `selectionChanged` handler (`_apply_edit_actions`), not a second
listener.

**`cc12bbf`** — Patrick asked for more: each vertex's `(x, y)` in decimal
feet to 3 significant digits, the wall's length the same way, and its
heading in degrees — but only when the wall is not exactly axis-aligned
(0/90/180/270), so an ordinary wall's selection doesn't clutter the bar with
`angle 0.0deg`. Two new pure helpers in `geometry.py`: `fmt_ft3` (decimal
feet, 3 sig figs, no unit suffix — a coordinate pair wants it once, not per
axis) and `heading_deg` (the full 0–360 compass heading, deliberately NOT
folded like `validate.py`'s `wall_angle_deviation_deg` — this is for reading
one wall's own direction, so 90 and 270 stay distinct, and a wall a
fraction of a degree off axis shows its real heading rather than being
rounded onto the nearest cardinal, which would hide exactly the drift this
project's whole orthogonality thread cares about).

Both checked with an offscreen headless render before committing, not just
trusted — caught the unicode-arrow crash class once already this session
(`→` is unencodable on this project's cp1252 console the moment it appears
in a failing assertion diff), so both labels use ASCII (`->`, `deg`) on
purpose. 12 new/updated tests across `test_geometry.py`, `test_selection.py`,
`test_walls.py`. Full gate GREEN both times (`collected=781` then `793`).
Both pushed straight to `main`, no PR — additive, no existing behaviour
changed, GREEN per the standing autonomy policy.

## 5. WHERE THINGS STAND

| | |
|---|---|
| `main` | `4f61c33` |
| Open branch | `cross-floor-align-fix` — [PR #34](https://github.com/pjm4github/FloorPlanner/pull/34), AMBER, stopped for Patrick's manual check |
| Gate | GREEN throughout, `collected=793` on `main`'s current tip |

**Still owed, unchanged by anything in this report:**

- **Item C's ruling** — `0061`/`0063`, still Patrick's, still RED, now the
  oldest item on his side of the channel.
- **The follow-on hardening pass** — `0062` §3's four masked reachability
  sites (`hit_candidates`, the rubber-band select, the two macro paths) and
  `wall_endpoint_open`'s `floor=None` default (`0063` §5) — named, not built,
  no receipt yet for either.
- **Grid snap** — read-back first, per `0055` §4's extra clause: does
  snapping cover an operation's *output*, or only cursor input?

## 6. TIER

**GREEN** — `0063`'s three items were all GREEN by their own ruling; the two
status-bar features are additive UI, no existing operation's output changed,
gate GREEN throughout.
