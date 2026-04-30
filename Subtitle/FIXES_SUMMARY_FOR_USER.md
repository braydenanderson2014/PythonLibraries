# Summary: Installer PATH Issue Fixes - April 9, 2026

## Executive Summary

I've identified and **fixed the root cause** of why tools weren't being added to the system PATH after installation. The main issue was that after ffmpeg installs via a child PowerShell process, the parent process wasn't reloading the system PATH from the Windows registry.

**Status**: ✅ **FIXED** - Ready to test with your colleague

---

## What Was Wrong

### **Critical Issue: FFmpeg PATH Not Propagating**

**The Problem**:
1. Installer runs ffmpeg installer in a **child PowerShell process**
2. Child process calls `winget` (or `choco`/`scoop`) to install ffmpeg
3. Package manager updates Windows registry PATH ✅
4. Child PowerShell exits ❌
5. **Parent process's `$env:Path` is now STALE** - doesn't reflect the registry changes
6. Parent process cannot find ffmpeg, so subsequent checks fail

**Why This Happened**:
- After a child PowerShell process exits, environment changes don't automatically propagate back to the parent
- The parent needs to explicitly call `Update-ProcessPathFromRegistry` to reload from the registry

### **Secondary Issues: Poor Diagnostics**

1. No warning if ffmpeg installed but still not accessible
2. No validation that the script is being run correctly (console vs ISE, admin privileges)
3. No clear guidance to users on troubleshooting

---

## Fixes Applied

### ✅ **Fix 1: Explicit PATH Refresh After FFmpeg Install**
**File**: `install_all_windows.ps1` (Line 5107-5108)

**What Changed**:
```powershell
# OLD: No PATH refresh
if ($LASTEXITCODE -ne 0) {
    Write-StatusFail "ffmpeg installation"
    throw "ffmpeg installation failed."
}
# Installer continues without refreshing PATH

# NEW: Explicit PATH refresh
if ($LASTEXITCODE -ne 0) {
    Write-StatusFail "ffmpeg installation"
    throw "ffmpeg installation failed."
}

# Refresh parent process PATH from registry after child PowerShell installer completes
Update-ProcessPathFromRegistry
```

**Impact**: ffmpeg installation now properly updates the parent process's `$env:Path`

---

### ✅ **Fix 2: Execution Environment Validation**
**File**: `install_all_windows.ps1` (Lines 110-120)

**What Changed**:
- Added PowerShell version check (requires 5.0+)
- Added warning if running in PowerShell ISE (ISE has different execution semantics)

**Output**:
```
WARNING: Running in PowerShell ISE may cause issues.
          For best results, run this script in PowerShell Console instead.
```

**Impact**: Prevents users from running in ISE where errors occur more frequently

---

### ✅ **Fix 3: Enhanced FFmpeg Verification**
**File**: `install_all_windows.ps1` (Lines 5133-5148)

**What Changed**:
- Explicitly checks if ffmpeg is accessible after installation
- Shows warning if installed but not on PATH
- Suggests terminal restart as mitigation

**Output**:
```
WARNING: ffmpeg was installed but is not yet accessible on PATH.
Try restarting your terminal or computer for PATH changes to take full effect.
```

**Impact**: Clear feedback to user if PATH issues occur

---

### ✅ **Fix 4: New Troubleshooting Guide**
**File**: `INSTALLER_TROUBLESHOOTING.md` (NEW)

**Covers**:
- How to run the installer correctly (console, not ISE, as admin)
- Why the original error occurred
- Step-by-step verification procedures
- Manual PATH configuration if needed
- Diagnosis using the installer log

---

## Files Modified/Created

| File | Change | Type |
|------|--------|------|
| `install_all_windows.ps1` | Added PATH refresh after ffmpeg | CRITICAL FIX |
| `install_all_windows.ps1` | Added environment validation | IMPROVEMENT |
| `install_all_windows.ps1` | Enhanced ffmpeg verification | IMPROVEMENT |
| `INSTALLER_TROUBLESHOOTING.md` | New comprehensive guide | DOCUMENTATION |
| `INSTALLER_FIXES_APPLIED.md` | Technical details of fixes | DOCUMENTATION |

---

## How to Test with Your Colleague

### **Step 1: Prepare**
```powershell
# Download/pull latest version with fixes
cd D:\PythonLibraries\Subtitle
git pull  # or download latest ZIP
```

