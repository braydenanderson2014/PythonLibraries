from PyQt6.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, QGroupBox, QFrame, QSpacerItem, QSizePolicy, QWidget, QToolButton)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import pyqtSignal, Qt
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from assets.Logger import Logger

logger = Logger()

# Get base path for resources (works with PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.settings import SettingsController
except ImportError:
    from settings import SettingsController  # type: ignore

# Try to use unified account manager (supports both JSON and DB)
try:
    from src.account_unified import get_account_manager
    account_manager = get_account_manager()  # Auto-detects backend
except ImportError:
    # Fallback to legacy JSON-only manager
    try:
        from src.account import AccountManager
        account_manager = AccountManager()
    except ImportError:
        from account import AccountManager  # type: ignore
        account_manager = AccountManager()

try:
    from src.app_paths import USER_DB
except ImportError:
    from app_paths import USER_DB  # type: ignore



def verify_user(username, password):
    return account_manager.verify_password(username, password)

class LoginDialog(QDialog):
    login_success = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("LoginDialog", "Initializing LoginDialog")
        self.setWindowTitle('Financial Manager - Login')
        self.setFixedSize(520, 750)  # Increased width to accommodate larger logo
        # Ensure login dialog always appears on top of other windows
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set initial styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e3c72, stop:0.5 #2a5298, stop:1 #1e3c72);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # Try to set a window icon if available (don't fail if missing)
        try:
            icon_path = os.path.join(BASE_PATH, 'resources', 'icons', 'Rent_Tracker.ico')
            self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        # Create main layout and container for centered content
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                margin: 20px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)

        center_widget = QWidget()
        center_layout = QVBoxLayout()
        # Increase top margin so there's room for a logo above the title
        # Reduce side margins so the credentials area shifts left and appears wider
        center_layout.setContentsMargins(30, 40, 30, 20)
        center_layout.setSpacing(18)

        # Simple branding area (logo, title + subtitle)
        branding_layout = QVBoxLayout()
        branding_layout.setSpacing(8)
        # Optional top logo — if present, show and scale it
        logo_label = QLabel()
        # Use Rent_Tracker.ico from resources
        logo_filename = "Rent_Tracker" + ".ico"
        logo_path = os.path.join(BASE_PATH, 'resources', 'icons', logo_filename)
        if os.path.exists(logo_path):
            try:
                pix = QPixmap(logo_path)
                if not pix.isNull():
                    pix = pix.scaledToWidth(120, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(pix)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    logo_label.setContentsMargins(0, 0, 0, 6)
                    branding_layout.addWidget(logo_label)
            except Exception:
                # ignore image problems and continue without logo
                pass
        title = QLabel('Financial Manager')
        title.setFont(QFont('Segoe UI', 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1e3c72; margin: 6px 0;")
        branding_layout.addWidget(title)
        subtitle = QLabel('Secure Financial Management')
        subtitle.setFont(QFont('Segoe UI', 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet('color: #666666;')
        branding_layout.addWidget(subtitle)
        center_layout.addLayout(branding_layout)

        # Credentials box frame
        cred_box = QFrame()
        cred_box.setObjectName('credBox')
        cred_box.setStyleSheet("""
            QFrame#credBox {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.4);
                margin: 10px 0;
                min-height: 250px;
            }
        """)

        # Use QFormLayout for consistent label/field alignment and to avoid fixed sizes
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setContentsMargins(30, 15, 30, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)

        # Username field
        username_label = QLabel('Username')
        username_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        username_label.setStyleSheet("color: #555555; margin-top: 2px;")

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('Enter your username')
        self.username_edit.setToolTip('Your account username')
        # Let the QFormLayout manage sizing; prefer expanding horizontally
        self.username_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.username_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 10px 12px;
                background-color: white;
                color: #333333;
                font-size: 14px;
                font-weight: 500;
                selection-background-color: #4a90e2;
            }
            QLineEdit:focus {
                border: 2px solid #cccccc;
                background-color: white;
                outline: none;
            }
        """)

        form.addRow(username_label, self.username_edit)

        # Password field with inline view button
        password_label = QLabel('Password')
        password_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        password_label.setStyleSheet("color: #555555; margin-top: 2px;")

        pw_widget = QWidget()
        pw_h = QHBoxLayout(pw_widget)
        pw_h.setContentsMargins(0, 0, 0, 0)
        pw_h.setSpacing(8)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText('Enter your password')
        self.password_edit.setToolTip('Your account password')
        self.password_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid transparent;
                background-color: white;
                color: #333333;
                font-size: 14px;
                padding: 8px 10px;
            }
        """)

        self.view_pw_btn = QToolButton()
        # Prefer icons from resources; fall back to text if icons missing
        eye_path = os.path.join(BASE_PATH, 'resources', 'icons', 'eye.png')
        eye_off_path = os.path.join(BASE_PATH, 'resources', 'icons', 'eye-off.png')
        self._eye_icon = QIcon(eye_path) if os.path.exists(eye_path) else None
        self._eye_off_icon = QIcon(eye_off_path) if os.path.exists(eye_off_path) else None
        if self._eye_icon is not None:
            try:
                self.view_pw_btn.setIcon(self._eye_icon)
            except Exception:
                self.view_pw_btn.setText('••')
        else:
            self.view_pw_btn.setText('••')

        self.view_pw_btn.setCheckable(True)
        self.view_pw_btn.setFixedSize(32, 32)
        self.view_pw_btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
                color: #888888;
            }
            QToolButton:hover { color: #333333; }
            QToolButton:checked { color: #4a90e2; }
        """)
        self.view_pw_btn.setToolTip('Show/Hide Password')
        self.view_pw_btn.toggled.connect(self.toggle_password_visibility)

        pw_h.addWidget(self.password_edit)
        pw_h.addWidget(self.view_pw_btn)

        form.addRow(password_label, pw_widget)
        # Buttons area below the form
        btn_container = QWidget()
        btn_container_layout = QVBoxLayout(btn_container)
        btn_container_layout.setContentsMargins(0, 10, 0, 0)
        btn_container_layout.setSpacing(12)

        # Primary login button
        self.login_btn = QPushButton('Sign In')
        self.login_btn.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.login_btn.setFixedHeight(48)
        self.login_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a90e2, stop:1 #357abd);
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #357abd, stop:1 #2e5d8f);
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2e5d8f, stop:1 #1e3c72);
            }
        """)
        btn_container_layout.addWidget(self.login_btn)

        # Secondary create account button
        self.create_user_btn = QPushButton('Create New Account')
        self.create_user_btn.setFont(QFont('Segoe UI', 12))
        self.create_user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_user_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.create_user_btn.setFixedHeight(44)
        self.create_user_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #4a90e2;
                border-radius: 12px;
                padding: 12px 25px;
                background-color: transparent;
                color: #4a90e2;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 226, 0.1);
                border: 2px solid #357abd;
                color: #357abd;
            }
            QPushButton:pressed {
                background-color: rgba(74, 144, 226, 0.2);
                border: 2px solid #2e5d8f;
                color: #2e5d8f;
            }
        """)
        btn_container_layout.addWidget(self.create_user_btn)

        # Connect button events
        self.login_btn.clicked.connect(self.handle_login)
        self.create_user_btn.clicked.connect(self.handle_create_user)

        # Connect Enter key to login
        self.username_edit.returnPressed.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)

    # Place the form and buttons inside the credentials frame
        creds_outer_layout = QVBoxLayout()
        # Left-align and reduce horizontal padding so fields appear longer
        creds_outer_layout.setContentsMargins(10, 6, 10, 12)
        creds_outer_layout.setSpacing(12)
        creds_outer_layout.addLayout(form)
        creds_outer_layout.addWidget(btn_container)

        cred_box.setLayout(creds_outer_layout)
        center_layout.addWidget(cred_box)
        # Footer with version info
        footer = QLabel('Financial Manager v1.0 • Secure & Reliable')
        footer.setFont(QFont('Segoe UI', 9))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Make footer less tall and use lighter spacing
        footer.setFixedHeight(20)
        footer.setStyleSheet("""
            QLabel {
                color: #888888;
                margin-top: 6px;
                padding: 4px 6px;
                background: transparent;
            }
        """)
        center_layout.addWidget(footer)
        
        center_widget.setLayout(center_layout)
        
        container_layout = QVBoxLayout()
        container_layout.addWidget(center_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(container_layout)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        
        # Set focus to username field for better UX
        self.username_edit.setFocus()

    def apply_theme(self):
        """Apply modern theme with gradient background and glassmorphism effects"""
        # The modern styling is now integrated into the UI components
        # This method is kept for compatibility but styling is handled in __init__
        pass

    def handle_login(self):
        """Handle login with support for both database and JSON accounts"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        account_id = None
        
        if not username or not password:
            QMessageBox.warning(self, 'Login Failed', 'Please enter username and password.')
            return
        
        # Try to authenticate from database first, then JSON
        try:
            from src.account_db import AccountDatabaseManager
            from src.account import AccountManager
        except ImportError:
            from account_db import AccountDatabaseManager  # type: ignore
            from account import AccountManager  # type: ignore
        
        # Step 1: Try database authentication
        logger.debug("LoginDialog", f"Attempting login for {username} - checking database first")
        db_manager = AccountDatabaseManager()
        db_user = db_manager.get_user_by_username(username)
        
        if db_user:
            # User found in database - verify password
            if db_manager.verify_password(username, password):
                logger.info("LoginDialog", f"User {username} authenticated via DATABASE")
                # Update last login timestamp
                db_manager.update_last_login(username)
                # Convert id to string to match signal type (expects str)
                account_id = str(db_user.get('id', ''))
                self.login_success.emit(account_id)
                self.accept()
                return
            else:
                logger.warning("LoginDialog", f"Password verification failed for {username} in database")
                QMessageBox.warning(self, 'Login Failed', 'Invalid username or password.')
                return
        
        # Step 2: Try JSON authentication (for backward compatibility)
        logger.debug("LoginDialog", f"User {username} not in database, checking JSON")
        json_manager = AccountManager()
        json_manager.load()
        
        if username in json_manager.accounts:
            # User found in JSON - verify password
            if json_manager.verify_password(username, password):
                logger.info("LoginDialog", f"User {username} authenticated via JSON, initiating migration")
                account = json_manager.get_account(username)
                account_id = account['account_id'] if account else None
                
                # Attempt automatic migration from JSON to database
                try:
                    from src.account_migration import auto_migrate_on_login
                    logger.debug("LoginDialog", f"Initiating auto-migration for user: {username}")
                    auto_migrate_on_login(username)
                    # After migration, update last_login in database
                    db_manager.update_last_login(username)
                except ImportError:
                    logger.debug("LoginDialog", "Account migration module not available")
                except Exception as e:
                    logger.warning("LoginDialog", f"Auto-migration failed (non-blocking): {e}")
                
                self.login_success.emit(account_id)
                self.accept()
                return
            else:
                logger.warning("LoginDialog", f"Password verification failed for {username} in JSON")
                QMessageBox.warning(self, 'Login Failed', 'Invalid username or password.')
                return
        
        # Step 3: User not found in either backend
        logger.warning("LoginDialog", f"User {username} not found in database or JSON")
        QMessageBox.warning(self, 'Login Failed', 'Invalid username or password.')

    def handle_create_user(self):
        from ui.create_user import CreateUserDialog
        dlg = CreateUserDialog(self)
        dlg.exec()
        account_manager.load()  # Reload accounts after user creation

    @staticmethod
    def validate_password(username, parent=None):
        # Re-authenticate for critical actions
        dlg = LoginDialog(parent)
        dlg.username_edit.setText(username)
        dlg.username_edit.setDisabled(True)
        if dlg.exec() == 1:
            return True
        return False

    def toggle_password_visibility(self, checked):
        # Toggle password echo mode and swap icon/text accordingly
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            icon = getattr(self, '_eye_off_icon', None)
            # show the 'eye-off' icon when password is visible
            if icon is not None:
                try:
                    self.view_pw_btn.setIcon(icon)
                    self.view_pw_btn.setText('')
                except Exception:
                    self.view_pw_btn.setIcon(QIcon())
                    self.view_pw_btn.setText('Ab')
            else:
                self.view_pw_btn.setIcon(QIcon())
                self.view_pw_btn.setText('Ab')
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            icon = getattr(self, '_eye_icon', None)
            if icon is not None:
                try:
                    self.view_pw_btn.setIcon(icon)
                    self.view_pw_btn.setText('')
                except Exception:
                    self.view_pw_btn.setIcon(QIcon())
                    self.view_pw_btn.setText('••')
            else:
                self.view_pw_btn.setIcon(QIcon())
                self.view_pw_btn.setText('••')
