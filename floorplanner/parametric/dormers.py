"""The DORMER parametric kind (0352, phase 1): its parameters, what its
dialog reports, and its findings. The arithmetic is `dormer_geometry.py`.

NOT REGISTERED YET. `DORMER` is built here and `register()`-ed in phase 2,
with the item and the catalog entry, so that nothing in the app offers a
dormer furnishing before one can be drawn.

`context` (all optional) is what the item knows about where it stands:

    ceiling_in         the ceiling of the room it is over, above this level
    host_z_face_in     the host roof's height at the dormer's face, this
                       level's datum; absent = it is over no roof
    host_slope         the host's rise per inch along the dormer's ridge
    host_ridge_in      the host's ridge height, this level's datum
"""
from floorplanner.parametric import dormer_geometry as dg
from floorplanner.parametric.findings import ADVISORY, ERROR, WARNING, Finding
from floorplanner.parametric.params import BOOL, ENUM, FLOAT, ParamSpec
from floorplanner.parametric.registry import ParametricKind


def _fmt(x, places=2):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def _gable(values):
    return values.get("form") != "shed"


def _free_right(values):
    return _gable(values) and not values.get("symmetric")


def _host(context):
    c = context or {}
    try:
        return float(c["host_z_face_in"]), float(c["host_slope"])
    except (KeyError, TypeError, ValueError):
        return None, None


def _ceiling(context):
    try:
        return float((context or {}).get("ceiling_in"))
    except (TypeError, ValueError):
        return None


