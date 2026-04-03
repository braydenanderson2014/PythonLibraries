"""Node-RED style flow canvas with branching / merge support.

Graph model
-----------
A flow is a list of FlowNodeItem objects.  Each item carries:

  node_id   – str matching NODE_LIBRARY
  node_kind – "normal" | "split" | "merge"
  params    – dict of per-node params

A ``split`` node has two downstream branch lists (True / False).
A ``merge`` node receives control from both branch paths.

Wire model
----------
Every WireItem now carries an optional ``branch_label``:
  None  -> plain sequential wire
  "true"  -> wire leaving the True (bottom) output port of a split
  "false" -> wire leaving the False (top) output port of a split

Serialisation
-------------
``collect_tree_definitions()`` returns the flat-with-branches format consumed
by the upgraded executor:

  [
    {"node_id": "size_check", "params": {...}},
    {
      "node_id": "split",          # sentinel node kind
      "params": {"condition": "size_gt_threshold"},
      "branches": {
        "true":  [list of node-defs for the True path],
        "false": [list of node-defs for the False path]
      }
    },
    {"node_id": "merge", "params": {}},  # re-join point
    ...continuation nodes...
  ]
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# ──────────────────────────────────────────────────────────────────────────────
# Colours & constants
# ──────────────────────────────────────────────────────────────────────────────

_C_BG        = QColor("#14161A")
_C_GRID_FINE = QColor("#1E222A")
_C_GRID_MAJ  = QColor("#2B313A")

_C_NODE_BASE   = QColor("#1E1F23")
_C_NODE_BORDER = QColor("#3A3D45")
_C_NODE_SELECT = QColor("#F6C945")
_C_NODE_TITLE  = QColor("#2A8CFF")
_C_SPLIT_TITLE = QColor("#D46B08")   # amber for split/condition
_C_MERGE_TITLE = QColor("#389E0D")   # green for merge

_C_TEXT  = QColor("#F2F5F7")
_C_MUTED = QColor("#AAB2BD")

_C_PORT_IN    = QColor("#7BD88F")
_C_PORT_OUT   = QColor("#FFB86C")
_C_PORT_TRUE  = QColor("#52C41A")    # green  – True / large branch
_C_PORT_FALSE = QColor("#FF4D4F")    # red    – False / small branch

_C_WIRE_PLAIN = QColor("#7A8AA0")
_C_WIRE_TRUE  = QColor("#52C41A")
_C_WIRE_FALSE = QColor("#FF4D4F")

NODE_W  = 230.0
NODE_H  = 88.0
PORT_R  = 6.0

# ──────────────────────────────────────────────────────────────────────────────
# FlowNodeItem
# ──────────────────────────────────────────────────────────────────────────────

class FlowNodeItem(QGraphicsObject):
    """A draggable node card.

    node_kind:
      "normal" – single in, single out
      "split"  – single in, two outs (true / false)
      "merge"  – two ins, single out
    """

    position_changed = pyqtSignal(object)

    def __init__(
        self,
        node_id: str,
        params: Optional[Dict[str, Any]] = None,
        node_kind: str = "normal",
    ) -> None:
        super().__init__()
        self.node_id   = node_id
        self.params    = dict(params or {})
        self.node_kind = node_kind          # "normal" | "split" | "merge"
        self.uid       = str(uuid.uuid4())  # stable id for wire lookup
        self.order_index = 1

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    # ── geometry ────────────────────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, NODE_W, NODE_H)

    # ── painting ────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, _option, _widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.boundingRect()

        border = _C_NODE_SELECT if self.isSelected() else _C_NODE_BORDER
        title_color = {
            "split": _C_SPLIT_TITLE,
            "merge": _C_MERGE_TITLE,
        }.get(self.node_kind, _C_NODE_TITLE)

        # card body
        painter.setPen(QPen(border, 2.0))
        painter.setBrush(_C_NODE_BASE)
        painter.drawRoundedRect(rect, 8.0, 8.0)

        # title bar
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(title_color)
        painter.drawRoundedRect(QRectF(0.0, 0.0, rect.width(), 24.0), 8.0, 8.0)
        # cover bottom corners of title bar
        painter.drawRect(QRectF(0.0, 14.0, rect.width(), 10.0))

        # title text
        painter.setPen(_C_TEXT)
        label = self.node_id
        if self.node_kind == "split":
            label = f"⬦ {self.node_id}"
        elif self.node_kind == "merge":
            label = f"⬧ {self.node_id}"
        painter.drawText(
            QRectF(10.0, 3.0, rect.width() - 50.0, 18.0),
            Qt.AlignmentFlag.AlignVCenter,
            label,
        )

        # order badge
        painter.drawText(
            QRectF(rect.width() - 36.0, 3.0, 26.0, 18.0),
            Qt.AlignmentFlag.AlignCenter,
            str(self.order_index),
        )

        # params hint
        painter.setPen(_C_MUTED)
        params_text = "params: yes" if self.params else "params: none"
        painter.drawText(
            QRectF(10.0, 34.0, rect.width() - 20.0, 20.0),
            Qt.AlignmentFlag.AlignVCenter,
            params_text,
        )

        # branch labels for split
        if self.node_kind == "split":
            painter.setPen(_C_PORT_TRUE)
            painter.drawText(
                QRectF(rect.width() - 80.0, rect.height() * 0.60, 70.0, 16.0),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                "true →",
            )
            painter.setPen(_C_PORT_FALSE)
            painter.drawText(
                QRectF(rect.width() - 80.0, rect.height() * 0.25, 70.0, 16.0),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                "false →",
            )

        # ports
        painter.setPen(Qt.PenStyle.NoPen)

        # input port(s)
        if self.node_kind in ("normal", "split"):
            painter.setBrush(_C_PORT_IN)
            painter.drawEllipse(self._local_input_port(), PORT_R, PORT_R)
        else:  # merge – two input ports
            painter.setBrush(_C_PORT_TRUE)
            painter.drawEllipse(self._local_merge_in_true(), PORT_R, PORT_R)
            painter.setBrush(_C_PORT_FALSE)
            painter.drawEllipse(self._local_merge_in_false(), PORT_R, PORT_R)

        # output port(s)
        if self.node_kind == "split":
            painter.setBrush(_C_PORT_TRUE)
            painter.drawEllipse(self._local_out_true(), PORT_R, PORT_R)
            painter.setBrush(_C_PORT_FALSE)
            painter.drawEllipse(self._local_out_false(), PORT_R, PORT_R)
        else:
            painter.setBrush(_C_PORT_OUT)
            painter.drawEllipse(self._local_output_port(), PORT_R, PORT_R)

    # ── local port positions (in item coords) ────────────────────────────────

    def _local_input_port(self) -> QPointF:
        return QPointF(0.0, NODE_H / 2.0)

    def _local_output_port(self) -> QPointF:
        return QPointF(NODE_W, NODE_H / 2.0)

    # split: output ports
    def _local_out_true(self) -> QPointF:
        return QPointF(NODE_W, NODE_H * 0.68)

    def _local_out_false(self) -> QPointF:
        return QPointF(NODE_W, NODE_H * 0.32)

    # merge: two input ports
    def _local_merge_in_true(self) -> QPointF:
        return QPointF(0.0, NODE_H * 0.68)

    def _local_merge_in_false(self) -> QPointF:
        return QPointF(0.0, NODE_H * 0.32)

    # ── scene-space port positions ────────────────────────────────────────────

    def scene_input_port(self, branch: Optional[str] = None) -> QPointF:
        if self.node_kind == "merge":
            if branch == "true":
                return self.mapToScene(self._local_merge_in_true())
            if branch == "false":
                return self.mapToScene(self._local_merge_in_false())
        return self.mapToScene(self._local_input_port())

    def scene_output_port(self, branch: Optional[str] = None) -> QPointF:
        if self.node_kind == "split":
            if branch == "true":
                return self.mapToScene(self._local_out_true())
            if branch == "false":
                return self.mapToScene(self._local_out_false())
        return self.mapToScene(self._local_output_port())

    # ── Qt item change ────────────────────────────────────────────────────────

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.position_changed.emit(self)
        return super().itemChange(change, value)

    # ── serialisation ─────────────────────────────────────────────────────────

    def to_definition(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "node_id":   self.node_id,
            "node_kind": self.node_kind,
            "params":    dict(self.params),
        }
        return d


# ──────────────────────────────────────────────────────────────────────────────
# WireItem
# ──────────────────────────────────────────────────────────────────────────────

class WireItem(QGraphicsPathItem):
    """Bezier wire between two nodes.

    branch_label: None | "true" | "false"
      Controls which output port of a split node the wire leaves from,
      and which input port of a merge node it connects to.
    """

    def __init__(
        self,
        source: FlowNodeItem,
        target: FlowNodeItem,
        branch_label: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.source       = source
        self.target       = target
        self.branch_label = branch_label
        self.setZValue(-1.0)
        color = {
            "true":  _C_WIRE_TRUE,
            "false": _C_WIRE_FALSE,
        }.get(branch_label or "", _C_WIRE_PLAIN)
        self.setPen(QPen(color, 2.0))
        self.refresh_path()

    def refresh_path(self) -> None:
        start = self.source.scene_output_port(self.branch_label)
        # For a merge target, the wire arrives on the matching input port
        end   = self.target.scene_input_port(self.branch_label)
        dx    = max(50.0, abs(end.x() - start.x()) * 0.5)

        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x() + dx, start.y()),
            QPointF(end.x()   - dx, end.y()),
            end,
        )
        self.setPath(path)

        # Draw an arrowhead at the midpoint for labelled wires
        if self.branch_label:
            mid   = path.pointAtPercent(0.5)
            angle = path.angleAtPercent(0.5)
            self._draw_arrow(mid, angle)

    def _draw_arrow(self, tip: QPointF, angle_deg: float) -> None:
        """Arrowhead is drawn as part of the QPainterPath."""
        import math
        rad   = math.radians(-angle_deg)
        alen  = 10.0
        awide = 5.0
        dx    = math.cos(rad)
        dy    = math.sin(rad)
        left  = QPointF(tip.x() - alen * dx + awide * dy, tip.y() - alen * dy - awide * dx)
        right = QPointF(tip.x() - alen * dx - awide * dy, tip.y() - alen * dy + awide * dx)
        arrow = QPainterPath()
        arrow.moveTo(tip)
        arrow.lineTo(left)
        arrow.lineTo(right)
        arrow.closeSubpath()
        # Merge into item path
        combined = self.path()
        combined.addPath(arrow)
        self.setPath(combined)


# ──────────────────────────────────────────────────────────────────────────────
# FlowCanvas (QGraphicsView)
# ──────────────────────────────────────────────────────────────────────────────

class FlowCanvas(QGraphicsView):
    """Grid-backed, pannable canvas."""

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setSceneRect(0.0, 0.0, 4000.0, 2000.0)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, _C_BG)
        left = int(rect.left()) - (int(rect.left()) % 20)
        top  = int(rect.top())  - (int(rect.top())  % 20)
        x = left
        while x < int(rect.right()):
            pen = _C_GRID_MAJ if x % 100 == 0 else _C_GRID_FINE
            painter.setPen(QPen(pen, 1.0))
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += 20
        y = top
        while y < int(rect.bottom()):
            pen = _C_GRID_MAJ if y % 100 == 0 else _C_GRID_FINE
            painter.setPen(QPen(pen, 1.0))
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += 20

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        self.scale(factor, factor)


# ──────────────────────────────────────────────────────────────────────────────
# NodeRedFlowCanvas – public API used by JobsWidget
# ──────────────────────────────────────────────────────────────────────────────

class NodeRedFlowCanvas(QWidget):
    """Node-RED-inspired visual flow editor with branch/merge support.

    Internal graph model
    --------------------
    self._nodes   – ordered list of FlowNodeItem (top-level sequence)
    self._wires   – list of WireItem (all edges, including branch edges)

    A ``split`` node carries branch sub-lists inside its ``branches`` dict:
      self._branches[split_uid] = {
          "true":  [FlowNodeItem, ...],
          "false": [FlowNodeItem, ...],
      }

    A ``merge`` node is just a normal FlowNodeItem of kind "merge"; the
    executor recognises it by id == "merge".
    """

    selected_node_changed = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._scene   = QGraphicsScene(self)
        self._view    = FlowCanvas(self._scene)

        # Main sequence (does not include branch children)
        self._nodes: List[FlowNodeItem] = []
        self._wires: List[WireItem]     = []

        # uid → {"true": [...], "false": [...]}
        self._branches: Dict[str, Dict[str, List[FlowNodeItem]]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()

        def _btn(label: str, slot) -> QPushButton:
            b = QPushButton(label)
            b.clicked.connect(slot)
            b.setMaximumHeight(26)
            toolbar.addWidget(b)
            return b

        _btn("Auto Layout",    self.auto_layout)
        _btn("Reset Zoom",     self._reset_zoom)
        toolbar.addSpacing(12)
        _btn("Add Branch",     self._add_branch_to_selected)
        _btn("Add Merge",      self._add_merge_after_selected)
        toolbar.addStretch()

        layout.addLayout(toolbar)
        layout.addWidget(self._view)

        self._scene.selectionChanged.connect(self._on_scene_selection_changed)

    # ── internal helpers ─────────────────────────────────────────────────────

    def _on_scene_selection_changed(self) -> None:
        self.selected_node_changed.emit(self.get_selected_node_definition())

    def _reset_zoom(self) -> None:
        self._view.resetTransform()

    def _on_node_moved(self, _node: FlowNodeItem) -> None:
        self._refresh_wires()

    def _make_node(self, node_id: str, params: Dict[str, Any], kind: str = "normal") -> FlowNodeItem:
        n = FlowNodeItem(node_id=node_id, params=params, node_kind=kind)
        n.position_changed.connect(self._on_node_moved)
        self._scene.addItem(n)
        return n

    def _remove_node_item(self, node: FlowNodeItem) -> None:
        self._scene.removeItem(node)

    def _add_wire(self, src: FlowNodeItem, tgt: FlowNodeItem, label: Optional[str] = None) -> WireItem:
        w = WireItem(src, tgt, branch_label=label)
        self._scene.addItem(w)
        self._wires.append(w)
        return w

    def _clear_all_wires(self) -> None:
        for w in self._wires:
            self._scene.removeItem(w)
        self._wires = []

    # ── public: add normal node ───────────────────────────────────────────────

    def add_node(self, node_id: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Append a normal node to the main sequence."""
        node = self._make_node(node_id, params or {}, "normal")
        self._nodes.append(node)
        self._scene.clearSelection()
        node.setSelected(True)
        self._reflow()

    # ── public: split & merge ─────────────────────────────────────────────────

    def _add_branch_to_selected(self) -> None:
        """Insert a split node after the currently selected node, and add two
        empty branch slots (true / false).  A merge node is automatically
        appended after the split to act as the re-join point."""
        selected = self.get_selected_node_item()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select a node to branch from.")
            return
        if selected.node_kind == "split":
            QMessageBox.information(self, "Already a Split", "This node is already a split.")
            return

        # Ask for the condition node id
        cond_id, ok = QInputDialog.getText(
            self, "Split Condition Node",
            "Condition node ID (e.g. size_check):",
            text="size_check",
        )
        if not ok or not cond_id.strip():
            return
        cond_id = cond_id.strip()

        idx = self._nodes.index(selected)

        split_node = self._make_node(cond_id, {}, "split")
        self._nodes.insert(idx + 1, split_node)

        # Two empty branch lists
        self._branches[split_node.uid] = {"true": [], "false": []}

        # Merge node immediately after the split in the main sequence
        merge_node = self._make_node("merge", {}, "merge")
        self._nodes.insert(idx + 2, merge_node)

        self._scene.clearSelection()
        split_node.setSelected(True)
        self._reflow()
        QMessageBox.information(
            self,
            "Branch Added",
            f"Split «{cond_id}» added.\n\n"
            "• Select the split node, then use 'Add Node' to add nodes to its True branch.\n"
            "• Hold Shift while clicking 'Add Node' (or use the context) to add False branch nodes.\n\n"
            "Tip: Right-click the split node for branch options.",
        )

    def _add_merge_after_selected(self) -> None:
        """Insert a standalone merge node after the selected node."""
        selected = self.get_selected_node_item()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select a node to merge after.")
            return
        idx = self._nodes.index(selected)
        merge_node = self._make_node("merge", {}, "merge")
        self._nodes.insert(idx + 1, merge_node)
        self._scene.clearSelection()
        merge_node.setSelected(True)
        self._reflow()

    def add_node_to_branch(self, node_id: str, split_uid: str, branch: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Programmatically append a node to a branch of a split node."""
        if split_uid not in self._branches:
            return
        if branch not in ("true", "false"):
            return
        node = self._make_node(node_id, params or {}, "normal")
        self._branches[split_uid][branch].append(node)
        self._reflow()

    # ── public: remove ─────────────────────────────────────────────────────────

    def remove_selected_node(self) -> None:
        selected = self.get_selected_node_item()
        if not selected:
            return

        # Remove from main list
        if selected in self._nodes:
            self._nodes.remove(selected)
            # Clean up branch data if it was a split
            if selected.uid in self._branches:
                for side in self._branches[selected.uid].values():
                    for child in side:
                        self._remove_node_item(child)
                del self._branches[selected.uid]

        else:
            # It's a branch child – find and remove it
            for uid, sides in self._branches.items():
                for side in sides.values():
                    if selected in side:
                        side.remove(selected)
                        break

        self._remove_node_item(selected)
        self._reflow()
        self.selected_node_changed.emit(None)

    # ── public: clear ─────────────────────────────────────────────────────────

    def clear_nodes(self) -> None:
        self._clear_all_wires()
        for uid, sides in self._branches.items():
            for side in sides.values():
                for n in side:
                    self._remove_node_item(n)
        self._branches.clear()
        for n in self._nodes:
            self._remove_node_item(n)
        self._nodes.clear()
        self.selected_node_changed.emit(None)

    # ── layout ────────────────────────────────────────────────────────────────

    def _reflow(self) -> None:
        """Recalculate positions for every node and wire."""
        self._update_order_badges()
        self._layout_nodes()
        self._rebuild_all_wires()

    def _update_order_badges(self) -> None:
        for i, node in enumerate(self._nodes, start=1):
            node.order_index = i
            node.update()

    def _layout_nodes(self) -> None:
        """Lay out main sequence horizontally; branch arms above/below."""
        x = 70.0
        y_main = 300.0
        gap_x  = 290.0
        gap_y  = 170.0

        for node in self._nodes:
            node.setPos(x, y_main)

            if node.node_kind == "split" and node.uid in self._branches:
                true_nodes  = self._branches[node.uid]["true"]
                false_nodes = self._branches[node.uid]["false"]

                # True branch: below main rail
                bx_true = x + gap_x
                for bn in true_nodes:
                    bn.setPos(bx_true, y_main + gap_y)
                    bx_true += gap_x

                # False branch: above main rail
                bx_false = x + gap_x
                for bn in false_nodes:
                    bn.setPos(bx_false, y_main - gap_y)
                    bx_false += gap_x

            x += gap_x

    def auto_layout(self) -> None:
        self._layout_nodes()
        self._refresh_wires()

    # ── wires ─────────────────────────────────────────────────────────────────

    def _rebuild_all_wires(self) -> None:
        self._clear_all_wires()

        for i, node in enumerate(self._nodes):
            # Wire to next main-sequence node
            if i + 1 < len(self._nodes):
                next_node = self._nodes[i + 1]

                if node.node_kind == "split":
                    # No direct sequential wire from split – branch wires handle it
                    pass
                elif next_node.node_kind == "merge":
                    # If the previous node is already handling merge via branches, skip
                    pass
                else:
                    self._add_wire(node, next_node)

            # Wires for split branches
            if node.node_kind == "split" and node.uid in self._branches:
                # Find the merge node that follows the split (next node)
                merge_node = self._nodes[i + 1] if i + 1 < len(self._nodes) and self._nodes[i + 1].node_kind == "merge" else None

                for branch_label, branch_nodes in self._branches[node.uid].items():
                    if not branch_nodes:
                        # Empty branch: wire directly to merge
                        if merge_node:
                            self._add_wire(node, merge_node, branch_label)
                        continue

                    # Wire: split → first branch node
                    self._add_wire(node, branch_nodes[0], branch_label)
                    # Wire: within branch
                    for j in range(len(branch_nodes) - 1):
                        self._add_wire(branch_nodes[j], branch_nodes[j + 1])
                    # Wire: last branch node → merge
                    if merge_node:
                        self._add_wire(branch_nodes[-1], merge_node, branch_label)

                # Wire: merge → next after merge
                if merge_node:
                    merge_idx = self._nodes.index(merge_node)
                    if merge_idx + 1 < len(self._nodes):
                        self._add_wire(merge_node, self._nodes[merge_idx + 1])

    def _refresh_wires(self) -> None:
        for w in self._wires:
            w.refresh_path()

    # ── selection helpers ─────────────────────────────────────────────────────

    def get_selected_node_item(self) -> Optional[FlowNodeItem]:
        for item in self._scene.selectedItems():
            if isinstance(item, FlowNodeItem):
                return item
        return None

    def get_selected_node_definition(self) -> Optional[Dict[str, Any]]:
        n = self.get_selected_node_item()
        return n.to_definition() if n else None

    def set_selected_node_params(self, params: Dict[str, Any]) -> bool:
        n = self.get_selected_node_item()
        if not n:
            return False
        n.params = dict(params)
        n.update()
        self.selected_node_changed.emit(n.to_definition())
        return True

    # ── serialise ─────────────────────────────────────────────────────────────

    def collect_tree_definitions(self) -> List[Dict[str, Any]]:
        """Return the flat-with-branches list used by the executor."""
        return self._serialise_sequence(self._nodes)

    def _serialise_sequence(self, nodes: List[FlowNodeItem]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for node in nodes:
            if node.node_kind == "split" and node.uid in self._branches:
                d: Dict[str, Any] = {
                    "node_id":   node.node_id,
                    "node_kind": "split",
                    "params":    dict(node.params),
                    "branches": {
                        "true":  self._serialise_sequence(self._branches[node.uid]["true"]),
                        "false": self._serialise_sequence(self._branches[node.uid]["false"]),
                    },
                }
                result.append(d)
            else:
                result.append(node.to_definition())
        return result

    # ── deserialise ───────────────────────────────────────────────────────────

    def load_tree(self, node_defs: List[Dict[str, Any]]) -> None:
        self.clear_nodes()
        self._deserialise_sequence(node_defs, self._nodes)
        self._reflow()

    def _deserialise_sequence(
        self,
        defs: List[Dict[str, Any]],
        target_list: List[FlowNodeItem],
    ) -> None:
        for node_def in defs:
            if isinstance(node_def, str):
                node_def = {"node_id": node_def, "params": {}, "node_kind": "normal"}
            if not isinstance(node_def, dict):
                continue
            node_id   = str(node_def.get("node_id",   "")).strip()
            node_kind = str(node_def.get("node_kind", "normal"))
            params    = node_def.get("params", {})
            if not isinstance(params, dict):
                params = {}
            if not node_id:
                continue

            node = self._make_node(node_id, params, node_kind)
            target_list.append(node)

            branches = node_def.get("branches")
            if node_kind == "split" and isinstance(branches, dict):
                self._branches[node.uid] = {"true": [], "false": []}
                self._deserialise_sequence(
                    branches.get("true", []),
                    self._branches[node.uid]["true"],
                )
                self._deserialise_sequence(
                    branches.get("false", []),
                    self._branches[node.uid]["false"],
                )

    # ── misc public ───────────────────────────────────────────────────────────

    def node_count(self) -> int:
        return len(self._nodes)
