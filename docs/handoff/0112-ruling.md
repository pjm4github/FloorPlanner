# 0112 — ruling: gitignore `plans.pdf` — and [`0111`](0111-ruling.md) §2's second half is withdrawn

**Patrick:** *"add the plans.pdf to git ignore. thats a cli test artifact."*

---

## 1. THE SUITE IS ALREADY CLEAN — I was wrong

[`0111`](0111-ruling.md) §2 said *"a test that exercises the CLI without `-o`
writes a PDF into the source tree … same class as D72"* and asked for a fix.

**Measured, `tests/test_fp2pdf.py:197`:**

```python
def test_main_round_trips_a_design_via_the_cli(tmp_path):
    out_path = tmp_path / "out.pdf"
    fp2pdf.main([str(design_path), "-o", str(out_path), …])
```

**It already passes `-o` into `tmp_path`. The test writes nothing into the
repo.** **Eighth time this run that I have asserted a mechanism without reading
it** — and the file I named was three lines from the one I quoted.

**[`0111`](0111-ruling.md) §2's second half is withdrawn. Nothing in the tests
changes.**

## 2. GITIGNORE IT ANYWAY — for the OTHER reason

**`fp2pdf.py:624` defaults `--out` to `Path("plans.pdf")`** — relative to the
current directory. **So anyone running the exporter from inside the checkout
drops one there**, which is exactly how this one arrived: **a hand-run of the
CLI during development, not the suite.**

> **The reason matters because it does not go away.** A test can be fixed once;
> **a CLI default is permanent, and the repo is where it will be run.**

**Add to `.gitignore`, with the reason on the line above it** — the file's own
convention, which every existing entry follows:

```
# fp2pdf's CLI defaults --out to "plans.pdf" relative to the cwd, so a hand-run
# from inside the checkout drops one here. Never a source file.
plans.pdf
```

**Delete the 28 KB one currently in `floorplanner/export/`.**

## 3. TIER

**GREEN.** One ignore line and one deletion. **Folded into
[`0111`](0111-ruling.md) §3's pre-session cleanup — not its own commit.**
