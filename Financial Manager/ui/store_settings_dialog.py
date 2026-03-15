"""
Store Location Settings Dialog
Allows setting the default location for tax calculations
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGroupBox, QCheckBox, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
from services.store_settings import StoreSettings
from assets.Logger import Logger

logger = Logger()

class StoreSettingsDialog(QDialog):
    """Dialog for managing store location and tax settings"""
    
    US_STATES = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
        'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina',
        'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
        'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
        'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
        'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Store Location & Tax Settings')
        self.setGeometry(100, 100, 500, 400)
        self.store_settings = StoreSettings()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout()
        
        # Store Info Section
        store_group = QGroupBox("Store Information")
        store_layout = QVBoxLayout()
        
        store_layout.addWidget(QLabel("Store Name:"))
        self.store_name_input = QLineEdit()
        store_layout.addWidget(self.store_name_input)
        
        store_layout.addWidget(QLabel("Address:"))
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Street address")
        store_layout.addWidget(self.address_input)
        
        store_group.setLayout(store_layout)
        main_layout.addWidget(store_group)
        
        # Location Section
        location_group = QGroupBox("Default Location for Tax Calculations")
        location_layout = QVBoxLayout()
        
        # State selector
        state_layout = QHBoxLayout()
        state_layout.addWidget(QLabel("State:"))
        self.state_combo = QComboBox()
        self.state_combo.addItem("-- Select State --", None)
        for code, name in sorted(self.US_STATES.items()):
            self.state_combo.addItem(f"{name} ({code})", code)
        state_layout.addWidget(self.state_combo)
        state_layout.addStretch()
        location_layout.addLayout(state_layout)
        
        # City input
        city_layout = QHBoxLayout()
        city_layout.addWidget(QLabel("City:"))
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("City name (optional for local taxes)")
        city_layout.addWidget(self.city_input)
        city_layout.addStretch()
        location_layout.addLayout(city_layout)
        
        # Zip code input
        zip_layout = QHBoxLayout()
        zip_layout.addWidget(QLabel("Zip Code:"))
        self.zip_input = QLineEdit()
        self.zip_input.setPlaceholderText("12345")
        zip_layout.addWidget(self.zip_input)
        zip_layout.addStretch()
        location_layout.addLayout(zip_layout)
        
        location_group.setLayout(location_layout)
        main_layout.addWidget(location_group)
        
        # Tax Preferences Section
        tax_group = QGroupBox("Tax Calculation Preferences")
        tax_layout = QVBoxLayout()
        
        self.state_tax_check = QCheckBox("Include State Sales Tax")
        self.state_tax_check.setChecked(True)
        tax_layout.addWidget(self.state_tax_check)
        
        self.local_tax_check = QCheckBox("Include Local/City Sales Tax")
        self.local_tax_check.setChecked(True)
        tax_layout.addWidget(self.local_tax_check)
        
        self.federal_tax_check = QCheckBox("Include Federal Tax")
        self.federal_tax_check.setChecked(False)
        tax_layout.addWidget(self.federal_tax_check)
        
        self.auto_calc_check = QCheckBox("Auto-Calculate Taxes in Sales")
        self.auto_calc_check.setChecked(True)
        self.auto_calc_check.setToolTip("If checked, taxes are automatically looked up and applied to sales")
        tax_layout.addWidget(self.auto_calc_check)
        
        tax_group.setLayout(tax_layout)
        main_layout.addWidget(tax_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load current settings into UI"""
        try:
            settings = self.store_settings.get_all_settings()
            
            # Store info
            self.store_name_input.setText(settings.get("store_name", "My Store"))
            self.address_input.setText(settings.get("location", {}).get("address", ""))
            
            # Location
            state = settings.get("location", {}).get("state")
            if state:
                index = self.state_combo.findData(state)
                if index >= 0:
                    self.state_combo.setCurrentIndex(index)
            
            self.city_input.setText(settings.get("location", {}).get("city", ""))
            self.zip_input.setText(settings.get("location", {}).get("zip_code", ""))
            
            # Tax preferences
            tax_prefs = settings.get("tax_settings", {})
            self.state_tax_check.setChecked(tax_prefs.get("include_state_tax", True))
            self.local_tax_check.setChecked(tax_prefs.get("include_local_tax", True))
            self.federal_tax_check.setChecked(tax_prefs.get("include_federal_tax", False))
            self.auto_calc_check.setChecked(tax_prefs.get("auto_calculate", True))
            
            logger.debug("StoreSettingsDialog", "Loaded settings into UI")
        except Exception as e:
            logger.error("StoreSettingsDialog", f"Error loading settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save settings from UI"""
        try:
            store_name = self.store_name_input.text().strip()
            if not store_name:
                QMessageBox.warning(self, "Error", "Store name is required")
                return
            
            state = self.state_combo.currentData()
            if not state:
                QMessageBox.warning(self, "Error", "Please select a state")
                return
            
            city = self.city_input.text().strip()
            zip_code = self.zip_input.text().strip()
            address = self.address_input.text().strip()
            
            # Save store name
            self.store_settings.set_store_name(store_name)
            
            # Save address
            self.store_settings.set_address(address)
            
            # Save location
            self.store_settings.set_location(state=state, city=city, zip_code=zip_code)
            
            # Save tax preferences
            tax_prefs = {
                "include_state_tax": self.state_tax_check.isChecked(),
                "include_local_tax": self.local_tax_check.isChecked(),
                "include_federal_tax": self.federal_tax_check.isChecked(),
                "auto_calculate": self.auto_calc_check.isChecked()
            }
            self.store_settings.set_tax_preferences(tax_prefs)
            
            logger.info("StoreSettingsDialog", f"Saved settings for {store_name} in {state}")
            QMessageBox.information(self, "Success", "Store settings saved successfully!")
            self.accept()
        
        except Exception as e:
            logger.error("StoreSettingsDialog", f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def reset_to_defaults(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.store_settings.reset_to_defaults():
                logger.info("StoreSettingsDialog", "Reset to default settings")
                self.load_settings()
                QMessageBox.information(self, "Success", "Settings reset to defaults")
            else:
                QMessageBox.critical(self, "Error", "Failed to reset settings")
