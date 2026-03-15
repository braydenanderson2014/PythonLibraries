# Build System Configuration

## Dependency Fallback System

The advanced build system now includes intelligent dependency fallback support to handle platform compatibility issues, especially with PyQt6 on x86 architectures.

### Configuration

Edit `.github/build-config.json` to configure dependency fallbacks and excluded architectures:

```json
{
  "name": "PDF-Utility",
  "architectures": {
    "windows": ["x64", "arm64"],
    "linux": ["x64", "arm64"], 
    "macos": ["x64", "arm64"]
  },
  "excluded_architectures": {
    "windows": ["x86"],
    "linux": [],
    "macos": []
  },
  "dependency_fallbacks": {
    "PyQt6": [
      {"package": "PyQt6>=6.5.0", "reason": "Latest stable version"},
      {"package": "PyQt6>=6.4.0", "reason": "Fallback to older stable"},
      {"package": "PyQt6>=6.3.0", "reason": "Further fallback"},
      {"package": "PyQt5>=5.15.0", "reason": "Legacy compatibility fallback"}
    ],
    "numpy": [
      {"package": "numpy>=1.24.0", "reason": "Latest version"},
      {"package": "numpy>=1.21.0", "reason": "Fallback for older systems"}
    ],
    "Pillow": [
      {"package": "Pillow>=10.0.0", "reason": "Latest version"},
      {"package": "Pillow>=9.0.0", "reason": "Fallback version"}
    ]
  }
}
```

### How It Works

1. **Excluded Architectures**: Builds for specified platforms/architectures are completely skipped
2. **Dependency Fallbacks**: When a dependency fails to install, the system tries fallback versions
3. **Smart Installation**: Each dependency is tried with its fallback chain until one succeeds
4. **Graceful Degradation**: If all fallbacks fail, the build continues with a warning

### PyQt6 x86 Compatibility Issue

**Problem**: PyQt6 requires Qt development tools (qmake) during installation, which aren't available in GitHub Actions runners for Windows x86 builds.

**Solutions Implemented**:

#### Option 1: Exclude x86 Builds (Recommended)
- Set `"excluded_architectures": {"windows": ["x86"]}`
- Simplest solution, works immediately
- Users on x86 systems can use x64 builds (most modern x86 systems support x64)

#### Option 2: PyQt5 Fallback System  
- Dependency fallback automatically tries PyQt5 when PyQt6 fails
- Requires PyQt6/PyQt5 compatibility (provided by `pyqt_compatibility.py`)
- More complex but supports legacy systems

#### Option 3: Code Compatibility Layer
- `pyqt_compatibility.py` provides seamless PyQt6 ↔ PyQt5 compatibility
- Automatically detects available PyQt version
- Minimal code changes required
- Optional import converter available (`convert_pyqt_imports.py`)

### Testing

Test the system locally:

```bash
python test_dependency_fallbacks.py
python test_pyqt_strategy.py
```

### Build Matrix Impact

Before (with x86 failures):
- ❌ Windows x86: Failed due to PyQt6
- ✅ Windows x64: Success
- ✅ Linux x64: Success  
- ✅ macOS arm64: Success

After (with exclusions):
- ⚪ Windows x86: Excluded
- ✅ Windows x64: Success
- ✅ Linux x64: Success
- ✅ macOS arm64: Success

After (with fallbacks):
- ✅ Windows x86: Success with PyQt5
- ✅ Windows x64: Success with PyQt6
- ✅ Linux x64: Success with PyQt6
- ✅ macOS arm64: Success with PyQt6

### Recommendations

1. **For production**: Use excluded architectures approach (Option 1)
   - Simplest and most reliable
   - x64 builds work on x86 systems anyway
   
2. **For maximum compatibility**: Use fallback system (Option 2)
   - More complex but supports all architectures
   - Requires testing with both PyQt versions

3. **For existing codebases**: Use compatibility layer (Option 3)
   - Minimal changes to existing code
   - Smooth transition path

### Build Workflow Features

- **Fail-Fast Protection**: Single platform failures don't cancel other builds
- **Timeout Handling**: Individual package timeouts prevent hanging builds
- **Comprehensive Logging**: Detailed installation progress and failure reasons
- **Automatic Release Creation**: Tagged builds automatically create GitHub releases
- **Development Builds**: Manual workflow dispatch for testing
