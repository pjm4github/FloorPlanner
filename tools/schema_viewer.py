#!/usr/bin/env python3
"""Read-only interactive JSON Schema graph, tree, inspector, and lint viewer.
Requires: PyQt6. Optional: PyYAML for YAML schemas.
Run: python schema_viewer.py path/to/schema.json
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QBrush, QPen, QPainter, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QSplitter, QTreeWidget,
    QTreeWidgetItem, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPathItem,
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLabel, QPushButton,
    QFileDialog, QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGraphicsItem, QGraphicsSimpleTextItem, QSizePolicy, QCheckBox)
from PyQt6.QtGui import QPainterPath

BLUE = '#00148C'
TEAL = '#008391'
ORANGE = '#D93D1F'
PURPLE = '#500A78'
GRAY = '#F0F0F0'
HILITE = '#FFF27A'          # yellow: the clicked item, echoed in the OTHER view
HILITE_PROBLEM = '#FFB3B3'  # light red: the same echo when it carries a finding


def escape_pointer(part):
    return str(part).replace('~', '~0').replace('/', '~1')


def pointer_child(pointer, part):
    return pointer + '/' + escape_pointer(part)


def resolve_local(root, ref):
    if ref == '#':
        return root, '#'
    if not ref.startswith('#/'):
        return None, None
    value = root
    try:
        for part in ref[2:].split('/'):
            part = unquote(part).replace('~1', '/').replace('~0', '~')
            value = value[int(part)] if isinstance(value, list) else value[part]
        return value, ref
    except (KeyError, IndexError, TypeError, ValueError):
        return None, None


def short_name(pointer):
    if pointer == '#':
        return 'Root'
    return pointer.rsplit('/', 1)[-1].replace('~1', '/').replace('~0', '~')


def pointer_parts(pointer):
    """The JSON-pointer path as decoded key names (the leading '#' dropped)."""
    out = []
    for part in pointer.split('/'):
        if part in ('', '#'):
            continue
        out.append(unquote(part).replace('~1', '/').replace('~0', '~'))
    return out


def _value_span(text, i):
    """The half-open span of the JSON value that begins at `text[i]` -- a full
    bracket match for an object/array (strings and escapes respected), or up to
    the next top-level delimiter for a scalar."""
    opening = text[i] if i < len(text) else ''
    j, depth, in_str, esc = i, 0, False, False
    while j < len(text):
        c = text[j]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif opening in '{[':
            if c in '{[':
                depth += 1
            elif c in '}]':
                depth -= 1
                if depth == 0:
                    return i, j + 1
        elif c in ',}]':
            return i, j
        j += 1
    return i, len(text)


def locate_pointer_offset(text, pointer):
    """The character offset in the raw schema source `text` where the object key
    named by `pointer` is declared -- found by walking the pointer's keys, each
    search SCOPED to the previous key's value span so a same-named key in a
    sibling can't capture it. Best-effort: it stops at the deepest key it can
    reach (an array index, which is not a key, ends the walk) and returns that
    key's offset, or 0 for the root / an unfound first key. Tuned for JSON."""
    start, end = 0, len(text)
    best = 0
    for part in pointer_parts(pointer):
        m = re.compile('"' + re.escape(part) + r'"\s*:').search(text, start, end)
        if not m:
            break
        best = m.start()
        v = m.end()
        while v < end and text[v] in ' \t\r\n':
            v += 1
        start, end = _value_span(text, v)
    return best


def offset_to_line(text, offset):
    return text.count('\n', 0, max(0, offset)) + 1


def type_label(schema):
    if not isinstance(schema, dict):
        return 'boolean schema' if isinstance(schema, bool) else type(schema).__name__
    if '$ref' in schema:
        return 'ref → ' + short_name(schema['$ref'])
    typ = schema.get('type')
    if isinstance(typ, list):
        return ' | '.join(map(str, typ))
    if typ:
        return str(typ)
    if 'enum' in schema:
        return 'enum'
    if 'properties' in schema:
        return 'object (inferred)'
    if 'items' in schema:
        return 'array (inferred)'
    if any(k in schema for k in ('allOf', 'oneOf', 'anyOf')):
        return 'composed'
    return 'unspecified'


def collect_nodes(root):
    """Extract object/definition nodes and schema-bearing relationships."""
    nodes = {}
    edges = set()
    visited = set()

    def visit(value, pointer, owner=None, label=None, depth=0):
        if depth > 100 or not isinstance(value, (dict, bool)) or pointer in visited:
            return
        visited.add(pointer)
        if isinstance(value, bool):
            return
        is_node = pointer == '#' or pointer.startswith('#/$defs/') and pointer.count('/') == 2 or pointer.startswith('#/definitions/') and pointer.count('/') == 2 or bool(value.get('properties')) or value.get('type') == 'object'
        current_owner = owner
        if is_node:
            nodes[pointer] = value
            if owner is not None and owner != pointer:
                edges.add((owner, pointer, label or 'contains'))
            current_owner = pointer
        if '$ref' in value and owner is not None:
            edges.add((current_owner or owner, value['$ref'], 'ref'))
        for defs_key in ('$defs', 'definitions'):
            for name, sub in (value.get(defs_key) or {}).items():
                visit(sub, pointer_child(pointer_child(pointer, defs_key), name), current_owner, 'defines', depth+1)
        for name, sub in (value.get('properties') or {}).items():
            visit(sub, pointer_child(pointer_child(pointer, 'properties'), name), current_owner, name, depth+1)
        for key in ('items', 'additionalProperties', 'not', 'if', 'then', 'else'):
            if isinstance(value.get(key), (dict, bool)):
                visit(value[key], pointer_child(pointer, key), current_owner, key, depth+1)
        for key in ('allOf', 'oneOf', 'anyOf', 'prefixItems'):
            for i, sub in enumerate(value.get(key, []) or []):
                visit(sub, pointer_child(pointer_child(pointer, key), i), current_owner, key, depth+1)
        for key in ('patternProperties', 'dependentSchemas'):
            for name, sub in (value.get(key) or {}).items():
                visit(sub, pointer_child(pointer_child(pointer, key), name), current_owner, key, depth+1)
    visit(root, '#')
    return nodes, edges


