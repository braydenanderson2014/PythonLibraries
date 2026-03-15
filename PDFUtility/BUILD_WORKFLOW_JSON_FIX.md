# Build Workflow JSON Name Fix

## Problem
The build workflow was failing with JSON parsing errors, specifically:
```
Error: Invalid format '  "name": "PDF_Utility",'
```

## Root Cause
1. **Underscore in name**: `PDF_Utility` contains underscores which can cause issues in bash scripts
2. **Insufficient JSON validation**: No error handling for malformed JSON
3. **No sanitization**: App name used directly in filenames without cleaning special characters

## Solutions Implemented

### 1. **Fixed JSON Configuration**
**Before:**
```json
{
  "name": "PDF_Utility",
  ...
}
```

**After:**
```json
{
  "name": "PDF-Utility",
  ...
}
```

### 2. **Enhanced JSON Validation**
```bash
# Validate JSON first
if jq empty .github/build-config.json 2>/dev/null; then
  CONFIG=$(cat .github/build-config.json)
  echo "✅ JSON file is valid"
else
  echo "❌ Invalid JSON in build-config.json, using defaults"
  # Fallback to defaults
fi
```

### 3. **Robust JSON Parsing**
```bash
# Extract with proper error handling
APP_NAME=$(echo "$CONFIG" | jq -r '.name // "PDF-Utility"' 2>/dev/null || echo "PDF-Utility")
BUILD_TYPE=$(echo "$CONFIG" | jq -r '.build_type // "onefile"' 2>/dev/null || echo "onefile")
WINDOWED=$(echo "$CONFIG" | jq -r '.windowed // false' 2>/dev/null || echo "false")
MAIN_FILE=$(echo "$CONFIG" | jq -r '.main_file // "auto"' 2>/dev/null || echo "auto")
```

### 4. **App Name Sanitization**
```bash
# Sanitize app name for use as filename (remove special characters)
APP_NAME_CLEAN=$(echo "$APP_NAME" | sed 's/[^a-zA-Z0-9-]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
```

This converts:
- `PDF_Utility` → `PDF-Utility`
- `My App Name!` → `My-App-Name`
- `Test@#$%App` → `Test-App`

### 5. **Enhanced Logging**
```bash
echo "📄 Configuration JSON:"
echo "$CONFIG" | jq .

echo "📊 Build Configuration:"
echo "  App Name: $APP_NAME"
echo "  App Name (Clean): $APP_NAME_CLEAN"
echo "  Build Type: $BUILD_TYPE"
echo "  Windowed: $WINDOWED"
echo "  Main File: $MAIN_FILE"
```

## Build Process Improvements

### Error Recovery
- **JSON validation**: Checks if JSON is parseable before using it
- **Fallback defaults**: Uses safe defaults if JSON parsing fails
- **Error handling**: All `jq` commands have fallback values
- **Graceful degradation**: Workflow continues even if config file is broken

### File Naming
- **Clean names**: Removes special characters that could break file systems
- **Consistent format**: `AppName-platform-architecture`
- **Cross-platform safe**: Works on Windows, Linux, and macOS
- **No spaces or special chars**: Prevents shell script issues

### Debugging Support
- **Step-by-step logging**: Shows each configuration step
- **JSON pretty-printing**: Displays parsed configuration for debugging
- **Clear error messages**: Indicates what went wrong and why
- **Value verification**: Shows extracted values before use

## Expected Output

### Successful Build Log
```
📋 Found repository build configuration
✅ JSON file is valid
📄 Configuration JSON:
{
  "name": "PDF-Utility",
  "version": "auto",
  "main_file": "auto",
  "build_type": "onefile",
  "windowed": false
}

📊 Build Configuration:
  App Name: PDF-Utility
  App Name (Clean): PDF-Utility
  Build Type: onefile
  Windowed: false
  Main File: auto

🏗️ Building PDF-Utility for windows-x64
📄 Main file: main_application.py
🚀 Running: pyinstaller --onefile --clean --name PDF-Utility-windows-x64 main_application.py
```

### Error Recovery Log
```
📋 Found repository build configuration
❌ Invalid JSON in build-config.json, using defaults

📊 Build Configuration:
  App Name: PDF-Utility
  App Name (Clean): PDF-Utility
  Build Type: onefile
  Windowed: false
  Main File: auto
```

## Files Modified

1. **`.github/build-config.json`**:
   - Changed `"PDF_Utility"` to `"PDF-Utility"`
   - Removed underscore to prevent bash issues

2. **`.github/workflows/build.yml`**:
   - Added JSON validation step
   - Enhanced error handling for JSON parsing
   - Added app name sanitization
   - Improved logging and debugging output
   - Used clean app names in all file operations

## Testing

The build workflow should now handle:
- ✅ Valid JSON configuration files
- ✅ Invalid/malformed JSON files (fallback to defaults)
- ✅ App names with special characters (automatically sanitized)
- ✅ Missing configuration files (use defaults)
- ✅ JSON parsing errors (graceful error handling)

## Backward Compatibility

- ✅ Works with existing configuration format
- ✅ Maintains all original functionality  
- ✅ Fallback behavior for missing or broken configs
- ✅ No breaking changes to API or behavior

---
*Build workflow JSON fixes implemented: August 17, 2025*  
*Status: Ready for testing*
