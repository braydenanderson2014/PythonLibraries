# Subtitle Tool Installer - Troubleshooting & PATH Setup Guide

## Overview

The installer manages several system tools that need to be available on your system PATH:
- **ffmpeg** - Video encoding/decoding
- **ffprobe** - Video analysis (part of ffmpeg)
- **mkvmerge** - MKV file manipulation (MKVToolNix)
- **HandBrakeCLI** - Video encoding
- **makemkvcon** - MKV creation from optical media

All of these must be accessible from your command line after installation.

---

## How PATH Setup Works

### 1. **FFmpeg Installation**
- The installer runs `install_ffmpeg_windows.ps1` in a child PowerShell process
- This child process uses winget/choco/scoop to install ffmpeg
- **FIX APPLIED**: After ffmpeg installation completes, the parent process now **explicitly refreshes** the system PATH from the Windows registry

### 2. **Optional Tools (mkvmerge, HandBrake, makemkvcon)**
- Installed directly in the main process using winget/choco/scoop
- Immediately followed by `Set-ToolCliReachable` which:
  - Detects the tool's installation directory
  - Adds it to user PATH if not already there
  - Refreshes the process PATH from registry
  - Verifies the tool is now accessible

### 3. **Auto-Bridging Mode**
- If a tool is found but not on PATH, the installer automatically adds its directory to PATH
- This handles cases where tools install to non-standard locations

---

## Common Issues & Solutions

### **Error: "The expression after & in a pipeline element produced an object that was not valid. Line 1 char 3"**

This error typically indicates one of the following:

#### **Issue 1: Running in PowerShell ISE (NOT RECOMMENDED)**
**Symptom**: Script fails with parsing errors
**Solution**: Use PowerShell **Console** instead, not ISE
- ❌ **WRONG**: Open PowerShell ISE and run the script
- ✅ **RIGHT**: 
  1. Press `Win + R`
  2. Type: `powershell`
  3. Right-click the PowerShell result and select **"Run as administrator"**
  4. Navigate to the Subtitle folder: `cd D:\PythonLibraries\Subtitle`
  5. Run: `.\install_all_windows.ps1`

#### **Issue 2: Not Running as Administrator**
**Symptom**: Permission denied errors, tools not found after install
**Solution**: Run PowerShell as administrator
- Right-click PowerShell → "Run as administrator"
- OR: Start Task Scheduler and run with elevated privileges

#### **Issue 3: File Encoding Issues**
**Symptom**: Strange characters or parsing errors at script start
**Solution**: 
- Ensure the script file is UTF-8 encoded (NOT UTF-16 or with BOM)
- Re-download the installer from the repository if you manually edited it

#### **Issue 4: Stale PATH in Current Session**
**Symptom**: Tools install successfully but still say "command not found"
**Solution**: 
- Close the PowerShell window and open a new one
- New sessions automatically get the updated PATH
- The installer now calls `Update-ProcessPathFromRegistry` after each tool install

---

## Verification Steps

### **After Installation Completes**

Run these commands in a **NEW** PowerShell window (important!):

```powershell
# Check ffmpeg
ffmpeg -version

# Check ffprobe
ffprobe -version

# Check mkvmerge (if installed)
mkvmerge --version

# Check HandBrakeCLI (if installed)
HandBrakeCLI --version

# Check makemkvcon (if installed)
makemkvcon --help
```

If any command says "not found" or "not recognized":
1. Check the installer log: `install_all_windows.log`
2. Verify the tools are installed in Program Files or app-local directories
3. See the "Manual PATH Configuration" section below

---

## Manual PATH Configuration

If tools were installed but aren't on the system PATH:

### **Via GUI (Easy)**
1. Press `Win + X` and select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under "User variables" (or "System variables"), find or create **Path**
5. Click **Edit** → **New**
6. Add the tool directory, examples:
   - FFmpeg: `C:\Users\<Username>\AppData\Local\Packages\Gyan\ffmpeg\bin`
   - MKVToolNix: `C:\Program Files\MKVToolNix`
   - HandBrake: `C:\Program Files\HandBrake`
   - MakeMKV: `C:\Program Files\MakeMKV`
