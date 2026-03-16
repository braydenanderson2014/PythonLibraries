from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from typing import Any, Callable

from otterforge.api.facade import OtterForgeAPI

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSplitter,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:
    QApplication = object  # type: ignore[assignment]
    QCheckBox = object  # type: ignore[assignment]
    QComboBox = object  # type: ignore[assignment]
    QFileDialog = object  # type: ignore[assignment]
    QFormLayout = object  # type: ignore[assignment]
    QGroupBox = object  # type: ignore[assignment]
    QHBoxLayout = object  # type: ignore[assignment]
    QLabel = object  # type: ignore[assignment]
    QLineEdit = object  # type: ignore[assignment]
    QMainWindow = object  # type: ignore[assignment]
    QMessageBox = object  # type: ignore[assignment]
    QProgressBar = object  # type: ignore[assignment]
    QPushButton = object  # type: ignore[assignment]
    QScrollArea = object  # type: ignore[assignment]
    QSplitter = object  # type: ignore[assignment]
    QTabWidget = object  # type: ignore[assignment]
    QTextEdit = object  # type: ignore[assignment]
    QVBoxLayout = object  # type: ignore[assignment]
    QWidget = object  # type: ignore[assignment]
    Qt = object  # type: ignore[assignment]
    QTimer = object  # type: ignore[assignment]
    QFont = object  # type: ignore[assignment]
    PYQT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scroll(widget: QWidget) -> QScrollArea:
    """Wrap *widget* in a scroll area so tall forms don't get clipped."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(widget)
    return area


if PYQT_AVAILABLE:
    class MainWindow(QMainWindow):
        """OtterForge main window - Build Automation Platform."""

        def __init__(self, api: OtterForgeAPI | None = None) -> None:
            super().__init__()
            self.api = api or OtterForgeAPI()
            self.last_scan_result: dict[str, Any] | None = None
            self.last_organization_plan: dict[str, Any] | None = None
            self.module_catalog: dict[str, dict[str, Any]] = {}
            self._op_history: list[dict[str, Any]] = []
            self.setWindowTitle("OtterForge - Build Automation Platform")
            self.resize(1120, 820)
            self._build_ui()
            self._refresh_all()

        # ------------------------------------------------------------------ #
        # UI construction                                                      #
        # ------------------------------------------------------------------ #

        def _build_ui(self) -> None:
            central = QWidget(self)
            root = QVBoxLayout(central)
            root.setContentsMargins(4, 4, 4, 4)
            root.setSpacing(4)

            self.tabs = QTabWidget(self)
            self.tabs.addTab(self._build_runtime_tab(),    "Runtime")
            self.tabs.addTab(self._build_build_tab(),      "Build")
            self.tabs.addTab(self._build_quality_tab(),    "Tests & Quality")
            self.tabs.addTab(self._build_security_tab(),   "Security")
            self.tabs.addTab(self._build_assets_tab(),     "Assets")
            self.tabs.addTab(self._build_toolchain_tab(),  "Toolchain")
            self.tabs.addTab(self._build_profiles_tab(),   "Profiles")
            self.tabs.addTab(self._build_matrix_ci_tab(),  "Matrix & CI")
            self.tabs.addTab(self._build_schema_tab(),     "Schema")
            self.tabs.addTab(self._build_organizer_tab(),  "Organizer")
            self.tabs.addTab(self._build_mcp_tab(),        "MCP")
            root.addWidget(self.tabs)
            root.addWidget(self._build_history_panel())

            self.setCentralWidget(central)
            self._busy_label = QLabel("")
            self._busy_progress = QProgressBar(self)
            self._busy_progress.setFixedWidth(220)
            self._busy_progress.setTextVisible(False)
            self._busy_progress.setRange(0, 100)
            self._busy_progress.setValue(0)
            self._busy_progress.setVisible(False)
            self.statusBar().addPermanentWidget(self._busy_label)
            self.statusBar().addPermanentWidget(self._busy_progress)
            self.statusBar().showMessage("OtterForge ready", 3000)
        # ---- Runtime -------------------------------------------------------

        def _build_runtime_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            info_group = QGroupBox("Storage & Server Status")
            info_form = QFormLayout(info_group)
            self.backend_value = QLabel("-")
            self.config_path_value = QLabel("-")
            self.mcp_value = QLabel("-")
            self.notif_status_value = QLabel("-")
            info_form.addRow("Active Backend:", self.backend_value)
            info_form.addRow("Config Path:", self.config_path_value)
            info_form.addRow("MCP Server:", self.mcp_value)
            info_form.addRow("Build Notifications:", self.notif_status_value)
            layout.addWidget(info_group)

            backend_group = QGroupBox("Switch / Migrate Backend")
            backend_form = QFormLayout(backend_group)
            self.backend_selector = QComboBox()
            self.backend_selector.addItems(["json", "sql"])
            self.backend_selector.setToolTip("Choose json (file-based) or sql (SQLite) storage.")
            backend_form.addRow("Target Backend:", self.backend_selector)

            backend_buttons = QHBoxLayout()
            self.apply_backend_button = QPushButton("Apply (switch now)")
            self.apply_backend_button.setToolTip("Switch the active backend without migrating existing data.")
            self.apply_backend_button.clicked.connect(self._apply_backend)
            backend_buttons.addWidget(self.apply_backend_button)

            self.migrate_backend_button = QPushButton("Migrate (copy data)")
            self.migrate_backend_button.setToolTip("Copy all current state to the new backend, then switch.")
            self.migrate_backend_button.clicked.connect(self._migrate_backend)
            backend_buttons.addWidget(self.migrate_backend_button)

            self.refresh_runtime_button = QPushButton("Refresh")
            self.refresh_runtime_button.clicked.connect(self._refresh_runtime)
            backend_buttons.addWidget(self.refresh_runtime_button)
            backend_form.addRow(backend_buttons)
            layout.addWidget(backend_group)

            notif_group = QGroupBox("Build Notifications")
            notif_form = QFormLayout(notif_group)
            self.notif_enabled_checkbox = QCheckBox("Enable desktop / terminal notifications after every build")
            self.notif_webhook_input = QLineEdit()
            self.notif_webhook_input.setPlaceholderText("https://hooks.slack.com/...  (leave blank to disable)")
            self.notif_webhook_input.setToolTip("POST build results as JSON to this URL. Leave blank to skip.")
            notif_form.addRow(self.notif_enabled_checkbox)
            notif_form.addRow("Webhook URL:", self.notif_webhook_input)

            notif_buttons = QHBoxLayout()
            save_notif_button = QPushButton("Save Notification Settings")
            save_notif_button.clicked.connect(self._save_notification_config)
            notif_buttons.addWidget(save_notif_button)
            load_notif_button = QPushButton("Load Current")
            load_notif_button.clicked.connect(self._load_notification_config)
            notif_buttons.addWidget(load_notif_button)
            notif_form.addRow(notif_buttons)
            layout.addWidget(notif_group)

            self.runtime_output = QTextEdit()
            self.runtime_output.setReadOnly(True)
            self.runtime_output.setPlaceholderText("Runtime status will appear here...")
            layout.addWidget(self.runtime_output)
            return container

        # ---- Build ---------------------------------------------------------

        def _build_build_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            builder_group = QGroupBox("Builder Selection")
            builder_layout = QFormLayout(builder_group)
            self.builder_selector = QComboBox()
            self.builder_selector.setToolTip("Select the build tool. 'auto' detects from project files.")
            builder_layout.addRow("Builder:", self.builder_selector)

            builder_buttons = QHBoxLayout()
            refresh_builders_button = QPushButton("Refresh List")
            refresh_builders_button.clicked.connect(self._refresh_builders)
            builder_buttons.addWidget(refresh_builders_button)
            inspect_builder_button = QPushButton("Inspect Selected")
            inspect_builder_button.setToolTip("Show options and availability details for the selected builder.")
            inspect_builder_button.clicked.connect(self._inspect_builder)
            builder_buttons.addWidget(inspect_builder_button)
            builder_layout.addRow(builder_buttons)
            layout.addWidget(builder_group)

            run_group = QGroupBox("Build Options")
            run_layout = QFormLayout(run_group)

            # Project path row with browse
            self.project_path_input = QLineEdit(".")
            self.project_path_input.setToolTip("Root directory of your project.")
            proj_row = QHBoxLayout()
            proj_row.addWidget(self.project_path_input)
            browse_proj = QPushButton("Browse...")
            browse_proj.setFixedWidth(72)
            browse_proj.clicked.connect(lambda: self._browse_dir(self.project_path_input))
            proj_row.addWidget(browse_proj)
            run_layout.addRow("Project Path:", proj_row)

            # Entry script row with browse
            self.entry_script_input = QLineEdit("main.py")
            self.entry_script_input.setToolTip("Main script or source file to build from.")
            entry_row = QHBoxLayout()
            entry_row.addWidget(self.entry_script_input)
            browse_entry = QPushButton("Browse...")
            browse_entry.setFixedWidth(72)
            browse_entry.clicked.connect(lambda: self._browse_file(self.entry_script_input))
            entry_row.addWidget(browse_entry)
            run_layout.addRow("Entry Script:", entry_row)

            self.executable_name_input = QLineEdit()
            self.executable_name_input.setPlaceholderText("MyApp  (leave blank to use project name)")
            run_layout.addRow("Executable Name:", self.executable_name_input)

            self.build_mode_selector = QComboBox()
            self.build_mode_selector.addItems(["onefile", "onedir"])
            self.build_mode_selector.setToolTip("onefile bundles into a single executable; onedir creates a folder.")
            run_layout.addRow("Bundle Mode:", self.build_mode_selector)

            self.console_mode_checkbox = QCheckBox("Show console window")
            self.console_mode_checkbox.setChecked(True)
            self.console_mode_checkbox.setToolTip("Uncheck for GUI apps to suppress the terminal window.")
            run_layout.addRow(self.console_mode_checkbox)

            # Icon path with browse
            self.icon_path_input = QLineEdit()
            self.icon_path_input.setPlaceholderText("path/to/icon.ico  (optional)")
            icon_row = QHBoxLayout()
            icon_row.addWidget(self.icon_path_input)
            browse_icon = QPushButton("Browse...")
            browse_icon.setFixedWidth(72)
            browse_icon.clicked.connect(
                lambda: self._browse_file(self.icon_path_input, filter="Icons (*.ico *.icns *.png)")
            )
            icon_row.addWidget(browse_icon)
            run_layout.addRow("Icon Path:", icon_row)

            # Output dir with browse
            self.output_dir_input = QLineEdit()
            self.output_dir_input.setPlaceholderText("dist  (leave blank for builder default)")
            out_row = QHBoxLayout()
            out_row.addWidget(self.output_dir_input)
            browse_out = QPushButton("Browse...")
            browse_out.setFixedWidth(72)
            browse_out.clicked.connect(lambda: self._browse_dir(self.output_dir_input))
            out_row.addWidget(browse_out)
            run_layout.addRow("Output Directory:", out_row)

            self.compiler_config_name_input = QLineEdit()
            self.compiler_config_name_input.setPlaceholderText("Saved compiler config name  (optional)")
            self.compiler_config_name_input.setToolTip(
                "Apply a named compiler config saved under the Toolchain tab."
            )
            run_layout.addRow("Compiler Config:", self.compiler_config_name_input)

            self.extra_builder_args_input = QLineEdit()
            self.extra_builder_args_input.setPlaceholderText("--add-data src;.  --hidden-import module")
            self.extra_builder_args_input.setToolTip(
                "Extra arguments passed verbatim to the builder. Shell-quote as needed."
            )
            run_layout.addRow("Extra Args:", self.extra_builder_args_input)

            self.clean_build_checkbox = QCheckBox("Clean build (remove previous output first)")
            run_layout.addRow(self.clean_build_checkbox)

            self.dry_run_checkbox = QCheckBox("Dry-run  (print command only, do not execute builder)")
            self.dry_run_checkbox.setChecked(True)
            self.dry_run_checkbox.setToolTip(
                "When checked the build command is shown but not run. "
                "Uncheck to perform a real build."
            )
            run_layout.addRow(self.dry_run_checkbox)

            self.container_build_checkbox = QCheckBox(
                "Run inside Docker container  (requires Container config on the Matrix & CI tab)"
            )
            self.container_build_checkbox.setToolTip(
                "Mount the project into a Docker container and run the build command there."
            )
            run_layout.addRow(self.container_build_checkbox)

            run_buttons = QHBoxLayout()
            self.run_build_button = QPushButton("Run Build")
            self.run_build_button.setToolTip("Execute the build (or dry-run if checked above).")
            self.run_build_button.clicked.connect(self._run_build)
            run_buttons.addWidget(self.run_build_button)

            sandbox_button = QPushButton("Launch Last Artifact in Sandbox")
            sandbox_button.setToolTip(
                "Open the last built artifact inside Windows Sandbox for safe testing."
            )
            sandbox_button.clicked.connect(self._launch_sandbox_from_build)
            run_buttons.addWidget(sandbox_button)
            run_layout.addRow(run_buttons)

            self.build_hint_label = QLabel("")
            self.build_hint_label.setStyleSheet("color: #c0392b; font-size: 11px;")
            run_layout.addRow(self.build_hint_label)
            layout.addWidget(run_group)

            self.build_result_label = QLabel("")
            font = self.build_result_label.font()
            font.setBold(True)
            self.build_result_label.setFont(font)
            layout.addWidget(self.build_result_label)

            self.build_output = QTextEdit()
            self.build_output.setReadOnly(True)
            self.build_output.setPlaceholderText("Build results will appear here...")
            layout.addWidget(self.build_output)
            self._last_artifact_paths: list[str] = []

            # Wire build guardrails
            self.project_path_input.textChanged.connect(self._validate_build_inputs)
            self.entry_script_input.textChanged.connect(self._validate_build_inputs)
            self._validate_build_inputs()
            return container

        # ---- Tests & Quality -----------------------------------------------

        def _build_quality_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            test_group = QGroupBox("Test Runner Gate")
            test_form = QFormLayout(test_group)

            self.test_project_path_input = QLineEdit(".")
            self.test_project_path_input.setToolTip("Project directory where tests should run.")
            test_proj_row = QHBoxLayout()
            test_proj_row.addWidget(self.test_project_path_input)
            browse_test_proj = QPushButton("Browse...")
            browse_test_proj.setFixedWidth(72)
            browse_test_proj.clicked.connect(lambda: self._browse_dir(self.test_project_path_input))
            test_proj_row.addWidget(browse_test_proj)
            test_form.addRow("Project Path:", test_proj_row)

            self.test_command_input = QLineEdit("pytest")
            self.test_command_input.setPlaceholderText("pytest  or  python -m pytest --tb=short")
            self.test_command_input.setToolTip("Shell command used to run the test suite.")
            test_form.addRow("Test Command:", self.test_command_input)

            self.test_gate_checkbox = QCheckBox(
                "Block build if tests fail  (gate is active for run_build calls too)"
            )
            self.test_gate_checkbox.setToolTip(
                "When checked, a failing test suite will prevent the build from proceeding."
            )
            test_form.addRow(self.test_gate_checkbox)

            test_buttons = QHBoxLayout()
            save_test_cfg_button = QPushButton("Save Test Config")
            save_test_cfg_button.clicked.connect(self._save_test_config)
            test_buttons.addWidget(save_test_cfg_button)

            load_test_cfg_button = QPushButton("Load Config")
            load_test_cfg_button.clicked.connect(self._load_test_config)
            test_buttons.addWidget(load_test_cfg_button)

            self.run_tests_button = QPushButton("Run Tests Now")
            self.run_tests_button.setToolTip("Execute the test command immediately and show results.")
            self.run_tests_button.clicked.connect(self._run_tests)
            test_buttons.addWidget(self.run_tests_button)
            test_form.addRow(test_buttons)

            self.tests_hint_label = QLabel("")
            self.tests_hint_label.setStyleSheet("color: #c0392b; font-size: 11px;")
            test_form.addRow(self.tests_hint_label)
            layout.addWidget(test_group)

            audit_group = QGroupBox("Dependency Audit")
            audit_form = QFormLayout(audit_group)

            self.audit_project_path_input = QLineEdit(".")
            audit_proj_row = QHBoxLayout()
            audit_proj_row.addWidget(self.audit_project_path_input)
            browse_audit = QPushButton("Browse...")
            browse_audit.setFixedWidth(72)
            browse_audit.clicked.connect(lambda: self._browse_dir(self.audit_project_path_input))
            audit_proj_row.addWidget(browse_audit)
            audit_form.addRow("Project Path:", audit_proj_row)

            self.audit_requirements_input = QLineEdit()
            self.audit_requirements_input.setPlaceholderText("requirements.txt  (leave blank for project default)")
            req_row = QHBoxLayout()
            req_row.addWidget(self.audit_requirements_input)
            browse_req = QPushButton("Browse...")
            browse_req.setFixedWidth(72)
            browse_req.clicked.connect(
                lambda: self._browse_file(self.audit_requirements_input, filter="Text (*.txt)")
            )
            req_row.addWidget(browse_req)
            audit_form.addRow("Requirements File:", req_row)

            self.audit_severity_selector = QComboBox()
            self.audit_severity_selector.addItems(["critical", "high", "medium", "low", "info"])
            self.audit_severity_selector.setCurrentText("high")
            self.audit_severity_selector.setToolTip(
                "Vulnerabilities at or above this severity will count as gate failures."
            )
            audit_form.addRow("Minimum Severity:", self.audit_severity_selector)

            self.audit_gate_checkbox = QCheckBox("Block build on audit failures")
            audit_form.addRow(self.audit_gate_checkbox)

            audit_buttons = QHBoxLayout()
            save_audit_cfg = QPushButton("Save Audit Config")
            save_audit_cfg.clicked.connect(self._save_audit_config)
            audit_buttons.addWidget(save_audit_cfg)

            load_audit_cfg = QPushButton("Load Config")
            load_audit_cfg.clicked.connect(self._load_audit_config)
            audit_buttons.addWidget(load_audit_cfg)

            self.run_audit_button = QPushButton("Run Audit Now")
            self.run_audit_button.setToolTip("Scan dependencies for known vulnerabilities using pip-audit or safety.")
            self.run_audit_button.clicked.connect(self._run_audit)
            audit_buttons.addWidget(self.run_audit_button)
            audit_form.addRow(audit_buttons)

            self.audit_hint_label = QLabel("")
            self.audit_hint_label.setStyleSheet("color: #c0392b; font-size: 11px;")
            audit_form.addRow(self.audit_hint_label)
            layout.addWidget(audit_group)

            self.quality_result_label = QLabel("")
            font = self.quality_result_label.font()
            font.setBold(True)
            self.quality_result_label.setFont(font)
            layout.addWidget(self.quality_result_label)

            self.quality_output = QTextEdit()
            self.quality_output.setReadOnly(True)
            self.quality_output.setPlaceholderText("Test and audit results will appear here...")
            layout.addWidget(self.quality_output)

            # Wire quality guardrails
            self.test_project_path_input.textChanged.connect(self._validate_quality_inputs)
            self.test_command_input.textChanged.connect(self._validate_quality_inputs)
            self.audit_project_path_input.textChanged.connect(self._validate_quality_inputs)
            self._validate_quality_inputs()
            return container

        # ---- Security ------------------------------------------------------

        def _build_security_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            sign_config_group = QGroupBox("Signing Configuration")
            sign_config_form = QFormLayout(sign_config_group)

            self.sign_project_path_input = QLineEdit(".")
            sign_proj_row = QHBoxLayout()
            sign_proj_row.addWidget(self.sign_project_path_input)
            browse_sign_proj = QPushButton("Browse...")
            browse_sign_proj.setFixedWidth(72)
            browse_sign_proj.clicked.connect(lambda: self._browse_dir(self.sign_project_path_input))
            sign_proj_row.addWidget(browse_sign_proj)
            sign_config_form.addRow("Project Path:", sign_proj_row)

            self.signing_tool_selector = QComboBox()
            self.signing_tool_selector.addItems(["signtool", "codesign", "gpg"])
            self.signing_tool_selector.setToolTip(
                "signtool: Windows;  codesign: macOS;  gpg: cross-platform detached signature."
            )
            sign_config_form.addRow("Signing Tool:", self.signing_tool_selector)

            self.signing_cert_input = QLineEdit()
            self.signing_cert_input.setPlaceholderText(".pfx or .p12 certificate path  (signtool only)")
            cert_row = QHBoxLayout()
            cert_row.addWidget(self.signing_cert_input)
            browse_cert = QPushButton("Browse...")
            browse_cert.setFixedWidth(72)
            browse_cert.clicked.connect(
                lambda: self._browse_file(self.signing_cert_input, filter="Certificates (*.pfx *.p12 *.pem)")
            )
            cert_row.addWidget(browse_cert)
            sign_config_form.addRow("Certificate:", cert_row)

            self.signing_timestamp_input = QLineEdit()
            self.signing_timestamp_input.setPlaceholderText(
                "http://timestamp.digicert.com  (signtool, optional)"
            )
            sign_config_form.addRow("Timestamp URL:", self.signing_timestamp_input)

            self.signing_developer_id_input = QLineEdit()
            self.signing_developer_id_input.setPlaceholderText(
                "Developer ID Application: ...  (codesign only)"
            )
            sign_config_form.addRow("Developer ID:", self.signing_developer_id_input)

            self.signing_key_id_input = QLineEdit()
            self.signing_key_id_input.setPlaceholderText("GPG key fingerprint or email  (gpg only)")
            sign_config_form.addRow("GPG Key ID:", self.signing_key_id_input)

            sign_cfg_buttons = QHBoxLayout()
            save_sign_cfg = QPushButton("Save Signing Config")
            save_sign_cfg.clicked.connect(self._save_signing_config)
            sign_cfg_buttons.addWidget(save_sign_cfg)
            load_sign_cfg = QPushButton("Load Config")
            load_sign_cfg.clicked.connect(self._load_signing_config)
            sign_cfg_buttons.addWidget(load_sign_cfg)
            sign_config_form.addRow(sign_cfg_buttons)
            layout.addWidget(sign_config_group)

            sign_run_group = QGroupBox("Sign Artifacts")
            sign_run_form = QFormLayout(sign_run_group)
            self.sign_artifacts_input = QTextEdit()
            self.sign_artifacts_input.setPlaceholderText(
                "One artifact path per line:\ndist/MyApp.exe\ndist/MyApp.zip"
            )
            self.sign_artifacts_input.setFixedHeight(90)
            sign_run_form.addRow("Artifact Paths:", self.sign_artifacts_input)

            self.sign_btn = QPushButton("Sign Artifacts")
            self.sign_btn.setToolTip("Sign each listed artifact using the configured tool.")
            self.sign_btn.clicked.connect(self._sign_artifacts)
            sign_run_form.addRow(self.sign_btn)

            self.security_hint_label = QLabel("")
            self.security_hint_label.setStyleSheet("color: #c0392b; font-size: 11px;")
            sign_run_form.addRow(self.security_hint_label)
            layout.addWidget(sign_run_group)

            self.security_result_label = QLabel("")
            font = self.security_result_label.font()
            font.setBold(True)
            self.security_result_label.setFont(font)
            layout.addWidget(self.security_result_label)

            self.security_output = QTextEdit()
            self.security_output.setReadOnly(True)
            self.security_output.setPlaceholderText("Signing results will appear here...")
            layout.addWidget(self.security_output)

            # Wire security guardrails
            self.sign_artifacts_input.textChanged.connect(self._validate_security_inputs)
            self.signing_cert_input.textChanged.connect(self._validate_security_inputs)
            self.signing_tool_selector.currentTextChanged.connect(self._validate_security_inputs)
            self._validate_security_inputs()
            self.signing_developer_id_input.textChanged.connect(self._validate_security_inputs)
            self.signing_key_id_input.textChanged.connect(self._validate_security_inputs)
            return container

        # ---- Assets --------------------------------------------------------

        def _build_assets_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            icon_group = QGroupBox("Icon Preparation")
            icon_form = QFormLayout(icon_group)

            self.icon_source_input = QLineEdit()
            self.icon_source_input.setPlaceholderText("path/to/source.png")
            self.icon_source_input.setToolTip("Source image to convert (PNG, JPG or SVG). Requires Pillow.")
            icon_source_row = QHBoxLayout()
            icon_source_row.addWidget(self.icon_source_input)
            browse_icon_source = QPushButton("Browse...")
            browse_icon_source.setFixedWidth(72)
            browse_icon_source.clicked.connect(
                lambda: self._browse_file(
                    self.icon_source_input, filter="Images (*.png *.jpg *.jpeg *.svg)"
                )
            )
            icon_source_row.addWidget(browse_icon_source)
            icon_form.addRow("Source Image:", icon_source_row)

            self.icon_platform_selector = QComboBox()
            self.icon_platform_selector.addItems(["windows", "macos", "linux"])
            self.icon_platform_selector.setToolTip(
                "windows -> .ico (multi-res);  macos -> .icns;  linux -> 512x512 .png"
            )
            icon_form.addRow("Target Platform:", self.icon_platform_selector)

            icon_buttons = QHBoxLayout()
            self.prepare_icon_btn = QPushButton("Prepare Icon")
            self.prepare_icon_btn.setToolTip(
                "Convert the source image to the platform-appropriate icon format."
            )
            self.prepare_icon_btn.clicked.connect(self._prepare_icon)
            icon_buttons.addWidget(self.prepare_icon_btn)

            list_assets_button = QPushButton("List Cached Assets")
            list_assets_button.setToolTip("Show all previously generated icon files for this source image.")
            list_assets_button.clicked.connect(self._list_assets)
            icon_buttons.addWidget(list_assets_button)
            icon_form.addRow(icon_buttons)

            self.assets_hint_label = QLabel("")
            self.assets_hint_label.setStyleSheet("color: #c0392b; font-size: 11px;")
            icon_form.addRow(self.assets_hint_label)
            layout.addWidget(icon_group)

            info_label = QLabel(
                "Tip: Pillow must be installed for icon conversion.  "
                "Run  pip install Pillow  if the command reports an error."
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

            self.assets_result_label = QLabel("")
            font = self.assets_result_label.font()
            font.setBold(True)
            self.assets_result_label.setFont(font)
            layout.addWidget(self.assets_result_label)

            self.assets_output = QTextEdit()
            self.assets_output.setReadOnly(True)
            self.assets_output.setPlaceholderText("Asset output will appear here...")
            layout.addWidget(self.assets_output)

            # Wire assets guardrails
            self.icon_source_input.textChanged.connect(self._validate_assets_inputs)
            self._validate_assets_inputs()
            return container

        # ---- Toolchain (unchanged structure, improved labels) ---------------

        def _build_toolchain_tab(self) -> QWidget:
            from PyQt6.QtWidgets import QListWidget

            container = QWidget()
            layout = QVBoxLayout(container)

            toolchain_group = QGroupBox("Toolchain Doctor")
            toolchain_layout = QFormLayout(toolchain_group)
            toolchain_buttons = QHBoxLayout()

            refresh_toolchain_button = QPushButton("Refresh Report")
            refresh_toolchain_button.clicked.connect(self._refresh_toolchain)
            toolchain_buttons.addWidget(refresh_toolchain_button)

            doctor_toolchain_button = QPushButton("Run Doctor Check")
            doctor_toolchain_button.setToolTip(
                "Check which required tools are available and show install hints for missing ones."
            )
            doctor_toolchain_button.clicked.connect(self._refresh_toolchain)
            toolchain_buttons.addWidget(doctor_toolchain_button)
            toolchain_layout.addRow(toolchain_buttons)
            layout.addWidget(toolchain_group)

            dependency_group = QGroupBox("Unified Module Manager")
            packs_layout = QFormLayout(dependency_group)

            self.modules_path_input = QLineEdit(".")
            self.modules_path_input.setToolTip(
                "Analyze pyproject.toml, requirements files, and Python imports in this project."
            )
            modules_row = QHBoxLayout()
            modules_row.addWidget(self.modules_path_input)
            browse_modules_path = QPushButton("Browse...")
            browse_modules_path.setFixedWidth(72)
            browse_modules_path.clicked.connect(lambda: self._browse_dir(self.modules_path_input))
            modules_row.addWidget(browse_modules_path)
            packs_layout.addRow("Project Path:", modules_row)

            self.module_os_selector = QComboBox()
            self.module_os_selector.addItems(["auto", "windows", "linux", "macos"])
            self.module_os_selector.currentIndexChanged.connect(self._refresh_module_search_managers)
            self.module_os_selector.currentIndexChanged.connect(self._refresh_unified_module_catalog)

            dep_buttons = QHBoxLayout()
            list_modules_button = QPushButton("Refresh Module Inventory")
            list_modules_button.clicked.connect(self._refresh_unified_module_catalog)
            dep_buttons.addWidget(list_modules_button)
            load_missing_button = QPushButton("Load Missing Into Typed Box")
            load_missing_button.clicked.connect(self._load_missing_dependencies_into_package_fields)
            dep_buttons.addWidget(load_missing_button)
            packs_layout.addRow("Operating System:", self.module_os_selector)
            packs_layout.addRow(dep_buttons)

            self.module_inventory_list = QListWidget()
            self.module_inventory_list.setMinimumHeight(130)
            self.module_inventory_list.itemSelectionChanged.connect(self._on_selected_module_changed)
            packs_layout.addRow("Modules:", self.module_inventory_list)

            self.module_candidate_selector = QComboBox()
            self.module_candidate_selector.setToolTip(
                "Install candidate for selected module (e.g. pip/uv for Python packages)."
            )
            packs_layout.addRow("Install Candidate:", self.module_candidate_selector)

            self.pack_os_selector = QComboBox()
            self.pack_os_selector.addItems(["auto", "windows", "linux", "macos"])
            self.pack_os_selector.currentIndexChanged.connect(self._sync_module_os_selector)
            self.pack_os_selector.currentIndexChanged.connect(self._refresh_unified_module_catalog)
            self.pack_os_selector.currentIndexChanged.connect(self._refresh_module_search_managers)
            self.pack_continue_on_error_checkbox = QCheckBox("Continue installing even if a step fails")

            packs_layout.addRow("OS Alias:", self.pack_os_selector)
            packs_layout.addRow(self.pack_continue_on_error_checkbox)

            self.package_query_input = QLineEdit()
            self.package_query_input.setPlaceholderText("requests, cmake, openssl, node, ...")
            self.package_query_input.setToolTip(
                "Search and add package modules to the unified module inventory."
            )

            self.package_browser_manager_selector = QComboBox()
            self.package_browser_manager_selector.setEditable(True)
            self.package_browser_manager_selector.setToolTip(
                "Search manager. Module install candidate selection is controlled per module."
            )

            self.package_name_input = QLineEdit()
            self.package_name_input.setPlaceholderText("Package name to install")
            self.package_name_input.setToolTip("Use a search result or type a package name manually.")

            self.dependency_bulk_input = QTextEdit()
            self.dependency_bulk_input.setPlaceholderText(
                "Type package names (comma/newline separated), e.g.\nrequests\nrich\npydantic"
            )
            self.dependency_bulk_input.setFixedHeight(70)

            packs_layout.addRow("Search Query:", self.package_query_input)
            packs_layout.addRow("Package Manager:", self.package_browser_manager_selector)
            packs_layout.addRow("Package Name:", self.package_name_input)
            packs_layout.addRow("Typed Packages:", self.dependency_bulk_input)

            package_buttons = QHBoxLayout()
            refresh_pkg_managers_button = QPushButton("Refresh Managers")
            refresh_pkg_managers_button.clicked.connect(self._refresh_package_browser_managers)
            package_buttons.addWidget(refresh_pkg_managers_button)

            search_packages_button = QPushButton("Search Packages")
            search_packages_button.clicked.connect(self._search_packages_from_toolchain_tab)
            package_buttons.addWidget(search_packages_button)

            plan_pkg_install_button = QPushButton("Plan Install  (dry-run)")
            plan_pkg_install_button.clicked.connect(lambda: self._install_package_from_toolchain_tab(False))
            package_buttons.addWidget(plan_pkg_install_button)

            run_pkg_install_button = QPushButton("Run Install")
            run_pkg_install_button.clicked.connect(lambda: self._install_package_from_toolchain_tab(True))
            package_buttons.addWidget(run_pkg_install_button)

            plan_pkg_uninstall_button = QPushButton("Plan Uninstall  (dry-run)")
            plan_pkg_uninstall_button.clicked.connect(lambda: self._uninstall_package_from_toolchain_tab(False))
            package_buttons.addWidget(plan_pkg_uninstall_button)

            run_pkg_uninstall_button = QPushButton("Run Uninstall")
            run_pkg_uninstall_button.clicked.connect(lambda: self._uninstall_package_from_toolchain_tab(True))
            package_buttons.addWidget(run_pkg_uninstall_button)

            packs_layout.addRow(package_buttons)

            typed_buttons = QHBoxLayout()
            plan_typed_install_button = QPushButton("Plan Typed Install")
            plan_typed_install_button.clicked.connect(lambda: self._install_typed_dependencies_from_toolchain_tab(False))
            typed_buttons.addWidget(plan_typed_install_button)

            run_typed_install_button = QPushButton("Run Typed Install")
            run_typed_install_button.clicked.connect(lambda: self._install_typed_dependencies_from_toolchain_tab(True))
            typed_buttons.addWidget(run_typed_install_button)
            packs_layout.addRow(typed_buttons)
            layout.addWidget(dependency_group)

            self.toolchain_output = QTextEdit()
            self.toolchain_output.setReadOnly(True)
            self.toolchain_output.setPlaceholderText("Toolchain report will appear here...")
            layout.addWidget(self.toolchain_output)
            return container

        # ---- Profiles ------------------------------------------------------

        def _build_profiles_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            create_group = QGroupBox("Create Build Profile")
            create_layout = QFormLayout(create_group)
            self.profile_name_input = QLineEdit()
            self.profile_name_input.setPlaceholderText("e.g. windows-release")
            self.profile_description_input = QLineEdit()
            self.profile_description_input.setPlaceholderText("Short description of this profile")
            self.profile_settings_input = QTextEdit("{}")
            self.profile_settings_input.setPlaceholderText(
                '{"builder": "pyinstaller", "mode": "onefile", "language": "python"}'
            )
            self.profile_settings_input.setFixedHeight(90)

            create_layout.addRow("Name:", self.profile_name_input)
            create_layout.addRow("Description:", self.profile_description_input)
            create_layout.addRow("Settings (JSON):", self.profile_settings_input)

            create_button = QPushButton("Create Profile")
            create_button.clicked.connect(self._create_profile)
            create_layout.addRow(create_button)
            layout.addWidget(create_group)

            query_group = QGroupBox("Browse Profiles")
            query_layout = QFormLayout(query_group)
            self.profile_selector = QComboBox()
            query_layout.addRow("Profile:", self.profile_selector)

            query_buttons = QHBoxLayout()
            list_profiles_button = QPushButton("Refresh List")
            list_profiles_button.clicked.connect(self._list_profiles)
            query_buttons.addWidget(list_profiles_button)

            show_profile_button = QPushButton("Show Selected")
            show_profile_button.clicked.connect(self._show_profile)
            query_buttons.addWidget(show_profile_button)
            query_layout.addRow(query_buttons)
            layout.addWidget(query_group)

            self.profile_output = QTextEdit()
            self.profile_output.setReadOnly(True)
            self.profile_output.setPlaceholderText("Profile details will appear here...")
            layout.addWidget(self.profile_output)
            return container

        # ---- Matrix & CI ---------------------------------------------------

        def _build_matrix_ci_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            container_group = QGroupBox("Docker / Container Build Config")
            container_form = QFormLayout(container_group)
            self.container_project_input = QLineEdit(".")
            container_proj_row = QHBoxLayout()
            container_proj_row.addWidget(self.container_project_input)
            browse_container_proj = QPushButton("Browse...")
            browse_container_proj.setFixedWidth(72)
            browse_container_proj.clicked.connect(lambda: self._browse_dir(self.container_project_input))
            container_proj_row.addWidget(browse_container_proj)
            container_form.addRow("Project Path:", container_proj_row)

            self.container_image_input = QLineEdit()
            self.container_image_input.setPlaceholderText("python:3.12-slim  or  yourorg/builder:latest")
            self.container_image_input.setToolTip(
                "Docker image used when 'Run inside Docker' is enabled on the Build tab."
            )
            container_form.addRow("Docker Image:", self.container_image_input)

            container_buttons = QHBoxLayout()
            save_container_cfg = QPushButton("Save Container Config")
            save_container_cfg.clicked.connect(self._save_container_config)
            container_buttons.addWidget(save_container_cfg)
            load_container_cfg = QPushButton("Load Config")
            load_container_cfg.clicked.connect(self._load_container_config)
            container_buttons.addWidget(load_container_cfg)
            container_form.addRow(container_buttons)
            layout.addWidget(container_group)

            matrix_group = QGroupBox("Build Matrix  (run multiple builders / platforms sequentially)")
            matrix_form = QFormLayout(matrix_group)
            self.matrix_project_input = QLineEdit(".")
            matrix_proj_row = QHBoxLayout()
            matrix_proj_row.addWidget(self.matrix_project_input)
            browse_matrix_proj = QPushButton("Browse...")
            browse_matrix_proj.setFixedWidth(72)
            browse_matrix_proj.clicked.connect(lambda: self._browse_dir(self.matrix_project_input))
            matrix_proj_row.addWidget(browse_matrix_proj)
            matrix_form.addRow("Project Path:", matrix_proj_row)

            self.matrix_entries_input = QTextEdit()
            self.matrix_entries_input.setPlaceholderText(
                '[\n'
                '  {"builder_name": "pyinstaller", "platform": "windows", "dry_run": true},\n'
                '  {"builder_name": "pyinstaller", "platform": "linux",   "dry_run": true}\n'
                ']'
            )
            self.matrix_entries_input.setToolTip(
                "JSON array of build-request objects. Each entry is one build in the matrix."
            )
            self.matrix_entries_input.setFixedHeight(120)
            matrix_form.addRow("Matrix Entries (JSON):", self.matrix_entries_input)

            matrix_buttons = QHBoxLayout()
            define_matrix_button = QPushButton("Save Matrix Definition")
            define_matrix_button.clicked.connect(self._define_matrix)
            matrix_buttons.addWidget(define_matrix_button)

            show_matrix_button = QPushButton("Show Stored Matrix")
            show_matrix_button.clicked.connect(self._show_matrix)
            matrix_buttons.addWidget(show_matrix_button)

            run_matrix_button = QPushButton("Run Matrix Now")
            run_matrix_button.setToolTip(
                "Execute every entry in the stored matrix sequentially and show a summary."
            )
            run_matrix_button.clicked.connect(self._run_matrix)
            matrix_buttons.addWidget(run_matrix_button)
            matrix_form.addRow(matrix_buttons)
            layout.addWidget(matrix_group)

            ci_group = QGroupBox("CI Workflow Generation")
            ci_form = QFormLayout(ci_group)
            self.ci_project_input = QLineEdit(".")
            ci_proj_row = QHBoxLayout()
            ci_proj_row.addWidget(self.ci_project_input)
            browse_ci_proj = QPushButton("Browse...")
            browse_ci_proj.setFixedWidth(72)
            browse_ci_proj.clicked.connect(lambda: self._browse_dir(self.ci_project_input))
            ci_proj_row.addWidget(browse_ci_proj)
            ci_form.addRow("Project Path:", ci_proj_row)

            self.ci_provider_selector = QComboBox()
            self.ci_provider_selector.addItems(["GitHub Actions"])
            ci_form.addRow("CI Provider:", self.ci_provider_selector)

            ci_info = QLabel(
                "Profiles are read from the stored matrix above. "
                "Save the matrix first, then generate the workflow."
            )
            ci_info.setWordWrap(True)
            ci_form.addRow(ci_info)

            ci_output_row = QHBoxLayout()
            self.ci_output_path_input = QLineEdit()
            self.ci_output_path_input.setPlaceholderText(
                ".github/workflows/otterforge.yml  (leave blank for default)"
            )
            ci_output_row.addWidget(self.ci_output_path_input)
            browse_ci_out = QPushButton("Browse...")
            browse_ci_out.setFixedWidth(72)
            browse_ci_out.clicked.connect(
                lambda: self._browse_file(self.ci_output_path_input, filter="YAML (*.yml *.yaml)")
            )
            ci_output_row.addWidget(browse_ci_out)
            ci_form.addRow("Output File:", ci_output_row)

            ci_buttons = QHBoxLayout()
            generate_ci_button = QPushButton("Generate CI Workflow")
            generate_ci_button.setToolTip(
                "Write a CI pipeline YAML (e.g. GitHub Actions) based on the stored build matrix."
            )
            generate_ci_button.clicked.connect(self._generate_ci_workflow)
            ci_buttons.addWidget(generate_ci_button)

            export_profile_button = QPushButton("Export Profile to File")
            export_profile_button.setToolTip(
                "Export a named profile as a JSON file that can be committed to the repository."
            )
            export_profile_button.clicked.connect(self._export_profile_config)
            ci_buttons.addWidget(export_profile_button)
            ci_form.addRow(ci_buttons)
            layout.addWidget(ci_group)

            sandbox_group = QGroupBox("Windows Sandbox Launcher")
            sandbox_form = QFormLayout(sandbox_group)
            self.sandbox_artifact_input = QLineEdit()
            self.sandbox_artifact_input.setPlaceholderText("dist/MyApp.exe")
            sandbox_art_row = QHBoxLayout()
            sandbox_art_row.addWidget(self.sandbox_artifact_input)
            browse_sandbox = QPushButton("Browse...")
            browse_sandbox.setFixedWidth(72)
            browse_sandbox.clicked.connect(
                lambda: self._browse_file(self.sandbox_artifact_input)
            )
            sandbox_art_row.addWidget(browse_sandbox)
            sandbox_form.addRow("Artifact to Test:", sandbox_art_row)

            self.sandbox_startup_input = QLineEdit()
            self.sandbox_startup_input.setPlaceholderText(
                "C:\\Users\\WDAGUtilityAccount\\Desktop\\MyApp.exe  (optional startup command)"
            )
            sandbox_form.addRow("Startup Command:", self.sandbox_startup_input)

            sandbox_buttons = QHBoxLayout()
            sandbox_avail_button = QPushButton("Check Availability")
            sandbox_avail_button.setToolTip(
                "Check whether Windows Sandbox is enabled on this machine."
            )
            sandbox_avail_button.clicked.connect(self._check_sandbox)
            sandbox_buttons.addWidget(sandbox_avail_button)

            launch_sandbox_button = QPushButton("Launch Sandbox")
            launch_sandbox_button.setToolTip(
                "Generate a .wsb config and open the artifact inside Windows Sandbox."
            )
            launch_sandbox_button.clicked.connect(self._launch_sandbox)
            sandbox_buttons.addWidget(launch_sandbox_button)
            sandbox_form.addRow(sandbox_buttons)
            layout.addWidget(sandbox_group)

            self.matrix_ci_result_label = QLabel("")
            font = self.matrix_ci_result_label.font()
            font.setBold(True)
            self.matrix_ci_result_label.setFont(font)
            layout.addWidget(self.matrix_ci_result_label)

            self.matrix_ci_output = QTextEdit()
            self.matrix_ci_output.setReadOnly(True)
            self.matrix_ci_output.setPlaceholderText("Matrix, CI and sandbox results will appear here...")
            layout.addWidget(self.matrix_ci_output)
            return _scroll(container)

        # ---- Schema --------------------------------------------------------

        def _build_schema_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            schema_group = QGroupBox("Project Schema")
            schema_layout = QFormLayout(schema_group)

            self.scan_path_input = QLineEdit(".")
            self.scan_path_input.setToolTip("Directory to scan for sources, entrypoints, assets and docs.")
            scan_row = QHBoxLayout()
            scan_row.addWidget(self.scan_path_input)
            browse_scan = QPushButton("Browse...")
            browse_scan.setFixedWidth(72)
            browse_scan.clicked.connect(lambda: self._browse_dir(self.scan_path_input))
            scan_row.addWidget(browse_scan)
            schema_layout.addRow("Scan Path:", scan_row)

            self.scan_include_ext_input = QLineEdit()
            self.scan_include_ext_input.setPlaceholderText(".py,.c,.h  (leave blank for all)")
            schema_layout.addRow("Include Extensions:", self.scan_include_ext_input)

            self.schema_output_path_input = QLineEdit()
            self.schema_output_path_input.setPlaceholderText("otterforge.project.json  (optional)")
            out_schema_row = QHBoxLayout()
            out_schema_row.addWidget(self.schema_output_path_input)
            browse_schema_out = QPushButton("Browse...")
            browse_schema_out.setFixedWidth(72)
            browse_schema_out.clicked.connect(
                lambda: self._browse_file(self.schema_output_path_input, filter="JSON (*.json)")
            )
            out_schema_row.addWidget(browse_schema_out)
            schema_layout.addRow("Export Output:", out_schema_row)

            self.schema_import_path_input = QLineEdit()
            self.schema_import_path_input.setPlaceholderText("path/to/otterforge.project.json")
            import_row = QHBoxLayout()
            import_row.addWidget(self.schema_import_path_input)
            browse_import = QPushButton("Browse...")
            browse_import.setFixedWidth(72)
            browse_import.clicked.connect(
                lambda: self._browse_file(self.schema_import_path_input, filter="JSON (*.json)")
            )
            import_row.addWidget(browse_import)
            schema_layout.addRow("Import Schema:", import_row)

            schema_buttons = QHBoxLayout()
            scan_button = QPushButton("Scan Project")
            scan_button.clicked.connect(self._scan_project)
            schema_buttons.addWidget(scan_button)

            export_button = QPushButton("Export Schema")
            export_button.clicked.connect(self._export_schema)
            schema_buttons.addWidget(export_button)

            import_button = QPushButton("Import Schema")
            import_button.clicked.connect(self._import_schema)
            schema_buttons.addWidget(import_button)
            schema_layout.addRow(schema_buttons)
            layout.addWidget(schema_group)

            self.schema_output = QTextEdit()
            self.schema_output.setReadOnly(True)
            self.schema_output.setPlaceholderText("Scan / schema results will appear here...")
            layout.addWidget(self.schema_output)
            return container

        # ---- Organizer -----------------------------------------------------

        def _build_organizer_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            plan_group = QGroupBox("Create Organization Plan")
            plan_layout = QFormLayout(plan_group)

            self.organize_target_input = QLineEdit(".")
            org_target_row = QHBoxLayout()
            org_target_row.addWidget(self.organize_target_input)
            browse_org = QPushButton("Browse...")
            browse_org.setFixedWidth(72)
            browse_org.clicked.connect(lambda: self._browse_dir(self.organize_target_input))
            org_target_row.addWidget(browse_org)
            plan_layout.addRow("Target Directory:", org_target_row)

            self.organize_mode_selector = QComboBox()
            self.organize_mode_selector.addItems(["copy", "move"])
            self.organize_mode_selector.setToolTip(
                "copy keeps originals and creates sorted copies; move relocates files."
            )
            plan_layout.addRow("Mode:", self.organize_mode_selector)

            self.organize_plan_file_input = QLineEdit()
            self.organize_plan_file_input.setPlaceholderText("organize_plan.json")
            plan_file_row = QHBoxLayout()
            plan_file_row.addWidget(self.organize_plan_file_input)
            browse_plan = QPushButton("Browse...")
            browse_plan.setFixedWidth(72)
            browse_plan.clicked.connect(
                lambda: self._browse_file(self.organize_plan_file_input, filter="JSON (*.json)")
            )
            plan_file_row.addWidget(browse_plan)
            plan_layout.addRow("Save Plan To:", plan_file_row)

            self.organize_force_checkbox = QCheckBox("Force overwrite existing files")
            plan_layout.addRow(self.organize_force_checkbox)

            plan_buttons = QHBoxLayout()
            create_plan_button = QPushButton("Create Plan")
            create_plan_button.clicked.connect(self._create_organization_plan)
            plan_buttons.addWidget(create_plan_button)

            save_plan_button = QPushButton("Save Plan to File")
            save_plan_button.clicked.connect(self._save_organization_plan)
            plan_buttons.addWidget(save_plan_button)
            plan_layout.addRow(plan_buttons)
            layout.addWidget(plan_group)

            apply_group = QGroupBox("Apply / Rollback")
            apply_layout = QFormLayout(apply_group)

            self.organize_apply_plan_input = QLineEdit()
            apply_row = QHBoxLayout()
            apply_row.addWidget(self.organize_apply_plan_input)
            browse_apply = QPushButton("Browse...")
            browse_apply.setFixedWidth(72)
            browse_apply.clicked.connect(
                lambda: self._browse_file(self.organize_apply_plan_input, filter="JSON (*.json)")
            )
            apply_row.addWidget(browse_apply)
            apply_layout.addRow("Apply Plan File:", apply_row)

            self.organize_manifest_path_input = QLineEdit()
            manifest_row = QHBoxLayout()
            manifest_row.addWidget(self.organize_manifest_path_input)
            browse_manifest = QPushButton("Browse...")
            browse_manifest.setFixedWidth(72)
            browse_manifest.clicked.connect(
                lambda: self._browse_file(self.organize_manifest_path_input, filter="JSON (*.json)")
            )
            manifest_row.addWidget(browse_manifest)
            apply_layout.addRow("Rollback Manifest:", manifest_row)

            apply_buttons = QHBoxLayout()
            apply_button = QPushButton("Apply Plan")
            apply_button.clicked.connect(self._apply_organization_plan)
            apply_buttons.addWidget(apply_button)

            rollback_button = QPushButton("Rollback")
            rollback_button.setToolTip("Undo a previous apply operation using its manifest file.")
            rollback_button.clicked.connect(self._rollback_organization)
            apply_buttons.addWidget(rollback_button)
            apply_layout.addRow(apply_buttons)
            layout.addWidget(apply_group)

            self.organizer_output = QTextEdit()
            self.organizer_output.setReadOnly(True)
            self.organizer_output.setPlaceholderText("Organizer results will appear here...")
            layout.addWidget(self.organizer_output)
            return container

        # ---- MCP -----------------------------------------------------------

        def _build_mcp_tab(self) -> QWidget:
            container = QWidget()
            layout = QVBoxLayout(container)

            status_group = QGroupBox("MCP Server Status")
            status_form = QFormLayout(status_group)
            self.mcp_status_value = QLabel("-")
            status_form.addRow("Status:", self.mcp_status_value)

            mcp_controls = QHBoxLayout()
            self.mcp_toggle_button = QPushButton("Start MCP Server")
            self.mcp_toggle_button.clicked.connect(self._toggle_mcp)
            mcp_controls.addWidget(self.mcp_toggle_button)

            refresh_mcp_button = QPushButton("Refresh Status")
            refresh_mcp_button.clicked.connect(self._refresh_mcp)
            mcp_controls.addWidget(refresh_mcp_button)
            status_form.addRow(mcp_controls)
            layout.addWidget(status_group)

            tools_group = QGroupBox("Tool Management")
            tools_form = QFormLayout(tools_group)
            self.mcp_tool_selector = QComboBox()
            self.mcp_tool_selector.setToolTip("Select a registered MCP tool to expose, hide, or inspect.")
            tools_form.addRow("Tool:", self.mcp_tool_selector)

            tool_buttons = QHBoxLayout()
            list_tools_button = QPushButton("Refresh Tools")
            list_tools_button.clicked.connect(self._refresh_mcp_tools)
            tool_buttons.addWidget(list_tools_button)

            expose_tool_button = QPushButton("Expose Selected")
            expose_tool_button.setToolTip("Make the selected tool available to MCP clients.")
            expose_tool_button.clicked.connect(lambda: self._set_mcp_tool_visibility(True))
            tool_buttons.addWidget(expose_tool_button)

            hide_tool_button = QPushButton("Hide Selected")
            hide_tool_button.setToolTip("Remove the selected tool from the MCP client tool list.")
            hide_tool_button.clicked.connect(lambda: self._set_mcp_tool_visibility(False))
            tool_buttons.addWidget(hide_tool_button)
            tools_form.addRow(tool_buttons)
            layout.addWidget(tools_group)

            self.mcp_output = QTextEdit()
            self.mcp_output.setReadOnly(True)
            self.mcp_output.setPlaceholderText("MCP status and tool list will appear here...")
            layout.addWidget(self.mcp_output)
            return container

        # ------------------------------------------------------------------ #
        # History panel                                                        #
        # ------------------------------------------------------------------ #

        def _build_history_panel(self) -> QWidget:
            from PyQt6.QtWidgets import QListWidget

            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(0)

            toggle_row = QHBoxLayout()
            toggle_btn = QPushButton("▼  Operation History")
            toggle_btn.setCheckable(True)
            toggle_btn.setChecked(True)
            toggle_btn.setFlat(True)
            toggle_btn.setStyleSheet("font-weight: bold; text-align: left; padding: 2px 4px;")
            clear_btn = QPushButton("Clear")
            clear_btn.setFixedWidth(60)
            toggle_row.addWidget(toggle_btn)
            toggle_row.addWidget(clear_btn)
            wrapper_layout.addLayout(toggle_row)

            self.history_list = QListWidget()
            self.history_list.setAlternatingRowColors(True)
            self.history_list.setMaximumHeight(120)
            self.history_list.setToolTip("Double-click an entry to view full details")
            wrapper_layout.addWidget(self.history_list)

            toggle_btn.toggled.connect(self.history_list.setVisible)
            toggle_btn.toggled.connect(
                lambda checked: toggle_btn.setText(
                    "▼  Operation History" if checked else "▶  Operation History"
                )
            )
            clear_btn.clicked.connect(self._clear_history)
            self.history_list.itemDoubleClicked.connect(self._show_history_detail)

            return wrapper

        def _append_history(self, op_type: str, success: bool | None, summary: str, detail: Any) -> None:
            from PyQt6.QtGui import QColor
            from PyQt6.QtWidgets import QListWidgetItem
            import datetime

            ts = datetime.datetime.now().strftime("%H:%M:%S")
            status = "OK" if success is True else ("FAIL" if success is False else "INFO")
            entry = {"ts": ts, "op": op_type, "success": success, "summary": summary, "detail": detail}
            self._op_history.insert(0, entry)
            if len(self._op_history) > 200:
                self._op_history = self._op_history[:200]

            item = QListWidgetItem(f"[{ts}]  {op_type:<10}  {status:<5}  {summary}")
            if success is True:
                item.setForeground(QColor("#1a7f37"))
            elif success is False:
                item.setForeground(QColor("#cf222e"))
            self.history_list.insertItem(0, item)

            while self.history_list.count() > 200:
                self.history_list.takeItem(self.history_list.count() - 1)

        def _clear_history(self) -> None:
            self._op_history.clear()
            self.history_list.clear()

        def _show_history_detail(self, item) -> None:
            row = self.history_list.row(item)
            if row < 0 or row >= len(self._op_history):
                return
            entry = self._op_history[row]
            detail_text = json.dumps(entry.get("detail", {}), indent=2, sort_keys=True)
            self._show_text_dialog(f"{entry['op']} detail - {entry['ts']}", detail_text)

        # ------------------------------------------------------------------ #
        # Input validation (UX guardrails)                                    #
        # ------------------------------------------------------------------ #

        def _validate_build_inputs(self, _text: str = "") -> None:
            project = self.project_path_input.text().strip()
            entry = self.entry_script_input.text().strip()
            issues: list[str] = []
            if not project:
                issues.append("Project Path is required")
            if not entry:
                issues.append("Entry Script is required")
            ok = not issues
            self.run_build_button.setEnabled(ok)
            self.build_hint_label.setText("  |  ".join(issues) if issues else "")

        def _validate_quality_inputs(self, _text: str = "") -> None:
            test_project = self.test_project_path_input.text().strip()
            test_command = self.test_command_input.text().strip()
            test_issues: list[str] = []
            if not test_project:
                test_issues.append("Project Path is required")
            if not test_command:
                test_issues.append("Test Command is required")
            tests_ok = not test_issues
            self.run_tests_button.setEnabled(tests_ok)
            self.tests_hint_label.setText("  |  ".join(test_issues) if test_issues else "")

            audit_project = self.audit_project_path_input.text().strip()
            audit_issues: list[str] = []
            if not audit_project:
                audit_issues.append("Project Path is required")
            audit_ok = not audit_issues
            self.run_audit_button.setEnabled(audit_ok)
            self.audit_hint_label.setText("  |  ".join(audit_issues) if audit_issues else "")

        def _validate_security_inputs(self, _text: str = "") -> None:
            artifacts = self.sign_artifacts_input.toPlainText().strip()
            tool = self.signing_tool_selector.currentText()
            issues: list[str] = []
            if not artifacts:
                issues.append("Enter at least one artifact path")
            if tool == "signtool" and not self.signing_cert_input.text().strip():
                issues.append("Certificate path is required for signtool")
            if tool == "codesign" and not self.signing_developer_id_input.text().strip():
                issues.append("Developer ID is required for codesign")
            if tool == "gpg" and not self.signing_key_id_input.text().strip():
                issues.append("GPG Key ID is required")
            ok = not issues
            self.sign_btn.setEnabled(ok)
            self.security_hint_label.setText("  |  ".join(issues) if issues else "")

        def _validate_assets_inputs(self, _text: str = "") -> None:
            source = self.icon_source_input.text().strip()
            ok = bool(source)
            self.prepare_icon_btn.setEnabled(ok)
            self.assets_hint_label.setText("" if ok else "Source Image path is required")

        # ------------------------------------------------------------------ #
        # Helpers                                                              #
        # ------------------------------------------------------------------ #

        def _browse_dir(self, target: QLineEdit) -> None:
            start = target.text().strip() or "."
            chosen = QFileDialog.getExistingDirectory(self, "Select Directory", start)
            if chosen:
                target.setText(chosen)

        def _browse_file(self, target: QLineEdit, filter: str = "All Files (*)") -> None:
            start = str(Path(target.text().strip() or ".").parent)
            chosen, _ = QFileDialog.getOpenFileName(self, "Select File", start, filter)
            if chosen:
                target.setText(chosen)

        def _set_busy_state(self, busy: bool, message: str = "") -> None:
            if busy:
                self._busy_label.setText(message)
                self._busy_progress.setRange(0, 0)
                self._busy_progress.setVisible(True)
                self.statusBar().showMessage(message)
                QApplication.processEvents()
                return

            self._busy_progress.setVisible(False)
            self._busy_progress.setRange(0, 100)
            self._busy_progress.setValue(0)
            self._busy_label.clear()
            QApplication.processEvents()

        def _run_with_busy(self, message: str, operation: Callable[[], Any]) -> Any:
            self._set_busy_state(True, message)
            try:
                return operation()
            finally:
                self._set_busy_state(False)

        def _refresh_all(self) -> None:
            self._refresh_runtime()
            self._refresh_builders()
            self._refresh_toolchain()
            self._refresh_module_search_managers()
            self._refresh_unified_module_catalog()
            self._refresh_profiles_selector()
            self._load_notification_config()
            self._refresh_mcp()
            self._refresh_mcp_tools()

        def _format_payload(self, payload: Any) -> str:
            return json.dumps(payload, indent=2, sort_keys=True)

        def _show_payload(self, widget: QTextEdit, payload: Any) -> None:
            widget.setPlainText(self._format_payload(payload))

        def _show_error(self, title: str, error: Exception) -> None:
            QMessageBox.critical(self, title, str(error))

        def _set_result_label(
            self,
            label: QLabel,
            success: bool | None,
            message: str,
            detail: Any | None = None,
            auto_clear_ms: int = 30000,
        ) -> None:
            detail_text = ""
            if detail is not None:
                detail_text = detail if isinstance(detail, str) else self._format_payload(detail)

            has_detail = success is False and bool(detail_text.strip())
            if has_detail:
                label.setText(f"{message}  <a href='details'>Details</a>")
            else:
                label.setText(message)

            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            label.setOpenExternalLinks(False)
            label.setProperty("_detail_text", detail_text)

            if not bool(label.property("_details_connected")):
                label.linkActivated.connect(lambda _link, lbl=label: self._show_result_details(lbl))
                label.setProperty("_details_connected", True)

            if success is True:
                label.setStyleSheet(
                    "color: #1f5f2e; background-color: #eaf7ee; "
                    "border: 1px solid #2a7f2a; border-radius: 6px; padding: 6px 10px;"
                )
            elif success is False:
                label.setStyleSheet(
                    "color: #8d1f14; background-color: #fdecec; "
                    "border: 1px solid #c0392b; border-radius: 6px; padding: 6px 10px;"
                )
            else:
                label.setStyleSheet(
                    "color: #735b00; background-color: #fff8e6; "
                    "border: 1px solid #b8860b; border-radius: 6px; padding: 6px 10px;"
                )

            current_token = int(label.property("_banner_token") or 0) + 1
            label.setProperty("_banner_token", current_token)
            QTimer.singleShot(
                auto_clear_ms,
                lambda lbl=label, token=current_token: self._auto_clear_result_label(lbl, token),
            )

        def _auto_clear_result_label(self, label: QLabel, token: int) -> None:
            if int(label.property("_banner_token") or 0) != token:
                return
            label.clear()
            label.setStyleSheet("")
            label.setProperty("_detail_text", "")

        def _show_result_details(self, label: QLabel) -> None:
            detail_text = str(label.property("_detail_text") or "").strip()
            if not detail_text:
                return
            self._show_text_dialog("Result Details", detail_text)

        def _show_text_dialog(self, title: str, body: str) -> None:
            from PyQt6.QtWidgets import QDialog

            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.resize(700, 500)

            layout = QVBoxLayout(dialog)
            text = QTextEdit()
            text.setReadOnly(True)
            text.setFont(QFont("Courier New", 9))
            text.setPlainText(body)
            layout.addWidget(text)
            dialog.exec()

        # ------------------------------------------------------------------ #
        # Runtime                                                              #
        # ------------------------------------------------------------------ #

        def _refresh_runtime(self) -> None:
            try:
                backend_status = self.api.get_memory_backend()
                mcp_status = self.api.get_mcp_status()
            except Exception as exc:
                self._show_error("Runtime Refresh Failed", exc)
                return

            self.backend_value.setText(str(backend_status["backend"]))
            self.config_path_value.setText(str(backend_status["runtime_config_path"]))
            self.mcp_value.setText(
                f"{'enabled' if mcp_status['enabled'] else 'disabled'} "
                f"({mcp_status['transport']})"
            )
            self.backend_selector.setCurrentText(str(backend_status["backend"]))
            self._show_payload(
                self.runtime_output,
                {"memory_backend": backend_status, "mcp_status": mcp_status},
            )

        def _apply_backend(self) -> None:
            backend = self.backend_selector.currentText()
            try:
                status = self.api.set_memory_backend(backend)
            except Exception as exc:
                self._show_error("Set Backend Failed", exc)
                return
            self._refresh_runtime()
            self.statusBar().showMessage(f"Backend switched to '{backend}'", 3000)
            self._show_payload(self.runtime_output, status)

        def _migrate_backend(self) -> None:
            backend = self.backend_selector.currentText()
            try:
                migration_result = self.api.migrate_memory_backend(backend)
            except Exception as exc:
                self._show_error("Migrate Backend Failed", exc)
                return
            self._refresh_runtime()
            self._show_payload(self.runtime_output, migration_result)
            self.statusBar().showMessage(f"Data migrated to '{backend}'", 3000)

        def _save_notification_config(self) -> None:
            enabled = self.notif_enabled_checkbox.isChecked()
            webhook = self.notif_webhook_input.text().strip()
            try:
                result = self.api.set_notification_config(enabled=enabled, webhook_url=webhook)
            except Exception as exc:
                self._show_error("Notification Config Save Failed", exc)
                return
            self._show_payload(self.runtime_output, result)
            self.statusBar().showMessage("Notification settings saved", 3000)

        def _load_notification_config(self) -> None:
            try:
                cfg = self.api.get_notification_config()
            except Exception as exc:
                self._show_error("Load Notification Config Failed", exc)
                return
            self.notif_enabled_checkbox.setChecked(bool(cfg.get("enabled", False)))
            self.notif_webhook_input.setText(str(cfg.get("webhook_url", "")))
            status = "enabled" if cfg.get("enabled") else "disabled"
            self.notif_status_value.setText(status)

        # ------------------------------------------------------------------ #
        # Build                                                                #
        # ------------------------------------------------------------------ #

        def _refresh_builders(self) -> None:
            try:
                builders = self.api.list_builders()
            except Exception as exc:
                self._show_error("Builder Refresh Failed", exc)
                return

            current_name = self.builder_selector.currentData() or self.builder_selector.currentText()
            self.builder_selector.clear()
            for builder in builders:
                status = "available" if builder["available"] else "not installed"
                text = f"{builder['name']}  ({status})"
                self.builder_selector.addItem(text, builder["name"])

            if current_name:
                for index in range(self.builder_selector.count()):
                    if self.builder_selector.itemData(index) == current_name:
                        self.builder_selector.setCurrentIndex(index)
                        break

            self._show_payload(self.build_output, builders)

        def _selected_builder_name(self) -> str:
            selected = self.builder_selector.currentData()
            if selected:
                return str(selected)
            return self.builder_selector.currentText().split(" ")[0]

        def _inspect_builder(self) -> None:
            builder_name = self._selected_builder_name()
            if not builder_name:
                QMessageBox.warning(self, "OtterForge", "No builder selected.")
                return
            try:
                details = self.api.inspect_builder(builder_name)
            except Exception as exc:
                self._show_error("Inspect Builder Failed", exc)
                return
            self._show_payload(self.build_output, details)

        def _run_build(self) -> None:
            args_text = self.extra_builder_args_input.text().strip()
            raw_builder_args = shlex.split(args_text) if args_text else []

            icon = self.icon_path_input.text().strip() or None
            output_dir = self.output_dir_input.text().strip() or None
            compiler_config_name = self.compiler_config_name_input.text().strip() or None

            payload: dict[str, Any] = {
                "project_path": self.project_path_input.text().strip() or ".",
                "builder_name": self._selected_builder_name(),
                "entry_script": self.entry_script_input.text().strip() or None,
                "executable_name": self.executable_name_input.text().strip() or None,
                "mode": self.build_mode_selector.currentText(),
                "console_mode": self.console_mode_checkbox.isChecked(),
                "icon_path": icon,
                "output_dir": output_dir,
                "compiler_config_name": compiler_config_name,
                "clean": self.clean_build_checkbox.isChecked(),
                "dry_run": self.dry_run_checkbox.isChecked(),
                "raw_builder_args": raw_builder_args,
                "container": self.container_build_checkbox.isChecked(),
            }

            try:
                result = self._run_with_busy("Running build...", lambda: self.api.run_build(payload))
            except Exception as exc:
                self._show_error("Build Failed", exc)
                return

            success = bool(result.get("success", False))
            artifacts = list(result.get("artifact_paths", []))
            self._last_artifact_paths = artifacts

            label_text = "OK: Build succeeded" if success else "FAIL: Build failed"
            if artifacts:
                label_text += f"  ({len(artifacts)} artifact(s) generated)"
            self._set_result_label(self.build_result_label, success, label_text, detail=result)

            self._show_payload(self.build_output, result)
            mode = "dry-run" if self.dry_run_checkbox.isChecked() else "real"
            self.statusBar().showMessage(
                f"Build {mode} {'succeeded' if success else 'FAILED'}", 4000
            )
            self._append_history("Build", success, label_text, result)

        # Kept for backwards compatibility with existing callers
        def _run_build_dry_run(self) -> None:
            self.dry_run_checkbox.setChecked(True)
            self._run_build()

        def _launch_sandbox_from_build(self) -> None:
            if not self._last_artifact_paths:
                QMessageBox.information(
                    self,
                    "No Artifacts",
                    "Run a real build first to produce artifacts, then launch in sandbox.",
                )
                return
            artifact = self._last_artifact_paths[0]
            try:
                result = self._run_with_busy("Launching sandbox...", lambda: self.api.launch_sandbox(artifact))
            except Exception as exc:
                self._show_error("Sandbox Launch Failed", exc)
                return
            self._show_payload(self.build_output, result)
            if result.get("success"):
                self.statusBar().showMessage(f"Sandbox launched: {artifact}", 4000)

        # ------------------------------------------------------------------ #
        # Tests & Quality                                                      #
        # ------------------------------------------------------------------ #

        def _save_test_config(self) -> None:
            project_path = self.test_project_path_input.text().strip() or "."
            command = self.test_command_input.text().strip() or "pytest"
            gate_enabled = self.test_gate_checkbox.isChecked()
            try:
                result = self.api.set_test_config(project_path, command=command, gate_enabled=gate_enabled)
            except Exception as exc:
                self._show_error("Save Test Config Failed", exc)
                return
            self._show_payload(self.quality_output, result)
            self._set_result_label(self.quality_result_label, None, "Test config saved", detail=result)
            self.statusBar().showMessage("Test config saved", 3000)

        def _load_test_config(self) -> None:
            project_path = self.test_project_path_input.text().strip() or "."
            try:
                cfg = self.api.get_test_config(project_path)
            except Exception as exc:
                self._show_error("Load Test Config Failed", exc)
                return
            if "error" not in cfg:
                self.test_command_input.setText(str(cfg.get("command", "pytest")))
                self.test_gate_checkbox.setChecked(bool(cfg.get("gate_enabled", False)))
            self._show_payload(self.quality_output, cfg)

        def _run_tests(self) -> None:
            project_path = self.test_project_path_input.text().strip() or "."
            command = self.test_command_input.text().strip() or None
            try:
                result = self._run_with_busy(
                    "Running tests...",
                    lambda: self.api.run_tests(project_path, command=command),
                )
            except Exception as exc:
                self._show_error("Run Tests Failed", exc)
                return
            success = bool(result.get("success", False))
            label = "OK: Tests passed" if success else "FAIL: Tests failed"
            self._set_result_label(self.quality_result_label, success, label, detail=result)
            self._show_payload(self.quality_output, result)
            self.statusBar().showMessage(label, 4000)
            self._append_history("Tests", success, label, result)

        def _save_audit_config(self) -> None:
            project_path = self.audit_project_path_input.text().strip() or "."
            gate = self.audit_gate_checkbox.isChecked()
            min_sev = self.audit_severity_selector.currentText()
            try:
                result = self.api.set_audit_config(project_path, gate_enabled=gate, min_severity=min_sev)
            except Exception as exc:
                self._show_error("Save Audit Config Failed", exc)
                return
            self._show_payload(self.quality_output, result)
            self._set_result_label(self.quality_result_label, None, "Audit config saved", detail=result)
            self.statusBar().showMessage("Audit config saved", 3000)

        def _load_audit_config(self) -> None:
            project_path = self.audit_project_path_input.text().strip() or "."
            try:
                cfg = self.api.get_audit_config(project_path)
            except Exception as exc:
                self._show_error("Load Audit Config Failed", exc)
                return
            if "error" not in cfg:
                self.audit_gate_checkbox.setChecked(bool(cfg.get("gate_enabled", False)))
                sev = str(cfg.get("min_severity", "high"))
                self.audit_severity_selector.setCurrentText(sev)
            self._show_payload(self.quality_output, cfg)

        def _run_audit(self) -> None:
            project_path = self.audit_project_path_input.text().strip() or "."
            req_file = self.audit_requirements_input.text().strip() or None
            try:
                result = self._run_with_busy(
                    "Running dependency audit...",
                    lambda: self.api.run_audit(project_path, requirements_file=req_file),
                )
            except Exception as exc:
                self._show_error("Run Audit Failed", exc)
                return
            vuln_count = int(result.get("count", 0))
            blocked = bool(result.get("blocked", False))
            if blocked:
                label = f"FAIL: Audit BLOCKED - {vuln_count} vulnerability(s) found"
                success = False
            elif vuln_count > 0:
                label = f"WARN: Audit passed gate - {vuln_count} vulnerability(s) found (below threshold)"
                success = None
            else:
                label = "OK: Audit clean - no vulnerabilities found"
                success = True
            self._set_result_label(self.quality_result_label, success, label, detail=result)
            self._show_payload(self.quality_output, result)
            self.statusBar().showMessage(label, 4000)
            self._append_history("Audit", success, label, result)

        # ------------------------------------------------------------------ #
        # Security                                                             #
        # ------------------------------------------------------------------ #

        def _save_signing_config(self) -> None:
            project_path = self.sign_project_path_input.text().strip() or "."
            tool = self.signing_tool_selector.currentText()
            try:
                result = self.api.set_signing_config(
                    project_path,
                    tool=tool,
                    cert=self.signing_cert_input.text().strip(),
                    timestamp_url=self.signing_timestamp_input.text().strip(),
                    developer_id=self.signing_developer_id_input.text().strip(),
                    key_id=self.signing_key_id_input.text().strip(),
                )
            except Exception as exc:
                self._show_error("Save Signing Config Failed", exc)
                return
            self._show_payload(self.security_output, result)
            self._set_result_label(self.security_result_label, None, "Signing config saved", detail=result)
            self.statusBar().showMessage("Signing config saved", 3000)

        def _load_signing_config(self) -> None:
            project_path = self.sign_project_path_input.text().strip() or "."
            try:
                cfg = self.api.get_signing_config(project_path)
            except Exception as exc:
                self._show_error("Load Signing Config Failed", exc)
                return
            if "error" not in cfg:
                self.signing_tool_selector.setCurrentText(str(cfg.get("tool", "gpg")))
                self.signing_timestamp_input.setText(str(cfg.get("timestamp_url", "")))
                self.signing_developer_id_input.setText(str(cfg.get("developer_id", "")))
                self.signing_key_id_input.setText(str(cfg.get("key_id", "")))
            self._show_payload(self.security_output, cfg)

        def _sign_artifacts(self) -> None:
            project_path = self.sign_project_path_input.text().strip() or "."
            raw = self.sign_artifacts_input.toPlainText().strip()
            artifact_paths = [line.strip() for line in raw.splitlines() if line.strip()]
            if not artifact_paths:
                QMessageBox.warning(self, "OtterForge", "Enter at least one artifact path to sign.")
                return

            tool = self.signing_tool_selector.currentText() or None
            try:
                result = self._run_with_busy(
                    "Signing artifacts...",
                    lambda: self.api.sign_artifacts(project_path, artifact_paths, tool=tool),
                )
            except Exception as exc:
                self._show_error("Sign Artifacts Failed", exc)
                return

            signed_count = len(result.get("signed", []))
            failed_count = len(result.get("failed", []))
            success = failed_count == 0 and signed_count > 0
            label = f"{'OK:' if success else 'FAIL:'} Signed {signed_count}, failed {failed_count}"
            self._set_result_label(self.security_result_label, success, label, detail=result)
            self._show_payload(self.security_output, result)
            self.statusBar().showMessage(label, 4000)
            self._append_history("Sign", success, label, result)

        # ------------------------------------------------------------------ #
        # Assets                                                               #
        # ------------------------------------------------------------------ #

        def _prepare_icon(self) -> None:
            source_path = self.icon_source_input.text().strip()
            if not source_path:
                QMessageBox.warning(self, "OtterForge", "Specify a source image path.")
                return
            platform = self.icon_platform_selector.currentText()
            try:
                result = self._run_with_busy(
                    "Preparing icon assets...",
                    lambda: self.api.prepare_icon(source_path, target_platform=platform),
                )
            except Exception as exc:
                self._show_error("Prepare Icon Failed", exc)
                return
            success = bool(result.get("success", False))
            label = f"{'OK:' if success else 'FAIL:'} Icon {'ready' if success else 'failed'}"
            if success:
                label += f" -> {result.get('path', '')}"
                # Auto-fill build tab icon field
                self.icon_path_input.setText(str(result.get("path", "")))
            self._set_result_label(self.assets_result_label, success, label, detail=result)
            self._show_payload(self.assets_output, result)
            self.statusBar().showMessage(label, 4000)
            self._append_history("Assets", success, label, result)

        def _list_assets(self) -> None:
            source_path = self.icon_source_input.text().strip()
            if not source_path:
                QMessageBox.warning(self, "OtterForge", "Specify a source image path to list its cached assets.")
                return
            try:
                result = self.api.list_assets(source_path)
            except Exception as exc:
                self._show_error("List Assets Failed", exc)
                return
            count = int(result.get("count", 0))
            self._set_result_label(
                self.assets_result_label, None, f"{count} cached asset(s) found", detail=result
            )
            self._show_payload(self.assets_output, result)

        # ------------------------------------------------------------------ #
        # Toolchain                                                            #
        # ------------------------------------------------------------------ #

        def _refresh_toolchain(self) -> None:
            try:
                toolchain = self.api.list_toolchain()
                doctor = self.api.doctor_toolchain()
            except Exception as exc:
                self._show_error("Toolchain Refresh Failed", exc)
                return
            self._show_payload(
                self.toolchain_output,
                {"toolchain": toolchain, "doctor": doctor},
            )

        def _list_modules_from_toolchain_tab(self) -> None:
            # Backward-compatible alias to the unified module inventory flow.
            self._refresh_unified_module_catalog()

        def _analyze_dependencies_from_toolchain_tab(self) -> None:
            self._refresh_unified_module_catalog()

        def _selected_os_name(self) -> str | None:
            os_name = self.module_os_selector.currentText().strip().lower()
            return None if os_name == "auto" else os_name

        def _sync_module_os_selector(self, _index: int | None = None) -> None:
            os_name = self.pack_os_selector.currentText().strip().lower()
            if self.module_os_selector.currentText().strip().lower() != os_name:
                self.module_os_selector.setCurrentText(os_name)

        def _refresh_module_search_managers(self, _index: int | None = None) -> None:
            if not hasattr(self, "package_browser_manager_selector"):
                return

            try:
                payload = self.api.list_package_managers(os_name=self._selected_os_name())
            except Exception as exc:
                self._show_error("Package Manager Refresh Failed", exc)
                return

            current_manager = self.package_browser_manager_selector.currentData()
            if current_manager is None:
                current_manager = self.package_browser_manager_selector.currentText().strip().lower()

            self.package_browser_manager_selector.clear()
            first_available = ""
            for item in payload.get("managers", []):
                manager_name = str(item.get("manager", "")).strip()
                available = bool(item.get("available", False))
                if not manager_name:
                    continue
                label = manager_name if available else f"{manager_name}  (not found on PATH)"
                self.package_browser_manager_selector.addItem(label, manager_name)
                if available and not first_available:
                    first_available = manager_name

            if current_manager:
                for index in range(self.package_browser_manager_selector.count()):
                    if self.package_browser_manager_selector.itemData(index) == current_manager:
                        self.package_browser_manager_selector.setCurrentIndex(index)
                        break
            elif first_available:
                self.package_browser_manager_selector.setCurrentText(first_available)

        def _upsert_modules(self, modules: list[dict[str, Any]]) -> None:
            for module in modules:
                module_id = str(module.get("module_id", "")).strip()
                if not module_id:
                    kind = str(module.get("module_kind", "module")).strip()
                    name = str(module.get("name", "")).strip().lower()
                    module_id = f"{kind}:{name}"
                    module["module_id"] = module_id
                self.module_catalog[module_id] = module

        def _module_display_label(self, module: dict[str, Any]) -> str:
            kind = str(module.get("module_kind", "module"))
            name = str(module.get("name", ""))
            source = str(module.get("source", ""))
            status = ""
            if module.get("installed") is True:
                version = str(module.get("installed_version") or "")
                status = f"installed{f' ({version})' if version else ''}"
            elif module.get("installed") is False:
                status = "missing"

            prefix = "[LANG]" if kind == "language_pack" else "[PKG]"
            tags = ", ".join(part for part in [source, status] if part)
            return f"{prefix} {name}{f'  ({tags})' if tags else ''}"

        def _render_module_inventory(self, preferred_module_id: str | None = None) -> None:
            from PyQt6.QtWidgets import QListWidgetItem

            current_item = self.module_inventory_list.currentItem()
            current_id = preferred_module_id
            if current_id is None and current_item is not None:
                current_id = str(current_item.data(Qt.ItemDataRole.UserRole) or "")

            self.module_inventory_list.clear()
            for module in sorted(
                self.module_catalog.values(),
                key=lambda item: (
                    str(item.get("module_kind", "")),
                    str(item.get("name", "")).lower(),
                ),
            ):
                row = QListWidgetItem(self._module_display_label(module))
                row.setData(Qt.ItemDataRole.UserRole, str(module.get("module_id", "")))
                self.module_inventory_list.addItem(row)

            if current_id:
                for index in range(self.module_inventory_list.count()):
                    row = self.module_inventory_list.item(index)
                    if str(row.data(Qt.ItemDataRole.UserRole) or "") == current_id:
                        self.module_inventory_list.setCurrentRow(index)
                        break

        def _refresh_unified_module_catalog(self, _index: int | None = None) -> None:
            target_path = self.modules_path_input.text().strip() or "."
            try:
                payload = self._run_with_busy(
                    "Refreshing module inventory...",
                    lambda: self.api.list_unified_modules(target_path, os_name=self._selected_os_name()),
                )
            except Exception as exc:
                self._show_error("Module Inventory Refresh Failed", exc)
                return

            existing_search_modules = {
                module_id: module
                for module_id, module in self.module_catalog.items()
                if str(module.get("source", "")) == "search"
            }
            self.module_catalog = {}
            self._upsert_modules(payload.get("modules", []))
            self._upsert_modules(list(existing_search_modules.values()))
            self._render_module_inventory()
            if self.module_inventory_list.count() > 0 and not self.package_name_input.text().strip():
                self.module_inventory_list.setCurrentRow(0)

            dependency_analysis = payload.get("dependency_analysis", {})
            dependency_count = len(dependency_analysis.get("dependency_inventory", []))
            missing_count = len(dependency_analysis.get("missing_dependencies", []))
            payload["module_inventory_total"] = len(self.module_catalog)
            self._show_payload(self.toolchain_output, payload)
            self.statusBar().showMessage(
                f"Module inventory ready ({dependency_count} dependencies, {missing_count} missing)",
                3000,
            )

        def _load_missing_dependencies_into_package_fields(self) -> None:
            target_path = self.modules_path_input.text().strip() or "."
            try:
                payload = self._run_with_busy(
                    "Finding missing dependencies...",
                    lambda: self.api.list_unified_modules(target_path, os_name=self._selected_os_name()),
                )
            except Exception as exc:
                self._show_error("Load Missing Dependencies Failed", exc)
                return

            dependency_analysis = payload.get("dependency_analysis", {})
            missing = [
                str(name)
                for name in dependency_analysis.get("missing_dependencies", [])
                if str(name).strip()
            ]

            self.dependency_bulk_input.setPlainText("\n".join(missing))
            if missing:
                self.package_name_input.setText(missing[0])

            self._upsert_modules(payload.get("modules", []))
            preferred = f"package:{missing[0].lower()}" if missing else None
            self._render_module_inventory(preferred_module_id=preferred)

            self._show_payload(self.toolchain_output, {"missing_dependencies": missing, "count": len(missing)})
            self.statusBar().showMessage(f"Loaded {len(missing)} missing dependencies", 3000)

        def _refresh_language_packs_selector(self) -> None:
            # Backward-compatible alias retained for old callers.
            self._refresh_unified_module_catalog()

        def _refresh_pack_managers(self, _index: int | None = None) -> None:
            # Legacy no-op: install candidates are now per selected unified module.
            return

        def _refresh_package_browser_managers(self, _index: int | None = None) -> None:
            self._refresh_module_search_managers(_index)

        def _selected_module(self) -> dict[str, Any] | None:
            item = self.module_inventory_list.currentItem()
            if item is None:
                return None
            module_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
            if not module_id:
                return None
            return self.module_catalog.get(module_id)

        def _on_selected_module_changed(self) -> None:
            module = self._selected_module()
            self.module_candidate_selector.clear()
            if module is None:
                return

            package_name = str(module.get("package_name") or module.get("name") or "").strip()
            if package_name:
                self.package_name_input.setText(package_name)

            first_available_index = -1
            for index, candidate in enumerate(module.get("install_candidates", [])):
                manager_name = str(candidate.get("manager", "")).strip()
                if not manager_name:
                    continue
                available = bool(candidate.get("available", False))
                label = manager_name if available else f"{manager_name}  (not found on PATH)"
                self.module_candidate_selector.addItem(label, dict(candidate))
                if available and first_available_index < 0:
                    first_available_index = index

            if first_available_index >= 0:
                self.module_candidate_selector.setCurrentIndex(first_available_index)

        def _sync_selected_package_name(self) -> None:
            self._on_selected_module_changed()

        def _selected_candidate_manager(self) -> str | None:
            candidate = self.module_candidate_selector.currentData()
            if isinstance(candidate, dict):
                manager = str(candidate.get("manager", "")).strip()
                return manager or None

            manager = self.module_candidate_selector.currentText().strip().split(" ", 1)[0]
            return manager or None

        def _search_packages_from_toolchain_tab(self) -> None:
            query = self.package_query_input.text().strip()
            if not query:
                QMessageBox.warning(self, "OtterForge", "Enter a package search query first.")
                return

            manager = self.package_browser_manager_selector.currentData()
            if manager is None:
                manager = self.package_browser_manager_selector.currentText().strip().split(" ", 1)[0]

            selected_os = self._selected_os_name()

            try:
                result = self._run_with_busy(
                    "Searching module candidates...",
                    lambda: self.api.search_unified_modules(
                        query=query,
                        manager=str(manager) if manager else None,
                        os_name=selected_os,
                        limit=25,
                    ),
                )
            except Exception as exc:
                self._show_error("Package Search Failed", exc)
                return

            modules = result.get("modules", [])
            self._upsert_modules(modules)
            preferred_module = None
            if modules:
                preferred_module = str(modules[0].get("module_id", ""))
            self._render_module_inventory(preferred_module_id=preferred_module)

            if self.module_inventory_list.count() > 0 and not self.package_name_input.text().strip():
                self.module_inventory_list.setCurrentRow(0)

            self._show_payload(self.toolchain_output, result)
            found_count = len(modules)
            self.statusBar().showMessage(f"Module search complete ({found_count} result(s))", 3000)

        def _install_package_from_toolchain_tab(self, execute: bool) -> None:
            module = self._selected_module()
            package_name = self.package_name_input.text().strip()
            if module is None and not package_name:
                QMessageBox.warning(self, "OtterForge", "Select a module or enter a package name first.")
                return

            manager = self._selected_candidate_manager()
            if not manager:
                fallback = self.package_browser_manager_selector.currentData()
                if fallback is None:
                    fallback = self.package_browser_manager_selector.currentText().strip().split(" ", 1)[0]
                manager = str(fallback).strip() or None

            selected_os = self._selected_os_name()

            if execute:
                confirmation = QMessageBox.warning(
                    self,
                    "Run Package Install",
                    "This will run install command(s) on your machine. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirmation != QMessageBox.StandardButton.Yes:
                    return

            try:
                if module is not None and str(module.get("module_kind")) == "language_pack":
                    pack_id = str(module.get("pack_id") or module.get("package_name") or "").strip()
                    if not pack_id:
                        QMessageBox.warning(self, "OtterForge", "Selected language pack is missing its pack ID.")
                        return
                    message = "Installing language pack..." if execute else "Preparing language pack install plan..."
                    result = self._run_with_busy(
                        message,
                        lambda: self.api.install_language_pack(
                            pack_id,
                            manager=manager,
                            os_name=selected_os,
                            execute=execute,
                            continue_on_error=self.pack_continue_on_error_checkbox.isChecked(),
                        ),
                    )
                else:
                    target_name = package_name or str(module.get("package_name") or module.get("name") or "").strip()
                    message = "Installing module package..." if execute else "Preparing module install plan..."
                    result = self._run_with_busy(
                        message,
                        lambda: self.api.install_package(
                            package_name=target_name,
                            manager=manager,
                            os_name=selected_os,
                            execute=execute,
                        ),
                    )
            except Exception as exc:
                self._show_error("Package Install Failed", exc)
                return

            self._show_payload(self.toolchain_output, result)
            action = "executed" if execute else "planned"
            self.statusBar().showMessage(f"Module install {action}", 3000)
            self._refresh_unified_module_catalog()

        def _uninstall_package_from_toolchain_tab(self, execute: bool) -> None:
            module = self._selected_module()
            package_name = self.package_name_input.text().strip()
            if module is None and not package_name:
                QMessageBox.warning(self, "OtterForge", "Select a module or enter a package name first.")
                return

            if module is not None and str(module.get("module_kind")) == "language_pack":
                QMessageBox.warning(
                    self,
                    "Uninstall Not Supported",
                    "Language packs currently support install planning/execution only.",
                )
                return

            manager = self._selected_candidate_manager()
            if not manager:
                fallback = self.package_browser_manager_selector.currentData()
                if fallback is None:
                    fallback = self.package_browser_manager_selector.currentText().strip().split(" ", 1)[0]
                manager = str(fallback).strip() or None

            selected_os = self._selected_os_name()

            if execute:
                confirmation = QMessageBox.warning(
                    self,
                    "Run Package Uninstall",
                    "This will run uninstall command(s) on your machine. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirmation != QMessageBox.StandardButton.Yes:
                    return

            try:
                message = "Uninstalling package..." if execute else "Preparing package uninstall plan..."
                target_name = package_name
                if not target_name and module is not None:
                    target_name = str(module.get("package_name") or module.get("name") or "").strip()
                result = self._run_with_busy(
                    message,
                    lambda: self.api.uninstall_package(
                        package_name=target_name,
                        manager=manager,
                        os_name=selected_os,
                        execute=execute,
                    ),
                )
            except Exception as exc:
                self._show_error("Package Uninstall Failed", exc)
                return

            self._show_payload(self.toolchain_output, result)
            action = "executed" if execute else "planned"
            self.statusBar().showMessage(f"Module uninstall {action}", 3000)
            self._refresh_unified_module_catalog()

        def _install_typed_dependencies_from_toolchain_tab(self, execute: bool) -> None:
            raw_text = self.dependency_bulk_input.toPlainText().strip()
            if not raw_text:
                QMessageBox.warning(self, "OtterForge", "Enter one or more package names first.")
                return

            candidates: list[str] = []
            for line in raw_text.replace(",", "\n").splitlines():
                value = line.strip()
                if value:
                    candidates.append(value)

            if not candidates:
                QMessageBox.warning(self, "OtterForge", "No package names were parsed from typed input.")
                return

            manager = self._selected_candidate_manager()
            if not manager:
                manager = self.package_browser_manager_selector.currentData()
                if manager is None:
                    manager = self.package_browser_manager_selector.currentText().strip().split(" ", 1)[0]

            selected_os = self._selected_os_name()

            if execute:
                confirmation = QMessageBox.warning(
                    self,
                    "Run Typed Dependency Install",
                    f"This will run install commands for {len(candidates)} package(s). Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirmation != QMessageBox.StandardButton.Yes:
                    return

            results: list[dict[str, Any]] = []
            action_label = "Installing typed dependencies..." if execute else "Preparing typed dependency plans..."
            self._set_busy_state(True, action_label)
            try:
                for package_name in candidates:
                    try:
                        result = self.api.install_package(
                            package_name=package_name,
                            manager=str(manager) if manager else None,
                            os_name=selected_os,
                            execute=execute,
                        )
                    except Exception as exc:
                        result = {
                            "package": package_name,
                            "executed": execute,
                            "success": False,
                            "error": str(exc),
                        }
                    results.append(result)
                    QApplication.processEvents()
            finally:
                self._set_busy_state(False)

            payload = {
                "executed": execute,
                "count": len(candidates),
                "results": results,
            }
            self._show_payload(self.toolchain_output, payload)
            action = "executed" if execute else "planned"
            self.statusBar().showMessage(f"Typed dependency install {action} ({len(candidates)} package(s))", 3000)
            self._refresh_unified_module_catalog()

        def _install_language_pack_from_toolchain_tab(self, execute: bool) -> None:
            # Backward-compatible alias now routed through the unified module install flow.
            self._install_package_from_toolchain_tab(execute)

        # ------------------------------------------------------------------ #
        # Profiles                                                             #
        # ------------------------------------------------------------------ #

        def _refresh_profiles_selector(self) -> None:
            try:
                profiles = self.api.list_profiles()
            except Exception as exc:
                self._show_error("Profile Refresh Failed", exc)
                return

            current_name = self.profile_selector.currentText()
            self.profile_selector.clear()
            for profile in profiles:
                self.profile_selector.addItem(str(profile["name"]))
            if current_name:
                self.profile_selector.setCurrentText(current_name)

        def _list_profiles(self) -> None:
            try:
                profiles = self.api.list_profiles()
            except Exception as exc:
                self._show_error("List Profiles Failed", exc)
                return
            self._refresh_profiles_selector()
            self._show_payload(self.profile_output, profiles)

        def _create_profile(self) -> None:
            profile_name = self.profile_name_input.text().strip()
            if not profile_name:
                QMessageBox.warning(self, "OtterForge", "Profile name is required.")
                return
            try:
                settings = json.loads(self.profile_settings_input.toPlainText().strip() or "{}")
            except json.JSONDecodeError as exc:
                QMessageBox.warning(self, "Invalid JSON", str(exc))
                return
            try:
                profile = self.api.create_profile(
                    profile_name,
                    settings=settings,
                    description=self.profile_description_input.text().strip(),
                )
            except Exception as exc:
                self._show_error("Create Profile Failed", exc)
                return
            self._refresh_profiles_selector()
            self.profile_selector.setCurrentText(profile_name)
            self._show_payload(self.profile_output, profile)
            self.statusBar().showMessage(f"Profile '{profile_name}' created", 3000)

        def _show_profile(self) -> None:
            profile_name = self.profile_selector.currentText().strip()
            if not profile_name:
                QMessageBox.warning(self, "OtterForge", "Select a profile first.")
                return
            try:
                profile = self.api.show_profile(profile_name)
            except Exception as exc:
                self._show_error("Show Profile Failed", exc)
                return
            self._show_payload(self.profile_output, profile)

        # ------------------------------------------------------------------ #
        # Matrix & CI                                                          #
        # ------------------------------------------------------------------ #

        def _save_container_config(self) -> None:
            project_path = self.container_project_input.text().strip() or "."
            image = self.container_image_input.text().strip()
            if not image:
                QMessageBox.warning(self, "OtterForge", "Enter a Docker image name.")
                return
            try:
                result = self.api.set_container_config(project_path, image=image)
            except Exception as exc:
                self._show_error("Save Container Config Failed", exc)
                return
            self._show_payload(self.matrix_ci_output, result)
            self._set_result_label(self.matrix_ci_result_label, None, "Container config saved", detail=result)
            self.statusBar().showMessage("Container config saved", 3000)

        def _load_container_config(self) -> None:
            project_path = self.container_project_input.text().strip() or "."
            try:
                cfg = self.api.get_container_config(project_path)
            except Exception as exc:
                self._show_error("Load Container Config Failed", exc)
                return
            if "error" not in cfg:
                self.container_image_input.setText(str(cfg.get("image", "")))
            self._show_payload(self.matrix_ci_output, cfg)

        def _define_matrix(self) -> None:
            project_path = self.matrix_project_input.text().strip() or "."
            raw = self.matrix_entries_input.toPlainText().strip()
            try:
                entries = json.loads(raw) if raw else []
            except json.JSONDecodeError as exc:
                QMessageBox.warning(self, "Invalid JSON", str(exc))
                return
            try:
                result = self.api.define_matrix(project_path, entries)
            except Exception as exc:
                self._show_error("Define Matrix Failed", exc)
                return
            self._show_payload(self.matrix_ci_output, result)
            self._set_result_label(
                self.matrix_ci_result_label,
                None,
                f"Matrix saved - {result.get('entries', 0)} entry(s)",
                detail=result,
            )
            self.statusBar().showMessage("Matrix definition saved", 3000)

        def _show_matrix(self) -> None:
            project_path = self.matrix_project_input.text().strip() or "."
            try:
                result = self.api.get_matrix(project_path)
            except Exception as exc:
                self._show_error("Show Matrix Failed", exc)
                return
            self._show_payload(self.matrix_ci_output, result)

        def _run_matrix(self) -> None:
            project_path = self.matrix_project_input.text().strip() or "."
            try:
                result = self._run_with_busy("Running matrix...", lambda: self.api.run_matrix(project_path))
            except Exception as exc:
                self._show_error("Run Matrix Failed", exc)
                return
            all_passed = bool(result.get("all_passed", False))
            passed = len(result.get("passed", []))
            total = int(result.get("total", 0))
            label = (
                f"OK: Matrix complete - {passed}/{total} passed"
                if all_passed
                else f"FAIL: Matrix complete - {passed}/{total} passed, "
                     f"{len(result.get('failed', []))} failed"
            )
            self._set_result_label(self.matrix_ci_result_label, all_passed, label, detail=result)
            self._show_payload(self.matrix_ci_output, result)
            self.statusBar().showMessage(label, 5000)
            self._append_history("Matrix", all_passed, label, result)

        def _generate_ci_workflow(self) -> None:
            project_path = self.ci_project_input.text().strip() or "."
            output_path = self.ci_output_path_input.text().strip() or None
            try:
                result = self._run_with_busy(
                    "Generating CI workflow...",
                    lambda: self.api.generate_ci_workflow(project_path, profiles=[], output_path=output_path),
                )
            except Exception as exc:
                self._show_error("CI Workflow Generation Failed", exc)
                return
            if "error" in result:
                self._set_result_label(
                    self.matrix_ci_result_label, False, f"FAIL: {result['error']}", detail=result
                )
                self._show_payload(self.matrix_ci_output, result)
                return
            label = f"OK: CI workflow written - {result.get('jobs', 0)} job(s)  ->  {result.get('saved_to', '')}"
            self._set_result_label(self.matrix_ci_result_label, True, label, detail=result)
            self._show_payload(self.matrix_ci_output, result)
            self.statusBar().showMessage("CI workflow generated", 4000)
            self._append_history("CI", True, label, result)

        def _export_profile_config(self) -> None:
            profile_name = self.profile_selector.currentText().strip()
            if not profile_name:
                QMessageBox.warning(
                    self, "OtterForge",
                    "Select a profile on the Profiles tab first, then return here to export it."
                )
                return
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Profile As", f"{profile_name}.json", "JSON (*.json)"
            )
            if not output_path:
                return
            try:
                result = self.api.export_profile_config(profile_name, output_path=output_path)
            except Exception as exc:
                self._show_error("Export Profile Failed", exc)
                return
            self._show_payload(self.matrix_ci_output, result)
            self.statusBar().showMessage(f"Profile exported to {output_path}", 4000)

        def _check_sandbox(self) -> None:
            try:
                available = self.api.sandbox_launcher.is_available()
            except Exception as exc:
                self._show_error("Sandbox Check Failed", exc)
                return
            label = (
                "OK: Windows Sandbox is available on this machine."
                if available
                else "FAIL: Windows Sandbox is NOT available. Enable it via Windows Features."
            )
            self._set_result_label(self.matrix_ci_result_label, available, label, detail={"available": available})
            self._show_payload(self.matrix_ci_output, {"available": available})

        def _launch_sandbox(self) -> None:
            artifact = self.sandbox_artifact_input.text().strip()
            if not artifact:
                QMessageBox.warning(self, "OtterForge", "Specify an artifact path to launch in sandbox.")
                return
            startup = self.sandbox_startup_input.text().strip() or None
            try:
                result = self._run_with_busy(
                    "Launching sandbox...",
                    lambda: self.api.launch_sandbox(artifact, startup_command=startup),
                )
            except Exception as exc:
                self._show_error("Sandbox Launch Failed", exc)
                return
            success = bool(result.get("success", False))
            label = "OK: Sandbox launched" if success else f"FAIL: Sandbox failed: {result.get('error', '')}"
            self._set_result_label(self.matrix_ci_result_label, success, label, detail=result)
            self._show_payload(self.matrix_ci_output, result)
            self.statusBar().showMessage(label, 4000)

        # ------------------------------------------------------------------ #
        # Schema                                                               #
        # ------------------------------------------------------------------ #

        def _scan_project(self) -> None:
            scan_path = self.scan_path_input.text().strip() or "."
            include_text = self.scan_include_ext_input.text().strip()
            include_extensions = (
                [item.strip() for item in include_text.split(",") if item.strip()]
                if include_text
                else None
            )
            try:
                result = self._run_with_busy(
                    "Scanning project...",
                    lambda: self.api.scan_project(scan_path, include_extensions=include_extensions),
                )
            except Exception as exc:
                self._show_error("Scan Failed", exc)
                return
            self.last_scan_result = result
            self._show_payload(self.schema_output, result)
            self.statusBar().showMessage("Project scan complete", 3000)

        def _export_schema(self) -> None:
            scan_path = self.scan_path_input.text().strip() or "."
            output_path = self.schema_output_path_input.text().strip()
            try:
                def _do_export() -> Any:
                    if not self.last_scan_result or Path(scan_path).resolve() != Path(
                        str(self.last_scan_result.get("path", ""))
                    ).resolve():
                        self.last_scan_result = self.api.scan_project(scan_path)
                    return self.api.export_project_schema(
                        self.last_scan_result,
                        destination=output_path or None,
                    )

                schema = self._run_with_busy("Exporting schema...", _do_export)
            except Exception as exc:
                self._show_error("Export Schema Failed", exc)
                return
            self._show_payload(self.schema_output, schema)
            self.statusBar().showMessage("Schema exported", 3000)

        def _import_schema(self) -> None:
            schema_path = self.schema_import_path_input.text().strip()
            if not schema_path:
                QMessageBox.warning(self, "OtterForge", "Schema path is required.")
                return
            try:
                schema = self._run_with_busy(
                    "Importing schema...",
                    lambda: self.api.import_project_schema(schema_path),
                )
            except Exception as exc:
                self._show_error("Import Schema Failed", exc)
                return
            self._show_payload(self.schema_output, schema)
            self.statusBar().showMessage("Schema imported", 3000)

        # ------------------------------------------------------------------ #
        # Organizer                                                            #
        # ------------------------------------------------------------------ #

        def _create_organization_plan(self) -> None:
            target = self.organize_target_input.text().strip() or "."
            mode = self.organize_mode_selector.currentText()
            try:
                plan = self._run_with_busy(
                    "Creating organization plan...",
                    lambda: self.api.create_organization_plan(target, mode=mode),
                )
            except Exception as exc:
                self._show_error("Create Plan Failed", exc)
                return
            self.last_organization_plan = plan
            self._show_payload(self.organizer_output, plan)
            self.statusBar().showMessage("Organization plan created", 3000)

        def _save_organization_plan(self) -> None:
            if not self.last_organization_plan:
                QMessageBox.warning(self, "OtterForge", "Create a plan before saving.")
                return
            plan_path = self.organize_plan_file_input.text().strip()
            if not plan_path:
                QMessageBox.warning(self, "OtterForge", "Plan file path is required.")
                return
            try:
                saved_path = self.api.save_organization_plan(self.last_organization_plan, plan_path)
            except Exception as exc:
                self._show_error("Save Plan Failed", exc)
                return
            resolved_path = str(Path(saved_path).resolve())
            self.organize_apply_plan_input.setText(resolved_path)
            self._show_payload(
                self.organizer_output,
                {"saved_plan": resolved_path, "plan_id": self.last_organization_plan.get("plan_id")},
            )
            self.statusBar().showMessage("Plan saved", 3000)

        def _apply_organization_plan(self) -> None:
            plan_path = self.organize_apply_plan_input.text().strip()
            force = self.organize_force_checkbox.isChecked()
            plan_source: dict[str, Any] | str = (
                plan_path if plan_path else (self.last_organization_plan or "")
            )
            if not plan_source:
                QMessageBox.warning(self, "OtterForge", "Provide a plan file or create a plan first.")
                return
            try:
                result = self._run_with_busy(
                    "Applying organization plan...",
                    lambda: self.api.apply_organization_plan(plan_source, force=force),
                )
            except Exception as exc:
                self._show_error("Apply Plan Failed", exc)
                return
            manifest_path = str(result.get("manifest_path", ""))
            if manifest_path:
                self.organize_manifest_path_input.setText(manifest_path)
            self._show_payload(self.organizer_output, result)
            self.statusBar().showMessage("Plan applied", 3000)

        def _rollback_organization(self) -> None:
            manifest_path = self.organize_manifest_path_input.text().strip()
            if not manifest_path:
                QMessageBox.warning(self, "OtterForge", "Manifest path is required.")
                return
            force = self.organize_force_checkbox.isChecked()
            try:
                result = self._run_with_busy(
                    "Rolling back organization changes...",
                    lambda: self.api.rollback_organization(manifest_path, force=force),
                )
            except Exception as exc:
                self._show_error("Rollback Failed", exc)
                return
            self._show_payload(self.organizer_output, result)
            self.statusBar().showMessage("Rollback complete", 3000)

        # ------------------------------------------------------------------ #
        # MCP                                                                  #
        # ------------------------------------------------------------------ #

        def _refresh_mcp(self) -> None:
            try:
                status = self.api.get_mcp_status()
            except Exception as exc:
                self._show_error("MCP Refresh Failed", exc)
                return
            status_text = (
                f"{' Enabled' if status['enabled'] else '[STOPPED] Disabled'} | "
                f"transport = {status['transport']} | "
                f"read-only = {status['read_only']}"
            )
            self.mcp_status_value.setText(status_text)
            self.mcp_toggle_button.setText(
                "Stop MCP Server" if status["enabled"] else "Start MCP Server"
            )
            self._show_payload(self.mcp_output, status)

        def _refresh_mcp_tools(self) -> None:
            try:
                tools = self.api.list_mcp_tools()
            except Exception as exc:
                self._show_error("MCP Tools Failed", exc)
                return
            current_tool = (
                self.mcp_tool_selector.currentData()
                or self.mcp_tool_selector.currentText().split(" ")[0]
            )
            self.mcp_tool_selector.clear()
            for tool in tools:
                kind = "mutating" if tool["mutating"] else "read-only"
                visibility = "visible" if tool.get("visible", True) else "hidden"
                text = f"{tool['tool_id']}  ({kind}, {visibility})"
                self.mcp_tool_selector.addItem(text, tool["tool_id"])
            if current_tool:
                for index in range(self.mcp_tool_selector.count()):
                    if self.mcp_tool_selector.itemData(index) == current_tool:
                        self.mcp_tool_selector.setCurrentIndex(index)
                        break
            self._show_payload(self.mcp_output, tools)

        def _toggle_mcp(self) -> None:
            try:
                status = self.api.get_mcp_status()
                result = self._run_with_busy(
                    "Updating MCP server state...",
                    lambda: self.api.stop_mcp_server() if status["enabled"] else self.api.start_mcp_server(),
                )
            except Exception as exc:
                self._show_error("MCP Toggle Failed", exc)
                return
            self._refresh_runtime()
            self._refresh_mcp()
            self._refresh_mcp_tools()
            self._show_payload(self.mcp_output, result)
            self.statusBar().showMessage("MCP server state updated", 3000)

        def _set_mcp_tool_visibility(self, enabled: bool) -> None:
            tool_id = (
                self.mcp_tool_selector.currentData()
                or self.mcp_tool_selector.currentText().split(" ")[0]
            )
            if not tool_id:
                QMessageBox.warning(self, "OtterForge", "Select a tool first.")
                return
            try:
                result = self.api.set_mcp_tool_visibility(str(tool_id), enabled)
            except Exception as exc:
                self._show_error("MCP Tool Visibility Failed", exc)
                return
            self._refresh_runtime()
            self._refresh_mcp_tools()
            self._show_payload(self.mcp_output, result)
            action = "exposed" if enabled else "hidden"
            self.statusBar().showMessage(f"Tool '{tool_id}' {action}", 3000)


def launch_ui() -> int:
    if not PYQT_AVAILABLE:
        raise RuntimeError(
            "PyQt6 is not installed. Install it with:  pip install PyQt6"
        )

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


