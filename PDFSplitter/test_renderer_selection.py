# test_renderer_selection.py

import os
import sys
import importlib
from pathlib import Path

# Add the parent directory to the path so we can import the necessary modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_renderer_priority():
    """Test that renderers are selected based on priority."""
    print("Testing Renderer Selection by Priority")
    print("======================================")
    
    try:
        # Import the renderers registry
        from editor.renderers.renderers_registry import RENDERER_MODULES
        
        print(f"Found {len(RENDERER_MODULES)} registered renderers:")
        for i, module_name in enumerate(RENDERER_MODULES):
            print(f"{i+1}. {module_name}")
            
        # Try to import each renderer and check its metadata
        print("\nTesting renderer loading and priority:")
        
        renderer_info = {}
        
        for module_name in RENDERER_MODULES:
            try:
                # Extract the renderer name from the module path
                parts = module_name.split('.')
                renderer_name = parts[-2]  # Get the renderer folder name
                
                # Build path to settings.json
                settings_path = Path("editor/renderers") / renderer_name / "settings.json"
                
                if os.path.exists(settings_path):
                    import json
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        
                    priority = metadata.get("priority", 10)  # Default to low priority
                    extensions = metadata.get("extensions", [])
                    
                    renderer_info[renderer_name] = {
                        "priority": priority,
                        "extensions": extensions
                    }
                    
                    print(f"✅ {renderer_name}")
                    print(f"   Priority: {priority}")
                    print(f"   Extensions: {', '.join(extensions)}")
                    
                else:
                    print(f"❌ {renderer_name} - settings.json not found")
                    
            except Exception as e:
                print(f"❌ Error loading {module_name}: {e}")
        
        # Simulate the priority-based renderer selection
        print("\nSimulated Renderer Selection:")
        
        # Group renderers by extension
        extension_renderers = {}
        for name, info in renderer_info.items():
            for ext in info["extensions"]:
                ext = ext.lower()
                if ext not in extension_renderers:
                    extension_renderers[ext] = []
                extension_renderers[ext].append((name, info["priority"]))
        
        # For each extension, select the highest priority renderer
        for ext, renderers in extension_renderers.items():
            # Sort by priority (lower number = higher priority)
            sorted_renderers = sorted(renderers, key=lambda x: x[1])
            if sorted_renderers:
                selected_renderer, priority = sorted_renderers[0]
                print(f"Extension {ext}: {selected_renderer} (priority: {priority})")
                
                # Check specifically for HTML and Markdown to verify PyQt is selected
                if ext == ".md" or ext == ".markdown":
                    if selected_renderer == "pyqt_markdown_renderer":
                        print(f"  ✅ PyQt Markdown renderer is correctly selected for {ext}")
                    else:
                        print(f"  ❌ PyQt Markdown renderer is NOT selected for {ext}!")
                        
                elif ext == ".html" or ext == ".htm":
                    if selected_renderer == "pyqt_html_renderer":
                        print(f"  ✅ PyQt HTML renderer is correctly selected for {ext}")
                    else:
                        print(f"  ❌ PyQt HTML renderer is NOT selected for {ext}!")
        
        # Try to import the PyQt renderer directly
        print("\nVerifying PyQt renderers can be imported:")
        try:
            from editor.renderers.pyqt_markdown_renderer.renderer import Renderer as PyQtMarkdownRenderer
            from editor.renderers.pyqt_markdown_renderer.renderer import PYQT_AVAILABLE
            print(f"✅ PyQt Markdown renderer imported successfully")
            print(f"   PyQt Available: {PYQT_AVAILABLE}")
        except ImportError as e:
            print(f"❌ Could not import PyQt Markdown renderer: {e}")
            
        try:
            from editor.renderers.pyqt_html_renderer.renderer import Renderer as PyQtHtmlRenderer
            print(f"✅ PyQt HTML renderer imported successfully")
        except ImportError as e:
            print(f"❌ Could not import PyQt HTML renderer: {e}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    # Get Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Run the test
    test_renderer_priority()
