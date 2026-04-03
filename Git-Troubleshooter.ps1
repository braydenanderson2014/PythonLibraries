# ======================================================================
# Git Troubleshooting System
# ======================================================================
# Description: Comprehensive Git error detection and remediation system
# Author: Brayden Anderson
# Date: 2026-01-17
# Purpose: Diagnose and fix common Git repository issues
# ======================================================================

param(
    [string]$RepoUrl,
    [string]$RepoPath = (Get-Location),
    [string]$ErrorType = "auto",
    [switch]$Verbose = $false,
    [switch]$DryRun = $false
)

# ======================================================================
# Color definitions
# ======================================================================
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Info    = "Cyan"
    Debug   = "Magenta"
}

# ======================================================================
# Logging Functions
# ======================================================================
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = if ($Colors.ContainsKey($Level)) { $Colors[$Level] } else { "White" }    
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $color
}

function Write-Success { Write-Log -Message $args[0] -Level "Success" }
function Write-Warning { Write-Log -Message $args[0] -Level "Warning" }
function Write-Error { Write-Log -Message $args[0] -Level "Error" }
function Write-Info { Write-Log -Message $args[0] -Level "Info" }
function Write-Debug { if ($Verbose) { Write-Log -Message $args[0] -Level "Debug" } }

# ======================================================================
# Utility Functions
# ======================================================================
function Test-GitRepository {
    param([string]$Path)
    
    Write-Debug "Testing Git repository at: $Path"
    
    if (-not (Test-Path -Path $Path)) {
        Write-Error "Repository path does not exist: $Path"
        return $false
    }
    
    if (-not (Test-Path -Path "$Path\.git")) {
        Write-Error "Not a Git repository: $Path"
        return $false
    }
    
    Write-Success "Valid Git repository found"
    return $true
}

function Invoke-GitCommand {
    param(
        [string]$Command,
        [string]$WorkingDirectory = $RepoPath
    )
    
    Write-Debug "Executing: git $Command"
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would execute: git $Command"
        return
    }
    
    Push-Location $WorkingDirectory
    try {
        $result = Invoke-Expression "git $Command" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Git command failed (exit code $LASTEXITCODE): git $Command"
            Write-Debug ($result | Out-String)
            return $null
        }
        if ($null -eq $result) {
            return ""
        }
        return $result
    }
    catch {
        Write-Error "Command failed: $_"
        return $null
    }
    finally {
        Pop-Location
    }
}

