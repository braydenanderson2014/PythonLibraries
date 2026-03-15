#!/usr/bin/env python3
"""
Integration script to update existing HTML and Markdown renderers with CEF Python support.
This script modifies the existing renderer files to use enhanced CEF-based rendering.
"""

import os
import shutil
from pathlib import Path

def backup_existing_files():
    """Create backups of existing renderer files."""
    print("Creating backups of existing renderer files...")
    
    files_to_backup = [
        "Editor/renderers/html_renderer/renderer.py",
        "Editor/renderers/markdown_renderer/renderer.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            print(f"  ✅ Backed up {file_path} to {backup_path}")
        else:
            print(f"  ⚠️  File not found: {file_path}")

def update_html_renderer():
    """Update the HTML renderer to use CEF Python."""
    print("\nUpdating HTML renderer...")
    
    html_renderer_path = "Editor/renderers/html_renderer/renderer.py"
    
    if not os.path.exists(html_renderer_path):
        print(f"  ❌ HTML renderer not found: {html_renderer_path}")
        return False
    
    # Read the existing file
    with open(html_renderer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if CEF integration is already present
    if "enhanced_html_renderer" in content:
        print("  ℹ️  CEF integration already present in HTML renderer")
        return True
    
    # Add CEF integration
    cef_integration = '''
# CEF Python integration
try:
    from enhanced_html_renderer import EnhancedHTMLRenderer
    CEF_ENHANCED = True
except ImportError:
    CEF_ENHANCED = False
'''
    
    # Find the class definition and add CEF initialization
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add import at the top after existing imports
        if i < 20 and "from ..base import BaseRenderer" in line:
            new_lines.append(cef_integration)
        
        # Add CEF renderer initialization to __init__ method
        elif "def __init__(self" in line and "class Renderer" in lines[max(0, i-5):i]:
            # Find the end of __init__ and add CEF initialization
            j = i + 1
            while j < len(lines) and not (lines[j].strip().startswith("def ") and not lines[j].strip().startswith("def __")):
                new_lines.append(lines[j])
                j += 1
            
            # Add CEF initialization before the next method
            new_lines.append("")
            new_lines.append("        # Initialize CEF enhanced renderer")
            new_lines.append("        if CEF_ENHANCED:")
            new_lines.append("            self.cef_renderer = EnhancedHTMLRenderer(self.editor, self.logger)")
            new_lines.append("        else:")
            new_lines.append("            self.cef_renderer = None")
            new_lines.append("")
            
            # Skip the lines we already processed
            i = j - 1
    
    # Write the updated content
    with open(html_renderer_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("  ✅ HTML renderer updated with CEF integration")
    return True

def update_markdown_renderer():
    """Update the Markdown renderer to use CEF Python."""
    print("\nUpdating Markdown renderer...")
    
    md_renderer_path = "Editor/renderers/markdown_renderer/renderer.py"
    
    if not os.path.exists(md_renderer_path):
        print(f"  ❌ Markdown renderer not found: {md_renderer_path}")
        return False
    
    # Read the existing file
    with open(md_renderer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if CEF integration is already present
    if "enhanced_markdown_renderer" in content:
        print("  ℹ️  CEF integration already present in Markdown renderer")
        return True
    
    # Add CEF integration
    cef_integration = '''
# CEF Python integration for enhanced markdown rendering
try:
    from enhanced_markdown_renderer import EnhancedMarkdownRenderer
    CEF_ENHANCED = True
except ImportError:
    CEF_ENHANCED = False
'''
    
    # Find the class definition and add CEF initialization
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add import at the top after existing imports
        if i < 20 and "from ..base import BaseRenderer" in line:
            new_lines.append(cef_integration)
        
        # Add CEF renderer initialization to __init__ method
        elif "def __init__(self" in line and "class Renderer" in lines[max(0, i-5):i]:
            # Find the end of __init__ and add CEF initialization
            j = i + 1
            while j < len(lines) and not (lines[j].strip().startswith("def ") and not lines[j].strip().startswith("def __")):
                new_lines.append(lines[j])
                j += 1
            
            # Add CEF initialization before the next method
            new_lines.append("")
            new_lines.append("        # Initialize CEF enhanced renderer")
            new_lines.append("        if CEF_ENHANCED:")
            new_lines.append("            self.cef_renderer = EnhancedMarkdownRenderer(self.editor, self.logger)")
            new_lines.append("        else:")
            new_lines.append("            self.cef_renderer = None")
            new_lines.append("")
            
            # Skip the lines we already processed
            i = j - 1
    
    # Write the updated content
    with open(md_renderer_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("  ✅ Markdown renderer updated with CEF integration")
    return True

def create_cef_helper_methods():
    """Create helper methods for CEF integration."""
    print("\nCreating CEF helper methods...")
    
    helper_content = '''#!/usr/bin/env python3
"""
CEF integration helper methods for existing renderers.
Provides enhanced preview widget creation with fallback support.
"""

def create_enhanced_html_preview(renderer, parent_frame, html_content, file_path=None):
    """
    Create an enhanced HTML preview widget using CEF or fallback.
    
    Args:
        renderer: The existing renderer instance
        parent_frame: Parent tkinter frame
        html_content: HTML content to display
        file_path: Optional file path for resource resolution
        
    Returns:
        Widget instance (CEF browser or fallback)
    """
    try:
        if hasattr(renderer, 'cef_renderer') and renderer.cef_renderer:
            return renderer.cef_renderer.create_preview_widget(
                parent_frame, html_content, file_path
            )
    except Exception as e:
        renderer.logger.error("CEFHelper", f"CEF widget creation failed: {e}")
    
    # Fallback to existing method
    return renderer._create_fallback_preview_widget(parent_frame, html_content)

def create_enhanced_markdown_preview(renderer, parent_frame, markdown_content, file_path=None):
    """
    Create an enhanced Markdown preview widget using CEF or fallback.
    
    Args:
        renderer: The existing renderer instance
        parent_frame: Parent tkinter frame
        markdown_content: Markdown content to display
        file_path: Optional file path for resource resolution
        
    Returns:
        Widget instance (CEF browser or fallback)
    """
    try:
        if hasattr(renderer, 'cef_renderer') and renderer.cef_renderer:
            return renderer.cef_renderer.create_preview_widget(
                parent_frame, markdown_content, file_path
            )
    except Exception as e:
        renderer.logger.error("CEFHelper", f"CEF widget creation failed: {e}")
    
    # Fallback to existing method
    return renderer._create_fallback_preview_widget(parent_frame, markdown_content)

def update_enhanced_widget_content(widget, content, is_markdown=False):
    """
    Update content in an enhanced widget (CEF or fallback).
    
    Args:
        widget: The widget to update
        content: New content (HTML or Markdown)
        is_markdown: Whether content is Markdown (needs conversion)
    """
    try:
        if hasattr(widget, 'set_html'):
            # CEF or tkhtmlview widget
            if is_markdown:
                # Convert markdown to HTML first
                try:
                    import markdown
                    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite'])
                    html_content = md.convert(content)
                    widget.set_html(html_content)
                except ImportError:
                    # Fallback: set as plain text
                    widget.set_html(f"<pre>{content}</pre>")
            else:
                widget.set_html(content)
                
        elif hasattr(widget, 'config') and hasattr(widget, 'insert'):
            # Text widget fallback
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", content)
            widget.config(state="disabled")
            
    except Exception as e:
        print(f"Error updating widget content: {e}")
'''
    
    with open("cef_helper_methods.py", 'w', encoding='utf-8') as f:
        f.write(helper_content)
    
    print("  ✅ CEF helper methods created")

def check_dependencies():
    """Check if required dependencies are available."""
    print("\nChecking dependencies...")
    
    dependencies = {
        'cefpython3': 'CEF Python (pip install cefpython3)',
        'markdown': 'Markdown processor (pip install markdown)',
        'bs4': 'BeautifulSoup (pip install beautifulsoup4)',
    }
    
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            print(f"  ✅ {dep} - Available")
        except ImportError:
            print(f"  ❌ {dep} - Missing ({description})")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with:")
        for dep in missing_deps:
            if dep == 'cefpython3':
                print(f"  pip install {dep}")
            elif dep == 'bs4':
                print("  pip install beautifulsoup4")
            else:
                print(f"  pip install {dep}")
        return False
    
    return True

def main():
    """Main integration function."""
    print("CEF Python Integration Script")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists("Editor"):
        print("❌ Please run this script from the PDFSplitter root directory")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install missing dependencies before proceeding")
        return False
    
    # Create backups
    backup_existing_files()
    
    # Update renderers
    success = True
    success &= update_html_renderer()
    success &= update_markdown_renderer()
    
    # Create helper methods
    create_cef_helper_methods()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ CEF Python integration completed successfully!")
        print("\nNext steps:")
        print("1. Test the enhanced renderers")
        print("2. Restart your application")
        print("3. Open HTML/Markdown files to see CEF rendering")
        print("4. Check the logs for any CEF-related messages")
    else:
        print("❌ Integration failed. Check the errors above.")
        print("Backup files have been created with .backup extension")
    
    return success

if __name__ == "__main__":
    main()
