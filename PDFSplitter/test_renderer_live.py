# test_renderer_live.py

import os
import sys
from pathlib import Path
import tempfile
import importlib
import time

# Add the parent directory to the path so we can import the necessary modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class MockEditor:
    """Mock editor class for testing."""
    
    class Logger:
        def info(self, source, message):
            print(f"[INFO] {source}: {message}")
            
        def warning(self, source, message):
            print(f"[WARNING] {source}: {message}")
            
        def error(self, source, message):
            print(f"[ERROR] {source}: {message}")
    
    def __init__(self):
        self.logger = self.Logger()
        
def create_test_files():
    """Create test HTML and Markdown files."""
    temp_dir = tempfile.mkdtemp()
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test HTML File</title>
</head>
<body>
    <h1>Test HTML File</h1>
    <p>This is a test HTML file for renderer selection testing.</p>
</body>
</html>
"""

    md_content = """# Test Markdown File

This is a test Markdown file for renderer selection testing.

## Features

- Bold text: **bold**
- Italic text: *italic*
- Code: `code`
"""

    html_path = os.path.join(temp_dir, "test.html")
    md_path = os.path.join(temp_dir, "test.md")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    return temp_dir, html_path, md_path

def test_live_renderer_selection():
    """Test the live renderer selection."""
    print("Testing Live Renderer Selection")
    print("==============================")
    
    # Create test files
    temp_dir, html_path, md_path = create_test_files()
    print(f"Created test files in: {temp_dir}")
    print(f"- HTML file: {html_path}")
    print(f"- MD file: {md_path}")
    
    try:
        # Import the PluginManager
        from editor.renderers.PluginManager import PluginManager
        
        # Create a mock editor
        mock_editor = MockEditor()
        
        # Create a PluginManager instance
        plugin_manager = PluginManager(mock_editor)
        
        # Load all renderers
        print("\nLoading renderers...")
        registry = plugin_manager.load_all_renderers()
        
        # Check which renderers were registered for each extension
        print("\nRegistered renderers:")
        for ext, (renderer_class, metadata) in registry.items():
            print(f"Extension {ext}: {metadata.get('name', 'unnamed')} (priority: {metadata.get('priority', 'n/a')})")
            
        # Check renderer for .html extension
        html_ext = os.path.splitext(html_path)[1].lower()
        if html_ext in registry:
            html_renderer_class, html_metadata = registry[html_ext]
            print(f"\nSelected renderer for HTML: {html_metadata.get('name', 'unnamed')}")
            if "pyqt" in html_metadata.get('name', '').lower():
                print("✅ PyQt HTML renderer correctly selected")
            else:
                print("❌ PyQt HTML renderer NOT selected!")
        else:
            print(f"❌ No renderer found for {html_ext}")
            
        # Check renderer for .md extension
        md_ext = os.path.splitext(md_path)[1].lower()
        if md_ext in registry:
            md_renderer_class, md_metadata = registry[md_ext]
            print(f"\nSelected renderer for Markdown: {md_metadata.get('name', 'unnamed')}")
            if "pyqt" in md_metadata.get('name', '').lower():
                print("✅ PyQt Markdown renderer correctly selected")
            else:
                print("❌ PyQt Markdown renderer NOT selected!")
        else:
            print(f"❌ No renderer found for {md_ext}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == "__main__":
    # Get Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Run the test
    test_live_renderer_selection()
