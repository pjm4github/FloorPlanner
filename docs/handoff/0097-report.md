# 0097 — report: `CLAUDE.md` trimmed to traps only — `0085-ruling.md`

**On [`0085-ruling.md`](0085-ruling.md) §2.**

## Byte count

`CLAUDE.md`: **13,824 → 4,730 bytes** (66% cut). Target was under 2 KB;
missed it — see §3.

## Where each cut paragraph went

Nothing deleted, one new file, **[`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)**,
carries everything the KEEP/CUT split named:

| cut from `CLAUDE.md` | destination |
|---|---|
| the module dependency roster | `ARCHITECTURE.md` §"Module layout" (also: every module already carries this in its own docstring — verified for all 17) |
| the phase-by-phase account (`P3.5`, `P4.2`, …) | `ARCHITECTURE.md` §"Phase history", pointing at `V5_MIGRATION_PLAN.md`/`progress/`, already authoritative for it |
| the measured perf figures (299ms→28ms etc.) | `ARCHITECTURE.md` §"Performance" |
| the extract/join narrative | `ARCHITECTURE.md` §"Extract / join" (also already in `extract.py`'s own module docstring, checked directly) |
| the floors narrative | `ARCHITECTURE.md` §"Floors" (the runtime-cache-not-a-global reasoning is also already in `config.py`'s own comment, checked directly) |

`docs/README.md`'s map gains one row pointing at the new file.

## The 12-item KEEP list — all present, each one line

Verified against `0085` §2's own list: `import FloorPlanner` re-export,
inches, mixins-not-wrappers, late-imports-only-to-close-a-cycle,
`snapshot`/`design_document`/`serialize`, generated `assets/`, one shared
`Vertex`, no synthesized Ctrl keys, `QApplication`-before-`QImage` +
`arr.copy()`, don't-memoize-the-wall-path / don't-move-junction-work,
coalesced wheel zoom, E402, `pytest --quick`.

## §3 — why the target was missed, stated rather than silently accepted

**`0085`'s own rule: "if a cut cannot get there without losing something
that passes the test, say so and leave it in — the number is a target, not
the rule."** Kept, beyond the 12-item list: the Linting/Tests section
(the actual `ruff`/`pytest` commands and marker selection — not in either
list, and cutting a command a reader needs to run would be exactly the
"wrong" failure mode the whole ruling is about), the headless
scratch-script pattern (six items, each a real "the code will mislead you"
trap — a modal dialog hangs headless, `QTest.mouseMove` doesn't synthesize
held drags — not just "slow to discover"), and repo etiquette (commit/push
policy, `gh`'s path). None of these were named for cutting; all pass the
test on inspection.

## Receipt

Full suite 786 passed (`--quick`), `ruff` clean, gate GREEN. Docs-only.

## Tier

GREEN.