# ======================================================================
# Diagnostic Functions
# ======================================================================
function Get-GitStatus {
    Write-Info "Scanning Git repository..."
    
    $diagnostics = @{}
    
    # Check basic status
    $status = Invoke-GitCommand "status" | Out-String
    $diagnostics["status"] = $status
    
    # Check for broken refs
    $fsck = Invoke-GitCommand "fsck --full 2>&1" | Out-String
    $diagnostics["fsck"] = $fsck
    
    # Check remote refs
    $remotes = Invoke-GitCommand "remote -v" | Out-String
    $diagnostics["remotes"] = $remotes
    
    # Check branches
    $branches = Invoke-GitCommand "branch -a" | Out-String
    $diagnostics["branches"] = $branches

    # Check merge/cherry-pick/rebase/revert state and unresolved files
    $gitDir = Join-Path $RepoPath ".git"
    $mergeState = @{
        MergeInProgress = (Test-Path (Join-Path $gitDir "MERGE_HEAD"))
        RebaseInProgress = (Test-Path (Join-Path $gitDir "rebase-merge")) -or (Test-Path (Join-Path $gitDir "rebase-apply"))
        CherryPickInProgress = (Test-Path (Join-Path $gitDir "CHERRY_PICK_HEAD"))
        RevertInProgress = (Test-Path (Join-Path $gitDir "REVERT_HEAD"))
        UnmergedFiles = @()
        ConflictMarkerFiles = @()
    }

    $unmergedFiles = Invoke-GitCommand "diff --name-only --diff-filter=U"
    if ($null -ne $unmergedFiles) {
        if ($unmergedFiles -is [array]) {
            $mergeState.UnmergedFiles = @($unmergedFiles | ForEach-Object { $_.ToString().Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        } else {
            $file = $unmergedFiles.ToString().Trim()
            if (-not [string]::IsNullOrWhiteSpace($file)) {
                $mergeState.UnmergedFiles = @($file)
            }
        }
    }

    # Detect unresolved conflict markers that may still exist inside tracked files.
    Push-Location $RepoPath
    try {
        $markerMatches = git grep -l -E "^(<<<<<<<|=======|>>>>>>>)" -- 2>$null
        if ($LASTEXITCODE -eq 0 -and $markerMatches) {
            if ($markerMatches -is [array]) {
                $mergeState.ConflictMarkerFiles = @($markerMatches | ForEach-Object { $_.ToString().Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
            } else {
                $markerFile = $markerMatches.ToString().Trim()
                if (-not [string]::IsNullOrWhiteSpace($markerFile)) {
                    $mergeState.ConflictMarkerFiles = @($markerFile)
                }
            }
        }
    }
    finally {
        Pop-Location
    }

    $diagnostics["merge_state"] = $mergeState
    
    return $diagnostics
}

function Test-GitConfig {
    param([string]$ConfigPath)
    
    Write-Debug "Validating Git config file: $ConfigPath"
    
    if (-not (Test-Path $ConfigPath)) {
        Write-Warning "Config file not found at: $ConfigPath"
        return @{Valid = $false; Error = "missing"}
    }
    
    try {
        # Try to read the config file
        $content = Get-Content $ConfigPath -Raw -ErrorAction Stop
        
        # Check for basic structure issues
        $issues = @()
        
        # Check for unclosed sections
        $openBrackets = ([regex]::Matches($content, '\[')).Count
        $closeBrackets = ([regex]::Matches($content, '\]')).Count
        if ($openBrackets -ne $closeBrackets) {
            $issues += "Unbalanced brackets in config file"
        }
        
        # Check for lines with invalid syntax (basic check)
        $lines = $content -split "`n"
        $lineNum = 0
        foreach ($line in $lines) {
            $lineNum++
            $trimmedLine = $line.Trim()
            
            # Skip empty lines and comments
            if ($trimmedLine -eq "" -or $trimmedLine.StartsWith("#") -or $trimmedLine.StartsWith(";")) {
                continue
            }
            
            # Section headers
            if ($trimmedLine.StartsWith("[")) {
                if (-not $trimmedLine.EndsWith("]")) {
                    $issues += "Line ${lineNum}: Unclosed section header"
                }
                continue
            }
            
            # Config entries should have = sign
            if (-not $trimmedLine.Contains("=")) {
                $issues += "Line ${lineNum}: Invalid config entry (missing '=')"
            }
        }
        
        # Try to parse with git config
        $parseTest = git config --file $ConfigPath --list 2>&1
        if ($LASTEXITCODE -ne 0) {
            $issues += "Git cannot parse config file: $parseTest"
        }
        
        # Check for remote origin configuration
        $remoteUrl = git config --file $ConfigPath --get remote.origin.url 2>$null
        $hasMissingRemote = [string]::IsNullOrWhiteSpace($remoteUrl)
        
        if ($issues.Count -gt 0) {
            return @{Valid = $false; Error = "syntax"; Issues = $issues; MissingRemote = $hasMissingRemote}
        }
        
        if ($hasMissingRemote) {
            return @{Valid = $true; Warning = "missing_remote"}
        }
        
        return @{Valid = $true}
    }
    catch {
        return @{Valid = $false; Error = "read_error"; Exception = $_.Exception.Message}
    }
}

function Find-GitError {
    param([hashtable]$Diagnostics)
    
    Write-Info "Analyzing repository for errors..."
    
    $errors = @()
    
    # Check for config file issues
    $configPath = "$RepoPath\.git\config"
    $configTest = Test-GitConfig -ConfigPath $configPath
    if (-not $configTest.Valid) {
        $errors += "bad_config_file"
        Write-Warning "Detected: Bad .git/config file ($($configTest.Error))"
        if ($configTest.Issues) {
            foreach ($issue in $configTest.Issues) {
                Write-Warning "  - $issue"
            }
        }
    } elseif ($configTest.Warning -eq "missing_remote") {
        $errors += "missing_remote_origin"
        Write-Warning "Detected: Missing remote origin configuration"
    }
    
    # Check for broken refs
    if ($Diagnostics["fsck"] -match "badRefContent|invalid sha1 pointer") {
        $errors += "broken_refs"
        Write-Warning "Detected: Broken reference files"
    }

    # Check for invalid HEAD (often caused by missing or corrupted local branch refs)
    if ($Diagnostics["fsck"] -match "invalid HEAD") {
        $errors += "broken_head_ref"
        Write-Warning "Detected: Invalid HEAD reference"
    }
    
    # Check for ORIG_HEAD issues
    if ($Diagnostics["fsck"] -match "ORIG_HEAD") {
        $errors += "corrupted_orig_head"
        Write-Warning "Detected: Corrupted ORIG_HEAD reference"
    }
    
    # Check for dangling commits
    if ($Diagnostics["fsck"] -match "dangling") {
        $errors += "dangling_objects"
        Write-Warning "Detected: Dangling objects"
    }
    
    # Check for loose objects
    if ($Diagnostics["fsck"] -match "loose") {
        $errors += "loose_objects"
        Write-Warning "Detected: Loose objects"
    }
    
    # Check for remote HEAD issues
    if ($Diagnostics["fsck"] -match "refs/remotes/origin/HEAD") {
        $errors += "remote_head_corruption"
        Write-Warning "Detected: Remote HEAD corruption"
    }
    
    # Check for stale remote refs
    if ($Diagnostics["remotes"] -match "^\[gone\]") {
        $errors += "stale_remote_refs"
        Write-Warning "Detected: Stale remote references"
    }

    # Check for in-progress merge/rebase/cherry-pick/revert states and unresolved files
    $mergeState = $Diagnostics["merge_state"]
    if ($null -ne $mergeState) {
        if ($mergeState.MergeInProgress) {
            $errors += "merge_in_progress"
            Write-Warning "Detected: Merge in progress"
        }
        if ($mergeState.RebaseInProgress) {
            $errors += "rebase_in_progress"
            Write-Warning "Detected: Rebase in progress"
        }
        if ($mergeState.CherryPickInProgress) {
            $errors += "cherry_pick_in_progress"
            Write-Warning "Detected: Cherry-pick in progress"
        }
        if ($mergeState.RevertInProgress) {
            $errors += "revert_in_progress"
            Write-Warning "Detected: Revert in progress"
        }
        if ($mergeState.UnmergedFiles.Count -gt 0) {
            $errors += "unmerged_paths"
            Write-Warning "Detected: Unmerged files in index"
            foreach ($path in $mergeState.UnmergedFiles) {
                Write-Warning "  - $path"
            }
        }
        if ($mergeState.ConflictMarkerFiles.Count -gt 0) {
            $errors += "conflict_markers_present"
            Write-Warning "Detected: Conflict markers remain in tracked files"
            foreach ($path in $mergeState.ConflictMarkerFiles) {
                Write-Warning "  - $path"
            }
        }
    }

    $errors = @($errors | Select-Object -Unique)
    
    if ($errors.Count -eq 0) {
        Write-Success "No common Git errors detected"
        return @("healthy")
    }
    
    return $errors
}

# ======================================================================
# Fix Functions
# ======================================================================
function Repair-BrokenRefs {
    Write-Info "Attempting to fix broken references..."
    
    $gitDir = "$RepoPath\.git"
    
    # Remove corrupted origin/main ref
    if (Test-Path "$gitDir/refs/remotes/origin/main") {
        Write-Warning "Removing corrupted origin/main ref"
        Remove-Item "$gitDir/refs/remotes/origin/main" -Force -ErrorAction SilentlyContinue
    }
    
    # Remove corrupted origin/HEAD ref
    if (Test-Path "$gitDir/refs/remotes/origin/HEAD") {
        Write-Warning "Removing corrupted origin/HEAD ref"
        Remove-Item "$gitDir/refs/remotes/origin/HEAD" -Force -ErrorAction SilentlyContinue
    }

    # Repair local branch ref when HEAD points to an invalid local branch (common with refs/heads/main corruption)
    $branchName = "main"
    $headPath = "$gitDir/HEAD"
    if (Test-Path $headPath) {
        $headContent = (Get-Content $headPath -Raw -ErrorAction SilentlyContinue).Trim()
        if ($headContent -match '^ref:\s+refs/heads/(.+)$') {
            $branchName = $Matches[1]
        }
    }

    $localBranchRef = "$gitDir/refs/heads/$branchName"
    if (Test-Path $localBranchRef) {
        $branchRefValue = (Get-Content $localBranchRef -Raw -ErrorAction SilentlyContinue).Trim()
        $isValidSha = $branchRefValue -match '^[0-9a-fA-F]{40}$' -and $branchRefValue -notmatch '^0{40}$'
        if (-not $isValidSha) {
            Write-Warning "Removing corrupted local branch ref refs/heads/$branchName"
            Remove-Item $localBranchRef -Force -ErrorAction SilentlyContinue
        }
    }

    # Rebuild local branch ref from remote tracking branch when available.
    if (-not $DryRun) {
        $fetchResult = Invoke-GitCommand "fetch origin --prune"
        if ($null -ne $fetchResult) {
            $remoteCommit = git rev-parse --verify "refs/remotes/origin/$branchName" 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($remoteCommit)) {
                Invoke-GitCommand "update-ref refs/heads/$branchName $remoteCommit" | Out-Null
                Invoke-GitCommand "symbolic-ref HEAD refs/heads/$branchName" | Out-Null
                Write-Success "Repaired refs/heads/$branchName from origin/$branchName"
            }
        }
    }
    
    Write-Success "Broken refs cleaned"
}

function Repair-CorruptedOrigHead {
    Write-Info "Fixing corrupted ORIG_HEAD..."
    
    $gitDir = "$RepoPath\.git"
    $origHeadPath = "$gitDir/ORIG_HEAD"
    
    if (Test-Path $origHeadPath) {
        Write-Warning "Removing corrupted ORIG_HEAD"
        Remove-Item $origHeadPath -Force -ErrorAction SilentlyContinue
        Write-Success "ORIG_HEAD removed"
    }
}

function Repair-DanglingObjects {
    Write-Info "Cleaning up dangling objects..."
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would run: git gc --prune=now"
    } else {
        Invoke-GitCommand "gc --prune=now" | Out-Null
        Write-Success "Garbage collection completed"
    }
}

function Repair-LooseObjects {
    Write-Info "Repacking loose objects..."
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would run: git repack -a -d"
    } else {
        Invoke-GitCommand "repack -a -d" | Out-Null
        Write-Success "Objects repacked"
    }
}

function Repair-RemoteHeadCorruption {
    Write-Info "Fixing remote HEAD corruption..."
    
    Invoke-GitCommand "remote prune origin" | Out-Null
    Write-Success "Remote pruned"
}

function Repair-StaleRemoteRefs {
    Write-Info "Removing stale remote references..."
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would run: git remote prune origin"
    } else {
        Invoke-GitCommand "remote prune origin" | Out-Null
        Write-Success "Stale refs removed"
    }
}

