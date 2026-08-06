#!/usr/bin/env python3
"""FAIL-FIRST RECEIPT for `tools/gate.py --docs`.

Break one thing at a time, PROVE the break actually landed on disk, run the
gate, restore, and prove the restore landed too. A red that was never caused by
the mutation you think you made is the failure this dance exists to prevent --
"verify that a probe actually landed" is a standing rule here for that reason.
"""
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
ROOT = pathlib.Path(".").resolve()
REC = ROOT / "docs/defects/0023-a-group-move-strands-the-region-of.md"
IDX = ROOT / "docs/defects/INDEX.md"
RDM = ROOT / "docs/defects/README.md"

# Assembled, never written out: this file is scanned by the very audit it
# exercises, and a literal reference to a record that does not exist would
# make the gate red on the probe rather than on the thing being probed.
DANGLING = "defect " + "99"


def gate():
    p = subprocess.run([sys.executable, "tools/gate.py", "--docs"],
                       capture_output=True, text=True, errors="replace")
    line = next((ln for ln in p.stdout.splitlines()
                 if ln.startswith(("Docs-Verdict", "Ref-Strict"))
                 and "Verdict" in ln), "<no verdict>")
    why = next((ln.strip() for ln in p.stdout.splitlines()
                if "resolve to no record" in ln or "MALFORMED" in ln
                or "DIFFERS" in ln
                or (".md:" in ln and "->" not in ln)), "")
    return p.returncode, line, why


CASES = [
    ("1  front matter malformed", REC,
     lambda t: t.replace("---\n# permanent key", "# permanent key", 1),
     lambda t: not t.startswith("---")),
    ("2  illegal state/state_reason", REC,
     lambda t: t.replace("state_reason: completed", "state_reason: null", 1),
     "state_reason"),
    ("3  label outside the taxonomy", REC,
     lambda t: t.replace("  - area:groups", "  - area:plumbing", 1),
     "area:plumbing"),
    ("4  milestone not in the Status table", REC,
     lambda t: t.replace("milestone: P4.5", "milestone: P9.9", 1),
     "milestone: P9.9"),
    ("5  title over the length limit", REC,
     lambda t: t.replace('title: "A group move strands',
                         'title: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
                         'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA A group '
                         'move strands', 1),
     "AAAAAAAA"),
    ("6  closed_by names no commit", REC,
     lambda t: t.replace("closed_by: null", "closed_by: deadbee", 1),
     "closed_by: deadbee"),
    ("7  a defect reference resolving to nothing", RDM,
     lambda t: t + "\n<!-- probe: " + DANGLING + " does not exist -->\n",
     DANGLING),
    ("8  INDEX.md differs from a regeneration", IDX,
     lambda t: t.replace("**50 records**", "**51 records**", 1),
     "**51 records**"),
]

print("FAIL-FIRST RECEIPT -- tools/gate.py --docs")
print("Each row: break it, verify the break is ON DISK, run the gate, restore.\n")
rc, line, _ = gate()
print(f"  BASELINE                                  rc={rc}  {line}\n")
if rc:
    print("  baseline is not green; aborting")
    sys.exit(1)

fails = 0
for name, path, mutate, marker in CASES:
    original = path.read_bytes()
    text = original.decode("utf-8")
    broken = mutate(text)
    if broken == text:
        print(f"  {name:<42} PROBE DID NOT APPLY -- pattern not found")
        fails += 1
        continue
    path.write_bytes(broken.encode("utf-8"))
    # PROVE the mutation is on disk before believing anything about the result
    now = path.read_text(encoding="utf-8")
    on_disk = marker(now) if callable(marker) else (marker in now)
    changed = path.read_bytes() != original
    rc, line, why = gate()
    path.write_bytes(original)
    restored = path.read_bytes() == original
    ok = on_disk and changed and rc != 0 and restored
    fails += not ok
    print(f"  {name:<42} probe={'ON DISK' if on_disk else 'MISSING'}  "
          f"rc={rc}  {'RED  ' if rc else 'GREEN'}  "
          f"restored={'yes' if restored else 'NO'}")
    if why:
        print(f"       -> {why[:110]}")

rc, line, _ = gate()
print(f"\n  RESTORED                                  rc={rc}  {line}")
print(f"\n  {len(CASES)} probes, {len(CASES) - fails} behaved as required, "
      f"{fails} did not")
sys.exit(1 if fails or rc else 0)
