#!/usr/bin/env python3
"""
Test the content filter with realistic examples
"""

from content_filter import ContentFilter

def test_realistic_cases():
    """Test with realistic submission examples"""
    
    filter_test = ContentFilter()
    
    print("Realistic Content Filter Test")
    print("=" * 40)
    
    test_cases = [
        # Valid submissions
        ("PDF merge crashes", "When merging large PDF files, the application crashes with an out of memory error."),
        ("Add dark mode", "Please add a dark mode theme for better usability in low-light environments."),
        ("Search functionality broken", "The search feature doesn't work properly when searching for text in merged PDFs."),
        
        # Invalid submissions - inappropriate language
        ("This app sucks", "This stupid app is terrible and sucks at everything."),
        
        # Invalid submissions - spam patterns
        ("HELP ME NOW", "URGENT URGENT URGENT FIX THIS IMMEDIATELY!!!!!"),
        ("Check this out", "Visit www.example.com for more info"),
        ("Repeated text", "aaaaaaaaaaaaaaaaaaaaaaaaa"),
        
        # Edge cases
        ("Short", "a"),  # Too short
        ("Long title but reasonable content", "This is a reasonable description that should pass all filters."),
        ("", "Empty title test"),  # Empty title
        ("Normal title", ""),  # Empty description
    ]
    
    passed = 0
    failed = 0
    
    for i, (title, desc) in enumerate(test_cases, 1):
        is_valid, issues = filter_test.validate_submission(title, desc)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        
        print(f"\n{i}. {status}")
        print(f"   Title: '{title}'")
        print(f"   Description: '{desc[:50]}{'...' if len(desc) > 50 else ''}'")
        
        if issues:
            for issue in issues:
                print(f"   - {issue}")
        
        if is_valid:
            passed += 1
        else:
            failed += 1
    
    print(f"\n" + "=" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")

if __name__ == "__main__":
    test_realistic_cases()
