# 0156 — report: R4a closed — PR #54 merged on green CI

**Code, 2026‑09‑06.** GREEN-tier close-out, per [`0154-ruling.md`](0154-ruling.md)
§3's own table: R4a's check is CI, not a manual one.

---

## 1. DISPOSITION — R4A CLOSED, MERGED

[PR #54](https://github.com/pjm4github/FloorPlanner/pull/54) — `ruff` and
`pytest (py3.13, full gate)` both green (the other three CI jobs remain
intentionally disabled per [`0105-ruling.md`](0105-ruling.md)); merged to
`main` at `0ea47c1`, branch `roofs-r4a-schema` deleted (local and remote),
under the standing GREEN-tier autonomy policy — no wait for a manual check,
none is owed. **R4a is done.**

Re-gated on the combined tree after the merge: full suite **1168 passed**,
7 deselected (`perf` lane), `ruff` clean, `python tools/gate.py` (full
mode) GREEN.

**R4b is the next available tranche (AMBER)** — the parameters dialog:
per-side overhang, heights/pitch via the End-On machinery, gable↔hip per
end, the `room_top` binding toggle. Per [`0154-ruling.md`](0154-ruling.md)
§3's order: R4a → **R4b** → R4c → R5.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items.
