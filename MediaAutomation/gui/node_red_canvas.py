"""Node-RED style flow canvas for building workflow trees visually."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FlowNodeItem(QGraphicsObject):
    """Visual node block with one input and one output port."""

    position_changed = pyqtSignal(object)

    NODE_WIDTH = 230.0
    NODE_HEIGHT = 88.0

    def __init__(self, node_id: str, params: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.node_id = node_id
        self.params = dict(params or {})
        self.order_index = 1
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, self.NODE_WIDTH, self.NODE_HEIGHT)

    def paint(self, painter: QPainter, _option, _widget=None) -> None:
        base = QColor("#1E1F23")
        border = QColor("#3A3D45")
        title = QColor("#2A8CFF")
        text = QColor("#F2F5F7")
        muted = QColor("#AAB2BD")

        if self.isSelected():
            border = QColor("#F6C945")

        rect = self.boundingRect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(border, 2.0))
        painter.setBrush(base)
        painter.drawRoundedRect(rect, 8.0, 8.0)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(title)
        painter.drawRoundedRect(QRectF(0.0, 0.0, rect.width(), 24.0), 8.0, 8.0)

        painter.setPen(text)
        painter.drawText(QRectF(10.0, 3.0, rect.width() - 50.0, 18.0), Qt.AlignmentFlag.AlignVCenter, self.node_id)

        painter.setPen(muted)
        params_text = "params: yes" if self.params else "params: none"
        painter.drawText(QRectF(10.0, 34.0, rect.width() - 20.0, 20.0), Qt.AlignmentFlag.AlignVCenter, params_text)

        painter.setPen(text)
        painter.drawText(
            QRectF(rect.width() - 36.0, 3.0, 26.0, 18.0),
            Qt.AlignmentFlag.AlignCenter,
            str(self.order_index),
        )

        in_color = QColor("#7BD88F")
        out_color = QColor("#FFB86C")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(in_color)
        painter.drawEllipse(QPointF(0.0, rect.height() / 2.0), 5.0, 5.0)

        painter.setBrush(out_color)
        painter.drawEllipse(QPointF(rect.width(), rect.height() / 2.0), 5.0, 5.0)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.position_changed.emit(self)
        return super().itemChange(change, value)

    def input_port_scene_pos(self) -> QPointF:
        local = QPointF(0.0, self.NODE_HEIGHT / 2.0)
        return self.mapToScene(local)

    def output_port_scene_pos(self) -> QPointF:
        local = QPointF(self.NODE_WIDTH, self.NODE_HEIGHT / 2.0)
        return self.mapToScene(local)

    def to_definition(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "params": dict(self.params)}


class WireItem(QGraphicsPathItem):
    """Bezier wire connecting one node output to the next node input."""

    def __init__(self, source: FlowNodeItem, target: FlowNodeItem):
        super().__init__()
        self.source = source
        self.target = target
        self.setZValue(-1.0)
        self.setPen(QPen(QColor("#7A8AA0"), 2.0))
        self.refresh_path()

    def refresh_path(self) -> None:
        start = self.source.output_port_scene_pos()
        end = self.target.input_port_scene_pos()
        dx = max(50.0, (end.x() - start.x()) * 0.5)

        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x() + dx, start.y()),
            QPointF(end.x() - dx, end.y()),
            end,
        )
        self.setPath(path)


class FlowCanvas(QGraphicsView):
    """Grid-backed canvas used by the flow editor."""

    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setSceneRect(0.0, 0.0, 2400.0, 1400.0)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#14161A"))

        fine_pen = QPen(QColor("#1E222A"), 1.0)
        major_pen = QPen(QColor("#2B313A"), 1.0)

        left = int(rect.left()) - (int(rect.left()) % 20)
        top = int(rect.top()) - (int(rect.top()) % 20)

        x = left
        while x < int(rect.right()):
            painter.setPen(major_pen if x % 100 == 0 else fine_pen)
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += 20

        y = top
        while y < int(rect.bottom()):
            painter.setPen(major_pen if y % 100 == 0 else fine_pen)
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += 20


class NodeRedFlowCanvas(QWidget):
    """Node-RED-inspired editor for sequence workflows."""

    selected_node_changed = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._view = FlowCanvas(self._scene)
        self._nodes: List[FlowNodeItem] = []
        self._wires: List[WireItem] = []

        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.auto_layout_btn = QPushButton("Auto Layout")
        self.auto_layout_btn.clicked.connect(self.auto_layout)
        toolbar.addWidget(self.auto_layout_btn)

        self.zoom_reset_btn = QPushButton("Reset Zoom")
        self.zoom_reset_btn.clicked.connect(self._reset_zoom)
        toolbar.addWidget(self.zoom_reset_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)
        layout.addWidget(self._view)

        self._scene.selectionChanged.connect(self._emit_selection_changed)

    def _emit_selection_changed(self) -> None:
        self.selected_node_changed.emit(self.get_selected_node_definition())

    def _reset_zoom(self) -> None:
        self._view.resetTransform()

    def _on_node_moved(self, _node: FlowNodeItem) -> None:
        self._refresh_wires()

    def add_node(self, node_id: str, params: Optional[Dict[str, Any]] = None) -> None:
        node = FlowNodeItem(node_id=node_id, params=params)
        node.position_changed.connect(self._on_node_moved)
        self._scene.addItem(node)
        self._nodes.append(node)

        x = 70.0 + (len(self._nodes) - 1) * 280.0
        y = 90.0
        node.setPos(x, y)
        node.setSelected(True)

        self._update_order_badges()
        self._rebuild_wires()

    def remove_selected_node(self) -> None:
        selected = self.get_selected_node_item()
        if not selected:
            return

        self._scene.removeItem(selected)
        self._nodes = [n for n in self._nodes if n is not selected]
        self._rebuild_wires()
        self._update_order_badges()
        self.selected_node_changed.emit(None)

    def clear_nodes(self) -> None:
        for wire in self._wires:
            self._scene.removeItem(wire)
        self._wires = []

        for node in self._nodes:
            self._scene.removeItem(node)
        self._nodes = []

        self.selected_node_changed.emit(None)

    def auto_layout(self) -> None:
        for i, node in enumerate(self._nodes):
            node.setPos(70.0 + i * 280.0, 90.0)
        self._refresh_wires()

    def _update_order_badges(self) -> None:
        for i, node in enumerate(self._nodes, start=1):
            node.order_index = i
            node.update()

    def _rebuild_wires(self) -> None:
        for wire in self._wires:
            self._scene.removeItem(wire)
        self._wires = []

        for i in range(len(self._nodes) - 1):
            wire = WireItem(self._nodes[i], self._nodes[i + 1])
            self._scene.addItem(wire)
            self._wires.append(wire)

    def _refresh_wires(self) -> None:
        for wire in self._wires:
            wire.refresh_path()

    def get_selected_node_item(self) -> Optional[FlowNodeItem]:
        selected = self._scene.selectedItems()
        if not selected:
            return None
        node = selected[0]
        if isinstance(node, FlowNodeItem):
            return node
        return None

    def get_selected_node_definition(self) -> Optional[Dict[str, Any]]:
        node = self.get_selected_node_item()
        if not node:
            return None
        return node.to_definition()

    def set_selected_node_params(self, params: Dict[str, Any]) -> bool:
        node = self.get_selected_node_item()
        if not node:
            return False
        node.params = dict(params)
        node.update()
        self.selected_node_changed.emit(node.to_definition())
        return True

    def collect_tree_definitions(self) -> List[Dict[str, Any]]:
        return [n.to_definition() for n in self._nodes]

    def load_tree(self, node_defs: List[Dict[str, Any]]) -> None:
        self.clear_nodes()
        for node_def in node_defs:
            if isinstance(node_def, str):
                self.add_node(node_def, {})
                continue
            if not isinstance(node_def, dict):
                continue
            node_id = str(node_def.get("node_id", "")).strip()
            if not node_id:
                continue
            params = node_def.get("params", {})
            if not isinstance(params, dict):
                params = {}
            self.add_node(node_id, params)
        self.auto_layout()

    def node_count(self) -> int:
        return len(self._nodes)
