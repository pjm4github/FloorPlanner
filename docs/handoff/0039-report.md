# 0039 — report: `fp2dxf` is not in this repository — blocked before it can start

**Per [`0038-ruling.md`](0038-ruling.md).**

**Housekeeping first: this is a SECOND numbering collision this session.**
[`0038-ruling.md`](0038-ruling.md) and this session's own
[`0038-report.md`](0038-report.md) (written earlier, in response to
`0037-ruling.md`, about the cross-floor investigation — unrelated to this
ruling) share a number, the same shape as the `0036` collision. Neither
renamed; both already committed and cited. Numbering continues forward from
`0039`.

---

## THE BLOCKER

**`fp2dxf.py`, its README, `sample_design.json`, `L1.dxf`/`L2.dxf`, the
sidecars, and the 16 screenshots are not anywhere in this repository.**
Checked: repo root, `fixtures/`, `fixtures/incoming/`, `docs/evidence/`, the
whole working tree by filename pattern (`*dxf*`, `*fp2dxf*`, `*chief*`,
`*sample_design*`), the full commit history on every branch (`git log --all`),
and every local and remote branch (`git branch -a`). Nothing.

**Every item in `0038`'s ruling depends on reading or modifying that file**:
the thickness-table rewiring (§3), the three library-hygiene fixes (§4), the
placement decision (§5), the README split (§6), the golden-file test (§7).
None of it can start without the file itself — not because the ruling is
unclear, but because there is nothing on disk to apply it to.

**Owed, the same way a plan goes to `fixtures/incoming/`**: `fp2dxf.py` (and
its README, sample input/output, and screenshots) dropped somewhere this
session can read it. Once it lands, `0038`'s own §5 already says where each
piece belongs, so no further ruling should be needed to start.

## Gate

Nothing built; nothing to lint or test. `python tools/gate.py` unaffected —
not run for this report, since no tracked file changed except this one and
`handoff/README.md`'s pair-table row.
