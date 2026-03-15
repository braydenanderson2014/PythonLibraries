#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import sys
import os
import traceback

def test_toolbar_manager():
    """Test toolbar manager import."""
    print("Testing ToolbarManager import...")
    try:
        from Editor.toolbar_manager import ToolbarManager
        print("✓ ToolbarManager imported successfully")
        return True
    except Exception as e:
        print(f"✗ ToolbarManager import failed: {e}")
        traceback.print_exc()
        return False

def test_renderer_imports():
    """Test renderer imports."""
    print("\nTesting renderer imports...")
    renderers = [
        'Editor.renderers.pdf_renderer.renderer',
        'Editor.renderers.html_renderer.renderer',
        'Editor.renderers.markdown_renderer.renderer',
        'Editor.renderers.text_renderer.renderer'
    ]
    
    success_count = 0
    for renderer_path in renderers:
        try:
            __import__(renderer_path)
            print(f"✓ {renderer_path} imported successfully")
            success_count += 1
        except Exception as e:
            print(f"✗ {renderer_path} import failed: {e}")
            traceback.print_exc()
    
    return success_count == len(renderers)

def test_registry_import():
    """Test registry import."""
    print("\nTesting registry import...")
    try:
        from Editor.renderers_registry import renderers_registry
        print("✓ renderers_registry imported successfully")
        print(f"  Registry contains: {list(renderers_registry.keys())}")
        return True
    except Exception as e:
        print(f"✗ renderers_registry import failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("PDF Splitter Import Test Suite")
    print("=" * 40)
    
    results = []
    results.append(test_toolbar_manager())
    results.append(test_renderer_imports())
    results.append(test_registry_import())
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All imports working correctly!")
        return 0
    else:
        print("✗ Some imports failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
