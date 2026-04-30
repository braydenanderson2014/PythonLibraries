# Subtitle Tool Installer - Why It Failed and How to Fix It

## Quick Answer: What Went Wrong?

Your installer failed with a PowerShell error because **tools weren't being added to your system PATH** after installation. This turned into a parsing error when the script tried to detect the tools.

**The Fix**: The installer now **explicitly updates the system PATH** after installing tools. You need to **download the latest version** and run it correctly.

---

## How to Run the Installer (The RIGHT Way)

### ⚠️ Common Mistake #1: Running in PowerShell ISE
**WRONG** ❌:
- Opening PowerShell ISE and running the script from there
- ISE has different execution rules and causes weird errors

**RIGHT** ✅:
- Use the regular **PowerShell Console**

### ⚠️ Common Mistake #2: Not Running as Administrator
**WRONG** ❌:
- Double-clicking the script
- Running from a regular (non-admin) PowerShell window
- Installing tools requires admin privileges

**RIGHT** ✅:
- Run PowerShell **as Administrator**

### Step-by-Step: The Correct Way

1. **Open PowerShell Console as Administrator**
   - Press `Win + R`
   - Type: `powershell`
   - **Right-click the PowerShell icon in the results**
   - Select **"Run as administrator"**
   - Click **Yes** if prompted

2. **Navigate to the Subtitle folder**
   ```powershell
   cd D:\PythonLibraries\Subtitle
   ```

3. **Download the latest version** (if you haven't already)
   ```powershell
   git pull
   ```
   Or download the latest ZIP from the repository

4. **Run the installer**
   ```powershell
   .\install_all_windows.ps1
   ```
   
   This should display an interactive menu. Choose your options and proceed.

5. **Wait for it to complete**
   - Installation can take 10-30 minutes depending on what's being installed
   - Let it finish without interrupting

---

## After Installation: Verify It Worked

**IMPORTANT**: Close PowerShell and open a **NEW** PowerShell window. Then run:

```powershell
# Check ffmpeg
ffmpeg -version

# Check other tools (if you installed them)
ffprobe -version
mkvmerge --version
HandBrakeCLI --version
```

These should all show version information, NOT an error like "command not found".

If they show version info: ✅ **Success!**  
If they show "command not found": ❌ See the troubleshooting section below

---

## If Tools Still Don't Work

### Option 1: Restart Your Computer (Easiest)
Sometimes Windows takes a restart to fully register PATH changes:
1. Save your work
2. Restart your computer
3. Open PowerShell and try the tool commands again

### Option 2: Manual PATH Configuration (If Option 1 didn't work)

1. Press `Win + X` and select **System**
2. Click **Advanced system settings** on the left
3. Click **Environment Variables** button at the bottom right
4. Under "User variables", find a variable named **Path**
   - If it doesn't exist, click **New** first
5. Click **Edit**
6. Click **New** and add the tool directory:
   - For ffmpeg: `C:\Users\YOUR_USERNAME\AppData\Local\Packages\Gyan\ffmpeg\bin`
   - Or wherever the tools are installed (check Program Files folder)
7. Click **OK** on all dialogs
8. **Close ALL PowerShell windows**
9. Open a new PowerShell and try again

### Option 3: Re-run the Installer
If manual PATH didn't work:
1. Close all PowerShell windows
2. Run the installer again (following the correct steps above)
3. This time, let it auto-configure paths

---

## Checking What Went Wrong

If you want to see what the installer did:

```powershell
# View the installation log
notepad .\install_all_windows.log
```

Look for these sections:
- `"ffmpeg installation"` - Did ffmpeg install successfully?
- `"ffmpeg accessible"` - Is ffmpeg on the PATH now?
- `"install method used"` - Which package manager was used?

If it says `"ffmpeg accessible: True"` then tools ARE on the PATH ✅

---

## Common Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| "Command not found" for ffmpeg | Restart PowerShell or computer |
| "PowerShell ISE may cause issues" warning | Close ISE, use PowerShell Console instead |
| "Access denied" errors | Run PowerShell as Administrator |
| Script won't run / "execution policy" error | Right-click script → "Run with PowerShell" |
| Tools installed but still not working | Restart computer, then try again |

---

## Still Stuck?

1. **Check this guide first** - your issue is probably listed above
2. **Check the detailed troubleshooting guide**: `INSTALLER_TROUBLESHOOTING.md`
3. **You can manually set tool paths** in the Subtitle Tool GUI:
   - Run the tool: `python subtitle_tool.py`
   - Go to **Tools** → **Tooling & Diagnostics**
   - Manually set the path to each tool
   - This bypasses the PATH issue entirely

---

## What Changed in the Latest Version?

✅ **Installer is now smarter**:
- Automatically refreshes system PATH after installing tools
- Warns you if running in the wrong environment
- Tells you what to do if tools aren't accessible

✅ **Your job**: 
- Run it the right way (PowerShell Console, as Admin)
- Verify tools work in a new terminal window
- Restart if needed

---

## TL;DR (Too Long; Didn't Read)

1. Open **PowerShell Console** (not ISE)
2. Right-click → **Run as Administrator**
3. Run: `cd D:\PythonLibraries\Subtitle && .\install_all_windows.ps1`
4. Wait for it to finish
5. Close PowerShell and open a new window
6. Test: `ffmpeg -version` (should work)
7. If not, restart your computer and try again

---

**Questions?** Check `INSTALLER_TROUBLESHOOTING.md` for detailed help.

