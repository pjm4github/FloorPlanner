# 0058 — report: the census, run — and the guide line, added

**Per [`0057-ruling.md`](0057-ruling.md) §2 (the deliverable `0056-report.md`
built and did not read) and §3 item 1 (the guide cross-reference).**

---

## 1. THE CENSUS

`docs/evidence/orthogonality_census.py` — every `*.json` under `examples/`
and `fixtures/` (recursive), each checked for the v5 shape before being
measured; nothing silently dropped, every skip named and why:

```
                                                    walls   >5   1-5  0.1-1 0.01-0.1 <0.01
examples/farmplaceBIGmultifloor.json                109      1    5     3      1     99
examples/fiveRoomTest.json                           16      0    0     0      0     16
examples/planc1.v5.json                              83      0    0     0      2     81
examples/planc1TestV5.json                           82      0    0     0      2     80
examples/roundedMultifloor.json                     122      0    0     0      0    122
examples/sample_plan.v5.json                         10      0    0     0      0     10
examples/site_demo.json                              14      0    0     0      0     14
examples/symmetricP1.json                            79      0    0     0      2     77
fixtures/chief-export/sample_design.json             20      0    0     0      0     20
fixtures/d74-wall-decoration.json                     5      0    0     0      0      5
fixtures/fragment2room.json                          12      0    0     0      0     12
fixtures/incoming/crossfloor-snap-2026-08-17.json   151     36    8    21     12     74
fixtures/prism-check.json                             4      0    0     0      0      4
fixtures/shower-glance-check.json                     4      0    0     0      0      4
fixtures/wiscaway2026-08-08.json                    103      2    0     0      0    101
fixtures/wiscaway2026-08-09R.json                   134     53    1     8      0     72

TOTAL                                               948     92   14    32     19    791
```

**Walls within 1° of orthogonal WITHOUT being on it: 63 of 948.** That is
[`0055`](0055-ruling.md) §4's own input to item C's tolerance argument.

**Skipped, and named rather than dropped (8):** `examples/planc1.json`,
`examples/planc1TestV4.json`, `examples/sample_plan.json` (legacy v1-v4, no
top-level `vertices`/`walls`); `fixtures/chief-export/L1.openings.json`,
`L2.openings.json` (DXF sidecars, not designs);
`fixtures/enclosure-form-check.json`, `seat-check.json`,
`walk-in-shower-close.json` (real v5 designs, furniture-only checks, zero
walls — verified by reading each file, not assumed).

**Two files cross-check against [`0055`](0055-ruling.md) §3's own numbers,
independently of the two already checked in `0056`'s tests:**
`wiscaway2026-08-08.json` — 103 walls, 2 off-axis, matching *"both
deliberate"*; `wiscaway2026-08-09R.json` — 134 walls, 62 off-axis
(53+1+8+0), matching the ruling's count exactly. **Four of the ruling's own
numbers now independently reproduced, not three.**

**`fixtures/incoming/crossfloor-snap-2026-08-17.json` is the outlier** — 36
walls over 5°, the highest count in the corpus by a wide margin. That file
is the live cross-floor-snapping intake plan ([`0035`](0035-ruling.md)–[`0037`](0037-ruling.md)),
not this task's thread; named here because the census found it, not
triaged here because it belongs to a different open investigation.

**What this does NOT settle, stated because `0055` §5 already declined it
for the two wiscaway files and the same caveat applies corpus-wide:** a
large-angle wall may be real architecture (a bay, a diagonal wing) rather
than drift. The band counts are a census of ANGLE, not of INTENT — same
limit as `0056`'s own instrument, now just run at scale.

## 2. THE GUIDE LINE

Added to `README.md`'s "Export to Chief Architect (DXF)" section (the
guide's actual location per [`0054-report.md`](0054-report.md) — **not**
`docs/guides/chief-architect-export.md`, which [`0057`](0057-ruling.md) §3
names but which `0052-ruling.md`'s own destination was superseded by where
the branch had already landed it before `0052` could be seen from it; the
correction goes where the guide actually lives, not to a second copy):

> **Before exporting, check Edit ▸ "Wall orthogonality report…".** A wall
> that is a fraction of a degree off axis draws as straight in FloorPlanner
> but reads as a real angle to Chief's CAD to Walls importer — this is the
> tool that tells you before Chief does.

Placed right after the export's own diagram and before the "pick an output
folder" instructions — the natural point in the workflow to check first.

## 3. WHAT WAS NOT DONE, PER `0057`'S OWN SCOPING

**§3 item 2** (should the export itself warn on off-axis walls?) —
**not ruled, not built.** `0057` names it as a question, not an
instruction, and says its own answer depends on this census: with 92 walls
corpus-wide over 5° concentrated almost entirely in one 151-wall outlier
file, a blanket export-time warning would likely be noise on every other
plan in the shipped corpus. Flagging the number as evidence for that
question, not answering it.

**§4** (the Edit-menu placement question) — noted, not reworked, per its
own "not worth a rework on its own."

**Item C (the repair) and grid snap (item A)** — still untouched, still
RED / unchanged respectively, unchanged from `0056`.

## 4. TIER

**GREEN**, per `0057-ruling.md` §6 — pushed without a stop.