7. Click **OK** → **OK** → **OK**
8. **Close all PowerShell/CMD windows and open new ones** for changes to take effect

### **Via PowerShell (Advanced)**
```powershell
# Add a directory to user PATH
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\path\to\tool\bin", "User")

# Then refresh current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify
echo $env:Path
```

---

## How to Run the Installer Correctly

### **Method 1: Right-Click & Run as Administrator (Easiest)**
1. Navigate to `D:\PythonLibraries\Subtitle`
2. Right-click **install_all_windows.ps1**
3. Click **"Run with PowerShell"**
4. ⚠️ If you get an execution policy error:
   - Open PowerShell as administrator
   - Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
   - Try again

### **Method 2: PowerShell Command Line**
```powershell
# Open PowerShell as Administrator, then:
cd D:\PythonLibraries\Subtitle
.\install_all_windows.ps1
```

### **Method 3: PowerShell with Specific Parameters**
```powershell
# Prefer a specific install method for all tools
.\install_all_windows.ps1 -FfmpegInstallMethod winget -ToolInstallMethod choco

# Install specific AI backends
.\install_all_windows.ps1 -InstallAiXtts -InstallAiFasterWhisper

# Full control with combined options
.\install_all_windows.ps1 -NoMenu -PythonInstallMethod winget -QuietInstallOutput
```

---

## Diagnosis: Check What the Installer Did

After installation, check the log file:

```powershell
# View installation log
Get-Content .\install_all_windows.log -Tail 50

# Or from PowerShell:
notepad .\install_all_windows.log
```

Look for entries like:
- `"ffmpeg pre-existed"` - was ffmpeg already installed?
- `"install method used: winget"` - which package manager was used?
- `"ffmpeg accessible: True/False"` - is it on PATH in the process?

---

## Installer Improvements (Latest Version)

✅ **FFmpeg PATH Refresh** - After ffmpeg installation, the parent process now refreshes PATH from registry
✅ **ISE Detection** - Script warns if running in PowerShell ISE
✅ **Version Check** - Validates PowerShell version (5.0+)
✅ **Better Verification** - Shows whether tools are accessible after PATH updates
✅ **Helpful Warnings** - Suggests restarting terminal if tools still not found

---

## If Tools Still Don't Work After Installation

1. **Restart your computer** (most reliable)
   - System PATH changes require a new session
   
2. **Or, open a new PowerShell window** and try again

3. **Check the manual PATH section above** and add tool directories yourself

4. **Run the GUI and configure manually**:
   - In Subtitle Tool GUI: **Tools** → **Tooling & Diagnostics**
   - Set paths explicitly for any missing tools

5. **If still stuck**: Report with:
   - `install_all_windows.log` contents
   - Output of `echo $env:Path` in PowerShell
   - Output of tool version commands that fail

---

## Quick Checklist

- [ ] Running PowerShell **Console**, not ISE
- [ ] Running as **Administrator**
- [ ] Script is **UTF-8 encoded** (not modified)
- [ ] Waited for installation to fully complete
- [ ] Opened a **NEW** PowerShell window after install
- [ ] Ran tool version commands to verify
- [ ] Checked **install_all_windows.log** for errors
- [ ] If needed, manually added tool directories to PATH

---

## Related Files

- `install_all_windows.ps1` - Main installer script
- `install_ffmpeg_windows.ps1` - FFmpeg-specific installer
- `install_all_windows.log` - Installer log (created during run)
- `.subtitle_tool_settings.json` - Application settings (includes manual tool paths)

---

## Getting Help

If you encounter issues:

1. Check this guide first (you probably aren't alone!)
2. Examine `install_all_windows.log` for specific error messages
3. Run the GUI and check **Tooling & Diagnostics** tab
4. Try manual PATH configuration if all else fails

