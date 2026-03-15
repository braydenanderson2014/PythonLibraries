#!/usr/bin/env python3
"""
Editor Settings Widget
Handles PDF Editor settings like startup behavior, appearance, and launching.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QCheckBox, QComboBox,
    QSpinBox, QLabel, QPushButton
)

from Settings.base_settings_widget import BaseSettingsWidget

class EditorSettingsWidget(BaseSettingsWidget):
    """PDF Editor settings tab widget"""
    
    def setup_ui(self):
        """Create the editor settings UI"""
        layout = QVBoxLayout(self)
        
        # Add disabled message at the top
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        
        disabled_label = QLabel("Editor functionality is currently disabled. These settings will be available once the editor is ready and any licenses are granted.")
        disabled_label.setWordWrap(True)
        disabled_label.setStyleSheet("color: gray; font-style: italic; padding: 10px; background: rgba(128, 128, 128, 0.1); border-radius: 5px;")
        layout.addWidget(disabled_label)
        
        # Editor settings group
        editor_group, editor_layout = self.create_group_box("Editor Settings", QFormLayout)
        editor_group.setEnabled(False)  # Disable the entire group
        
        # Editor startup options
        startup_group, startup_layout = self.create_group_box("Startup Behavior", QVBoxLayout)
        
        self.editor_auto_open_cb = QCheckBox("Automatically open selected files in editor")
        self.editor_auto_open_cb.setToolTip("When launching the editor, automatically open any files that are currently selected")
        self.editor_auto_open_cb.toggled.connect(self.on_settings_changed)
        startup_layout.addWidget(self.editor_auto_open_cb)
        
        self.editor_remember_session_cb = QCheckBox("Remember last editing session")
        self.editor_remember_session_cb.setToolTip("Remember which files were open when the editor was last closed")
        self.editor_remember_session_cb.toggled.connect(self.on_settings_changed)
        startup_layout.addWidget(self.editor_remember_session_cb)
        
        self.editor_confirm_close_cb = QCheckBox("Confirm when closing with unsaved changes")
        self.editor_confirm_close_cb.setToolTip("Ask for confirmation before closing the editor with unsaved changes")
        self.editor_confirm_close_cb.toggled.connect(self.on_settings_changed)
        startup_layout.addWidget(self.editor_confirm_close_cb)
        
        editor_layout.addRow(startup_group)
        
        # Editor appearance group
        appearance_group, appearance_layout = self.create_group_box("Appearance", QFormLayout)
        
        self.editor_font_combo = QComboBox()
        self.editor_font_combo.addItems(["System Default", "Courier New", "Consolas", "Arial", "Times New Roman"])
        self.editor_font_combo.currentTextChanged.connect(self.on_settings_changed)
        appearance_layout.addRow("Font:", self.editor_font_combo)
        
        self.editor_font_size_spin = QSpinBox()
        self.editor_font_size_spin.setRange(8, 24)
        self.editor_font_size_spin.setValue(12)
        self.editor_font_size_spin.valueChanged.connect(self.on_settings_changed)
        appearance_layout.addRow("Font Size:", self.editor_font_size_spin)
        
        self.editor_syntax_highlighting_cb = QCheckBox("Enable syntax highlighting")
        self.editor_syntax_highlighting_cb.toggled.connect(self.on_settings_changed)
        appearance_layout.addRow("", self.editor_syntax_highlighting_cb)
        
        editor_layout.addRow(appearance_group)
        
        # Launch button group
        launch_group, launch_layout = self.create_group_box("Launch Editor", QVBoxLayout)
        
        self.launch_editor_btn = self.create_styled_button("Open PDF Editor", "Opens the PDF editor in a new window")
        self.launch_editor_btn.clicked.connect(self.launch_editor)
        
        # Add help text
        launch_help = QLabel(
            "Opens the PDF editor in a new window. If files are selected in the main application, "
            "they will be automatically opened in the editor if the option above is enabled."
        )
        launch_help.setWordWrap(True)
        launch_help.setStyleSheet("color: gray; font-style: italic;")
        
        launch_layout.addWidget(self.launch_editor_btn)
        launch_layout.addWidget(launch_help)
        
        # Add groups to main layout
        layout.addWidget(editor_group)
        layout.addWidget(launch_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load editor settings from the controller"""
        # Startup behavior
        self.editor_auto_open_cb.setChecked(
            self.get_setting("editor", "auto_open_selected", False)
        )
        self.editor_remember_session_cb.setChecked(
            self.get_setting("editor", "remember_session", True)
        )
        self.editor_confirm_close_cb.setChecked(
            self.get_setting("editor", "confirm_close_unsaved", True)
        )
        
        # Appearance
        font = self.get_setting("editor", "font", "System Default")
        font_index = self.editor_font_combo.findText(font)
        if font_index >= 0:
            self.editor_font_combo.setCurrentIndex(font_index)
            
        font_size = int(self.get_setting("editor", "font_size", 12))
        self.editor_font_size_spin.setValue(font_size)
        
        self.editor_syntax_highlighting_cb.setChecked(
            self.get_setting("editor", "syntax_highlighting", True)
        )
        
    def save_settings(self):
        """Save editor settings to the controller"""
        # Startup behavior
        self.set_setting("editor", "auto_open_selected", self.editor_auto_open_cb.isChecked())
        self.set_setting("editor", "remember_session", self.editor_remember_session_cb.isChecked())
        self.set_setting("editor", "confirm_close_unsaved", self.editor_confirm_close_cb.isChecked())
        
        # Appearance
        self.set_setting("editor", "font", self.editor_font_combo.currentText())
        self.set_setting("editor", "font_size", self.editor_font_size_spin.value())
        self.set_setting("editor", "syntax_highlighting", self.editor_syntax_highlighting_cb.isChecked())
        
    def launch_editor(self):
        """Launch the PDF editor"""
        try:
            # This would typically call the main application's editor launch method
            from main_application import MainApplication
            if hasattr(MainApplication, 'instance'):
                app_instance = MainApplication.instance
                if hasattr(app_instance, 'launch_pdf_editor'):
                    app_instance.launch_pdf_editor()
                else:
                    self.show_info_message("Editor Launch", "PDF Editor functionality not yet implemented.")
            else:
                self.show_info_message("Editor Launch", "PDF Editor functionality not yet implemented.")
                
        except Exception as e:
            self.logger.error("EditorSettings", f"Error launching PDF editor: {str(e)}")
            self.show_warning_message("Editor Launch Error", f"Failed to launch PDF editor: {str(e)}")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
