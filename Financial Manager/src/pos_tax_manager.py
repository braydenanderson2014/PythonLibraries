"""
POS Tax Management Module
Handles tax calculations and location-based tax rates
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.Logger import Logger

logger = Logger()

# US State Tax Rates (default rates, can be customized)
DEFAULT_TAX_RATES = {
    "AL": 4.0, "AK": 0.0, "AZ": 5.6, "AR": 6.5, "CA": 7.25,
    "CO": 2.9, "CT": 6.35, "DE": 0.0, "FL": 6.0, "GA": 4.0,
    "HI": 4.0, "ID": 6.0, "IL": 6.25, "IN": 7.0, "IA": 6.0,
    "KS": 5.7, "KY": 6.0, "LA": 4.45, "ME": 5.5, "MD": 6.0,
    "MA": 6.25, "MI": 6.0, "MN": 6.875, "MS": 7.0, "MO": 4.225,
    "MT": 0.0, "NE": 5.5, "NV": 6.85, "NH": 0.0, "NJ": 6.625,
    "NM": 5.125, "NY": 4.0, "NC": 4.75, "ND": 5.0, "OH": 5.75,
    "OK": 4.45, "OR": 0.0, "PA": 6.0, "RI": 7.0, "SC": 6.0,
    "SD": 4.2, "TN": 7.0, "TX": 6.25, "UT": 4.85, "VT": 6.0,
    "VA": 5.3, "WA": 6.5, "WV": 6.0, "WI": 5.0, "WY": 4.0
}


class POSTaxManager:
    """Manages tax calculations and rates"""
    
    def __init__(self, db_manager=None):
        """Initialize tax manager with optional database"""
        logger.debug("POSTaxManager", "Initializing POSTaxManager")
        self.db = db_manager
        self.tax_rates_cache = {}
        self.load_tax_rates()
        logger.info("POSTaxManager", "POSTaxManager initialized successfully")
    
    def load_tax_rates(self):
        """Load tax rates from database or use defaults"""
        logger.debug("POSTaxManager", "Loading tax rates from database")
        if self.db:
            try:
                self.tax_rates_cache = self._load_from_database()
                logger.info("POSTaxManager", f"Loaded {len(self.tax_rates_cache)} tax rates from database")
            except Exception as e:
                logger.warning("POSTaxManager", f"Error loading from database: {e}, using defaults")
                self.tax_rates_cache = DEFAULT_TAX_RATES.copy()
        else:
            self.tax_rates_cache = DEFAULT_TAX_RATES.copy()
    
    def reload_tax_rates(self):
        """Reload tax rates from database (call after changes are saved)"""
        logger.info("POSTaxManager", "Reloading tax rates from database")
        self.load_tax_rates()
        logger.info("POSTaxManager", f"Tax rates reloaded. Cache now contains: {list(self.tax_rates_cache.keys())}")
    
    def _load_from_database(self) -> Dict[str, float]:
        """Load active tax rates from database"""
        if not self.db:
            return {}
        
        try:
            cursor = self.db.execute_query(
                'SELECT location, rate FROM pos_tax_rates WHERE is_active = 1'
            )
            return {row['location']: row['rate'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error("POSTaxManager", f"Error loading tax rates from database: {e}")
            return {}
    
    def get_tax_rate(self, location: str) -> float:
        """Get tax rate for a location
        
        Args:
            location: Location code (e.g., 'CA', 'NYC', or full address). If None/empty, uses DEFAULT rate
        
        Returns:
            Tax rate as decimal (0.0-1.0, e.g., 0.08 for 8%)
        """
        logger.debug("POSTaxManager", f"Getting tax rate for location: {location}")
        
        if not location:
            # Use DEFAULT rate if no location provided
            if 'DEFAULT' in self.tax_rates_cache:
                default_rate_pct = self.tax_rates_cache['DEFAULT']
                logger.debug("POSTaxManager", f"No location provided, using DEFAULT rate: {default_rate_pct}%")
                return default_rate_pct / 100.0  # Convert percentage to decimal
            else:
                logger.warning("POSTaxManager", "No location and no DEFAULT rate defined, using 0% tax")
                return 0.0
        
        location_upper = location.upper().strip()
        
        # Check if exact match in cache
        if location_upper in self.tax_rates_cache:
            return self.tax_rates_cache[location_upper] / 100.0  # Convert percentage to decimal
        
        # Try to extract state code (first 2 characters or before comma)
        state_code = location_upper.split(',')[0].strip()[-2:] if ',' in location_upper else location_upper[:2]
        
        if state_code in self.tax_rates_cache:
            return self.tax_rates_cache[state_code] / 100.0  # Convert percentage to decimal
        
        # Fall back to DEFAULT if location not found
        if 'DEFAULT' in self.tax_rates_cache:
            default_rate_pct = self.tax_rates_cache['DEFAULT']
            logger.debug("POSTaxManager", f"Tax rate not found for {location}, using DEFAULT: {default_rate_pct}%")
            return default_rate_pct / 100.0  # Convert percentage to decimal
        
        # Default to 0% if nothing found
        logger.warning("POSTaxManager", f"Tax rate not found for {location} and no DEFAULT defined, using 0%")
        return 0.0
    
    def calculate_tax(self, subtotal: float, tax_rate: float) -> float:
        """Calculate tax amount
        
        Args:
            subtotal: Pre-tax amount
            tax_rate: Tax rate as decimal (0.0-1.0, e.g., 0.08 for 8%)
        
        Returns:
            Tax amount rounded to 2 decimal places
        """
        tax_rate_pct = tax_rate * 100.0 if tax_rate < 1 else tax_rate
        logger.debug("POSTaxManager", f"Calculating tax: subtotal=${subtotal:.2f}, rate={tax_rate_pct:.2f}%")
        tax_amount = subtotal * tax_rate
        return round(tax_amount, 2)
    
    def calculate_total_with_tax(self, subtotal: float, tax_rate: float) -> tuple:
        """Calculate total including tax
        
        Args:
            subtotal: Pre-tax amount
            tax_rate: Tax rate as decimal (0.0-1.0, e.g., 0.08 for 8%)
        
        Returns:
            Tuple of (tax_amount, total_with_tax)
        """
        tax_amount = self.calculate_tax(subtotal, tax_rate)
        total = round(subtotal + tax_amount, 2)
        return tax_amount, total
    
    def add_tax_rate(self, location: str, rate: float, description: str = "") -> str:
        """Add or update a tax rate for a location
        
        Args:
            location: Location code (e.g., 'CA', 'NYC')
            rate: Tax rate as percentage (0-100)
            description: Optional description
        
        Returns:
            Tax rate ID
        """
        logger.debug("POSTaxManager", f"Adding tax rate: {location} = {rate}%")
        
        if rate < 0 or rate > 100:
            logger.error("POSTaxManager", f"Invalid tax rate: {rate}")
            raise ValueError(f"Tax rate must be between 0 and 100, got {rate}")
        
        if not self.db:
            logger.warning("POSTaxManager", "No database manager, only updating cache")
            self.tax_rates_cache[location.upper()] = rate
            return ""
        
        try:
            tax_rate_id = str(uuid.uuid4())
            self.db.execute_query('''
                INSERT OR REPLACE INTO pos_tax_rates 
                (tax_rate_id, location, rate, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (tax_rate_id, location.upper(), rate, description))
            
            self.db.commit()
            
            # Update cache
            self.tax_rates_cache[location.upper()] = rate
            
            logger.info("POSTaxManager", f"Tax rate added: {location} = {rate}%")
            return tax_rate_id
        except Exception as e:
            logger.error("POSTaxManager", f"Error adding tax rate: {e}")
            raise
    
    def get_all_tax_rates(self) -> Dict[str, float]:
        """Get all tax rates from database
        
        Returns:
            Dictionary of location -> tax rate (as decimal 0-1)
        """
        logger.debug("POSTaxManager", "Fetching all tax rates")
        
        if not self.db:
            # Return rates as decimals for dialog compatibility
            return {loc: (rate / 100.0) for loc, rate in self.tax_rates_cache.items()}
        
        try:
            cursor = self.db.execute_query(
                'SELECT location, rate FROM pos_tax_rates WHERE is_active = 1 ORDER BY location'
            )
            # Return rates as decimals
            return {row['location']: (row['rate'] / 100.0) for row in cursor.fetchall()}
        except Exception as e:
            logger.error("POSTaxManager", f"Error fetching tax rates: {e}")
            return {}
    
    def set_default_tax_rate(self, rate: float) -> bool:
        """Set the default tax rate for the business
        
        Args:
            rate: Tax rate as decimal (e.g., 0.08 for 8%)
        
        Returns:
            True if successful
        """
        logger.debug("POSTaxManager", f"Setting default tax rate to {rate}")
        
        if rate < 0 or rate > 1:
            logger.error("POSTaxManager", "Tax rate must be between 0 and 1")
            raise ValueError("Tax rate must be between 0 and 1")
        
        # Convert decimal to percentage for storage
        rate_percentage = rate * 100.0
        
        if not self.db:
            logger.warning("POSTaxManager", "No database manager, only updating cache")
            # Store as a special default entry
            self.tax_rates_cache['DEFAULT'] = rate_percentage
            return True
        
        try:
            # Add or update the DEFAULT entry
            self.add_tax_rate('DEFAULT', rate_percentage, 'Default tax rate')
            logger.info("POSTaxManager", f"Default tax rate set to {rate_percentage}%")
            return True
        except Exception as e:
            logger.error("POSTaxManager", f"Error setting default tax rate: {e}")
            return False
    
    def add_location_tax_rate(self, location: str, rate: float) -> bool:
        """Add or update tax rate for a specific location (alias for add_tax_rate with decimal conversion)
        
        Args:
            location: Location code (e.g., 'CA', 'NYC')
            rate: Tax rate as decimal (e.g., 0.08 for 8%)
        
        Returns:
            True if successful
        """
        logger.debug("POSTaxManager", f"Adding location tax rate: {location} = {rate}")
        
        if rate < 0 or rate > 1:
            logger.error("POSTaxManager", "Tax rate must be between 0 and 1")
            raise ValueError("Tax rate must be between 0 and 1")
        
        # Convert decimal to percentage for storage
        rate_percentage = rate * 100.0
        
        try:
            self.add_tax_rate(location, rate_percentage, f"Tax rate for {location}")
            return True
        except Exception as e:
            logger.error("POSTaxManager", f"Error adding location tax rate: {e}")
            return False
    
    def deactivate_tax_rate(self, location: str) -> bool:
        """Deactivate a tax rate"""
        logger.debug("POSTaxManager", f"Deactivating tax rate: {location}")
        
        if not self.db:
            if location.upper() in self.tax_rates_cache:
                del self.tax_rates_cache[location.upper()]
            return True
        
        try:
            self.db.execute_query(
                'UPDATE pos_tax_rates SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE location = ?',
                (location.upper(),)
            )
            self.db.commit()
            
            if location.upper() in self.tax_rates_cache:
                del self.tax_rates_cache[location.upper()]
            
            logger.info("POSTaxManager", f"Tax rate deactivated: {location}")
            return True
        except Exception as e:
            logger.error("POSTaxManager", f"Error deactivating tax rate: {e}")
            return False
    
    def get_state_tax_rate(self, state_code: str) -> float:
        """Get default US state tax rate
        
        Args:
            state_code: Two-letter state code (e.g., 'CA')
        
        Returns:
            Default tax rate for state
        """
        state_code_upper = state_code.upper()
        return DEFAULT_TAX_RATES.get(state_code_upper, 0.0)
    
    def reset_to_defaults(self) -> int:
        """Reset all tax rates to US defaults
        
        Returns:
            Number of tax rates added
        """
        logger.debug("POSTaxManager", "Resetting tax rates to defaults")
        
        if not self.db:
            self.tax_rates_cache = DEFAULT_TAX_RATES.copy()
            return len(DEFAULT_TAX_RATES)
        
        try:
            # Clear existing
            self.db.execute_query('DELETE FROM pos_tax_rates')
            
            # Add defaults
            count = 0
            for location, rate in DEFAULT_TAX_RATES.items():
                self.add_tax_rate(location, rate, f"Default US state rate")
                count += 1
            
            logger.info("POSTaxManager", f"Reset {count} tax rates to defaults")
            self.load_tax_rates()
            return count
        except Exception as e:
            logger.error("POSTaxManager", f"Error resetting tax rates: {e}")
            return 0
