#!/usr/bin/env python3
"""Debug the content filter patterns"""

import re

patterns = [
    r"(.)\1{10,}",  # Repeated characters more than 10 times
    r"[A-Z]{20,}",  # Excessive caps (20+ consecutive)
    r"https?://[^\s]+",  # Full URLs
    r"www\.[^\s]+\.[a-z]{2,}",  # www.domain.com patterns
    r"[!]{5,}",  # Excessive exclamation marks
    r"[?]{5,}",  # Excessive question marks
]

test_texts = [
    "PDF merge crashes",
    "When merging large PDF files, the application crashes",
    "Add dark mode",
    "HELP ME NOW",
    "aaaaaaaaaaaaaaaaaaaaaaaaa",
    "Visit www.example.com",
    "!!!!!",
    "URGENT URGENT URGENT"
]

for text in test_texts:
    print(f"\nTesting: '{text}'")
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"  Pattern {i}: {pattern} -> MATCHED: '{match.group()}'")
        else:
            print(f"  Pattern {i}: {pattern} -> No match")
