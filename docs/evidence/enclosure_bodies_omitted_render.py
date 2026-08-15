"""D76 evidence, per handoff 0022-ruling.md SS3: row 1 of the enclosure-form
check (`walk_in_shower`'s bench) cannot be read from
`enclosure-form-measurement-after.png` -- the bench is real, correctly
placed, correctly sized (0021-report.md SS6's mesh dump proves it), and still
invisible, because `fp3d.py`'s viewer does not composite an opaque interior
mesh through a translucent body at any alpha tested (D76).

    python docs/evidence/enclosure_bodies_omitted_render.py

Writes `enclosure-bodies-omitted.png` beside this file. Run standalone --
`enclosure_form_measurement.py`'s own `look()` already found `--shot`'s
framebuffer grab flaky when invoked as a subprocess-of-a-subprocess under
`QT_QPA_PLATFORM=offscreen`; this script grabs its own framebuffer directly
rather than shelling out to `fp3d.py`, for the same reason.

DELIBERATELY DOES NOT SET `QT_QPA_PLATFORM=offscreen`. Measured here: under
`offscreen`, this machine's Qt cannot create a GL context at all --
`QOpenGLWidget: Failed to create context`, `grabFramebuffer()` returns a null
image, `.save()` returns `False`, and `fp3d.py --shot` prints "wrote" and
writes nothing regardless (the return value is not checked) -- a second,
sharper instance of the same "reported success and wrote nothing" shape this
module's docstring already names. The real (non-offscreen) platform opens a
window and renders through the actual display, and that succeeds. So this
needs a real desktop session; it will not run in a headless/CI shell.

THIS DOES NOT FIX THE COMPOSITING BUG (D76) AND IS NOT A VIEWER FLAG. It
calls `fp3d.build_model()` unmodified on the same
`fixtures/enclosure-form-check.json` fixture the existing measurement uses,
then -- in this script only -- drops the one mesh that is in the way:
`walk_in_shower`'s glass body (`furnishings:glass`; it is the only glass item
in this 3-item fixture, so nothing else is affected). Nothing is invented:
every remaining mesh is exactly what `build_model` built, known, present and
already measured by `enclosure_form_measurement.py`'s mesh dump. That is the
distinction 0022-ruling.md SS3 draws from the refused `--stack` option, which
would have supplied a number the document does not contain -- this hides a
part that is known, present and measured, in order to photograph another
part.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OMIT = {"furnishings:glass"}          # walk_in_shower's body only -- see module docstring


def load_fp3d():
    spec = importlib.util.spec_from_file_location(
        "fp3d_bodies_omitted", ROOT / "floorplanner" / "viewer" / "fp3d.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    fp3d = load_fp3d()
    doc_path = ROOT / "fixtures" / "enclosure-form-check.json"
    doc = json.loads(doc_path.read_text("utf-8"))
    model = fp3d.build_model(doc)

    before = sorted(m.name for m in model.meshes)
    model.meshes = [m for m in model.meshes if m.name not in OMIT]
    after = sorted(m.name for m in model.meshes)
    print(f"meshes before: {before}")
    print(f"meshes after (omitted {sorted(OMIT)}): {after}")
    assert set(before) - set(after) == OMIT, (
        "the omission did not remove exactly the intended mesh -- the "
        "fixture's material assignments may have changed; do not trust "
        "this render until that is understood")

    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv[:1])
    win = QMainWindow()
    win.setWindowTitle("D76 evidence -- walk_in_shower, body omitted")
    body = fp3d.Plan3DWidget(model)
    win.setCentralWidget(body)
    win.resize(1200, 820)
    win.show()
    for _ in range(3):
        app.processEvents()
    out = Path(__file__).resolve().parent / "enclosure-bodies-omitted.png"
    body.view.grabFramebuffer().save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
