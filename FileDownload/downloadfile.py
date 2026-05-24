#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import secrets
import hashlib
import logging
import threading
import queue
import json
import urllib.request
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
from flask import Flask, request, render_template_string, send_file, redirect, url_for, session, flash, Response
from waitress import serve

# ===================== CONFIGURATION =====================

# Path to the file you want users to download
FILE_PATH = r"./Dance Recital 2026 (Mar-April)-Final(Handbraked).zip"

# Name the user will see when downloading
DOWNLOAD_NAME = "Dance Recital 2026 (Mar-April)-Final(Handbraked).zip"

# Favicon URL (optional - leave empty string "" if not using)
FAVICON_URL = "/favicon.png"  # Served from root directory
FAVICON_FILE = "unnamed.png"  # Actual filename in your directory

# Sponsor QR code image (optional - leave empty string "" if not using)
SPONSOR_QR_FILE = "Sponsor.png"  # Actual filename in your directory

# Simple PIN required to access download page (stored as SHA-256 hash)
# To generate hash: python3 -c "import hashlib; print(hashlib.sha256('YOUR_PIN'.encode()).hexdigest())"
DOWNLOAD_PIN = "0342"  # <-- change this! (will be hashed on startup)

# Secret key for session - generates a new random key on each startup
# For persistent sessions across restarts, replace with: secrets.token_hex(32)
FLASK_SECRET_KEY = secrets.token_hex(32)  # Cryptographically secure random key

# Security: Session timeout in minutes
SESSION_LIFETIME_MINUTES = 30

# Security: Rate limiting for PIN attempts
MAX_PIN_ATTEMPTS = 5  # Maximum attempts
LOCKOUT_DURATION_MINUTES = 15  # Lockout duration after max attempts

# Host and port to bind to
HOST = "0.0.0.0"
PORT = 8000
DEV_PORT = 8001  # Port for development mode (--dev argument)

# Server lifetime: Auto-shutdown at configured date/time
# Set to True to enable automatic shutdown at AUTO_SHUTDOWN_DATETIME
AUTO_SHUTDOWN_ENABLED = True
# Formats accepted: YYYY-MM-DD HH:MM[:SS] or YYYY-MM-DDTHH:MM[:SS]
AUTO_SHUTDOWN_DATETIME = "2026-06-30 23:59:59"

# =========================================================

# Configure security logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_LIFETIME_MINUTES)

# Rate limiting storage (IP -> [attempt times])
rate_limit_storage = defaultdict(list)
rate_limit_lock = Lock()

# Store hashed PIN
PIN_HASH = None

# Console messaging system
console_messages = []  # Store recent messages
console_message_lock = Lock()
message_queue = queue.Queue()  # For SSE updates
MAX_CONSOLE_MESSAGES = 50  # Keep last 50 messages
console_message_counter = 0  # Monotonic ID for reliable SSE fan-out

# Scheduled reboot system
scheduled_reboot_time = None  # datetime when reboot should occur
reboot_lock = Lock()

# Active download tracking
active_downloads = {}  # {ip: {'start_time': datetime, 'file': filename}}
download_lock = Lock()
server_start_time = datetime.now()

# Connection tracking
active_connections = {}  # {ip: {'first_seen': datetime, 'last_seen': datetime}}
connection_lock = Lock()
ip_location_cache = {}  # {ip: {'city': str, 'region': str, 'country': str}}
# Active download tracking
active_downloads = {}  # {ip: {'start_time': datetime, 'file': filename}}
download_lock = Lock()
server_start_time = datetime.now()

# Connection tracking
active_connections = {}  # {ip: {'first_seen': datetime, 'last_seen': datetime}}
connection_lock = Lock()
ip_location_cache = {}  # {ip: {'city': str, 'region': str, 'country': str}}
location_cache_lock = Lock()

# Security helper functions
def get_client_ip():
    """Get the real client IP address, accounting for Cloudflare proxy"""
    # Cloudflare passes the real client IP in CF-Connecting-IP header
    if 'CF-Connecting-IP' in request.headers:
        return request.headers.get('CF-Connecting-IP')
    # Fallback to X-Forwarded-For if available
    elif 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For can contain multiple IPs, get the first one
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    # Final fallback to direct remote_addr
    return request.remote_addr


def get_ip_location(ip):
    """Get approximate location for an IP address (city, region, country)"""
    # Check cache first
    with location_cache_lock:
        if ip in ip_location_cache:
            return ip_location_cache[ip]
    
    # Skip for localhost/private IPs
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip == 'localhost':
        location = {'city': 'Local', 'region': 'Network', 'country': 'Private'}
        with location_cache_lock:
            ip_location_cache[ip] = location
        return location
    
    try:
        # Use free ip-api.com service (no API key needed, 45 req/min limit)
        url = f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country'
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 'success':
                location = {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'country': data.get('country', 'Unknown')
                }
            else:
                location = {'city': 'Unknown', 'region': 'Unknown', 'country': 'Unknown'}
    except Exception as e:
        logger.debug(f"Could not get location for IP {ip}: {str(e)}")
        location = {'city': 'Unknown', 'region': 'Unknown', 'country': 'Unknown'}
    
    # Cache the result
    with location_cache_lock:
        ip_location_cache[ip] = location
    
    return location


