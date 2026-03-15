"""
Tax Rate Lookup Service
Supports multiple tax data sources with fallback logic:
1. Free public tax database (primary)
2. TaxJar API (fallback)
Supports combining state, local, and federal taxes
"""

import requests
import json
import os
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
from assets.Logger import Logger

logger = Logger()

# Load environment variables
load_dotenv('./resources/env.env')

class TaxService:
    """Service for looking up tax rates from multiple sources"""
    
    # Try multiple free tax database sources
    FREE_TAX_DB_URLS = [
        "https://raw.githubusercontent.com/evainnovations/usa_sales_tax_db/main/db.json",
        "https://api.ziplookup.com/tax",
    ]
    TAXJAR_API_KEY = os.getenv('TAXJAR_API_KEY', '')
    TAXJAR_API_URL = "https://api.taxjar.com/v2"
    
    # Federal tax rate (simplified - actually varies by product/service)
    FEDERAL_TAX_RATE = 0.0
    
    # Cache for tax rates to minimize API calls
    _tax_cache: Dict[str, Tuple[float, str]] = {}
    
    @classmethod
    def lookup_tax_rate(cls, location: str, include_federal: bool = False) -> Optional[Dict[str, float]]:
        """
        Look up tax rate for a location (state/city/zip).
        Returns dict with keys: 'state_rate', 'local_rate', 'combined_rate', 'source'
        or None if not found.
        
        Args:
            location: Can be state code (CA), city (San Francisco), or zip code (94102)
            include_federal: Whether to include federal tax in combined_rate
            
        Returns:
            Dict with tax rates or None if lookup fails
        """
        
        if not location:
            return None
        
        location = location.strip().upper()
        
        # Check cache first
        if location in cls._tax_cache:
            cached_rate, cached_source = cls._tax_cache[location]
            return {
                'state_rate': cached_rate,
                'local_rate': 0,
                'combined_rate': cached_rate,
                'source': cached_source
            }
        
        # Try hardcoded US state rates first (fastest, always available)
        result = cls._lookup_hardcoded_rates(location)
        if result:
            cls._tax_cache[location] = (result['combined_rate'], 'Hardcoded DB')
            return result
        
        # Try free database second
        result = cls._lookup_free_database(location)
        if result:
            cls._tax_cache[location] = (result['combined_rate'], 'Free DB')
            return result
        
        # Fall back to TaxJar if API key is configured
        if cls.TAXJAR_API_KEY:
            result = cls._lookup_taxjar(location)
            if result:
                cls._tax_cache[location] = (result['combined_rate'], 'TaxJar')
                return result
        
        logger.warning("TaxService", f"Could not find tax rate for location: {location}")
        return None
    
    @classmethod
    def _lookup_hardcoded_rates(cls, location: str) -> Optional[Dict[str, float]]:
        """
        Look up tax rate from hardcoded US state rates.
        This is fast and always available.
        """
        try:
            state_codes = cls.get_us_state_rates()
            
            # Extract state code (first 2 chars)
            state_code = location[:2] if len(location) >= 2 else location
            
            if state_code in state_codes:
                rate = state_codes[state_code]
                logger.info("TaxService", f"Found hardcoded rate for {location}: {rate*100:.2f}%")
                return {
                    'state_rate': rate,
                    'local_rate': 0,
                    'combined_rate': rate,
                    'source': 'Hardcoded Database'
                }
        except Exception as e:
            logger.debug("TaxService", f"Error looking up hardcoded rates: {e}")
        
        return None
    
    @classmethod
    def _lookup_free_database(cls, location: str) -> Optional[Dict[str, float]]:
        """
        Look up tax rate from free public database.
        Returns combined state + local tax rate.
        """
        try:
            # Try multiple free tax database URLs
            for url in cls.FREE_TAX_DB_URLS:
                try:
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    
                    tax_data = response.json()
                    
                    # Database format varies, but typically has state codes
                    # Extract state code from location (first 2 chars if it's a state code)
                    state_code = location[:2] if len(location) == 2 else None
                    
                    if state_code and state_code in tax_data:
                        state_info = tax_data[state_code]
                        
                        # Get state rate (usually under 'rate' or similar)
                        state_rate = float(state_info.get('rate', 0)) / 100
                        local_rate = 0
                        
                        # Try to get local rate if city/zip is provided
                        if len(location) > 2:
                            # For full lookups, some databases have city/zip data
                            local_rate = cls._extract_local_rate(tax_data, location)
                        
                        combined_rate = state_rate + local_rate
                        
                        logger.info("TaxService", 
                            f"Found tax rate for {location}: State={state_rate*100:.2f}%, Local={local_rate*100:.2f}%")
                        
                        return {
                            'state_rate': state_rate,
                            'local_rate': local_rate,
                            'combined_rate': combined_rate,
                            'source': 'Free Database'
                        }
                except requests.exceptions.RequestException:
                    continue  # Try next URL
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug("TaxService", f"Error parsing free tax database: {e}")
        
        return None
    
    @classmethod
    def _extract_local_rate(cls, tax_data: dict, location: str) -> float:
        """Extract local tax rate from database for city/zip"""
        try:
            # This depends on the database structure
            # For now, return 0 as a placeholder
            # You can expand this based on actual database structure
            return 0
        except Exception as e:
            logger.debug("TaxService", f"Could not extract local rate: {e}")
            return 0
    
    @classmethod
    def _lookup_taxjar(cls, location: str) -> Optional[Dict[str, float]]:
        """
        Look up tax rate from TaxJar API.
        Requires TAXJAR_API_KEY environment variable.
        """
        if not cls.TAXJAR_API_KEY:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {cls.TAXJAR_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # TaxJar expects state, city, or zip
            params = {}
            
            if len(location) == 2:  # State code
                params['state'] = location
            elif location.isdigit() and len(location) == 5:  # ZIP code
                params['zip'] = location
            else:  # Assume city
                params['city'] = location
            
            # Query TaxJar rates endpoint
            url = f"{cls.TAXJAR_API_URL}/rates/{location}"
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            rate_data = data.get('rate', {})
            
            state_rate = float(rate_data.get('state', 0)) / 100
            local_rate = float(rate_data.get('county', 0)) / 100 + float(rate_data.get('city', 0)) / 100
            combined_rate = state_rate + local_rate
            
            logger.info("TaxService",
                f"Found tax rate for {location} via TaxJar: State={state_rate*100:.2f}%, Local={local_rate*100:.2f}%")
            
            return {
                'state_rate': state_rate,
                'local_rate': local_rate,
                'combined_rate': combined_rate,
                'source': 'TaxJar'
            }
        
        except requests.exceptions.RequestException as e:
            logger.debug("TaxService", f"TaxJar lookup failed: {e}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug("TaxService", f"Error parsing TaxJar response: {e}")
        
        return None
    
    @classmethod
    def combine_taxes(cls, state_rate: float = 0, local_rate: float = 0, 
                     federal_rate: float = 0) -> float:
        """
        Combine multiple tax rates (state, local, federal).
        
        Args:
            state_rate: State sales tax (as decimal, e.g., 0.0725 for 7.25%)
            local_rate: Local/city sales tax
            federal_rate: Federal tax
            
        Returns:
            Combined tax rate as decimal
        """
        return state_rate + local_rate + federal_rate
    
    @classmethod
    def get_location_taxes(cls, location: str, include_state: bool = True,
                          include_local: bool = True, 
                          include_federal: bool = False) -> Optional[Dict]:
        """
        Get detailed tax breakdown for a location with options to include/exclude taxes.
        
        Args:
            location: State code, city, or zip
            include_state: Include state sales tax
            include_local: Include local/city tax
            include_federal: Include federal tax
            
        Returns:
            Dict with detailed tax breakdown or None
        """
        try:
            # Get base tax data
            tax_data = cls.lookup_tax_rate(location)
            
            if not tax_data:
                return None
            
            state_rate = tax_data['state_rate'] if include_state else 0
            local_rate = tax_data['local_rate'] if include_local else 0
            federal_rate = cls.FEDERAL_TAX_RATE if include_federal else 0
            
            combined = cls.combine_taxes(state_rate, local_rate, federal_rate)
            
            return {
                'state_rate': state_rate,
                'local_rate': local_rate,
                'federal_rate': federal_rate,
                'combined_rate': combined,
                'source': tax_data.get('source', 'Unknown'),
                'breakdown': {
                    'state': f"{state_rate*100:.2f}%" if state_rate > 0 else "None",
                    'local': f"{local_rate*100:.2f}%" if local_rate > 0 else "None",
                    'federal': f"{federal_rate*100:.2f}%" if federal_rate > 0 else "None"
                }
            }
        
        except Exception as e:
            logger.debug("TaxService", f"Error getting location taxes: {e}")
            return None
    
    @classmethod
    def get_us_state_rates(cls) -> Dict[str, float]:
        """
        Get a simple mapping of US state codes to sales tax rates.
        This is a hardcoded fallback for common states.
        """
        return {
            'AL': 0.04, 'AK': 0.00, 'AZ': 0.0560, 'AR': 0.0625, 'CA': 0.0725,
            'CO': 0.0290, 'CT': 0.0635, 'DE': 0.00, 'FL': 0.06, 'GA': 0.04,
            'HI': 0.04, 'ID': 0.06, 'IL': 0.0625, 'IN': 0.07, 'IA': 0.06,
            'KS': 0.0570, 'KY': 0.06, 'LA': 0.0445, 'ME': 0.055, 'MD': 0.06,
            'MA': 0.0625, 'MI': 0.06, 'MN': 0.0685, 'MS': 0.07, 'MO': 0.0725,
            'MT': 0.00, 'NE': 0.0550, 'NV': 0.0685, 'NH': 0.00, 'NJ': 0.0625,
            'NM': 0.0563, 'NY': 0.04, 'NC': 0.04, 'ND': 0.05, 'OH': 0.0575,
            'OK': 0.0450, 'OR': 0.00, 'PA': 0.06, 'RI': 0.07, 'SC': 0.05,
            'SD': 0.045, 'TN': 0.0925, 'TX': 0.0625, 'UT': 0.0610, 'VT': 0.06,
            'VA': 0.0575, 'WA': 0.0650, 'WV': 0.06, 'WI': 0.05, 'WY': 0.04,
        }
    
    @classmethod
    def clear_cache(cls):
        """Clear the tax rate cache"""
        cls._tax_cache.clear()
        logger.info("TaxService", "Tax rate cache cleared")