function Repair-BadConfigFile {
    Write-Info "Attempting to repair .git/config file..."
    
    $configPath = "$RepoPath\.git\config"
    $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    # Backup existing config
    if (Test-Path $configPath) {
        Write-Info "Backing up config to: $backupPath"
        if (-not $DryRun) {
            Copy-Item $configPath $backupPath -Force
        }
    }
    
    # Try to create a minimal valid config
    Write-Info "Creating minimal valid config file..."
    
    # Extract remote URL if possible from backup
    $remoteUrl = $null
    $userName = $null
    $userEmail = $null
    
    if (Test-Path $configPath) {
        try {
            $content = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
            if ($content -match 'url\s*=\s*(.+)') {
                $remoteUrl = $Matches[1].Trim()
                Write-Info "Extracted remote URL: $remoteUrl"
            }
            if ($content -match 'name\s*=\s*(.+)') {
                $userName = $Matches[1].Trim()
                Write-Info "Extracted user name: $userName"
            }
            if ($content -match 'email\s*=\s*(.+)') {
                $userEmail = $Matches[1].Trim()
                Write-Info "Extracted user email: $userEmail"
            }
        }
        catch {
            Write-Warning "Could not extract config values from corrupted file"
        }
    }
    
    if (-not $DryRun) {
        # Create new minimal config
        $newConfig = @"
[core]
	repositoryformatversion = 0
	filemode = false
	bare = false
	logallrefupdates = true
	symlinks = false
	ignorecase = true
"@
        
        # Add remote if we found one
        if ($remoteUrl) {
            $newConfig += @"
`n[remote "origin"]
	url = $remoteUrl
	fetch = +refs/heads/*:refs/remotes/origin/*
"@
        }
        
        # Add branch config
        $newConfig += @"
`n[branch "main"]
	remote = origin
	merge = refs/heads/main
"@
        
        # Add user config if found
        if ($userName -or $userEmail) {
            $newConfig += "`n[user]"
            if ($userName) { $newConfig += "`n`tname = $userName" }
            if ($userEmail) { $newConfig += "`n`temail = $userEmail" }
        }
        
        # Write new config
        Set-Content -Path $configPath -Value $newConfig -Encoding UTF8
        Write-Success "Created new config file with minimal settings"
        
        # Validate new config
        $validation = Test-GitConfig -ConfigPath $configPath
        if ($validation.Valid) {
            Write-Success "New config file validated successfully"
        } else {
            Write-Warning "New config file may still have issues"
        }
        
        # Try to re-add remote if we couldn't extract URL
        if (-not $remoteUrl) {
            Write-Warning "Remote URL not found in corrupted config."
            $addRemote = Read-Host "Would you like to add a remote URL now? (yes/no)"
            if ($addRemote -eq "yes" -or $addRemote -eq "y") {
                $inputUrl = Read-Host "Enter the repository URL (e.g., https://github.com/user/repo.git)"
                if (-not [string]::IsNullOrWhiteSpace($inputUrl)) {
                    try {
                        git config --file $configPath remote.origin.url $inputUrl
                        git config --file $configPath remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
                        Write-Success "Remote 'origin' added successfully with URL: $inputUrl"
                    }
                    catch {
                        Write-Warning "Failed to add remote: $_"
                    }
                } else {
                    Write-Warning "No URL provided. You can add it later with: git remote add origin <url>"
                }
            } else {
                Write-Info "You can add a remote later with: git remote add origin <repository-url>"
            }
        }
    } else {
        Write-Warning "[DRY RUN] Would backup and recreate .git/config file"
    }
}

function Repair-MissingRemoteOrigin {
    Write-Info "Remote origin configuration is missing..."
    
    $configPath = "$RepoPath\.git\config"
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would prompt for remote URL and add to config"
        return
    }
    
    Write-Warning "No remote 'origin' found in repository."
    $addRemote = Read-Host "Would you like to add a remote URL now? (yes/no)"
    
    if ($addRemote -eq "yes" -or $addRemote -eq "y") {
        $inputUrl = Read-Host "Enter the repository URL (e.g., https://github.com/user/repo.git)"
        
        if (-not [string]::IsNullOrWhiteSpace($inputUrl)) {
            try {
                # Check if origin already exists (shouldn't, but just in case)
                $existingUrl = git config --get remote.origin.url 2>$null
                if ($existingUrl) {
                    Write-Info "Updating existing remote origin URL..."
                    git config remote.origin.url $inputUrl
                } else {
                    Write-Info "Adding new remote origin..."
                    git remote add origin $inputUrl
                }
                
                Write-Success "Remote 'origin' configured with URL: $inputUrl"
                
                # Offer to fetch from remote
                $doFetch = Read-Host "Would you like to fetch from the remote now? (yes/no)"
                if ($doFetch -eq "yes" -or $doFetch -eq "y") {
                    Write-Info "Fetching from origin..."
                    git fetch origin
                    Write-Success "Fetch completed"
                }
            }
            catch {
                Write-Error "Failed to add remote: $_"
            }
        } else {
            Write-Warning "No URL provided. You can add it later with: git remote add origin <url>"
        }
    } else {
        Write-Info "You can add a remote later with: git remote add origin <repository-url>"
    }
}

