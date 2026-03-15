#!/usr/bin/env python3
"""
Test script for Advanced Issue Manager
Tests basic functionality without requiring actual GitHub API calls
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_advanced_manager():
    """Test the Advanced Issue Manager can initialize and run basic functions"""
    print("=== Testing Advanced Issue Manager ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")
    
    # Test basic imports first
    try:
        import requests
        print(f"✓ requests available: {requests.__version__}")
    except ImportError as e:
        print(f"✗ requests import error: {e}")
        return False
    
    try:
        import json
        print("✓ json available")
    except ImportError as e:
        print(f"✗ json import error: {e}")
        return False
    
    try:
        # Import the module
        from advanced_issue_manager import IssueAutoManager, SKLEARN_AVAILABLE, NLTK_AVAILABLE
        print(f"✓ Successfully imported IssueAutoManager")
        print(f"  - scikit-learn available: {SKLEARN_AVAILABLE}")
        print(f"  - NLTK available: {NLTK_AVAILABLE}")
        
        # Test initialization
        manager = IssueAutoManager("fake_token", "test_owner", "test_repo")
        print("✓ Successfully initialized manager")
        
        # Test basic content extraction
        test_issue = {
            'title': 'Test issue title',
            'body': 'This is a test issue body with some content',
            'number': 123
        }
        
        content = manager._extract_content(test_issue)
        print(f"✓ Content extraction works: '{content[:50]}...'")
        
        # Test text classification
        issue_content = manager._extract_content(test_issue)
        issue_type, confidence = manager._classify_type(issue_content)
        print(f"✓ Issue classification works: {issue_type} (confidence: {confidence:.2f})")
        
        # Test completeness scoring
        score, missing = manager._analyze_completeness(issue_content, issue_type)
        print(f"✓ Completeness scoring works: {score:.2f}, missing: {missing}")
        
        print("\n=== All tests passed! ===")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_advanced_manager()
    sys.exit(0 if success else 1)