def validate_instance(schema, instance):
    """Return (severity, instance pointer, message, schema pointer) findings."""
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError('Instance validation requires jsonschema: pip install jsonschema') from exc
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema)
    findings = []
    for error in validator.iter_errors(instance):
        ip = '#'+''.join('/'+escape_pointer(part) for part in error.absolute_path)
        sp = '#'+''.join('/'+escape_pointer(part) for part in error.absolute_schema_path)
        message = f'{error.validator}: {error.message}'
        findings.append(('ERROR', ip, message, sp))
        # Required/additionalProperties errors refer to the parent instance object.
        # Keep the parent pointer for reliable navigation.
    return sorted(findings, key=lambda e:(e[1],e[2]))


def instance_type(value):
    if value is None:
        return 'null'
    if isinstance(value,bool):
        return 'boolean'
    if isinstance(value,dict):
        return 'object'
    if isinstance(value,list):
        return 'array'
    if isinstance(value,str):
        return 'string'
    if isinstance(value,int):
        return 'integer'
    if isinstance(value,float):
        return 'number'
    return type(value).__name__


def audit(root):
    issues = []
    field_types = defaultdict(set)
    field_locations = defaultdict(list)
    visited = set()

    def add(level, pointer, message):
        issues.append((level, pointer, message))

    def walk(schema, pointer, depth=0):
        if depth > 100 or not isinstance(schema, dict) or pointer in visited:
            return
        visited.add(pointer)
        ref = schema.get('$ref')
        if isinstance(ref, str):
            if ref.startswith('#') and resolve_local(root, ref)[0] is None:
                add('ERROR', pointer, 'Unresolved local $ref: ' + ref)
            elif not ref.startswith('#'):
                add('INFO', pointer, 'External $ref not resolved: ' + ref)
        props = schema.get('properties', {})
        if isinstance(props, dict):
            required = schema.get('required', [])
            if isinstance(required, list):
                for name in required:
                    if name not in props:
                        add('WARNING', pointer, 'Required field not declared locally: ' + str(name) + ' (may be defined through composition)')
            for name, sub in props.items():
                loc = pointer_child(pointer_child(pointer, 'properties'), name)
                if re.search(r'[A-Z]|-', name):
                    add('STYLE', loc, 'Field name differs from snake_case convention')
                if isinstance(sub, dict):
                    field_types[name].add(type_label(sub))
                    field_locations[name].append(loc)
                    if not any(k in sub for k in ('type', '$ref', 'enum', 'const', 'allOf', 'anyOf', 'oneOf', 'properties', 'items')):
                        add('INFO', loc, 'Field has no explicit type or structural constraint')
        for key, value in schema.items():
            child = pointer_child(pointer, key)
            if key in ('$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas') and isinstance(value, dict):
                for name, sub in value.items():
                    walk(sub, pointer_child(child, name), depth+1)
            elif key in ('items', 'additionalProperties', 'not', 'if', 'then', 'else'):
                walk(value, child, depth+1)
            elif key in ('allOf', 'oneOf', 'anyOf', 'prefixItems') and isinstance(value, list):
                for i, sub in enumerate(value):
                    walk(sub, pointer_child(child, i), depth+1)
    walk(root, '#')
    for name, types in field_types.items():
        if len(types) > 1:
            add('REVIEW', field_locations[name][0], f'Field "{name}" has multiple declared types across schema: {", ".join(sorted(types))}; may be intentional')
    return issues


NODE_WIDTH = 222


def node_fields(schema):
    return list((schema.get('properties') or {}).items()) if isinstance(schema, dict) else []


def node_height(schema, expanded=False, extras_line=False):
    """The drawn height of a node box -- header, subtitle, its field rows (up to
    six, or ALL when `expanded` by a double-click), and one optional extras line
    ('+N more fields' / '[N nested hidden]'). Shared by `NodeItem` and the layout,
    so rows never overlap whatever the box is showing."""
    n = len(node_fields(schema))
    rows = n if expanded else min(n, 6)
    return 58 + rows * 17 + (14 if extras_line else 0)


