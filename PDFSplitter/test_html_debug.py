#!/usr/bin/env python3
"""
Test script to debug HTML rendering issues.
"""

def test_css_processing():
    """Test CSS interceptor with the test HTML."""
    print("Testing CSS Processing:")
    print("=" * 50)
    
    test_html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HTMLRenderer Test Page</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 1em; }
    h1 { color: #336699; }
    p { line-height: 1.5; }
    .highlight { background: #fffae6; padding: 0.2em; }
    table { border-collapse: collapse; width: 100%; margin-top: 1em; }
    table, th, td { border: 1px solid #888; }
    th, td { padding: 0.5em; text-align: left; }
    ul { margin-top: 1em; }
    button { padding: 0.5em 1em; margin-top: 1em; }
  </style>
</head>
<body>
  <h1>Welcome to the HTMLRenderer Test</h1>
  <p>This is a <span class="highlight">live-editable</span> paragraph.</p>
  
  <h2>Simple Table</h2>
  <table>
    <thead>
      <tr><th>Name</th><th>Age</th><th>City</th></tr>
    </thead>
    <tbody>
      <tr><td>Alice</td><td>30</td><td>New York</td></tr>
      <tr><td>Bob</td><td>25</td><td>San Francisco</td></tr>
    </tbody>
  </table>

  <h2>Inline Script</h2>
  <button onclick="document.getElementById('msg').textContent = 'Button clicked!';">
    Click Me
  </button>
  <p id="msg" style="margin-top:.5em; color:green;"></p>
</body>
</html>'''

    try:
        import sys
        sys.path.append('/workspaces/SystemCommands/PDFSplitter')
        
        from Editor.renderers.html_renderer.css_interceptor import CSSInterceptor
        from Editor.renderers.html_renderer.java_script_interceptor import JavaScriptInterceptor
        
        # Test CSS processing
        print("1. Processing CSS...")
        css_processor = CSSInterceptor(test_html, base_path="/workspaces/SystemCommands/PDFSplitter")
        processed_css = css_processor.inline_css()
        print(f"   CSS processed successfully: {len(processed_css)} characters")
        
        # Test JavaScript processing  
        print("2. Processing JavaScript...")
        js_processor = JavaScriptInterceptor(processed_css)
        final_html = js_processor.safe_scripts()
        print(f"   JavaScript processed successfully: {len(final_html)} characters")
        
        # Show a sample of the processed HTML
        print("\n3. Sample of processed HTML:")
        print("-" * 30)
        lines = final_html.split('\n')
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            print(f"{i+1:2d}: {line}")
        if len(lines) > 20:
            print(f"... ({len(lines)-20} more lines)")
            
        print("\n✅ HTML processing successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing HTML: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tkhtmlview_capabilities():
    """Test tkhtmlview capabilities with complex CSS."""
    print("\nTesting tkhtmlview capabilities:")
    print("=" * 50)
    
    try:
        import tkinter as tk
        from tkhtmlview import HTMLScrolledText
        
        # Simple test HTML
        simple_html = '''<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
    h1 { color: #336699; text-align: center; }
    .highlight { background: #fffae6; padding: 0.2em; border: 1px solid #ddd; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
    th, td { border: 1px solid #888; padding: 0.5em; text-align: left; }
    th { background: #e0e0e0; }
</style>
</head>
<body>
    <h1>Test HTML Rendering</h1>
    <p>This paragraph has <span class="highlight">highlighted text</span> to test CSS.</p>
    <table>
        <tr><th>Column 1</th><th>Column 2</th></tr>
        <tr><td>Data 1</td><td>Data 2</td></tr>
    </table>
</body>
</html>'''
        
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        # Test if HTMLScrolledText can handle the HTML
        widget = HTMLScrolledText(root, html=simple_html)
        print("✅ HTMLScrolledText created successfully")
        
        # Test if we can update HTML
        widget.set_html(simple_html)
        print("✅ HTML content updated successfully")
        
        root.destroy()
        return True
        
    except ImportError:
        print("❌ tkhtmlview not available")
        return False
    except Exception as e:
        print(f"❌ Error testing tkhtmlview: {e}")
        return False

if __name__ == "__main__":
    print("HTML Renderer Debug Test")
    print("=" * 60)
    
    success = True
    success &= test_css_processing()
    success &= test_tkhtmlview_capabilities()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! HTML processing should work correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.")
