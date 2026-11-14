"""The STAIRS parametric kind: its parameters, its validation, its summary.

The arithmetic is `stair_geometry.py` (shared with the 3D viewer); this file
is everything about stairs that the viewer does not need -- what may be
edited, what counts as acceptable, and how the result is described.
"""
from floorplanner.parametric import stair_geometry as sg
from floorplanner.parametric.findings import (
    ADVISORY, ERROR, NOT_EVALUATED, PASS, WARNING, Finding)
from floorplanner.parametric.params import ENUM, FLOAT, INT, ParamSpec
from floorplanner.parametric.registry import ParametricKind, register

_TOL = 1e-9

_TURN_LABELS = {0: "None", 90: "+90° (left)", -90: "−90° (right)",
                180: "+180° (left U)", -180: "−180° (right U)"}


def _turn_choices(values):
    kind = values.get("type") if values.get("type") in sg.TURNS else "straight"
    return tuple((t, _TURN_LABELS[t]) for t in sg.TURNS[kind])


def _fmt(x, places=3):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def _ctx(context):
    context = context or {}
    elevs = context.get("elevations") or {}
    values = list(elevs.values()) if isinstance(elevs, dict) else list(elevs)
    return float(context.get("this_elev", 0.0) or 0.0), values


def to_floor_name(context):
    """The name of the level a LINKED stair rises to, or None."""
    this_elev, _ = _ctx(context)
    elevs = (context or {}).get("elevations") or {}
    if not isinstance(elevs, dict):
        return None
    best = None
    for name, e in elevs.items():
        gap = float(e) - this_elev
        if gap > 1e-6 and (best is None or gap < best[0]):
            best = (gap, name)
    return best[1] if best else None


