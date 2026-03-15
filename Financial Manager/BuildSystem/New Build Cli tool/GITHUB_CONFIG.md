# GitHub Configuration for BuildCLI

This document explains how to configure GitHub integration for BuildCLI module management.

## Configuration Files

### 1. `github_config_template.json`
This is the user template that provides all available configuration options with empty/default values. Users can copy this to `~/.buildcli/github_config.json` and customize it.

### 2. `github_config_program.json`
This is the program's default configuration used when no user configuration is found. It contains working defaults and example module sources.

## Setting Up GitHub Integration

### Quick Setup

1. **Initialize GitHub configuration:**
   ```bash
   buildcli github-config-init
   ```

2. **Edit the configuration file:**
   ```bash
   # The file will be created at ~/.buildcli/github_config.json
   # Edit it with your preferred text editor
   ```

3. **Set your GitHub token (optional but recommended):**
   ```bash
   # Set environment variable
   export BUILDCLI_GITHUB_TOKEN="your_github_token_here"
   
   # Or edit the config file directly
   buildcli config-set github.personal_access_token "your_token_here"
   ```

### Configuration Options

#### GitHub API Settings
```json
{
  "github": {
    "personal_access_token": "ghp_xxxxxxxxxxxx",
    "username": "your_username",
    "api": {
      "base_url": "https://api.github.com",
      "timeout": 30,
      "max_retries": 3
    }
  }
}
```

#### Module Sources
```json
{
  "module_sources": {
    "primary": {
      "type": "github",
      "url": "https://github.com/buildcli-official/buildcli-modules",
      "branch": "main",
      "enabled": true,
      "trusted": true,
      "manifest_url": "https://raw.githubusercontent.com/buildcli-official/buildcli-modules/main/modules.json"
    }
  }
}
```

#### Security Settings
```json
{
  "security": {
    "verify_signatures": true,
    "allowed_authors": ["buildcli-official", "buildcli-verified"],
    "blocked_authors": [],
    "require_code_review": true,
    "scan_for_vulnerabilities": true,
    "max_module_size_mb": 50,
    "allowed_file_extensions": [".py", ".json", ".md", ".txt", ".yml", ".yaml"]
  }
}
```

## Using GitHub Integration

### List Available Modules
```bash
# List from primary source
buildcli list-remote-modules

# List from specific source
buildcli list-remote-modules community
```

### Install Modules
```bash
# Install from primary source
buildcli install-module git

# Install from specific source
buildcli install-module docker community
```

### Update Modules
```bash
# Update a specific module
buildcli update-module git

# Update all modules (future feature)
buildcli update-all-modules
```

### Manage Sources
```bash
# List configured sources
buildcli list-sources

# Show current configuration
buildcli config-show github
```

## Authentication

### Personal Access Token
For private repositories or higher rate limits, configure a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with appropriate permissions:
   - `public_repo` (for public repositories)
   - `repo` (for private repositories)
3. Set the token in your configuration or environment variable

### Environment Variables
```bash
# Primary method
export BUILDCLI_GITHUB_TOKEN="your_token_here"

# Alternative if you prefer
export GITHUB_TOKEN="your_token_here"
```

### SSH Authentication (Future Feature)
```json
{
  "authentication": {
    "method": "ssh",
    "use_ssh": true,
    "ssh_key_path": "~/.ssh/id_rsa"
  }
}
```

## Module Repository Structure

### Expected Repository Layout
```
buildcli-modules/
├── modules.json          # Module manifest
├── git/                  # Module directory
│   ├── module.py        # Main module file
│   ├── requirements.txt # Dependencies (optional)
│   └── README.md        # Module documentation
├── docker/
│   ├── module.py
│   └── requirements.txt
└── ...
```

### Module Manifest Format
```json
{
  "modules": [
    {
      "name": "git",
      "version": "1.0.0",
      "description": "Git integration module",
      "author": "BuildCLI Official",
      "commands": ["git", "clone", "push", "pull", "commit"],
      "download_url": "https://github.com/buildcli-official/buildcli-modules/releases/download/v1.0.0/git.zip",
      "dependencies": ["gitpython>=3.1.0"],
      "min_buildcli_version": "1.0.0"
    }
  ]
}
```

## Security Considerations

### Trusted Sources
- Only enable trusted sources in production
- Use `trusted: true` only for official and verified repositories
- Review security settings regularly

### Code Review
```json
{
  "security": {
    "require_code_review": true,
    "allowed_authors": ["buildcli-official"],
    "verify_signatures": true
  }
}
```

### File Restrictions
```json
{
  "security": {
    "allowed_file_extensions": [".py", ".json", ".md", ".txt"],
    "max_module_size_mb": 50,
    "scan_for_vulnerabilities": true
  }
}
```

## Troubleshooting

### Common Issues

1. **Rate limiting:**
   ```bash
   # Set up authentication token
   export BUILDCLI_GITHUB_TOKEN="your_token"
   ```

2. **Network issues:**
   ```bash
   # Check configuration
   buildcli config-show github
   
   # Test connectivity
   buildcli list-remote-modules
   ```

3. **Permission errors:**
   ```bash
   # Check file permissions
   ls -la ~/.buildcli/
   
   # Recreate configuration
   buildcli github-config-init --force
   ```

### Debug Mode
```bash
# Enable verbose logging
buildcli --verbose list-remote-modules

# Check configuration
buildcli config-get github.api.base_url
```

## Examples

### Complete Setup Example
```bash
# 1. Initialize configurations
buildcli config-init
buildcli github-config-init

# 2. Set GitHub token
export BUILDCLI_GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# 3. List available modules
buildcli list-remote-modules

# 4. Install a module
buildcli install-module git

# 5. Use the module
buildcli git clone https://github.com/user/repo.git
```

### Enterprise Setup
```json
{
  "module_sources": {
    "enterprise": {
      "type": "github_enterprise",
      "url": "https://github.company.com/api/v3",
      "organization": "company-buildtools",
      "repository": "buildcli-modules",
      "enabled": true,
      "trusted": true
    }
  }
}
```

This configuration system provides a flexible and secure way to manage modules from GitHub repositories while maintaining security and user control.