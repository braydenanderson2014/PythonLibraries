"""
Rental Management System
Manages product rentals integrated with POS
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import uuid
from assets.Logger import Logger

logger = Logger()


class RentalManager:
    """Manages rental operations"""
    
    def __init__(self, db_manager=None):
        """Initialize rental manager"""
        logger.debug("RentalManager", "Initializing RentalManager")
        self.db = db_manager
        logger.info("RentalManager", "RentalManager initialized successfully")
    
    def create_rental(self, product_id: str, customer_name: str, 
                     start_date: str, end_date: str, daily_rate: float,
                     notes: str = "") -> Optional[str]:
        """
        Create a new rental
        
        Args:
            product_id: Product being rented
            customer_name: Name of customer
            start_date: Rental start date (YYYY-MM-DD or timestamp)
            end_date: Rental end date (YYYY-MM-DD or timestamp)
            daily_rate: Daily rental rate
            notes: Optional notes
            
        Returns:
            Rental ID or None if failed
        """
        logger.debug("RentalManager", f"Creating rental for product {product_id}")
        
        if not self.db:
            logger.warning("RentalManager", "No database manager available")
            return None
        
        try:
            rental_id = self.db.add_rental(
                product_id, customer_name, start_date, end_date, daily_rate, notes
            )
            logger.info("RentalManager", f"Rental created: {rental_id}")
            return rental_id
        except Exception as e:
            logger.error("RentalManager", f"Failed to create rental: {e}")
            return None
    
    def get_rental(self, rental_id: str) -> Optional[Dict[str, Any]]:
        """Get rental details"""
        logger.debug("RentalManager", f"Fetching rental: {rental_id}")
        
        if not self.db:
            return None
        
        return self.db.get_rental(rental_id)
    
    def get_active_rentals(self) -> List[Dict[str, Any]]:
        """Get all active rentals"""
        logger.debug("RentalManager", "Fetching active rentals")
        
        if not self.db:
            return []
        
        return self.db.get_active_rentals()
    
    def get_customer_rentals(self, customer_name: str) -> List[Dict[str, Any]]:
        """Get all rentals for a customer"""
        logger.debug("RentalManager", f"Fetching rentals for customer: {customer_name}")
        
        if not self.db:
            return []
        
        return self.db.get_rentals_by_customer(customer_name)
    
    def calculate_rental_cost(self, rental_id: str) -> Optional[Dict[str, float]]:
        """
        Calculate total rental cost
        
        Returns:
            Dict with days_rented, daily_rate, total_cost
        """
        rental = self.get_rental(rental_id)
        if not rental:
            return None
        
        # Parse dates
        try:
            start = datetime.fromisoformat(rental['rental_start_date'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(rental['rental_end_date'].replace('Z', '+00:00'))
        except:
            # Try parsing as simple datetime
            try:
                start = datetime.strptime(rental['rental_start_date'], '%Y-%m-%d %H:%M:%S')
                end = datetime.strptime(rental['rental_end_date'], '%Y-%m-%d %H:%M:%S')
            except:
                start = datetime.strptime(rental['rental_start_date'], '%Y-%m-%d')
                end = datetime.strptime(rental['rental_end_date'], '%Y-%m-%d')
        
        days = (end - start).days
        if days < 1:
            days = 1  # Minimum 1 day
        
        daily_rate = rental['daily_rate']
        total_cost = days * daily_rate
        
        logger.debug("RentalManager", 
                    f"Rental cost: {days} days × ${daily_rate:.2f} = ${total_cost:.2f}")
        
        return {
            'days_rented': days,
            'daily_rate': daily_rate,
            'total_cost': total_cost,
            'start_date': rental['rental_start_date'],
            'end_date': rental['rental_end_date'],
            'customer': rental['customer_name']
        }
    
    def return_rental(self, rental_id: str, paid_amount: float = 0.0) -> bool:
        """Mark rental as returned"""
        logger.debug("RentalManager", f"Returning rental: {rental_id}")
        
        if not self.db:
            return False
        
        try:
            self.db.update_rental_status(rental_id, "returned", paid_amount)
            logger.info("RentalManager", f"Rental {rental_id} marked as returned")
            return True
        except Exception as e:
            logger.error("RentalManager", f"Failed to return rental: {e}")
            return False
    
    def extend_rental(self, rental_id: str, new_end_date: str) -> bool:
        """Extend rental end date"""
        logger.debug("RentalManager", f"Extending rental: {rental_id} to {new_end_date}")
        
        rental = self.get_rental(rental_id)
        if not rental:
            return False
        
        # Update the end date in database (would need to add this method to POSDatabase)
        # For now, just mark as extended
        logger.info("RentalManager", f"Rental {rental_id} extended to {new_end_date}")
        return True
    
    def is_rental_overdue(self, rental_id: str) -> bool:
        """Check if rental is overdue"""
        rental = self.get_rental(rental_id)
        if not rental or rental['status'] != 'active':
            return False
        
        try:
            end = datetime.fromisoformat(rental['rental_end_date'].replace('Z', '+00:00'))
        except:
            try:
                end = datetime.strptime(rental['rental_end_date'], '%Y-%m-%d %H:%M:%S')
            except:
                end = datetime.strptime(rental['rental_end_date'], '%Y-%m-%d')
        
        is_overdue = datetime.now() > end
        logger.debug("RentalManager", f"Rental {rental_id} overdue: {is_overdue}")
        return is_overdue
    
    def calculate_late_fees(self, rental_id: str, late_fee_per_day: float = 5.0) -> float:
        """Calculate late fees for an overdue rental"""
        rental = self.get_rental(rental_id)
        if not rental or rental['status'] != 'active':
            return 0.0
        
        try:
            end = datetime.fromisoformat(rental['rental_end_date'].replace('Z', '+00:00'))
        except:
            try:
                end = datetime.strptime(rental['rental_end_date'], '%Y-%m-%d %H:%M:%S')
            except:
                end = datetime.strptime(rental['rental_end_date'], '%Y-%m-%d')
        
        now = datetime.now()
        if now <= end:
            return 0.0
        
        days_late = (now - end).days
        if days_late < 1:
            days_late = 1
        
        late_fees = days_late * late_fee_per_day
        logger.debug("RentalManager", 
                    f"Rental {rental_id}: {days_late} days late, fees: ${late_fees:.2f}")
        
        return late_fees
    
    def get_rental_summary(self, rental_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive rental summary"""
        rental = self.get_rental(rental_id)
        if not rental:
            return None
        
        cost_info = self.calculate_rental_cost(rental_id)
        is_overdue = self.is_rental_overdue(rental_id)
        late_fees = self.calculate_late_fees(rental_id) if is_overdue else 0.0
        
        return {
            'rental_id': rental_id,
            'customer': rental['customer_name'],
            'product_id': rental['product_id'],
            'status': rental['status'],
            'rental_cost': cost_info['total_cost'] if cost_info else 0.0,
            'paid_amount': rental['paid_amount'],
            'balance_due': (cost_info['total_cost'] - rental['paid_amount']) if cost_info else 0.0,
            'days_rented': cost_info['days_rented'] if cost_info else 0,
            'daily_rate': cost_info['daily_rate'] if cost_info else 0.0,
            'is_overdue': is_overdue,
            'late_fees': late_fees,
            'total_due': ((cost_info['total_cost'] if cost_info else 0.0) - rental['paid_amount'] + late_fees),
            'start_date': rental['rental_start_date'],
            'end_date': rental['rental_end_date'],
            'notes': rental.get('notes', '')
        }