function Repair-Healthy {
    Write-Success "Repository is healthy - no fixes needed"
}

function Repair-MergeState {
    param(
        [string]$IssueType,
        [hashtable]$Diagnostics
    )

    $mergeState = $Diagnostics["merge_state"]

    Write-Warning "Merge workflow issue detected: $IssueType"
    switch ($IssueType) {
        "merge_in_progress" { Write-Info "Finish the merge with: git add <resolved-files> ; git commit" }
        "rebase_in_progress" { Write-Info "Continue or abort with: git rebase --continue OR git rebase --abort" }
        "cherry_pick_in_progress" { Write-Info "Continue or abort with: git cherry-pick --continue OR git cherry-pick --abort" }
        "revert_in_progress" { Write-Info "Continue or abort with: git revert --continue OR git revert --abort" }
        "unmerged_paths" {
            Write-Info "Resolve unmerged files before other automated repair actions."
            if ($mergeState -and $mergeState.UnmergedFiles.Count -gt 0) {
                Write-Info "Unmerged paths:"
                foreach ($path in $mergeState.UnmergedFiles) {
                    Write-Host "  - $path" -ForegroundColor Yellow
                }
            }
        }
        "conflict_markers_present" {
            Write-Info "Remove conflict markers and stage files to clear index conflicts."
            if ($mergeState -and $mergeState.ConflictMarkerFiles.Count -gt 0) {
                Write-Info "Files with marker patterns:"
                foreach ($path in $mergeState.ConflictMarkerFiles) {
                    Write-Host "  - $path" -ForegroundColor Yellow
                }
            }
        }
    }
}

