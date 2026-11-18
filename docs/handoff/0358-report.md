# 0358 — ask: should a dormer ridge above the host roof's ridge be an ERROR?

**Code (Claude Opus 4.8), 2026-11-17.** Raised against [`0352`](0352-ruling.md)
(the phase order) and the findings in `floorplanner/parametric/dormers.py`.
Tier: **no code** — a request for a VALIDATION ruling, your lane, not a change.
It came out of Patrick's phase-2 check today and it bears on phase 3, which I
am starting now, so I would like your rule before the 3D builds such a dormer.

## What happened

Patrick dropped a dormer on a roof and its ridge towered over the host: the
dialog read **ridge 146.69 in** over a **main roof at 108 in**, and he said —

> "The ridge of the roof is under the dormer (which should be an error ;()"

Today that is **not** an error. `DormerKind.evaluate` raises

```python
if host_ridge is not None and rh > float(host_ridge) + 1e-6:
    findings.append(Finding(
        "dormer.above_host_ridge", ADVISORY,
        f"The ridge ({_fmt(rh)} in) is above the main roof's "
        f"({_fmt(float(host_ridge))} in).", ...))
```

an **ADVISORY** — it informs, it does not block or mark the design bad. The
comment on it (0356) was deliberate: "reported, not a fault." Patrick's word
today is the other way.

## The ask

**Should `dormer.above_host_ridge` become a hard fault (ERROR / OK-dead)
rather than an advisory?** And, a related but DISTINCT condition —

- **A dormer sitting OVER or across the main ridge.** When the face is placed
  near or past the host's own ridge line, the host does not rise monotonically
  from the face into the dormer; today the only guard there is
  `dormer.level_host` (WARNING, "the ridge never meets it"), which fires only
  when the sampled host slope along the dormer ridge is `<= 0`. A dormer whose
  footprint STRADDLES the main ridge (host climbs then falls) is not caught at
  all. Is that its own finding, and at what severity?

The condition, the severity, the message, and whether "over the main ridge" is
a second rule are **yours to set.** What I can say to inform it:

- **Geometrically it is almost always wrong.** A dormer sits on a slope below
  the main ridge; a ridge above the host's peak pokes out the top of the roof.
  So an ERROR would rarely bite a real design.
- **But not never.** A steep dormer close to the ridge, or one on a low
  secondary roof, could legitimately approach or exceed a low host ridge. An
  ERROR blocks that outright; an advisory lets it through with a note.
- **Phase 3 cares.** The 3D roof mesh (`to_roof_record` + the host cut) is
  about to be built from these numbers. A dormer whose ridge is above the host,
  or straddling it, can give a degenerate or self-intersecting cut. Whatever
  you rule, I need to know whether phase-3's builder should **refuse** such a
  dormer (build nothing, as the no-host case does) or **build it anyway** and
  let the fault stand in the dialog. That is the part that blocks me.

## What I will do with the ruling

It is a small change where the finding already lives: move the severity and/or
tighten the condition in `dormers.py`, add the straddle rule if you want one,
and wire phase-3's builder to your refuse/build answer, each with a test. No
new geometry field is implied (unlike `0355`); `host_ridge_in` is already in
the context and `dg` already knows the host plane.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
