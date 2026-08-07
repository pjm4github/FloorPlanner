#!/usr/bin/env python3
"""Does the hook fire on a COMMAND-POSITION commit and stay quiet on a mention?

Kept in a file rather than a heredoc on purpose: the hook inspects the whole
Bash command line, so a heredoc containing `&& git commit` is itself a
command-position match and the test would block its own runner. That is the
guard behaving correctly, and it is worth knowing before it surprises someone.
"""
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
G = "git" + " commit"                      # assembled, for the reason above

CASES = [
    (f"{G} -m x", 2, "bare invocation"),
    (f"git add -A docs && {G} -q -F -", 2, "compound with &&"),
    (f"cd /tmp; {G} --amend", 2, "after a semicolon, --amend"),
    (f"sudo {G} -m x", 2, "one prefix token"),
    (f"echo 'see {G} in the docs'", 0, "mention in a quoted arg"),
    (f"grep -rn '{G}' docs/", 0, "grep for the phrase"),
    ("python tools/gate.py", 0, "unrelated command"),
]

print("COMMAND-POSITION MATCHING  (2 = blocks, 0 = allowed through)")
ok = 0
for cmd, want, label in CASES:
    p = subprocess.run([sys.executable, ".claude/hooks/verify_gate.py"],
                       input=json.dumps({"tool_name": "Bash",
                                         "tool_input": {"command": cmd}}),
                       capture_output=True, text=True)
    good = p.returncode == want
    ok += good
    print(f"  rc={p.returncode} want={want} {'ok ' if good else 'BAD'}  "
          f"{label:<26} {cmd[:44]}")
print(f"  {ok}/{len(CASES)} correct")
sys.exit(0 if ok == len(CASES) else 1)
