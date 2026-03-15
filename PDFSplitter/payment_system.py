# payment_system.py
import os
import json
import stripe
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import platform
from datetime import datetime
from PDFUtility.PDFLogger import Logger

class PaymentSystem:
    def __init__(self):
        # Initialize Stripe with your test key
        self.logger = Logger()
        self.logger.info("PAYMENT","=================================================================")
        self.logger.info("PAYMENT"," EVENT: INIT")
        self.logger.info("PAYMENT","=================================================================")
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.public_key = os.getenv('STRIPE_PUBLIC_KEY')
        self.price_id = os.getenv('STRIPE_PRICE_ID')
        self.setup_storage()

    def setup_storage(self):
        """Set up storage directory based on platform"""
        if platform.system() == "Windows":
            base_dir = os.path.join(os.getenv('APPDATA'), 'PDFUtility')
        elif platform.system() == "Darwin":  # macOS
            base_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'PDFUtility')
        else:  # Linux and others
            base_dir = os.path.join(os.path.expanduser('~'), '.pdfutility')
        self.logger.info(f"PAYMENT"," Storage base dir {base_dir}")

        # Create directory if it doesn't exist
        self.data_dir = Path(base_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up paths
        self.purchase_file = self.data_dir / 'purchase_status.json'
        self.logger.info("PAYMENT", f"Ensuring payment status file is set up: {self.purchase_file}")
        self.load_purchase_status()

    def load_purchase_status(self):
        """Load purchase status from file"""
        self.logger.info("PAYMENT"," Loading Purchase Status")
        try:
            if self.purchase_file.exists():
                with open(self.purchase_file, 'r') as f:
                    self.logger.debug("PAYMENT"," Loading purchase file.")
                    self.purchase_status = json.load(f)
                    self.logger.debug("PAYMENT"," Purchase status {self.purchase_status}")
            else:
                self.purchase_status = {'ads_removed': False}
                self.logger.debug("PAYMENT"," Ads Removed false")
                self.save_purchase_status()
        except Exception as e:
            self.logger.error("PAYMENT", f"Error loading purchase status: {e}")
            self.purchase_status = {'ads_removed': False}

    def save_purchase_status(self):
        """Save purchase status to file"""
        self.logger.info("PAYMENT"," Saving Purchase Status")
        try:
            with open(self.purchase_file, 'w') as f:
                json.dump(self.purchase_status, f)
            self.logger.info("PAYMENT"," Purchase Status Saved")
        except Exception as e:
            self.logger.error("PAYMENT", f"Error saving purchase status: {e}")
            messagebox.showerror("PAYMENT", "Could not save purchase status")

    def create_checkout_session(self):
        """Create Stripe checkout session"""
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': self.price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://localhost:5000/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:5000/cancel',
            )
            return checkout_session
        except Exception as e:
            self.logger.exception("PAYMENT",f"Error creating checkout session: {e}")
            return None

    def process_success(self, session_id):
        """Process successful payment"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                self.purchase_status['ads_removed'] = True
                self.purchase_status['purchase_date'] = datetime.now().isoformat()
                self.purchase_status['session_id'] = session_id
                self.save_purchase_status()
                return True
        except Exception as e:
            self.logger.exception("PAYMENT", f"Error processing success: {e}")
        return False

    def has_removed_ads(self):
        """Check if ads have been removed"""
        return self.purchase_status.get('ads_removed', False)

    def show_purchase_dialog(self, parent):
        """Show purchase dialog with Stripe checkout"""
        dialog = tk.Toplevel(parent)
        dialog.title("Remove Ads")
        dialog.geometry("400x250")
        dialog.transient(parent)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')

        # Add content
        tk.Label(
            dialog,
            text="Remove Ads Forever",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        tk.Label(
            dialog,
            text="Enjoy an ad-free experience for just $4.99",
            font=("Arial", 12)
        ).pack(pady=10)

        tk.Button(
            dialog,
            text="Purchase Now",
            command=lambda: self.handle_purchase(dialog),
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        ).pack(pady=20)

        tk.Button(
            dialog,
            text="Cancel",
            command=dialog.destroy,
            font=("Arial", 10)
        ).pack(pady=5)

    def handle_purchase(self, dialog):
        """Handle the purchase process"""
        session = self.create_checkout_session()
        if session:
            dialog.destroy()
            webbrowser.open(session.url)
            # You would need to implement a way to handle the success callback
            # This could be through a local server or by having users manually
            # enter their confirmation code
        else:
            messagebox.showerror(
                "Error",
                "Could not initiate checkout. Please try again later."
            )