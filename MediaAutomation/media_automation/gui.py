from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

from .app_runner import execute_pipeline

try:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal  # type: ignore[reportMissingImports]
    from PyQt6.QtWidgets import (  # type: ignore[reportMissingImports]
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QTabWidget,
        QTextBrowser,
        QWidget,
    )
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "PyQt6 is required for GUI mode. Install with: pip install PyQt6 PyQt6-WebEngine"
    ) from exc

try:
    from PyQt6.QtCore import QUrl  # type: ignore[reportMissingImports]
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore[reportMissingImports]
except ModuleNotFoundError:
    QUrl = None
    QWebEngineView = None


class PipelineWorker(QObject):
    finished = pyqtSignal(int, str)

    def __init__(self, config_path: Path, dry_run: bool, job_name: str | None, plugins: Iterable[str]) -> None:
        super().__init__()
        self.config_path = config_path
        self.dry_run = dry_run
        self.job_name = job_name
        self.plugins = list(plugins)

    def run(self) -> None:
        code, lines = execute_pipeline(
            config_path=self.config_path,
            dry_run_override=self.dry_run,
            only_job=self.job_name,
            plugins=self.plugins,
        )
        self.finished.emit(code, "\n".join(lines))


class MainWindow(QMainWindow):
    def __init__(self, config_path: Path, dry_run_default: bool, plugins: list[str]) -> None:
        super().__init__()
        self.setWindowTitle("Media Automation Console")
        self.resize(1200, 760)

        self.thread: QThread | None = None
        self.worker: PipelineWorker | None = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.pipeline_tab = QWidget()
        self.web_tab = QWidget()
        self.tabs.addTab(self.pipeline_tab, "Pipeline")
        self.tabs.addTab(self.web_tab, "Web Tools")

        self.config_path_input = QLineEdit(str(config_path))
        self.job_select = QComboBox()
        self.job_select.addItem("All jobs", "")
        self.dry_run_checkbox = QCheckBox("Dry run")
        self.dry_run_checkbox.setChecked(dry_run_default)
        self.plugins_input = QLineEdit(",".join(plugins))
        self.output_log = QPlainTextEdit()
        self.output_log.setReadOnly(True)

        self._build_pipeline_ui()
        self._build_web_ui()
        self._reload_job_names()

    def _build_pipeline_ui(self) -> None:
        layout = QGridLayout(self.pipeline_tab)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_config)

        refresh_button = QPushButton("Reload Jobs")
        refresh_button.clicked.connect(self._reload_job_names)

        run_button = QPushButton("Run Pipeline")
        run_button.clicked.connect(self._run_pipeline)

        layout.addWidget(QLabel("Config file"), 0, 0)
        layout.addWidget(self.config_path_input, 0, 1)
        layout.addWidget(browse_button, 0, 2)

        layout.addWidget(QLabel("Job"), 1, 0)
        layout.addWidget(self.job_select, 1, 1)
        layout.addWidget(refresh_button, 1, 2)

        layout.addWidget(self.dry_run_checkbox, 2, 1)

        layout.addWidget(QLabel("Plugins (comma-separated import paths)"), 3, 0)
        layout.addWidget(self.plugins_input, 3, 1, 1, 2)

        layout.addWidget(run_button, 4, 0, 1, 3)
        layout.addWidget(self.output_log, 5, 0, 1, 3)

    def _build_web_ui(self) -> None:
        layout = QGridLayout(self.web_tab)
        self.web_url_input = QLineEdit("https://example.com")
        open_button = QPushButton("Open")
        open_button.clicked.connect(self._open_web_url)

        layout.addWidget(QLabel("Tool URL"), 0, 0)
        layout.addWidget(self.web_url_input, 0, 1)
        layout.addWidget(open_button, 0, 2)

        if QWebEngineView and QUrl:
            self.web_view = QWebEngineView()
            self.web_view.setUrl(QUrl(self.web_url_input.text().strip()))
            layout.addWidget(self.web_view, 1, 0, 1, 3)
        else:
            self.web_view = None
            fallback = QTextBrowser()
            fallback.setPlainText(
                "PyQt6-WebEngine is not installed.\n"
                "Install with: pip install PyQt6-WebEngine\n"
                "You can still copy URLs from this tab and open them externally."
            )
            layout.addWidget(fallback, 1, 0, 1, 3)

    def _browse_config(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select config file",
            str(Path(self.config_path_input.text()).parent),
            "JSON (*.json)",
        )
        if selected:
            self.config_path_input.setText(selected)
            self._reload_job_names()

    def _reload_job_names(self) -> None:
        path = Path(self.config_path_input.text().strip())
        current = self.job_select.currentData()
        self.job_select.clear()
        self.job_select.addItem("All jobs", "")

        if not path.exists():
            return

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return

        for job in raw.get("jobs", []):
            name = job.get("name")
            if isinstance(name, str) and name.strip():
                self.job_select.addItem(name, name)

        if current:
            idx = self.job_select.findData(current)
            if idx >= 0:
                self.job_select.setCurrentIndex(idx)

    def _run_pipeline(self) -> None:
        config_path = Path(self.config_path_input.text().strip())
        if not config_path.exists():
            QMessageBox.critical(self, "Config Missing", f"Config file not found: {config_path}")
            return

        if self.thread is not None and self.thread.isRunning():
            QMessageBox.warning(self, "Busy", "A pipeline run is already in progress.")
            return

        self.output_log.appendPlainText(f"Starting run with config: {config_path}")

        selected_job = self.job_select.currentData()
        job_name = selected_job if isinstance(selected_job, str) and selected_job else None
        plugins = [p.strip() for p in self.plugins_input.text().split(",") if p.strip()]

        self.thread = QThread(self)
        self.worker = PipelineWorker(
            config_path=config_path,
            dry_run=self.dry_run_checkbox.isChecked(),
            job_name=job_name,
            plugins=plugins,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_pipeline_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_pipeline_finished(self, code: int, output_text: str) -> None:
        self.output_log.appendPlainText(output_text)
        self.output_log.appendPlainText(f"Run completed with exit code {code}\n")
        self.thread = None
        self.worker = None

    def _open_web_url(self) -> None:
        url_text = self.web_url_input.text().strip()
        if not url_text:
            return
        if self.web_view and QUrl:
            self.web_view.setUrl(QUrl(url_text))


def launch_gui(config_path: Path, dry_run_default: bool, plugins: list[str]) -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(config_path=config_path, dry_run_default=dry_run_default, plugins=plugins)
    window.show()
    return app.exec()
