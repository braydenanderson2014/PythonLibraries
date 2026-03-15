# GitHub Token Setup Guide

## Overview
The PyInstaller Build Tool Enhanced requires a GitHub API token to access release information for the update system. This guide explains how to set up your token.

## Why is a GitHub Token Needed?
- **Rate Limiting**: Authenticated requests have higher rate limits (5,000 vs 60 per hour)
- **Private Repositories**: Required if your build tool repository is private
- **Reliability**: Reduces chance of API failures during update checks

## Creating a GitHub Token

### Step 1: Go to GitHub Settings
1. Visit [GitHub Token Settings](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"

### Step 2: Configure Token
1. **Note**: Enter a descriptive name like "PyInstaller Build Tool"
2. **Expiration**: Choose your preferred expiration (90 days recommended)
3. **Scopes**: Select only:
   - `public_repo` (for accessing public repository releases)
   - OR `repo` (if your repository is private)

### Step 3: Generate and Copy
1. Click "Generate token"
2. **Important**: Copy the token immediately (you won't see it again)

### Step 4: Add to Environment File
1. Open `Build_Script.env`
2. Replace `your_github_token_here` with your actual token:
   ```
   GITHUB_API_TOKEN=ghp_your_actual_token_here
   ```

## Security Notes
- **Never commit** your actual token to version control
- Keep `Build_Script.env` in your `.gitignore`
- Regenerate tokens periodically for security
- Use the minimum required scopes

## Troubleshooting

### Token Not Working
- Verify the token has correct scopes
- Check if token has expired
- Ensure repository name and owner are correct in `Build_Script.env`

### Rate Limiting Issues
- Without token: 60 requests per hour
- With token: 5,000 requests per hour
- Rate limits reset every hour

### Repository Access
- For public repos: `public_repo` scope is sufficient
- For private repos: `repo` scope is required
- Organization repos may need additional permissions

## Example Configuration

```bash
# Build_Script.env
GITHUB_REPO_OWNER=braydenanderson2014
GITHUB_REPO_NAME=Build_Script
GITHUB_API_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CURRENT_VERSION=1.0.0
```

## Testing Your Setup

Run the build tool with update check:
```bash
python build_gui_enhanced.py --update
```

You should see:
- ✅ No "rate limit" errors
- ✅ Successful release fetching
- ✅ Higher API request allowance

---
*Last Updated: August 3, 2025*
*Part of PyInstaller Build Tool Enhanced Documentation*
