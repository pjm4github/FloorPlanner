---
# permanent key, independent of GitHub
id: 26
title: "Shadow mode kills the process instead of reporting: a DesignVerificationError raised inside a Qt"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:io
milestone: P3.6

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 29
related: [28]
state_source: status-table
github_issue: null
---

# D26 — Shadow mode kills the process instead of reporting: a DesignVerificationError raised inside a Qt

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 94) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Shadow mode kills the process instead of reporting: a `DesignVerificationError` raised inside a Qt callback becomes `abort()`.** ROOT CAUSE, with a traceback — not memory corruption, which is where the first three rounds of guessing were headed. The chain, each link measured: (1) `_commit_if_changed` is connected to a **`QTimer.timeout` signal**, so it runs inside a C++→Python callback; (2) under `deep`, `verify()` finds **I11 (two placed rooms overlap)** and raises, as it is designed to; (3) since PyQt 5.5 an exception escaping such a callback is handed to `sys.excepthook` and then **`qFatal()`** is called; (4) `qFatal` → `abort()` → `__fastfail(FAST_FAIL_FATAL_APP_EXIT)` = **`0xC0000409` raised from `Qt6Core.dll+0x1cf68`**. Caught by installing a `sys.excepthook` (`tools/qt_excepthook.py`) — the traceback is available for exactly one moment before the abort. <br><br>**FOUR PROPERTIES THAT LOOKED LIKE A RACE, ALL EXPLAINED:** *no stderr message* — PyQt calls `qFatal` after the hook and it never reached the pipe; *deterministic crash point, intermittent occurrence* — the **timer** decides which quiescent point runs the check, so it lands at the same test when it fires there and misses otherwise; *every "suppressing" intervention* (faulthandler 0/6, flushing tracer 0/8, `-x` 0/8) — each only shifted timing enough to move the timer, and none was a fix; *the `E` at `test_a_group_rotation_also_keeps_the_corners`* — the same fault surfacing through the safer teardown path. <br><br>**Two of my own claims withdrawn by this:** capture mode was never the variable (it crashed on run 1 under `--capture=sys`, where fd capture is off), and my first read of the dump mislabelled fastfail **7** as `GS_COOKIE_INIT` — an off-by-one in a table typed from memory; 7 is `FAST_FAIL_FATAL_APP_EXIT`, i.e. `abort()`, and that one wrong word pointed the whole diagnosis at corruption. `tools/read_minidump.py` now carries the table with a note saying so. <br><br>**This is an APP defect, not a test defect.** Any genuine invariant violation found at a quiescent point aborts the process rather than reporting it — on Windows, in a GUI session, a user loses their work. Fixed at (A) by a **narrow** boundary guard: `verify()` goes on raising, and the callback call sites catch `DesignVerificationError` only and route it to the report channel. The underlying I11 is real and is **defect 28**.

## Site

`mainwindow.py` (`_commit_if_changed`, on the dirty timer); `design/verify.py` raises by design

## Milestone

**P3.6**
