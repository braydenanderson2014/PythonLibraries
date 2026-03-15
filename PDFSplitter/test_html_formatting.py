#!/usr/bin/env python3
"""
Test the HTML formatting function.
"""

def test_html_formatting():
    print("Testing HTML Text Formatting:")
    print("=" * 50)
    
    test_html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <title>HTMLRenderer Test Page</title>
</head>
<body>
  <h1>Welcome to the HTMLRenderer Test</h1>
  <p>This is a live-editable paragraph. Try changing this text and watch the live preview update.</p>
  
  <h2>Unordered List</h2>
  <ul>
    <li>First item</li>
    <li>Second item with a link</li>
    <li>Third item</li>
  </ul>

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

  <p>This is another paragraph with some text.</p>
</body>
</html>'''

    try:
        import sys
        sys.path.append('/workspaces/SystemCommands/PDFSplitter')
        
        from bs4 import BeautifulSoup
        from Editor.renderers.html_renderer.renderer import Renderer
        
        # Create a renderer instance to access the formatting method
        renderer = Renderer()
        
        # Parse the HTML
        soup = BeautifulSoup(test_html, 'html.parser')
        body = soup.find('body')
        
        if body:
            formatted_text = renderer._format_html_for_text_display(body)
            print("Formatted HTML output:")
            print("-" * 30)
            print(formatted_text)
            print("-" * 30)
            print(f"✅ HTML formatting successful! ({len(formatted_text)} characters)")
        else:
            print("❌ No body tag found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing HTML formatting: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_html_formatting()
