from PyQt6.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QGroupBox, QFrame, QSpacerItem, QSizePolicy, QWidget)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from src.app_paths import USER_DB
from src.settings import SettingsController
from assets.hasher import hash_password
from assets.Logger import Logger
logger = Logger()


def verify_user(username, password):
    logger.debug("change_pass", f"Verifying user: {username}")
    if not os.path.exists(USER_DB):
        logger.warning("change_pass", "User database not found")
        return False
    with open(USER_DB, 'r') as f:
        for line in f:
            u, p = line.strip().split(':')
            if u == username and p == hash_password(password):
                logger.info("change_pass", f"User verified: {username}")
                return True
    logger.warning("change_pass", f"User verification failed: {username}")
    return False

def update_password(username, new_password):
    logger.debug("change_pass", f"Updating password for user: {username}")
    if not os.path.exists(USER_DB):
        logger.error("change_pass", "User database not found")
        return False
    lines = []
    with open(USER_DB, 'r') as f:
        for line in f:
            u, p = line.strip().split(':')
            if u == username:
                lines.append(f'{u}:{hash_password(new_password)}\n')
            else:
                lines.append(line)
    with open(USER_DB, 'w') as f:
        f.writelines(lines)
    logger.info("change_pass", f"Password updated for user: {username}")
    return True

class ChangePasswordDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        logger.debug("ChangePasswordDialog", f"Initializing ChangePasswordDialog for user {username}")
        self.username = username
        self.setWindowTitle('Change Password')
        self.setMinimumWidth(420)
        self.setMinimumHeight(520)
        self.apply_theme()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(24)
        # Title
        title = QLabel(f'Change password for {username}')
        title.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)
        # Credentials box
        cred_box = QFrame()
        cred_box.setObjectName('credBox')
        cred_box.setStyleSheet('''
            QFrame#credBox {
                background: rgba(40,40,40,0.97);
                border-radius: 16px;
                border: 1px solid #444;
                margin-top: 24px;
            }
        ''')
        cred_layout = QVBoxLayout()
        cred_layout.setContentsMargins(24, 24, 24, 24)
        cred_layout.setSpacing(18)
        cred_label = QLabel('Change Password')
        cred_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        cred_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cred_label.setStyleSheet('color: #bbb;')
        cred_layout.addWidget(cred_label)
        self.current_edit = QLineEdit()
        self.current_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_edit.setPlaceholderText('Current Password')
        self.current_edit.setStyleSheet('border-radius: 8px; padding: 12px; background: #222; color: #f0f0f0; font-size: 15px;')
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_edit.setPlaceholderText('New Password')
        self.new_edit.setStyleSheet('border-radius: 8px; padding: 12px; background: #222; color: #f0f0f0; font-size: 15px;')
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText('Confirm New Password')
        self.confirm_edit.setStyleSheet('border-radius: 8px; padding: 12px; background: #222; color: #f0f0f0; font-size: 15px;')
        cred_layout.addWidget(self.current_edit)
        cred_layout.addWidget(self.new_edit)
        cred_layout.addWidget(self.confirm_edit)
        cred_box.setLayout(cred_layout)
        center_layout.addWidget(cred_box)
        # Button
        self.change_btn = QPushButton('Change Password')
        self.change_btn.setStyleSheet('font-weight: bold; border-radius: 8px; padding: 12px 32px; background: #0078d4; color: #fff; font-size: 15px;')
        self.change_btn.clicked.connect(self.handle_change)
        center_layout.addWidget(self.change_btn)
        center_widget.setLayout(center_layout)
        layout.addStretch()
        layout.addWidget(center_widget)
        layout.addStretch()
        self.setLayout(layout)

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


    def handle_change(self):
        logger.debug("ChangePasswordDialog", f"Attempting password change for {self.username}")
        current = self.current_edit.text()
        new = self.new_edit.text()
        confirm = self.confirm_edit.text()
        if not verify_user(self.username, current):
            logger.warning("ChangePasswordDialog", f"Password change failed: invalid current password")
            QMessageBox.warning(self, 'Error', 'Current password is incorrect.')
            return
        if not new:
            logger.warning("ChangePasswordDialog", "Password change failed: new password empty")
            QMessageBox.warning(self, 'Error', 'New password cannot be empty.')
            return
        if new != confirm:
            logger.warning("ChangePasswordDialog", "Password change failed: passwords do not match")
            QMessageBox.warning(self, 'Error', 'New passwords do not match.')
            return
        update_password(self.username, new)
        logger.info("ChangePasswordDialog", f"Password changed successfully for {self.username}")
        QMessageBox.information(self, 'Success', 'Password changed successfully.')
        self.accept()
