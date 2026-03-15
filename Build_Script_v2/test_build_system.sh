#!/bin/bash
# Test script for Build System v2

echo "=========================================="
echo "Build System v2 - Test Suite"
echo "=========================================="
echo ""

# Test 1: List commands
echo "Test 1: Listing available commands..."
python build_system.py -i << EOF
list
exit
EOF
echo ""

# Test 2: Scan Python files
echo "Test 2: Scanning Python files for entry points..."
python build_system.py scan-python --find-main
echo ""

# Test 3: Scan general files
echo "Test 3: Scanning project files..."
python build_system.py scan --target .
echo ""

# Test 4: Build dry-run
echo "Test 4: Build with dry-run (preview command)..."
python build_system.py build example_app.py --dry-run --name TestApp
echo ""

# Test 5: Help command
echo "Test 5: Getting help for build command..."
python build_system.py -i << EOF
help build
exit
EOF
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
echo ""
echo "To actually build the example app:"
echo "  python build_system.py build example_app.py --name TestApp"
echo ""
echo "To run with icon detection (requires images):"
echo "  python build_system.py scan-icon --target ./assets"
echo "  python build_system.py build"
