"""Jobs tab widget with visual behavior-tree builder and workflow scheduling."""

import json
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class JobsWidget(QWidget):
    """Manage jobs, trees/nodes, and post-processing schedule from one place."""

    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager
        self.selected_job_id = None

        self._setup_ui()
        self._refresh_all()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_all)
        self.refresh_timer.start(2500)

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self._build_nodes_group())
        layout.addWidget(self._build_jobs_group())
        layout.addWidget(self._build_schedule_group())
        layout.addWidget(self._build_actions_group())
        self.setLayout(layout)

    def _build_nodes_group(self) -> QGroupBox:
        group = QGroupBox("Behavior Trees & Node Library")
        layout = QVBoxLayout()

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Tree:"))
        self.tree_combo = QComboBox()
        self.tree_combo.currentTextChanged.connect(self._load_selected_tree_into_builder)
        top_row.addWidget(self.tree_combo)

        delete_tree_btn = QPushButton("Delete Tree")
        delete_tree_btn.clicked.connect(self._delete_selected_tree)
        top_row.addWidget(delete_tree_btn)

        top_row.addWidget(QLabel("Custom tree name:"))
        self.custom_tree_name_edit = QLineEdit()
        self.custom_tree_name_edit.setPlaceholderText("my_custom_flow")
        top_row.addWidget(self.custom_tree_name_edit)

        save_tree_btn = QPushButton("Save Tree")
        save_tree_btn.clicked.connect(self._save_custom_tree)
        top_row.addWidget(save_tree_btn)

        layout.addLayout(top_row)

        builder_row = QHBoxLayout()

        lib_group = QGroupBox("Available Nodes")
        lib_layout = QVBoxLayout()
        self.nodes_table = QTableWidget(0, 4)
        self.nodes_table.setHorizontalHeaderLabels(["Node ID", "Name", "Description", "Param Hints"])
        self.nodes_table.horizontalHeader().setStretchLastSection(True)
        self.nodes_table.setMaximumHeight(200)
        lib_layout.addWidget(self.nodes_table)
        lib_group.setLayout(lib_layout)
        builder_row.addWidget(lib_group)

        controls_layout = QVBoxLayout()
        add_btn = QPushButton(">>")
        add_btn.clicked.connect(self._add_selected_node_to_tree)
        controls_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected_tree_node)
        controls_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_tree_builder)
        controls_layout.addWidget(clear_btn)
        controls_layout.addStretch()
        builder_row.addLayout(controls_layout)

        tree_group = QGroupBox("Tree Builder (Drag/Drop to reorder)")
        tree_layout = QVBoxLayout()
        self.tree_builder_list = QListWidget()
        self.tree_builder_list.setMaximumHeight(200)
        self.tree_builder_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree_builder_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree_builder_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_builder_list.currentItemChanged.connect(self._on_tree_node_selected)
        tree_layout.addWidget(self.tree_builder_list)
        tree_group.setLayout(tree_layout)
        builder_row.addWidget(tree_group)

        params_group = QGroupBox("Selected Node Parameters (JSON)")
        params_layout = QVBoxLayout()
        self.selected_node_label = QLabel("Selected node: none")
        params_layout.addWidget(self.selected_node_label)
        self.node_params_edit = QPlainTextEdit()
        self.node_params_edit.setPlaceholderText('{\n  "threshold_gb": 8.0\n}')
        self.node_params_edit.setMaximumHeight(120)
        params_layout.addWidget(self.node_params_edit)

        params_btns = QHBoxLayout()
        apply_params_btn = QPushButton("Apply Params")
        apply_params_btn.clicked.connect(self._apply_selected_node_params)
        params_btns.addWidget(apply_params_btn)

        reset_params_btn = QPushButton("Reset Params")
        reset_params_btn.clicked.connect(self._reset_selected_node_params)
        params_btns.addWidget(reset_params_btn)
        params_btns.addStretch()
        params_layout.addLayout(params_btns)
        params_group.setLayout(params_layout)
        builder_row.addWidget(params_group)

        layout.addLayout(builder_row)
        group.setLayout(layout)
        return group

    def _build_jobs_group(self) -> QGroupBox:
        group = QGroupBox("All Jobs")
        layout = QVBoxLayout()

        self.jobs_table = QTableWidget(0, 7)
        self.jobs_table.setHorizontalHeaderLabels(
            ["Job ID", "Query", "Type", "Status", "Manager", "Attempts", "Updated"]
        )
        self.jobs_table.horizontalHeader().setStretchLastSection(True)
        self.jobs_table.itemSelectionChanged.connect(self._on_job_selected)
        layout.addWidget(self.jobs_table)

        self.selected_job_label = QLabel("Selected job: none")
        layout.addWidget(self.selected_job_label)

        group.setLayout(layout)
        return group

    def _build_schedule_group(self) -> QGroupBox:
        group = QGroupBox("Schedule Next Step For Selected Job")
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Action:"))
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["encode", "subtitle", "workflow"])
        self.action_type_combo.currentTextChanged.connect(self._on_action_type_changed)
        row1.addWidget(self.action_type_combo)

        row1.addWidget(QLabel("Schedule:"))
        self.schedule_mode_combo = QComboBox()
        self.schedule_mode_combo.addItems(["now", "once", "cron", "interval"])
        self.schedule_mode_combo.currentTextChanged.connect(self._on_schedule_mode_changed)
        row1.addWidget(self.schedule_mode_combo)
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Input file:"))
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Path to source media file...")
        row2.addWidget(self.input_path_edit)
        browse_in = QPushButton("Browse")
        browse_in.clicked.connect(self._browse_input)
        row2.addWidget(browse_in)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Output file:"))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Path to output file...")
        row3.addWidget(self.output_path_edit)
        browse_out = QPushButton("Browse")
        browse_out.clicked.connect(self._browse_output)
        row3.addWidget(browse_out)
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        self.profile_label = QLabel("Preset/Profile:")
        row4.addWidget(self.profile_label)
        self.profile_edit = QLineEdit()
        self.profile_edit.setPlaceholderText("HandBrake preset or subtitle profile (optional; ignored by workflow)")
        row4.addWidget(self.profile_edit)

        self.workflow_threshold_label = QLabel("Workflow size threshold (GB):")
        row4.addWidget(self.workflow_threshold_label)
        self.workflow_threshold_spin = QDoubleSpinBox()
        self.workflow_threshold_spin.setDecimals(2)
        self.workflow_threshold_spin.setSingleStep(0.25)
        self.workflow_threshold_spin.setMinimum(0.25)
        self.workflow_threshold_spin.setMaximum(500.0)
        default_threshold = float(self.task_manager.get_workflow_defaults().get("size_threshold_gb", 10.0))
        self.workflow_threshold_spin.setValue(default_threshold)
        row4.addWidget(self.workflow_threshold_spin)

        self.save_threshold_btn = QPushButton("Save As Default")
        self.save_threshold_btn.clicked.connect(self._save_default_threshold)
        row4.addWidget(self.save_threshold_btn)
        layout.addLayout(row4)

        row5 = QHBoxLayout()
        self.once_time_label = QLabel("Run at (minutes from now):")
        row5.addWidget(self.once_time_label)
        self.once_minutes_spin = QSpinBox()
        self.once_minutes_spin.setMinimum(1)
        self.once_minutes_spin.setMaximum(10080)
        self.once_minutes_spin.setValue(15)
        row5.addWidget(self.once_minutes_spin)

        self.cron_label = QLabel("Cron:")
        row5.addWidget(self.cron_label)
        self.cron_edit = QLineEdit()
        self.cron_edit.setPlaceholderText("0 2 * * *")
        row5.addWidget(self.cron_edit)

        self.interval_label = QLabel("Interval:")
        row5.addWidget(self.interval_label)
        self.interval_value_spin = QSpinBox()
        self.interval_value_spin.setMinimum(1)
        self.interval_value_spin.setMaximum(10000)
        self.interval_value_spin.setValue(1)
        row5.addWidget(self.interval_value_spin)

        self.interval_unit_combo = QComboBox()
        self.interval_unit_combo.addItems(["minutes", "hours", "days"])
        row5.addWidget(self.interval_unit_combo)
        row5.addStretch()
        layout.addLayout(row5)

        row6 = QHBoxLayout()
        self.schedule_btn = QPushButton("Schedule Next Step")
        self.schedule_btn.setStyleSheet("background-color: #28A745;")
        self.schedule_btn.clicked.connect(self._schedule_action)
        row6.addWidget(self.schedule_btn)
        row6.addStretch()
        layout.addLayout(row6)

        self._on_schedule_mode_changed(self.schedule_mode_combo.currentText())
        self._on_action_type_changed(self.action_type_combo.currentText())

        group.setLayout(layout)
        return group

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox("Follow-up Actions")
        layout = QVBoxLayout()

        self.actions_table = QTableWidget(0, 9)
        self.actions_table.setHorizontalHeaderLabels(
            [
                "Action ID",
                "Job ID",
                "Type",
                "Schedule",
                "Status",
                "Task ID",
                "Input",
                "Output",
                "Message",
            ]
        )
        self.actions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.actions_table)

        group.setLayout(layout)
        return group

    def _create_tree_item(self, node_id: str, params: dict | None = None) -> QListWidgetItem:
        params = params or {}
        item = QListWidgetItem(self._format_tree_node_text(node_id, params))
        item.setData(Qt.ItemDataRole.UserRole, {"node_id": node_id, "params": dict(params)})
        return item

    @staticmethod
    def _format_tree_node_text(node_id: str, params: dict) -> str:
        return f"{node_id} [params]" if params else node_id

    def _node_def_from_item(self, item: QListWidgetItem) -> dict:
        payload = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(payload, dict):
            node_id = str(payload.get("node_id", "")).strip()
            params = payload.get("params", {})
            if isinstance(params, dict) and node_id:
                return {"node_id": node_id, "params": dict(params)}
        node_id = item.text().split(" ", 1)[0].strip()
        return {"node_id": node_id, "params": {}}

    def _collect_tree_definitions(self) -> list[dict]:
        defs = []
        for i in range(self.tree_builder_list.count()):
            defs.append(self._node_def_from_item(self.tree_builder_list.item(i)))
        return defs

    def _on_tree_node_selected(self, current: QListWidgetItem, _previous: QListWidgetItem):
        if not current:
            self.selected_node_label.setText("Selected node: none")
            self.node_params_edit.setPlainText("{}")
            return
        node_def = self._node_def_from_item(current)
        self.selected_node_label.setText(f"Selected node: {node_def.get('node_id', '')}")
        self.node_params_edit.setPlainText(json.dumps(node_def.get("params", {}), indent=2))

    def _apply_selected_node_params(self):
        item = self.tree_builder_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Node Selected", "Select a tree node to apply parameters.")
            return

        raw_text = self.node_params_edit.toPlainText().strip()
        if not raw_text:
            raw_text = "{}"

        try:
            parsed = json.loads(raw_text)
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Could not parse JSON: {e}")
            return

        if not isinstance(parsed, dict):
            QMessageBox.warning(self, "Invalid Parameters", "Node parameters must be a JSON object.")
            return

        node_def = self._node_def_from_item(item)
        node_def["params"] = parsed
        item.setData(Qt.ItemDataRole.UserRole, node_def)
        item.setText(self._format_tree_node_text(node_def["node_id"], parsed))

    def _reset_selected_node_params(self):
        item = self.tree_builder_list.currentItem()
        if not item:
            return
        node_def = self._node_def_from_item(item)
        node_def["params"] = {}
        item.setData(Qt.ItemDataRole.UserRole, node_def)
        item.setText(node_def["node_id"])
        self.node_params_edit.setPlainText("{}")

    def _on_schedule_mode_changed(self, mode: str):
        is_once = mode == "once"
        is_cron = mode == "cron"
        is_interval = mode == "interval"

        self.once_time_label.setVisible(is_once)
        self.once_minutes_spin.setVisible(is_once)
        self.cron_label.setVisible(is_cron)
        self.cron_edit.setVisible(is_cron)
        self.interval_label.setVisible(is_interval)
        self.interval_value_spin.setVisible(is_interval)
        self.interval_unit_combo.setVisible(is_interval)

    def _on_action_type_changed(self, action_type: str):
        is_workflow = action_type == "workflow"
        self.workflow_threshold_label.setVisible(is_workflow)
        self.workflow_threshold_spin.setVisible(is_workflow)
        self.save_threshold_btn.setVisible(is_workflow)
        self.tree_combo.setEnabled(is_workflow)
        self.custom_tree_name_edit.setEnabled(is_workflow)
        self.tree_builder_list.setEnabled(is_workflow)
        self.node_params_edit.setEnabled(is_workflow)

    def _browse_input(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input Media File", "")
        if file_path:
            self.input_path_edit.setText(file_path)

    def _browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Output File", "")
        if file_path:
            self.output_path_edit.setText(file_path)

    def _on_job_selected(self):
        selected_rows = self.jobs_table.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_job_id = None
            self.selected_job_label.setText("Selected job: none")
            return
        row = selected_rows[0].row()
        job_id_item = self.jobs_table.item(row, 0)
        if not job_id_item:
            return
        self.selected_job_id = job_id_item.text()
        query = self.jobs_table.item(row, 1).text() if self.jobs_table.item(row, 1) else ""
        self.selected_job_label.setText(f"Selected job: {self.selected_job_id} ({query})")

    def _add_selected_node_to_tree(self):
        selected = self.nodes_table.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        node_item = self.nodes_table.item(row, 0)
        if not node_item:
            return
        self.tree_builder_list.addItem(self._create_tree_item(node_item.text(), {}))

    def _remove_selected_tree_node(self):
        row = self.tree_builder_list.currentRow()
        if row >= 0:
            self.tree_builder_list.takeItem(row)

    def _clear_tree_builder(self):
        self.tree_builder_list.clear()
        self.selected_node_label.setText("Selected node: none")
        self.node_params_edit.setPlainText("{}")

    def _save_default_threshold(self):
        value = float(self.workflow_threshold_spin.value())
        self.task_manager.update_workflow_defaults(size_threshold_gb=value)
        QMessageBox.information(self, "Saved", f"Default workflow threshold saved: {value:.2f} GB")

    def _load_selected_tree_into_builder(self, tree_name: str):
        trees = self.task_manager.get_behavior_trees()
        nodes = trees.get(tree_name, [])
        self.tree_builder_list.clear()
        for node_def in nodes:
            if isinstance(node_def, str):
                self.tree_builder_list.addItem(self._create_tree_item(node_def, {}))
                continue
            if isinstance(node_def, dict):
                node_id = str(node_def.get("node_id", "")).strip()
                if not node_id:
                    continue
                params = node_def.get("params", {})
                if not isinstance(params, dict):
                    params = {}
                self.tree_builder_list.addItem(self._create_tree_item(node_id, params))
        if tree_name:
            self.custom_tree_name_edit.setText(tree_name)
        self._on_tree_node_selected(self.tree_builder_list.currentItem(), None)

    def _save_custom_tree(self):
        name = self.custom_tree_name_edit.text().strip()
        node_defs = self._collect_tree_definitions()
        try:
            self.task_manager.add_custom_behavior_tree(name, node_defs)
            QMessageBox.information(self, "Tree Saved", f"Saved custom behavior tree: {name}")
            self._refresh_nodes_and_trees()
        except Exception as e:
            QMessageBox.critical(self, "Tree Save Error", str(e))

    def _delete_selected_tree(self):
        tree_name = self.tree_combo.currentText().strip()
        if not tree_name:
            return
        builtins = {"default_media_flow", "encode_always_flow", "direct_output_flow"}
        if tree_name in builtins:
            QMessageBox.warning(self, "Not Allowed", "Built-in trees cannot be deleted.")
            return
        reply = QMessageBox.question(
            self,
            "Delete Tree",
            f"Delete custom tree '{tree_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.task_manager.delete_custom_behavior_tree(tree_name)
            self._refresh_nodes_and_trees()

    def _schedule_action(self):
        if not self.selected_job_id:
            QMessageBox.warning(self, "No job selected", "Select a job first from the All Jobs table.")
            return

        action_type = self.action_type_combo.currentText()
        schedule_mode = self.schedule_mode_combo.currentText()
        input_path = self.input_path_edit.text().strip()
        output_path = self.output_path_edit.text().strip()
        preset_or_profile = self.profile_edit.text().strip()
        if not input_path or not output_path:
            QMessageBox.warning(self, "Validation", "Input and output paths are required.")
            return

        scheduled_time = None
        cron_expression = None
        interval_value = None
        interval_unit = None
        if schedule_mode == "once":
            run_at = datetime.now() + timedelta(minutes=self.once_minutes_spin.value())
            scheduled_time = run_at.isoformat()
        elif schedule_mode == "cron":
            cron_expression = self.cron_edit.text().strip()
            if not cron_expression:
                QMessageBox.warning(self, "Validation", "Cron expression is required for cron mode.")
                return
        elif schedule_mode == "interval":
            interval_value = int(self.interval_value_spin.value())
            interval_unit = self.interval_unit_combo.currentText()

        try:
            workflow_options = None
            if action_type == "workflow":
                threshold = float(self.workflow_threshold_spin.value())
                self.task_manager.update_workflow_defaults(size_threshold_gb=threshold)
                workflow_options = {
                    "size_threshold_gb": threshold,
                    "tree_name": self.tree_combo.currentText() or "default_media_flow",
                }

            action_id = self.task_manager.schedule_followup_action(
                job_id=self.selected_job_id,
                action_type=action_type,
                schedule_mode=schedule_mode,
                input_path=input_path,
                output_path=output_path,
                preset_or_profile=preset_or_profile,
                scheduled_time=scheduled_time,
                cron_expression=cron_expression,
                interval_value=interval_value,
                interval_unit=interval_unit,
                workflow_options=workflow_options,
            )
            QMessageBox.information(self, "Scheduled", f"Scheduled follow-up action: {action_id}")
            self._refresh_actions_table()
        except Exception as e:
            QMessageBox.critical(self, "Scheduling Error", str(e))

    def _refresh_all(self):
        self._refresh_nodes_and_trees()
        self._refresh_jobs_table()
        self._refresh_actions_table()

    def _refresh_nodes_and_trees(self):
        nodes = self.task_manager.get_available_nodes()
        self.nodes_table.setRowCount(len(nodes))
        for row, (node_id, meta) in enumerate(nodes.items()):
            self.nodes_table.setItem(row, 0, QTableWidgetItem(node_id))
            self.nodes_table.setItem(row, 1, QTableWidgetItem(str(meta.get("name", ""))))
            self.nodes_table.setItem(row, 2, QTableWidgetItem(str(meta.get("description", ""))))
            params = meta.get("params", {})
            param_hint = ", ".join(params.keys()) if isinstance(params, dict) else ""
            self.nodes_table.setItem(row, 3, QTableWidgetItem(param_hint))

        trees = self.task_manager.get_behavior_trees()
        current = self.tree_combo.currentText()
        self.tree_combo.blockSignals(True)
        self.tree_combo.clear()
        for tree_name in trees.keys():
            self.tree_combo.addItem(tree_name)
        if current:
            idx = self.tree_combo.findText(current)
            if idx >= 0:
                self.tree_combo.setCurrentIndex(idx)
        self.tree_combo.blockSignals(False)

        if self.tree_combo.count() > 0 and self.tree_builder_list.count() == 0:
            self._load_selected_tree_into_builder(self.tree_combo.currentText())

    def _refresh_jobs_table(self):
        jobs = self.task_manager.get_all_jobs()
        ordered = sorted(jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)
        self.jobs_table.setRowCount(len(ordered))
        for row, job in enumerate(ordered):
            self.jobs_table.setItem(row, 0, QTableWidgetItem(job.get("job_id", "")))
            self.jobs_table.setItem(row, 1, QTableWidgetItem(job.get("query", "")))
            self.jobs_table.setItem(row, 2, QTableWidgetItem(job.get("content_type", "")))
            self.jobs_table.setItem(row, 3, QTableWidgetItem(job.get("status", "")))
            self.jobs_table.setItem(row, 4, QTableWidgetItem(job.get("selected_manager") or "-"))
            self.jobs_table.setItem(row, 5, QTableWidgetItem(str(job.get("attempts", 0))))
            self.jobs_table.setItem(row, 6, QTableWidgetItem(self._format_time(job.get("updated_at", ""))))

    def _refresh_actions_table(self):
        actions = self.task_manager.get_followup_actions()
        ordered = sorted(actions.values(), key=lambda a: a.get("created_at", ""), reverse=True)
        self.actions_table.setRowCount(len(ordered))
        for row, action in enumerate(ordered):
            self.actions_table.setItem(row, 0, QTableWidgetItem(action.get("action_id", "")))
            self.actions_table.setItem(row, 1, QTableWidgetItem(action.get("job_id", "")))
            self.actions_table.setItem(row, 2, QTableWidgetItem(action.get("action_type", "")))
            self.actions_table.setItem(row, 3, QTableWidgetItem(action.get("schedule_mode", "")))
            self.actions_table.setItem(row, 4, QTableWidgetItem(action.get("status", "")))
            self.actions_table.setItem(row, 5, QTableWidgetItem(action.get("scheduler_task_id") or "-"))
            self.actions_table.setItem(row, 6, QTableWidgetItem(action.get("input_path", "")))
            self.actions_table.setItem(row, 7, QTableWidgetItem(action.get("output_path", "")))
            self.actions_table.setItem(row, 8, QTableWidgetItem(action.get("message", "")))

    @staticmethod
    def _format_time(iso_value: str) -> str:
        if not iso_value:
            return "-"
        try:
            dt = datetime.fromisoformat(iso_value)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return iso_value

    def closeEvent(self, event):
        self.refresh_timer.stop()
        super().closeEvent(event)
