# HELP - Content Filtering and Rate Limiting

## Content Quality Standards

The PDF Utility Issue Reporting System includes content filtering and rate limiting to maintain a professional environment for bug reports and feature requests.

### Content Filtering

#### Purpose
- **Professional Standards**: Ensures all submissions maintain professional quality
- **Community Guidelines**: Enforces respectful communication
- **Spam Prevention**: Blocks low-quality or spam submissions
- **Quality Control**: Encourages thoughtful, detailed reports

#### What Gets Filtered

##### Inappropriate Language
The system automatically detects and blocks submissions containing:
- Profanity or inappropriate language
- Disrespectful or offensive terms
- Derogatory comments about the software or developers

##### Spam Patterns
- **Repeated Characters**: Excessive use of repeated characters (aaaaa, !!!!!)
- **Excessive Capitalization**: Messages written entirely in capital letters
- **URLs and Links**: External links that may be spam or malicious
- **Generic Spam Terms**: Common spam keywords and phrases

##### Content Length Issues
- **Too Short**: Descriptions must be at least 10 characters long
- **Too Long**: Content is limited to 5,000 characters to encourage concise reporting
- **Empty Fields**: All required fields must contain meaningful content

### Rate Limiting

#### Purpose
- **Quality Over Quantity**: Encourages well-thought-out submissions
- **Server Protection**: Prevents overloading the issue tracking system
- **Fair Usage**: Ensures all users have equal access to report issues
- **Spam Prevention**: Stops automated or excessive submissions

#### Rate Limits

##### Hourly Limits
- **Maximum 5 submissions per hour**
- **Cooldown Period**: 5 minutes between submissions
- **Reset**: Limits reset every hour

##### Daily Limits
- **Maximum 20 submissions per day**
- **Rolling Period**: Calculated on a 24-hour rolling basis
- **Reset**: Limits reset every 24 hours

#### How Rate Limiting Works

1. **First Submission**: Goes through immediately if content is appropriate
2. **Cooldown Period**: Must wait 5 minutes before the next submission
3. **Hourly Check**: System verifies you haven't exceeded 5 submissions in the last hour
4. **Daily Check**: System verifies you haven't exceeded 20 submissions in the last 24 hours
5. **Blocked Submission**: If limits are exceeded, you'll see a clear message with wait time

### Error Messages

#### Content Filter Messages
- **"Contains inappropriate language"**: Your submission contains words that don't meet our professional standards
- **"Contains spam-like patterns"**: Your content looks like spam (excessive caps, repeated characters, etc.)
- **"Content too short"**: Your description needs to be more detailed (minimum 10 characters)
- **"Content too long"**: Your submission exceeds the maximum length (5,000 characters)

#### Rate Limit Messages
- **"Hourly submission limit reached"**: You've submitted 5 issues in the last hour
- **"Daily submission limit reached"**: You've submitted 20 issues in the last 24 hours
- **"Please wait X minutes between submissions"**: You're in the cooldown period

### Best Practices

#### Writing Quality Submissions

##### For Bug Reports
- **Be Specific**: Use clear, descriptive language
- **Stay Professional**: Focus on the technical issue, not emotions
- **Provide Details**: Include steps to reproduce, expected vs actual behavior
- **Use Technical Terms**: Proper technical vocabulary is appreciated

##### For Feature Requests
- **Be Constructive**: Explain why the feature would be useful
- **Provide Context**: Give examples of how you'd use the feature
- **Consider Implementation**: Think about how the feature might work
- **Be Patient**: Feature development takes time

#### Avoiding Filter Triggers
- **Proofread**: Review your submission before submitting
- **Professional Tone**: Keep language respectful and technical
- **Avoid Spam Patterns**: Don't use excessive punctuation or capitalization
- **Be Concise**: Get to the point without being too brief

### Working with Rate Limits

#### Planning Your Submissions
- **Quality First**: Take time to write detailed, helpful reports
- **Batch Related Issues**: If you find multiple issues, consider whether they're related
- **Use Search**: Check if your issue has already been reported
- **Wait Between Submissions**: Use the cooldown period to refine your next report

#### If You Hit Rate Limits
- **Be Patient**: Rate limits reset automatically
- **Review and Improve**: Use the wait time to improve your pending submissions
- **Prioritize**: Submit the most important issues first
- **Consider Email**: For urgent issues, consider other communication channels

### Technical Details

#### Data Storage
- **Local Storage**: Rate limiting data is stored locally on your computer
- **Privacy**: No personal information is transmitted
- **Automatic Cleanup**: Old submission records are automatically cleaned up

#### Filter Customization
The content filter is designed to be reasonable while maintaining quality standards:
- **Minimal Word List**: Only clearly inappropriate terms are blocked
- **Professional Focus**: Academic and technical language is always allowed
- **Regular Updates**: Filter rules may be updated based on community feedback

### Troubleshooting

#### False Positives
If you believe your submission was incorrectly filtered:
- **Review Content**: Check for unintentional issues (typos that create inappropriate words)
- **Rephrase**: Try rewording your submission
- **Contact Support**: Use alternative contact methods if the filter is too aggressive

#### Rate Limit Issues
- **Check Timer**: Wait for the specified time before resubmitting
- **Clear Cache**: If limits seem incorrect, restart the application
- **System Clock**: Ensure your system time is accurate

### Philosophy

The content filtering and rate limiting systems are designed with these principles:
- **Quality Over Quantity**: Better to have fewer, high-quality reports
- **Professional Environment**: Maintain standards that benefit everyone
- **Fair Access**: Ensure the system is available to all users
- **Constructive Communication**: Encourage helpful, detailed feedback

---

*These systems help maintain a productive environment for improving PDF Utility. Thank you for your understanding and cooperation!*
