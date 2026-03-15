#!/usr/bin/env python3
"""
Integration script for enhanced HTML/Markdown rendering in PDFSplitter.
This updates existing renderers with improved capabilities.
"""

import os
import shutil
from pathlib import Path

def backup_existing_renderers():
    """Create backups of existing renderer files."""
    print("Creating backups of existing renderer files...")
    
    renderer_paths = [
        "Editor/renderers/html_renderer/renderer.py",
        "Editor/renderers/markdown_renderer/renderer.py"
    ]
    
    for path in renderer_paths:
        if os.path.exists(path):
            backup_path = f"{path}.backup"
            shutil.copy2(path, backup_path)
            print(f"  ✅ Backed up: {path}")
        else:
            print(f"  ⚠️  Not found: {path}")

def update_html_renderer():
    """Update HTML renderer with enhanced capabilities."""
    print("\nUpdating HTML renderer...")
    
    renderer_path = "Editor/renderers/html_renderer/renderer.py"
    
    if not os.path.exists(renderer_path):
        print(f"  ❌ HTML renderer not found: {renderer_path}")
        return False
    
    # Read existing content
    with open(renderer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already enhanced
    if "EnhancedWebRenderer" in content:
        print("  ℹ️  HTML renderer already enhanced")
        return True
    
    # Add enhanced renderer import
    enhanced_import = '''
# Enhanced rendering capabilities
try:
    from enhanced_web_renderer import EnhancedWebRenderer
    ENHANCED_RENDERING = True
except ImportError:
    ENHANCED_RENDERING = False
'''
    
    # Find import section and add enhanced renderer
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add import after existing imports
        if "from ..base import BaseRenderer" in line:
            new_lines.extend(enhanced_import.split('\n'))
        
        # Enhance __init__ method
        elif "def __init__(self" in line and any("class Renderer" in prev_line for prev_line in lines[max(0, i-5):i]):
            # Find the end of __init__ method
            j = i + 1
            while j < len(lines) and not (lines[j].strip().startswith("def ") and not lines[j].strip().startswith("def __")):
                new_lines.append(lines[j])
                j += 1
            
            # Add enhanced renderer initialization
            new_lines.extend([
                "",
                "        # Initialize enhanced renderer",
                "        if ENHANCED_RENDERING:",
                "            self.enhanced_renderer = EnhancedWebRenderer(self.editor, self.logger)",
                "        else:",
                "            self.enhanced_renderer = None",
                ""
            ])
            
            # Skip processed lines
            i = j - 1
        
        # Enhance create_preview_widget method
        elif "def create_preview_widget(self" in line:
            new_lines.extend([
                "        # Try enhanced renderer first",
                "        if self.enhanced_renderer:",
                "            try:",
                "                return self.enhanced_renderer.create_html_widget(parent_frame, html_content, file_path)",
                "            except Exception as e:",
                "                self.logger.error('HTMLRenderer', f'Enhanced rendering failed: {e}')",
                "",
                "        # Fallback to original implementation"
            ])
    
    # Write updated content
    with open(renderer_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("  ✅ HTML renderer enhanced")
    return True

def update_markdown_renderer():
    """Update Markdown renderer with enhanced capabilities."""
    print("\nUpdating Markdown renderer...")
    
    renderer_path = "Editor/renderers/markdown_renderer/renderer.py"
    
    if not os.path.exists(renderer_path):
        print(f"  ❌ Markdown renderer not found: {renderer_path}")
        return False
    
    # Read existing content
    with open(renderer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already enhanced
    if "EnhancedWebRenderer" in content:
        print("  ℹ️  Markdown renderer already enhanced")
        return True
    
    # Add enhanced renderer import
    enhanced_import = '''
# Enhanced markdown rendering capabilities
try:
    from enhanced_web_renderer import EnhancedWebRenderer
    ENHANCED_RENDERING = True
except ImportError:
    ENHANCED_RENDERING = False
'''
    
    # Similar update process as HTML renderer
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add import after existing imports
        if "from ..base import BaseRenderer" in line:
            new_lines.extend(enhanced_import.split('\n'))
        
        # Enhance __init__ method
        elif "def __init__(self" in line and any("class Renderer" in prev_line for prev_line in lines[max(0, i-5):i]):
            # Find the end of __init__ method
            j = i + 1
            while j < len(lines) and not (lines[j].strip().startswith("def ") and not lines[j].strip().startswith("def __")):
                new_lines.append(lines[j])
                j += 1
            
            # Add enhanced renderer initialization
            new_lines.extend([
                "",
                "        # Initialize enhanced markdown renderer",
                "        if ENHANCED_RENDERING:",
                "            self.enhanced_renderer = EnhancedWebRenderer(self.editor, self.logger)",
                "        else:",
                "            self.enhanced_renderer = None",
                ""
            ])
            
            # Skip processed lines
            i = j - 1
        
        # Enhance create_preview_widget method
        elif "def create_preview_widget(self" in line:
            new_lines.extend([
                "        # Try enhanced renderer first",
                "        if self.enhanced_renderer:",
                "            try:",
                "                return self.enhanced_renderer.create_markdown_widget(parent_frame, markdown_content, file_path)",
                "            except Exception as e:",
                "                self.logger.error('MarkdownRenderer', f'Enhanced rendering failed: {e}')",
                "",
                "        # Fallback to original implementation"
            ])
    
    # Write updated content
    with open(renderer_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("  ✅ Markdown renderer enhanced")
    return True

def install_dependencies():
    """Install optional dependencies for enhanced rendering."""
    print("\nInstalling optional dependencies...")
    
    dependencies = [
        "tkhtmlview",  # HTML rendering in tkinter
    ]
    
    import subprocess
    import sys
    
    for dep in dependencies:
        try:
            print(f"  Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"  ✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Failed to install {dep}: {e}")
            print(f"     (Optional dependency - enhanced renderer will use fallbacks)")

def create_renderer_test():
    """Create a test script for the enhanced renderers."""
    print("\nCreating renderer test script...")
    
    test_content = '''#!/usr/bin/env python3
"""
Test script for enhanced HTML/Markdown renderers.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_renderers():
    """Test the enhanced rendering capabilities."""
    try:
        from enhanced_web_renderer import EnhancedWebRenderer
    except ImportError:
        print("❌ Enhanced web renderer not found!")
        return False
    
    print("🧪 Testing Enhanced HTML/Markdown Renderers")
    print("=" * 50)
    
    # Create test window
    root = tk.Tk()
    root.title("Enhanced Renderer Test")
    root.geometry("900x700")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Initialize renderer
    renderer = EnhancedWebRenderer()
    
    # Test HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
            h2 { color: #34495e; }
            code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
            .highlight { background: #fff3cd; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Enhanced HTML Rendering Test</h1>
        <h2>Features</h2>
        <ul>
            <li><strong>Bold text</strong> and <em>italic text</em></li>
            <li>Inline <code>code blocks</code></li>
            <li>Styled content with CSS</li>
        </ul>
        
        <div class="highlight">
            <strong>Highlight:</strong> This content uses enhanced HTML rendering 
            with fallback support for better compatibility.
        </div>
        
        <h2>Code Example</h2>
        <pre><code>
def enhanced_rendering():
    print("Enhanced HTML/Markdown rendering!")
    return "Success"
        </code></pre>
    </body>
    </html>
    """
    
    # Test Markdown content
    markdown_content = """
# Enhanced Markdown Rendering Test

This is a test of the **enhanced Markdown renderer** with improved capabilities.

## Features

- **Bold** and *italic* text formatting
- `Inline code` with proper styling
- Code blocks with syntax highlighting
- Tables and lists
- GitHub-style rendering

### Code Example

```python
def test_markdown_renderer():
    print("Testing enhanced Markdown rendering!")
    
    # Features:
    features = [
        "GitHub-style CSS",
        "Syntax highlighting", 
        "Table support",
        "Browser fallback"
    ]
    
    return features
```

### Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| HTML Rendering | ✅ | tkhtmlview + fallbacks |
| Markdown Conversion | ✅ | markdown library |
| Browser Fallback | ✅ | Opens in default browser |
| Syntax Highlighting | ✅ | Pygments integration |

### Benefits

> Enhanced rendering provides better visual presentation while maintaining 
> compatibility with systems that don't have advanced dependencies installed.

The renderer automatically detects available libraries and uses the best 
option available, falling back gracefully when needed.
"""
    
    # HTML Tab
    html_frame = ttk.Frame(notebook)
    notebook.add(html_frame, text="HTML Test")
    
    try:
        html_widget = renderer.create_html_widget(html_frame, html_content)
        print("✅ HTML widget created successfully")
    except Exception as e:
        print(f"❌ HTML widget creation failed: {e}")
        error_label = ttk.Label(html_frame, text=f"HTML rendering failed: {e}")
        error_label.pack(pady=20)
    
    # Markdown Tab
    md_frame = ttk.Frame(notebook)
    notebook.add(md_frame, text="Markdown Test")
    
    try:
        md_widget = renderer.create_markdown_widget(md_frame, markdown_content)
        print("✅ Markdown widget created successfully")
    except Exception as e:
        print(f"❌ Markdown widget creation failed: {e}")
        error_label = ttk.Label(md_frame, text=f"Markdown rendering failed: {e}")
        error_label.pack(pady=20)
    
    # Info tab
    info_frame = ttk.Frame(notebook)
    notebook.add(info_frame, text="Renderer Info")
    
    info_text = tk.Text(info_frame, wrap=tk.WORD, padx=10, pady=10)
    info_text.pack(fill=tk.BOTH, expand=True)
    
    # Display renderer capabilities
    info_content = f"""
Enhanced Renderer Capabilities:

tkhtmlview available: {renderer.tkhtmlview_available}
webview available: {renderer.webview_available}  
markdown available: {renderer.markdown_available}

Rendering Strategy:
1. Try tkhtmlview for HTML (if available)
2. Fall back to enhanced text widget with HTML parsing
3. For Markdown: convert to HTML first, then render
4. Browser fallback option always available

Features:
- GitHub-style Markdown CSS
- Syntax highlighting for code blocks
- Responsive design
- Table support
- Automatic dependency detection
- Graceful fallbacks

Integration:
- Drop-in replacement for existing renderers
- Maintains backward compatibility
- Enhanced visual presentation
- Better user experience
"""
    
    info_text.insert('1.0', info_content)
    info_text.config(state='disabled')
    
    print("\\n🎉 Test window created successfully!")
    print("Close the window when you're done testing.")
    
    # Run the GUI
    root.mainloop()
    
    # Cleanup
    renderer.cleanup()
    print("✅ Cleanup completed")
    
    return True

if __name__ == "__main__":
    success = test_enhanced_renderers()
    if success:
        print("\\n🎉 Enhanced renderer test completed successfully!")
    else:
        print("\\n❌ Enhanced renderer test failed!")
'''
    
    with open("test_enhanced_renderers.py", 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("  ✅ Test script created: test_enhanced_renderers.py")

def main():
    """Main integration function."""
    print("Enhanced Renderer Integration for PDFSplitter")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("Editor"):
        print("❌ Please run this script from the PDFSplitter root directory")
        print("Current directory:", os.getcwd())
        return False
    
    try:
        # Install optional dependencies
        install_dependencies()
        
        # Create backups
        backup_existing_renderers()
        
        # Update renderers
        html_success = update_html_renderer()
        md_success = update_markdown_renderer()
        
        # Create test script
        create_renderer_test()
        
        print("\\n" + "=" * 60)
        
        if html_success and md_success:
            print("✅ Enhanced renderer integration completed successfully!")
            print("\\nNext steps:")
            print("1. Test the enhanced renderers: python test_enhanced_renderers.py")
            print("2. Restart your PDFSplitter application")
            print("3. Open HTML/Markdown files to see enhanced rendering")
            print("4. Check application logs for any rendering messages")
            print("\\nFeatures added:")
            print("- Better HTML rendering with tkhtmlview")
            print("- GitHub-style Markdown rendering")
            print("- Browser fallback for complex content")
            print("- Graceful fallbacks for missing dependencies")
        else:
            print("❌ Some updates failed. Check the errors above.")
            print("Backup files (.backup) are available for rollback.")
        
        return html_success and md_success
        
    except Exception as e:
        print(f"❌ Integration failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
