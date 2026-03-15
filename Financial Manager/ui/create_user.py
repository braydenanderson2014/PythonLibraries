from PyQt6.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, QGroupBox, QFrame, QSpacerItem, QSizePolicy, QWidget, QToolButton)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Get base path for resources (works with PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.settings import SettingsController
except ImportError:
    from settings import SettingsController  # type: ignore

try:
    from src.account_db import AccountDatabaseManager
except ImportError:
    from account_db import AccountDatabaseManager  # type: ignore

try:
    from src.app_paths import USER_DB
except ImportError:
    from app_paths import USER_DB  # type: ignore

from assets.Logger import Logger
logger = Logger()

account_manager = AccountDatabaseManager()

def user_exists(username):
    logger.debug("create_user", f"Checking if user exists: {username}")
    return account_manager.get_user_by_username(username) is not None

def add_user(username, password):
    logger.debug("create_user", f"Adding new user: {username}")
    account_manager.create_user(username, password)

class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("CreateUserDialog", "Initializing CreateUserDialog")
        # Use the same visual theme as the login dialog and a form layout
        self.setWindowTitle('Create New User')
        self.setFixedSize(520, 680)
        # top-level dialog styling is applied by apply_theme (kept for compatibility)
        self.apply_theme()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                margin: 12px;
                border: 1px solid rgba(0,0,0,0.06);
            }
        """)

        center_widget = QWidget()
        center_layout = QVBoxLayout()
        # leave more room at top for a logo
        center_layout.setContentsMargins(30, 36, 30, 20)
        center_layout.setSpacing(14)

        # Optional top logo (Splash.png)
        splash_label = QLabel()
        splash_path = os.path.join('resources', 'Splash.png')
        if os.path.exists(splash_path):
            try:
                px = QPixmap(splash_path)
                if not px.isNull():
                    px = px.scaledToWidth(112, Qt.TransformationMode.SmoothTransformation)
                    splash_label.setPixmap(px)
                    splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    center_layout.addWidget(splash_label)
            except Exception:
                pass

        title = QLabel('Create a New User Account')
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1e3c72; margin: 6px 0;")
        center_layout.addWidget(title)

        # Credentials frame with QFormLayout
        cred_box = QFrame()
        cred_box.setObjectName('credBox')
        cred_box.setStyleSheet("""
            QFrame#credBox {
                background: rgba(255,255,255,0.98);
                border-radius: 14px;
                border: 1px solid rgba(0,0,0,0.06);
                margin-top: 12px;
            }
        """)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setContentsMargins(24, 18, 24, 18)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)

        # Username
        user_label = QLabel('Username')
        user_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        user_label.setStyleSheet('color: #555555;')
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('Choose a username')
        self.username_edit.setToolTip('Your desired account username')
        self.username_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.username_edit.setStyleSheet('''
            QLineEdit { border: 2px solid #e0e0e0; border-radius: 12px; padding: 10px 12px; background-color: white; color: #333333; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #cccccc; }
        ''')
        form.addRow(user_label, self.username_edit)

        # Password with toggle
        pw_label = QLabel('Password')
        pw_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        pw_label.setStyleSheet('color: #555555;')
        pw_widget = QWidget()
        pw_h = QHBoxLayout(pw_widget)
        pw_h.setContentsMargins(0, 0, 0, 0)
        pw_h.setSpacing(8)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText('Choose a password')
        self.password_edit.setToolTip('Your desired account password')
        self.password_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.password_edit.setStyleSheet('''
            QLineEdit { border: 2px solid transparent; background-color: white; color: #333333; font-size: 14px; padding: 8px 10px; }
        ''')
        self.view_pw_btn = QToolButton()
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
        self.view_pw_btn.setStyleSheet('QToolButton{ background: transparent; border:none; color:#888888;}')
        self.view_pw_btn.toggled.connect(self._toggle_pw_create)
        pw_h.addWidget(self.password_edit)
        pw_h.addWidget(self.view_pw_btn)
        form.addRow(pw_label, pw_widget)

        # Confirm password
        confirm_label = QLabel('Confirm Password')
        confirm_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        confirm_label.setStyleSheet('color: #555555;')
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText('Confirm password')
        self.confirm_edit.setToolTip('Retype your password')
        self.confirm_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.confirm_edit.setStyleSheet('''
            QLineEdit { border: 2px solid #e0e0e0; border-radius: 12px; padding: 10px 12px; background-color: white; color: #333333; font-size: 14px; }
        ''')
        form.addRow(confirm_label, self.confirm_edit)

        # Buttons container
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.setSpacing(8)
        self.create_btn = QPushButton('Create Account')
        self.create_btn.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.setFixedHeight(44)
        self.create_btn.setStyleSheet('''
            QPushButton { border: none; border-radius: 12px; padding: 12px 24px; background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4a90e2, stop:1 #357abd); color: white; font-size: 15px; }
            QPushButton:hover { background-color: #357abd; }
        ''')
        self.create_btn.clicked.connect(self.handle_create)
        btn_layout.addWidget(self.create_btn)

    # cred_box layout will be the card_layout containing the form and buttons
        # Put form and button stack together in a vertical layout inside the card
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 12, 0, 12)
        card_layout.setSpacing(8)
        card_layout.addLayout(form)
        card_layout.addWidget(btn_container)
        cred_box.setLayout(card_layout)

        center_layout.addWidget(cred_box)

        center_widget.setLayout(center_layout)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(center_widget)
        container.setLayout(container_layout)
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        logger.info("CreateUserDialog", "CreateUserDialog initialized")

    def apply_theme(self):
        settings = SettingsController()
        theme = settings.get_theme()
        if theme == 'dark':
            self.setStyleSheet('''
                QDialog { background-color: #181818; color: #f0f0f0; }
                QFrame#credBox { background: rgba(40,40,40,0.97); border-radius: 16px; border: 1px solid #444; }
                QLabel { color: #f0f0f0; }
            ''')
        elif theme == 'light':
            self.setStyleSheet('''
                QDialog { background-color: #f8f8f8; color: #232323; }
                QFrame#credBox { background: #fff; border-radius: 16px; border: 1px solid #ccc; }
                QLabel { color: #232323; }
            ''')
        elif theme == 'blue':
            self.setStyleSheet('''
                QDialog { background-color: #e3f2fd; color: #0d47a1; }
                QFrame#credBox { background: #bbdefb; border-radius: 16px; border: 1px solid #90caf9; }
                QLabel { color: #0d47a1; }
            ''')
        elif theme == 'high-contrast':
            self.setStyleSheet('''
                QDialog { background-color: #000; color: #fff; }
                QFrame#credBox { background: #222; border-radius: 16px; border: 2px solid #fff; }
                QLabel { color: #fff; }
            ''')
        else:
            self.setStyleSheet('')

    def _toggle_pw_create(self, checked):
        logger.debug("CreateUserDialog", f"Toggling password visibility: {checked}")
        # Toggle password echo and swap the icon/text similar to login dialog
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            icon = getattr(self, '_eye_off_icon', None)
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

    def handle_create(self):
        logger.debug("CreateUserDialog", "Attempting to create new user")
        try:
            from src.account_db import AccountDatabaseManager
            from src.account import generate_account_id
        except ImportError:
            from account_db import AccountDatabaseManager  # type: ignore
            from account import generate_account_id  # type: ignore
        account_manager = AccountDatabaseManager()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        if not username or not password:
            logger.warning("CreateUserDialog", "User creation failed: missing username or password")
            QMessageBox.warning(self, 'Error', 'Username and password required.')
            return
        if password != confirm:
            logger.warning("CreateUserDialog", "User creation failed: passwords do not match")
            QMessageBox.warning(self, 'Error', 'Passwords do not match.')
            return
        if account_manager.get_user_by_username(username) is not None:
            logger.warning("CreateUserDialog", f"User creation failed: user already exists: {username}")
            QMessageBox.warning(self, 'Error', 'User already exists.')
            return
        # Generate account ID and create user in database
        account_id = generate_account_id()
        account_manager.create_user(username, password, account_id)
        logger.info("CreateUserDialog", f"User created successfully: {username} (ID: {account_id})")
        QMessageBox.information(self, 'Success', 'User created successfully.')
        self.accept()
