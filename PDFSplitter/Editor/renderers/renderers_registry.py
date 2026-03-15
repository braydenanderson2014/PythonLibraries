# Registry of all renderer modules for PyInstaller compatibility
# Add new renderers here instead of relying on dynamic discovery

RENDERER_MODULES = [
    "editor.renderers.pdf_renderer.renderer",
    "editor.renderers.markdown_renderer.renderer", 
    "editor.renderers.html_renderer.renderer",
    "editor.renderers.text_renderer.renderer",
    "editor.renderers.cef_markdown_renderer.renderer",
    "editor.renderers.cef_html_renderer.renderer",
    "editor.renderers.pyqt_markdown_renderer.renderer",
    "editor.renderers.pyqt_html_renderer.renderer"
    # Add more renderers here as needed:
    # "editor.renderers.image_renderer.renderer",
    # "editor.renderers.json_renderer.renderer",
]

# Optional: You can also define renderer metadata here if needed
RENDERER_METADATA = {
    "pdf_renderer": {
        "name": "PDF Renderer",
        "description": "Advanced PDF viewer and editor",
        "priority": 1
    },
    "text_renderer": {
        "name": "Text Renderer", 
        "description": "Plain text file editor",
        "priority": 10
    },
    "cef_markdown_renderer": {
        "name": "CEF Markdown Renderer",
        "description": "Chrome-based Markdown renderer with full HTML5 support",
        "priority": 2  # Higher priority than standard markdown renderer
    },
    "cef_html_renderer": {
        "name": "CEF HTML Renderer",
        "description": "Chrome-based HTML renderer with full CSS3 and JavaScript support",
        "priority": 2  # Higher priority than standard HTML renderer
    },
    "pyqt_markdown_renderer": {
        "name": "PyQt Markdown Renderer",
        "description": "PyQt WebEngine-based Markdown renderer with full HTML5 support - compatible with Python 3.13",
        "priority": 1  # Highest priority to be used before CEF
    },
    "pyqt_html_renderer": {
        "name": "PyQt HTML Renderer",
        "description": "PyQt WebEngine-based HTML renderer with full CSS3 and JavaScript support - compatible with Python 3.13",
        "priority": 1  # Highest priority to be used before CEF
    }
    # Add more metadata as needed
}