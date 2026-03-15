#!/usr/bin/env python3
"""Test toolbar and renderer integration."""

import sys
import os

def test_renderer_tools():
    """Test that renderers have tools method."""
    try:
        from Editor.renderers.text_renderer.renderer import TextRenderer
        renderer = TextRenderer()
        
        if hasattr(renderer, 'tools'):
            tools = renderer.tools()
            print(f"TextRenderer tools: {tools}")
            print(f"Tools type: {type(tools)}")
            return True
        else:
            print("TextRenderer missing tools() method")
            return False
    except Exception as e:
        print(f"Error testing renderer tools: {e}")
        return False

def test_toolbar_creation():
    """Test toolbar manager creation."""
    try:
        import tkinter as tk
        from Editor.toolbar_manager import ToolbarManager
        
        root = tk.Tk()
        root.withdraw()
        
        toolbar = ToolbarManager(root, None)
        print("ToolbarManager created successfully")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"Error creating toolbar: {e}")
        return False

if __name__ == "__main__":
    print("Testing toolbar and renderer integration...")
    
    success = True
    success &= test_renderer_tools()
    success &= test_toolbar_creation()
    
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
