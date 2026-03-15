#!/usr/bin/env python3
"""
Clean up duplicate automated comments on GitHub issues
This script will identify and remove duplicate bot comments to clean up issues that were processed multiple times.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta

def get_github_headers():
    """Get GitHub API headers with authentication"""
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_BOT_TOKEN')
    if not token:
        print("❌ No GitHub token found. Set GITHUB_TOKEN or GITHUB_BOT_TOKEN environment variable.")
        sys.exit(1)
    
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PDF-Utility-Comment-Cleaner/1.0'
    }

def get_repo_info():
    """Get repository information from environment"""
    owner = os.getenv('GITHUB_OWNER')
    repo = os.getenv('GITHUB_REPO')
    
    if not owner or not repo:
        print("❌ Missing GITHUB_OWNER or GITHUB_REPO environment variables.")
        sys.exit(1)
    
    return owner, repo

def find_duplicate_comments(owner, repo, headers, dry_run=True):
    """Find and optionally remove duplicate automated comments"""
    issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    try:
        # Get recent issues (last 50)
        response = requests.get(
            issues_url,
            headers=headers,
            params={'state': 'all', 'per_page': 50, 'sort': 'updated', 'direction': 'desc'}
        )
        response.raise_for_status()
        issues = response.json()
        
        print(f"📋 Found {len(issues)} recent issues to check")
        
        total_duplicates = 0
        
        for issue in issues:
            issue_number = issue['number']
            
            # Get comments for this issue
            comments_url = f"{issues_url}/{issue_number}/comments"
            comments_response = requests.get(comments_url, headers=headers)
            comments_response.raise_for_status()
            comments = comments_response.json()
            
            if not comments:
                continue
            
            # Find automated comments
            bot_comments = []
            for comment in comments:
                body = comment['body']
                if (('This is an automated response' in body or 
                     'AUTO-RESPONSE-ID:' in body or
                     '🐛 **Thank you for reporting this bug!**' in body or
                     '✨ **Thank you for this feature request!**' in body)):
                    bot_comments.append(comment)
            
            if len(bot_comments) <= 1:
                continue  # No duplicates
            
            print(f"\n🔍 Issue #{issue_number}: Found {len(bot_comments)} automated comments")
            
            # Group similar comments
            comment_groups = {}
            for comment in bot_comments:
                # Create a signature for the comment type
                body = comment['body']
                signature = 'unknown'
                
                if '🐛 **Thank you for reporting this bug!**' in body:
                    signature = 'bug-welcome'
                elif '✨ **Thank you for this feature request!**' in body:
                    signature = 'feature-welcome'
                elif '🔄 **Duplicate Issue Detected**' in body:
                    signature = 'duplicate-found'
                elif '❓ **More Information Needed**' in body:
                    signature = 'needs-info'
                
                if signature not in comment_groups:
                    comment_groups[signature] = []
                comment_groups[signature].append(comment)
            
            # Process duplicates
            for signature, group_comments in comment_groups.items():
                if len(group_comments) > 1:
                    duplicates_count = len(group_comments) - 1
                    total_duplicates += duplicates_count
                    
                    # Keep the newest comment, remove older ones
                    group_comments.sort(key=lambda c: c['created_at'])
                    to_remove = group_comments[:-1]  # All except the last (newest)
                    
                    print(f"   📝 {signature}: {len(group_comments)} comments, removing {len(to_remove)} duplicates")
                    
                    for comment in to_remove:
                        comment_id = comment['id']
                        created_at = comment['created_at']
                        
                        if dry_run:
                            print(f"      🗑️  Would delete: Comment {comment_id} (created {created_at})")
                        else:
                            # Delete the duplicate comment
                            delete_url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
                            delete_response = requests.delete(delete_url, headers=headers)
                            
                            if delete_response.status_code == 204:
                                print(f"      ✅ Deleted: Comment {comment_id} (created {created_at})")
                            else:
                                print(f"      ❌ Failed to delete comment {comment_id}: {delete_response.status_code}")
        
        print(f"\n📊 Summary:")
        print(f"   - Issues checked: {len(issues)}")
        print(f"   - Duplicate comments found: {total_duplicates}")
        
        if dry_run:
            print(f"   - Mode: DRY RUN (no changes made)")
            print(f"   - Run with --execute to actually remove duplicates")
        else:
            print(f"   - Mode: EXECUTE (duplicates were removed)")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("🧹 GitHub Issue Comment Cleaner")
    print("=" * 40)
    
    # Check command line arguments
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("   Use --execute flag to actually remove duplicates")
    else:
        print("⚠️  EXECUTE MODE - Duplicate comments will be removed")
        confirm = input("Are you sure you want to proceed? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            sys.exit(0)
    
    print()
    
    # Get configuration
    headers = get_github_headers()
    owner, repo = get_repo_info()
    
    print(f"📁 Repository: {owner}/{repo}")
    print()
    
    # Process duplicates
    find_duplicate_comments(owner, repo, headers, dry_run)
    
    if dry_run:
        print(f"\n💡 To actually remove duplicates, run:")
        print(f"   python {sys.argv[0]} --execute")

if __name__ == "__main__":
    main()
