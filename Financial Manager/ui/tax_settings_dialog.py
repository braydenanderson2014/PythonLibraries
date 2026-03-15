"""
Tax Settings Dialog
Allows administrators to set tax rates by location
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QGroupBox, QFormLayout, QComboBox, QApplication)
from PyQt6.QtCore import Qt
from src.pos_manager import POSManager
from services.tax_service import TaxService
from assets.Logger import Logger

logger = Logger()


class TaxSettingsDialog(QDialog):
    """Dialog for managing tax rates by location"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Tax Rate Settings')
        self.setGeometry(100, 100, 600, 500)
        self.pos_manager = POSManager()
        self.init_ui()
        self.load_tax_rates()
    
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout()
        
        # Default tax rate section
        default_group = QGroupBox("Default Tax Rate")
        default_layout = QFormLayout()
        
        default_layout.addRow(QLabel("Default Tax Rate (%):"))
        self.default_tax_input = QDoubleSpinBox()
        self.default_tax_input.setMinimum(0)
        self.default_tax_input.setMaximum(100)
        self.default_tax_input.setDecimals(4)
        self.default_tax_input.setValue(8.0)
        self.default_tax_input.setToolTip("Tax rate used when no location is specified")
        default_layout.addRow(self.default_tax_input)
        
        default_group.setLayout(default_layout)
        main_layout.addWidget(default_group)
        
        # Location-specific rates section
        location_group = QGroupBox("Location-Specific Tax Rates")
        location_layout = QVBoxLayout()
        
        # Search/Select existing location
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Quick Select:"))
        self.location_search_combo = QComboBox()
        self.location_search_combo.addItem("-- Choose a location --", None)
        self.location_search_combo.currentIndexChanged.connect(self.on_location_selected)
        search_layout.addWidget(self.location_search_combo)
        search_layout.addStretch()
        location_layout.addLayout(search_layout)
        
        # Input fields for adding/updating
        input_layout = QHBoxLayout()
        
        input_layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Type location (CA, NY, TX, etc.)")
        self.location_input.textChanged.connect(self.lookup_location_tax_rate)
        input_layout.addWidget(self.location_input)
        
        # Lookup button
        lookup_btn = QPushButton("Look Up")
        lookup_btn.setMaximumWidth(80)
        lookup_btn.clicked.connect(self.lookup_location_tax_rate)
        input_layout.addWidget(lookup_btn)
        
        # Status label for auto-lookup (shows result or spinner)
        self.lookup_status_label = QLabel("Ready")
        self.lookup_status_label.setStyleSheet("color: blue; font-weight: bold; min-width: 250px;")
        input_layout.addWidget(self.lookup_status_label)
        
        location_layout.addLayout(input_layout)
        
        # Tax rate input
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Auto Tax Rate:"))
        self.location_tax_input = QDoubleSpinBox()
        self.location_tax_input.setMinimum(0)
        self.location_tax_input.setMaximum(100)
        self.location_tax_input.setDecimals(4)
        self.location_tax_input.setValue(8.0)
        self.location_tax_input.setToolTip("Auto-populated from online lookup. Edit to override.")
        rate_layout.addWidget(self.location_tax_input)
        
        add_btn = QPushButton("Save Tax Rate")
        add_btn.setMaximumWidth(120)
        add_btn.clicked.connect(self.add_or_update_location)
        rate_layout.addWidget(add_btn)
        rate_layout.addStretch()
        
        location_layout.addLayout(rate_layout)
        
        # Tax rates table
        self.tax_table = QTableWidget()
        self.tax_table.setColumnCount(3)
        self.tax_table.setHorizontalHeaderLabels(["Location", "Tax Rate (%)", "Remove"])
        self.tax_table.horizontalHeader().setStretchLastSection(False)
        location_layout.addWidget(self.tax_table)
        
        location_group.setLayout(location_layout)
        main_layout.addWidget(location_group)
        
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
    
    def load_tax_rates(self):
        """Load current tax rates from POSManager"""
        try:
            # Load all tax rates
            all_rates = self.pos_manager.get_all_tax_rates()
            
            # Look for default rate
            default_rate = 0.08  # Default fallback
            if 'DEFAULT' in all_rates:
                default_rate = all_rates['DEFAULT']
            elif None in all_rates:
                default_rate = all_rates[None]
            
            self.default_tax_input.setValue(default_rate * 100)
            
            # Populate search combo with existing locations
            self.location_search_combo.blockSignals(True)
            self.location_search_combo.clear()
            self.location_search_combo.addItem("-- Select a location --", None)
            
            # Add all existing locations to search combo
            locations_added = set()
            
            self.tax_table.setRowCount(0)
            for location, rate in all_rates.items():
                if location is None or location == 'DEFAULT':
                    continue  # Skip the default, it's handled separately
                
                # Add to search combo
                if location not in locations_added:
                    self.location_search_combo.addItem(str(location), location)
                    locations_added.add(location)
                
                row = self.tax_table.rowCount()
                self.tax_table.insertRow(row)
                
                # Location name
                location_item = QTableWidgetItem(location)
                location_item.setFlags(location_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tax_table.setItem(row, 0, location_item)
                
                # Tax rate (convert from decimal to percentage)
                rate_value = rate if isinstance(rate, (int, float)) else 0.0
                rate_item = QTableWidgetItem(f"{rate_value*100:.4f}")
                rate_item.setFlags(rate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tax_table.setItem(row, 1, rate_item)
                
                # Remove button
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, l=location: self.remove_location(l))
                self.tax_table.setCellWidget(row, 2, remove_btn)
            
            self.location_search_combo.blockSignals(False)
            logger.info("TaxSettingsDialog", f"Loaded {self.tax_table.rowCount()} location-specific tax rates")
            
        except Exception as e:
            logger.error("TaxSettingsDialog", f"Error loading tax rates: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load tax rates: {e}")
    
    def add_or_update_location(self):
        """Add or update a location's tax rate"""
        try:
            location = self.location_input.text().strip()
            if not location:
                QMessageBox.warning(self, "Error", "Please enter a location name")
                return
            
            tax_rate = self.location_tax_input.value() / 100.0
            
            # IMMEDIATELY save to database - don't wait for Save Settings button
            logger.debug("TaxSettingsDialog", f"Immediately saving tax rate to database: {location} = {tax_rate}")
            self.pos_manager.add_location_tax_rate(location, tax_rate)
            
            # Check if location already exists
            existing_row = -1
            for row in range(self.tax_table.rowCount()):
                if self.tax_table.item(row, 0).text() == location:
                    existing_row = row
                    break
            
            if existing_row >= 0:
                # Update existing
                self.tax_table.item(existing_row, 1).setText(f"{tax_rate*100:.4f}")
                # CRITICAL FIX: Reload tax rates immediately after update
                self.pos_manager.reload_tax_rates()
                QMessageBox.information(self, "Success", f"Updated tax rate for {location} (saved to database)")
            else:
                # Add new
                row = self.tax_table.rowCount()
                self.tax_table.insertRow(row)
                
                location_item = QTableWidgetItem(location)
                location_item.setFlags(location_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tax_table.setItem(row, 0, location_item)
                
                rate_item = QTableWidgetItem(f"{tax_rate*100:.4f}")
                rate_item.setFlags(rate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tax_table.setItem(row, 1, rate_item)
                
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, l=location: self.remove_location(l))
                self.tax_table.setCellWidget(row, 2, remove_btn)
                
                # CRITICAL FIX: Reload tax rates immediately after add
                self.pos_manager.reload_tax_rates()
                QMessageBox.information(self, "Success", f"Added tax rate for {location} (saved to database)")
            
            # Clear inputs
            self.location_input.clear()
            self.location_tax_input.setValue(8.0)
            
        except Exception as e:
            logger.error("TaxSettingsDialog", f"Error adding/updating location: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add/update location: {e}")
    
    def remove_location(self, location):
        """Remove a location from the table"""
        try:
            for row in range(self.tax_table.rowCount()):
                if self.tax_table.item(row, 0).text() == location:
                    self.tax_table.removeRow(row)
                    break
        except Exception as e:
            logger.error("TaxSettingsDialog", f"Error removing location: {e}")
    
    def lookup_location_tax_rate(self):
        """Automatically look up and populate tax rate for entered location"""
        try:
            location = self.location_input.text().strip().upper()
            if not location:
                self.location_tax_input.setValue(8.0)  # Reset to default
                self.lookup_status_label.setText("Ready")
                self.lookup_status_label.setStyleSheet("color: blue; font-weight: bold;")
                return
            
            # Show loading status
            self.lookup_status_label.setText("Looking up...")
            self.lookup_status_label.setStyleSheet("color: orange; font-weight: bold;")
            QApplication.processEvents()  # Update UI immediately
            
            # Try online lookup first (TaxService with smart fallback)
            tax_data = TaxService.lookup_tax_rate(location)
            
            if tax_data:
                # Found online!
                combined_rate = tax_data['combined_rate'] * 100
                state_rate = tax_data['state_rate'] * 100
                local_rate = tax_data['local_rate'] * 100
                source = tax_data.get('source', 'Unknown')
                
                # Populate the tax rate input
                self.location_tax_input.setValue(combined_rate)
                
                # Show detailed status
                if local_rate > 0:
                    status = f"FOUND ({source}): State {state_rate:.2f}% + Local {local_rate:.2f}% = {combined_rate:.2f}%"
                else:
                    status = f"FOUND ({source}): {combined_rate:.2f}%"
                
                self.lookup_status_label.setText(status)
                self.lookup_status_label.setStyleSheet("color: green; font-weight: bold;")
                logger.info("TaxSettingsDialog", f"Online lookup for {location}: {status}")
            else:
                # Not found online
                self.lookup_status_label.setText("NOT FOUND - Enter rate manually below")
                self.lookup_status_label.setStyleSheet("color: red; font-weight: bold;")
                logger.warning("TaxSettingsDialog", f"Could not find online tax rate for {location}")
            
        except Exception as e:
            logger.debug("TaxSettingsDialog", f"Error looking up tax rate: {e}")
            self.lookup_status_label.setText(f"ERROR: {str(e)[:40]}")
            self.lookup_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def on_location_selected(self, index):
        """Handle location selection from search combo"""
        # Get the data associated with the selected item
        location = self.location_search_combo.itemData(index)
        if location is None:
            return
        
        # Clear the input and populate with selected location
        self.location_input.blockSignals(True)
        self.location_input.setText(str(location))
        self.location_input.blockSignals(False)
        
        # Trigger lookup to populate tax rate
        self.lookup_location_tax_rate()
    
    def save_settings(self):
        """Save all tax settings"""
        try:
            # Save default tax rate
            default_rate = self.default_tax_input.value() / 100.0
            self.pos_manager.set_default_tax_rate(default_rate)
            
            # Save location-specific rates
            for row in range(self.tax_table.rowCount()):
                location = self.tax_table.item(row, 0).text()
                rate_text = self.tax_table.item(row, 1).text()
                rate = float(rate_text) / 100.0
                
                self.pos_manager.add_location_tax_rate(location, rate)
            
            # CRITICAL FIX: Reload tax rates from database so they're immediately available
            # This ensures that any open POS tabs will get the updated rates when they check
            logger.info("TaxSettingsDialog", "Reloading tax rates after save")
            self.pos_manager.reload_tax_rates()
            
            logger.info("TaxSettingsDialog", "Tax settings saved and reloaded successfully")
            QMessageBox.information(self, "Success", "Tax settings saved successfully!")
            
        except Exception as e:
            logger.error("TaxSettingsDialog", f"Error saving tax settings: {e}")
            QMessageBox.critical(self, "Error", f"Error saving tax settings: {e}")

            QMessageBox.critical(self, "Error", f"Failed to save tax settings: {e}")
    
    def reset_to_defaults(self):
        """Reset to default tax values"""
        reply = QMessageBox.question(
            self, 'Confirm Reset',
            'Are you sure you want to reset all tax rates to defaults?\n\nThis will reset the default rate to 8% and remove all location-specific rates.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.default_tax_input.setValue(8.0)
                self.tax_table.setRowCount(0)
                self.pos_manager.set_default_tax_rate(0.08)
                QMessageBox.information(self, "Success", "Tax rates reset to defaults")
            except Exception as e:
                logger.error("TaxSettingsDialog", f"Error resetting tax rates: {e}")
                QMessageBox.critical(self, "Error", f"Failed to reset tax rates: {e}")