# ======================================================================
# Recovery Functions
# ======================================================================
function Invoke-FullRecovery {
    Write-Warning "Starting full repository recovery..."
    
    Push-Location $RepoPath
    
    try {
        # Prune remote refs
        Write-Info "Step 1: Pruning remote references..."
        Invoke-GitCommand "remote prune origin" | Out-Null
        
        # Garbage collection
        Write-Info "Step 2: Running garbage collection..."
        Invoke-GitCommand "gc --aggressive --prune=now" | Out-Null
        
        # Verify repository
        Write-Info "Step 3: Verifying repository integrity..."
        $fsckResult = Invoke-GitCommand "fsck --full" | Out-String
        
        if ($fsckResult -match "error") {
            Write-Warning "Repository still has issues after recovery"
            return $false
        }
        
        # Fetch fresh refs
        Write-Info "Step 4: Fetching fresh references from remote..."
        Invoke-GitCommand "fetch origin" | Out-Null
        
        Write-Success "Full recovery completed"
        Pop-Location
        return $true
    }
    catch {
        Write-Error "Recovery failed: $_"
        Pop-Location
        return $false
    }
}

function Invoke-HardReset {
    param([string]$Branch = "main")
    
    Write-Warning "Performing hard reset to origin/$Branch..."
    
    if (-not $DryRun) {
        $confirm = Read-Host "This will discard all local changes. Continue? (yes/no)"
        if ($confirm -ne "yes") {
            Write-Warning "Hard reset cancelled"
            return $false
        }
    }
    
    Invoke-GitCommand "fetch origin" | Out-Null
    Invoke-GitCommand "reset --hard origin/$Branch" | Out-Null
    Invoke-GitCommand "clean -fd" | Out-Null
    
    Write-Success "Hard reset completed"
    return $true
}

