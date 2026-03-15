"""
Tutorial Settings Section for Settings Dialog
Add this to your existing settings dialog to give users control over tutorials.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, 
    QPushButton, QLabel, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt

class TutorialSettingsWidget(QWidget):
    """Settings widget for tutorial configuration"""
    
    def __init__(self, settings_controller, tutorial_manager=None, parent=None):
        super().__init__(parent)
        self.settings = settings_controller
        self.tutorial_manager = tutorial_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the tutorial settings UI"""
        layout = QVBoxLayout(self)
        
        # Main tutorial group
        main_group = QGroupBox("Tutorial System")
        main_layout = QVBoxLayout(main_group)
        
        # Enable/disable tutorials
        self.enable_tutorials_cb = QCheckBox("Enable interactive tutorials")
        self.enable_tutorials_cb.setToolTip("Enable or disable the entire tutorial system")
        main_layout.addWidget(self.enable_tutorials_cb)
        
        # Auto-start for new users
        self.auto_start_cb = QCheckBox("Auto-start tutorials for new users")
        self.auto_start_cb.setToolTip("Automatically show tutorials when the application starts for the first time")
        main_layout.addWidget(self.auto_start_cb)
        
        # Show first-run tutorials
        self.first_run_cb = QCheckBox("Show first-run tutorials")
        self.first_run_cb.setToolTip("Show tutorials that explain basic application features")
        main_layout.addWidget(self.first_run_cb)
        
        layout.addWidget(main_group)
        
        # Tutorial management group
        manage_group = QGroupBox("Tutorial Management")
        manage_layout = QVBoxLayout(manage_group)
        
        # Tutorial selection
        tutorial_layout = QHBoxLayout()
        tutorial_layout.addWidget(QLabel("Reset specific tutorial:"))
        
        self.tutorial_combo = QComboBox()
        self.tutorial_combo.addItems([
            "main_application",
            "split_widget", 
            "merge_widget",
            "image_converter",
            "search_widget",
            "settings"
        ])
        tutorial_layout.addWidget(self.tutorial_combo)
        
        self.reset_specific_btn = QPushButton("Reset Selected")
        self.reset_specific_btn.clicked.connect(self.reset_specific_tutorial)
        tutorial_layout.addWidget(self.reset_specific_btn)
        
        manage_layout.addLayout(tutorial_layout)
        
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
        manage_layout.addWidget(self.reset_all_btn)
        
        layout.addWidget(manage_group)
        
        # Tutorial status group
        status_group = QGroupBox("Tutorial Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        # Refresh status button
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self.update_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        # Connect signals
        self.enable_tutorials_cb.toggled.connect(self.on_settings_changed)
        self.auto_start_cb.toggled.connect(self.on_settings_changed)
        self.first_run_cb.toggled.connect(self.on_settings_changed)
        
        # Initial status update
        self.update_status()
    
    def load_settings(self):
        """Load current tutorial settings"""
        self.enable_tutorials_cb.setChecked(
            self.settings.get_setting("tutorials", "enabled", True)
        )
        self.auto_start_cb.setChecked(
            self.settings.get_setting("tutorials", "auto_start", True)
        )
        self.first_run_cb.setChecked(
            self.settings.get_setting("tutorials", "show_first_run", True)
        )
        
        # Enable/disable dependent controls
        self.on_enable_tutorials_changed()
        self.enable_tutorials_cb.toggled.connect(self.on_enable_tutorials_changed)
    
    def on_enable_tutorials_changed(self):
        """Handle tutorial enable/disable"""
        enabled = self.enable_tutorials_cb.isChecked()
        self.auto_start_cb.setEnabled(enabled)
        self.first_run_cb.setEnabled(enabled)
    
    def on_settings_changed(self):
        """Handle settings changes"""
        # Save immediately when settings change
        self.save_settings()
        self.update_status()
    
    def save_settings(self):
        """Save tutorial settings"""
        self.settings.set_setting("tutorials", "enabled", self.enable_tutorials_cb.isChecked())
        self.settings.set_setting("tutorials", "auto_start", self.auto_start_cb.isChecked())
        self.settings.set_setting("tutorials", "show_first_run", self.first_run_cb.isChecked())
        self.settings.save_settings()
    
    def update_status(self):
        """Update tutorial status display"""
        completed = self.settings.get_setting("tutorials", "completed", {})
        if not isinstance(completed, dict):
            completed = {}
        
        total_tutorials = len([
            "main_application", "split_widget", "merge_widget", 
            "image_converter", "search_widget", "settings"
        ])
        completed_count = len([k for k, v in completed.items() if v])
        
        enabled = self.settings.get_setting("tutorials", "enabled", True)
        auto_start = self.settings.get_setting("tutorials", "auto_start", True)
        
        status_text = f"""
<b>Tutorial System Status:</b><br>
• Enabled: {'Yes' if enabled else 'No'}<br>
• Auto-start: {'Yes' if auto_start else 'No'}<br>
• Completed tutorials: {completed_count} of {total_tutorials}<br>
• Remaining: {total_tutorials - completed_count}
        """
        
        if completed:
            status_text += "<br><br><b>Completed tutorials:</b><br>"
            for tutorial_name, is_completed in completed.items():
                if is_completed:
                    status_text += f"• {tutorial_name.replace('_', ' ').title()}<br>"
        
        self.status_label.setText(status_text.strip())
    
    def reset_specific_tutorial(self):
        """Reset a specific tutorial"""
        tutorial_name = self.tutorial_combo.currentText()
        
        reply = QMessageBox.question(
            self, 
            "Reset Tutorial",
            f"Reset the '{tutorial_name.replace('_', ' ').title()}' tutorial?\n\n"
            "This will allow the tutorial to be shown again.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.tutorial_manager:
                self.tutorial_manager.reset_tutorial_completion(tutorial_name)
            else:
                # Direct settings access if no tutorial manager
                completed = self.settings.get_setting("tutorials", "completed", {})
                if isinstance(completed, dict) and tutorial_name in completed:
                    del completed[tutorial_name]
                    self.settings.set_setting("tutorials", "completed", completed)
                    self.settings.save_settings()
            
            self.update_status()
            QMessageBox.information(self, "Tutorial Reset", f"The '{tutorial_name}' tutorial has been reset.")
    
    def reset_all_tutorials(self):
        """Reset all tutorials"""
        reply = QMessageBox.question(
            self,
            "Reset All Tutorials", 
            "Reset ALL tutorials?\n\n"
            "This will allow all tutorials to be shown again as if you were a new user.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.tutorial_manager:
                self.tutorial_manager.reset_tutorials()
            else:
                # Direct settings access if no tutorial manager
                self.settings.set_setting("tutorials", "completed", {})
                self.settings.save_settings()
            
            self.update_status()
            QMessageBox.information(self, "Tutorials Reset", "All tutorials have been reset.")

# Integration instructions for your settings dialog:

"""
TO ADD TUTORIAL SETTINGS TO YOUR EXISTING SETTINGS DIALOG:

1. Import the tutorial settings widget:
   from tutorial_settings_widget import TutorialSettingsWidget

2. In your settings dialog, add a new tab or section:
   
   # If using tabs:
   tutorial_tab = TutorialSettingsWidget(self.settings, self.tutorial_manager)
   self.tabs.addTab(tutorial_tab, "Tutorials")
   
   # If using sections:
   tutorial_section = TutorialSettingsWidget(self.settings, self.tutorial_manager)
   self.layout.addWidget(tutorial_section)

3. Make sure to pass your settings controller and tutorial manager:
   - settings_controller: Your SettingsController instance
   - tutorial_manager: Your TutorialManager instance (optional)

4. The widget will automatically:
   - Load current settings
   - Save changes immediately
   - Update status in real-time
   - Provide reset functionality

SETTINGS STRUCTURE:
The tutorial system uses these settings paths:
- tutorials.enabled: bool (default: True)
- tutorials.auto_start: bool (default: True) 
- tutorials.show_first_run: bool (default: True)
- tutorials.completed: dict (default: {})

Example completed dict:
{
    "main_application": True,
    "split_widget": False,
    "merge_widget": True
}
"""
