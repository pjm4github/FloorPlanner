"""The generic properties dialog for a parametric furnishing (PyQt6).

ONE dialog for every parametric kind. The kind supplies its parameter list,
its `evaluate` and, optionally, a preview widget; this file builds the form
from the list and owns the acceptance rules, which are the same for all of
them (STAIRS_FURNISHING_SPECIFICATION.md sec 6.3):

    * an ERROR blocks OK, and focus goes to the offending field;
    * a WARNING or a NOT_EVALUATED check needs the acknowledgement box ticked;
    * Cancel changes nothing.

THE DIALOG EDITS A DRAFT. It never touches the furnishing: the caller reads
`result_state()` after `exec()` returns Accepted and applies it, so a
cancelled dialog leaves the document, and the undo stack, exactly as they
were.
"""
import re

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QGuiApplication, QValidator
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from floorplanner import config as _config
from floorplanner.parametric import findings as F
from floorplanner.parametric.params import BOOL, ENUM, FLOAT, INT


# Typing a unit in a pitch field: a "d"/"deg" suffix means degrees, anything
# else is read as rise/run -- "XXX in 12" (Patrick, 2026-11-19). Shared by the
# generic dialog (dormer) and the roof End-On dialog.
_PITCH_INPUT_RE = re.compile(
    r"^\s*([+-]?\d*\.?\d*)\s*(d|deg|deg\.|°|in|in12|in 12|/12)?\s*$", re.I)


def pitch_unit_from_text(text):
    """(unit_key, number) for a typed pitch, or (None, None) if not a number.
    `unit_key` is 'deg' when a d/deg suffix is typed, else 'in12'."""
    m = _PITCH_INPUT_RE.match(text or "")
    if m is None or m.group(1) in ("", "+", "-", "."):
        return None, None
    try:
        num = float(m.group(1))
    except (TypeError, ValueError):
        return None, None
    tok = (m.group(2) or "").lower().strip().rstrip(".")
    return ("deg" if tok in ("d", "deg", "°") else "in12"), num


class PitchSpinBox(QDoubleSpinBox):
    """A pitch spinbox that accepts a typed unit. `unitTyped(key, number)` fires
    (deferred, so the dialog may safely re-range the box) when the text carries a
    recognised unit; `textFromValue` keeps the usual suffix for display."""
    unitTyped = pyqtSignal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending = None

    def _core(self, text):
        """Drop the field's CURRENT suffix (e.g. " deg"), which Qt re-appends to
        whatever the user types, so a bare number is read in neither unit -- it
        is the typed token, if any, that decides (Patrick, 2026-11-19)."""
        s = self.suffix()
        if s and text.endswith(s):
            text = text[:-len(s)]
        return text

    def validate(self, text, pos):
        m = _PITCH_INPUT_RE.match(self._core(text))
        if m is None:
            return (QValidator.State.Invalid, text, pos)
        if m.group(1) in ("", "+", "-", "."):
            return (QValidator.State.Intermediate, text, pos)
        return (QValidator.State.Acceptable, text, pos)

    def valueFromText(self, text):
        unit, num = pitch_unit_from_text(self._core(text))
        if unit is None:
            return self.value()
        self._pending = (unit, num)
        QTimer.singleShot(0, self._emit_pending)
        return num

    def _emit_pending(self):
        if self._pending is not None:
            pend, self._pending = self._pending, None
            self.unitTyped.emit(*pend)

# Session preferences a FLOAT field's unit dropdown may remember, keyed by
# `ParamSpec.unit_setting`: (getter, setter). Flipping the unit in one dialog
# is remembered for the next (Patrick, 2026-11-19).
_UNIT_PREFS = {"pitch_units": (_config.pitch_units, _config.set_pitch_units)}

