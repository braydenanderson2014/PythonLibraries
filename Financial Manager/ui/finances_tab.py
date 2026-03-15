from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ui.financial_tracker import FinancialTracker
from assets.Logger import Logger

logger = Logger()

class FinancesTab(QWidget):
    def __init__(self, current_user_id=None):
        super().__init__()
        logger.debug("FinancesTab", f"Initializing FinancesTab for user {current_user_id}")
        self.current_user_id = current_user_id
        layout = QVBoxLayout()
        
        # Use the new financial tracker
        self.financial_tracker = FinancialTracker(current_user_id)
        layout.addWidget(self.financial_tracker)
        
        self.setLayout(layout)
        logger.info("FinancesTab", f"FinancesTab initialized for user {current_user_id}")
    
    def set_current_user(self, user_id):
        """Set the current user for the finances tab"""
        logger.debug("FinancesTab", f"Setting current user to {user_id}")
        self.current_user_id = user_id
        self.financial_tracker.set_current_user(user_id)
