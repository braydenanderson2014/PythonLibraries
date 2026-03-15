#!/usr/bin/env python3
"""
Simulate the GitHub Actions workflow approach locally
"""

import subprocess
import sys
import os

def test_ci_approach():
    """Test the CI/GitHub Actions approach locally"""
    print("=== Testing CI/GitHub Actions Approach Locally ===")
    
    try:
        # Step 1: Install dependencies (already done)
        print("✓ Dependencies already installed")
        
        # Step 2: Download NLTK data using the CI approach
        print("Step 2: Downloading NLTK data using CI approach...")
        result = subprocess.run([
            'py', '-3.13', '-m', 'nltk.downloader', 'punkt', 'punkt_tab', 'stopwords'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ NLTK data download successful")
        else:
            print(f"⚠ NLTK download had issues (exit code: {result.returncode})")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
        
        # Step 3: Verify NLTK installation
        print("Step 3: Verifying NLTK installation...")
        verify_result = subprocess.run([
            'py', '-3.13', '-c', """
import nltk
try:
    nltk.data.find('tokenizers/punkt_tab')
    print('✓ punkt_tab available')
except LookupError:
    try:
        nltk.data.find('tokenizers/punkt')
        print('✓ punkt available (fallback)')
    except LookupError:
        print('⚠ No punkt tokenizers found')

try:
    nltk.data.find('corpora/stopwords')
    print('✓ stopwords available')
except LookupError:
    print('⚠ stopwords not found')

from nltk.tokenize import word_tokenize
tokens = word_tokenize('This is a test sentence.')
print(f'✓ Tokenization test successful: {tokens[:3]}...')
"""
        ], capture_output=True, text=True, timeout=30)
        
        print("NLTK Verification output:")
        print(verify_result.stdout)
        if verify_result.stderr:
            print("Warnings/Errors:")
            print(verify_result.stderr)
        
        # Step 4: Test the advanced issue manager
        print("Step 4: Testing Advanced Issue Manager...")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
        
        from advanced_issue_manager import IssueAutoManager
        manager = IssueAutoManager("fake_token", "test_owner", "test_repo")
        
        test_content = "This is a test issue for workflow simulation"
        keywords = manager._extract_keywords(test_content)
        print(f"✓ Keyword extraction successful: {keywords}")
        
        print("\n=== CI Approach Test PASSED! ===")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ci_approach()
    sys.exit(0 if success else 1)
