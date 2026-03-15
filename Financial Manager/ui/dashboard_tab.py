from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from assets.Logger import Logger

logger = Logger()

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        logger.debug("DashboardTab", "Initializing DashboardTab")
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Dashboard Overview'))
        self.setLayout(layout)
        logger.info("DashboardTab", "DashboardTab initialized")
