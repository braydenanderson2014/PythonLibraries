#!/usr/bin/env python3
"""
Simple test for environment loading
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ dotenv loaded successfully")
except ImportError:
    print("⚠️ dotenv not available")

import os
print("ENABLE_LOG_UPLOAD:", os.getenv('ENABLE_LOG_UPLOAD'))
print("GITHUB_OWNER:", os.getenv('GITHUB_OWNER'))
print("GITHUB_REPO:", os.getenv('GITHUB_REPO'))

# Test the labels functionality
bug_labels = os.getenv('ISSUE_LABELS_BUG', 'bug,user-reported').split(',')
bug_labels.extend(['Auto', 'unconfirmed'])
print("Bug labels with Auto/unconfirmed:", [label.strip() for label in bug_labels])

feature_labels = os.getenv('ISSUE_LABELS_FEATURE', 'enhancement,feature-request').split(',')
feature_labels.extend(['Auto', 'unconfirmed'])
print("Feature labels with Auto/unconfirmed:", [label.strip() for label in feature_labels])
