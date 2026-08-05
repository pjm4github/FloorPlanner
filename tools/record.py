#!/usr/bin/env python3
"""Apply an anchored edit to a record file, and PROVE it landed.

Why this exists, and it is not convenience. Three times in one phase an
instrument silently did nothing and was trusted because something else was
green:

  * a fail-first probe whose pattern did not match (the file is CRLF on disk),
    which exited 0 and reported success while changing no bytes;
  * a plan edit whose script used `if anchor in s:` and skipped silently;
  * a plan edit whose script RAISED, and was committed through anyway because
    `tools/gate.py` was green.

The last is the worst shape: a correct check overridden by an unrelated green.
`gate.py` has never made a claim about `docs/*.md` -- it runs the tests, and the
tests do not read them. That is not a bug in the gate; it is the boundary of
what its green means.

So the edit and its verification stop being two steps a human connects: this
applies the change, re-reads the file from disk, confirms the new text is
present, and EXITS NON-ZERO if it is not. Then "the sequence is green" can mean
both artifacts.

    from tools.record import edit
    edit("docs/V5_MIGRATION_PLAN.md", anchor=OLD, new=NEW)          # replace
    edit("docs/CODE_REVIEW_v2.md", anchor=ROW, new=NEW, mode="before")

    python tools/record.py --verify docs/V5_MIGRATION_PLAN.md "some added text"
"""
import sys


class RecordEditError(RuntimeError):
    """An anchored edit did not apply, or did not verify after writing."""


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def edit(path, anchor, new, mode="replace", verify=None, count=1):
    """Apply an anchored edit and verify it landed. Raises on any doubt.

    `mode`: "replace" (anchor -> new), "before"/"after" (new goes either side
    of the anchor, which stays). `verify` defaults to `new` -- pass something
    shorter when `new` is reformatted on the way in.

    LINE ENDINGS ARE THE FILE'S, not the caller's: `new` is normalised to LF
    and then converted once to whatever the file uses. Doing that conversion
    twice is what produced a CRCRLF file and an 8,988-line phantom diff, so it
    happens here, once, where it can be got right for everyone."""
    s = _read(path)
    nl = "\r\n" if "\r\n" in s else "\n"
    if "\r\r\n" in s:
        raise RecordEditError(f"{path}: file already contains CRCRLF")

    def fit(t):
        t = t.replace("\r\n", "\n")
        return t.replace("\n", nl) if nl == "\r\n" else t

    a, n = fit(anchor), fit(new)
    found = s.count(a)
    if found != count:
        raise RecordEditError(
            f"{path}: anchor found {found} time(s), expected {count}. "
            f"Anchor began: {anchor[:70]!r}")
    if mode == "replace":
        out = s.replace(a, n, count)
    elif mode == "before":
        out = s.replace(a, n + a, count)
    elif mode == "after":
        out = s.replace(a, a + n, count)
    else:
        raise RecordEditError(f"unknown mode {mode!r}")
    _write(path, out)

    # ...and PROVE it, from disk, not from the string we think we wrote
    back = _read(path)
    want = fit(verify if verify is not None else new).strip()
    if want and want.splitlines()[0] not in back:
        raise RecordEditError(f"{path}: wrote the edit but cannot find it "
                              f"afterwards -- nothing was recorded")
    if "\r\r\n" in back:
        raise RecordEditError(f"{path}: the edit introduced CRCRLF")
    return True


def verify(path, *texts):
    """True if every `texts` is present; raises listing whatever is missing."""
    s = _read(path).replace("\r\n", "\n")
    missing = [t for t in texts if t.replace("\r\n", "\n") not in s]
    if missing:
        raise RecordEditError(
            f"{path}: MISSING {len(missing)} of {len(texts)}: "
            + "; ".join(repr(m[:60]) for m in missing))
    return True


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "--verify" or len(argv) < 3:
        print(__doc__)
        return 2
    try:
        verify(argv[1], *argv[2:])
    except RecordEditError as exc:
        print(f"Record-Verify: RED -- {exc}")
        return 1
    print(f"Record-Verify: GREEN -- {len(argv) - 2} text(s) present "
          f"in {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
