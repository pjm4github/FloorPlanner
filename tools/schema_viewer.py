#!/usr/bin/env python3
"""Read-only interactive JSON Schema graph, tree, inspector, and lint viewer.
Requires: PyQt6. Optional: PyYAML for YAML schemas.
Run: python schema_viewer.py path/to/schema.json
"""
import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QBrush, QPen, QPainter, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QSplitter, QTreeWidget,
    QTreeWidgetItem, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPathItem,
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLabel, QPushButton,
    QFileDialog, QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGraphicsItem, QGraphicsSimpleTextItem, QSizePolicy)
from PyQt6.QtGui import QPainterPath

BLUE = '#00148C'
TEAL = '#008391'
ORANGE = '#D93D1F'
PURPLE = '#500A78'
GRAY = '#F0F0F0'


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


class NodeItem(QGraphicsRectItem):
    def __init__(self, pointer, schema, x, y, on_select, issue_count):
        fields = list((schema.get('properties') or {}).items()) if isinstance(schema, dict) else []
        self.height = 58 + min(len(fields), 6)*17 + (14 if len(fields)>6 else 0)
        super().__init__(0, 0, 222, self.height)
        self.pointer = pointer
        self.on_select = on_select
        self.setPos(x, y)
        self.setBrush(QBrush(QColor('#FFFFFF')))
        self.setPen(QPen(QColor(ORANGE if issue_count else BLUE), 2 if issue_count else 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        header = QGraphicsRectItem(0, 0, 222, 29, self)
        header.setBrush(QBrush(QColor(BLUE)))
        header.setPen(QPen(Qt.PenStyle.NoPen))
        title = QGraphicsSimpleTextItem(short_name(pointer), self)
        title.setBrush(QBrush(QColor('white')))
        title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        title.setPos(8, 5)
        subtitle = QGraphicsSimpleTextItem(type_label(schema), self)
        subtitle.setBrush(QBrush(QColor('#555555')))
        subtitle.setPos(8, 31)
        for i, (name, sub) in enumerate(fields[:6]):
            t = QGraphicsSimpleTextItem(f'{name}: {type_label(sub)}', self)
            t.setBrush(QBrush(QColor('#202020')))
            t.setFont(QFont('Arial', 8))
            t.setPos(8, 52+i*17)
        if len(fields)>6:
            t=QGraphicsSimpleTextItem(f'… {len(fields)-6} more fields', self)
            t.setPos(8, 52+6*17)
        if issue_count:
            flag=QGraphicsSimpleTextItem(f'! {issue_count}', self)
            flag.setBrush(QBrush(QColor('#FFB45A')))
            flag.setPos(178, 5)

    def mousePressEvent(self, event):
        self.on_select(self.pointer)
        super().mousePressEvent(event)


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
        except Exception as exc:
            QMessageBox.critical(self, 'Cannot open schema', str(exc))

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

    def populate_graph(self):
        scene = self.graph.scene()
        scene.clear()
        self.graph_items = {}
        keys = list(self.nodes)
        # Deterministic layered arrangement, with bounded row widths.
        columns = max(1, min(5, math.ceil(math.sqrt(len(keys)))))
        positions = {}
        for i, key in enumerate(keys):
            x, y = (i % columns)*290, (i // columns)*235
            positions[key] = QPointF(x, y)
        issue_counts = defaultdict(int)
        for _, path, _ in self.issues:
            for key in self.nodes:
                if path == key or path.startswith(key+'/'):
                    issue_counts[key] += 1
        for key in keys:
            pos=positions[key]
            item=NodeItem(key,self.nodes[key],pos.x(),pos.y(),self.select_pointer,issue_counts[key])
            scene.addItem(item)
            self.graph_items[key]=item
        for source, target, label in sorted(self.edges):
            if source not in positions:
                continue
            if target not in positions:
                # Resolve a reference into the closest graph node (or skip external references).
                if not target.startswith('#'):
                    continue
                ancestor=target
                while ancestor not in positions and '/' in ancestor:
                    ancestor=ancestor.rsplit('/',1)[0]
                if ancestor not in positions:
                    continue
                target=ancestor
            if source == target:
                continue
            a=self.graph_items[source]
            b=self.graph_items[target]
            p1=a.sceneBoundingRect().center()
            p2=b.sceneBoundingRect().center()
            path=QPainterPath(p1)
            dx=p2.x()-p1.x()
            path.cubicTo(p1.x()+dx*.5,p1.y(),p2.x()-dx*.5,p2.y(),p2.x(),p2.y())
            edge=QGraphicsPathItem(path)
            edge.setPen(QPen(QColor(PURPLE if label=='ref' else TEAL), 1.4, Qt.PenStyle.DashLine if label=='ref' else Qt.PenStyle.SolidLine))
            edge.setZValue(-1)
            scene.addItem(edge)
        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-60,-60,60,60))
        self.graph.resetTransform()
        if keys:
            self.graph.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

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
        for key,graphic in self.graph_items.items():
            graphic.setSelected(key==node)

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
