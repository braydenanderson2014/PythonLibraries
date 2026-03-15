#!/usr/bin/env python3
"""
Tutorial Settings Widget
Handles tutorial system settings like enable/disable, auto-start, management, and status.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QCheckBox, QComboBox,
    QLabel, QPushButton
)

from Settings.base_settings_widget import BaseSettingsWidget

class TutorialSettingsWidget(BaseSettingsWidget):
    """Tutorial settings tab widget"""
    
    def setup_ui(self):
        """Create the tutorial settings UI"""
        layout = QVBoxLayout(self)
        
        # Main tutorial system group
        main_group, main_layout = self.create_group_box("Tutorial System", QFormLayout)
        
        # Enable/disable tutorials
        self.enable_tutorials_cb = QCheckBox("Enable interactive tutorials")
        self.enable_tutorials_cb.setToolTip("Enable or disable the entire tutorial system")
        self.enable_tutorials_cb.toggled.connect(self.on_tutorial_enable_changed)
        self.enable_tutorials_cb.toggled.connect(self.on_settings_changed)
        main_layout.addRow("", self.enable_tutorials_cb)
        
        # Auto-start for new users
        self.auto_start_cb = QCheckBox("Auto-start tutorials for new users")
        self.auto_start_cb.setToolTip("Automatically show tutorials when the application starts for the first time")
        self.auto_start_cb.toggled.connect(self.on_settings_changed)
        main_layout.addRow("", self.auto_start_cb)
        
        # Show first-run tutorials
        self.first_run_cb = QCheckBox("Show first-run tutorials")
        self.first_run_cb.setToolTip("Show tutorials that explain basic application features")
        self.first_run_cb.toggled.connect(self.on_settings_changed)
        main_layout.addRow("", self.first_run_cb)
        
        # Show on tab switch
        self.show_on_tab_switch_cb = QCheckBox("Show tutorials when switching to new tabs")
        self.show_on_tab_switch_cb.setToolTip("Automatically show tutorials for widgets when you first switch to their tab")
        self.show_on_tab_switch_cb.toggled.connect(self.on_settings_changed)
        main_layout.addRow("", self.show_on_tab_switch_cb)
        
        # Animation speed
        self.animation_speed_combo = QComboBox()
        self.animation_speed_combo.addItems(["slow", "normal", "fast"])
        self.animation_speed_combo.setToolTip("Speed of tutorial animations and transitions")
        self.animation_speed_combo.currentTextChanged.connect(self.on_settings_changed)
        main_layout.addRow("Animation speed:", self.animation_speed_combo)
        
        layout.addWidget(main_group)
        
        # Tutorial management group
        manage_group, manage_layout = self.create_group_box("Tutorial Management", QFormLayout)
        
        # Tutorial selection for reset
        tutorial_layout = QHBoxLayout()
        self.tutorial_combo = QComboBox()
        self.tutorial_combo.addItems([
            "main_application",
            "split_widget", 
            "merge_widget",
            "image_converter",
            "search_widget",
            "white_space",
            "text_to_speech",
            "auto_import",
            "settings"
        ])
        tutorial_layout.addWidget(self.tutorial_combo)
        
        self.reset_specific_btn = self.create_styled_button("Reset Selected", "Reset the selected tutorial")
        self.reset_specific_btn.clicked.connect(self.reset_specific_tutorial)
        tutorial_layout.addWidget(self.reset_specific_btn)
        
        manage_layout.addRow("Reset specific tutorial:", tutorial_layout)
        
        # Reset all button
        self.reset_all_btn = QPushButton("Reset All Tutorials")
        self.reset_all_btn.clicked.connect(self.reset_all_tutorials)
        self.reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        manage_layout.addRow("", self.reset_all_btn)
        
        layout.addWidget(manage_group)
        
        # Tutorial status group
        status_group, status_layout = self.create_group_box("Tutorial Status", QFormLayout)
        
        self.tutorial_status_label = QLabel()
        self.tutorial_status_label.setWordWrap(True)
        status_layout.addRow("", self.tutorial_status_label)
        
        # Refresh status button
        self.refresh_tutorial_status_btn = self.create_styled_button("Refresh Status", "Refresh tutorial status information")
        self.refresh_tutorial_status_btn.clicked.connect(self.update_tutorial_status)
        status_layout.addRow("", self.refresh_tutorial_status_btn)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load tutorial settings from the controller"""
        # Enable tutorials
        enabled = self.get_setting("tutorials", "enabled", True)
        self.enable_tutorials_cb.setChecked(enabled)
        
        # Auto-start
        auto_start = self.get_setting("tutorials", "auto_start", True)
        self.auto_start_cb.setChecked(auto_start)
        
        # First-run tutorials
        first_run = self.get_setting("tutorials", "show_first_run", True)
        self.first_run_cb.setChecked(first_run)
        
        # Show on tab switch
        show_on_switch = self.get_setting("tutorials", "show_on_tab_switch", True)
        self.show_on_tab_switch_cb.setChecked(show_on_switch)
        
        # Animation speed
        speed = self.get_setting("tutorials", "animation_speed", "normal")
        speed_index = self.animation_speed_combo.findText(speed)
        if speed_index >= 0:
            self.animation_speed_combo.setCurrentIndex(speed_index)
            
        # Update dependent controls
        self.on_tutorial_enable_changed()
        
        # Update tutorial status
        self.update_tutorial_status()
        
    def save_settings(self):
        """Save tutorial settings to the controller"""
        self.set_setting("tutorials", "enabled", self.enable_tutorials_cb.isChecked())
        self.set_setting("tutorials", "auto_start", self.auto_start_cb.isChecked())
        self.set_setting("tutorials", "show_first_run", self.first_run_cb.isChecked())
        self.set_setting("tutorials", "show_on_tab_switch", self.show_on_tab_switch_cb.isChecked())
        self.set_setting("tutorials", "animation_speed", self.animation_speed_combo.currentText())
        
    def on_tutorial_enable_changed(self):
        """Handle tutorial enable/disable change"""
        enabled = self.enable_tutorials_cb.isChecked()
        
        # Enable/disable dependent controls
        self.auto_start_cb.setEnabled(enabled)
        self.first_run_cb.setEnabled(enabled)
        self.show_on_tab_switch_cb.setEnabled(enabled)
        self.animation_speed_combo.setEnabled(enabled)
        self.tutorial_combo.setEnabled(enabled)
        self.reset_specific_btn.setEnabled(enabled)
        self.reset_all_btn.setEnabled(enabled)
        self.refresh_tutorial_status_btn.setEnabled(enabled)
        
    def reset_specific_tutorial(self):
        """Reset the selected tutorial"""
        try:
            selected_tutorial = self.tutorial_combo.currentText()
            
            # Confirm action
            if self.show_question_message(
                "Reset Tutorial", 
                f"Are you sure you want to reset the '{selected_tutorial}' tutorial?\n\n"
                "This will show the tutorial again the next time you use that feature."
            ):
                # Reset the specific tutorial
                success = self.settings_controller.reset_tutorial(selected_tutorial)
                
                if success:
                    self.show_info_message("Reset Tutorial", f"Tutorial '{selected_tutorial}' has been reset.")
                    self.update_tutorial_status()
                else:
                    self.show_warning_message("Reset Tutorial", f"Failed to reset tutorial '{selected_tutorial}'.")
                    
        except Exception as e:
            self.logger.error("TutorialSettings", f"Error resetting specific tutorial: {str(e)}")
            self.show_warning_message("Reset Tutorial Error", f"Failed to reset tutorial: {str(e)}")
            
    def reset_all_tutorials(self):
        """Reset all tutorials"""
        try:
            # Confirm action with stronger warning
            if self.show_question_message(
                "Reset All Tutorials", 
                "Are you sure you want to reset ALL tutorials?\n\n"
                "This will show all tutorials again and cannot be undone.\n\n"
                "This action will reset the tutorial state for all features."
            ):
                # Reset all tutorials
                success = self.settings_controller.reset_all_tutorials()
                
                if success:
                    self.show_info_message("Reset All Tutorials", "All tutorials have been reset.")
                    self.update_tutorial_status()
                else:
                    self.show_warning_message("Reset All Tutorials", "Failed to reset all tutorials.")
                    
        except Exception as e:
            self.logger.error("TutorialSettings", f"Error resetting all tutorials: {str(e)}")
            self.show_warning_message("Reset All Tutorials Error", f"Failed to reset all tutorials: {str(e)}")
            
    def update_tutorial_status(self):
        """Update the tutorial status display"""
        try:
            if not self.enable_tutorials_cb.isChecked():
                self.tutorial_status_label.setText("Tutorials are disabled.")
                self.tutorial_status_label.setStyleSheet("color: red;")
                return
                
            # Get tutorial status from settings controller
            tutorial_status = self.settings_controller.get_tutorial_status()
            
            if tutorial_status:
                completed_count = tutorial_status.get("completed", 0)
                total_count = tutorial_status.get("total", 0)
                tutorial_details = tutorial_status.get("tutorial_status", {})
                
                status_text = f"Tutorials completed: {completed_count}/{total_count}\n\n"
                
                for tutorial_name, is_completed in tutorial_details.items():
                    if is_completed:
                        status_text += f"✓ {tutorial_name.replace('_', ' ').title()}\n"
                    else:
                        status_text += f"○ {tutorial_name.replace('_', ' ').title()}\n"
                        
                self.tutorial_status_label.setText(status_text)
                
                if completed_count == total_count:
                    self.tutorial_status_label.setStyleSheet("color: green;")
                elif completed_count > 0:
                    self.tutorial_status_label.setStyleSheet("color: orange;")
                else:
                    self.tutorial_status_label.setStyleSheet("color: blue;")
            else:
                self.tutorial_status_label.setText("No tutorial status available.")
                self.tutorial_status_label.setStyleSheet("color: gray;")
                
        except Exception as e:
            self.logger.error("TutorialSettings", f"Error updating tutorial status: {str(e)}")
            self.tutorial_status_label.setText("Error loading tutorial status.")
            self.tutorial_status_label.setStyleSheet("color: red;")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
