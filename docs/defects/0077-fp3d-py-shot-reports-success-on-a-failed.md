---
# permanent key, independent of GitHub
id: 77
title: "fp3d.py --shot reports success on a failed framebuffer grab"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-15
closed: null
closed_by: null
rank: 77
related: [76]
state_source: row
github_issue: null
---

# D77 — `fp3d.py --shot` reports success on a failed framebuffer grab

**Found producing [D76](0076-an-opaque-mesh-inside-a-translucent-body-does.md)'s
evidence render**, not a defect in the vessel/enclosure split itself — its own
record because it is a general tooling gap, not a detail of that task.

## The finding

`main()` (`floorplanner/viewer/fp3d.py:1544`) does:

```python
body.view.grabFramebuffer().save(a.shot)
print(f"  wrote {a.shot}")
```

**`.save()`'s return value is never checked.** Under `QT_QPA_PLATFORM=offscreen`
on this machine, `QOpenGLWidget` cannot create a GL context at all —
`grabFramebuffer()` returns a null image, `.save()` returns `False`, no file is
written, and `--shot` still prints `wrote <path>` and exits 0. Measured directly:
`python floorplanner/viewer/fp3d.py fixtures/enclosure-form-check.json --shot
out.png` under offscreen printed the message and wrote nothing, reproducibly.
The **same command without forcing `offscreen`** — the real Windows platform,
an actual (if brief) window — succeeds and writes a real file.

**This is "reported success and wrote nothing" again**, the shape
`docs/WORKING_AGREEMENT.md`'s instrument-validation rule already names for two
other cases (a vertex census, a call counter) — here inside the CLI's own exit
path rather than a measurement script.

## Why it matters

**Every evidence render this project's manual checks depend on goes through
this path**, and the failure is silent: no traceback, no non-zero exit, no
stderr the caller is told to look at (the `QOpenGLWidget` warnings print to
stderr regardless of outcome, on success too, so they are not a reliable
tell). Anyone scripting a headless render — the obvious thing to try, and what
[`docs/evidence/enclosure_form_measurement.py`](../evidence/enclosure_form_measurement.py)'s
own docstring already warns against for a related reason — gets a false
"wrote" and a missing file, discovered only by checking the file exists.
[`docs/evidence/enclosure_bodies_omitted_render.py`](../evidence/enclosure_bodies_omitted_render.py)
now documents the workaround (do not force `offscreen`; a real display
session is required) but nothing in `fp3d.py` itself protects the next script
that does not already know this.

## Not fixed here

The fix is one line — check `.save()`'s return and raise or exit non-zero on
`False` — but it is production code (`floorplanner/viewer/fp3d.py`), out of
scope for the task this was found under, and Code does not fold a content
correction into an unrelated commit.

## Ruling

*(Open — filed 2026‑08‑15.)* Not scheduled. The fix is cheap and low-risk
whenever someone is next in `fp3d.py`'s CLI path.
