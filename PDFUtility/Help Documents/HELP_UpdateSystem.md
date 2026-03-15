# HELP - Update System

## PDF Utility Update System

The PDF Utility includes an automatic update system that keeps your application current with the latest features and bug fixes.

### Features

#### Automatic Update Checking
- **Background Checks**: The application automatically checks for updates every 24 hours
- **Non-Intrusive**: Update checks happen in the background without interrupting your work
- **Smart Notifications**: You'll be notified only when new updates are available

#### Manual Update Checks
- **Help Menu Access**: Go to `Help > Check for Updates` to manually check for updates
- **Instant Results**: Get immediate feedback on whether updates are available
- **Version Information**: See your current version and the latest available version

#### Update Management
- **Version Skipping**: You can skip specific versions if you prefer not to update immediately
- **Download Integration**: Direct links to download the latest version from GitHub
- **Release Notes**: View detailed information about what's new in each update

### How It Works

#### Automatic Updates
1. The system checks for updates every 24 hours when the application is running
2. If a new version is found, you'll see a notification dialog
3. You can choose to:
   - **Update Now**: Opens the download page for the latest version
   - **Skip This Version**: Ignores this specific version
   - **Remind Me Later**: Closes the dialog but will remind you again later

#### Manual Updates
1. Go to `Help > Check for Updates` in the menu bar
2. The system will check GitHub for the latest release
3. If an update is available, you'll see the update dialog
4. Follow the same options as automatic updates

### Configuration

The update system is configured through your `.env` file:

- **UPDATE_CHECK_INTERVAL**: How often to check for updates (default: 86400 seconds = 24 hours)
- **GITHUB_OWNER**: The GitHub repository owner (braydenanderson2014)
- **GITHUB_REPO**: The repository name (pdf-utility)

### Privacy and Security

- **No Personal Data**: The update system only checks version numbers
- **Secure Connection**: All communications use HTTPS
- **GitHub Integration**: Updates are distributed through official GitHub releases
- **No Automatic Downloads**: You always choose when and if to update

### Troubleshooting

#### Update Check Failed
- **Check Internet Connection**: Ensure you have a stable internet connection
- **GitHub Access**: Verify that GitHub is accessible from your network
- **Firewall Settings**: Make sure your firewall allows the application to access the internet

#### Version Information Missing
- **Configuration**: Check that your `.env` file contains the correct GitHub repository information
- **File Permissions**: Ensure the application can read the `.env` file

### Tips

- **Stay Current**: Regular updates include important bug fixes and security improvements
- **Test Environment**: Consider testing updates in a non-production environment first
- **Backup Settings**: Your settings and preferences are preserved during updates

---

*For technical support, use the issue reporting system in Help > Report an Issue*