_SEVERITY_INK = {
    F.ERROR: QColor(185, 28, 28),
    F.WARNING: QColor(180, 83, 9),
    F.NOT_EVALUATED: QColor(107, 33, 168),
    F.ADVISORY: QColor(29, 78, 216),
    F.PASS: QColor(100, 116, 139),
}
_SEVERITY_WORD = {
    F.ERROR: "ERROR", F.WARNING: "WARNING", F.NOT_EVALUATED: "NOT CHECKED",
    F.ADVISORY: "ADVISORY", F.PASS: "pass",
}
# 0365 (Patrick): a WARNING / NOT_EVALUATED check is advisory -- "it's
# understood the settings are only suggestive" -- so it no longer carries an
# acknowledgement box; the dialog accepts those without a gate. The ONLY
# acknowledgement left is the buildability override below: an ERROR the user
# may keep on the plan (drawn red) to fix out there, which is a real decision,
# not a suggestion, and still needs an explicit tick.
ACK_OVERRIDE_TEXT = ("I understand this cannot be built as drawn — keep it on "
                     "the plan (drawn red) so I can fix it there")


class ParametricDialog(QDialog):
    def __init__(self, definition, state, context=None, parent=None):
        super().__init__(parent)
        self.definition = definition
        self.context = dict(context or {})
        self._specs = list(definition.specs())
        self._initial = definition.normalize(state)
        self.values = dict(self._initial)
        self._widgets = {}
        self._key_by_widget = {}
        self._edited_key = None          # the field the user changed last
        self._combo_choices = {}
        self._unit_combos = {}           # key -> the unit QComboBox (unit_modes)
        self._unit_mode = {}             # key -> the active UnitMode
        self._derived = None
        self._findings = []
        self._loading = False
        self._ack_ids = None
        self._result = None

        self.setWindowTitle(definition.title)
        self.setModal(True)
        self._build()
        self._refresh()

    # -- construction --------------------------------------------------------
    def _build(self):
        # The body (preview + parameters + validation) scrolls; the button box
        # sits OUTSIDE the scroll area so OK / Cancel / Reset are always reachable
        # even on a short screen (Patrick, 2026-11-15: the dialog opened taller
        # than the screen and the bottom buttons fell off the edge).
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        body_w = QWidget()
        scroll.setWidget(body_w)
        outer.addWidget(scroll, 1)

        body = QVBoxLayout(body_w)
        top = QHBoxLayout()
        body.addLayout(top, 1)

        self.preview = self.definition.make_preview(self)
        if self.preview is not None:
            top.addWidget(self.preview, 3)

        side = QVBoxLayout()
        top.addLayout(side, 2)

        box = QGroupBox("Controlling parameters")
        form = QFormLayout(box)
        # Tight rows so the whole list needs less height (Patrick, 2026-11-15).
        form.setVerticalSpacing(2)
        form.setContentsMargins(8, 6, 8, 6)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        for spec in self._specs:
            w = self._make_widget(spec)
            self._widgets[spec.key] = w
            self._key_by_widget[w] = spec.key
            label = QLabel(spec.label + ":")
            label.setBuddy(w)
            form.addRow(label, self._row_widget(spec, w))
        side.addWidget(box)

        calc = QGroupBox("Calculated")
        calc_lay = QVBoxLayout(calc)
        self.calc_label = QLabel()
        self.calc_label.setTextFormat(Qt.TextFormat.RichText)
        self.calc_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.calc_label.setAccessibleName("Calculated values")
        calc_lay.addWidget(self.calc_label)
        side.addWidget(calc)
        side.addStretch(1)

        val = QGroupBox("Validation")
        val_lay = QVBoxLayout(val)
        self.headline = QLabel()
        font = self.headline.font()
        font.setBold(True)
        self.headline.setFont(font)
        self.headline.setWordWrap(True)
        val_lay.addWidget(self.headline)
        self.findings_list = QListWidget()
        self.findings_list.setWordWrap(True)
        self.findings_list.setAlternatingRowColors(True)
        self.findings_list.setMinimumHeight(120)
        self.findings_list.setAccessibleName("Validation findings")
        val_lay.addWidget(self.findings_list)
        self.ack = QCheckBox(ACK_OVERRIDE_TEXT)
        val_lay.addWidget(self.ack)
        body.addWidget(val)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Reset)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(
            QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset)
        outer.addWidget(self.buttons)
        self._size_to_screen(1000, 760)

    def _size_to_screen(self, want_w, want_h):
        """Open at `want_w x want_h`, but never larger than the available screen
        (leaving a margin for the title bar / taskbar). When the content needs
        more than the clamped height the scroll area shows a scrollbar, so the
        button box below it stays on screen."""
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            want_w = min(want_w, avail.width() - 60)
            want_h = min(want_h, avail.height() - 80)
        self.resize(max(want_w, 480), max(want_h, 360))

    def _make_widget(self, spec):
        if spec.kind == FLOAT:
            typed_units = bool(spec.unit_modes) and spec.unit_setting == "pitch_units"
            w = PitchSpinBox() if typed_units else QDoubleSpinBox()
            # Recalculate when editing FINISHES (focus-out / Enter / arrow-step),
            # not on every keystroke: mid-typing a half-entered number would feed
            # the coupling partial values and lock the coupled fields out of range
            # (Patrick, 2026-11-18). Programmatic setValue still signals, so tests
            # and the live preview on a committed value are unaffected.
            w.setKeyboardTracking(False)
            if spec.unit_modes:
                self._init_unit_field(spec, w)   # range/suffix per the active mode
                if typed_units:
                    w.unitTyped.connect(
                        lambda key, num, s=spec: self._on_unit_typed(s, key, num))
            else:
                w.setDecimals(spec.decimals)
                w.setRange(float(spec.minimum), float(spec.maximum))
                w.setSingleStep(float(spec.step))
                if spec.unit:
                    w.setSuffix(" " + spec.unit)
            w.valueChanged.connect(self._on_changed)
        elif spec.kind == INT:
            w = QSpinBox()
            w.setRange(int(spec.minimum), int(spec.maximum))
            w.setSingleStep(max(1, int(spec.step)))
            w.setKeyboardTracking(False)       # as FLOAT above
            w.valueChanged.connect(self._on_changed)
        elif spec.kind == ENUM:
            w = QComboBox()
            w.currentIndexChanged.connect(self._on_changed)
        elif spec.kind == BOOL:
            w = QCheckBox()
            w.toggled.connect(self._on_changed)
        else:
            raise ValueError(f"unknown parameter kind {spec.kind!r}")
        w.setAccessibleName(spec.label)
        if spec.tooltip:
            w.setToolTip(spec.tooltip)
        return w

    # -- unit dropdowns (a FLOAT field shown in either of two units) ----------
    def _active_unit_key(self, spec):
        get = _UNIT_PREFS.get(spec.unit_setting, (None, None))[0]
        pref = get() if get is not None else None
        if pref and any(m.key == pref for m in spec.unit_modes):
            return pref                      # a remembered choice
        return spec.unit_modes[0].key        # else this field's native unit

    def _mode_by_key(self, spec, key):
        return next((m for m in spec.unit_modes if m.key == key),
                    spec.unit_modes[0])

    @staticmethod
    def _apply_mode_to_spin(spin, mode):
        spin.setDecimals(mode.decimals)
        spin.setRange(float(mode.minimum), float(mode.maximum))
        spin.setSingleStep(float(mode.step))
        spin.setSuffix(mode.suffix)

    def _init_unit_field(self, spec, spin):
        mode = self._mode_by_key(spec, self._active_unit_key(spec))
        self._unit_mode[spec.key] = mode
        self._apply_mode_to_spin(spin, mode)
        combo = QComboBox()
        for m in spec.unit_modes:
            combo.addItem(m.label, m.key)
        idx = combo.findData(mode.key)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.setAccessibleName(spec.label + " unit")
        combo.setToolTip("Show this pitch as rise per 12 in, or in degrees.")
        combo.currentIndexChanged.connect(lambda _i, s=spec: self._on_unit_changed(s))
        self._unit_combos[spec.key] = combo

    def _row_widget(self, spec, w):
        """The field cell: the spinbox alone, or the spinbox + its unit combo."""
        combo = self._unit_combos.get(spec.key)
        if combo is None:
            return w
        cell = QWidget()
        lay = QHBoxLayout(cell)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(w, 1)
        lay.addWidget(combo)
        return cell

    def _on_unit_typed(self, spec, unit_key, number):
        """The user TYPED a unit (e.g. "30 deg") -- set that unit and take the
        number AS-TYPED in it (no conversion: it is a fresh value, not a flip)."""
        mode = self._mode_by_key(spec, unit_key)
        self._unit_mode[spec.key] = mode
        setter = _UNIT_PREFS.get(spec.unit_setting, (None, None))[1]
        if setter is not None:
            setter(mode.key)
        self.values[spec.key] = float(mode.from_display(number))
        self._loading = True
        try:
            combo = self._unit_combos.get(spec.key)
            if combo is not None:
                i = combo.findData(mode.key)
                if i >= 0:
                    combo.setCurrentIndex(i)
            spin = self._widgets[spec.key]
            self._apply_mode_to_spin(spin, mode)
            spin.setValue(number)
        finally:
            self._loading = False
        self._read_widgets()
        self._refresh()

    def _on_unit_changed(self, spec):
        if self._loading:
            return
        combo = self._unit_combos[spec.key]
        old_mode = self._unit_mode[spec.key]
        new_mode = self._mode_by_key(spec, combo.currentData())
        if new_mode.key == old_mode.key:
            return
        spin = self._widgets[spec.key]
        # keep the field's CANONICAL value across the flip. Prefer the stored
        # one (no round-trip drift) unless the user typed a new display value.
        stored = self.values.get(spec.key)
        shown = spin.value()
        tol = 0.5 * 10 ** (-old_mode.decimals) + 1e-9
        if stored is not None and abs(old_mode.to_display(float(stored)) - shown) <= tol:
            canonical = float(stored)
        else:
            canonical = float(old_mode.from_display(shown))
        self._unit_mode[spec.key] = new_mode
        setter = _UNIT_PREFS.get(spec.unit_setting, (None, None))[1]
        if setter is not None:
            setter(new_mode.key)
        self.values[spec.key] = canonical
        self._loading = True
        try:
            self._apply_mode_to_spin(spin, new_mode)
            spin.setValue(new_mode.to_display(canonical))
        finally:
            self._loading = False
        self._refresh()

    # -- the draft -----------------------------------------------------------
    def _on_changed(self, *_args):
        if self._loading:
            return
        # which field the user just changed, so a kind can tell edits apart
        # (the dormer's ridge anchor: the last of eaves/pitch set is pinned).
        self._edited_key = self._key_by_widget.get(self.sender())
        self._read_widgets()
        self._refresh()

    def _read_widgets(self):
        """Widgets -> the draft. Choices are read first, because they decide
        which numbers are editable; a number is read only while its field is
        editable -- a disabled field is SHOWING a calculated value, not
        holding an input. A field that has just become editable is read too,
        so detaching a linked rise starts from the rise it was showing."""
        v = self.values
        for spec in self._specs:
            w = self._widgets[spec.key]
            if spec.kind == ENUM and w.currentIndex() >= 0:
                v[spec.key] = w.currentData()
            elif spec.kind == BOOL:
                v[spec.key] = w.isChecked()
        for spec in self._specs:
            if spec.kind in (FLOAT, INT) and spec.enabled(v):
                val = self._widgets[spec.key].value()
                if spec.unit_modes:                 # display unit -> canonical
                    val = float(self._unit_mode[spec.key].from_display(val))
                v[spec.key] = val
        # a transient hint of the field just edited; the kind may use it and
        # it is never stored (dropped from the draft right after normalize).
        v["_edited"] = self._edited_key
        self.values = self.definition.normalize(v)
        self.values.pop("_edited", None)

    def _refresh(self):
        self._derived, self._findings = self.definition.evaluate(
            self.values, self.context)
        self._show_values()
        self._show_summary()
        self._show_findings()
        if self.preview is not None:
            self.preview.set_data(self.values, self._derived, self.context)

    def _show_values(self):
        self._loading = True
        try:
            v = self.values
            for spec in self._specs:
                w = self._widgets[spec.key]
                enabled = spec.enabled(v)
                if spec.kind == ENUM:
                    choices = spec.choices_for(v)
                    if self._combo_choices.get(spec.key) != choices:
                        w.clear()
                        for value, text in choices:
                            w.addItem(text, value)
                        self._combo_choices[spec.key] = choices
                    idx = w.findData(v.get(spec.key))
                    if idx < 0 and w.count():
                        idx = 0
                    if idx != w.currentIndex():
                        w.setCurrentIndex(idx)
                elif spec.kind == BOOL:
                    w.setChecked(bool(v.get(spec.key)))
                else:
                    shown = v.get(spec.key)
                    if not enabled and spec.shown_fn is not None:
                        calc = spec.shown_fn(v, self._derived, self.context)
                        if calc is not None:
                            shown = calc
                    if shown is not None:
                        shown = int(shown) if spec.kind == INT else float(shown)
                        if spec.unit_modes:         # canonical -> display unit
                            shown = self._unit_mode[spec.key].to_display(shown)
                        if abs(w.value() - shown) > 1e-9:
                            w.setValue(shown)
                w.setEnabled(enabled)
        finally:
            self._loading = False

    def _show_summary(self):
        rows = self.definition.summary(self.values, self._derived, self.context)
        cells = "".join(
            f"<tr><td style='padding-right:12px;color:#475569'>{label}</td>"
            f"<td><b>{text}</b></td></tr>" for label, text in rows)
        self.calc_label.setText(f"<table>{cells}</table>")

    def _show_findings(self):
        fs = F.sort_findings(self._findings)
        self.headline.setText(F.headline(fs))
        ink = (_SEVERITY_INK[F.ERROR] if F.blocks(fs)
               else _SEVERITY_INK[F.WARNING] if F.needs_ack(fs)
               else QColor(21, 128, 61))
        self.headline.setStyleSheet(f"color: {ink.name()};")
        self.findings_list.clear()
        for f in fs:
            item = QListWidgetItem(
                f"{_SEVERITY_WORD.get(f.severity, f.severity)}: {f.message}")
            item.setForeground(QBrush(_SEVERITY_INK.get(f.severity, QColor(0, 0, 0))))
            item.setData(Qt.ItemDataRole.UserRole, f.rule_id)
            self.findings_list.addItem(item)
        # 0365: the box is ONLY for an overridable error (the "keep it on the
        # plan drawn red to fix there" decision). Warnings / not-evaluated
        # checks are suggestive and carry no box.
        over = F.overridable_errors(fs)
        ids = tuple(sorted(f.rule_id for f in over))
        if ids != self._ack_ids:
            # a DIFFERENT overridable error is a different thing to agree to
            self._ack_ids = ids
            self.ack.setChecked(False)
        self.ack.setText(ACK_OVERRIDE_TEXT)
        self.ack.setVisible(bool(ids))
        self.ack.setEnabled(not F.blocks(fs))
        self.ack.setStyleSheet("")

    # -- the checkpoint ------------------------------------------------------
    def set_value(self, key, value):
        """Set one parameter as if the user had (tests, and scripted use)."""
        self.values[key] = value
        self.values = self.definition.normalize(self.values)
        self._refresh()

    def findings(self):
        return list(self._findings)

    def try_accept(self) -> bool:
        """The full validation checkpoint. True only when the draft may be
        committed; otherwise the dialog stays open and says why."""
        self._read_widgets()
        self._refresh()
        fs = self._findings
        if F.blocks(fs):
            first = F.sort_findings(F.errors(fs))[0]
            w = self._widgets.get(first.field or "")
            if w is not None and w.isEnabled():
                w.setFocus()
            else:
                self.findings_list.setFocus()
            return False
        # 0365: only an overridable error still gates on the box; warnings and
        # not-evaluated checks accept without one (they are suggestive).
        if F.overridable_errors(fs) and not self.ack.isChecked():
            self.ack.setStyleSheet("color: #b91c1c; font-weight: bold;")
            self.ack.setFocus()
            return False
        result = dict(self.values)
        result["acknowledged"] = sorted(f.rule_id for f in F.unresolved(fs))
        self._result = result
        return True

    def accept(self):
        if self.try_accept():
            super().accept()

    def reset(self):
        self.values = dict(self._initial)
        self._ack_ids = None
        self._refresh()

    def result_state(self):
        """The accepted state, or None when the dialog was not accepted."""
        return None if self._result is None else dict(self._result)
