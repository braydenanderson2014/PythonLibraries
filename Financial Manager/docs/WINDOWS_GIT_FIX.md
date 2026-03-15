# 🪟 WINDOWS GIT CORRUPTION FIX

## ⚠️ READ THIS IF GIT KEEPS CORRUPTING ON WINDOWS

This file contains the fix for recurring Git corruption issues on your Windows machine.

---

## 🎯 The Problem

Git corruption happens on Windows due to:
- Windows Defender scanning `.git` folder during operations
- Long path limitations (260 characters)
- File system monitoring conflicts
- OneDrive folder interference (even when disabled)

---

## ✅ THE FIX - Run These Commands

### **STEP 1: Run PowerShell as Administrator**

Right-click PowerShell → "Run as Administrator"

```powershell
# 1. Windows Defender Exclusion (Replace path if your repo is elsewhere)
Add-MpPreference -ExclusionPath "$env:USERPROFILE\OneDrive\Documents\GitHub\SystemCommands\.git"

# 2. Enable Long Paths in Windows Registry
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# 3. Enable Long Paths in Git
git config --system core.longpaths true

# 4. Verify Defender Exclusion
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath

Write-Host "✓ All admin tasks complete. RESTART REQUIRED!" -ForegroundColor Green
```

### **STEP 2: Run in Regular PowerShell or Git Bash**

```bash
# Git Windows Optimizations
git config --global core.fsmonitor false
git config --global core.filesRefLockTimeout 10000
git config --global core.autocrlf true
git config --global core.fscache false

# Verify settings
echo "✓ Git configs applied!"
git config --global --list | grep core
```

### **STEP 3: RESTART YOUR COMPUTER**

Required for registry changes to take effect.

---

## 🔍 Verify It Worked

After restart, run these to verify:

```bash
# Check Git configs
git config --global --list | grep core

# Should see:
# core.longpaths=true
# core.fsmonitor=false
# core.filesRefLockTimeout=10000
# core.autocrlf=true
# core.fscache=false
```

**In PowerShell:**
```powershell
# Check Defender exclusion
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
# Should show your .git folder path
```

---

## 🚨 If Corruption Still Happens

### Quick Recovery Script

Save this as `fix_git.bat` in your repo root:

```batch
@echo off
echo === Git Recovery for Windows ===

REM Close VS Code and GitHub Desktop first!
echo Close VS Code and GitHub Desktop, then press any key...
pause

REM Fetch from remote
echo Fetching from remote...
git fetch origin

REM Reset to remote main
echo Resetting to origin/main...
git reset --hard origin/main

echo.
echo ✓ Recovery complete!
pause
```

Double-click when corruption happens.

---

## 📋 What These Commands Do

### Windows Defender Exclusion
- Stops Defender from scanning `.git` folder
- Prevents file locking during Git operations
- **Most important fix**

### Long Paths
- Allows paths longer than 260 characters
- Prevents silent failures in deep folder structures
- Required for `Python Projects/Financial Manager/...` paths

### Git Optimizations
- `core.fsmonitor false` - Disables filesystem monitoring (can cause locks)
- `core.filesRefLockTimeout 10000` - Wait 10 seconds for locks (instead of failing immediately)
- `core.autocrlf true` - Windows-friendly line endings
- `core.fscache false` - Disables Git's file cache (can get stale on Windows)

---

## 🎯 Best Practices

### Before Leaving Work (Codespace):
1. `git add . && git commit && git push`
2. Verify: `git status` (should be clean)
3. Go to https://github.com/codespaces
4. Stop codespace (don't just close tab)
5. Wait for "Stopped" status

### Before Starting at Home (Windows):
1. Verify Codespace is stopped
2. Open GitHub Desktop
3. Let it fetch automatically
4. Pull changes
5. Open VS Code

### Before Leaving Home (Windows):
1. Save all files in VS Code
2. **Close VS Code completely**
3. Wait 5 seconds
4. Open GitHub Desktop
5. Commit and Push
6. Verify push succeeded
7. Close GitHub Desktop

---

## ⚠️ Critical Rules

1. ✅ **ALWAYS** close VS Code before using GitHub Desktop for Git operations
2. ✅ **ALWAYS** verify Codespace is stopped before pulling at home
3. ✅ **NEVER** have both VS Code and GitHub Desktop open simultaneously
4. ✅ **ALWAYS** commit and push before switching machines

---

## 🔧 Troubleshooting

### Check if OneDrive is Really Disabled

```powershell
Get-Process | Where-Object {$_.Name -like "*OneDrive*"}
Get-Service | Where-Object {$_.DisplayName -like "*OneDrive*"}
```

If these return anything, OneDrive is still running in background.

### Check What's Locking Git Files

Download [Handle from Sysinternals](https://learn.microsoft.com/en-us/sysinternals/downloads/handle)

```powershell
handle.exe .git
```

Shows which processes are accessing your `.git` folder.

---

## 📞 Still Having Issues?

If corruption continues after applying all fixes:

1. **Move repo out of OneDrive folder**
   ```bash
   # Move to: C:\Code\SystemCommands
   # Clone fresh to new location
   ```

2. **Use only Git CLI instead of GitHub Desktop**
   ```bash
   # In VS Code terminal:
   git add .
   git commit -m "Your message"
   git push
   ```

3. **Check for antivirus interference**
   - Exclude repo from any third-party antivirus
   - Disable real-time scanning for developer folders

---

**Status:** Apply these fixes and test for a few days. Corruption should stop! 🎯
