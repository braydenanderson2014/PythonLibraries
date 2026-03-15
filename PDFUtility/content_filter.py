#!/usr/bin/env python3
"""
Content Filter for Issue Reporter
Filters inappropriate content and implements rate limiting
"""

import os
import re
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class ContentFilter:
    """Content filtering and rate limiting for issue submissions"""
    
    def __init__(self):
        self.filter_file = os.path.join(os.path.dirname(__file__), 'content_filter.json')
        self.rate_limit_file = os.path.join(os.path.dirname(__file__), 'submission_history.json')
        self._load_filters()
        
    def _load_filters(self):
        """Load content filters from file or create default ones"""
        default_filters = {
            "inappropriate_words": [
                # Basic inappropriate words (keeping list minimal and professional)
                "stupid", "dumb", "idiot", "moron", "crap", "suck", "sucks", 
                "hate", "awful", "terrible", "trash", "garbage", "bullsh", 
                "damn", "hell", "wtf", "omg"
            ],
            "spam_patterns": [
                r"(.)\1{10,}",  # Repeated characters more than 10 times
                r"[A-Z]{20,}",  # Excessive caps (20+ consecutive)
                r"https?://[^\s]+",  # Full URLs
                r"www\.[^\s]+\.[a-z]{2,}",  # www.domain.com patterns
                r"[!]{5,}",  # Excessive exclamation marks
                r"[?]{5,}",  # Excessive question marks
            ],
            "max_submission_length": 5000,
            "min_submission_length": 10,
            "rate_limit": {
                "max_submissions_per_hour": 5,
                "max_submissions_per_day": 20,
                "cooldown_minutes": 5
            }
        }
        
        if os.path.exists(self.filter_file):
            try:
                with open(self.filter_file, 'r', encoding='utf-8') as f:
                    loaded_filters = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_filters.items():
                        if key not in loaded_filters:
                            loaded_filters[key] = value
                    self.filters = loaded_filters
            except Exception:
                self.filters = default_filters
        else:
            self.filters = default_filters
            self._save_filters()
    
    def _save_filters(self):
        """Save filters to file"""
        try:
            os.makedirs(os.path.dirname(self.filter_file), exist_ok=True)
            with open(self.filter_file, 'w', encoding='utf-8') as f:
                json.dump(self.filters, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save content filters: {e}")
    
    def check_inappropriate_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text contains inappropriate content
        Returns (is_clean, list_of_issues)
        """
        issues = []
        
        if not text or not text.strip():
            return True, []
        
        text_lower = text.lower()
        
        # Check inappropriate words
        inappropriate_found = []
        for word in self.filters["inappropriate_words"]:
            if word.lower() in text_lower:
                inappropriate_found.append(word)
        
        if inappropriate_found:
            issues.append(f"Contains inappropriate language: {', '.join(inappropriate_found)}")
        
        # Check spam patterns
        spam_detected = False
        for pattern in self.filters["spam_patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                if pattern.startswith(r"(.)\1"):  # Repeated characters
                    issues.append("Contains excessive repeated characters")
                    spam_detected = True
                    break
                elif "[A-Z]" in pattern:  # Excessive caps
                    issues.append("Contains excessive capital letters")
                    spam_detected = True
                    break
                elif "http" in pattern or "www" in pattern:  # URLs
                    issues.append("Contains URLs or web links")
                    spam_detected = True
                    break
                elif "[!]" in pattern or "[?]" in pattern:  # Excessive punctuation
                    issues.append("Contains excessive punctuation")
                    spam_detected = True
                    break
        
        # Check length limits
        if len(text) > self.filters["max_submission_length"]:
            issues.append(f"Content too long (max {self.filters['max_submission_length']} characters)")
        
        if len(text.strip()) < self.filters["min_submission_length"]:
            issues.append(f"Content too short (min {self.filters['min_submission_length']} characters)")
        
        return len(issues) == 0, issues
    
    def check_rate_limit(self, user_id: str = "default") -> Tuple[bool, str, int]:
        """
        Check if user is within rate limits
        Returns (is_allowed, reason, seconds_until_allowed)
        """
        now = datetime.now()
        
        # Load submission history
        history = self._load_submission_history()
        
        # Clean old entries
        user_submissions = history.get(user_id, [])
        
        # Filter submissions from last 24 hours
        day_ago = now - timedelta(days=1)
        hour_ago = now - timedelta(hours=1)
        recent_submissions = [
            datetime.fromisoformat(sub) for sub in user_submissions
            if datetime.fromisoformat(sub) > day_ago
        ]
        
        # Check daily limit
        daily_count = len(recent_submissions)
        if daily_count >= self.filters["rate_limit"]["max_submissions_per_day"]:
            return False, "Daily submission limit reached", 86400  # 24 hours
        
        # Check hourly limit
        hourly_submissions = [sub for sub in recent_submissions if sub > hour_ago]
        if len(hourly_submissions) >= self.filters["rate_limit"]["max_submissions_per_hour"]:
            return False, "Hourly submission limit reached", 3600  # 1 hour
        
        # Check cooldown period
        if recent_submissions:
            last_submission = max(recent_submissions)
            cooldown = timedelta(minutes=self.filters["rate_limit"]["cooldown_minutes"])
            if now - last_submission < cooldown:
                remaining_seconds = int((last_submission + cooldown - now).total_seconds())
                return False, f"Please wait {self.filters['rate_limit']['cooldown_minutes']} minutes between submissions", remaining_seconds
        
        return True, "OK", 0
    
    def record_submission(self, user_id: str = "default"):
        """Record a successful submission"""
        history = self._load_submission_history()
        
        if user_id not in history:
            history[user_id] = []
        
        # Add current submission
        history[user_id].append(datetime.now().isoformat())
        
        # Keep only last 30 days of submissions
        month_ago = datetime.now() - timedelta(days=30)
        history[user_id] = [
            sub for sub in history[user_id]
            if datetime.fromisoformat(sub) > month_ago
        ]
        
        self._save_submission_history(history)
    
    def _load_submission_history(self) -> Dict:
        """Load submission history from file"""
        if os.path.exists(self.rate_limit_file):
            try:
                with open(self.rate_limit_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_submission_history(self, history: Dict):
        """Save submission history to file"""
        try:
            os.makedirs(os.path.dirname(self.rate_limit_file), exist_ok=True)
            with open(self.rate_limit_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save submission history: {e}")
    
    def validate_submission(self, title: str, description: str, user_id: str = "default") -> Tuple[bool, List[str]]:
        """
        Validate a complete submission
        Returns (is_valid, list_of_issues)
        """
        issues = []
        
        # Check rate limiting first
        rate_allowed, rate_reason, wait_time = self.check_rate_limit(user_id)
        if not rate_allowed:
            if wait_time > 60:
                wait_text = f"{wait_time // 60} minutes"
            else:
                wait_text = f"{wait_time} seconds"
            issues.append(f"Rate limit exceeded: {rate_reason}. Please wait {wait_text}.")
            return False, issues
        
        # Check title content
        title_clean, title_issues = self.check_inappropriate_content(title)
        if not title_clean:
            issues.extend([f"Title: {issue}" for issue in title_issues])
        
        # Check description content
        desc_clean, desc_issues = self.check_inappropriate_content(description)
        if not desc_clean:
            issues.extend([f"Description: {issue}" for issue in desc_issues])
        
        return len(issues) == 0, issues
    
    def get_filter_stats(self) -> Dict:
        """Get statistics about the content filter"""
        history = self._load_submission_history()
        
        total_submissions = sum(len(user_subs) for user_subs in history.values())
        active_users = len([user for user, subs in history.items() if subs])
        
        # Recent activity
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        recent_submissions = []
        
        for user_subs in history.values():
            recent_submissions.extend([
                datetime.fromisoformat(sub) for sub in user_subs
                if datetime.fromisoformat(sub) > day_ago
            ])
        
        return {
            "total_submissions": total_submissions,
            "active_users": active_users,
            "submissions_last_24h": len(recent_submissions),
            "filter_words_count": len(self.filters["inappropriate_words"]),
            "spam_patterns_count": len(self.filters["spam_patterns"]),
            "rate_limits": self.filters["rate_limit"]
        }

# Global content filter instance
content_filter = ContentFilter()

def validate_issue_content(title: str, description: str, user_id: str = "default") -> Tuple[bool, List[str]]:
    """
    Convenience function to validate issue content
    Returns (is_valid, list_of_issues)
    """
    return content_filter.validate_submission(title, description, user_id)

def record_successful_submission(user_id: str = "default"):
    """
    Record a successful submission for rate limiting
    """
    content_filter.record_submission(user_id)

if __name__ == "__main__":
    # Test the content filter
    filter_test = ContentFilter()
    
    print("Content Filter Test")
    print("=" * 30)
    
    test_cases = [
        ("Good title", "This is a well-written bug report with proper description."),
        ("", "No title provided"),
        ("HELP!!!", "URGENT URGENT URGENT FIX THIS NOW!!!"),
        ("Bug report", "This feature is stupid and sucks"),
        ("Feature request", "Please add dark mode for better usability"),
        ("Test", "a"),  # Too short
        ("Long content", "x" * 6000),  # Too long
    ]
    
    for title, desc in test_cases:
        is_valid, issues = filter_test.validate_submission(title, desc)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"{status} - Title: '{title[:20]}...', Description: '{desc[:30]}...'")
        if issues:
            for issue in issues:
                print(f"    - {issue}")
        print()
    
    print("Filter Statistics:")
    stats = filter_test.get_filter_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
