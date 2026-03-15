# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google AdSense Configuration
ADSENSE_CLIENT = os.getenv('GOOGLE_ADSENSE_CLIENT')
ADSENSE_SLOT = os.getenv('GOOGLE_ADSENSE_SLOT')

# Application Configuration
APP_NAME = "PDF Utility"
DEFAULT_WINDOW_SIZE = "1200x700"
MIN_WINDOW_SIZE = (1000, 600)

# Ad Section Configuration
AD_WIDTH = 150  # pixels
AD_HEIGHT = 600  # pixels

# Check if required environment variables are set
def validate_config():
    missing_vars = []
    if not ADSENSE_CLIENT:
        missing_vars.append('GOOGLE_ADSENSE_CLIENT')
    if not ADSENSE_SLOT:
        missing_vars.append('GOOGLE_ADSENSE_SLOT')
    
    if missing_vars:
        print("Warning: Missing environment variables:", ", ".join(missing_vars))
        print("Ads will be disabled.")
        return False
    return True