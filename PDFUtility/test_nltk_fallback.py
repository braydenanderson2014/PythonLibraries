#!/usr/bin/env python3
"""
Test NLTK fallback behavior specifically for punkt_tab issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_nltk_fallback():
    """Test NLTK tokenization with fallback when punkt_tab is missing"""
    print("=== Testing NLTK Fallback Behavior ===")
    
    try:
        from advanced_issue_manager import IssueAutoManager
        
        # Create manager
        manager = IssueAutoManager("fake_token", "test_owner", "test_repo")
        print("✓ Manager created successfully")
        
        # Test keyword extraction with problematic content
        test_content = "This is a test issue with some content for tokenization testing!"
        
        print(f"Testing keyword extraction with: '{test_content}'")
        keywords = manager._extract_keywords(test_content)
        print(f"✓ Keywords extracted: {keywords}")
        
        # Test simple tokenization directly
        simple_tokens = manager._simple_tokenize(test_content)
        print(f"✓ Simple tokenization works: {simple_tokens[:5]}...")
        
        print("\n=== NLTK Fallback Test Passed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_nltk_fallback()
    sys.exit(0 if success else 1)
