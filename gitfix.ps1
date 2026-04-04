# PowerShell Script to Fix Git HEAD Errors
# Description: Removes corrupted Git HEAD reference files and pulls latest changes
# Author: Brayden Anderson
# Date: 2026-01-17

param(
    [string]$Branch = "main"
)

Write-Host "Fixing Git HEAD errors and config issues..." -ForegroundColor Green

function Get-MergeIssueState {
    $gitDir = ".git"
    $state = @{
        MergeInProgress = (Test-Path (Join-Path $gitDir "MERGE_HEAD"))
        RebaseInProgress = (Test-Path (Join-Path $gitDir "rebase-merge")) -or (Test-Path (Join-Path $gitDir "rebase-apply"))
        CherryPickInProgress = (Test-Path (Join-Path $gitDir "CHERRY_PICK_HEAD"))
        RevertInProgress = (Test-Path (Join-Path $gitDir "REVERT_HEAD"))
        UnmergedFiles = @()
        ConflictMarkerFiles = @()
    }

    $unmerged = git diff --name-only --diff-filter=U 2>$null
    if ($LASTEXITCODE -eq 0 -and $unmerged) {
        if ($unmerged -is [array]) {
            $state.UnmergedFiles = @($unmerged | ForEach-Object { $_.ToString().Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        } else {
            $entry = $unmerged.ToString().Trim()
            if (-not [string]::IsNullOrWhiteSpace($entry)) {
                $state.UnmergedFiles = @($entry)
            }
        }
    }

    $markerMatches = git grep -l -E "^(<<<<<<<|=======|>>>>>>>)" -- 2>$null
    if ($LASTEXITCODE -eq 0 -and $markerMatches) {
        if ($markerMatches -is [array]) {
            $state.ConflictMarkerFiles = @($markerMatches | ForEach-Object { $_.ToString().Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        } else {
            $entry = $markerMatches.ToString().Trim()
            if (-not [string]::IsNullOrWhiteSpace($entry)) {
                $state.ConflictMarkerFiles = @($entry)
            }
        }
    }

    return $state
}

function Show-MergeIssueSummary {
    param([hashtable]$State)

    Write-Host "Merge workflow issue detected. Resolve this first:" -ForegroundColor Yellow
    if ($State.MergeInProgress) { Write-Host " - Merge in progress (MERGE_HEAD present)" -ForegroundColor Yellow }
    if ($State.RebaseInProgress) { Write-Host " - Rebase in progress" -ForegroundColor Yellow }
    if ($State.CherryPickInProgress) { Write-Host " - Cherry-pick in progress" -ForegroundColor Yellow }
    if ($State.RevertInProgress) { Write-Host " - Revert in progress" -ForegroundColor Yellow }

    if ($State.UnmergedFiles.Count -gt 0) {
        Write-Host "Unmerged files:" -ForegroundColor Yellow
        foreach ($path in $State.UnmergedFiles) {
            Write-Host " - $path" -ForegroundColor Gray
        }
    }

    if ($State.ConflictMarkerFiles.Count -gt 0) {
        Write-Host "Files containing conflict markers:" -ForegroundColor Yellow
        foreach ($path in $State.ConflictMarkerFiles) {
            Write-Host " - $path" -ForegroundColor Gray
        }
    }

    Write-Host "Suggested commands:" -ForegroundColor Cyan
    Write-Host " - git status"
    Write-Host " - git add <resolved-files>"
    Write-Host " - git commit (merge) OR git rebase --continue OR git cherry-pick --continue"
}

$mergeState = Get-MergeIssueState
$hasMergeIssues = $mergeState.MergeInProgress -or $mergeState.RebaseInProgress -or $mergeState.CherryPickInProgress -or $mergeState.RevertInProgress -or $mergeState.UnmergedFiles.Count -gt 0

if (-not $hasMergeIssues -and $mergeState.ConflictMarkerFiles.Count -gt 0) {
    Write-Host "Conflict-marker patterns were found in tracked files, but Git reports no active merge/rebase/cherry-pick/revert and no unmerged index entries." -ForegroundColor Yellow
    Write-Host "Proceeding with repair steps. Review these files manually if needed:" -ForegroundColor Yellow
    foreach ($path in $mergeState.ConflictMarkerFiles) {
        Write-Host " - $path" -ForegroundColor Gray
    }
}

if ($hasMergeIssues) {
    Show-MergeIssueSummary -State $mergeState
    Write-Host "Stopping gitfix.ps1 to avoid making repository state worse while merge issues are active." -ForegroundColor Red
    exit 1
}

function Test-ValidRefSha {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    if ($Value -notmatch '^[0-9a-fA-F]{40}$') { return $false }
    if ($Value -match '^0{40}$') { return $false }
    return $true
}

# Check and fix .git/config file
$configPath = ".git\config"
if (Test-Path $configPath) {
    Write-Host "Validating .git/config file..." -ForegroundColor Cyan
    
    # Try to parse config
    $configTest = git config --file $configPath --list 2>&1
    $configValid = ($LASTEXITCODE -eq 0)
    
    if (-not $configValid) {
        Write-Host "Detected bad .git/config file. Creating backup and repair..." -ForegroundColor Yellow
        
        # Backup corrupted config
        $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $configPath $backupPath -Force
        Write-Host "Backup created: $backupPath" -ForegroundColor Gray
        
        # Extract remote URL if possible
        $content = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
        $remoteUrl = if ($content -match 'url\s*=\s*(.+)') { $Matches[1].Trim() } else { $null }
        
        # Create minimal valid config
        $newConfig = @"
[core]
	repositoryformatversion = 0
	filemode = false
	bare = false
	logallrefupdates = true
	symlinks = false
	ignorecase = true
"@
        
        if ($remoteUrl) {
            $newConfig += @"
`n[remote "origin"]
	url = $remoteUrl
	fetch = +refs/heads/*:refs/remotes/origin/*
`n[branch "$Branch"]
	remote = origin
	merge = refs/heads/$Branch
"@
            Write-Host "Preserved remote URL: $remoteUrl" -ForegroundColor Gray
        }
        
        Set-Content -Path $configPath -Value $newConfig -Encoding UTF8
        Write-Host "Config file repaired successfully!" -ForegroundColor Green
        
        # Prompt for remote URL if not found
        if (-not $remoteUrl) {
            Write-Host "Remote URL not found in corrupted config." -ForegroundColor Yellow
            $addRemote = Read-Host "Would you like to add a remote URL now? (yes/no)"
            if ($addRemote -eq "yes" -or $addRemote -eq "y") {
                $inputUrl = Read-Host "Enter the repository URL (e.g., https://github.com/user/repo.git)"
                if (-not [string]::IsNullOrWhiteSpace($inputUrl)) {
                    git remote add origin $inputUrl
                    Write-Host "Remote 'origin' added successfully with URL: $inputUrl" -ForegroundColor Green
                } else {
                    Write-Host "No URL provided. You can add it later with: git remote add origin <url>" -ForegroundColor Yellow
                }
            } else {
                Write-Host "You can add a remote later with: git remote add origin <repository-url>" -ForegroundColor Gray
            }
        }
    } else {
        # Config is valid, check if remote origin exists
        $remoteUrl = git config --get remote.origin.url 2>$null
        if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
            Write-Host "Config file is valid but missing remote origin." -ForegroundColor Yellow
            $addRemote = Read-Host "Would you like to add a remote URL now? (yes/no)"
            if ($addRemote -eq "yes" -or $addRemote -eq "y") {
                $inputUrl = Read-Host "Enter the repository URL (e.g., https://github.com/user/repo.git)"
                if (-not [string]::IsNullOrWhiteSpace($inputUrl)) {
                    git remote add origin $inputUrl
                    Write-Host "Remote 'origin' added successfully with URL: $inputUrl" -ForegroundColor Green
                } else {
                    Write-Host "No URL provided. You can add it later with: git remote add origin <url>" -ForegroundColor Yellow
                }
            } else {
                Write-Host "You can add a remote later with: git remote add origin <repository-url>" -ForegroundColor Gray
            }
        } else {
            Write-Host "Config file is valid with remote: $remoteUrl" -ForegroundColor Green
        }
    }
}

# Remove corrupted HEAD reference files
Remove-Item .git/ORIG_HEAD -Force -ErrorAction SilentlyContinue
Remove-Item .git/refs/remotes/origin/HEAD -Force -ErrorAction SilentlyContinue

Write-Host "Corrupted HEAD refs removed." -ForegroundColor Yellow

# Repair broken local branch ref when needed (e.g., refs/heads/main bad/empty).
$localBranchRef = ".git/refs/heads/$Branch"
$needsLocalRefRepair = $false

if (Test-Path $localBranchRef) {
    $localRefValue = (Get-Content $localBranchRef -Raw -ErrorAction SilentlyContinue).Trim()
    if (-not (Test-ValidRefSha -Value $localRefValue)) {
        $backupPath = "$localBranchRef.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $localBranchRef $backupPath -Force -ErrorAction SilentlyContinue
        Remove-Item $localBranchRef -Force -ErrorAction SilentlyContinue
        Write-Host "Removed corrupted local ref and created backup: $backupPath" -ForegroundColor Yellow
        $needsLocalRefRepair = $true
    }
}

git rev-parse --verify "refs/heads/$Branch" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $needsLocalRefRepair = $true
}

if ($needsLocalRefRepair) {
    Write-Host "Rebuilding refs/heads/$Branch from origin/$Branch..." -ForegroundColor Cyan

    git fetch origin --prune
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to fetch from origin while repairing refs." -ForegroundColor Red
        exit 1
    }

    $remoteCommit = (git rev-parse --verify "refs/remotes/origin/$Branch" 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteCommit)) {
        $remoteLine = (git ls-remote --heads origin $Branch 2>$null | Select-Object -First 1)
        if (-not [string]::IsNullOrWhiteSpace($remoteLine)) {
            $remoteCommit = ($remoteLine -split "`t")[0]
        }
    }

    if ([string]::IsNullOrWhiteSpace($remoteCommit)) {
        Write-Host "Could not resolve origin/$Branch commit. Ref repair aborted." -ForegroundColor Red
        exit 1
    }

    git update-ref "refs/heads/$Branch" $remoteCommit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to recreate refs/heads/$Branch." -ForegroundColor Red
        exit 1
    }

    git symbolic-ref HEAD "refs/heads/$Branch"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to repoint HEAD to refs/heads/$Branch." -ForegroundColor Red
        exit 1
    }

    Write-Host "Local branch ref repaired to commit $remoteCommit" -ForegroundColor Green
}

# Pull latest changes
Write-Host "Pulling latest changes from $Branch branch..." -ForegroundColor Green
git pull --ff-only origin $Branch

if ($LASTEXITCODE -ne 0) {
    Write-Host "Git pull failed. Repository may still need manual intervention." -ForegroundColor Red
    exit 1
}

Write-Host "Git repository fixed and updated!" -ForegroundColor Green