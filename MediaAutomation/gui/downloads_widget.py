"""
Downloads tab widget.

Lets users:
- Type a movie/show query
- Search across available tools
- Create a tracked download job
- Monitor job status and manager attempts in real time
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from datetime import datetime
import threading


class _DownloadsSignals(QObject):
    """Thread-safe signals for background search callbacks."""

    search_completed = pyqtSignal(dict)
    search_failed = pyqtSignal(str)


class DownloadsWidget(QWidget):
    """UI for search + download-job creation and tracking."""

    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager
        self.signals = _DownloadsSignals()

        self.signals.search_completed.connect(self._on_search_completed)
        self.signals.search_failed.connect(self._on_search_failed)

        self._setup_ui()
        self._refresh_manager_choices()
        self._refresh_jobs_table()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_jobs_table)
        self.refresh_timer.start(2000)

    def _setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(self._build_search_group())
        layout.addWidget(self._build_results_group())
        layout.addWidget(self._build_jobs_group())

        self.setLayout(layout)

    def _build_search_group(self) -> QGroupBox:
        group = QGroupBox("Search & Create Download Job")
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Title:"))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Type a movie, show, artist, or book title...")
        row1.addWidget(self.query_input)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Type:"))
        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems(["movie", "show", "music", "book", "generic"])
        self.content_type_combo.currentTextChanged.connect(lambda _: self._refresh_manager_choices())
        row2.addWidget(self.content_type_combo)

        row2.addWidget(QLabel("Manager:"))
        self.manager_combo = QComboBox()
        row2.addWidget(self.manager_combo)

        row2.addStretch()

        self.search_btn = QPushButton("Search Sources")
        self.search_btn.clicked.connect(self._run_search)
        row2.addWidget(self.search_btn)

        self.create_job_btn = QPushButton("Create Download Job")
        self.create_job_btn.setStyleSheet("background-color: #28A745;")
        self.create_job_btn.clicked.connect(self._create_job)
        row2.addWidget(self.create_job_btn)

        layout.addLayout(row2)

        self.search_status_label = QLabel("Ready")
        layout.addWidget(self.search_status_label)

        group.setLayout(layout)
        return group

    def _build_results_group(self) -> QGroupBox:
        group = QGroupBox("Search Results")
        layout = QVBoxLayout()

        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["Source", "Title", "Size", "Seeders", "Link Available"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setMaximumHeight(220)

        layout.addWidget(self.results_table)
        group.setLayout(layout)
        return group

    def _build_jobs_group(self) -> QGroupBox:
        group = QGroupBox("Download Jobs")
        layout = QVBoxLayout()

        self.jobs_table = QTableWidget(0, 8)
        self.jobs_table.setHorizontalHeaderLabels(
            ["Job ID", "Query", "Type", "Status", "Manager", "Attempts", "Updated", "Message"]
        )
        self.jobs_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.jobs_table)
        group.setLayout(layout)
        return group

    def _refresh_manager_choices(self):
        content_type = self.content_type_combo.currentText()
        managers = self.task_manager.get_available_download_managers(content_type)

        self.manager_combo.blockSignals(True)
        self.manager_combo.clear()
        self.manager_combo.addItem("auto")
        for name in managers:
            self.manager_combo.addItem(name)
        self.manager_combo.blockSignals(False)

    def _run_search(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Validation", "Enter a title to search.")
            return

        content_type = self.content_type_combo.currentText()
        self.search_status_label.setText("Searching...")
        self.search_btn.setEnabled(False)

        def _worker():
            try:
                result = self.task_manager.search_download_sources(query, content_type)
                self.signals.search_completed.emit(result)
            except Exception as e:
                self.signals.search_failed.emit(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_search_completed(self, result: dict):
        self.search_btn.setEnabled(True)
        if not result.get("success", False):
            errors = "; ".join(result.get("errors", [])) or "Search failed"
            self.search_status_label.setText(errors)
            QMessageBox.warning(self, "Search", errors)
            self._fill_results([])
            return

        sources = result.get("sources", [])
        self.search_status_label.setText(f"Found {len(sources)} source entries")
        self._fill_results(sources)

    def _on_search_failed(self, error_message: str):
        self.search_btn.setEnabled(True)
        self.search_status_label.setText(f"Search failed: {error_message}")
        QMessageBox.critical(self, "Search Error", error_message)

    def _fill_results(self, rows):
        self.results_table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            self.results_table.setItem(row, 0, QTableWidgetItem(str(item.get("source", ""))))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(item.get("title", ""))))

            size = item.get("size", 0)
            size_str = self._format_size(size)
            self.results_table.setItem(row, 2, QTableWidgetItem(size_str))

            self.results_table.setItem(row, 3, QTableWidgetItem(str(item.get("seeders", 0))))
            has_link = "Yes" if item.get("magnet_url") else "No"
            self.results_table.setItem(row, 4, QTableWidgetItem(has_link))

    def _create_job(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Validation", "Enter a title first.")
            return

        content_type = self.content_type_combo.currentText()
        selected_manager = self.manager_combo.currentText()
        preferred = None if selected_manager == "auto" else selected_manager

        job_id = self.task_manager.create_download_job(
            query=query,
            content_type=content_type,
            preferred_manager=preferred,
        )

        self._refresh_jobs_table()
        QMessageBox.information(self, "Job Created", f"Created job {job_id}")

    def _refresh_jobs_table(self):
        jobs = self.task_manager.get_download_jobs()
        # Newest first
        ordered = sorted(jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)

        self.jobs_table.setRowCount(len(ordered))
        for row, job in enumerate(ordered):
            self.jobs_table.setItem(row, 0, QTableWidgetItem(job.get("job_id", "")))
            self.jobs_table.setItem(row, 1, QTableWidgetItem(job.get("query", "")))
            self.jobs_table.setItem(row, 2, QTableWidgetItem(job.get("content_type", "")))

            status_item = QTableWidgetItem(job.get("status", ""))
            self.jobs_table.setItem(row, 3, status_item)

            self.jobs_table.setItem(row, 4, QTableWidgetItem(job.get("selected_manager") or "-"))
            self.jobs_table.setItem(row, 5, QTableWidgetItem(str(job.get("attempts", 0))))
            self.jobs_table.setItem(row, 6, QTableWidgetItem(self._format_time(job.get("updated_at", ""))))
            self.jobs_table.setItem(row, 7, QTableWidgetItem(job.get("message", "")))

    @staticmethod
    def _format_size(size_value) -> str:
        try:
            size = float(size_value)
        except Exception:
            return "-"
        if size <= 0:
            return "-"
        units = ["B", "KB", "MB", "GB", "TB"]
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024.0
            idx += 1
        return f"{size:.1f} {units[idx]}"

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
