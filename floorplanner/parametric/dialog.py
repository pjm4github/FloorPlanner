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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from floorplanner.parametric import findings as F
from floorplanner.parametric.params import BOOL, ENUM, FLOAT, INT

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
ACK_TEXT = "I understand these checks are unresolved / warnings remain"


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
            form.addRow(label, w)
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
        self.ack = QCheckBox(ACK_TEXT)
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
            w = QDoubleSpinBox()
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
                v[spec.key] = self._widgets[spec.key].value()
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
        ids = tuple(sorted(f.rule_id for f in F.unresolved(fs)))
        if ids != self._ack_ids:
            # a DIFFERENT set of open checks is a different thing to agree to
            self._ack_ids = ids
            self.ack.setChecked(False)
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
        if F.needs_ack(fs) and not self.ack.isChecked():
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
