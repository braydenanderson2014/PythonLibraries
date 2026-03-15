#!/usr/bin/env python3
"""Debug the content filter by examining actual loaded filters"""

from content_filter import ContentFilter

filter_test = ContentFilter()

print("Current filters:")
print("Inappropriate words:", filter_test.filters["inappropriate_words"])
print("Spam patterns:", filter_test.filters["spam_patterns"])
print()

# Test a simple case manually
text = "PDF merge crashes"
print(f"Testing: '{text}'")

# Test inappropriate words
text_lower = text.lower()
inappropriate_found = []
for word in filter_test.filters["inappropriate_words"]:
    if word.lower() in text_lower:
        inappropriate_found.append(word)
        print(f"  Found inappropriate word: {word}")

if not inappropriate_found:
    print("  No inappropriate words found")

# Test spam patterns
import re
for i, pattern in enumerate(filter_test.filters["spam_patterns"]):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"  Pattern {i} ({pattern}) matched: {match.group()}")
    else:
        print(f"  Pattern {i} ({pattern}) no match")

# Now test the actual method
is_clean, issues = filter_test.check_inappropriate_content(text)
print(f"\nMethod result: is_clean={is_clean}, issues={issues}")