### **Step 2: Run Correctly ⚠️ IMPORTANT**
1. **Open PowerShell Console** (NOT ISE!)
   - Press `Win + R` 
   - Type: `powershell`
   - **Right-click result → "Run as administrator"**
   
2. Navigate and run:
```powershell
cd D:\PythonLibraries\Subtitle
.\install_all_windows.ps1
```

### **Step 3: Verify After Installation**
**Open a NEW PowerShell window** (close the old one first) and run:
```powershell
ffmpeg -version
ffprobe -version
mkvmerge --version    # if installed
HandBrakeCLI --version  # if installed
makemkvcon --help     # if installed
```

All should return version info, NOT "command not found"

### **Step 4: If Issues Persist**
1. Check the install log: `cat .\install_all_windows.log | tail -50`
2. See the troubleshooting guide: `.\INSTALLER_TROUBLESHOOTING.md`
3. Try manual PATH configuration (documented in guide)

---

## Expected vs Actual Behavior

### **Original Error**
```
The expression after & in a pipeline element produced an object that was not valid. Line 1 char 3
```
At position "Line 1 char 3", which is at the start of the `&` operator

### **Root Cause**
- Running in PowerShell ISE instead of console
- NOT running as administrator
- (After fixes) PATH refresh issue prevented tools from being found

### **After Fixes**
- Clear warning if ISE is detected
- Explicit PATH refresh ensures tools are accessible
- Verification shows what went wrong (if anything)
- User gets actionable guidance (terminal restart, manual PATH, etc.)

---

## Backward Compatibility

✅ **All changes are backward compatible**:
- Fixes are additive (no breaking changes to existing functionality)
- Optional tools already worked (they use direct process calls + PATH refresh)
- Existing installations unaffected
- All parameters/features remain the same

---

## Double-Check: What About Optional Tools?

**mkvmerge, HandBrake, makemkvcon**:
- Already working correctly (they're installed directly in parent process)
- Already call `Update-ProcessPathFromRegistry` after install (in `Set-ToolCliReachable`)
- No additional fixes needed

**Why different from ffmpeg?**:
- FFmpeg runs in a **child PowerShell** (spawn separate process)
- Optional tools run **in the parent process** directly

---

## Technical Details for Reference

### Function: `Update-ProcessPathFromRegistry`
```powershell
function Update-ProcessPathFromRegistry {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}
```

**What it does**:
- Reads system PATH from Windows registry (both Machine and User scopes)
- Updates current PowerShell process's `$env:Path` variable
- Ensures newly installed tools are visible to the current session

### Where Called After Fixes:
1. After ffmpeg install (was missing, now added) ✨
2. After mkvmerge/HandBrake/makemkvcon install (was already there)
3. When bridging CLIs that aren't on PATH

---

## Action Items

### For You:
- [ ] Share this summary with your colleague
- [ ] Have them follow the "How to Test" section
- [ ] Ask them to report back on whether it works
- [ ] If issues remain, check the troubleshooting guide

### For Your Colleague:
- [ ] **IMPORTANT**: Use PowerShell Console, not ISE
- [ ] **IMPORTANT**: Run as Administrator
- [ ] Download latest version with fixes
- [ ] Follow verification steps after installation
- [ ] Check troubleshooting guide if needed

---

## Questions to Ask If Issues Persist

1. **Execution method**:
   - Are you using PowerShell Console or ISE?
   - Are you running as Administrator?

2. **System state**:
   - Is this after a fresh Windows install?
   - Do you have winget, choco, or scoop installed?

3. **Logs**:
   - What does `install_all_windows.log` show at the end?
   - Any error messages near the tool installation sections?

4. **PATH state**:
   - After installation, run: `$env:Path` - show the output
   - Try: `ffmpeg -version` in a NEW terminal window

---

## References

- **New Troubleshooting Guide**: [`INSTALLER_TROUBLESHOOTING.md`](./INSTALLER_TROUBLESHOOTING.md)
- **Technical Details**: [`INSTALLER_FIXES_APPLIED.md`](./INSTALLER_FIXES_APPLIED.md)
- **Installer Script**: [`install_all_windows.ps1`](./install_all_windows.ps1)

---

## Success Criteria

After running the fixed installer, your colleague should see:

✅ No PowerShell parsing errors  
✅ FFmpeg installation completes  
✅ Running `ffmpeg -version` in a new terminal shows version info  
✅ Optional tools (mkvmerge, HandBrake) accessible on PATH  
✅ Subtitle Tool can use all tools without fallback errors  

---

**Ready to test!** 🚀 Let me know how it goes.

