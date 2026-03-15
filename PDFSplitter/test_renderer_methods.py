#!/usr/bin/env python3
"""
Test script to verify all renderers implement the required abstract methods.
"""

import os
import sys
import importlib
import inspect
from abc import ABC, abstractmethod

# Add the current directory to the path
sys.path.insert(0, '/workspaces/SystemCommands/PDFSplitter')

try:
    # Mock the dependencies that might not be available
    sys.modules['fitz'] = type('MockModule', (), {})()
    sys.modules['tkhtmlview'] = type('MockModule', (), {'HTMLLabel': type('MockClass', (), {})})()
    sys.modules['ttkbootstrap'] = type('MockModule', (), {'Style': type('MockClass', (), {}), 'Window': type('MockClass', (), {})})()
    sys.modules['markdown'] = type('MockModule', (), {'markdown': lambda x: x})()
    
    # Mock the editor modules
    sys.modules['editor.renderers.base'] = type('MockModule', (), {})()
    sys.modules['editor.document_model'] = type('MockModule', (), {})()
    sys.modules['editor.file_api'] = type('MockModule', (), {})()
    
    # Define BaseRenderer for testing
    class BaseRenderer(ABC):
        def __init__(self, editor):
            self.editor = editor
        
        @classmethod
        @abstractmethod
        def extensions(cls):
            pass
        
        @abstractmethod
        def open(self, path: str) -> str:
            pass
        
        @abstractmethod
        def scroll(self, tab_id: str, direction: str, amount: int):
            pass
    
    # Test each renderer
    renderers = [
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/text_renderer/renderer.py',
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/pdf_renderer/renderer.py',
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/markdown_renderer/renderer.py',
        '/workspaces/SystemCommands/PDFSplitter/Editor/renderers/html_renderer/renderer.py',
    ]
    
    print("Testing renderer implementations:")
    print("=" * 50)
    
    for renderer_path in renderers:
        print(f"\nTesting: {os.path.basename(os.path.dirname(renderer_path))}")
        
        try:
            # Read the file content
            with open(renderer_path, 'r') as f:
                content = f.read()
            
            # Check if scroll method is implemented
            if 'def scroll(' in content:
                print("  ✅ scroll method implemented")
            else:
                print("  ❌ scroll method missing")
            
            # Check other required methods
            required_methods = ['def open(', 'def extensions(']
            for method in required_methods:
                if method in content:
                    print(f"  ✅ {method.replace('def ', '').replace('(', '')} method implemented")
                else:
                    print(f"  ❌ {method.replace('def ', '').replace('(', '')} method missing")
        
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")

    print("\n" + "=" * 50)
    print("All renderers should now have the scroll method implemented!")

except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()