class NodeItem(QGraphicsRectItem):
    """One schema object. Draggable (its position is remembered); collapsible by
    the [+]/[-] box in its header when it owns a subtree; DOUBLE-CLICK expands the
    box to show every field when it has more than the six that fit; and it can be
    HIGHLIGHTED (yellow, or light red when it carries a finding) to echo a click
    made in the tree."""

    TOGGLE_RECT = QRectF(6, 7, 15, 15)

    def __init__(self, pointer, schema, on_select, on_toggle, on_moved,
                 on_expand_fields, issue_count=0, child_count=0, collapsed=False,
                 hidden_count=0, expanded=False):
        fields = node_fields(schema)
        self.pointer = pointer
        self.issue_count = issue_count
        self.extra_fields = len(fields) > 6        # a double-click expands these
        extras = []
        if not expanded and len(fields) > 6:
            extras.append(f'+{len(fields)-6} more (double-click)')
        if collapsed and hidden_count:
            extras.append(f'[{hidden_count} nested hidden]')
        rows = len(fields) if expanded else min(len(fields), 6)
        self.height = node_height(schema, expanded, bool(extras))
        super().__init__(0, 0, NODE_WIDTH, self.height)
        self.on_select = on_select
        self.on_toggle = on_toggle
        self.on_moved = on_moved
        self.on_expand_fields = on_expand_fields
        self.has_toggle = child_count > 0
        self._press_pos = None
        self.setBrush(QBrush(QColor('#FFFFFF')))
        self.setPen(QPen(QColor(ORANGE if issue_count else BLUE), 2 if issue_count else 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(1)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        header = QGraphicsRectItem(0, 0, NODE_WIDTH, 29, self)
        header.setBrush(QBrush(QColor(BLUE)))
        header.setPen(QPen(Qt.PenStyle.NoPen))
        if self.has_toggle:
            box = QGraphicsRectItem(self.TOGGLE_RECT, self)
            box.setBrush(QBrush(QColor('white')))
            box.setPen(QPen(QColor(BLUE), 1))
            sign = QGraphicsSimpleTextItem('+' if collapsed else '-', box)
            sign.setFont(QFont('Arial', 11, QFont.Weight.Bold))
            sign.setBrush(QBrush(QColor(BLUE)))
            sign.setPos(10.5, 2.5)
        title = QGraphicsSimpleTextItem(short_name(pointer), self)
        title.setBrush(QBrush(QColor('white')))
        title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        title.setPos(26 if self.has_toggle else 8, 5)
        subtitle = QGraphicsSimpleTextItem(type_label(schema), self)
        subtitle.setBrush(QBrush(QColor('#555555')))
        subtitle.setPos(8, 31)
        for i, (name, sub) in enumerate(fields if expanded else fields[:6]):
            t = QGraphicsSimpleTextItem(f'{name}: {type_label(sub)}', self)
            t.setBrush(QBrush(QColor('#202020')))
            t.setFont(QFont('Arial', 8))
            t.setPos(8, 52+i*17)
        if extras:
            t = QGraphicsSimpleTextItem('   '.join(extras), self)
            t.setBrush(QBrush(QColor('#888888')))
            t.setFont(QFont('Arial', 8))
            t.setPos(8, 52+rows*17)
        if issue_count:
            flag=QGraphicsSimpleTextItem(f'! {issue_count}', self)
            flag.setBrush(QBrush(QColor('#FFB45A')))
            flag.setPos(NODE_WIDTH-44, 5)

    def set_highlight(self, on, problem=False):
        """Fill the box to echo a selection made elsewhere -- yellow, or light red
        when it carries a finding; white when cleared."""
        if on:
            self.setBrush(QBrush(QColor(HILITE_PROBLEM if problem else HILITE)))
        else:
            self.setBrush(QBrush(QColor('#FFFFFF')))

    def mousePressEvent(self, event):
        if self.has_toggle and self.TOGGLE_RECT.contains(self.mapFromScene(event.scenePos())):
            self.on_toggle(self.pointer)      # collapse/expand, not a selection or drag
            event.accept()
            return
        self._press_pos = self.pos()
        self.on_select(self.pointer)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # remember the drop ONLY if the node actually moved -- a plain click must
        # not pin it (which would freeze it against later auto-layout).
        if self._press_pos is not None:
            d = self.pos() - self._press_pos
            if abs(d.x()) + abs(d.y()) > 2.0:
                self.on_moved(self.pointer, self.pos())
        self._press_pos = None

    def mouseDoubleClickEvent(self, event):
        if self.has_toggle and self.TOGGLE_RECT.contains(self.mapFromScene(event.scenePos())):
            return                             # the toggle box is for collapse
        if self.extra_fields:
            self.on_expand_fields(self.pointer)   # show/hide the overflow fields
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class GraphView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setScene(QGraphicsScene(self))
        self.setBackgroundBrush(QColor('#F7F8FB'))

    def wheelEvent(self, event):
        scale = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(scale, scale)


class MainWindow(QMainWindow):
    def __init__(self, initial=None):
        super().__init__()
        self.setWindowTitle('JSON Schema Structure Viewer — read-only')
        self.resize(1450, 850)
        self.root = None
        self.nodes = {}
        self.edges = set()
        self.issues = []
        self.path_to_item = {}
        self.path = None
        self.instance = None
        self.instance_path = None
        self.instance_findings = []
        self.instance_items = {}
        self.graph_items = {}
        self.layout_overrides = {}   # pointer -> (x, y) the user dragged a node to
        self.collapsed = set()       # pointers whose subtree is folded away
        self.ref_edges = []          # (item, source, target) for the dashed $ref links
        self.show_all_refs = False   # off: show a node's refs only when it is selected
        self._selected_node = None
        self._selected_pointer = None
        self.fields_expanded = set()  # nodes a double-click expanded to all fields
        self.issue_counts = {}        # graph node -> finding count (for highlight colour)
        self._graph_hl = None         # the pointer currently highlighted in the graph
        self._tree_hl_item = None     # the tree row currently shaded
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        open_btn = QPushButton('Open schema…')
        open_btn.clicked.connect(self.open_dialog)
        bar.addWidget(open_btn)
        instance_btn = QPushButton('Open JSON instance…')
        instance_btn.clicked.connect(self.open_instance_dialog)
        bar.addWidget(instance_btn)
        collapse_btn = QPushButton('Collapse all')
        collapse_btn.setToolTip('Fold every subtree in the graph (click a node’s [+] to reopen)')
        collapse_btn.clicked.connect(self.collapse_all)
        bar.addWidget(collapse_btn)
        expand_btn = QPushButton('Expand all')
        expand_btn.clicked.connect(self.expand_all)
        bar.addWidget(expand_btn)
        reset_btn = QPushButton('Reset layout')
        reset_btn.setToolTip('Forget dragged positions and folds remembered for this schema')
        reset_btn.clicked.connect(self.reset_layout)
        bar.addWidget(reset_btn)
        edit_btn = QPushButton('Edit source ↗')
        edit_btn.setToolTip('Open the schema FILE in an external editor at the selected '
                            'node (VS Code / Sublime / Notepad++ jump to the line; set '
                            '$SCHEMA_VIEWER_EDITOR to override). Then Reload. [Ctrl+E]')
        edit_btn.setShortcut('Ctrl+E')
        edit_btn.clicked.connect(self.open_source_at_selection)
        bar.addWidget(edit_btn)
        reload_btn = QPushButton('Reload')
        reload_btn.setToolTip('Re-read the schema from disk after you edit it, keeping the '
                              'current layout, folds and selection. [F5]')
        reload_btn.setShortcut('F5')
        reload_btn.clicked.connect(self.reload_schema)
        bar.addWidget(reload_btn)
        self.refs_check = QCheckBox('All references')
        self.refs_check.setToolTip('Off: a node’s $ref links (dashed) show only while it is '
                                   'selected. On: draw every $ref link at once.')
        self.refs_check.toggled.connect(self.on_refs_toggled)
        bar.addWidget(self.refs_check)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Filter tree by name or JSON pointer…')
        self.search.textChanged.connect(self.filter_tree)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bar.addWidget(self.search, 1)
        self.summary = QLabel('Open a JSON Schema file to begin')
        bar.addWidget(self.summary)
        # The toolbar must consume only one row; the splitter gets all extra height.
        layout.addLayout(bar, 0)
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(split, 1)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Schema hierarchy', 'Type'])
        self.tree.setColumnWidth(0, 260)
        self.tree.itemSelectionChanged.connect(self.tree_selected)
        split.addWidget(self.tree)
        self.graph = GraphView()
        split.addWidget(self.graph)
        tabs = QTabWidget()
        self.inspector = QPlainTextEdit()
        self.inspector.setReadOnly(True)
        tabs.addTab(self.inspector, 'Inspector')
        self.issue_table = QTableWidget(0, 3)
        self.issue_table.setHorizontalHeaderLabels(['Severity', 'JSON pointer', 'Finding'])
        self.issue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.issue_table.cellClicked.connect(self.issue_selected)
        tabs.addTab(self.issue_table, 'Schema findings')
        self.instance_tree = QTreeWidget()
        self.instance_tree.setHeaderLabels(['Instance JSON path', 'Actual type / value'])
        self.instance_tree.setColumnWidth(0, 230)
        self.instance_tree.itemSelectionChanged.connect(self.instance_selected)
        tabs.addTab(self.instance_tree, 'Instance tree')
        self.validation_table = QTableWidget(0, 4)
        self.validation_table.setHorizontalHeaderLabels(['Severity', 'Instance path', 'Mismatch', 'Schema rule path'])
        self.validation_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.validation_table.cellClicked.connect(self.validation_selected)
        tabs.addTab(self.validation_table, 'Instance mismatches')
        self.tabs = tabs
        split.addWidget(tabs)
        split.setSizes([320, 750, 380])
        if initial:
            self.load_file(initial)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open JSON Schema', '', 'Schema files (*.json *.yaml *.yml);;All files (*)')
        if path:
            self.load_file(path)

    def open_instance_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open JSON data instance', '', 'JSON files (*.json);;All files (*)')
        if path:
            self.load_instance(path)

    def open_source_at_selection(self):
        """Open the schema's SOURCE FILE in an external editor, at the line that
        declares the selected node -- the edit end of the look-at-it / edit-it /
        reload loop. Copies `path:line` to the clipboard so even an editor that
        can't jump leaves him one paste away, and always names the line found."""
        if not self.path:
            self.statusBar().showMessage('Open a schema first.', 4000)
            return
        pointer = self._selected_pointer or '#'
        try:
            text = Path(self.path).read_text(encoding='utf-8-sig')
        except OSError as exc:
            self.statusBar().showMessage(f'Cannot read {self.path}: {exc}', 8000)
            return
        line = offset_to_line(text, locate_pointer_offset(text, pointer))
        try:
            QApplication.clipboard().setText(f'{self.path}:{line}')
        except Exception:
            pass
        where = short_name(pointer)
        opened = self._launch_editor(self.path, line)
        if opened:
            self.statusBar().showMessage(
                f'{where} → line {line}; opened in {opened} '
                f'(path:line copied to clipboard).', 9000)
        else:
            self.statusBar().showMessage(
                f'{where} → line {line} of {self.path}; copied to clipboard '
                f'(no external editor found — set $SCHEMA_VIEWER_EDITOR).', 12000)

    def _launch_editor(self, path, line):
        """Launch the first editor that will take a line jump, returning its name
        for the status line, or None if none could be started. Order: an explicit
        $SCHEMA_VIEWER_EDITOR, then VS Code / VSCodium / Cursor / Sublime, then
        Notepad++, then the OS default app (which cannot jump to the line)."""
        target = str(Path(path))
        goto = f'{target}:{line}'
        candidates = []
        env = os.environ.get('SCHEMA_VIEWER_EDITOR')
        if env:
            candidates.append((env, [env, goto]))
        for name in ('code', 'codium', 'cursor'):
            exe = shutil.which(name)
            if exe:
                candidates.append((name, [exe, '-g', goto]))
        subl = shutil.which('subl')
        if subl:
            candidates.append(('Sublime Text', [subl, goto]))
        for npp in (shutil.which('notepad++'),
                    r'C:\Program Files\Notepad++\notepad++.exe',
                    r'C:\Program Files (x86)\Notepad++\notepad++.exe'):
            if npp and os.path.exists(npp):
                candidates.append(('Notepad++', [npp, f'-n{line}', target]))
                break
        for label, cmd in candidates:
            exe = cmd[0]
            try:
                if exe.lower().endswith(('.cmd', '.bat')):
                    # a .cmd (VS Code's launcher on Windows) needs the shell
                    comspec = os.environ.get('COMSPEC', 'cmd.exe')
                    subprocess.Popen([comspec, '/c', *cmd])
                else:
                    subprocess.Popen(cmd)
                return label
            except OSError:
                continue
        try:
            os.startfile(target)  # noqa: S606  (Windows default handler; no line jump)
            return 'the system default app'
        except (OSError, AttributeError):
            return None

    def reload_schema(self):
        """Re-read the schema from disk after an external edit, keeping the
        current folds, dragged positions, field expansions and selection so the
        area under review stays put. A broken edit leaves the last good view up
        (with the parser's line/column in the error) -- fix it and Reload again."""
        if not self.path:
            self.statusBar().showMessage('No schema loaded to reload.', 4000)
            return
        keep = self._selected_pointer
        keep_fields = set(self.fields_expanded)
        if not self.load_file(self.path):
            self.statusBar().showMessage(
                'Reload failed — the edited file did not parse; the previous '
                'view is unchanged.', 9000)
            return
        self.fields_expanded = {p for p in keep_fields if p in self.nodes}
        self.populate_graph(fit=False)        # keep his zoom/pan on the edited area
        if keep and keep in self.path_to_item:
            self.select_pointer(keep)
        self.statusBar().showMessage(
            f'Reloaded {Path(self.path).name} — {len(self.nodes)} objects, '
            f'{len(self.issues)} schema findings.', 6000)

    def load_instance(self, path):
        if self.root is None:
            QMessageBox.warning(self, 'Schema required', 'Open the formal JSON Schema first.')
            return
        try:
            instance = json.loads(Path(path).read_text(encoding='utf-8-sig'))
            findings = validate_instance(self.root, instance)
        except Exception as exc:
            QMessageBox.critical(self, 'Cannot validate JSON instance', str(exc))
            return
        self.instance = instance
        self.instance_path = path
        self.instance_findings = findings
        self.populate_instance_tree()
        self.populate_validation()
        self.update_summary()
        self.tabs.setCurrentWidget(self.validation_table)

    def update_summary(self):
        schema_summary = f'{len(self.nodes)} objects · {len(self.issues)} schema findings'
        if self.instance_path:
            schema_summary += f' · {len(self.instance_findings)} instance mismatches'
        self.summary.setText(schema_summary)

    def populate_instance_tree(self):
        self.instance_tree.clear()
        self.instance_items = {}
        error_paths = [f[1] for f in self.instance_findings]
        def visit(value, pointer, name, parent, depth):
            if depth > 100:
                return
            preview = instance_type(value)
            if not isinstance(value,(dict,list)):
                preview += ' : ' + repr(value)[:100]
            item = QTreeWidgetItem([str(name), preview])
            item.setData(0, Qt.ItemDataRole.UserRole, pointer)
            if parent is None:
                self.instance_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            self.instance_items[pointer] = item
            if any(p==pointer or p.startswith(pointer+'/') for p in error_paths):
                item.setForeground(0,QColor(ORANGE))
            if isinstance(value,dict):
                for k,v in value.items():
                    visit(v,pointer_child(pointer,k),k,item,depth+1)
            elif isinstance(value,list):
                for i,v in enumerate(value):
                    visit(v,pointer_child(pointer,i),f'[{i}]',item,depth+1)
        visit(self.instance,'#','Root',None,0)
        self.instance_tree.expandToDepth(1)

    def populate_validation(self):
        self.validation_table.setRowCount(len(self.instance_findings))
        for row, finding in enumerate(self.instance_findings):
            for col, val in enumerate(finding):
                cell = QTableWidgetItem(str(val))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col==0:
                    cell.setForeground(QColor(ORANGE))
                self.validation_table.setItem(row,col,cell)

    def instance_selected(self):
        items = self.instance_tree.selectedItems()
        if not items:
            return
        pointer = items[0].data(0,Qt.ItemDataRole.UserRole)
        value,_ = resolve_local(self.instance,pointer)
        related = [f for f in self.instance_findings if f[1]==pointer or f[1].startswith(pointer+'/')]
        detail = f'INSTANCE: {pointer}\nActual type: {instance_type(value)}\n'
        if related:
            detail += '\nVALIDATION MISMATCHES:\n' + '\n'.join(f'{f[1]}: {f[2]}' for f in related[:50]) + '\n'
        detail += '\nACTUAL JSON VALUE:\n'+json.dumps(value,indent=2,ensure_ascii=False)
        self.inspector.setPlainText(detail)

    def validation_selected(self,row,col):
        _, pointer, _, schema_pointer = self.instance_findings[row]
        item = self.instance_items.get(pointer)
        if item:
            self.instance_tree.setCurrentItem(item)
            self.instance_tree.scrollToItem(item)
        self.tabs.setCurrentWidget(self.instance_tree)
        # schema rule is available in the fourth column for cross-navigation.

    def load_file(self, path):
        try:
            raw = Path(path).read_text(encoding='utf-8-sig')
            if Path(path).suffix.lower() in ('.yaml', '.yml'):
                try:
                    import yaml
                except ImportError as exc:
                    raise ValueError('YAML requires: pip install pyyaml') from exc
                root = yaml.safe_load(raw)
            else:
                root = json.loads(raw)
            if not isinstance(root, (dict, bool)):
                raise ValueError('Expected a JSON Schema object or boolean')
            self.root = root
            self.path = path
            self.nodes, self.edges = collect_nodes(root)
            self.issues = audit(root)
            self._load_layout()
            self.populate_tree()
            self.populate_graph()
            self.populate_issues()
            self.instance = None
            self.instance_path = None
            self.instance_findings = []
            self.instance_tree.clear()
            self.validation_table.setRowCount(0)
            self.update_summary()
            self.setWindowTitle('JSON Schema Structure Viewer — ' + str(path))
            self.select_pointer('#')
            return True
        except Exception as exc:
            QMessageBox.critical(self, 'Cannot open schema', str(exc))
            return False

    def populate_tree(self):
        self.tree.clear()
        self.path_to_item = {}
        def walk(value, pointer, parent, label, depth):
            if depth > 100:
                return
            item = QTreeWidgetItem([label, type_label(value)])
            item.setData(0, Qt.ItemDataRole.UserRole, pointer)
            (parent or self.tree).addChild(item) if parent else self.tree.addTopLevelItem(item)
            self.path_to_item[pointer] = item
            if isinstance(value, dict):
                for key in ('$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas'):
                    if isinstance(value.get(key), dict):
                        for name, sub in value[key].items():
                            walk(sub, pointer_child(pointer_child(pointer,key),name), item, name, depth+1)
                for key in ('items', 'additionalProperties', 'not', 'if', 'then', 'else'):
                    if isinstance(value.get(key), (dict,bool)):
                        walk(value[key], pointer_child(pointer,key), item, key, depth+1)
                for key in ('allOf', 'oneOf', 'anyOf', 'prefixItems'):
                    if isinstance(value.get(key), list):
                        for i, sub in enumerate(value[key]):
                            walk(sub, pointer_child(pointer_child(pointer,key),i), item, f'{key}[{i}]', depth+1)
        walk(self.root, '#', None, 'Root', 0)
        self.tree.expandToDepth(1)

    COL_W = 300           # horizontal gap between containment layers
    ROW_GAP = 26          # vertical gap between sibling node boxes

    def _structure(self):
        """The containment forest that drives the layout, plus the cross-links.

        Every edge whose label is not 'ref' is structural (contains/defines/a
        property name); 'ref' edges are drawn on top but never drive placement.
        Returns `(children, parent, roots, refs)` -- a single PRIMARY parent per
        node (the shallowest, by a breadth-first walk from the root), so a node
        reached several ways is laid out once; the rest become cross-links too."""
        struct = defaultdict(list)
        refs = []
        order = {k: i for i, k in enumerate(self.nodes)}
        seen = set()
        for source, target, label in self.edges:
            tgt = self._graph_node_of(target)
            if source not in self.nodes or tgt is None or source == tgt:
                continue
            if label == 'ref':
                refs.append((source, tgt))
            elif (source, tgt) not in seen:
                seen.add((source, tgt))
                struct[source].append(tgt)
        for src in struct:
            struct[src].sort(key=lambda k: order.get(k, 1 << 30))
        # breadth-first from the root: first arrival fixes the primary parent
        parent = {}
        roots = []
        start = '#' if '#' in self.nodes else None
        queue = []
        if start is not None:
            roots.append(start)
            queue.append(start)
        seen_nodes = set(roots)
        while queue:
            cur = queue.pop(0)
            for child in struct.get(cur, ()):
                if child not in seen_nodes:
                    seen_nodes.add(child)
                    parent[child] = cur
                    queue.append(child)
        # any node the root never reaches is its own root (kept, in schema order)
        for key in self.nodes:
            if key not in seen_nodes:
                seen_nodes.add(key)
                roots.append(key)
                queue.append(key)
                while queue:
                    cur = queue.pop(0)
                    for child in struct.get(cur, ()):
                        if child not in seen_nodes:
                            seen_nodes.add(child)
                            parent[child] = cur
                            queue.append(child)
        children = defaultdict(list)
        for child, par in parent.items():
            children[par].append(child)
        for par in children:
            children[par].sort(key=lambda k: order.get(k, 1 << 30))
        return children, parent, roots, refs

    def _graph_node_of(self, pointer):
        """The nearest ancestor pointer that is an actual graph node, or None for
        an external/unresolvable reference."""
        if pointer in self.nodes:
            return pointer
        if not pointer.startswith('#'):
            return None
        node = pointer
        while node not in self.nodes and '/' in node:
            node = node.rsplit('/', 1)[0]
        return node if node in self.nodes else None

    def _compute_layout(self, children, roots):
        """A tidy left-to-right tree: x by containment depth, y stacked so no two
        boxes overlap and each parent sits centred on its visible children. A
        collapsed node is laid out as a leaf. Returns `(positions, visible,
        hidden_count)`."""
        visible = set()
        hidden_count = {}

        def count_hidden(node):
            total = 0
            for child in children.get(node, ()):
                total += 1 + count_hidden(child)
            return total

        def height_of(node):
            schema = self.nodes[node]
            expanded = node in self.fields_expanded
            kids = children.get(node, ())
            extras = ((not expanded and len(node_fields(schema)) > 6)
                      or (node in self.collapsed and bool(kids)))
            return node_height(schema, expanded, extras)

        y_cursor = [0.0]
        positions = {}

        def place(node, depth):
            visible.add(node)
            x = depth * self.COL_W
            kids = [] if node in self.collapsed else children.get(node, ())
            if node in self.collapsed:
                hidden_count[node] = count_hidden(node)
            if not kids:
                y = y_cursor[0]
                y_cursor[0] += height_of(node) + self.ROW_GAP
            else:
                ys = [place(child, depth + 1) for child in kids]
                y = (ys[0] + ys[-1]) / 2.0
            positions[node] = QPointF(x, y)
            return y

        for root in roots:
            place(root, 0)
        # final guard: no two boxes in a column may overlap (centring a parent on
        # a short subtree can nudge it into its neighbour) -- push the lower down.
        cols = defaultdict(list)
        for node in visible:
            cols[round(positions[node].x())].append(node)
        for nodes_in_col in cols.values():
            nodes_in_col.sort(key=lambda n: positions[n].y())
            for prev, cur in zip(nodes_in_col, nodes_in_col[1:], strict=False):
                floor = positions[prev].y() + height_of(prev) + self.ROW_GAP
                if positions[cur].y() < floor:
                    positions[cur] = QPointF(positions[cur].x(), floor)
        return positions, visible, hidden_count

    def populate_graph(self, fit=True):
        scene = self.graph.scene()
        scene.clear()
        self.graph_items = {}
        if not self.nodes:
            return
        children, _parent, roots, refs = self._structure()
        positions, visible, hidden_count = self._compute_layout(children, roots)
        for key, (x, y) in self.layout_overrides.items():
            if key in positions:                      # a remembered manual drop
                positions[key] = QPointF(x, y)
        issue_counts = defaultdict(int)
        for _, path, _ in self.issues:
            node = self._graph_node_of(path)
            if node is not None:
                issue_counts[node] += 1
        self.issue_counts = issue_counts
        for key in visible:
            pos = positions[key]
            item = NodeItem(key, self.nodes[key], self.select_pointer,
                            self.toggle_collapse, self.on_node_moved,
                            self.toggle_fields,
                            issue_count=issue_counts[key],
                            child_count=len(children.get(key, ())),
                            collapsed=key in self.collapsed,
                            hidden_count=hidden_count.get(key, 0),
                            expanded=key in self.fields_expanded)
            item.setPos(pos)
            scene.addItem(item)
            self.graph_items[key] = item
        self.ref_edges = []
        structural = [(s, t, False) for s in children for t in children[s]]
        structural += [(s, t, True) for s, t in refs]
        for source, target, is_ref in structural:
            if source not in self.graph_items or target not in self.graph_items:
                continue
            edge = self._add_edge(scene, self.graph_items[source],
                                  self.graph_items[target], is_ref)
            if is_ref:
                self.ref_edges.append((edge, source, target))
        self._apply_ref_visibility()
        # the items were just rebuilt -- restore the cross-view highlight onto the
        # fresh node, so a field expand or a collapse keeps the yellow echo.
        self._graph_hl = None
        if self._selected_pointer is not None:
            self._apply_highlight(self._selected_pointer,
                                  self._graph_node_of(self._selected_pointer) or '')
        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-60, -60, 60, 60))
        if fit:
            self.graph.resetTransform()
            self.graph.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _add_edge(self, scene, a, b, is_ref):
        """A curve anchored to the node BORDERS (not their centres, which used to
        drive the line straight through the boxes). It leaves the source on the
        side facing the target and arrives on the target's facing side."""
        ra, rb = a.sceneBoundingRect(), b.sceneBoundingRect()
        if rb.center().x() >= ra.center().x():
            p1 = QPointF(ra.right(), ra.center().y())
            p2 = QPointF(rb.left(), rb.center().y())
        else:
            p1 = QPointF(ra.left(), ra.center().y())
            p2 = QPointF(rb.right(), rb.center().y())
        dx = p2.x() - p1.x()
        bend = max(abs(dx) * 0.5, 40.0)
        c1x = p1.x() + (bend if dx >= 0 else -bend)
        c2x = p2.x() - (bend if dx >= 0 else -bend)
        path = QPainterPath(p1)
        path.cubicTo(c1x, p1.y(), c2x, p2.y(), p2.x(), p2.y())
        edge = QGraphicsPathItem(path)
        edge.setPen(QPen(QColor(PURPLE if is_ref else TEAL), 1.4,
                         Qt.PenStyle.DashLine if is_ref else Qt.PenStyle.SolidLine))
        edge.setZValue(-1)
        scene.addItem(edge)
        return edge

    def _apply_ref_visibility(self):
        """Dashed $ref links are the graph's clutter: by default show only those
        touching the SELECTED node, so the base view stays a clean tree. The 'All
        references' checkbox overrides that and draws every one."""
        sel = self._selected_node
        for edge, source, target in self.ref_edges:
            edge.setVisible(self.show_all_refs or sel in (source, target))

    def on_refs_toggled(self, checked):
        self.show_all_refs = bool(checked)
        self._apply_ref_visibility()

    def toggle_collapse(self, pointer):
        if pointer in self.collapsed:
            self.collapsed.discard(pointer)
        else:
            self.collapsed.add(pointer)
        self._save_layout()
        self.populate_graph(fit=False)        # keep the viewer's current zoom/pan

    def toggle_fields(self, pointer):
        """A double-click grew or shrank this node's field list (session-only,
        not remembered); relay the whole graph so the column reflows."""
        if pointer in self.fields_expanded:
            self.fields_expanded.discard(pointer)
        else:
            self.fields_expanded.add(pointer)
        self.populate_graph(fit=False)

    def _apply_highlight(self, pointer, node):
        """Echo a click in BOTH views: fill the nearest graph node, and shade the
        exact tree row -- yellow, or light red when it carries a finding."""
        if self._graph_hl in self.graph_items:
            self.graph_items[self._graph_hl].set_highlight(False)
        self._graph_hl = node if node in self.graph_items else None
        if self._graph_hl is not None:
            self.graph_items[self._graph_hl].set_highlight(
                True, self.issue_counts.get(self._graph_hl, 0) > 0)
        self._highlight_tree_row(pointer)

    def _highlight_tree_row(self, pointer):
        if self._tree_hl_item is not None:
            try:
                for col in (0, 1):
                    self._tree_hl_item.setBackground(col, QBrush())
            except RuntimeError:
                pass                       # the row went away on a reload
        item = self.path_to_item.get(pointer)
        self._tree_hl_item = item
        if item is None:
            return
        problem = any(p == pointer or p.startswith(pointer + '/')
                      for _lvl, p, _m in self.issues)
        brush = QBrush(QColor(HILITE_PROBLEM if problem else HILITE))
        for col in (0, 1):
            item.setBackground(col, brush)

    def collapse_all(self):
        """Fold every subtree except the root's, so only the top layers show."""
        children, _p, roots, _refs = self._structure()
        rootset = set(roots)
        self.collapsed = {k for k, kids in children.items() if kids and k not in rootset}
        self._save_layout()
        self.populate_graph()

    def expand_all(self):
        self.collapsed = set()
        self._save_layout()
        self.populate_graph()

    def on_node_moved(self, pointer, pos):
        moved = (pos.x(), pos.y())
        if self.layout_overrides.get(pointer) == moved:
            return
        self.layout_overrides[pointer] = moved
        self._save_layout()

    # -- remembered layouts, keyed by the schema's absolute path -------------
    def _layout_store_path(self):
        return Path.home() / '.schema_viewer_layouts.json'

    def _layout_key(self):
        return str(Path(self.path).resolve()) if self.path else None

    def _read_store(self):
        try:
            return json.loads(self._layout_store_path().read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}

    def _load_layout(self):
        self.layout_overrides = {}
        self.collapsed = set()
        self.fields_expanded = set()   # a per-session peek, not remembered
        self._graph_hl = None
        self._tree_hl_item = None
        self._selected_pointer = None
        key = self._layout_key()
        if not key:
            return
        saved = self._read_store().get(key, {})
        for ptr, xy in (saved.get('positions') or {}).items():
            if ptr in self.nodes and isinstance(xy, list) and len(xy) == 2:
                self.layout_overrides[ptr] = (float(xy[0]), float(xy[1]))
        self.collapsed = {p for p in (saved.get('collapsed') or []) if p in self.nodes}

    def _save_layout(self):
        key = self._layout_key()
        if not key:
            return
        store = self._read_store()
        store[key] = {
            'positions': {p: [round(x, 1), round(y, 1)]
                          for p, (x, y) in self.layout_overrides.items()
                          if p in self.nodes},
            'collapsed': sorted(p for p in self.collapsed if p in self.nodes),
        }
        try:
            self._layout_store_path().write_text(
                json.dumps(store, indent=2), encoding='utf-8')
        except OSError:
            pass          # a read-only home is no reason to break the viewer

    def reset_layout(self):
        """Forget the remembered positions and folds for this schema."""
        self.layout_overrides = {}
        self.collapsed = set()
        self._save_layout()
        self.populate_graph()

    def closeEvent(self, event):
        self._save_layout()
        super().closeEvent(event)

    def populate_issues(self):
        self.issue_table.setRowCount(len(self.issues))
        for row,(level,pointer,msg) in enumerate(self.issues):
            for col,val in enumerate((level,pointer,msg)):
                item=QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col==0:
                    item.setForeground(QColor(ORANGE if level in ('ERROR','WARNING') else PURPLE))
                self.issue_table.setItem(row,col,item)

    def tree_selected(self):
        items=self.tree.selectedItems()
        if items:
            self.display_pointer(items[0].data(0,Qt.ItemDataRole.UserRole))

    def select_pointer(self,pointer):
        item=self.path_to_item.get(pointer)
        if item:
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)
        self.display_pointer(pointer)

    def display_pointer(self,pointer):
        if self.root is None:
            return
        value, _ = resolve_local(self.root,pointer)
        if value is None:
            return
        issues=[(sev,msg) for sev,path,msg in self.issues if path==pointer or path.startswith(pointer+'/')]
        report=f'JSON pointer: {pointer}\nType: {type_label(value)}\n'
        if issues:
            report+='\nFINDINGS IN SUBTREE:\n'+'\n'.join(f'[{sev}] {msg}' for sev,msg in issues[:30])+'\n'
        report+='\nSCHEMA DEFINITION:\n'+json.dumps(value,indent=2,ensure_ascii=False)
        self.inspector.setPlainText(report)
        node=pointer
        while node not in self.graph_items and '/' in node:
            node=node.rsplit('/',1)[0]
        self._selected_node = node if node in self.graph_items else None
        self._selected_pointer = pointer
        for key,graphic in self.graph_items.items():
            graphic.setSelected(key==node)
        self._apply_highlight(pointer, node)
        self._apply_ref_visibility()

    def issue_selected(self,row,col):
        self.select_pointer(self.issues[row][1])

    def filter_tree(self,text):
        term=text.lower().strip()
        def visit(item):
            match=term in item.text(0).lower() or term in item.data(0,Qt.ItemDataRole.UserRole).lower()
            child_match=False
            for i in range(item.childCount()):
                child_match=visit(item.child(i)) or child_match
            show=not term or match or child_match
            item.setHidden(not show)
            if term and child_match:
                item.setExpanded(True)
            return show
        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schema',nargs='?',help='Path to JSON Schema (.json/.yaml/.yml)')
    parser.add_argument('instance',nargs='?',help='Path to a real JSON data file to validate')
    args=parser.parse_args()
    app=QApplication(sys.argv[:1])
    win=MainWindow(args.schema)
    if args.instance and args.schema and win.root is not None:
        win.load_instance(args.instance)
    win.show()
    sys.exit(app.exec())

if __name__=='__main__':
    main()