# ======================================================================
# Clone Functions
# ======================================================================
function Invoke-FreshClone {
    param([string]$Url)
    
    if (-not $Url) {
        Write-Error "Repository URL is required for fresh clone"
        return $false
    }
    
    Write-Warning "Creating fresh clone..."
    
    $backupPath = "$RepoPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    Write-Info "Backing up current repository to: $backupPath"
    if (-not $DryRun) {
        Move-Item $RepoPath $backupPath -ErrorAction SilentlyContinue
    }
    
    Write-Info "Cloning repository from: $Url"
    if (-not $DryRun) {
        git clone $Url $RepoPath | Out-Null
        Write-Success "Fresh clone completed. Backup saved to: $backupPath"
    } else {
        Write-Warning "[DRY RUN] Would clone $Url to $RepoPath"
    }
    
    return $true
}

# ======================================================================
# Menu and Interactive Functions
# ======================================================================
function Show-Menu {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Git Troubleshooting System" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select an action:" -ForegroundColor Yellow
    Write-Host "  1. Auto-diagnose and fix errors"
    Write-Host "  2. Run full repository recovery"
    Write-Host "  3. Hard reset to origin/main"
    Write-Host "  4. Create fresh clone"
    Write-Host "  5. View detailed diagnostics"
    Write-Host "  6. Exit"
    Write-Host ""
}

