# Run Aurora Engine Lobby Server with proper Unicode encoding
# This script sets UTF-8 encoding to handle emojis in console output

# Set Python to use UTF-8 encoding with error handling
$env:PYTHONIOENCODING = "utf-8:replace"

# Alternative: Use utf-8 with ignore to skip problematic characters
# $env:PYTHONIOENCODING = "utf-8:ignore"

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Run the server with log output
Write-Host "Starting Aurora Engine Lobby Server..." -ForegroundColor Green
Write-Host "Encoding set to: $env:PYTHONIOENCODING" -ForegroundColor Cyan

# Run with Tee-Object to capture logs
python lobby_server.py 2>&1 | Tee-Object -FilePath "lobbylogs.txt" 

# Alternative without Tee-Object (no log file):
# python lobby_server.py
