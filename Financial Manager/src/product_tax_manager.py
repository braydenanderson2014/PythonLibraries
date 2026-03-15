"""
Product Tax Category Management
Manages different tax categories (grocery, standard, tools, exempt, etc.)
"""

from typing import Dict, Optional, List, Any
import uuid
from assets.Logger import Logger

logger = Logger()

# Default tax categories
DEFAULT_TAX_CATEGORIES = {
    "grocery": {
        "description": "Grocery/food items (reduced/exempt tax)",
        "tax_rate_modifier": -0.03,  # Reduce base rate by 3%
        "is_exempt": False
    },
    "standard": {
        "description": "Standard retail items",
        "tax_rate_modifier": 0.0,  # No modifier
        "is_exempt": False
    },
    "tools": {
        "description": "Tools and equipment",
        "tax_rate_modifier": 0.01,  # Increase by 1%
        "is_exempt": False
    },
    "clothing": {
        "description": "Clothing items (often reduced tax)",
        "tax_rate_modifier": -0.02,  # Reduce by 2%
        "is_exempt": False
    },
    "services": {
        "description": "Services (often exempt or different rate)",
        "tax_rate_modifier": 0.0,
        "is_exempt": True
    },
    "digital": {
        "description": "Digital goods/downloads",
        "tax_rate_modifier": 0.0,
        "is_exempt": False
    }
}


class ProductTaxManager:
    """Manages product tax categories and calculations"""
    
    def __init__(self, db_manager=None):
        """Initialize product tax manager"""
        logger.debug("ProductTaxManager", "Initializing ProductTaxManager")
        self.db = db_manager
        self.categories_cache = {}
        self.load_categories()
        logger.info("ProductTaxManager", "ProductTaxManager initialized successfully")
    
    def load_categories(self):
        """Load tax categories from database or initialize defaults"""
        logger.debug("ProductTaxManager", "Loading tax categories")
        
        if self.db:
            try:
                categories = self.db.get_all_product_tax_categories()
                self.categories_cache = {cat['category_name']: cat for cat in categories}
                logger.info("ProductTaxManager", f"Loaded {len(categories)} tax categories from database")
                
                # Add missing default categories
                for default_name in DEFAULT_TAX_CATEGORIES:
                    if default_name not in self.categories_cache:
                        self.add_category(
                            default_name,
                            DEFAULT_TAX_CATEGORIES[default_name]['description'],
                            DEFAULT_TAX_CATEGORIES[default_name]['tax_rate_modifier'],
                            DEFAULT_TAX_CATEGORIES[default_name]['is_exempt']
                        )
            except Exception as e:
                logger.warning("ProductTaxManager", f"Failed to load from database: {e}")
                self._initialize_defaults()
        else:
            self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize with default categories"""
        logger.debug("ProductTaxManager", "Initializing with default tax categories")
        for name, config in DEFAULT_TAX_CATEGORIES.items():
            if name not in self.categories_cache:
                self.categories_cache[name] = {
                    'category_name': name,
                    'description': config['description'],
                    'tax_rate_modifier': config['tax_rate_modifier'],
                    'is_exempt': config['is_exempt']
                }
    
    def add_category(self, category_name: str, description: str = "",
                    tax_rate_modifier: float = 0.0, is_exempt: bool = False) -> str:
        """Add a new tax category"""
        logger.debug("ProductTaxManager", f"Adding category: {category_name}")
        
        category_id = str(uuid.uuid4())
        
        category = {
            'tax_category_id': category_id,
            'category_name': category_name,
            'description': description,
            'tax_rate_modifier': tax_rate_modifier,
            'is_exempt': is_exempt
        }
        
        self.categories_cache[category_name] = category
        
        # Save to database if available
        if self.db:
            try:
                self.db.add_product_tax_category(
                    category_name, description, tax_rate_modifier, is_exempt
                )
            except Exception as e:
                logger.warning("ProductTaxManager", f"Failed to save to database: {e}")
        
        logger.info("ProductTaxManager", f"Category added: {category_id}")
        return category_id
    
    def get_category(self, category_name: str) -> Optional[Dict[str, Any]]:
        """Get a tax category by name"""
        logger.debug("ProductTaxManager", f"Fetching category: {category_name}")
        return self.categories_cache.get(category_name)
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all tax categories"""
        logger.debug("ProductTaxManager", "Fetching all categories")
        return list(self.categories_cache.values())
    
    def get_category_names(self) -> List[str]:
        """Get list of all category names"""
        return list(self.categories_cache.keys())
    
    def calculate_tax_with_category(self, amount: float, base_tax_rate: float,
                                   category_name: str = "standard") -> float:
        """
        Calculate tax for an amount considering product category
        
        Args:
            amount: Item price
            base_tax_rate: Base location tax rate (as decimal, e.g., 0.0725)
            category_name: Product tax category
            
        Returns:
            Adjusted tax amount
        """
        logger.debug("ProductTaxManager", 
                    f"Calculating tax: amount={amount}, base_rate={base_tax_rate}, category={category_name}")
        
        category = self.get_category(category_name)
        if not category:
            logger.warning("ProductTaxManager", f"Category not found: {category_name}, using standard")
            category = self.get_category("standard") or {"tax_rate_modifier": 0.0, "is_exempt": False}
        
        # If exempt from tax
        if category.get('is_exempt', False):
            logger.debug("ProductTaxManager", f"Item is tax exempt: {category_name}")
            return 0.0
        
        # Apply modifier to base rate
        modifier = category.get('tax_rate_modifier', 0.0)
        adjusted_rate = max(0.0, base_tax_rate + modifier)  # Ensure rate doesn't go negative
        
        tax_amount = amount * adjusted_rate
        logger.debug("ProductTaxManager", 
                    f"Tax calculated: base_rate={base_tax_rate:.4f}, modifier={modifier:.4f}, "
                    f"adjusted_rate={adjusted_rate:.4f}, tax=${tax_amount:.2f}")
        
        return tax_amount
    
    def get_category_description(self, category_name: str) -> str:
        """Get description of a tax category"""
        category = self.get_category(category_name)
        if category:
            return category.get('description', '')
        return 'Unknown category'
    
    def is_category_exempt(self, category_name: str) -> bool:
        """Check if a category is exempt from tax"""
        category = self.get_category(category_name)
        return category.get('is_exempt', False) if category else False
    
    def get_tax_rate_info(self, category_name: str) -> Dict[str, Any]:
        """Get detailed tax rate info for a category"""
        category = self.get_category(category_name) or self.get_category("standard")
        
        return {
            'category_name': category.get('category_name', 'standard'),
            'description': category.get('description', ''),
            'tax_rate_modifier': category.get('tax_rate_modifier', 0.0),
            'is_exempt': category.get('is_exempt', False),
            'modifier_percentage': category.get('tax_rate_modifier', 0.0) * 100
        }
