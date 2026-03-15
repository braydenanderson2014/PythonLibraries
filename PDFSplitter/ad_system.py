# ad_system.py
import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path
from placeholder_ad import setup_placeholder_ads
import random
from PDFUtility.PDFLogger import Logger

class AdSystem:
    def __init__(self, parent):
        self.parent = parent
        self.current_ad = None
        self.rotation_delay = 30000  # 30 seconds in milliseconds
        self.logger = Logger()
        self.logger.info("ADSYSTEM","=================================================================")
        self.logger.info("ADSYSTEM"," EVENT: INIT")
        self.logger.info("ADSYSTEM","=================================================================")
        # Ensure we have placeholder ads
        setup_placeholder_ads()
        
        # Create ad display label
        self.ad_label = tk.Label(self.parent, bg="white")
        self.ad_label.grid(row=1, pady=5, padx=5, sticky="nsew")
        
        # Load and start displaying ads
        self.load_ads()
        self.start_rotation()
    
    def load_ads(self):
        """Load available ads from the ads directory"""
        self.logger.info("ADSYSTEM"," Loading ads...")
        ads_dir = Path(__file__).parent / 'ads'
        self.logger.info(f"ADSYSTEM"," Ads Directory: {ads_dir}")
        self.ads = list(ads_dir.glob('*.png'))
        
        if not self.ads:
            self.logger.info("ADSYSTEM"," Now displaying Placeholder images.")
            self.show_placeholder()
        else:
            self.logger.info("ADSYSTEM"," Now displaying ads ...")
            self.display_ad(self.ads[0])
    
    def show_placeholder(self):
        """Show a placeholder when no ads are available"""
        self.logger.info("ADSYSTEM"," Setting up PlaceHolder Image")
        self.ad_label.configure(
            text="Advertisement Space\n\nContact us to advertise here",
            image="",
            compound="center",
            width=20,
            height=10
        )
    
    def display_ad(self, ad_path):
        """Display an ad image"""
        self.logger.info("ADSYSTEM"," Setting up ad...")
        try:
            image = Image.open(ad_path)
            # Resize image to fit the ad space
            image = image.resize((130, 500), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.ad_label.configure(image=photo)
            self.ad_label.image = photo  # Keep reference
            self.current_ad = ad_path
        except Exception as e:
            self.logger.error(f"ADSYSTEM"," Error displaying ad: {e}")
            self.show_placeholder()
    
    def rotate_ads(self):
        """Rotate through available ads"""
        self.logger.info("ADSYSTEM"," Now Rotating through available ads...")
        if self.ads:
            new_ad = random.choice(self.ads)
            self.display_ad(new_ad)
            self.logger.info("ADSYSTEM"," Ad is now being displayed... at least theoretically")
        
        # Schedule next rotation using tkinter's after()
        self.logger.info("ADSYSTEM"," Scheduled UI Event (rotation)")
        self.parent.after(self.rotation_delay, self.rotate_ads)
    
    def start_rotation(self):
        """Start the ad rotation"""
        self.logger.info("ADSYSTEM"," Starting ad rotation")
        self.parent.after(self.rotation_delay, self.rotate_ads)