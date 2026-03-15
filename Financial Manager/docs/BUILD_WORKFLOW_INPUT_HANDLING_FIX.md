# Build Workflow Input Handling Fix

## Error Analysis
The error you're seeing:
```
Error: Invalid format '  "name": "PDF-Utility",'
```

This happens when GitHub Actions workflow inputs contain empty strings (`""`) instead of proper values, causing bash script variables to be empty and JSON parsing to fail.

## Root Cause
The problematic code pattern:
```bash
# This causes issues when inputs are empty
if [[ "" != "" && "" != "{}" ]]; then
    WORKFLOW_CONFIG=''
    CONFIG=$(echo "$CONFIG" "$WORKFLOW_CONFIG" | jq -s '.[0] * .[1]')
fi
```

When workflow inputs are not provided, GitHub Actions substitutes them with empty strings, leading to:
- Invalid JSON merging operations
- Bash conditional failures  
- JSON parsing errors

## Solutions Implemented

### 1. **Advanced Build Workflow** (`advanced-build.yml`)
This is a comprehensive workflow that handles the complex configuration system from your error:

#### Features:
- ✅ **Matrix-based builds** for all platform/architecture combinations
- ✅ **Dynamic configuration** with input overrides
- ✅ **JSON validation** at every step
- ✅ **Proper input handling** with fallbacks
- ✅ **Multi-job architecture** (configure → build)

#### Usage:
```yaml
# Trigger with inputs
workflow_dispatch:
  inputs:
    platforms: "windows,linux"
    config_override: '{"windowed": true}'
    build_cli_version: "2.1.0"
```

### 2. **Simple Build Workflow** (`build.yml`) 
Enhanced the existing simple workflow with better input handling:

#### Features:
- ✅ **Static matrix** (simpler, more reliable)
- ✅ **Input validation** for config overrides
- ✅ **Proper fallbacks** for empty inputs
- ✅ **Single-job architecture** (faster)

## Fixed Input Handling

### Before (Problematic):
```bash
# Undefined behavior with empty inputs
if [[ "" != "" && "" != "{}" ]]; then
    WORKFLOW_CONFIG=''
    CONFIG=$(echo "$CONFIG" "$WORKFLOW_CONFIG" | jq -s '.[0] * .[1]')
fi
```

### After (Robust):
```bash
# Proper input validation
CONFIG_OVERRIDE="${{ github.event.inputs.config_override }}"
PLATFORMS_INPUT="${{ github.event.inputs.platforms }}"

# Apply config override if provided and valid
if [[ -n "$CONFIG_OVERRIDE" && "$CONFIG_OVERRIDE" != "{}" && "$CONFIG_OVERRIDE" != "" ]]; then
  echo "🔧 Applying workflow configuration overrides"
  if echo "$CONFIG_OVERRIDE" | jq empty 2>/dev/null; then
    CONFIG=$(echo "$CONFIG" "$CONFIG_OVERRIDE" | jq -s '.[0] * .[1]')
    echo "✅ Applied configuration overrides"
  else
    echo "❌ Invalid JSON in config override, ignoring"
  fi
fi
```

## Key Improvements

### 1. **Proper Variable Assignment**
```bash
# OLD: Direct substitution (fails with empty inputs)
if [[ "${{ github.event.inputs.config_override }}" != "" ]]; then

# NEW: Variable assignment with validation
CONFIG_OVERRIDE="${{ github.event.inputs.config_override }}"
if [[ -n "$CONFIG_OVERRIDE" && "$CONFIG_OVERRIDE" != "{}" ]]; then
```

### 2. **JSON Validation**
```bash
# Validate JSON before using it
if echo "$CONFIG_OVERRIDE" | jq empty 2>/dev/null; then
    # Safe to use
else
    echo "❌ Invalid JSON, ignoring"
fi
```

### 3. **Comprehensive Error Handling**
```bash
# Fallback values for all operations
APP_NAME=$(echo "$CONFIG" | jq -r '.name // "PDF-Utility"' 2>/dev/null || echo "PDF-Utility")
```

### 4. **Enhanced Logging**
```bash
echo "🔧 Applying workflow configuration overrides"
echo "Override JSON: $CONFIG_OVERRIDE"
echo "✅ Applied configuration overrides"
```

## Choosing the Right Workflow

### Use `advanced-build.yml` if you need:
- Complex platform/architecture matrix
- Dynamic configuration merging
- Workflow input overrides
- Maximum flexibility and control

### Use `build.yml` if you need:
- Simple, reliable builds
- Faster execution (single job)
- Basic configuration support
- Minimal complexity

## Troubleshooting

### If you see input-related errors:
1. **Check workflow inputs**: Ensure they're properly defined
2. **Validate JSON**: Use `jq` to check JSON syntax
3. **Check logs**: Look for validation messages
4. **Use defaults**: Remove custom inputs to test with defaults

### If you see JSON parsing errors:
1. **Validate config file**: Check `.github/build-config.json` syntax
2. **Check input JSON**: Validate any override JSON
3. **Enable debug logging**: Add `echo` statements to see values
4. **Use fallbacks**: Workflows now gracefully handle JSON errors

## Migration Guide

### If you're currently using a broken workflow:
1. **Switch to `advanced-build.yml`** for full feature compatibility
2. **Or use the fixed `build.yml`** for simpler needs
3. **Test with manual dispatch** first
4. **Check the build logs** for validation messages

### Testing the fix:
1. **Manual trigger**: Use GitHub Actions tab
2. **With inputs**: Try different input combinations
3. **Without inputs**: Test default behavior
4. **Invalid inputs**: Test error handling

---
*Input handling fixes implemented: August 17, 2025*
*Status: Ready for production use*

## Example Usage

### Advanced Workflow:
```bash
# Manual dispatch with overrides
platforms: "windows,linux"
config_override: '{"windowed": true, "build_type": "onedir"}'
```

### Simple Workflow:
```bash
# Manual dispatch with basic config
config_override: '{"name": "MyApp", "windowed": true}'
```

Both workflows now handle empty inputs gracefully and provide clear error messages.
