#!/usr/bin/env python3
"""
Complete Bot Setup Guide for Private Repository Issue Reporting
"""

def create_env_template():
    """Create example .env template with bot configuration"""
    template = """# GitHub Configuration for Issue Reporting
# Choose one of the approaches below:

# ==========================================
# APPROACH 1: Bot Account (Recommended)
# ==========================================
# Create a dedicated GitHub bot account for issue reporting
GITHUB_BOT_TOKEN=ghp_your_bot_personal_access_token_here
GITHUB_BOT_USERNAME=pdf-utility-bot

# ==========================================
# APPROACH 2: Personal Account (Fallback)
# ==========================================
# Uses your personal account (fallback if no bot token)
GITHUB_TOKEN=ghp_your_personal_access_token_here

# ==========================================
# Repository Configuration (Required)
# ==========================================
GITHUB_OWNER=your-username
GITHUB_REPO=your-repo-name
ISSUES_API_URL=https://api.github.com/repos/{owner}/{repo}/issues

# ==========================================
# Issue Labels (Optional)
# ==========================================
ISSUE_LABELS_BUG=bug,user-reported,automated
ISSUE_LABELS_FEATURE=enhancement,feature-request,automated

# ==========================================
# Application Info (Optional)
# ==========================================
CURRENT_VERSION=1.0.0
"""
    
    with open('.env.example', 'w') as f:
        f.write(template)
    
    print("✅ Created .env.example template file")

def print_setup_guide():
    """Print comprehensive setup instructions"""
    print("🤖 Bot Account Setup Guide for Private Repository")
    print("=" * 60)
    
    print("\n🎯 Goal: Issues appear as 'PDF Utility Bot' instead of your personal account")
    
    print("\n📋 STEP 1: Create Bot GitHub Account")
    print("1. Open incognito/private browser window")
    print("2. Go to github.com and click 'Sign up'")
    print("3. Create account with details:")
    print("   • Username: pdf-utility-bot (or similar)")
    print("   • Email: pdf-utility-bot@yourdomain.com")
    print("   • Password: Strong unique password")
    print("4. Verify email and complete setup")
    
    print("\n🎨 STEP 2: Customize Bot Profile")
    print("1. Go to Settings → Profile")
    print("2. Set profile details:")
    print("   • Name: 'PDF Utility Bot'")
    print("   • Bio: 'Automated issue reporting for PDF Utility'")
    print("   • Company: Your company/project name")
    print("   • Location: (optional)")
    print("3. Upload robot/bot avatar image")
    
    print("\n🔑 STEP 3: Generate Bot Access Token")
    print("1. Still in bot account, go to Settings")
    print("2. Developer settings → Personal access tokens → Tokens (classic)")
    print("3. Generate new token (classic)")
    print("4. Configure token:")
    print("   • Note: 'PDF Utility Issue Reporter'")
    print("   • Expiration: No expiration (or very long)")
    print("   • Scopes: Check 'repo' (full control of private repositories)")
    print("5. Generate token and COPY IT IMMEDIATELY")
    print("6. Save token securely (you can't see it again)")
    
    print("\n🏠 STEP 4: Invite Bot to Your Repository")
    print("1. Switch back to your personal GitHub account")
    print("2. Go to your PDF Utility repository")
    print("3. Settings → Manage access → Invite a collaborator")
    print("4. Enter the bot username: pdf-utility-bot")
    print("5. Select role: 'Write' (needed to create issues)")
    print("6. Send invitation")
    
    print("\n✅ STEP 5: Accept Invitation")
    print("1. Switch back to bot account")
    print("2. Check notifications or email")
    print("3. Accept the repository invitation")
    print("4. Verify you can see the private repository")
    
    print("\n⚙️  STEP 6: Update .env Configuration")
    print("1. Open your .env file")
    print("2. Add/update these lines:")
    print("   GITHUB_BOT_TOKEN=your_bot_token_here")
    print("   GITHUB_BOT_USERNAME=pdf-utility-bot")
    print("3. Keep existing GITHUB_TOKEN as fallback")
    print("4. Save the file")
    
    print("\n🧪 STEP 7: Test the Setup")
    print("1. Run PDF Utility")
    print("2. Open Issue Reporter")
    print("3. Submit a test issue")
    print("4. Check that issue appears with bot as author")
    print("5. Success message should mention bot submission")
    
    print("\n✅ Expected Results:")
    print("• Issues created by: 'PDF Utility Bot'")
    print("• Issue footer: '🤖 This issue was automatically submitted by pdf-utility-bot'")
    print("• Your personal account not associated with issues")
    print("• Clean separation of automated vs manual reports")
    
    print("\n🔒 Security Notes:")
    print("• Bot token only has access to repositories you invite it to")
    print("• Can revoke bot access anytime from repository settings")
    print("• Bot can't access your personal repositories")
    print("• Token can be regenerated if compromised")
    
    print("\n🆘 Troubleshooting:")
    print("• 'Authentication failed': Check bot token is correct")
    print("• 'Repository not found': Ensure bot accepted invitation")
    print("• 'Permission denied': Bot needs 'Write' access")
    print("• Falls back to personal token if bot token missing")

if __name__ == "__main__":
    create_env_template()
    print_setup_guide()
