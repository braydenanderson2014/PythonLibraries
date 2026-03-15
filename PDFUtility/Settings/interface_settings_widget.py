#!/usr/bin/env python3
"""
Interface Settings Widget
Handles interface-related settings like toolbar, status bar, previews, etc.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QGroupBox, QFormLayout, QCheckBox, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt

from Settings.base_settings_widget import BaseSettingsWidget

class InterfaceSettingsWidget(BaseSettingsWidget):
    """Interface settings tab widget"""
    
    def setup_ui(self):
        """Create the interface settings UI"""
        layout = QVBoxLayout(self)
        
        # Interface settings group
        interface_group, interface_layout = self.create_group_box("Interface Settings", QFormLayout)
        
        # Show toolbar
        self.show_toolbar_cb = QCheckBox("Show toolbar")
        self.show_toolbar_cb.stateChanged.connect(self.on_settings_changed)
        interface_layout.addRow("", self.show_toolbar_cb)
        
        # Show status bar
        self.show_statusbar_cb = QCheckBox("Show status bar")
        self.show_statusbar_cb.stateChanged.connect(self.on_settings_changed)
        interface_layout.addRow("", self.show_statusbar_cb)
        
        # Confirm file delete
        self.confirm_delete_cb = QCheckBox("Confirm file delete")
        self.confirm_delete_cb.stateChanged.connect(self.on_settings_changed)
        interface_layout.addRow("", self.confirm_delete_cb)
        
        # Preview quality
        self.preview_quality_combo = QComboBox()
        self.preview_quality_combo.addItems(["Low", "Medium", "High"])
        self.preview_quality_combo.currentTextChanged.connect(self.on_settings_changed)
        interface_layout.addRow("Preview quality:", self.preview_quality_combo)
        
        # Preview size
        self.preview_size_spin = QSpinBox()
        self.preview_size_spin.setMinimum(100)
        self.preview_size_spin.setMaximum(500)
        self.preview_size_spin.setSingleStep(10)
        self.preview_size_spin.setValue(200)
        self.preview_size_spin.setSuffix(" px")
        self.preview_size_spin.valueChanged.connect(self.on_settings_changed)
        interface_layout.addRow("Preview size:", self.preview_size_spin)
        
        # Add to layout
        layout.addWidget(interface_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load interface settings from the controller"""
        # Show toolbar
        show_toolbar = self.get_setting("ui", "show_toolbar", True)
        self.show_toolbar_cb.setChecked(show_toolbar)
        
        # Show status bar
        show_statusbar = self.get_setting("ui", "show_statusbar", True)
        self.show_statusbar_cb.setChecked(show_statusbar)
        
        # Confirm delete
        confirm_delete = self.get_setting("ui", "confirm_file_delete", True)
        self.confirm_delete_cb.setChecked(confirm_delete)
        
        # Preview quality
        preview_quality = self.get_setting("ui", "preview_quality", "Medium")
        index = self.preview_quality_combo.findText(preview_quality)
        if index >= 0:
            self.preview_quality_combo.setCurrentIndex(index)
            
        # Preview size
        preview_size = self.get_setting("ui", "preview_size", 200)
        self.preview_size_spin.setValue(preview_size)
        
    def save_settings(self):
        """Save interface settings to the controller"""
        # Show toolbar
        self.set_setting("ui", "show_toolbar", self.show_toolbar_cb.isChecked())
        
        # Show status bar
        self.set_setting("ui", "show_statusbar", self.show_statusbar_cb.isChecked())
        
        # Confirm delete
        self.set_setting("ui", "confirm_file_delete", self.confirm_delete_cb.isChecked())
        
        # Preview quality
        self.set_setting("ui", "preview_quality", self.preview_quality_combo.currentText())
        
        # Preview size
        self.set_setting("ui", "preview_size", self.preview_size_spin.value())
        
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
