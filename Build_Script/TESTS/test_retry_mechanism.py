#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from build_cli import install_package_with_retry

# Test the retry mechanism
print("Testing install_package_with_retry function:")
print("=" * 50)

# Test with a package that should install quickly
print("\n1. Testing with 'requests' (should succeed quickly):")
success, status = install_package_with_retry("requests", "pip", max_retries=2, timeout=30)
print(f"   Result: {success}, Status: {status}")

# Test with a non-existent package (should fail)
print("\n2. Testing with 'non-existent-package-12345' (should fail):")
success, status = install_package_with_retry("non-existent-package-12345", "pip", max_retries=2, timeout=10)
print(f"   Result: {success}, Status: {status}")

print("\n✅ Retry mechanism test completed")
