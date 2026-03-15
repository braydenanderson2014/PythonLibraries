#!/usr/bin/env python3
"""
Simple Bot Account Setup for Issue Reporting
This approach uses a dedicated bot GitHub account
"""

print("🤖 Simple Bot Account Setup (Recommended for Private Repos):")
print("=" * 65)

print("\n📝 Step 1: Create Bot Account")
print("1. Create a new GitHub account (e.g., 'pdf-utility-bot')")
print("2. Use an email like: pdf-utility-bot@yourdomain.com")
print("3. Set a recognizable profile:")
print("   - Avatar: Robot/bot image")
print("   - Name: 'PDF Utility Bot'")
print("   - Bio: 'Automated issue reporting for PDF Utility'")

print("\n🔑 Step 2: Generate Bot Token")
print("1. Log into the bot account")
print("2. Go to Settings → Developer settings → Personal access tokens")
print("3. Generate new token (classic) with permissions:")
print("   - repo (full control of private repositories)")
print("   - write:discussion (if using discussions)")
print("4. Copy the token securely")

print("\n🏠 Step 3: Invite Bot to Repository")
print("1. From your main account, go to your repository")
print("2. Settings → Manage access → Invite a collaborator")
print("3. Invite the bot account")
print("4. Give 'Write' permission (needed to create issues)")
print("5. Accept invitation from bot account")

print("\n⚙️  Step 4: Update Application")
print("1. Update .env file:")
print("   GITHUB_BOT_TOKEN=your_bot_token_here")
print("   GITHUB_BOT_USERNAME=pdf-utility-bot")
print("2. Modify issue_reporter.py to use bot token")

print("\n✅ Benefits of Bot Account:")
print("• Issues appear to be created by 'PDF Utility Bot'")
print("• Clean separation from personal account")
print("• Easy to manage permissions")
print("• Works immediately with private repos")
print("• No complex GitHub App setup required")

print("\n🎯 Result:")
print("Issues will show:")
print("• Author: PDF Utility Bot")
print("• Not associated with your personal account")
print("• Clear indication it's automated")
