param(
    [switch]$NoPause,
    [switch]$IncludeDev,
    [switch]$ForceRecreateVenv,
    [string]$PythonCommand = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

trap {
    Write-Host ""
    Write-Host "=== INSTALLATION FAILED ===" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    if (-not $NoPause) {
        Read-Host "Press Enter to close"
    }
    exit 1
}

function Write-StatusOK {
    param([string]$Message)
    Write-Host "$Message..." -NoNewline -ForegroundColor White
    Write-Host " [ " -NoNewline -ForegroundColor White
    Write-Host "OK" -NoNewline -ForegroundColor Green
    Write-Host " ]" -ForegroundColor White
}

function Test-CommandAvailable {
    param([string]$CommandName)
    return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Resolve-PythonCommand {
    param([string]$RequestedCommand)

    if ($RequestedCommand) {
        return @($RequestedCommand)
    }

    $candidates = @(
        @("py", "-3.13"),
        @("py", "-3.12"),
        @("py", "-3.11"),
        @("py", "-3"),
        @("python")
    )

    foreach ($candidate in $candidates) {
        $commandName = $candidate[0]
        if (-not (Test-CommandAvailable $commandName)) {
            continue
        }

        try {
            if ($candidate.Length -gt 1) {
                $null = & $candidate[0] $candidate[1..($candidate.Length - 1)] -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            } else {
                $null = & $candidate[0] -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            }
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }

    throw "Python 3.11 or newer was not found. Install Python first, then rerun this script."
}

function Invoke-Python {
    param(
        [string[]]$CommandParts,
        [string[]]$Arguments
    )

    if ($CommandParts.Length -gt 1) {
        & $CommandParts[0] $CommandParts[1..($CommandParts.Length - 1)] @Arguments
    } else {
        & $CommandParts[0] @Arguments
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $($CommandParts -join ' ') $($Arguments -join ' ')"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptDir
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$pythonCommandParts = Resolve-PythonCommand -RequestedCommand $PythonCommand

Write-Host "=== OtterForge Windows Installer ===" -ForegroundColor Cyan
Write-Host "Project root: $projectRoot"
Write-Host ""

Push-Location $projectRoot
try {
    if ($ForceRecreateVenv -and (Test-Path $venvPath)) {
        Write-Host "Removing existing .venv..." -ForegroundColor Yellow
        Remove-Item -Path $venvPath -Recurse -Force
    }

    if (-not (Test-Path $venvPython)) {
        Write-Host "Creating local virtual environment in .venv..." -ForegroundColor Yellow
        Invoke-Python -CommandParts $pythonCommandParts -Arguments @("-m", "venv", ".venv")
        Write-StatusOK "Created local virtual environment"
    } else {
        Write-StatusOK "Local virtual environment already exists"
    }

    Write-Host "Upgrading pip, setuptools, and wheel..." -ForegroundColor Yellow
    Invoke-Python -CommandParts @($venvPython) -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    Write-StatusOK "Packaging tools upgraded"

    $extras = if ($IncludeDev) { "full" } else { "ui,assets" }
    Write-Host "Installing OtterForge with extras [$extras]..." -ForegroundColor Yellow
    Invoke-Python -CommandParts @($venvPython) -Arguments @("-m", "pip", "install", "-e", ".[$extras]")
    Write-StatusOK "OtterForge dependencies installed"

    Write-Host "Verifying imports..." -ForegroundColor Yellow
    Invoke-Python -CommandParts @($venvPython) -Arguments @(
        "-c",
        "import otterforge; from otterforge.ui.main_window import PYQT_AVAILABLE; import PIL; print('PyQt6 available:', PYQT_AVAILABLE); print('Pillow available:', bool(PIL))"
    )
    Write-StatusOK "Import verification completed"

    Write-Host ""
    Write-Host "Installation complete." -ForegroundColor Green
    Write-Host "Use .venv\\Scripts\\python.exe -m otterforge ui or launch_ui.bat to start the UI." -ForegroundColor Green
} finally {
    Pop-Location
}

if (-not $NoPause) {
    Read-Host "Press Enter to close"
}

exit 0