class DormerKind(ParametricKind):
    kind = "dormer"
    title = "Dormer Properties"

    def specs(self):
        d = dg.STATE_DEFAULTS

        def size(key, label, lo, hi, step=1.0, tip="", enabled=None):
            return ParamSpec(key, label, FLOAT, d[key], unit="in", minimum=lo,
                             maximum=hi, step=step, tooltip=tip,
                             enabled_fn=enabled)

        return [
            ParamSpec("form", "Form", ENUM, d["form"],
                      choices=(("gable", "Gable"), ("shed", "Shed")),
                      tooltip="A shed has one plane: the ridge is its high "
                              "edge and it falls to the left."),
            ParamSpec("symmetric", "Symmetric", BOOL, d["symmetric"],
                      enabled_fn=_gable,
                      tooltip="The right side takes the left side's numbers."),
            size("span_left_in", "Half-width, left", dg.MIN_SPAN_IN, 480.0,
                 tip="Ridge to the eaves line (knob B / G)."),
            size("span_right_in", "Half-width, right", dg.MIN_SPAN_IN, 480.0,
                 enabled=_free_right),
            size("eaves_h_in", "Eaves height", 0.0, 360.0, 0.5,
                 "The eaves line above THIS level's floor."),
            ParamSpec("pitch_12", "Pitch", FLOAT, d["pitch_12"], unit="in 12",
                      minimum=0.5, maximum=24.0, step=0.5,
                      tooltip="Rise per 12 in of run, on the left plane."),
            size("eave_overhang_left_in", "Eave overhang, left", 0.0, 60.0,
                 tip="Knob E."),
            size("eave_overhang_right_in", "Eave overhang, right", 0.0, 60.0,
                 enabled=_free_right),
            size("face_overhang_in", "Face overhang", 0.0, 60.0,
                 tip="The rake past the face (knob F)."),
            size("guide_left_in", "Side guide, left", 0.0, 480.0,
                 tip="Knob C, as a guide line only: where a side wall would "
                     "stand. 0 = on the eaves line. It draws no wall."),
            size("guide_right_in", "Side guide, right", 0.0, 480.0,
                 enabled=_free_right),
            size("depth_in", "Length off a roof", 1.0, 600.0,
                 tip="The ridge length used only when no roof is under the "
                     "dormer; on a roof the ridge runs until it meets it."),
        ]

    def normalize(self, state):
        return dg.normalize_state(state)

    def to_state(self, values):
        st = dg.normalize_state(values)
        return {k: st[k] for k in dg.STATE_DEFAULTS}

    def evaluate(self, values, context):
        st = dg.normalize_state(values)
        findings = []
        if st["pitch_12"] <= 0.0:
            findings.append(Finding("dormer.flat", ERROR,
                                    "A dormer needs a pitch above zero.",
                                    field="pitch_12"))
            return None, findings
        z_face, slope = _host(context)
        ceiling = _ceiling(context)
        rh = dg.ridge_height(st)
        depth, met = dg.ridge_depth(st, z_face, slope)
        derived = {
            "state": st, "ridge_h_in": rh, "slopes": dg.slopes(st),
            "depth_in": depth, "on_roof": met,
            "valleys": dg.valley_lines(st, z_face, slope),
            "knees": ([] if ceiling is None
                      else dg.knee_lines(st, ceiling, z_face, slope)),
            "full_height_in": (None if ceiling is None
                               else dg.full_height_width(st, ceiling)),
            "footprint": dg.footprint(st, depth), "ceiling_in": ceiling,
        }
        if z_face is None:
            findings.append(Finding(
                "dormer.no_host", WARNING,
                "This dormer is not over a roof. It is drawn "
                f"{_fmt(st['depth_in'])} in long and cuts nothing.",
                field="depth_in"))
        elif not met:
            findings.append(Finding(
                "dormer.level_host", WARNING,
                "The roof under this dormer does not rise along its ridge, so "
                "the ridge never meets it. Turn the dormer to face down the "
                "slope."))
        elif depth <= 0.0:
            findings.append(Finding(
                "dormer.buried", WARNING,
                f"The roof here is already {_fmt(z_face)} in up, at or above "
                f"this dormer's ridge ({_fmt(rh)} in). Nothing of it shows. "
                "Raise the eaves or the pitch, or move it down the slope.",
                actual=rh, limit=z_face, field="eaves_h_in"))
        host_ridge = (context or {}).get("host_ridge_in")
        if host_ridge is not None and rh > float(host_ridge) + 1e-6:
            findings.append(Finding(
                "dormer.above_host_ridge", ADVISORY,
                f"The ridge ({_fmt(rh)} in) is above the main roof's "
                f"({_fmt(float(host_ridge))} in).", actual=rh,
                limit=float(host_ridge), field="pitch_12"))
        if ceiling is not None and derived["full_height_in"] <= 0.0:
            findings.append(Finding(
                "dormer.no_full_height", ADVISORY,
                f"The ridge ({_fmt(rh)} in) is not above the {_fmt(ceiling)} in "
                "ceiling: this dormer adds no full-height floor.",
                actual=rh, limit=ceiling, field="eaves_h_in"))
        return derived, findings

    def summary(self, values, derived, context):
        if derived is None:
            return [("Result", "cannot be built")]
        st = derived["state"]
        sl, sr = derived["slopes"]
        rows = [("Ridge height", f"{_fmt(derived['ridge_h_in'])} in above this floor"),
                ("Pitch", f"{_fmt(sl * 12.0)} in 12"
                          + ("" if st["form"] == "shed" or abs(sl - sr) < 1e-9
                             else f" left, {_fmt(sr * 12.0)} in 12 right")),
                ("Ridge length", f"{_fmt(derived['depth_in'])} in"
                                 + (" (to the roof)" if derived["on_roof"]
                                    else " (not on a roof)"))]
        if derived["ceiling_in"] is not None:
            rows.append(("Full height under it",
                         f"{_fmt(derived['full_height_in'])} in wide at the "
                         f"{_fmt(derived['ceiling_in'])} in ceiling"))
            for (x, _y0), (_x, y1) in derived["knees"]:
                rows.append((f"Knee line, {'left' if x > 0 else 'right'}",
                             f"{_fmt(abs(x))} in from the ridge, "
                             f"{_fmt(y1)} in long"))
            if not derived["knees"] and derived["full_height_in"] > 0.0:
                rows.append(("Knee lines", "none: full height to both sides"))
        return rows


DORMER = DormerKind()