def validate_stairway(inputs, geometry, code_profile, building_context=None):
    """The findings for one calculated stair (spec sec 6).

    `building_context` is where headroom, landings and handrails would be
    measured from. Nothing supplies it yet, so those three are reported
    NOT_EVALUATED -- which is a statement that they were not checked, and is
    never rendered as a pass."""
    p = code_profile
    g = geometry
    out = []
    h, d, W = g.riser_height, g.tread_depth, g.stair_width

    if g.riser_count < 2 or g.tread_count < 1:
        out.append(Finding(
            "stair.degenerate", ERROR,
            f"{g.riser_count} riser(s) and {g.tread_count} tread(s) is not a "
            f"stair this furnishing can draw. Increase the rise or the riser "
            f"count" + (", or lower/raise the landing." if g.landing else "."),
            actual=g.riser_count, limit=2, field="riser_count"))

    if h > p.max_riser_in + _TOL:
        need = sg.auto_riser_count(g.total_rise, p.max_riser_in)
        out.append(Finding(
            "riser.max_height", ERROR,
            f"Riser height {_fmt(h)} in exceeds the {_fmt(p.max_riser_in)} in "
            f"maximum. Use at least {need} risers.",
            actual=h, limit=p.max_riser_in, field="riser_count"))
    else:
        out.append(Finding("riser.max_height", PASS,
                           f"Riser height {_fmt(h)} in is within the "
                           f"{_fmt(p.max_riser_in)} in maximum.",
                           actual=h, limit=p.max_riser_in))

    if d < p.min_tread_in - _TOL:
        out.append(Finding(
            "tread.min_depth", ERROR,
            f"Tread depth {_fmt(d)} in is below the {_fmt(p.min_tread_in)} in "
            f"minimum.", actual=d, limit=p.min_tread_in, field="tread_depth_in"))
    else:
        out.append(Finding("tread.min_depth", PASS,
                           f"Tread depth {_fmt(d)} in meets the "
                           f"{_fmt(p.min_tread_in)} in minimum.",
                           actual=d, limit=p.min_tread_in))

    if W < p.min_width_in - _TOL:
        out.append(Finding(
            "width.min_nominal", ERROR,
            f"Stair width {_fmt(W)} in is below the {_fmt(p.min_width_in)} in "
            f"nominal minimum.", actual=W, limit=p.min_width_in,
            field="stair_width_in"))
    else:
        out.append(Finding("width.min_nominal", PASS,
                           f"Nominal width {_fmt(W)} in meets the "
                           f"{_fmt(p.min_width_in)} in minimum (clear width "
                           f"between handrails is not checked).",
                           actual=W, limit=p.min_width_in))

    # every riser of one stair is H / N here, so the modelled variation is 0
    out.append(Finding("riser.uniformity", PASS,
                       "All risers are equal in this model (variation 0 in; "
                       f"limit {_fmt(p.max_riser_variation_in)} in). As-built "
                       "variation is a site check.",
                       actual=0.0, limit=p.max_riser_variation_in))

    tallest = max((f.risers * h for f in g.flights), default=0.0)
    if tallest > p.max_flight_rise_in + _TOL:
        out.append(Finding(
            "flight.max_rise", WARNING,
            f"One flight rises {_fmt(tallest)} in without a landing; the "
            f"profile's limit between landings is {_fmt(p.max_flight_rise_in)} "
            f"in. Add a landing, or confirm the adopted code edition.",
            actual=tallest, limit=p.max_flight_rise_in, field="type"))

    if g.landing is not None:
        if W >= p.min_width_in - _TOL:
            out.append(Finding(
                "landing.intermediate", PASS,
                f"The intermediate landing is {_fmt(g.landing[2])} x "
                f"{_fmt(g.landing[3])} in, at least the stair width in the "
                f"direction of travel.", actual=W, limit=p.min_width_in))
        want = inputs.landing_height
        if want is not None and abs(want - g.landing_height) > 0.01:
            out.append(Finding(
                "landing.snapped", ADVISORY,
                f"Landing drawn at {_fmt(g.landing_height)} in "
                f"({g.landing_risers} risers up); {_fmt(want)} in is not a "
                f"whole number of {_fmt(h)} in risers.",
                actual=g.landing_height, limit=want, field="landing_height_in"))

    ci = g.comfort_index
    if ci < p.comfort_lo_in - _TOL or ci > p.comfort_hi_in + _TOL:
        out.append(Finding(
            "comfort.2r_plus_t", ADVISORY,
            f"2 x riser + tread = {_fmt(ci, 2)} in, outside the "
            f"{_fmt(p.comfort_lo_in)}-{_fmt(p.comfort_hi_in)} in comfort "
            f"range. A guideline, not a code limit.", actual=ci))
    else:
        out.append(Finding("comfort.2r_plus_t", PASS,
                           f"2 x riser + tread = {_fmt(ci, 2)} in, inside the "
                           f"comfort range.", actual=ci))

    measured = building_context or {}
    for rule, text in (
            ("headroom.min", f"Headroom ({_fmt(p.min_headroom_in)} in minimum "
                             f"above the nosing line) is not checked: the "
                             f"construction over the stair is not measured."),
            ("landing.top_bottom", "Top and bottom landings, and door swings "
                                   "onto them, are not checked."),
            ("handrail.guard", "Handrails, guards and clear width between "
                               "them are not modelled.")):
        if rule not in measured:
            out.append(Finding(rule, NOT_EVALUATED, text))
    out.append(Finding(
        "code.profile", WARNING,
        f"Checked against \"{p.title}\". These are preliminary defaults, not "
        f"a determination for your jurisdiction."))
    return out