function Show-Diagnostics {
    param([hashtable]$Diagnostics)
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Detailed Diagnostics Report" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "GIT STATUS:" -ForegroundColor Yellow
    Write-Host $Diagnostics["status"]
    
    Write-Host "FSCK RESULTS:" -ForegroundColor Yellow
    Write-Host $Diagnostics["fsck"]
    
    Write-Host "REMOTES:" -ForegroundColor Yellow
    Write-Host $Diagnostics["remotes"]
    
    Write-Host "BRANCHES:" -ForegroundColor Yellow
    Write-Host $Diagnostics["branches"]

    Write-Host "MERGE STATE:" -ForegroundColor Yellow
    $mergeState = $Diagnostics["merge_state"]
    if ($null -eq $mergeState) {
        Write-Host "Unavailable"
    } else {
        Write-Host "Merge in progress: $($mergeState.MergeInProgress)"
        Write-Host "Rebase in progress: $($mergeState.RebaseInProgress)"
        Write-Host "Cherry-pick in progress: $($mergeState.CherryPickInProgress)"
        Write-Host "Revert in progress: $($mergeState.RevertInProgress)"
        Write-Host "Unmerged files: $($mergeState.UnmergedFiles.Count)"
        Write-Host "Conflict marker files: $($mergeState.ConflictMarkerFiles.Count)"
    }
}

