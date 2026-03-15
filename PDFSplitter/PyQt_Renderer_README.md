# PyQt WebEngine Renderer Implementation

## Overview
This implementation provides modern HTML and Markdown rendering in the PDFSplitter application using PyQt6's WebEngine component, which is compatible with Python 3.13.3.

## Components

1. **PyQt Markdown Renderer**
   - Full support for GitHub-flavored Markdown
   - JavaScript and CSS support via WebEngine
   - Seamless integration with Tkinter

2. **PyQt HTML Renderer**
   - Full browser capabilities with HTML5, CSS3, and JavaScript
   - Resource path resolution for local files
   - Dual tab support with live preview

## Installation
To use these renderers, install the required dependencies:

```
pip install -r requirements_pyqt.txt
```

Or install manually:

```
pip install PyQt6 PyQt6-WebEngine beautifulsoup4
```

## Compatibility
- Works with Python 3.13.3 (and earlier versions)
- Falls back to standard renderers if PyQt6 is not available
- Gracefully handles missing dependencies

## Features
- Dual tab editing with synchronized preview
- Full JavaScript execution and DOM manipulation
- Resource path resolution for images and other assets
- Responsive layout and styling
- Automatic refresh on edit

## Implementation Details
- PyQtWebFrame class for Tkinter integration
- BeautifulSoup for HTML parsing and resource path fixing
- Full editor with syntax highlighting
- Live preview updates

## Testing
Run the included test script to verify proper functionality:

```
python test_pyqt_html_renderer.py
```
