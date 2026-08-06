---
# permanent key, independent of GitHub
id: 25
title: "A gesture can create a door-straddles-junction scene state that the document can only represent as"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-07-31
closed: 2026-08-01
closed_by: null
rank: 30
related: [17]
state_source: row
github_issue: null
---

# D25 — A gesture can create a door-straddles-junction scene state that the document can only represent as

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 95) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**A gesture can create a door-straddles-junction scene state that the document can only represent as a reported fault; the creating edit should report it.**~~ **CLOSED at P4.1b, 2026‑08‑01 — the gesture now says so at release, and only the message changed.** Both gestures (draw-release and endpoint-drag release) call `report_doorway_landings`: the straddle question is asked of `plan_split_edge` (the ONE definition of "a junction lands inside this opening" — no second planner), the body search runs at `ON_SEG_TOL` rather than `JOIN_TOL` so a deliberate reveal never nags, and the message names the edit and the door through a scene-filed list drained at the debounce beside the defect-6 report (its own head — nothing failed to be *placed*, so "Could not place" would misblame a door that is fine). What the gesture DOES is untouched, per the ruling; decline/split/weld policy stays P4.3's. The walk's report path (R2c) is unchanged and stays as the load-path safety net. **Receipt, fail-first and mechanism-proving:** both pinning tests run unchanged against pre-fix `main@708dc2e`, reach their preconditions (the end measurably rests on the host's centreline inside the door span — the defect-28 vacuity lesson), and fail on the message assert with the status bar holding only the generic tool hint. Drawing or dragging a wall so its end lands on another wall's BODY inside a doorway is accepted silently. The scene is self-consistent — the door fits its wall — but the document must split that wall at the junction, and no segment can then hold the door. Since **R2c** the walk emits it and files it (`openings_failed`), so nothing is lost and nothing slides; what is missing is that **the edit which created the state says nothing at the time**. That is defect 17's lesson exactly: a gesture whose consequence is invisible until a later save is a silent decline wearing a different hat. **Once this closes, the walk's report path becomes dead code for live edits and stays as the load-path safety net** — a legacy file can still arrive in this state and a load cannot decline. <br><br>**Phase: P4.1 as proposed, and I would argue P4.3 — recorded rather than swallowed.** P4.1's deliverable is *delete-wall keeps the room*, and the guard here is not about deletion; the gestures that create the state are draw-release and end-drag. P4.3 is the task that introduces `settings.editing.{shuffle, auto_coalesce, auto_weld, auto_bind}` — the flags that decide *what a gesture does on its own* — and "may a wall end land inside a doorway, and if so who is told" is a member of that family, not of the delete family. Counter-argument for P4.1, which is real: it is the next task to touch wall-op gestures at all, and leaving this until P4.3 means two more phases of silence. Registered at P4.1 per the ruling; the dissent is here so it is visible when P4.1 opens rather than re-litigated from memory.

## Site

`view.py` (draw release), `walls.py` (`mousePressEvent` / end-drag, `split_body_landings`)

## Milestone

~~**P4.1** *(provisional; argued P4.3)*~~ **P4.1b (done 2026‑08‑01)** *(ruled 2026‑07‑31)* — **move trigger:** re-open the phasing at whichever comes first, P4.1's start or the first user report of a door lost across a junction. **FIRST REAL-USER CONFIRMATION OF THE GESTURE ARM — Gate 3, 2026-07-31.** Patrick drew a wall ending on a doorway: the join **correctly declined** to split through the door, so the end was left unwelded — and the only thing he saw was the **generic torn-network warning**, which names an edit but not *this* edit or *this* cause. So the mechanism behaved exactly as R2c designed it (the walk emits and files; nothing is silently lost) and the **ergonomics gap is the whole of what remains**: the gesture that created the state says nothing at the time, and the message he did get sends him looking for a tear rather than a doorway. That is defect 17's lesson in the wild — a gesture whose consequence is invisible until a later report. **It strengthens the P4.1 case over my P4.3 dissent:** the argument for P4.3 was that this belongs with the flags that decide what a gesture does on its own, but a user hitting it at draw-time wants the message at draw-time, and P4.1 is the next task to touch wall-op gestures at all. The mechanism is already in place (R2c: the walk reports and emits), so what is deferred is only the gesture-level warning. **RULED 2026‑07‑31 at the P4.1 read-back: P4.1b — standalone and immediate, branching the moment P4.1's PR merges.** The move trigger fired on both arms at once (P4.1 opened; Gate 3 delivered the first user report). The fold into P4.1 was rejected on the fold-proposer's own stated honesty — it rested on next-to-touch plus the fired trigger, not on mechanism. Scope is message-only per the plan's P4.1b task text: the gesture-time message naming the edit and the doorway through the defect-6 vocabulary; no change to what the gesture does; decline/split/weld policy remains P4.3's with the `auto_*` flags (the dissent's surviving kernel).