class StairsKind(ParametricKind):
    kind = "stairs"
    title = "Stairway Properties"

    def specs(self):
        d = sg.STATE_DEFAULTS
        return [
            ParamSpec("type", "Type", ENUM, d["type"],
                      choices=(("straight", "Straight"), ("L", "L (one 90° turn)"),
                               ("U", "U (one 180° turn)")),
                      tooltip="Straight flight, or two flights about one landing."),
            ParamSpec("turn_deg", "Turn", ENUM, d["turn_deg"],
                      choices_fn=_turn_choices,
                      enabled_fn=lambda v: v.get("type") != "straight",
                      tooltip="Which way the stair turns at its landing, as "
                              "walked going up."),
            ParamSpec("direction", "Arrow", ENUM, d["direction"],
                      choices=(("up", "Up"), ("down", "Down")),
                      tooltip="The travel arrow drawn on the plan."),
            ParamSpec("rise_mode", "Rise", ENUM, d["rise_mode"],
                      choices=(("linked", "Linked to the level above"),
                               ("detached", "Detached (typed in)")),
                      tooltip="Linked: the rise follows the floor levels. "
                              "Detached: the rise is the number below."),
            ParamSpec("total_rise_in", "Total rise", FLOAT, d["total_rise_in"],
                      unit="in", minimum=1.0, maximum=600.0, step=0.5,
                      enabled_fn=lambda v: v.get("rise_mode") == "detached",
                      shown_fn=lambda v, g, c: None if g is None else g.total_rise,
                      tooltip="Finished floor to finished floor."),
            ParamSpec("tread_depth_in", "Tread depth", FLOAT, d["tread_depth_in"],
                      unit="in", minimum=1.0, maximum=48.0, step=0.25,
                      tooltip="Nosing to nosing, along the direction of travel."),
            ParamSpec("stair_width_in", "Stair width", FLOAT, d["stair_width_in"],
                      unit="in", minimum=6.0, maximum=240.0, step=1.0,
                      tooltip="Nominal width across the stair."),
            ParamSpec("riser_count_mode", "Riser count", ENUM, d["riser_count_mode"],
                      choices=(("auto", "Auto (fewest that fit)"),
                               ("manual", "Manual"))),
            ParamSpec("riser_count", "Risers", INT, d["riser_count"],
                      minimum=1, maximum=200, step=1,
                      enabled_fn=lambda v: v.get("riser_count_mode") == "manual",
                      shown_fn=lambda v, g, c: None if g is None else g.riser_count),
            ParamSpec("landing_mode", "Landing", ENUM, d["landing_mode"],
                      choices=(("half", "Half way between floors"),
                               ("custom", "At a set height")),
                      enabled_fn=lambda v: v.get("type") != "straight"),
            ParamSpec("landing_height_in", "Landing height", FLOAT,
                      d["landing_height_in"], unit="in", minimum=0.0,
                      maximum=600.0, step=1.0,
                      enabled_fn=lambda v: (v.get("type") != "straight"
                                            and v.get("landing_mode") == "custom"),
                      shown_fn=lambda v, g, c: (None if g is None
                                                else g.landing_height),
                      tooltip="Height of the landing above the lower floor. It "
                              "snaps to a whole number of risers."),
        ]

    def normalize(self, state):
        return sg.normalize_state(state)

    def evaluate(self, values, context):
        st = sg.normalize_state(values)
        this_elev, elevs = _ctx(context)
        rise, linked_ok = sg.effective_rise(st, this_elev, elevs)
        profile = sg.profile_for(st)
        findings = []
        if st["rise_mode"] == "linked":
            if linked_ok:
                if rise <= 0:
                    findings.append(Finding(
                        "rise.linked", ERROR, "The level above is not higher "
                        "than this one.", actual=rise, limit=0.0, field="rise_mode"))
            else:
                findings.append(Finding(
                    "rise.unlinked", WARNING,
                    f"No level stands above this one, so the stair uses its "
                    f"stored rise of {_fmt(rise)} in. Add the upper level, or "
                    f"switch to a detached rise.", actual=rise, field="rise_mode"))
        inputs = sg.inputs_from_state(st, rise)
        try:
            geom = sg.calculate_stair_geometry(inputs, profile.max_riser_in)
        except sg.StairError as exc:
            findings.append(Finding("input.invalid", ERROR, str(exc),
                                    field=exc.field))
            return None, findings
        findings += validate_stairway(inputs, geom, profile,
                                      (context or {}).get("building"))
        return geom, findings

    def summary(self, values, derived, context):
        g = derived
        rows = [("From floor", str((context or {}).get("this_floor") or "—"))]
        if values.get("rise_mode") == "linked":
            rows.append(("To floor", to_floor_name(context) or "none above"))
        else:
            rows.append(("To floor", "detached"))
        if g is None:
            return rows + [("Result", "cannot be calculated")]
        rows += [
            ("Risers", f"{g.riser_count} @ {_fmt(g.riser_height)} in"),
            ("Treads", f"{g.tread_count} @ {_fmt(g.tread_depth)} in"),
            ("Total rise", f"{_fmt(g.total_rise)} in"),
            ("Run", f"{_fmt(g.total_run)} in"
                    + ("" if g.landing is None else " (flights, less the landing)")),
            ("Pitch", f"{g.pitch_degrees:.1f}°"),
        ]
        if g.landing is not None:
            rows.append(("Landing", f"{_fmt(g.landing_height)} in up "
                                    f"({g.landing_risers} risers), "
                                    f"{_fmt(g.landing[2])} x {_fmt(g.landing[3])} in"))
        rows += [("Footprint", f"{_fmt(g.footprint_length)} x "
                               f"{_fmt(g.footprint_width)} in"),
                 ("2 x riser + tread", f"{_fmt(g.comfort_index, 2)} in")]
        return rows

    def make_preview(self, parent=None):
        from floorplanner.parametric.stair_view import StairPreview  # late: Qt
        return StairPreview(parent)


STAIRS = register(StairsKind())
