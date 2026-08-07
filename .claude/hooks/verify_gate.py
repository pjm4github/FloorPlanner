#!/usr/bin/env python3
"""PreToolUse hook: refuse `git commit` unless a FRESH GREEN gate is on disk.

THE ENFORCEMENT HALF OF "a green signal is only evidence about what it
measures". The gate has always measured the right thing. Nothing has ever made
running it unskippable, and there are four incidents behind that gap:

  * a gate line transcribed into a commit message WITHOUT its ", 2 errors", so
    the message read green while the run was red (3cdf046);
  * "515 collected" quoted in a report written after two more tests landed;
  * "516 collected" quoted the same way, with a reconciliation ASSERTED against
    it that was never performed -- 512 + 6 is 518;
  * a commit whose trailer was correct for an earlier state of the tree.

THREE OF THOSE FOUR WERE A CLAIM ABOUT A GATE RATHER THAN A GATE. So this hook
reads THE RESULT FILE and never the commit message. A message can say anything;
`.gate-result.json` is written by `tools/gate.py` itself, at the end of a
full-mode run, from the numbers it just computed.

Three conditions, and the third is the one that matters:

  1. `.gate-result.json` EXISTS          -- you ran the gate at all
  2. its verdict is GREEN                -- and it passed
  3. it is NEWER THAN EVERY TRACKED FILE -- and it passed on THIS tree

Without (3) the hook is theatre: a green result from an hour and six edits ago
would wave through exactly the fourth incident. It is also the condition most
likely to be silently broken, which is why the fail-first receipt for this hook
tests it explicitly by touching a source file and retrying.

Exit codes: 0 lets the command through, 2 blocks it and shows stderr to the
model. Any other failure mode here (unreadable JSON, no git) also blocks, on the
principle that a guard which cannot verify must not approve.

WHAT THIS CANNOT SEE, stated here because an unstated boundary reads as
coverage -- and this one was found by testing the hook rather than by reasoning
about it:

  * A COMMAND THAT EDITS TRACKED FILES AND THEN COMMITS, IN ONE INVOCATION, is
    not covered by the freshness check. `PreToolUse` fires BEFORE the command
    runs, so the tree the hook inspects is the tree as it was at approval time.
    A single Bash call that touches a source file and then commits will be
    approved against the pre-edit state -- measured, by exactly that command
    landing an empty commit while the guard watched. Splitting edit and commit
    into separate calls (the normal working shape) is fully covered.

    THE MOST COMMON SHAPE OF THIS IS NOW BLOCKED OUTRIGHT: a command containing
    BOTH a gate invocation and a commit. See `GATE_RUN_RE` below. It does not
    close the general case -- nothing at PreToolUse can -- but it closes the one
    that actually happens, which was writing this very boundary note and then
    walking into it within the hour.
  * `xargs`-fed commits, shell aliases, and any commit made outside these
    tools.
  * WHETHER THE COMMIT MESSAGE DESCRIBES THE RUN. This hook closes exactly one
    question -- *did the gate run, green, on this tree* -- and it never reads
    the message. A message can quote a trailer that is wrong, or invented, or
    from an earlier run, and this will approve it. That second question is
    closed by `python tools/gate.py --trailer`, which reprints the stored block
    for redirection into the message file so the numbers never pass through a
    human. It went unclosed until 2026-08-07, behind two instruments that were
    both working correctly.

It raises the floor. It is not a sandbox, and treating it as one is the failure
mode it exists to prevent.
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULT = os.path.join(ROOT, ".gate-result.json")
GATE_CMD = "python tools/gate.py"

# `git commit` in a COMMAND POSITION: at the start of a line, or after a shell
# separator, optionally behind one prefix token (`sudo git commit`). MULTILINE
# so a heredoc-bearing command still anchors per line. See the note at the call
# site for what this deliberately misses.
COMMIT_RE = re.compile(r"(?:^|[;&|])\s*(?:\S+\s+)?git\s+commit\b", re.M)

# A RUN OF THE GATE, in the same command line as a commit.
#
# Why this is enforced rather than left to discipline: `PreToolUse` fires BEFORE
# the command runs, so when one call does `gate.py` and then commits, the hook
# judges the tree AS IT WAS BEFORE THE GATE EVEN RAN. The verdict it reads is
# the PREVIOUS run's. On 2026-08-07 that let a commit through on a RED gate --
# in the same session, and within the hour, as the note above documenting the
# hole was written. Three times that session a rule was written and then broken
# by its author; the answer to that is a check, not more resolve.
#
# Deliberately matches the TOOL, not the word "gate": `tools/gate.py` in any
# spelling (`python tools/gate.py`, `py -m ...`, a bare path), which is the only
# thing that writes the result file the commit is about to be judged against.
GATE_RUN_RE = re.compile(r"tools[/\\]gate\.py")


def block(msg):
    sys.stderr.write(f"BLOCKED: {msg}\n")
    sys.exit(2)


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        sys.exit(0)                    # not a hook invocation we understand

    cmd = ""
    ti = payload.get("tool_input") or {}
    if isinstance(ti, dict):
        cmd = str(ti.get("command") or "")

    # Only commits are gated, and only ACTUAL INVOCATIONS of one.
    #
    # The first draft matched the substring anywhere in the command line and
    # blocked the very command that was validating it -- an `echo` whose
    # argument merely CONTAINED the words. `grep "git commit" docs/` would have
    # been blocked too, and this repo's documents are full of the phrase. So the
    # match is anchored to a command position. That still catches every form
    # used here -- `git add -A && git commit ...`, `git commit <paths> -F -` fed
    # by a heredoc, `cd x; git commit` -- while a mention inside a quoted
    # argument is not an invocation and is not treated as one.
    #
    # `--amend` is a commit and is not exempt. Deliberately NOT handled:
    # `xargs git commit`, shell aliases, and a commit made outside these tools.
    # This hook raises the floor; it is not a sandbox, and saying so is the
    # point -- an unstated boundary reads as coverage.
    if not COMMIT_RE.search(cmd):
        sys.exit(0)

    # ONE CALL CANNOT BOTH RUN THE GATE AND COMMIT. Checked before the result
    # file is even read, because in this shape the result file is guaranteed to
    # be the WRONG one: this hook runs before the command, so it would be
    # judging the previous run's verdict against the pre-command tree, and
    # whatever the gate is about to say would never be consulted at all.
    if GATE_RUN_RE.search(cmd):
        block("this command runs the gate AND commits.\n"
              "         PreToolUse fires BEFORE the command, so the verdict "
              "checked here is the\n"
              "         PREVIOUS run's -- the gate you are about to run cannot "
              "affect it. On\n"
              "         2026-08-07 exactly this let a commit through on a RED "
              "gate.\n"
              "         Run the gate and commit in SEPARATE calls: read the "
              "verdict, then commit.")

    if not os.path.exists(RESULT):
        block(f"no {os.path.basename(RESULT)} -- the gate has not been run.\n"
              f"         Run `{GATE_CMD}` and commit after it reports GREEN.")

    try:
        with open(RESULT, encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError) as e:
        block(f"{os.path.basename(RESULT)} is unreadable ({e}).\n"
              f"         Re-run `{GATE_CMD}`.")

    verdict = str(data.get("verdict", "")).upper()
    if verdict != "GREEN":
        trailer = [ln for ln in (data.get("trailer") or [])
                   if "RED" in ln or "UNRECONCILED" in ln]
        detail = ("\n         " + "\n         ".join(trailer)) if trailer else ""
        block(f"the last full-mode gate was {verdict or 'not GREEN'}."
              f"{detail}\n         Fix it, re-run `{GATE_CMD}`, then commit.")

    # (3) FRESHNESS. The result must post-date every tracked file, or it is a
    # verdict about a tree that no longer exists.
    try:
        listing = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                                 capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        block(f"cannot list tracked files to check gate freshness ({e}).")

    stamp = os.path.getmtime(RESULT)
    newer = []
    for rel in listing.decode("utf-8", "replace").split("\0"):
        if not rel:
            continue
        try:
            if os.path.getmtime(os.path.join(ROOT, rel)) > stamp:
                newer.append(rel)
        except OSError:
            continue                   # deleted-but-tracked: not a staleness signal

    if newer:
        age = (time.time() - stamp) / 60
        shown = ", ".join(sorted(newer)[:5])
        more = f" (+{len(newer) - 5} more)" if len(newer) > 5 else ""
        block(f"the gate result is STALE -- {len(newer)} tracked file(s) have "
              f"changed since it was written {age:.1f} min ago:\n"
              f"         {shown}{more}\n"
              f"         A green gate for an earlier tree is not a green gate "
              f"for this one.\n         Re-run `{GATE_CMD}`, then commit.")

    sys.exit(0)


if __name__ == "__main__":
    main()
