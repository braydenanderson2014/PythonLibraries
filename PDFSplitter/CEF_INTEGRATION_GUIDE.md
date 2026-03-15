# CEF Python Integration Guide

## Overview

CEF Python provides a full Chrome rendering engine for Python applications, offering superior HTML/CSS/JavaScript support compared to tkhtmlview or basic text widgets.

## Installation

### Option 1: Using pip (Recommended)
```bash
pip install cefpython3
```

### Option 2: Using conda
```bash
conda install -c conda-forge cefpython3
```

### Option 3: From source (Advanced)
```bash
git clone https://github.com/cztomczak/cefpython.git
cd cefpython
python setup.py install
```

## System Requirements

- **Windows**: Windows 7+ (32-bit and 64-bit)
- **Linux**: Ubuntu 14.04+, CentOS 7+ (64-bit)
- **macOS**: macOS 10.10+ (64-bit)
- **Python**: Python 2.7, 3.4-3.11
- **RAM**: At least 512MB available
- **Disk**: ~200MB for CEF binaries

## Benefits of CEF Python Integration

### 1. **Superior Rendering**
- Full Chrome rendering engine
- Complete CSS3 support (gradients, animations, flexbox, grid)
- Modern HTML5 features
- Hardware acceleration support
- Better typography and font rendering

### 2. **JavaScript Execution**
- Full ES6+ JavaScript support
- Modern browser APIs
- Interactive content support
- Framework compatibility (React, Vue, etc.)
- Real-time updates and animations

### 3. **Developer Experience**
- Better debugging with Chrome DevTools integration
- Responsive design support
- Media query support
- Print preview capabilities
- Standards compliance

### 4. **Performance**
- Hardware acceleration
- Efficient memory usage
- Fast rendering pipeline
- Multi-process architecture

## Implementation Architecture

### Current Architecture (tkhtmlview)
```
Markdown/HTML Content → tkhtmlview → Limited HTML Rendering
                                   ↓
                               Basic CSS Support
                               No JavaScript
                               Limited Modern Features
```

### Enhanced Architecture (CEF Python)
```
Markdown/HTML Content → Markdown Processor → Full HTML Document
                                           ↓
                                    CSS/JS Interceptors
                                           ↓
                                    CEF Browser Widget
                                           ↓
                               Full Chrome Rendering Engine
                               Complete CSS3 Support
                               Full JavaScript Execution
                               Modern Web Standards
```

## Integration Points

### 1. **HTML Renderer Enhancement**
- Replace tkhtmlview with CEF browser widget
- Maintain fallback for environments without CEF
- Process CSS/JavaScript through existing interceptors
- Support live preview updates

### 2. **Markdown Renderer Enhancement**
- Convert Markdown to styled HTML
- Use GitHub-style CSS for professional appearance
- Support syntax highlighting for code blocks
- Enable table rendering with proper styling

### 3. **Tab Manager Integration**
- CEF widgets work seamlessly with existing tab system
- Proper resource cleanup on tab close
- Scrolling and navigation support
- Print and export capabilities

## File Structure

```
PDFSplitter/
├── cef_browser_widget.py          # CEF browser widget implementation
├── enhanced_html_renderer.py      # Enhanced HTML renderer with CEF
├── enhanced_markdown_renderer.py  # Enhanced Markdown renderer with CEF
└── Editor/
    └── renderers/
        ├── html_renderer/
        │   ├── renderer.py         # Update to use enhanced renderer
        │   ├── css_interceptor.py  # Existing CSS processing
        │   └── java_script_interceptor.py # Existing JS processing
        └── markdown_renderer/
            └── renderer.py         # Update to use enhanced renderer
```

## Migration Strategy

### Phase 1: Fallback Implementation ✅
- Created enhanced renderers with CEF support
- Maintained fallback to existing tkhtmlview/text widgets
- No breaking changes to existing functionality

### Phase 2: Integration
1. Update existing HTML renderer to use enhanced version
2. Update existing Markdown renderer to use enhanced version
3. Add CEF initialization to main application startup
4. Add CEF cleanup to application shutdown

### Phase 3: Optimization
1. Implement proper resource management
2. Add configuration options for CEF settings
3. Enable developer tools for debugging
4. Add performance monitoring

## Code Example: Using Enhanced Renderers

```python
# In existing HTML renderer
from enhanced_html_renderer import EnhancedHTMLRenderer

class HTMLRenderer(BaseRenderer):
    def __init__(self):
        self.enhanced_renderer = EnhancedHTMLRenderer(self.editor, self.logger)
    
    def create_preview_widget(self, parent_frame, html_content, file_path):
        return self.enhanced_renderer.create_preview_widget(
            parent_frame, html_content, file_path
        )
```

## Testing

Each enhanced renderer includes comprehensive tests:

```bash
# Test CEF browser widget
python cef_browser_widget.py

# Test enhanced HTML renderer
python enhanced_html_renderer.py

# Test enhanced Markdown renderer
python enhanced_markdown_renderer.py
```

## Configuration Options

### CEF Settings
```python
cef_settings = {
    'debug': False,                    # Enable/disable debug mode
    'log_severity': cef.LOGSEVERITY_WARNING,
    'multi_threaded_message_loop': False,
    'cache_path': 'cache/',           # Browser cache directory
    'user_data_path': 'userdata/',    # User data directory
}
```

### Browser Settings
```python
browser_settings = {
    'file_access_from_file_urls': True,     # Allow local file access
    'universal_access_from_file_urls': True,
    'web_security': False,                  # Disable for local development
    'javascript_access_clipboard': True,    # Allow clipboard access
}
```

## Troubleshooting

### Common Issues

1. **Import Error**: CEF not installed
   ```bash
   pip install cefpython3
   ```

2. **Display Issues**: X11 forwarding problems
   ```bash
   export DISPLAY=:0
   ```

3. **Memory Issues**: Increase available RAM
   ```python
   # Reduce CEF cache size
   settings['cache_path'] = ''  # Disable cache
   ```

4. **Performance Issues**: Hardware acceleration
   ```python
   # Enable hardware acceleration
   settings['multi_threaded_message_loop'] = True
   ```

## Next Steps

1. **Install CEF Python**: `pip install cefpython3`
2. **Test Integration**: Run test scripts to verify functionality
3. **Update Renderers**: Integrate enhanced renderers into existing code
4. **Configure Settings**: Optimize CEF settings for your use case
5. **Deploy**: Test in production environment

The CEF Python integration will significantly improve the HTML and Markdown rendering capabilities of your PDF editor, providing a modern web browsing experience within the application.
