# 0081 — report: current state, consolidated — three AMBER PRs, item C's read-back, every GREEN settings/`fp2pdf` item

**Not tied to a single ruling** — a consolidated status report so the whole
state is in one place rather than split across `0079`/`0080` and three open
PRs. Nothing new built here; this restates what is already landed and what
is still owed.

---

## 1. THREE AMBER PRs, ALL OPEN, ALL UNCHANGED — ONE APP SESSION

| PR | fixes | merge condition |
|---|---|---|
| [#34](https://github.com/pjm4github/FloorPlanner/pull/34) | `_align_to_wall`'s cross-floor snap (`0061`/`0062`/`0063`) | see below |
| [#35](https://github.com/pjm4github/FloorPlanner/pull/35) | the wall status-bar label's two defects (`0068`/`0069`) | see below |
| [#36](https://github.com/pjm4github/FloorPlanner/pull/36) | D80, the T-junction grid-snap bug (`0070`/`0071`) | see below |

**Patrick's checks, restated verbatim so none of the four drift across
handoffs:**

> 1. **PR #34** — *"With the second floor hidden, does a wall you draw still
>    jump to something you cannot see?"*
> 2. **PR #35** — a wall you believe is straight must say nothing about its
>    angle; a wall you believe is crooked must not claim an exact cardinal.
> 3. **PR #36** — *"With snap set to 6″, draw and then slide an interior
>    wall inside an existing room. Does every corner land on a 6″ line?"*
> 4. **One line for the record** — is the status-bar label, as it stands on
>    `main`, what you asked for? (The check already happened — you asked
>    for more mid-session, only possible from the running app — this line
>    is just it written down.)
> 5. **`0068` §4** — off-axis walls: heading (`89.9990deg`), or how far off
>    axis (`0.0010deg`)? The heading can round to a false cardinal at a
>    small enough deviation; the second can never.

Nothing merged yet. `main` is unaffected by any of the three — each stays
on its own branch until checked.

## 2. ITEM C (THE ORTHOGONALITY REPAIR) — READ-BACK ANSWERED, REPAIR NOT BUILT

[`0066-ruling.md`](0066-ruling.md) ruled the repair's tolerance is a
**displacement, in inches** — not the degree the report reads in; two
nearly-identical angles (0.9094°/0.9290°) move a wall end by 1″ and 3″
respectively.

[`0079-report.md`](0079-report.md): the displacement instrument is built
and merged to `main` (GREEN, no branch needed — `wall_orthogonality()` now
reports both numbers, cross-checked against the ruling's own 63-value
sorted list to the exact value). The read-back item 2 (the repair itself)
was blocked on is answered in full — the conflict predicate, which
endpoint moves, the preview's wording, the interlock, the acceptance
restated as an inequality. **Measured: 14 of 63 near-axis corpus walls
have a conflict, but only 2 are fully unrepairable — 61 of 63 would
actually be fixed by this first delivery.**

**The repair itself is not built.** It is AMBER (`0066` §7 item 2) and
does not start until the read-back is ruled.

## 3. SETTINGS / `fp2pdf` — EVERY GREEN ITEM ACROSS FIVE RULINGS BUILT

[`0072`](0072-ruling.md)→[`0073`](0073-ruling.md)→[`0074`](0074-ruling.md)→[`0075`](0075-ruling.md)→[`0077`](0077-ruling.md)→[`0078-ruling.md`](0078-ruling.md),
built in two batches ([`0076-report.md`](0076-report.md),
[`0080-report.md`](0080-report.md)), all merged to `main`:

- `coerce_setting()` — one shared, type-aware settings loader (a real bug
  fixed along the way: its own bool branch was `bool("false") is True`).
- The app-settings store rebuilt on plain JSON (`QSettings` dropped
  entirely), with migration from the legacy INI, full materialisation of
  every `DEFAULT_SETTINGS` key, a `SETTINGS_VERSION`/migration-table
  mechanism with a mechanical pin test, and a corrupt-file quarantine path
  — none of it silently losing data, each guarantee receipted as a real
  RED→GREEN differential.
- `fp2pdf.py`'s four hygiene faults fixed to match `fp2dxf.py`'s own
  precedent, and a new dependency-free `_stdt.py` leaf so the two
  exporters no longer depend on each other.
- `reportlab` in `requirements-dev.txt` — its own end-to-end receipts now
  actually render a PDF in CI instead of being skipped.

**Still AMBER/RED, not built:** the three-rung settings-precedence chain,
the "use as default" checkbox, the export-menu re-parent, the PDF options
dialog, `--settings`, the application CLI. All wait on `0074`'s own
read-back (key list with types; which keys are plan-only vs. app-wide;
what an old plan without a key does at each rung).

## 4. WHAT'S CURRENTLY UNBLOCKED FOR CODE, NAMED SO NOTHING IS ASSUMED

Nothing GREEN is currently waiting to be picked up — every GREEN item
across `0066`/`0072`–`0078` is built and merged. What remains is either:

- **Blocked on Patrick** — the four manual checks (§1), item C's read-back
  ruling (§2), the settings-precedence read-back (§3), `0068` §4's
  heading-vs-deviation question.
- **RED, unruled** — item C's §3 (a user-settable `T`, the graph solve for
  the 2 conflicted walls), the application CLI (`0072` §3), `0066` item 3.
- **Named, not ordered** — the follow-on reachability-hardening pass
  (`0062` §3's four masked sites, `0063` §5's `wall_endpoint_open`
  default), grid snap's own read-back (`0055` §4).

**`0066` — item C — was the only reserved number; it is spent.** No number
is currently reserved.

## 5. TIER

**GREEN** — a status report, no code.
