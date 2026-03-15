# GitHub Workflows: ID Extraction and User-Closed Handler

This document describes two important GitHub workflows that automate project management for the PDF Utility issue tracker.

## 1. Extract Program ID Workflow
**File**: `.github/workflows/extract-program-id.yml`

### Purpose
Automatically extracts Program IDs from issue bodies and updates the project's ID field.

### Triggers
- `issues: [opened, edited]` - Runs when issues are created or edited

### Functionality
1. **Multi-Pattern ID Extraction**: Uses 4 different patterns to find Program IDs:
   - Bug Report Format: `**Program ID**: PDF-UTIL-XXXXXXXX-XXXX-XXXX`
   - Feature Request Format: `**Program ID:** PDF-UTIL-XXXXXXXX-XXXX-XXXX`
   - General Format: `PDF-UTIL-XXXXXXXX-XXXX-XXXX` (standalone)
   - Inline Format: Text containing the ID anywhere

2. **Project Integration**: 
   - Connects to user project `/users/braydenanderson2014/projects/4`
   - Updates the "ID" field with extracted Program ID
   - Adds confirmation comment to the issue

3. **Error Handling**:
   - Handles missing ID gracefully
   - Provides detailed logging
   - Reports extraction failures

### Expected Outcomes
- ✅ Automatic Program ID extraction from issue templates
- ✅ Project field automatically populated
- ✅ Confirmation comment added to issue
- ✅ Improved issue tracking and organization

## 2. User-Closed Handler Workflow
**File**: `.github/workflows/user-closed-handler.yml`

### Purpose
Handles issues marked with the "user-closed" label by updating Archive Bucket to "User-Closed".

### Triggers
- `issues: [closed, labeled]` - Runs when issues are closed or labels are added

### Functionality
1. **Label Detection**: 
   - Checks if issue has "user-closed" label
   - Only processes issues with this label

2. **Archive Bucket Update**:
   - Queries project structure via GraphQL
   - Finds "Archive Bucket" field and "User-Closed" option
   - Updates the field value to "User-Closed"

3. **Status Update**:
   - Also updates "Status" field to "Done"
   - Ensures consistent project state

4. **Confirmation**:
   - Adds comment confirming the archive update
   - Provides visibility into automated actions

### Expected Outcomes
- ✅ Issues with "user-closed" label automatically archived
- ✅ Archive Bucket field set to "User-Closed"
- ✅ Status field updated to "Done"
- ✅ Confirmation comment added

## Workflow Integration

### Issue Lifecycle with Workflows
1. **Issue Created** → Extract Program ID workflow runs
2. **Program ID extracted** → ID field populated in project
3. **User closes issue** → User-closed handler may run
4. **"user-closed" label applied** → Archive Bucket updated to "User-Closed"

### Project Field Updates
| Field | Updated By | Value | Trigger |
|-------|------------|-------|---------|
| ID | extract-program-id.yml | PDF-UTIL-XXXXXXXX-XXXX-XXXX | Issue opened/edited |
| Archive Bucket | user-closed-handler.yml | User-Closed | "user-closed" label |
| Status | user-closed-handler.yml | Done | "user-closed" label |

## Configuration Requirements

### Project Setup
- **Project**: `/users/braydenanderson2014/projects/4`
- **Required Fields**:
  - ID (Text field)
  - Archive Bucket (Single select with "User-Closed" option)
  - Status (Single select with "Done" option)

### Repository Setup
- **Required Labels**: `user-closed`
- **Permissions**: Issues write, Projects write
- **Token**: GITHUB_TOKEN with project access

## Testing

### Extract Program ID
Run test: `python test_id_extraction.py`
- Tests all 4 extraction patterns
- Verifies regex matching
- Confirms extraction accuracy

### User-Closed Handler  
Run test: `python test_user_closed_workflow.py`
- Tests label detection logic
- Verifies GraphQL query structure
- Confirms workflow behavior

## Monitoring

### Success Indicators
- ✅ Program IDs appear in project ID field
- ✅ Archive Bucket shows "User-Closed" for closed issues
- ✅ Status updates to "Done" automatically
- ✅ Confirmation comments added to issues

### Troubleshooting
- Check workflow runs in Actions tab
- Verify project field configuration
- Ensure "User-Closed" option exists in Archive Bucket
- Confirm token permissions for project access

## Benefits
1. **Automation**: Reduces manual project management
2. **Consistency**: Standardized field updates
3. **Visibility**: Clear tracking of issue lifecycle
4. **Efficiency**: Immediate updates without human intervention
5. **Organization**: Proper archiving of user-closed issues

Both workflows work together to create a comprehensive automated issue management system that maintains project organization and provides clear visibility into issue status and ownership.