# ======================================================================
# Main Execution
# ======================================================================
function Invoke-GitTroubleshooter {
    Write-Host ""
    Write-Host "Git Troubleshooting System Starting..." -ForegroundColor Green
    Write-Host ""
    
    # Validate repository
    if (-not (Test-GitRepository -Path $RepoPath)) {
        Write-Error "Cannot proceed without valid Git repository"
        exit 1
    }
    
    Write-Info "Repository path: $RepoPath"
    
    # Auto-detect errors
    $diagnostics = Get-GitStatus
    $detectedErrors = Find-GitError -Diagnostics $diagnostics
    
    Write-Info "Detected issues: $($detectedErrors -join ', ')"

    $mergeRelatedIssues = @("merge_in_progress", "rebase_in_progress", "cherry_pick_in_progress", "revert_in_progress", "unmerged_paths", "conflict_markers_present")
    
    # Execute fixes based on detected errors
    foreach ($issueType in $detectedErrors) {
        switch ($issueType) {
            "bad_config_file" { Repair-BadConfigFile }
            "missing_remote_origin" { Repair-MissingRemoteOrigin }
            "broken_refs" { Repair-BrokenRefs }
            "broken_head_ref" { Repair-BrokenRefs }
            "corrupted_orig_head" { Repair-CorruptedOrigHead }
            "dangling_objects" { Repair-DanglingObjects }
            "loose_objects" { Repair-LooseObjects }
            "remote_head_corruption" { Repair-RemoteHeadCorruption }
            "stale_remote_refs" { Repair-StaleRemoteRefs }
            "merge_in_progress" { Repair-MergeState -IssueType $issueType -Diagnostics $diagnostics }
            "rebase_in_progress" { Repair-MergeState -IssueType $issueType -Diagnostics $diagnostics }
            "cherry_pick_in_progress" { Repair-MergeState -IssueType $issueType -Diagnostics $diagnostics }
            "revert_in_progress" { Repair-MergeState -IssueType $issueType -Diagnostics $diagnostics }
            "unmerged_paths" { Repair-MergeState -IssueType $issueType -Diagnostics $diagnostics }
            "conflict_markers_present" { Repair-MergeState -IssueType $issueType -Diagnostics $diagnostics }
            "healthy" { Repair-Healthy }
        }
    }
    
    # Attempt to fetch latest changes
    $hasMergeStateBlockers = ($detectedErrors | Where-Object { $mergeRelatedIssues -contains $_ }).Count -gt 0
    if ($hasMergeStateBlockers) {
        Write-Warning "Skipping fetch: repository has active merge workflow conflicts that must be resolved first."
    }
    elseif ($detectedErrors -notcontains "healthy") {
        Write-Info "Attempting to fetch latest changes..."
        $fetchResult = Invoke-GitCommand "fetch origin"
        
        if ($null -ne $fetchResult) {
            Write-Success "Successfully fetched latest changes"
        } else {
            Write-Warning "Fetch operation encountered issues"
        }
    }
    
    Write-Host ""
    Write-Success "Troubleshooting completed!"
    Write-Host ""
}

# ======================================================================
# Interactive Mode
# ======================================================================
function Invoke-InteractiveMode {
    do {
        Show-Menu
        $choice = Read-Host "Enter your choice (1-6)"
        
        switch ($choice) {
            "1" {
                Write-Host ""
                Invoke-GitTroubleshooter
            }
            "2" {
                Write-Host ""
                Invoke-FullRecovery | Out-Null
            }
            "3" {
                Write-Host ""
                $branch = Read-Host "Enter branch name (default: main)"
                if ([string]::IsNullOrWhiteSpace($branch)) { $branch = "main" }
                Invoke-HardReset -Branch $branch | Out-Null
            }
            "4" {
                Write-Host ""
                if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
                    $RepoUrl = Read-Host "Enter repository URL"
                }
                Invoke-FreshClone -Url $RepoUrl | Out-Null
            }
            "5" {
                Write-Host ""
                $diagnostics = Get-GitStatus
                Show-Diagnostics -Diagnostics $diagnostics
            }
            "6" {
                Write-Success "Exiting Git Troubleshooter"
                exit 0
            }
            default {
                Write-Error "Invalid choice. Please try again."
            }
        }
    } while ($true)
}

# ======================================================================
# Script Entry Point
# ======================================================================
if ($ErrorType -eq "auto") {
    # Auto-mode: detect and fix
    Invoke-GitTroubleshooter
} else {
    # Specific error mode (extensible)
    switch ($ErrorType) {
        "interactive" { Invoke-InteractiveMode }
        "full-recovery" { Invoke-FullRecovery }
        "hard-reset" { Invoke-HardReset }
        "fresh-clone" { Invoke-FreshClone -Url $RepoUrl }
        default { 
            Write-Error "Unknown error type: $ErrorType"
            Write-Info "Valid options: auto, interactive, full-recovery, hard-reset, fresh-clone"
        }
    }
}

Write-Debug "Script execution completed"
