#!/usr/bin/env python3
"""
Test script to verify the tab manager and renderer integration.
"""

import os

def test_tab_manager_changes():
    """Test the tab manager changes."""
    print("Testing Tab Manager Changes:")
    print("=" * 50)
    
    # Test 1: Filename extraction
    test_paths = [
        "/home/user/documents/test.pdf",
        "C:\\Users\\User\\Documents\\file with spaces.txt",
        "/complex/path/to/My Document (Version 1).md",
        "simple.html"
    ]
    
    print("\n1. Testing filename extraction:")
    for path in test_paths:
        filename = os.path.basename(path)
        print(f"  {path} -> {filename}")
    
    # Test 2: Check if renderer methods are properly implemented
    print("\n2. Checking renderer implementations:")
    
    renderers = [
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/text_renderer/renderer.py',
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/pdf_renderer/renderer.py',
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/markdown_renderer/renderer.py',
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/html_renderer/renderer.py',
    ]
    
    for renderer_path in renderers:
        renderer_name = os.path.basename(os.path.dirname(renderer_path))
        print(f"\n  {renderer_name}:")
        
        try:
            with open(renderer_path, 'r') as f:
                content = f.read()
            
            # Check for scroll method
            if 'def scroll(' in content:
                print("    ✅ scroll method implemented")
            else:
                print("    ❌ scroll method missing")
            
            # Check for renderer parameter in register_tab_widget
            if 'renderer=self' in content:
                print("    ✅ renderer parameter passed to register_tab_widget")
            else:
                print("    ❌ renderer parameter not passed to register_tab_widget")
        
        except Exception as e:
            print(f"    ❌ Error reading file: {e}")
    
    # Test 3: Check tab manager scroll delegation
    print("\n3. Checking tab manager scroll delegation:")
    
    try:
        tab_manager_path = '/workspaces/SystemCommands/PDFSplitter/Editor/tab_manager.py'
        with open(tab_manager_path, 'r') as f:
            content = f.read()
        
        if '_handle_scroll_event' in content:
            print("    ✅ _handle_scroll_event method implemented")
        else:
            print("    ❌ _handle_scroll_event method missing")
        
        if 'renderer.scroll(' in content:
            print("    ✅ Delegating to renderer scroll method")
        else:
            print("    ❌ Not delegating to renderer scroll method")
        
        if '_add_tab_tooltip' in content:
            print("    ✅ Tab tooltip functionality implemented")
        else:
            print("    ❌ Tab tooltip functionality missing")
    
    except Exception as e:
        print(f"    ❌ Error reading tab manager: {e}")
    
    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    test_tab_manager_changes()