def track_connection(ip):
    """Track a connection from an IP address"""
    with connection_lock:
        if ip not in active_connections:
            active_connections[ip] = {
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        else:
            active_connections[ip]['last_seen'] = datetime.now()


def get_ip_location(ip):
    """Get approximate location for an IP address (city, region, country)"""
    # Check cache first
    with location_cache_lock:
        if ip in ip_location_cache:
            return ip_location_cache[ip]
    
    # Skip for localhost/private IPs
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip == 'localhost':
        location = {'city': 'Local', 'region': 'Network', 'country': 'Private'}
        with location_cache_lock:
            ip_location_cache[ip] = location
        return location
    
    try:
        # Use free ip-api.com service (no API key needed, 45 req/min limit)
        url = f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country'
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 'success':
                location = {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'country': data.get('country', 'Unknown')
                }
            else:
                location = {'city': 'Unknown', 'region': 'Unknown', 'country': 'Unknown'}
    except Exception as e:
        logger.debug(f"Could not get location for IP {ip}: {str(e)}")
        location = {'city': 'Unknown', 'region': 'Unknown', 'country': 'Unknown'}
    
    # Cache the result
    with location_cache_lock:
        ip_location_cache[ip] = location
    
    return location


def track_connection(ip):
    """Track a connection from an IP address"""
    with connection_lock:
        if ip not in active_connections:
            active_connections[ip] = {
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        else:
            active_connections[ip]['last_seen'] = datetime.now()


def add_console_message(message, msg_type='info'):
    """Add a message to the console display
    msg_type: 'info', 'warning', 'error', 'success'
    """
    global console_message_counter
    with console_message_lock:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        console_message_counter += 1
        msg_data = {
            'id': console_message_counter,
            'timestamp': timestamp,
            'type': msg_type,
            'message': message
        }
        console_messages.append(msg_data)
        
        # Keep only last MAX_CONSOLE_MESSAGES
        if len(console_messages) > MAX_CONSOLE_MESSAGES:
            console_messages.pop(0)
        
        # Add to queue for SSE
        message_queue.put(msg_data)


def parse_time_duration(duration_str):
    """Parse time duration like '5m', '2h', '30s' into seconds"""
    import re
    match = re.match(r'^(\d+)([smh])$', duration_str.lower())
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    return None


def schedule_reboot(duration_str):
    """Schedule a server reboot after specified duration"""
    global scheduled_reboot_time
    
    seconds = parse_time_duration(duration_str)
    if seconds is None:
        return False, "Invalid time format. Use: 5m, 2h, 30s"
    
    with reboot_lock:
        scheduled_reboot_time = datetime.now() + timedelta(seconds=seconds)
    
    # Calculate human-readable time
    if seconds < 60:
        time_str = f"{seconds} seconds"
    elif seconds < 3600:
        time_str = f"{seconds // 60} minutes"
    else:
        time_str = f"{seconds // 3600} hours"
    
    return True, time_str


def cancel_reboot():
    """Cancel scheduled reboot"""
    global scheduled_reboot_time
    with reboot_lock:
        if scheduled_reboot_time:
            scheduled_reboot_time = None
            return True
        return False


def check_scheduled_reboot():
    """Check if it's time for scheduled reboot"""
    global scheduled_reboot_time
    with reboot_lock:
        if scheduled_reboot_time and datetime.now() >= scheduled_reboot_time:
            return True
    return False


def hash_pin(pin):
    """Hash a PIN using SHA-256"""
    return hashlib.sha256(pin.encode()).hexdigest()


def check_rate_limit(ip_address):
    """
    Check if an IP address has exceeded the rate limit.
    Returns (allowed: bool, retry_after: int|None)
    """
    with rate_limit_lock:
        now = datetime.now()
        
        # Clean up old attempts
        cutoff_time = now - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        rate_limit_storage[ip_address] = [
            t for t in rate_limit_storage[ip_address] if t > cutoff_time
        ]
        
        attempts = rate_limit_storage[ip_address]
        
        if len(attempts) >= MAX_PIN_ATTEMPTS:
            # Calculate remaining lockout time
            oldest_attempt = min(attempts)
            unlock_time = oldest_attempt + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            retry_after = int((unlock_time - now).total_seconds() / 60) + 1
            return False, retry_after
        
        return True, None


def record_attempt(ip_address):
    """Record a failed PIN attempt"""
    with rate_limit_lock:
        rate_limit_storage[ip_address].append(datetime.now())


def add_security_headers(response):
    """Add security headers to response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; "
        "connect-src 'self' https://static.cloudflareinsights.com"
    )
    return response


app.after_request(add_security_headers)


# Simple HTML templates (kept inline for one-file script)
PIN_PAGE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Download</title>
    {% if favicon_url %}<link rel="icon" type="image/png" href="{{ favicon_url }}">{% endif %}
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-deep: #0d1b2a;
            --bg-mid: #1b263b;
            --surface: #ffffff;
            --surface-alt: #f3f7fb;
            --text-main: #102a43;
            --text-soft: #5c6f82;
            --line: #d8e3ee;
            --accent: #1f7a8c;
            --accent-strong: #125d71;
            --accent-soft: #e6f6f8;
            --danger-bg: #fff1f1;
            --danger-border: #f2abab;
            --danger-text: #b42318;
            --shadow: 0 24px 56px rgba(10, 30, 60, 0.26);
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background:
                radial-gradient(1300px 600px at 10% -10%, #27476e 0%, transparent 60%),
                radial-gradient(900px 420px at 100% 100%, #2d6a4f 0%, transparent 55%),
                linear-gradient(140deg, var(--bg-deep) 0%, var(--bg-mid) 70%, #274c77 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 24px;
            color: var(--text-main);
        }

        body::before {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: 0.16;
            background-image:
                linear-gradient(90deg, rgba(255,255,255,0.18) 1px, transparent 1px),
                linear-gradient(rgba(255,255,255,0.14) 1px, transparent 1px);
            background-size: 40px 40px;
        }

        .container {
            position: relative;
            background: var(--surface);
            padding: 34px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.55);
            box-shadow: var(--shadow);
            max-width: 460px;
            width: 100%;
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(16px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .lock-icon {
            text-align: center;
            margin-bottom: 18px;
        }

        .lock-icon svg {
            width: 62px;
            height: 62px;
            fill: var(--accent);
            filter: drop-shadow(0 6px 14px rgba(18, 93, 113, 0.24));
        }

        h1 {
            text-align: center;
            font-size: 1.85rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 8px;
            letter-spacing: -0.01em;
        }

        .subtitle {
            text-align: center;
            color: var(--text-soft);
            font-size: 0.95rem;
            margin-bottom: 26px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 700;
            color: var(--text-main);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        input[type="password"] {
            width: 100%;
            padding: 14px 14px;
            margin-bottom: 20px;
            border-radius: 12px;
            border: 1px solid var(--line);
            font-size: 1rem;
            transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
            background: var(--surface-alt);
            color: var(--text-main);
        }

        input[type="password"]:focus {
            outline: none;
            border-color: var(--accent);
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(31, 122, 140, 0.12);
        }

        button {
            background: linear-gradient(160deg, var(--accent) 0%, var(--accent-strong) 100%);
            border: none;
            color: white;
            padding: 14px 20px;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            font-size: 1rem;
            font-weight: 700;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(18, 93, 113, 0.34);
        }

        button:active {
            transform: translateY(0);
        }

        .flash {
            background: var(--danger-bg);
            border-left: 4px solid var(--danger-border);
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: var(--danger-text);
            font-size: 0.9rem;
            animation: shake 0.5s ease;
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }

        .footer {
            margin-top: 24px;
            padding-top: 18px;
            border-top: 1px solid var(--line);
            font-size: 0.85rem;
            color: #7f92a7;
            text-align: center;
            line-height: 1.5;
        }

        .footer svg {
            width: 16px;
            height: 16px;
            vertical-align: middle;
            fill: #7f92a7;
            margin-right: 4px;
        }

        .shutdown-warning {
            background: linear-gradient(135deg, #fff5e6 0%, #ffe8cc 100%);
            border: 2px solid #ffb84d;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 20px;
            color: #8b5a00;
            font-size: 0.85rem;
            text-align: center;
            font-weight: 600;
        }
        
        .shutdown-warning svg {
            width: 18px;
            height: 18px;
            vertical-align: middle;
            fill: #ff9900;
            margin-right: 6px;
        }

        .console-messages {
            margin-top: 24px;
            background: #0f1a2a;
            border: 1px solid #2a3a53;
            border-radius: 12px;
            padding: 16px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
        }

        .console-message {
            margin-bottom: 8px;
            padding: 6px 8px;
            border-radius: 6px;
            animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .console-message.info {
            background: rgba(66, 153, 225, 0.1);
            border-left: 3px solid #4299e1;
            color: #90cdf4;
        }

        .console-message.warning {
            background: rgba(237, 137, 54, 0.1);
            border-left: 3px solid #ed8936;
            color: #fbd38d;
        }

        .console-message.error {
            background: rgba(245, 101, 101, 0.1);
            border-left: 3px solid #f56565;
            color: #fc8181;
        }

        .console-message.success {
            background: rgba(72, 187, 120, 0.1);
            border-left: 3px solid #48bb78;
            color: #9ae6b4;
        }

        .console-timestamp {
            color: #718096;
            margin-right: 8px;
        }

        /* Notification Banner */
        .notification-banner {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            min-width: 320px;
            max-width: 600px;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideDown 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 500;
        }

        .notification-banner.warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
        }

        .notification-banner.error {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }

        .notification-banner.info {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }

        .notification-banner.success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }

        @keyframes slideDown {
            from {
                transform: translateX(-50%) translateY(-100px);
                opacity: 0;
            }
            to {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
        }

        @keyframes slideUp {
            from {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
            to {
                transform: translateX(-50%) translateY(-100px);
                opacity: 0;
            }
        }

        .notification-banner.hiding {
            animation: slideUp 0.3s ease forwards;
        }

        @media (max-width: 640px) {
            .container {
                padding: 26px 20px;
                border-radius: 16px;
            }

            h1 {
                font-size: 1.55rem;
            }

            .notification-banner {
                min-width: 0;
                width: calc(100% - 24px);
                left: 12px;
                right: 12px;
                transform: none;
            }

            @keyframes slideDown {
                from {
                    transform: translateY(-100px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            @keyframes slideUp {
                from {
                    transform: translateY(0);
                    opacity: 1;
                }
                to {
                    transform: translateY(-100px);
                    opacity: 0;
                }
            }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="lock-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 1C8.676 1 6 3.676 6 7v3H5c-1.103 0-2 .897-2 2v9c0 1.103.897 2 2 2h14c1.103 0 2-.897 2-2v-9c0-1.103-.897-2-2-2h-1V7c0-3.324-2.676-6-6-6zm0 2c2.276 0 4 1.724 4 4v3H8V7c0-2.276 1.724-4 4-4zm0 10c1.103 0 2 .897 2 2s-.897 2-2 2-2-.897-2-2 .897-2 2-2z"/>
        </svg>
    </div>
    
    <h1>Secure Download</h1>
    <p class="subtitle">Enter your PIN to access the file</p>

    {% if shutdown_warning %}
    <div class="shutdown-warning" id="shutdownWarning">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 2L1 21h22L12 2zm0 3.5L19.5 19h-15L12 5.5zM11 10v4h2v-4h-2zm0 5v2h2v-2h-2z"/>
        </svg>
        <span id="shutdownWarningText">{{ shutdown_warning }}</span>
    </div>
    {% endif %}

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}
          <div class="flash">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="POST" action="{{ url_for('enter_pin') }}">
        <label for="pin">Access PIN</label>
        <input type="password" id="pin" name="pin" required autofocus placeholder="Enter your PIN">
        <button type="submit">🔓 Unlock Download</button>
    </form>

    <div class="footer">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 2C6.486 2 2 6.486 2 12s4.486 10 10 10 10-4.486 10-10S17.514 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
        </svg>
        Protected by secure authentication
    </div>
    
    <div class="console-messages" id="consoleMessages"></div>
</div>
<script>
const eventSource = new EventSource('/console-messages');
const consoleDiv = document.getElementById('consoleMessages');
const NOTIFY_TYPES = new Set(['success', 'warning', 'error']);
const pendingBrowserNotifications = [];
let notificationPermissionRequestInFlight = false;
let sseOpened = false;
let pollingActive = false;
let pollingTimer = null;
let lastMessageId = 0;

eventSource.onopen = function() {
    sseOpened = true;
    console.log('SSE connection opened');
};

eventSource.onerror = function(e) {
    console.error('SSE error:', e);
    startPollingFallback();
};

function applyShutdownWarning(warning) {
    const warningDiv = document.getElementById('shutdownWarning');
    const warningText = document.getElementById('shutdownWarningText');
    const text = (warning || '').trim();

    if (text && warningText) {
        warningText.textContent = text;
        if (warningDiv) warningDiv.style.display = 'flex';
    } else if (warningDiv) {
        warningDiv.style.display = 'none';
    }
}

eventSource.addEventListener('shutdown-warning', function(e) {
    const warning = (e.data || '').trim();
    console.log('[SSE] shutdown-warning:', warning || '(cleared)');
    applyShutdownWarning(warning);
});

function ensureNotificationPermission() {
    if (!('Notification' in window)) {
        return;
    }

    if (Notification.permission === 'default' && !notificationPermissionRequestInFlight) {
        notificationPermissionRequestInFlight = true;
        Notification.requestPermission()
            .then(permission => {
                notificationPermissionRequestInFlight = false;
                if (permission === 'granted') {
                    flushPendingBrowserNotifications();
                }
            })
            .catch(() => {
                notificationPermissionRequestInFlight = false;
            });
    }
}

function flushPendingBrowserNotifications() {
    while (pendingBrowserNotifications.length > 0 && Notification.permission === 'granted') {
        const item = pendingBrowserNotifications.shift();
        createBrowserNotification(item.message, item.type);
    }
}

function showNotification(message, type) {
    // Remove any existing notifications
    const existing = document.querySelectorAll('.notification-banner');
    existing.forEach(n => n.remove());
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification-banner ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.add('hiding');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createBrowserNotification(message, type) {
    try {
        const notification = new Notification('Secure Download', {
            body: message,
            icon: '{{ favicon_url }}',
        });

        setTimeout(() => notification.close(), 5000);
        return true;
    } catch (error) {
        console.error('Browser notification failed:', error);
        return false;
    }
}

function showBrowserNotification(message, type) {
    if (!('Notification' in window) || !window.isSecureContext) {
        showNotification(message, type);
        return;
    }

    if (Notification.permission === 'granted') {
        if (!createBrowserNotification(message, type)) {
            showNotification(message, type);
        }
        return;
    }

    if (Notification.permission === 'default') {
        pendingBrowserNotifications.push({message, type});
        ensureNotificationPermission();
    }

    showNotification(message, type);
}

ensureNotificationPermission();

setTimeout(() => {
    if (!sseOpened) {
        console.warn('SSE did not open quickly; switching to polling fallback');
        startPollingFallback();
    }
}, 3000);

function processIncomingMessage(timestamp, type, message) {
    console.log(`[SSE] message type=${type} at ${timestamp}: ${message}`);

    if (NOTIFY_TYPES.has(type)) {
        showBrowserNotification(message, type);
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `console-message ${type}`;
    msgDiv.innerHTML = `<span class="console-timestamp">${timestamp}</span>${message}`;

    consoleDiv.appendChild(msgDiv);
    consoleDiv.scrollTop = consoleDiv.scrollHeight;

    while (consoleDiv.children.length > 50) {
        consoleDiv.removeChild(consoleDiv.firstChild);
    }
}

eventSource.onmessage = function(e) {
    if (!e.data) return;
    const parts = e.data.split('|');
    if (parts.length !== 3) return;
    
    const [timestamp, type, message] = parts;
    processIncomingMessage(timestamp, type, message);
};

async function pollMessagesOnce() {
    try {
        const response = await fetch(`/console-messages-poll?after_id=${lastMessageId}`, {cache: 'no-store'});
        if (!response.ok) {
            throw new Error(`Polling failed with status ${response.status}`);
        }

        const data = await response.json();
        const messages = Array.isArray(data.messages) ? data.messages : [];

        for (const msg of messages) {
            processIncomingMessage(msg.timestamp, msg.type, msg.message);
            lastMessageId = Math.max(lastMessageId, Number(msg.id || 0));
        }

        applyShutdownWarning(data.shutdown_warning || '');
    } catch (error) {
        console.error('Polling fallback error:', error);
    }
}

function startPollingFallback() {
    if (pollingActive) {
        return;
    }

    pollingActive = true;
    try {
        eventSource.close();
    } catch (e) {
        console.debug('EventSource close skipped:', e);
    }

    pollMessagesOnce();
    pollingTimer = setInterval(pollMessagesOnce, 2000);
}

// Log donation link clicks
function logDonation(platform) {
    fetch('/log-donation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({platform: platform})
    }).catch(e => console.error('Failed to log donation click:', e));
}
</script>
</body>
</html>
"""

DOWNLOAD_PAGE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download Ready</title>
    {% if favicon_url %}<link rel="icon" type="image/png" href="{{ favicon_url }}">{% endif %}
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-deep: #0d1b2a;
            --bg-mid: #1b263b;
            --surface: #ffffff;
            --surface-alt: #f3f7fb;
            --text-main: #102a43;
            --text-soft: #5c6f82;
            --line: #d8e3ee;
            --accent: #1f7a8c;
            --accent-strong: #125d71;
            --accent-soft: #e6f6f8;
            --ok: #1b8a5a;
            --shadow: 0 24px 56px rgba(10, 30, 60, 0.26);
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background:
                radial-gradient(1300px 600px at 10% -10%, #27476e 0%, transparent 60%),
                radial-gradient(900px 420px at 100% 100%, #2d6a4f 0%, transparent 55%),
                linear-gradient(140deg, var(--bg-deep) 0%, var(--bg-mid) 70%, #274c77 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 24px;
            color: var(--text-main);
        }

        body::before {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: 0.16;
            background-image:
                linear-gradient(90deg, rgba(255,255,255,0.18) 1px, transparent 1px),
                linear-gradient(rgba(255,255,255,0.14) 1px, transparent 1px);
            background-size: 40px 40px;
        }

        .container {
            position: relative;
            background: var(--surface);
            padding: 34px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.55);
            box-shadow: var(--shadow);
            max-width: 560px;
            width: 100%;
            text-align: center;
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(16px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .top-ribbon {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 14px;
            padding: 6px 12px;
            background: var(--accent-soft);
            border: 1px solid #bce8ee;
            border-radius: 999px;
            color: var(--accent-strong);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .logo-header {
            margin-bottom: 12px;
        }

        .logo-header img {
            max-width: 104px;
            height: auto;
            border-radius: 14px;
            border: 1px solid var(--line);
            box-shadow: 0 8px 20px rgba(10, 30, 60, 0.15);
        }

        @keyframes scaleIn {
            from {
                transform: scale(0.75);
                opacity: 0;
            }
            to {
                transform: scale(1);
                opacity: 1;
            }
        }

        h1 {
            font-size: 1.95rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 10px;
            letter-spacing: -0.01em;
        }

        .subtitle {
            color: var(--text-soft);
            font-size: 0.98rem;
            margin-bottom: 16px;
        }

        .file-info {
            background: var(--surface-alt);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 18px;
            margin: 20px 0 22px;
            text-align: left;
        }

        .file-label {
            color: var(--text-soft);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 7px;
            font-weight: 700;
        }

        .file-name {
            color: var(--text-main);
            font-size: 1.02rem;
            font-weight: 600;
            word-break: break-all;
        }

        a.button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            background: linear-gradient(160deg, var(--accent) 0%, var(--accent-strong) 100%);
            color: white;
            min-height: 54px;
            width: 100%;
            padding: 14px 22px;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 700;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            letter-spacing: 0.01em;
        }

        a.button:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(18, 93, 113, 0.36);
        }

        a.button:active {
            transform: translateY(0);
        }

        .button-icon {
            font-size: 1.25rem;
            vertical-align: middle;
            margin-right: 9px;
        }

        .sponsor-section {
            margin-top: 26px;
            padding: 22px;
            background: linear-gradient(165deg, #fff8ec 0%, #fef2d8 100%);
            border-radius: 12px;
            border: 1px solid #f3d7a6;
            text-align: left;
        }

        .sponsor-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #7a4b00;
            margin-bottom: 10px;
        }

        .sponsor-text {
            font-size: 0.9rem;
            color: #6d4e1f;
            margin-bottom: 16px;
            line-height: 1.6;
        }

        .sponsor-qr {
            margin: 16px 0;
            text-align: center;
        }

        .sponsor-qr img {
            max-width: 200px;
            border-radius: 8px;
            border: 1px solid #e7c88f;
            box-shadow: 0 4px 12px rgba(81, 52, 9, 0.15);
        }

        .sponsor-buttons {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 16px;
        }
        
        .sponsor-button {
            display: inline-flex;
            align-items: center;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 600;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            color: white;
        }

        .sponsor-button.github {
            background: linear-gradient(135deg, #24292e 0%, #1a1d21 100%);
        }

        .sponsor-button.github:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(36, 41, 46, 0.4);
        }

        .sponsor-button.patreon {
            background: linear-gradient(135deg, #ff424d 0%, #e82c37 100%);
        }

        .sponsor-button.patreon:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 66, 77, 0.4);
        }

        .sponsor-button.venmo {
            background: linear-gradient(135deg, #3d95ce 0%, #2d7bb5 100%);
        }

        .sponsor-button.venmo:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(61, 149, 206, 0.4);
        }

        .sponsor-button.kofi {
            background: linear-gradient(135deg, #ff5e5b 0%, #ff3e3a 100%);
        }

        .sponsor-button.kofi:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 94, 91, 0.4);
        }

        .sponsor-button svg {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            fill: currentColor;
        }

        .footer {
            margin-top: 24px;
            padding-top: 18px;
            border-top: 1px solid var(--line);
            font-size: 0.85rem;
            color: #7f92a7;
            line-height: 1.5;
        }

        .footer svg {
            width: 16px;
            height: 16px;
            vertical-align: middle;
            fill: #7f92a7;
            margin-right: 4px;
        }

        .shutdown-warning {
            background: linear-gradient(135deg, #fff5e6 0%, #ffe8cc 100%);
            border: 2px solid #ffb84d;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 20px;
            color: #8b5a00;
            font-size: 0.85rem;
            text-align: center;
            font-weight: 600;
        }
        
        .shutdown-warning svg {
            width: 18px;
            height: 18px;
            vertical-align: middle;
            fill: #ff9900;
            margin-right: 6px;
        }

        @media (max-width: 640px) {
            .container {
                padding: 26px 20px;
                border-radius: 16px;
            }

            h1 {
                font-size: 1.6rem;
            }

            .sponsor-section {
                padding: 18px;
            }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="top-ribbon">Secure transfer ready</div>

    <div class="logo-header">
        <img src="/favicon.png" alt="Logo" onerror="this.style.display='none'">
    </div>

    <h1>Your download is ready</h1>
    <p class="subtitle">Click below to begin the secure file transfer.</p>

    {% if shutdown_warning %}
    <div class="shutdown-warning" id="shutdownWarning">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 2L1 21h22L12 2zm0 3.5L19.5 19h-15L12 5.5zM11 10v4h2v-4h-2zm0 5v2h2v-2h-2z"/>
        </svg>
        <span id="shutdownWarningText">{{ shutdown_warning }}</span>
    </div>
    {% endif %}

    <div class="file-info">
        <div class="file-label">Prepared file</div>
        <div class="file-name">{{ filename }}</div>
    </div>

    <a class="button" href="{{ url_for('download_file') }}">
        <span class="button-icon">⬇</span>Download file
    </a>

    <div class="sponsor-section">
        <div class="sponsor-title">Support this project</div>
        <p class="sponsor-text">
            This file and hosting are provided at no cost. If this was useful, optional support helps fund future content and infrastructure.
        </p>
        {% if sponsor_qr_available %}
        <div class="sponsor-qr">
            <img src="/sponsor-qr" alt="Donation QR Code" onerror="this.style.display='none'">
        </div>
        {% endif %}
        <div class="sponsor-buttons">
            <a href="https://github.com/sponsors/braydenanderson2014?frequency=one-time&sponsor=braydenanderson2014" target="_blank" class="sponsor-button github" onclick="logDonation('GitHub Sponsors')">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M12 2C6.477 2 2 6.477 2 12s4.486 10 10 10 10-4.486 10-10S17.52 2 12 2zm4 14H8c-.55 0-1-.45-1-1V9c0-.55.45-1 1-1h8c.55 0 1 .45 1 1v6c0 .55-.45 1-1 1zm-1-7H9v5h6V9z"/>
                </svg>
                GitHub Sponsors
            </a>
            <a href="https://patreon.com/braydenanderson2014?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink" target="_blank" class="sponsor-button patreon" onclick="logDonation('Patreon')">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M15.386 2c-3.653 0-6.614 2.961-6.614 6.614 0 3.653 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
                </svg>
                Patreon
            </a>
            <a href="https://account.venmo.com/u/Brayden-Anderson-20" target="_blank" class="sponsor-button venmo" onclick="logDonation('Venmo')">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M20.5 3h-17C2.67 3 2 3.67 2 4.5v15c0 .83.67 1.5 1.5 1.5h17c.83 0 1 .45 1 1v-15c0-.83-.67-1.5-1.5-1.5zM12 17.5c-3.03 0-5.5-2.47-5.5-5.5S8.97 6.5 12 6.5s5.5 2.47 5.5 5.5-2.47 5.5-5.5 5.5zm0-9c-1.93 0-3.5 1.57-3.5 3.5s1.57 3.5 3.5 3.5 3.5-1.57 3.5-3.5-1.57-3.5-3.5-3.5z"/>
                </svg>
                Venmo
            </a>
            <a href="https://ko-fi.com/joesupercool15673" target="_blank" class="sponsor-button kofi" onclick="logDonation('Ko-fi')">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4 14H8c-.55 0-1-.45-1-1V9c0-.55.45-1 1-1h8c.55 0 1 .45 1 1v6c0 .55-.45 1-1 1zm-1-7H9v5h6V9z"/>
                </svg>
                Ko-fi
            </a>
        </div>
    </div>
    
    <div class="footer">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 2C6.486 2 2 6.486 2 12s4.486 10 10 10 10-4.486 10-10S17.514 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
        </svg>
        If the download does not start, refresh this page and try again. If it still fails, contact support.
    </div>
    
    <div class="console-messages" id="consoleMessages"></div>
</div>
<script>
const eventSource = new EventSource('/console-messages');
const consoleDiv = document.getElementById('consoleMessages');
const NOTIFY_TYPES = new Set(['success', 'warning', 'error']);
const pendingBrowserNotifications = [];
let notificationPermissionRequestInFlight = false;
let sseOpened = false;
let pollingActive = false;
let pollingTimer = null;
let lastMessageId = 0;

eventSource.onopen = function() {
    sseOpened = true;
    console.log('SSE connection opened');
};

eventSource.onerror = function(e) {
    console.error('SSE error:', e);
    startPollingFallback();
};

function applyShutdownWarning(warning) {
    const warningDiv = document.getElementById('shutdownWarning');
    const warningText = document.getElementById('shutdownWarningText');
    const text = (warning || '').trim();

    if (text && warningText) {
        warningText.textContent = text;
        if (warningDiv) warningDiv.style.display = 'flex';
    } else if (warningDiv) {
        warningDiv.style.display = 'none';
    }
}

eventSource.addEventListener('shutdown-warning', function(e) {
    const warning = (e.data || '').trim();
    console.log('[SSE] shutdown-warning:', warning || '(cleared)');
    applyShutdownWarning(warning);
});

function ensureNotificationPermission() {
    if (!('Notification' in window)) {
        return;
    }

    if (Notification.permission === 'default' && !notificationPermissionRequestInFlight) {
        notificationPermissionRequestInFlight = true;
        Notification.requestPermission()
            .then(permission => {
                notificationPermissionRequestInFlight = false;
                if (permission === 'granted') {
                    flushPendingBrowserNotifications();
                }
            })
            .catch(() => {
                notificationPermissionRequestInFlight = false;
            });
    }
}

function flushPendingBrowserNotifications() {
    while (pendingBrowserNotifications.length > 0 && Notification.permission === 'granted') {
        const item = pendingBrowserNotifications.shift();
        createBrowserNotification(item.message, item.type);
    }
}

eventSource.onmessage = function(e) {
    if (!e.data) return;
    const parts = e.data.split('|');
    if (parts.length !== 3) return;
    
    const [timestamp, type, message] = parts;
    processIncomingMessage(timestamp, type, message);
};

function processIncomingMessage(timestamp, type, message) {
    console.log(`[SSE] message type=${type} at ${timestamp}: ${message}`);

    if (NOTIFY_TYPES.has(type)) {
        showBrowserNotification(message, type);
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `console-message ${type}`;
    msgDiv.innerHTML = `<span class="console-timestamp">${timestamp}</span>${message}`;

    consoleDiv.appendChild(msgDiv);
    consoleDiv.scrollTop = consoleDiv.scrollHeight;

    while (consoleDiv.children.length > 50) {
        consoleDiv.removeChild(consoleDiv.firstChild);
    }
}

function showNotification(message, type) {
    // Remove any existing notifications
    const existing = document.querySelectorAll('.notification-banner');
    existing.forEach(n => n.remove());
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification-banner ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.add('hiding');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createBrowserNotification(message, type) {
    try {
        const notification = new Notification('Secure Download', {
            body: message,
            icon: '{{ favicon_url }}',
        });

        setTimeout(() => notification.close(), 5000);
        return true;
    } catch (error) {
        console.error('Browser notification failed:', error);
        return false;
    }
}

function showBrowserNotification(message, type) {
    if (!('Notification' in window) || !window.isSecureContext) {
        showNotification(message, type);
        return;
    }

    if (Notification.permission === 'granted') {
        if (!createBrowserNotification(message, type)) {
            showNotification(message, type);
        }
        return;
    }

    if (Notification.permission === 'default') {
        pendingBrowserNotifications.push({message, type});
        ensureNotificationPermission();
    }

    showNotification(message, type);
}

ensureNotificationPermission();

setTimeout(() => {
    if (!sseOpened) {
        console.warn('SSE did not open quickly; switching to polling fallback');
        startPollingFallback();
    }
}, 3000);

async function pollMessagesOnce() {
    try {
        const response = await fetch(`/console-messages-poll?after_id=${lastMessageId}`, {cache: 'no-store'});
        if (!response.ok) {
            throw new Error(`Polling failed with status ${response.status}`);
        }

        const data = await response.json();
        const messages = Array.isArray(data.messages) ? data.messages : [];

        for (const msg of messages) {
            processIncomingMessage(msg.timestamp, msg.type, msg.message);
            lastMessageId = Math.max(lastMessageId, Number(msg.id || 0));
        }

        applyShutdownWarning(data.shutdown_warning || '');
    } catch (error) {
        console.error('Polling fallback error:', error);
    }
}

function startPollingFallback() {
    if (pollingActive) {
        return;
    }

    pollingActive = true;
    try {
        eventSource.close();
    } catch (e) {
        console.debug('EventSource close skipped:', e);
    }

    pollMessagesOnce();
    pollingTimer = setInterval(pollMessagesOnce, 2000);
}

// Log donation link clicks
function logDonation(platform) {
    fetch('/log-donation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({platform: platform})
    }).catch(e => console.error('Failed to log donation click:', e));
}
</script>
</body>
</html>
"""


def file_exists_or_die():
    if not os.path.isfile(FILE_PATH):
        raise FileNotFoundError(f"FILE_PATH does not exist: {FILE_PATH}")


def get_configured_shutdown_datetime():
    """Return configured shutdown datetime, or None if disabled/invalid."""
    if not AUTO_SHUTDOWN_ENABLED:
        return None

    raw_value = AUTO_SHUTDOWN_DATETIME.strip()
    normalized_value = raw_value.replace("T", " ")

    # Require an explicit time component to avoid accidental midnight cutoffs.
    if " " not in normalized_value:
        logger.error(
            "Invalid AUTO_SHUTDOWN_DATETIME value: %s (missing time). "
            "Use YYYY-MM-DD HH:MM[:SS] or YYYY-MM-DDTHH:MM[:SS]",
            AUTO_SHUTDOWN_DATETIME,
        )
        return None

    try:
        # Accept both with and without seconds.
        return datetime.strptime(normalized_value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(normalized_value, "%Y-%m-%d %H:%M")
        except ValueError:
            logger.error(
                "Invalid AUTO_SHUTDOWN_DATETIME value: %s. "
                "Use a real calendar date/time like 2026-06-30 23:59:59",
                AUTO_SHUTDOWN_DATETIME,
            )
            return None


def get_shutdown_warning(now=None):
    """Build the current shutdown warning text, if any."""
    if now is None:
        now = datetime.now()

    shutdown_at = get_configured_shutdown_datetime()
    if not shutdown_at or now > shutdown_at:
        return None

    time_remaining = shutdown_at - now
    days = time_remaining.days
    hours = time_remaining.seconds // 3600

    if days > 0:
        return f"⚠️ This service will shut down in {days} day{'s' if days != 1 else ''}"
    if hours > 0:
        return f"⚠️ This service will shut down in {hours} hour{'s' if hours != 1 else ''}"
    return "⚠️ This service will shut down very soon!"


@app.route("/", methods=["GET"])
def index():
    # Track connection
    ip_address = get_client_ip()
    track_connection(ip_address)
    
    # Calculate shutdown warning message
    shutdown_warning = get_shutdown_warning()
    sponsor_qr_available = bool(SPONSOR_QR_FILE and os.path.isfile(SPONSOR_QR_FILE))
    
    # Check session timeout
    if session.get("authorized", False):
        auth_time = session.get("auth_time")
        if auth_time:
            auth_datetime = datetime.fromisoformat(auth_time)
            if datetime.now() - auth_datetime > timedelta(minutes=SESSION_LIFETIME_MINUTES):
                session.clear()
                logger.info(f"Session expired for IP: {get_client_ip()}")
                flash("Your session has expired. Please enter PIN again.")
                return render_template_string(PIN_PAGE_HTML, favicon_url=FAVICON_URL, shutdown_warning=shutdown_warning, sponsor_qr_available=sponsor_qr_available)
        return render_template_string(DOWNLOAD_PAGE_HTML, filename=DOWNLOAD_NAME, favicon_url=FAVICON_URL, shutdown_warning=shutdown_warning, sponsor_qr_available=sponsor_qr_available)
    return render_template_string(PIN_PAGE_HTML, favicon_url=FAVICON_URL, shutdown_warning=shutdown_warning, sponsor_qr_available=sponsor_qr_available)


@app.route("/", methods=["POST"])
def enter_pin():
    ip_address = get_client_ip()
    track_connection(ip_address)
    
    # Check rate limit
    allowed, retry_after = check_rate_limit(ip_address)
    if not allowed:
        logger.warning(f"Rate limit exceeded for IP: {ip_address}")
        flash(f"Too many failed attempts. Please try again in {retry_after} minutes.")
        return redirect(url_for("index"))
    
    pin = request.form.get("pin", "").strip()
    pin_hash = hash_pin(pin)
    
    if pin_hash == PIN_HASH:
        session.permanent = True
        session["authorized"] = True
        session["auth_time"] = datetime.now().isoformat()
        
        # Log successful authentication with location
        location = get_ip_location(ip_address)
        location_str = f"{location['city']}, {location['region']}, {location['country']}"
        logger.info(f"[SUCCESS] Authentication from IP: {ip_address} | Location: {location_str}")
        
        return redirect(url_for("index"))
    else:
        record_attempt(ip_address)
        attempts_left = MAX_PIN_ATTEMPTS - len(rate_limit_storage[ip_address])
        logger.warning(f"Failed authentication attempt from IP: {ip_address} ({attempts_left} attempts left)")
        flash(f"Incorrect PIN. {attempts_left} attempts remaining.")
        session["authorized"] = False
        return redirect(url_for("index"))


@app.route("/download", methods=["GET"])
def download_file():
    if not session.get("authorized", False):
        logger.warning(f"Unauthorized download attempt from IP: {get_client_ip()}")
        flash("You must enter the correct PIN before downloading.")
        return redirect(url_for("index"))

    # Check session timeout
    auth_time = session.get("auth_time")
    if auth_time:
        auth_datetime = datetime.fromisoformat(auth_time)
        if datetime.now() - auth_datetime > timedelta(minutes=SESSION_LIFETIME_MINUTES):
            session.clear()
            logger.info(f"Session expired during download for IP: {get_client_ip()}")
            flash("Your session has expired. Please enter PIN again.")
            return redirect(url_for("index"))

    file_exists_or_die()
    client_ip = get_client_ip()
    logger.info(f"[DOWNLOAD] File requested by IP: {client_ip} | File: {DOWNLOAD_NAME}")
    
    # send_file will stream the file to the client
    # Note: We cannot reliably detect when download completes since
    # browsers stay connected to the page after download finishes
    try:
        response = send_file(
            FILE_PATH,
            as_attachment=True,
            download_name=DOWNLOAD_NAME
        )
        return response
    except Exception as e:
        logger.warning(f"[DOWNLOAD] Failed to start for IP: {client_ip} | Error: {str(e)}")
        raise


@app.route("/favicon.png", methods=["GET"])
def favicon():
    """Serve the favicon file"""
    if FAVICON_FILE and os.path.isfile(FAVICON_FILE):
        return send_file(FAVICON_FILE, mimetype='image/png')
    else:
        return "", 404


@app.route("/sponsor-qr", methods=["GET"])
def sponsor_qr():
    """Serve the sponsor QR code image"""
    if SPONSOR_QR_FILE and os.path.isfile(SPONSOR_QR_FILE):
        return send_file(SPONSOR_QR_FILE, mimetype='image/png')
    else:
        return "", 404


@app.route("/shutdown-info")
def shutdown_info():
    """Return current shutdown/reboot information as JSON"""
    now = datetime.now()
    warning = None
    
    # Check for scheduled reboot (takes priority)
    with reboot_lock:
        if scheduled_reboot_time and scheduled_reboot_time > now:
            time_left = scheduled_reboot_time - now
            minutes = int(time_left.total_seconds() / 60)
            seconds = int(time_left.total_seconds() % 60)
            
            if minutes > 0:
                warning = f"⚠️ Server restart scheduled in {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                warning = f"⚠️ Server restart scheduled in {seconds} second{'s' if seconds != 1 else ''}"
    
    # If no scheduled reboot, check for configured auto-shutdown
    if not warning:
        warning = get_shutdown_warning(now)
    
    return {'warning': warning}


@app.route("/console-messages-poll")
def console_messages_poll():
    """Return console messages after a given ID (fallback for environments where SSE is unreliable)."""
    after_id_raw = request.args.get("after_id", "0")
    try:
        after_id = int(after_id_raw)
    except ValueError:
        after_id = 0

    with console_message_lock:
        new_messages = [m for m in console_messages if m.get('id', 0) > after_id]

    payload = {
        'messages': new_messages,
        'shutdown_warning': get_shutdown_warning(),
    }
    return payload


@app.route("/log-donation", methods=["POST"])
def log_donation():
    """Log donation link clicks"""
    try:
        data = request.get_json()
        platform = data.get('platform', 'Unknown')
        ip = get_client_ip()
        logger.info(f"[DONATION] Link clicked: {platform} from IP: {ip}")
        return {'status': 'logged'}, 200
    except Exception as e:
        logger.error(f"Failed to log donation click: {e}")
        return {'status': 'error'}, 500


@app.route("/console-messages")
def console_messages_sse():
    """Server-Sent Events endpoint for live console messages"""
    # Capture client IP in request context before generator starts
    client_ip = get_client_ip()
    heartbeat_interval_seconds = 15
    last_shutdown_warning = None
    last_sent_message_id = 0
    
    def generate():
        nonlocal last_shutdown_warning, last_sent_message_id

        def serialize_console_message(msg):
            safe_message = str(msg['message']).replace('\n', ' ')
            return f"data: {msg['timestamp']}|{msg['type']}|{safe_message}\n\n"

        logger.info(f"SSE connection opened from {client_ip}")
        try:
            # Send an immediate comment so proxies see the stream start right away.
            yield ": connected\n\n"

            current_shutdown_warning = get_shutdown_warning()
            last_shutdown_warning = current_shutdown_warning
            if current_shutdown_warning:
                yield f"event: shutdown-warning\ndata: {current_shutdown_warning}\n\n"

            # Send all existing messages first
            with console_message_lock:
                if console_messages:
                    last_sent_message_id = console_messages[-1].get('id', 0)
                for msg in console_messages:
                    yield serialize_console_message(msg)
            
            # Then send new messages as they are appended to console_messages.
            while True:
                # Push any messages this client has not seen yet.
                with console_message_lock:
                    pending = [m for m in console_messages if m.get('id', 0) > last_sent_message_id]

                for msg in pending:
                    logger.debug(f"SSE sending: {msg['type']} - {msg['message']}")
                    yield serialize_console_message(msg)
                    last_sent_message_id = msg.get('id', last_sent_message_id)

                current_shutdown_warning = get_shutdown_warning()
                if current_shutdown_warning != last_shutdown_warning:
                    last_shutdown_warning = current_shutdown_warning
                    if current_shutdown_warning:
                        yield f"event: shutdown-warning\ndata: {current_shutdown_warning}\n\n"
                    else:
                        yield "event: shutdown-warning\ndata: \n\n"

                # Send heartbeat to keep connection alive, then wait.
                yield ": heartbeat\n\n"
                import time
                time.sleep(heartbeat_interval_seconds)
        except GeneratorExit:
            # Client disconnected (closed tab/browser)
            logger.info(f"[DISCONNECT] Client disconnected: {client_ip}")
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    shutdown_requested = True
    logger.info("Shutdown signal received (Ctrl+C). Server will stop gracefully.")
    sys.exit(0)


def console_input_thread():
    """Thread to handle console input for live messages"""
    is_dev_mode = '--dev' in sys.argv
    mode_indicator = "[DEV MODE] " if is_dev_mode else ""
    
    print("\n" + "=" * 60)
    print(f"{mode_indicator}CONSOLE MESSAGING & CONTROL SYSTEM")
    print("=" * 60)
    print("MESSAGE COMMANDS:")
    print("  /info <message>    - Blue info message")
    print("  /warning <message> - Yellow warning message")
    print("  /error <message>   - Red error message")
    print("  /success <message> - Green success message")
    print("  /clear             - Clear all messages")
    print("")
    print("SYSTEM COMMANDS:")
    print("  /reboot <time>     - Schedule server restart (e.g., /reboot 5m)")
    print("  /shutdown          - Shut down server immediately")
    print("  /cancel            - Cancel scheduled reboot")
    print("  /status            - Show server status")
    print("  /connections       - Show all connected IPs with locations")
    print("  /test              - Send test message to verify SSE connection")
    print("=" * 60 + "\n")
    
    while not shutdown_requested:
        try:
            user_input = input()
            if not user_input.strip():
                continue
            
            # System commands
            if user_input == "/test":
                add_console_message("🧪 Test notification from server", "success")
                print("✓ Test success notification sent to all connected clients")
                continue
            
            if user_input == "/shutdown":
                print("\n" + "="* 60)
                print("⚠️  SHUTTING DOWN SERVER")
                print("=" * 60)
                add_console_message("🛑 SERVER IS SHUTTING DOWN NOW", "error")
                import time
                time.sleep(2)  # Give time for message to be sent
                logger.info("Server shutdown initiated by administrator")
                os._exit(0)
            
            if user_input == "/clear":
                with console_message_lock:
                    console_messages.clear()
                print("✓ Console messages cleared")
                continue
            
            if user_input == "/cancel":
                if cancel_reboot():
                    print("✓ Scheduled reboot cancelled")
                    add_console_message("Scheduled server restart has been cancelled", "info")
                else:
                    print("✗ No reboot scheduled")
                continue
            
            if user_input == "/status":
                print("\n" + "=" * 60)
                print("SERVER STATUS")
                print("=" * 60)
                
                # Uptime
                uptime = datetime.now() - server_start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                print(f"⏱️  Uptime: {hours}h {minutes}m")
                print(f"🌐 Server: http://{HOST}:{PORT}")
                
                # Active sessions
                # Note: Flask sessions are client-side, so we can't count them directly
                # We can track active downloads instead
                
                # Active downloads
                with download_lock:
                    if active_downloads:
                        print(f"\n📥 Active Downloads: {len(active_downloads)}")
                        for ip, info in active_downloads.items():
                            elapsed = datetime.now() - info['start_time']
                            elapsed_str = f"{int(elapsed.total_seconds())}s"
                            print(f"   • {ip} - {info['file']} ({elapsed_str})")
                    else:
                        print(f"\n📥 Active Downloads: 0")
                
                # Rate limiting status
                locked_ips = sum(1 for attempts in rate_limit_storage.values() if len(attempts) >= MAX_PIN_ATTEMPTS)
                if locked_ips > 0:
                    print(f"\n🔒 Locked IPs: {locked_ips}")
                
                # Scheduled reboot
                with reboot_lock:
                    if scheduled_reboot_time:
                        time_left = scheduled_reboot_time - datetime.now()
                        minutes_left = int(time_left.total_seconds() / 60)
                        seconds_left = int(time_left.total_seconds() % 60)
                        print(f"\n⏰ Scheduled Reboot: {minutes_left}m {seconds_left}s")
                        print(f"   At: {scheduled_reboot_time.strftime('%H:%M:%S')}")
                    else:
                        print(f"\n⏰ Scheduled Reboot: None")
                
                # Auto-shutdown
                shutdown_at = get_configured_shutdown_datetime()
                if shutdown_at:
                    now = datetime.now()
                    if now <= shutdown_at:
                        time_left = shutdown_at - now
                        days = time_left.days
                        hours = int((time_left.total_seconds() % 86400) // 3600)
                        print(f"\n📅 Auto-Shutdown: {days}d {hours}h")
                        print(f"   At: {shutdown_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                print("=" * 60 + "\n")
                continue
            
            if user_input == "/connections":
                print("\n" + "=" * 60)
                print("CONNECTED IPs")
                print("=" * 60)
                
                with connection_lock:
                    if active_connections:
                        print(f"Total: {len(active_connections)} unique IP(s)\n")
                        
                        # Clean up stale connections (older than 10 minutes)
                        now = datetime.now()
                        stale_ips = [ip for ip, info in active_connections.items() 
                                    if (now - info['last_seen']).total_seconds() > 600]
                        for ip in stale_ips:
                            del active_connections[ip]
                        
                        for ip, info in sorted(active_connections.items(), 
                                             key=lambda x: x[1]['last_seen'], 
                                             reverse=True):
                            last_seen = info['last_seen']
                            time_ago = now - last_seen
                            
                            # Format time ago
                            if time_ago.total_seconds() < 60:
                                time_str = "just now"
                            elif time_ago.total_seconds() < 3600:
                                mins = int(time_ago.total_seconds() / 60)
                                time_str = f"{mins}m ago"
                            else:
                                hours = int(time_ago.total_seconds() / 3600)
                                time_str = f"{hours}h ago"
                            
                            # Get location (async to avoid blocking)
                            location = get_ip_location(ip)
                            loc_str = f"{location['city']}, {location['region']}, {location['country']}"
                            
                            # Check if currently downloading
                            with download_lock:
                                is_downloading = ip in active_downloads
                            
                            status = "📥 Downloading" if is_downloading else "🌐 Connected"
                            print(f"{status} | {ip}")
                            print(f"           {loc_str}")
                            print(f"           Last seen: {time_str}")
                            print()
                    else:
                        print("No active connections\n")
                
                print("=" * 60 + "\n")
                continue
            
            # Parse command
            if user_input.startswith("/"):
                parts = user_input.split(" ", 1)
                command = parts[0][1:]  # Remove /
                
                # Reboot command
                if command == "reboot":
                    if len(parts) < 2:
                        print("✗ Usage: /reboot <time> (e.g., /reboot 5m, /reboot 2h)")
                        continue
                    
                    success, result = schedule_reboot(parts[1])
                    if success:
                        print(f"✓ Server restart scheduled in {result}")
                        add_console_message(f"⚠️ SERVER RESTART SCHEDULED IN {result.upper()}", "warning")
                        add_console_message("Please complete your downloads before the restart", "warning")
                    else:
                        print(f"✗ {result}")
                    continue
                
                # Message commands
                if len(parts) < 2:
                    print("✗ Invalid command format. Use: /type message")
                    continue
                
                message = parts[1]
                
                if command in ['info', 'warning', 'error', 'success']:
                    add_console_message(message, command)
                    print(f"✓ Sent {command} message")
                else:
                    print(f"✗ Unknown command: /{command}")
            else:
                # Default to info
                add_console_message(user_input, 'info')
                print("✓ Sent info message")
                
        except EOFError:
            break
        except Exception as e:
            print(f"✗ Error: {e}")


def reboot_monitor_thread():
    """Thread to monitor scheduled reboot and send warnings"""
    warned_5min = False
    warned_1min = False
    
    while not shutdown_requested:
        try:
            with reboot_lock:
                if scheduled_reboot_time:
                    time_left = (scheduled_reboot_time - datetime.now()).total_seconds()
                    
                    # Check if it's time to reboot
                    if time_left <= 0:
                        add_console_message("⚠️ SERVER RESTARTING NOW", "error")
                        logger.info("Scheduled reboot initiated")
                        print("\n⚠️ SCHEDULED REBOOT - Restarting server...")
                        import time
                        time.sleep(2)
                        # Trigger restart by raising exception
                        os.execl(sys.executable, sys.executable, *sys.argv, "--restart")
                    
                    # 5 minute warning
                    elif time_left <= 300 and not warned_5min:
                        add_console_message("⚠️ SERVER WILL RESTART IN 5 MINUTES", "warning")
                        warned_5min = True
                        print("⏰ 5 minute warning sent")
                    
                    # 1 minute warning
                    elif time_left <= 60 and not warned_1min:
                        add_console_message("⚠️ SERVER WILL RESTART IN 1 MINUTE - Save your work!", "error")
                        warned_1min = True
                        print("⏰ 1 minute warning sent")
                else:
                    # Reset warning flags when no reboot scheduled
                    warned_5min = False
                    warned_1min = False
            
            import time
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            logger.error(f"Reboot monitor error: {e}")
            import time
            time.sleep(5)


def run_server():
    """Run the main server with lifetime check"""
    global PIN_HASH, PORT
    
    # Check for dev mode
    is_dev_mode = '--dev' in sys.argv
    if is_dev_mode:
        PORT = DEV_PORT
    
    file_exists_or_die()
    
    # Hash the PIN on startup
    PIN_HASH = hash_pin(DOWNLOAD_PIN)
    
    # Check if we're past configured shutdown time
    now = datetime.now()
    shutdown_at = get_configured_shutdown_datetime()
    if shutdown_at:
        # If shutdown time has already passed, stop startup
        if now > shutdown_at:
            logger.info("=" * 60)
            logger.info("SERVER SHUTDOWN: configured shutdown time has passed")
            logger.info(f"Current date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("Server is configured to run until AUTO_SHUTDOWN_DATETIME.")
            logger.info("Set AUTO_SHUTDOWN_ENABLED = False to disable.")
            logger.info("=" * 60)
            return False  # Don't restart
        
        # Calculate time remaining
        time_remaining = shutdown_at - now
        days_remaining = time_remaining.days
        hours_remaining = time_remaining.seconds // 3600
    else:
        days_remaining = None
        shutdown_at = None
    
    logger.info("=" * 60)
    if is_dev_mode:
        logger.info("[DEV MODE] Secure Download Server Starting")
    else:
        logger.info("Secure Download Server Starting")
    logger.info("=" * 60)
    if is_dev_mode:
        logger.info("⚠️  DEVELOPMENT MODE - Running on separate port")
    logger.info(f"Serving: {FILE_PATH}")
    logger.info(f"Download name: {DOWNLOAD_NAME}")
    logger.info(f"PIN is configured (stored as hash)")
    logger.info(f"Session timeout: {SESSION_LIFETIME_MINUTES} minutes")
    logger.info(f"Rate limiting: {MAX_PIN_ATTEMPTS} attempts per {LOCKOUT_DURATION_MINUTES} minutes")
    logger.info(f"Server address: http://{HOST}:{PORT}")
    logger.info(f"All access attempts will be logged to: download_server.log")
    if shutdown_at and days_remaining is not None:
        if days_remaining > 0:
            logger.info(f"Auto-shutdown: {days_remaining} days remaining")
        else:
            logger.info(f"Auto-shutdown: {hours_remaining} hours remaining")
        logger.info(f"Shutdown date: {shutdown_at.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Use Waitress production WSGI server
    logger.info("Starting production WSGI server (Waitress)...")
    logger.info("Press Ctrl+C to stop the server gracefully (will not auto-restart)")
    logger.info("============================================================")
    serve(
        app,
        host=HOST,
        port=PORT,
        threads=12,  # Increased to handle more concurrent large file downloads
        channel_timeout=900,  # 15 minutes for very large files
        connection_limit=200,  # Increased connection limit
        cleanup_interval=30,  # Clean up idle connections
        recv_bytes=8192,  # Receive buffer size
        # Keep this near default so SSE heartbeats/events flush promptly.
        send_bytes=1,  # Force flush for SSE events
        asyncore_use_poll=True  # Better performance for many connections
    )



if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Start console input thread
    console_thread = threading.Thread(target=console_input_thread, daemon=True)
    console_thread.start()

    # Start reboot monitor thread
    reboot_thread = threading.Thread(target=reboot_monitor_thread, daemon=True)
    reboot_thread.start()

    add_console_message("Server started and ready to accept connections", "success")

    try:
        run_server()
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
        raise

    logger.info("Server has shut down.")
