#!/usr/bin/env python3
"""
Issue Reporting System for PDF Utility
Allows users to report bugs and request features via GitHub API
Supports private repositories while showing public issue status
"""

import os
import sys
import json
import requests
import base64
from datetime import datetime
from github_app_auth import get_github_app_auth, is_github_app_configured
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QCheckBox, QProgressBar,
    QMessageBox, QTabWidget, QWidget, QFormLayout, QScrollArea,
    QGroupBox, QFileDialog, QListWidget, QListWidgetItem,
    QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import content filter
try:
    from content_filter import validate_issue_content, record_successful_submission
except ImportError:
    # Fallback if content filter is not available
    def validate_issue_content(title, description, user_id="default"):
        return True, []
    def record_successful_submission(user_id="default"):
        pass

class IssueReporter(QThread):
    """Background thread to submit issues to GitHub"""
    issue_submitted = pyqtSignal(dict)  # Issue data
    submission_failed = pyqtSignal(str)  # Error message
    upload_progress = pyqtSignal(int)  # Progress percentage
    
    def __init__(self, issue_data, log_files=None):
        super().__init__()
        self.issue_data = issue_data
        self.log_files = log_files or []
        
        # Authentication priority: GitHub App > Bot Token > Personal Token
        self.github_app_auth = get_github_app_auth()
        self.github_bot_token = os.getenv('GITHUB_BOT_TOKEN', '')
        self.github_bot_username = os.getenv('GITHUB_BOT_USERNAME', 'pdf-utility-bot')
        
        self.github_owner = os.getenv('GITHUB_OWNER', '')
        self.github_repo = os.getenv('GITHUB_REPO', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.issues_url = os.getenv('ISSUES_API_URL', '').format(
            owner=self.github_owner, 
            repo=self.github_repo
        )
        
        # Determine authentication method and credentials
        if self.github_app_auth and self.github_app_auth.is_configured():
            self.auth_method = "github_app"
            self.auth_headers = self.github_app_auth.get_authenticated_headers()
        elif self.github_bot_token:
            self.auth_method = "bot_token"
            self.auth_headers = {
                'Authorization': f'token {self.github_bot_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Bot/1.0'
            }
        elif self.github_token:
            self.auth_method = "personal_token"
            self.auth_headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Reporter/1.0'
            }
        else:
            self.auth_method = None
            self.auth_headers = None
    
    def run(self):
        """Submit issue to GitHub"""
        try:
            if not all([self.github_owner, self.github_repo]):
                missing_items = []
                if not self.github_owner: missing_items.append("GITHUB_OWNER")
                if not self.github_repo: missing_items.append("GITHUB_REPO")
                self.submission_failed.emit(f"GitHub configuration incomplete: Missing {', '.join(missing_items)}")
                return
            
            if not self.auth_headers:
                self.submission_failed.emit("No valid authentication method available. Please configure GitHub App, bot token, or personal token.")
                return
            
            # Add Content-Type to headers
            headers = self.auth_headers.copy()
            headers['Content-Type'] = 'application/json'
            
            # Prepare issue body with logs included as text and attribution
            self.upload_progress.emit(20)
            issue_body = self._prepare_issue_body()
            self.upload_progress.emit(50)
            
            # Prepare issue data
            issue_payload = {
                'title': self.issue_data['title'],
                'body': issue_body,
                'labels': self.issue_data['labels']
            }
            
            self.upload_progress.emit(80)
            
            # Submit issue
            response = requests.post(self.issues_url, headers=headers, json=issue_payload, timeout=30)
            response.raise_for_status()
            
            issue_info = response.json()
            self.upload_progress.emit(100)
            
            # Determine submission attribution
            auth_info = self._get_auth_attribution()
            
            result = {
                'number': issue_info['number'],
                'url': issue_info['html_url'],
                'title': issue_info['title'],
                'auth_method': self.auth_method,
                'submitted_by': auth_info['submitted_by'],
                'auth_description': auth_info['description']
            }
            
            self.issue_submitted.emit(result)
            
        except requests.exceptions.RequestException as e:
            self.submission_failed.emit(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            self.submission_failed.emit(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.submission_failed.emit(f"Unexpected error: {str(e)}")

    def _prepare_issue_body(self):
        """Prepare the issue body with all details and embedded log files"""
        body_parts = []
        
        # Issue description
        body_parts.append("## Description")
        body_parts.append(self.issue_data['description'])
        body_parts.append("")
        
        # Steps to reproduce (for bugs)
        if 'steps' in self.issue_data and self.issue_data['steps']:
            body_parts.append("## Steps to Reproduce")
            body_parts.append(self.issue_data['steps'])
            body_parts.append("")
        
        # Expected vs Actual behavior (for bugs)
        if 'expected' in self.issue_data and self.issue_data['expected']:
            body_parts.append("## Expected Behavior")
            body_parts.append(self.issue_data['expected'])
            body_parts.append("")
        
        if 'actual' in self.issue_data and self.issue_data['actual']:
            body_parts.append("## Actual Behavior")
            body_parts.append(self.issue_data['actual'])
            body_parts.append("")
        
        # System information
        body_parts.append("## System Information")
        body_parts.append(f"- **Application Version**: {os.getenv('CURRENT_VERSION', 'Unknown')}")
        body_parts.append(f"- **Operating System**: {sys.platform}")
        body_parts.append(f"- **Python Version**: {sys.version.split()[0]}")
        body_parts.append(f"- **Submitted**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        body_parts.append("")
        
        # Include log files as text if provided
        if self.log_files:
            body_parts.append("## Log Files")
            for log_file in self.log_files:
                if not os.path.exists(log_file):
                    continue
                    
                # Check file size (limit to 10KB per log for readability)
                max_size_kb = 10
                if os.path.getsize(log_file) > max_size_kb * 1024:
                    body_parts.append(f"### {os.path.basename(log_file)} (truncated - file too large)")
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            # Read last 5KB of the file
                            f.seek(-max_size_kb * 1024, 2)
                            content = f.read()
                    except Exception:
                        content = "Unable to read log file"
                else:
                    body_parts.append(f"### {os.path.basename(log_file)}")
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception:
                        content = "Unable to read log file"
                
                body_parts.append("```")
                body_parts.append(content.strip())
                body_parts.append("```")
                body_parts.append("")
            
        # Footer
        body_parts.append("---")
        auth_info = self._get_auth_attribution()
        body_parts.append(f"🤖 *{auth_info['footer']}*")
        
        return "\n".join(body_parts)
    
    def _get_auth_attribution(self):
        """Get authentication attribution information"""
        if self.auth_method == "github_app":
            return {
                'submitted_by': 'GitHub App',
                'description': 'PDF Utility Issue Bot (GitHub App)',
                'footer': 'This issue was automatically submitted by PDF Utility Issue Bot (GitHub App) on behalf of a user'
            }
        elif self.auth_method == "bot_token":
            return {
                'submitted_by': f'Bot ({self.github_bot_username})',
                'description': f'Bot Account: {self.github_bot_username}',
                'footer': f'This issue was automatically submitted by {self.github_bot_username} on behalf of a PDF Utility user'
            }
        elif self.auth_method == "personal_token":
            return {
                'submitted_by': 'Personal Token',
                'description': 'Personal Access Token',
                'footer': 'This issue was submitted via the in-app reporting system using personal access token'
            }
        else:
            return {
                'submitted_by': 'Unknown',
                'description': 'Unknown authentication method',
                'footer': 'This issue was submitted via the in-app reporting system'
            }

class IssueListLoader(QThread):
    """Background thread to load existing issues from GitHub"""
    issues_loaded = pyqtSignal(list)  # List of issues
    load_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, issue_type="all"):
        super().__init__()
        self.issue_type = issue_type  # "all", "bugs", "features"
        
        # Use the same authentication priority as IssueReporter
        self.github_app_auth = get_github_app_auth()
        
        self.github_owner = os.getenv('GITHUB_OWNER', '')
        self.github_repo = os.getenv('GITHUB_REPO', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.github_bot_token = os.getenv('GITHUB_BOT_TOKEN', '')
        self.issues_url = os.getenv('ISSUES_API_URL', '').format(
            owner=self.github_owner, 
            repo=self.github_repo
        )
        
        # Determine authentication headers
        if self.github_app_auth and self.github_app_auth.is_configured():
            self.auth_headers = self.github_app_auth.get_authenticated_headers()
        elif self.github_bot_token:
            self.auth_headers = {
                'Authorization': f'token {self.github_bot_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Bot/1.0'
            }
        elif self.github_token:
            self.auth_headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Reporter/1.0'
            }
        else:
            self.auth_headers = None
    
    def run(self):
        """Load issues from GitHub"""
        try:
            if not all([self.github_owner, self.github_repo]):
                self.load_failed.emit("GitHub configuration incomplete")
                return
            
            if not self.auth_headers:
                self.load_failed.emit("No valid authentication method available")
                return
            
            # Parameters for GitHub API
            params = {
                'state': 'all',  # Get both open and closed issues
                'sort': 'updated',
                'direction': 'desc',
                'per_page': 100
            }
            
            # Add label filtering based on type
            if self.issue_type == "bugs":
                params['labels'] = 'bug'
            elif self.issue_type == "features":
                params['labels'] = 'enhancement'
            
            response = requests.get(self.issues_url, headers=self.auth_headers, params=params, timeout=15)
            response.raise_for_status()
            
            issues = response.json()
            
            # Filter and format issues
            formatted_issues = []
            for issue in issues:
                formatted_issue = {
                    'number': issue['number'],
                    'title': issue['title'],
                    'state': issue['state'],
                    'labels': [label['name'] for label in issue['labels']],
                    'created_at': issue['created_at'],
                    'updated_at': issue['updated_at'],
                    'url': issue['html_url'],
                    'body': issue['body'][:200] + '...' if len(issue['body']) > 200 else issue['body']
                }
                formatted_issues.append(formatted_issue)
            
            self.issues_loaded.emit(formatted_issues)
            
        except requests.exceptions.RequestException as e:
            self.load_failed.emit(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            self.load_failed.emit(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.load_failed.emit(f"Unexpected error: {str(e)}")

class IssueDetailsLoader(QThread):
    """Background thread to load detailed issue information including comments"""
    details_loaded = pyqtSignal(dict)  # Issue details with comments
    load_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, issue_number):
        super().__init__()
        self.issue_number = issue_number
        
        # Use the same authentication priority as other classes
        self.github_app_auth = get_github_app_auth()
        
        self.github_owner = os.getenv('GITHUB_OWNER', '')
        self.github_repo = os.getenv('GITHUB_REPO', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.github_bot_token = os.getenv('GITHUB_BOT_TOKEN', '')
        self.issue_url = os.getenv('ISSUES_API_URL', '').format(
            owner=self.github_owner, 
            repo=self.github_repo
        ) + f'/{issue_number}'
        self.comments_url = self.issue_url + '/comments'
        
        # Determine authentication headers
        if self.github_app_auth and self.github_app_auth.is_configured():
            self.auth_headers = self.github_app_auth.get_authenticated_headers()
        elif self.github_bot_token:
            self.auth_headers = {
                'Authorization': f'token {self.github_bot_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Bot/1.0'
            }
        elif self.github_token:
            self.auth_headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Reporter/1.0'
            }
        else:
            self.auth_headers = None
    
    def run(self):
        """Load issue details and comments from GitHub"""
        try:
            if not all([self.github_owner, self.github_repo]):
                self.load_failed.emit("GitHub configuration incomplete")
                return
            
            if not self.auth_headers:
                self.load_failed.emit("No valid authentication method available")
                return
            
            # Load issue details
            issue_response = requests.get(self.issue_url, headers=self.auth_headers, timeout=15)
            issue_response.raise_for_status()
            issue_data = issue_response.json()
            
            # Load comments
            comments_response = requests.get(self.comments_url, headers=self.auth_headers, timeout=15)
            comments_response.raise_for_status()
            comments_data = comments_response.json()
            
            # Format the detailed information
            details = {
                'issue': {
                    'number': issue_data['number'],
                    'title': issue_data['title'],
                    'state': issue_data['state'],
                    'labels': [{'name': label['name'], 'color': label['color']} for label in issue_data['labels']],
                    'created_at': issue_data['created_at'],
                    'updated_at': issue_data['updated_at'],
                    'closed_at': issue_data.get('closed_at'),
                    'url': issue_data['html_url'],
                    'body': issue_data['body'],
                    'user': issue_data['user']['login'],
                    'assignees': [assignee['login'] for assignee in issue_data.get('assignees', [])],
                    'milestone': issue_data.get('milestone', {}).get('title') if issue_data.get('milestone') else None
                },
                'comments': []
            }
            
            # Format comments
            for comment in comments_data:
                comment_info = {
                    'id': comment['id'],
                    'user': comment['user']['login'],
                    'body': comment['body'],
                    'created_at': comment['created_at'],
                    'updated_at': comment['updated_at'],
                    'url': comment['html_url']
                }
                details['comments'].append(comment_info)
            
            self.details_loaded.emit(details)
            
        except requests.exceptions.RequestException as e:
            self.load_failed.emit(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            self.load_failed.emit(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.load_failed.emit(f"Unexpected error: {str(e)}")

class IssueStatusWidget(QWidget):
    """Widget to display detailed issue status with comments and labels"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_issue = None
        self.is_repo_public = None  # Cache repository visibility
        self.setup_ui()
    
    def check_repository_visibility(self):
        """Check if the repository is public or private"""
        if self.is_repo_public is not None:
            return self.is_repo_public  # Return cached result
        
        try:
            github_owner = os.getenv('GITHUB_OWNER', '')
            github_repo = os.getenv('GITHUB_REPO', '')
            
            if not all([github_owner, github_repo]):
                self.is_repo_public = False  # Default to private if config missing
                return self.is_repo_public
            
            # Use the same authentication priority as other components
            github_app_auth = get_github_app_auth()
            
            if github_app_auth and github_app_auth.is_configured():
                headers = github_app_auth.get_authenticated_headers()
            else:
                github_token = os.getenv('GITHUB_TOKEN', '') or os.getenv('GITHUB_BOT_TOKEN', '')
                if not github_token:
                    self.is_repo_public = False  # Default to private if no auth
                    return self.is_repo_public
                
                headers = {
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                }
            
            repo_url = f"https://api.github.com/repos/{github_owner}/{github_repo}"
            response = requests.get(repo_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                repo_data = response.json()
                self.is_repo_public = not repo_data.get('private', True)  # GitHub returns private: true/false
            else:
                self.is_repo_public = False  # Default to private if API call fails
                
        except Exception as e:
            print(f"Warning: Could not determine repository visibility: {e}")
            self.is_repo_public = False  # Default to private if there's an error
        
        return self.is_repo_public
    
    def setup_ui(self):
        """Setup the detailed status UI"""
        layout = QVBoxLayout(self)
        
        # Header with issue info
        self.header_label = QLabel("Select an issue to view detailed status")
        self.header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        
        # Issue details scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        scroll.setWidget(self.details_widget)
        
        layout.addWidget(scroll)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.refresh_btn.setEnabled(False)
        layout.addWidget(self.refresh_btn)
    
    def display_issue_status(self, issue_number):
        """Load and display detailed status for an issue"""
        self.current_issue = issue_number
        self.refresh_btn.setEnabled(True)
        self.header_label.setText(f"Loading detailed status for issue #{issue_number}...")
        
        # Clear existing details
        self.clear_details()
        
        # Start loading details
        self.details_loader = IssueDetailsLoader(issue_number)
        self.details_loader.details_loaded.connect(self.on_details_loaded)
        self.details_loader.load_failed.connect(self.on_details_failed)
        self.details_loader.start()
    
    def refresh_status(self):
        """Refresh the current issue status"""
        if self.current_issue:
            self.display_issue_status(self.current_issue)
    
    def clear_details(self):
        """Clear the details display"""
        # Remove all widgets from details layout
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def on_details_loaded(self, details):
        """Display the loaded issue details"""
        issue = details['issue']
        comments = details['comments']
        
        # Update header
        status_icon = "🟢 OPEN" if issue['state'] == 'open' else "🔴 CLOSED"
        self.header_label.setText(f"{status_icon} Issue #{issue['number']}: {issue['title']}")
        
        # Issue metadata group
        metadata_group = QGroupBox("Issue Information")
        metadata_layout = QFormLayout(metadata_group)
        
        # State and labels
        labels_text = self.format_labels(issue['labels'])
        metadata_layout.addRow("Status:", QLabel(f"{issue['state'].upper()} {status_icon}"))
        metadata_layout.addRow("Labels:", QLabel(labels_text))
        metadata_layout.addRow("Created:", QLabel(self.format_datetime(issue['created_at'])))
        metadata_layout.addRow("Updated:", QLabel(self.format_datetime(issue['updated_at'])))
        
        if issue['closed_at']:
            metadata_layout.addRow("Closed:", QLabel(self.format_datetime(issue['closed_at'])))
        
        metadata_layout.addRow("Reporter:", QLabel(issue['user']))
        
        if issue['assignees']:
            metadata_layout.addRow("Assignees:", QLabel(", ".join(issue['assignees'])))
        
        if issue['milestone']:
            metadata_layout.addRow("Milestone:", QLabel(issue['milestone']))
        
        # Only show URL for public repositories
        if self.check_repository_visibility():
            metadata_layout.addRow("URL:", self.create_link_label(issue['url']))
        
        self.details_layout.addWidget(metadata_group)
        
        # Issue description
        if issue['body']:
            desc_group = QGroupBox("Description")
            desc_layout = QVBoxLayout(desc_group)
            
            desc_text = QTextEdit()
            desc_text.setPlainText(issue['body'])
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(200)
            desc_layout.addWidget(desc_text)
            
            self.details_layout.addWidget(desc_group)
        
        # Comments section
        if comments:
            comments_group = QGroupBox(f"Comments ({len(comments)})")
            comments_layout = QVBoxLayout(comments_group)
            
            for i, comment in enumerate(comments):
                comment_frame = QGroupBox(f"Comment by {comment['user']} - {self.format_datetime(comment['created_at'])}")
                comment_layout = QVBoxLayout(comment_frame)
                
                comment_text = QTextEdit()
                comment_text.setPlainText(comment['body'])
                comment_text.setReadOnly(True)
                comment_text.setMaximumHeight(150)
                comment_layout.addWidget(comment_text)
                
                # Comment metadata
                if comment['updated_at'] != comment['created_at']:
                    updated_label = QLabel(f"Last updated: {self.format_datetime(comment['updated_at'])}")
                    updated_label.setStyleSheet("color: gray; font-style: italic;")
                    comment_layout.addWidget(updated_label)
                
                comments_layout.addWidget(comment_frame)
                
                # Add separator between comments (except last)
                if i < len(comments) - 1:
                    separator = QLabel("─" * 50)
                    separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    separator.setStyleSheet("color: lightgray;")
                    comments_layout.addWidget(separator)
            
            self.details_layout.addWidget(comments_group)
        else:
            no_comments_group = QGroupBox("Comments")
            no_comments_layout = QVBoxLayout(no_comments_group)
            no_comments_layout.addWidget(QLabel("No comments yet."))
            self.details_layout.addWidget(no_comments_group)
        
        # Status summary at the bottom
        summary_group = QGroupBox("Status Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        summary_text = self.generate_status_summary(issue, comments)
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        # Use theme-aware styling for better readability in all themes
        summary_label.setStyleSheet("""
            background-color: palette(base);
            color: palette(text);
            padding: 10px;
            border: 1px solid palette(mid);
            border-radius: 5px;
        """)
        summary_layout.addWidget(summary_label)
        
        self.details_layout.addWidget(summary_group)
    
    def on_details_failed(self, error):
        """Handle failed details loading"""
        self.header_label.setText(f"Failed to load issue details: {error}")
    
    def format_labels(self, labels):
        """Format labels with colors"""
        if not labels:
            return "No labels"
        
        formatted_labels = []
        for label in labels:
            # Create colored label representation
            color = f"#{label['color']}" if label['color'] else "#cccccc"
            formatted_labels.append(f"🏷️ {label['name']}")
        
        return " | ".join(formatted_labels)
    
    def format_datetime(self, datetime_str):
        """Format datetime string for display"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            return datetime_str
    
    def create_link_label(self, url):
        """Create a clickable link label"""
        label = QLabel(f'<a href="{url}">View on GitHub</a>')
        label.setOpenExternalLinks(True)
        return label
    
    def generate_status_summary(self, issue, comments):
        """Generate a human-readable status summary"""
        summary_parts = []
        
        # Basic status
        if issue['state'] == 'open':
            summary_parts.append("🟢 This issue is currently OPEN and awaiting attention.")
        else:
            summary_parts.append("🔴 This issue has been CLOSED.")
        
        # Label analysis
        labels = [label['name'].lower() for label in issue['labels']]
        
        if 'bug' in labels:
            summary_parts.append("🐛 This is classified as a BUG REPORT.")
        elif 'enhancement' in labels or 'feature-request' in labels:
            summary_parts.append("✨ This is a FEATURE REQUEST.")
        
        if 'auto' in labels:
            summary_parts.append("🤖 This was submitted via the automated reporting system.")
        
        if 'unconfirmed' in labels:
            summary_parts.append("❓ This issue is UNCONFIRMED - awaiting developer review.")
        elif 'confirmed' in labels:
            summary_parts.append("✅ This issue has been CONFIRMED by developers.")
        
        if 'in-progress' in labels or 'working' in labels:
            summary_parts.append("🔄 This issue is currently IN PROGRESS.")
        
        if 'duplicate' in labels:
            summary_parts.append("📋 This has been marked as a DUPLICATE of another issue.")
        
        if 'wontfix' in labels:
            summary_parts.append("🚫 This issue has been marked as WILL NOT FIX.")
        
        # Comment analysis
        if comments:
            summary_parts.append(f"💬 There are {len(comments)} comment(s) on this issue.")
            
            # Check for recent activity
            if comments:
                last_comment_date = comments[-1]['created_at']
                try:
                    last_dt = datetime.fromisoformat(last_comment_date.replace('Z', '+00:00'))
                    now = datetime.now(last_dt.tzinfo)
                    days_ago = (now - last_dt).days
                    
                    if days_ago == 0:
                        summary_parts.append("🕐 There was activity TODAY.")
                    elif days_ago == 1:
                        summary_parts.append("🕐 There was activity YESTERDAY.")
                    elif days_ago <= 7:
                        summary_parts.append(f"🕐 Last activity was {days_ago} days ago.")
                    else:
                        summary_parts.append(f"🕐 Last activity was {days_ago} days ago (may be stale).")
                except:
                    pass
        else:
            summary_parts.append("💭 No comments or updates yet.")
        
        # Add note for private repositories
        if not self.check_repository_visibility():
            summary_parts.append("🔒 This is a PRIVATE repository - GitHub URL not displayed for security.")
        
        return "\n".join(summary_parts)

class IssueReportDialog(QDialog):
    """Dialog for reporting issues and feature requests"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Issue / Request Feature")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        
        self.log_files = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for the issue report dialog"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Report tab
        self.report_tab = QWidget()
        self.setup_report_tab()
        self.tabs.addTab(self.report_tab, "Report Issue / Request Feature")
        
        # View issues tab
        self.issues_tab = QWidget()
        self.setup_issues_tab()
        self.tabs.addTab(self.issues_tab, "Known Issues & Features")
        
        layout.addWidget(self.tabs)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.submit_btn = QPushButton("Submit Issue/Request")
        self.submit_btn.clicked.connect(self.submit_issue)
        button_layout.addWidget(self.submit_btn)
        
        self.refresh_btn = QPushButton("Refresh Issues")
        self.refresh_btn.clicked.connect(self.load_issues)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Close")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Load issues on startup
        QTimer.singleShot(500, self.load_issues)
    
    def setup_report_tab(self):
        """Setup the report tab UI"""
        layout = QVBoxLayout(self.report_tab)
        
        # Issue type selection
        type_group = QGroupBox("Issue Type")
        type_layout = QVBoxLayout(type_group)
        
        self.issue_type = QComboBox()
        self.issue_type.addItem("Bug Report", "bug")
        self.issue_type.addItem("Feature Request", "feature")
        self.issue_type.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.issue_type)
        
        layout.addWidget(type_group)
        
        # Title
        title_group = QGroupBox("Title")
        title_layout = QVBoxLayout(title_group)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Brief description of the issue or feature")
        title_layout.addWidget(self.title_edit)
        
        layout.addWidget(title_group)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Detailed description...")
        self.description_edit.setMaximumHeight(150)
        desc_layout.addWidget(self.description_edit)
        
        layout.addWidget(desc_group)
        
        # Bug-specific fields
        self.bug_group = QGroupBox("Bug Details")
        bug_layout = QFormLayout(self.bug_group)
        
        self.steps_edit = QTextEdit()
        self.steps_edit.setPlaceholderText("1. Do this...\n2. Then this...\n3. See error")
        self.steps_edit.setMaximumHeight(100)
        bug_layout.addRow("Steps to Reproduce:", self.steps_edit)
        
        self.expected_edit = QTextEdit()
        self.expected_edit.setPlaceholderText("What should happen...")
        self.expected_edit.setMaximumHeight(80)
        bug_layout.addRow("Expected Behavior:", self.expected_edit)
        
        self.actual_edit = QTextEdit()
        self.actual_edit.setPlaceholderText("What actually happens...")
        self.actual_edit.setMaximumHeight(80)
        bug_layout.addRow("Actual Behavior:", self.actual_edit)
        
        layout.addWidget(self.bug_group)
        
        # Log files
        log_group = QGroupBox("Log Files (Optional)")
        log_layout = QVBoxLayout(log_group)
        
        log_button_layout = QHBoxLayout()
        self.add_log_btn = QPushButton("Add Log Files")
        self.add_log_btn.clicked.connect(self.add_log_files)
        log_button_layout.addWidget(self.add_log_btn)
        
        self.clear_logs_btn = QPushButton("Clear All")
        self.clear_logs_btn.clicked.connect(self.clear_log_files)
        log_button_layout.addWidget(self.clear_logs_btn)
        
        log_button_layout.addStretch()
        log_layout.addLayout(log_button_layout)
        
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(80)
        log_layout.addWidget(self.log_list)
        
        layout.addWidget(log_group)
        
        # Set initial visibility
        self.on_type_changed()
    
    def setup_issues_tab(self):
        """Setup the issues viewing tab with detailed status"""
        layout = QVBoxLayout(self.issues_tab)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter:"))
        self.issue_filter = QComboBox()
        self.issue_filter.addItem("All Issues", "all")
        self.issue_filter.addItem("Bugs Only", "bugs")
        self.issue_filter.addItem("Features Only", "features")
        self.issue_filter.currentIndexChanged.connect(self.filter_issues)
        filter_layout.addWidget(self.issue_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Create splitter for issues list and detailed view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Issues list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Issues List:"))
        
        self.issues_list = QListWidget()
        self.issues_list.itemClicked.connect(self.on_issue_selected)
        left_layout.addWidget(self.issues_list)
        
        self.status_label = QLabel("Loading issues...")
        left_layout.addWidget(self.status_label)
        
        splitter.addWidget(left_widget)
        
        # Right side: Detailed status view
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Detailed Status:"))
        
        self.status_widget = IssueStatusWidget()
        right_layout.addWidget(self.status_widget)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (40% list, 60% details)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
    
    def on_type_changed(self):
        """Handle issue type change"""
        is_bug = self.issue_type.currentData() == "bug"
        self.bug_group.setVisible(is_bug)
        
        # Update placeholders
        if is_bug:
            self.title_edit.setPlaceholderText("Brief description of the bug")
            self.description_edit.setPlaceholderText("Describe what went wrong in detail...")
        else:
            self.title_edit.setPlaceholderText("Brief description of the requested feature")
            self.description_edit.setPlaceholderText("Describe the feature you'd like to see...")
    
    def add_log_files(self):
        """Add log files to the report"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Log Files", 
            "", 
            "Log files (*.log *.txt);;All files (*.*)"
        )
        
        for file_path in files:
            if file_path not in self.log_files:
                self.log_files.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.log_list.addItem(item)
    
    def clear_log_files(self):
        """Clear all log files"""
        self.log_files.clear()
        self.log_list.clear()
    
    def submit_issue(self):
        """Submit the issue/feature request"""
        # Validate input
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a title.")
            return
        
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a description.")
            return
        
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        # Content validation and rate limiting
        is_valid, validation_issues = validate_issue_content(title, description)
        if not is_valid:
            error_message = "Submission blocked:\n\n" + "\n".join(f"• {issue}" for issue in validation_issues)
            QMessageBox.warning(self, "Content Validation Failed", error_message)
            return
        
        # Prepare issue data
        issue_type = self.issue_type.currentData()
        
        issue_data = {
            'title': title,
            'description': description,
            'type': issue_type
        }
        
        # Add labels
        if issue_type == "bug":
            labels = os.getenv('ISSUE_LABELS_BUG', 'bug,user-reported').split(',')
            issue_data['steps'] = self.steps_edit.toPlainText().strip()
            issue_data['expected'] = self.expected_edit.toPlainText().strip()
            issue_data['actual'] = self.actual_edit.toPlainText().strip()
        else:
            labels = os.getenv('ISSUE_LABELS_FEATURE', 'enhancement,feature-request').split(',')
        
        # Add Auto and unconfirmed tags to all issues
        labels.extend(['Auto', 'unconfirmed'])
        issue_data['labels'] = [label.strip() for label in labels]
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.submit_btn.setEnabled(False)
        
        # Start submission
        self.reporter = IssueReporter(issue_data, self.log_files)
        self.reporter.issue_submitted.connect(self.on_issue_submitted)
        self.reporter.submission_failed.connect(self.on_submission_failed)
        self.reporter.upload_progress.connect(self.progress_bar.setValue)
        self.reporter.start()
    
    def on_issue_submitted(self, result):
        """Handle successful issue submission"""
        self.progress_bar.setVisible(False)
        self.submit_btn.setEnabled(True)
        
        # Record successful submission for rate limiting
        record_successful_submission()
        
        # Create success message
        success_msg = f"Your issue has been submitted successfully!\n\n"
        success_msg += f"Issue #{result['number']}: {result['title']}\n"
        success_msg += f"URL: {result['url']}\n\n"
        
        # Show authentication method used
        if result.get('auth_method'):
            success_msg += f"🤖 Submitted via: {result['auth_description']}\n"
            
            if result['auth_method'] == 'github_app':
                success_msg += "Using GitHub App authentication provides the best security and attribution.\n\n"
            elif result['auth_method'] == 'bot_token':
                success_msg += "This helps keep automated reports separate from personal contributions.\n\n"
            else:
                success_msg += "\n"
        
        success_msg += "Thank you for helping improve PDF Utility!"
        
        QMessageBox.information(
            self,
            "Issue Submitted",
            success_msg
        )
        
        # Clear form
        self.clear_form()
        
        # Refresh issues
        self.load_issues()
    
    def on_submission_failed(self, error):
        """Handle failed issue submission"""
        self.progress_bar.setVisible(False)
        self.submit_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Submission Failed",
            f"Failed to submit issue:\n{error}"
        )
    
    def clear_form(self):
        """Clear the form after submission"""
        self.title_edit.clear()
        self.description_edit.clear()
        self.steps_edit.clear()
        self.expected_edit.clear()
        self.actual_edit.clear()
        self.clear_log_files()
    
    def load_issues(self):
        """Load existing issues"""
        self.status_label.setText("Loading issues...")
        self.refresh_btn.setEnabled(False)
        
        issue_type = self.issue_filter.currentData()
        
        self.loader = IssueListLoader(issue_type)
        self.loader.issues_loaded.connect(self.on_issues_loaded)
        self.loader.load_failed.connect(self.on_load_failed)
        self.loader.start()
    
    def on_issues_loaded(self, issues):
        """Handle loaded issues"""
        self.refresh_btn.setEnabled(True)
        self.issues_list.clear()
        
        if not issues:
            self.status_label.setText("No issues found.")
            return
        
        self.status_label.setText(f"Loaded {len(issues)} issues.")
        
        for issue in issues:
            # Create item text
            state_icon = "🟢" if issue['state'] == 'open' else "🔴"
            labels_text = ", ".join(issue['labels']) if issue['labels'] else "no labels"
            
            item_text = f"{state_icon} #{issue['number']}: {issue['title']}\n"
            item_text += f"   Labels: {labels_text} | Updated: {issue['updated_at'][:10]}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, issue)
            self.issues_list.addItem(item)
    
    def on_load_failed(self, error):
        """Handle failed issue loading"""
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Failed to load issues: {error}")
    
    def filter_issues(self):
        """Filter issues based on selection"""
        self.load_issues()
    
    def on_issue_selected(self, item):
        """Handle issue selection to show detailed status"""
        issue_data = item.data(Qt.ItemDataRole.UserRole)
        if issue_data:
            self.status_widget.display_issue_status(issue_data['number'])

def get_issue_reporter(parent=None):
    """Factory function to get issue reporter dialog"""
    return IssueReportDialog(parent)
