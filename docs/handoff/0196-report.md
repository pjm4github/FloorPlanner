# 0196 — report: PR #64 merged on his word (the record 0194 owed); 0195's clamp built and its closure demand answered; AMBER, stopped for his check

**Code, 2026‑09‑24, on [`0195-ruling.md`](0195-ruling.md).** First the
record [`0195`](0195-ruling.md) §4 names as owed: Patrick's check of PR #64
passed — his words, *"that fixed it, merge PR #64"* — and on that word
`roofs-r5c-undo-macro` was landed on `main` at `d86bfd3`, fast-forward,
the branch deleted local and remote; only `main` remains on the remote.
[`0194`](0194-report.md) had said "stopped for his check" and no report
recorded the merge; this one does, and the tree and the record agree
again. Then §2's tranche: branch `roofs-r5e-grip-clamp` off `main` at
`d86bfd3`, PR #65 open, gate GREEN, **stopped for his check** — drag
the dormer's back knob past the host's crest and watch it stop dead there
instead of folding back.

## 1. THE CORRECTION — 0194 §1 overclaimed, exactly as 0195 §2 says

0194 §1 said the rebuild *"derives the back end onto that very point"*,
unqualified. It does so **only on the rising side of the host's
surface**: past the crest, or past the footprint, the height read at the
cursor is one the host already reached nearer the face, `meet_along`
finds that earlier crossing, and the derived end lands **short of the
cursor** — further out, shorter. The sentence was stated more strongly
than the code supported and was not measured at the edges; the test
dragged 40″ up a host whose crest was 90″ away. Withdrawn, and replaced
by §2 below.

## 2. THE CLAMP — built as ruled

**`roofclip.rising_reach(rf, origin, direction)`** (Qt-free, beside
`meet_along`): how far along the ray the host's surface keeps strictly
rising while the point stays inside the host's footprint — half-inch
steps bracket the end, bisection finds it to about a nano-inch (the
rising test is a 1e-9 finite difference, so the end lands that far short
of the crest, never past it). Zero when the origin is outside the
footprint or the surface does not rise from it.

**`RoofItem.drag_end(1)` on a dormer** clamps the landed distance to that
reach: `a = min(max(MIN_RIDGE_LEN_IN, landed), reach)`; a reach under
`MIN_RIDGE_LEN_IN` refuses the drag outright. Everything else is as 0194
built it — the cursor read `GRIP_END_OFFSET_IN` inward, the landing on
the 6″ grid along the ridge, the height from `surface_height(host)` at
the landed point, the refusal within 1″ of the eaves. So the grip tracks
the cursor everywhere it can go and stops dead where it cannot.

**The three tests, fail-first as ordered** (`tests/test_roof_dormer.py`):

* **The rising side, pinned:** drags to plan y = 156, 144 and 108 (the
  crest at 100) land the back end on the dragged point to **1e-9**, the
  ridge at the host's surface there. Passed before the clamp and after.
* **Past the crest:** a drag 30″ past the crest lands **on** the crest
  (plan y = 100 to 1e-6, the ridge at the host's own 150″ to 1e-8), and
  a further drag stays there. **Failed before the clamp** — the unclamped
  code folded back to y = 72, ridge 134.88″ — and passes after.
* **Past the footprint:** a dormer 20″ from the host's gable end with a
  diagonal (Shift) ridge leaves the footprint while still rising; a drag
  well beyond is clamped at the footprint's edge (x = 400 to 1e-6), the
  ridge at the host's surface **there**, never off a continued plane.
  **Failed before** (landed at x = 420.8, outside) and passes after.

## 3. THE DEMAND — what closes the dormer below its eaves, named and probed

**The closure is R4f's `_cross_roof_risers`** (`fp3d.py`, 0174's own
fix): for every boundary where two roofs' final territories touch at
**unequal** height — a boundary that is not a seam — it emits a
double-sided vertical riser quad (`_riser_quad`) from the lower surface
to the higher along that segment. The dormer's two eaves lines and its
face are exactly such boundaries against the host: the dormer's cells
end there at its eaves height, the host's cells meet them at the host's
lower surface, and the riser spans the difference — up to 14.6″ at the
face on the fixture geometry (116″ over 101.4″), tapering to nothing
where the eaves meet the host plane. The gable triangle above the eaves
is `_gable_fascia_pieces` (an open gable end). No other geometry is
involved; the deleted cheeks and face were never what closed it — they
overlapped the risers.

**Probed** (`tests/test_viewer_dormer.py`, one test): four rays each
crossing a plane inside the gap — the left eaves plane at x = 170 and the
right at x = 230 (plan y = 180, z = 111 between the host's 106.8″ and the
eaves' 116″), the front at y = 190 at the ridge line and near a corner
(z = 108 between 101.4″ and 116″, cast **along y across** the plane, so
the face is measured this time) — each hits the built roof mesh; with
`_cross_roof_risers` patched to return nothing, **all four miss**. So it
is the risers, and nothing else, that close the dormer, and the next
deletion in that file cannot open it silently.

## 4. THE CHECK — receipts

`tests/test_roof_dormer.py` +3 (the three of §2), `tests/test_viewer_dormer.py`
+1 (§3). Full suite **1351 passed**, 7 deselected (`perf` lane), `ruff`
clean, gate GREEN — the branch's own run. Every pre-existing dormer, grip,
tool, macro and intersection test passes unmodified.

## 5. `fixtures/incoming/`, with ages

`README.md` only.

## 6. WHAT HAPPENS NEXT

His check of PR #65: drag the dormer's back knob up the slope and past
the crest. On his word it merges, branch deleted in the merge step. Then
R6 multifloor — still waiting on his fixture and his one-line display
answer ([`0186`](0186-ruling.md) §4), owed by him, not by Code.

**Carried:** unchanged from [`0195`](0195-ruling.md), its §3 discharged
above.
