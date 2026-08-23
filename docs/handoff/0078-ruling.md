# 0078 — ruling: materialise the settings — and the `version` key now has to do real work

**On Patrick's own answer to [`0077`](0077-ruling.md) §4**, quoted:

> *"I want to see the settings in the file."*

**Settled. `_ensure_settings_file()` writes every `DEFAULT_SETTINGS` key at its
default value, plus the `version` marker.** Everything else in
[`0077`](0077-ruling.md) stands unchanged.

---

## 1. WHAT THE FILE CONTAINS

```json
{
  "version": 1,
  "auto_bind": true,
  "auto_coalesce": true,
  "auto_weld": true,
  "canvas_h_in": 840.0,
  "canvas_w_in": 1200.0,
  "cost_per_sqft": 150.0,
  "rotate_snap_deg": 15.0,
  "shuffle": false,
  "wall_snap_in": 6.0
}
```

**`DEFAULT_SETTINGS` mirrored exactly, plus `version`. One rule, no exception
list** — an exceptions list is a second table, and this thread has been about
nothing else.

**Two consequences of "exactly", both deliberate:**

* **`auto_bind` is in the file** even though it is deliberately absent from the
  dialog (ruled 2026‑08‑03: *"a control would promise behaviour nothing
  enforces"*). **The file mirrors the model, and the model has the flag.** A
  user who edits it will see nothing happen — **that is already true of the
  flag, and it is better than a hand-maintained skip-list that drifts.**
* **`anthropic_api_key` is NOT in the file.** It is not in `DEFAULT_SETTINGS`,
  and [`0075`](0075-ruling.md) §3 clause 2 stands: **materialisation never mints
  a slot for a secret.** It appears only if migration found a real one.

**Creation order is unchanged** ([`0075`](0075-ruling.md) §3): migrate first,
only when the JSON is absent; the INI is left on disk, unread. **The created
file is now `version` + defaults + whatever migration actually found.**

## 2. THE PINNING PROBLEM IS NOW REAL, AND MY OWN MITIGATION NO LONGER APPLIES

[`0074`](0074-ruling.md) §5 answered pinning with: *"the read path treats an
**absent** key as 'use the code default'."*

> ### WITH FULL MATERIALISATION THERE ARE NO ABSENT KEYS. THAT MITIGATION IS VOID.
>
> Every user's file answers rung 2 of [`0074`](0074-ruling.md) §2's chain
> forever, so **rung 1 — `DEFAULT_SETTINGS` — becomes unreachable for anyone who
> has ever launched the app.** Change a shipped default next year and **it
> reaches nobody.** That is not a reason to refuse what Patrick asked for; it is
> the bill that comes with it, and it has to be paid with a mechanism rather
> than a marker.

**RULED: the `version` key does the job it exists for.**

* `config.py` gains `SETTINGS_VERSION` and an ordered migration table.
* On load, a file whose `version` is behind is migrated forward — a step may
  add a new key, rename one, or re-default one — and the version is bumped and
  written back.
* **A key the file does not carry still falls through to `DEFAULT_SETTINGS`**,
  so a hand-edited or truncated file degrades instead of failing.

**AND THE DISCIPLINE IS MECHANICAL, NOT REMEMBERED.** This project's own finding
holds: *"the only two things that have ever fixed this class here are generation
and a gate that fails."*

> **`test_changing_DEFAULT_SETTINGS_requires_a_version_bump`** — pin a hash of
> `DEFAULT_SETTINGS` (keys, types **and** values) against the current
> `SETTINGS_VERSION`. **Editing a default reddens the gate**, and the way to
> green it is to bump the version, add the migration row, and update the pin.
>
> **Not a courtesy test — it is the only thing standing between a materialised
> file and a default nobody can ever change again.**

## 3. I TIERED THIS TWO DIFFERENT WAYS AND OWE THE CORRECTION

[`0074`](0074-ruling.md) §6 put first-run materialisation in the **AMBER** row.
[`0077`](0077-ruling.md) §7 item 6 called it **GREEN**. **Both are mine and they
contradict.**

**GREEN is right, and the reason is the mistake:** `0074` bundled materialisation
into one row with the dialog's Save behaviour and the note-label rewrite, which
**are** user-visible. **Materialisation alone changes no operation's output and
nothing on screen — it writes a file the user has to go and open.** The row was
wrong, not the tier.

## 4. TIER AND ORDER — [`0077`](0077-ruling.md) §7 with item 6 unblocked

| | | |
|---|---|---|
| 1 | [`0077`](0077-ruling.md) §2 — `coerce_setting`'s bool branch | **GREEN**, still first: the only live defect |
| 2 | [`0077`](0077-ruling.md) §6 — `reportlab` into `requirements-dev.txt` | **GREEN** |
| 3 | [`0077`](0077-ruling.md) §3 — the missing differential | **GREEN**, one revert |
| 4 | [`0077`](0077-ruling.md) §5 — the `_stdt.py` leaf, lazy | **GREEN** |
| 5 | [`0077`](0077-ruling.md) §6 — the corrupt-settings-file path | **GREEN** |
| 6 | **§1 — materialisation** | **GREEN, unblocked** |
| 7 | **§2 — `SETTINGS_VERSION`, the migration table, the pin test** | **GREEN, and it lands WITH item 6, never after** |
| 8 | The read-back ([`0074`](0074-ruling.md) §6 item 0) and everything AMBER | unchanged, still owed |

**Items 6 and 7 are one commit.** A materialised file shipped without the
version guard is the pinning trap with a marker on it that nothing enforces —
**and by the time it matters, every user already has the file.**

**No new manual check.** [`0075`](0075-ruling.md) §6's third question already
covers this ground; the file's contents are visible to Patrick the moment he
opens it.

**`0066` — item C — remains reserved and unwritten, no promise attached
([`0070`](0070-ruling.md) §8).**
