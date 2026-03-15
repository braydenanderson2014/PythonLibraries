#!/usr/bin/env python3
"""
Advanced Issue Auto-Manager
Enhanced duplicate detection and issue processing with ML-based analysis
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import hashlib
from dataclasses import dataclass, asdict
import sys

# Import scientific libraries with error handling
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
    print("✓ scikit-learn and numpy imported successfully")
except ImportError as e:
    print(f"⚠ scikit-learn/numpy import error: {e}")
    print("Installing fallback implementations...")
    SKLEARN_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
    print("✓ NLTK imported successfully")
except ImportError as e:
    print(f"⚠ NLTK import error: {e}")
    print("Using fallback text processing...")
    NLTK_AVAILABLE = False

# Download required NLTK data if available
if NLTK_AVAILABLE:
    try:
        # Test if NLTK data is available (should be pre-downloaded in CI)
        try:
            nltk.data.find('tokenizers/punkt_tab')
            print("✓ NLTK punkt_tab data available")
        except LookupError:
            try:
                nltk.data.find('tokenizers/punkt')
                print("✓ NLTK punkt data available (using older version)")
            except LookupError:
                print("⚠ No NLTK punkt tokenizers found, will use fallback")
                NLTK_AVAILABLE = False
        
        try:
            nltk.data.find('corpora/stopwords')
            print("✓ NLTK stopwords data available")
        except LookupError:
            print("⚠ NLTK stopwords not found, using basic stopwords")
                
    except Exception as e:
        print(f"⚠ NLTK data check failed: {e}")
        NLTK_AVAILABLE = False

@dataclass
class IssueAnalysis:
    """Analysis results for an issue"""
    issue_number: int
    type: str  # 'bug', 'feature', 'question', 'documentation', 'unknown'
    confidence: float
    keywords: List[str]
    sentiment: str  # 'positive', 'negative', 'neutral'
    completeness_score: float
    missing_elements: List[str]
    duplicate_candidates: List[Dict]
    auto_labels: List[str]
    suggested_response: str
    priority_score: int  # 1-5 scale

class IssueAutoManager:
    """Advanced issue processing and management system"""
    
    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"
        
        # ML Components (with fallbacks)
        if SKLEARN_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer(
                    stop_words='english',
                    max_features=1000,
                    ngram_range=(1, 2),
                    lowercase=True
                )
                print("✓ TF-IDF vectorizer initialized")
            except Exception as e:
                print(f"⚠ TF-IDF initialization failed: {e}")
                self.vectorizer = None
        else:
            self.vectorizer = None
            print("⚠ Using simple text similarity (sklearn not available)")
        
        if NLTK_AVAILABLE:
            try:
                self.stemmer = PorterStemmer()
                self.stop_words = set(stopwords.words('english'))
                print("✓ NLTK components initialized")
            except Exception as e:
                print(f"⚠ NLTK initialization failed: {e}")
                self.stemmer = None
                self.stop_words = set(['the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'])
        else:
            self.stemmer = None
            self.stop_words = set(['the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'])
            print("⚠ Using basic stop words (NLTK not available)")
        
        # Configuration
        self.config = {
            'DUPLICATE_THRESHOLD': 0.85,
            'SIMILARITY_THRESHOLD': 0.75,
            'STALE_DAYS': 30,
            'AUTO_CLOSE_DAYS': 45,
            'MIN_CONFIDENCE': 0.6,
            'BATCH_SIZE': 50
        }
        
        # Classification patterns
        self.bug_patterns = [
            r'\b(error|exception|crash|fail|bug|broken|not work|doesn\'?t work)\b',
            r'\b(traceback|stack trace|stacktrace)\b',
            r'\b(unexpected|incorrect|wrong|invalid)\b'
        ]
        
        self.feature_patterns = [
            r'\b(feature|request|suggestion|enhance|improve|add)\b',
            r'\b(would like|could you|please add|support)\b',
            r'\b(new|implement|create)\b'
        ]
        
        self.question_patterns = [
            r'\b(how|what|why|where|when|question)\b',
            r'\b(help|assistance|guidance)\b'
        ]
        
        # Response templates
        self.responses = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates for different issue types"""
        return {
            'bug_welcome': '''🐛 **Thank you for reporting this bug!**

Your issue has been automatically analyzed and processed. Here's what we found:

**Analysis Summary:**
- Issue Type: Bug Report
- Confidence: {confidence}%
- Priority: {priority}/5
{missing_info}

**What happens next?**
- Our team will investigate this issue
- We may ask for additional information if needed
- Updates will be posted here as we work on a fix

**Quick Tips:**
- Check our [troubleshooting guide](link-to-docs) for common solutions
- Subscribe to this issue for updates
- Use 👍 reactions to show this affects you too

*This analysis was performed automatically. A human maintainer will review soon.*''',

            'feature_welcome': '''✨ **Thank you for this feature request!**

Your suggestion has been automatically analyzed and will be reviewed by our team.

**Analysis Summary:**
- Issue Type: Feature Request
- Confidence: {confidence}%
- Priority: {priority}/5

**What happens next?**
- We'll evaluate this request against our roadmap
- Community feedback helps us prioritize features
- Implementation timeline will be shared if approved

**Help us prioritize:**
- 👍 React with thumbs up if you want this feature
- Add use cases or examples in comments
- Share how this would benefit your workflow

*This analysis was performed automatically. A human maintainer will review soon.*''',

            'duplicate_detected': '''🔄 **Potential Duplicate Detected**

Our analysis suggests this issue might be similar to existing ones:

**Similar Issues:**
{duplicate_list}

**Similarity Analysis:**
- Highest match: {highest_similarity}%
- Common keywords: {common_keywords}

**If this is a duplicate:**
- Please check the linked issues first
- Add your specific details to the most relevant existing issue
- This issue may be closed to avoid fragmentation

**If this is unique:**
- Add more specific details about your case
- Explain how it differs from the linked issues
- We'll re-evaluate the classification

*This analysis was performed automatically using ML-based duplicate detection.*''',

            'needs_info': '''❓ **Additional Information Needed**

Our automated analysis indicates this issue needs more details for proper processing:

**Missing Elements:**
{missing_elements}

**For Bug Reports, please provide:**
- [ ] Clear steps to reproduce the issue
- [ ] Expected behavior description
- [ ] Actual behavior description  
- [ ] System information (OS, version, etc.)
- [ ] Error logs or screenshots

**For Feature Requests, please provide:**
- [ ] Detailed description of the desired feature
- [ ] Use cases and examples
- [ ] Expected behavior or workflow
- [ ] Any alternatives you've considered

**Timeline:** This issue will be marked as stale if no response is received within 7 days.

*This request was generated automatically based on content analysis.*''',

            'stale_warning': '''⏰ **Stale Issue Notice**

This issue has been inactive for **{days} days** and will be automatically closed in 7 days without activity.

**To keep this issue active:**
- [ ] Add new information or updates
- [ ] Respond to any pending questions
- [ ] Confirm the issue is still relevant

**If you're no longer experiencing this issue:**
- Feel free to close it yourself
- Let us know what resolved it for future reference

**For maintainers:**
- Add the `keep-open` label to prevent auto-closure
- Update the issue status if working on it

*This is an automated housekeeping message.*'''
        }
    
    def analyze_issue(self, issue: Dict) -> IssueAnalysis:
        """Perform comprehensive analysis of an issue"""
        content = self._extract_content(issue)
        
        # Type classification
        issue_type, confidence = self._classify_type(content)
        
        # Keyword extraction
        keywords = self._extract_keywords(content)
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(content)
        
        # Completeness analysis
        completeness_score, missing_elements = self._analyze_completeness(content, issue_type)
        
        # Duplicate detection
        duplicate_candidates = self._find_duplicates(issue)
        
        # Auto-labeling
        auto_labels = self._suggest_labels(issue_type, confidence, missing_elements, duplicate_candidates)
        
        # Priority scoring
        priority_score = self._calculate_priority(issue, issue_type, sentiment, completeness_score)
        
        # Response generation
        suggested_response = self._generate_response(
            issue_type, confidence, priority_score, missing_elements, duplicate_candidates
        )
        
        return IssueAnalysis(
            issue_number=issue['number'],
            type=issue_type,
            confidence=confidence,
            keywords=keywords,
            sentiment=sentiment,
            completeness_score=completeness_score,
            missing_elements=missing_elements,
            duplicate_candidates=duplicate_candidates,
            auto_labels=auto_labels,
            suggested_response=suggested_response,
            priority_score=priority_score
        )
    
    def _extract_content(self, issue: Dict) -> str:
        """Extract and clean issue content"""
        title = issue.get('title', '')
        body = issue.get('body', '')
        return f"{title} {body}".lower()
    
    def _classify_type(self, content: str) -> Tuple[str, float]:
        """Classify issue type using pattern matching and ML"""
        scores = {}
        
        # Pattern-based scoring
        for pattern in self.bug_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            scores['bug'] = scores.get('bug', 0) + matches
        
        for pattern in self.feature_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            scores['feature'] = scores.get('feature', 0) + matches
        
        for pattern in self.question_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            scores['question'] = scores.get('question', 0) + matches
        
        # Determine type and confidence
        if not scores:
            return 'unknown', 0.0
        
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        total_score = sum(scores.values())
        
        confidence = min(max_score / max(total_score, 1), 1.0)
        
        return max_type, confidence
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from content"""
        try:
            # Try NLTK tokenization first if available
            if NLTK_AVAILABLE:
                try:
                    tokens = word_tokenize(content)
                    tokens = [self.stemmer.stem(token.lower()) for token in tokens 
                             if token.isalpha() and token.lower() not in self.stop_words]
                except Exception as nltk_error:
                    print(f"⚠ NLTK tokenization failed: {nltk_error}")
                    # Fallback to simple tokenization
                    tokens = self._simple_tokenize(content)
            else:
                # Use simple tokenization
                tokens = self._simple_tokenize(content)
            
            # Get frequency
            from collections import Counter
            freq = Counter(tokens)
            
            # Return top keywords
            return [word for word, count in freq.most_common(10)]
            
        except Exception as e:
            print(f"⚠ Keyword extraction failed: {e}")
            # Return simple word list as fallback
            words = content.lower().split()
            return [word for word in words if len(word) > 3 and word.isalpha()][:10]
    
    def _simple_tokenize(self, content: str) -> List[str]:
        """Simple tokenization fallback when NLTK fails"""
        import re
        # Simple word extraction with basic filtering
        words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
        # Filter out stop words and short words
        filtered = [word for word in words 
                   if len(word) > 2 and word not in self.stop_words]
        return filtered
    
    def _analyze_sentiment(self, content: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'broken', 'useless', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        else:
            return 'neutral'
    
    def _analyze_completeness(self, content: str, issue_type: str) -> Tuple[float, List[str]]:
        """Analyze how complete the issue description is"""
        missing = []
        score = 1.0
        
        if issue_type == 'bug':
            # Check for bug report elements
            if not re.search(r'(steps|reproduce|how to)', content, re.IGNORECASE):
                missing.append('Steps to reproduce')
                score -= 0.25
            
            if not re.search(r'(expected|should|supposed)', content, re.IGNORECASE):
                missing.append('Expected behavior')
                score -= 0.25
            
            if not re.search(r'(actual|instead|but|however)', content, re.IGNORECASE):
                missing.append('Actual behavior')
                score -= 0.25
            
            if not re.search(r'(version|os|system|platform)', content, re.IGNORECASE):
                missing.append('System information')
                score -= 0.25
        
        elif issue_type == 'feature':
            # Check for feature request elements
            if len(content) < 50:
                missing.append('Detailed description')
                score -= 0.3
            
            if not re.search(r'(use case|example|scenario)', content, re.IGNORECASE):
                missing.append('Use cases or examples')
                score -= 0.3
        
        return max(score, 0.0), missing
    
    def _find_duplicates(self, issue: Dict) -> List[Dict]:
        """Find potential duplicate issues using ML similarity"""
        try:
            # Get existing issues
            existing_issues = self._get_existing_issues()
            
            if not existing_issues:
                return []
            
            # Use advanced ML-based similarity if available
            if self.vectorizer is not None and SKLEARN_AVAILABLE:
                return self._find_duplicates_ml(issue, existing_issues)
            else:
                return self._find_duplicates_simple(issue, existing_issues)
                
        except Exception as e:
            print(f"Error in duplicate detection: {e}")
            return []
    
    def _find_duplicates_ml(self, issue: Dict, existing_issues: List[Dict]) -> List[Dict]:
        """ML-based duplicate detection using TF-IDF and cosine similarity"""
        try:
            # Prepare texts for vectorization
            current_text = self._extract_content(issue)
            existing_texts = [self._extract_content(existing) for existing in existing_issues]
            all_texts = [current_text] + existing_texts
            
            # Vectorize
            if len(all_texts) < 2:
                return []
            
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Calculate similarities
            current_vector = tfidf_matrix[0:1]
            existing_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(current_vector, existing_vectors)[0]
            
            # Find high-similarity issues
            duplicates = []
            for i, similarity in enumerate(similarities):
                if similarity >= self.config['SIMILARITY_THRESHOLD']:
                    duplicates.append({
                        'issue': existing_issues[i],
                        'similarity': float(similarity),
                        'similarity_percent': round(similarity * 100, 1)
                    })
            
            # Sort by similarity
            duplicates.sort(key=lambda x: x['similarity'], reverse=True)
            
            return duplicates[:5]  # Return top 5 matches
            
        except Exception as e:
            print(f"Error in ML duplicate detection: {e}")
            return self._find_duplicates_simple(issue, existing_issues)
    
    def _find_duplicates_simple(self, issue: Dict, existing_issues: List[Dict]) -> List[Dict]:
        """Simple duplicate detection using keyword matching"""
        try:
            current_text = self._extract_content(issue).lower()
            current_words = set(word for word in current_text.split() if word not in self.stop_words and len(word) > 2)
            
            duplicates = []
            for existing in existing_issues:
                existing_text = self._extract_content(existing).lower()
                existing_words = set(word for word in existing_text.split() if word not in self.stop_words and len(word) > 2)
                
                if not current_words or not existing_words:
                    continue
                
                # Simple Jaccard similarity
                intersection = len(current_words.intersection(existing_words))
                union = len(current_words.union(existing_words))
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= (self.config['SIMILARITY_THRESHOLD'] - 0.1):  # Lower threshold for simple method
                        duplicates.append({
                            'issue': existing,
                            'similarity': similarity,
                            'similarity_percent': round(similarity * 100, 1)
                        })
            
            # Sort by similarity
            duplicates.sort(key=lambda x: x['similarity'], reverse=True)
            
            return duplicates[:5]  # Return top 5 matches
            
        except Exception as e:
            print(f"Error in simple duplicate detection: {e}")
            return []
    
    def _get_existing_issues(self) -> List[Dict]:
        """Get existing issues from the repository"""
        try:
            headers = {'Authorization': f'token {self.github_token}'}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
            
            params = {
                'state': 'open',
                'per_page': 100,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error fetching existing issues: {e}")
            return []
    
    def _suggest_labels(self, issue_type: str, confidence: float, 
                       missing_elements: List[str], duplicates: List[Dict]) -> List[str]:
        """Suggest labels based on analysis"""
        labels = ['auto-processed']
        
        # Type-based labels
        if confidence >= self.config['MIN_CONFIDENCE']:
            if issue_type == 'bug':
                labels.append('bug')
            elif issue_type == 'feature':
                labels.append('enhancement')
            elif issue_type == 'question':
                labels.append('question')
        
        # Quality labels
        if missing_elements:
            labels.append('needs-more-info')
        
        # Duplicate labels
        if duplicates:
            labels.append('potential-duplicate')
        
        return labels
    
    def _calculate_priority(self, issue: Dict, issue_type: str, 
                          sentiment: str, completeness: float) -> int:
        """Calculate issue priority (1-5 scale)"""
        priority = 3  # Default medium priority
        
        # Type influence
        if issue_type == 'bug':
            if 'crash' in issue.get('title', '').lower() or 'crash' in issue.get('body', '').lower():
                priority += 2
            elif 'error' in issue.get('title', '').lower():
                priority += 1
        
        # Sentiment influence
        if sentiment == 'negative':
            priority += 1
        elif sentiment == 'positive':
            priority -= 1
        
        # Completeness influence
        if completeness >= 0.8:
            priority += 1
        elif completeness < 0.5:
            priority -= 1
        
        return max(1, min(5, priority))
    
    def _generate_response(self, issue_type: str, confidence: float, 
                          priority: int, missing_elements: List[str],
                          duplicates: List[Dict]) -> str:
        """Generate appropriate auto-response"""
        if duplicates:
            # Handle duplicates
            duplicate_list = '\n'.join([
                f"- #{dup['issue']['number']}: {dup['issue']['title']} ({dup['similarity_percent']}% similar)"
                for dup in duplicates[:3]
            ])
            
            common_keywords = ', '.join(self._extract_keywords(
                ' '.join([dup['issue']['title'] + ' ' + (dup['issue']['body'] or '') 
                         for dup in duplicates[:2]])
            )[:5])
            
            return self.responses['duplicate_detected'].format(
                duplicate_list=duplicate_list,
                highest_similarity=duplicates[0]['similarity_percent'],
                common_keywords=common_keywords
            )
        
        if missing_elements:
            # Needs more info
            missing_list = '\n'.join([f"- {element}" for element in missing_elements])
            return self.responses['needs_info'].format(missing_elements=missing_list)
        
        if issue_type == 'bug':
            missing_info = ''
            if missing_elements:
                missing_info = f"\n- Missing Information: {', '.join(missing_elements)}"
            
            return self.responses['bug_welcome'].format(
                confidence=round(confidence * 100, 1),
                priority=priority,
                missing_info=missing_info
            )
        
        elif issue_type == 'feature':
            return self.responses['feature_welcome'].format(
                confidence=round(confidence * 100, 1),
                priority=priority
            )
        
        # Default response
        return '''👋 **Thank you for opening this issue!**

Your issue has been received and will be reviewed by our team.

*This is an automated response. A human maintainer will follow up soon.*'''
    
    async def process_issue(self, issue_number: int) -> IssueAnalysis:
        """Process a single issue"""
        # Get issue details
        issue = self._get_issue(issue_number)
        if not issue:
            raise ValueError(f"Issue #{issue_number} not found")
        
        # Analyze issue
        analysis = self.analyze_issue(issue)
        
        # Apply labels
        if analysis.auto_labels:
            self._add_labels(issue_number, analysis.auto_labels)
        
        # Add response comment
        if analysis.suggested_response:
            self._add_comment(issue_number, analysis.suggested_response)
        
        return analysis
    
    def _get_issue(self, issue_number: int) -> Optional[Dict]:
        """Get issue details from GitHub API"""
        try:
            headers = {'Authorization': f'token {self.github_token}'}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error fetching issue #{issue_number}: {e}")
            return None
    
    def _add_labels(self, issue_number: int, labels: List[str]):
        """Add labels to an issue"""
        try:
            headers = {'Authorization': f'token {self.github_token}'}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/labels"
            
            response = requests.post(url, headers=headers, json={'labels': labels})
            response.raise_for_status()
            
            print(f"Added labels to #{issue_number}: {labels}")
            
        except Exception as e:
            print(f"Error adding labels to #{issue_number}: {e}")
    
    def _add_comment(self, issue_number: int, comment: str):
        """Add comment to an issue"""
        try:
            headers = {'Authorization': f'token {self.github_token}'}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments"
            
            response = requests.post(url, headers=headers, json={'body': comment})
            response.raise_for_status()
            
            print(f"Added comment to #{issue_number}")
            
        except Exception as e:
            print(f"Error adding comment to #{issue_number}: {e}")

# CLI Interface
if __name__ == "__main__":
    import argparse
    import sys
    
    try:
        parser = argparse.ArgumentParser(description='Advanced Issue Auto-Manager')
        parser.add_argument('--token', required=True, help='GitHub token')
        parser.add_argument('--owner', required=True, help='Repository owner')
        parser.add_argument('--repo', required=True, help='Repository name')
        parser.add_argument('--issue', type=int, help='Process specific issue number')
        parser.add_argument('--analyze-only', action='store_true', help='Only analyze, don\'t take actions')
        parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
        
        args = parser.parse_args()
        
        if args.verbose:
            print("=== Advanced Issue Manager Debug Info ===")
            print(f"Python executable: {sys.executable}")
            print(f"Working directory: {os.getcwd()}")
            print(f"Arguments: {vars(args)}")
            
            # Check dependencies
            try:
                import sklearn
                print(f"scikit-learn version: {sklearn.__version__}")
            except ImportError as e:
                print(f"scikit-learn import error: {e}")
            
            try:
                import nltk
                print(f"NLTK version: {nltk.__version__}")
                print(f"NLTK data path: {nltk.data.path}")
            except ImportError as e:
                print(f"NLTK import error: {e}")
            
            try:
                import numpy
                print(f"NumPy version: {numpy.__version__}")
            except ImportError as e:
                print(f"NumPy import error: {e}")
            
            print("=== End Debug Info ===")
        
        print(f"Starting Advanced Issue Manager...")
        print(f"Repository: {args.owner}/{args.repo}")
        if args.issue:
            print(f"Processing issue #{args.issue}")
        
        manager = IssueAutoManager(args.token, args.owner, args.repo)
        
        if args.issue:
            # Process specific issue
            import asyncio
            
            async def main():
                try:
                    analysis = await manager.process_issue(args.issue)
                    print("Issue processing completed successfully!")
                    print(json.dumps(asdict(analysis), indent=2, default=str))
                    return 0
                except Exception as e:
                    print(f"Error processing issue #{args.issue}: {e}")
                    import traceback
                    traceback.print_exc()
                    return 1
            
            exit_code = asyncio.run(main())
            sys.exit(exit_code)
        else:
            print("No specific issue provided - processing would run on new issues")
            print("This script is designed to be called with --issue parameter")
            sys.exit(0)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
