#!/usr/bin/env python
# html_server.py - Simple HTTP server for rendering HTML content
# This is automatically generated - do not edit

import os
import sys
import json
import signal
import tempfile
import threading
import time
import http.server
import socketserver
import webbrowser
from http import HTTPStatus

# Find an available port
def find_available_port(start_port=8000, max_attempts=100):
    for port in range(start_port, start_port + max_attempts):
        try:
            with socketserver.TCPServer(("127.0.0.1", port), None) as server:
                pass
            return port
        except OSError:
            continue
    raise RuntimeError("Could not find an available port")

# Custom request handler
class HTMLRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, content_map=None, **kwargs):
        self.content_map = content_map or {}
        super().__init__(*args, directory=directory, **kwargs)
        
    def do_GET(self):
        path = self.path.strip("/")
        
        # Handle special paths
        if path == "ping":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"pong")
            return
            
        # Check if this is a content request
        if path in self.content_map:
            content = self.content_map[path]
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return
            
        # Default handling for files
        return super().do_GET()

# Update content in the server
def update_content(content_id, html_content):
    global content_map
    content_map[content_id] = html_content
    
# Start server function
def start_server(directory=None):
    global httpd, server_thread, content_map, server_port
    
    # Initialize content map
    content_map = {}
    
    # Find an available port
    server_port = find_available_port()
    
    # Create server
    handler = lambda *args, **kwargs: HTMLRequestHandler(*args, directory=directory, content_map=content_map, **kwargs)
    httpd = socketserver.TCPServer(("127.0.0.1", server_port), handler)
    
    # Start server in a thread
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    
    # Write port to stdout for parent process
    print(f"SERVER_PORT={server_port}")
    sys.stdout.flush()
    
    return server_port

# Stop server function
def stop_server():
    global httpd
    if 'httpd' in globals():
        httpd.shutdown()
        httpd.server_close()

# Main function
def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    
    # Create a temporary directory for content
    temp_dir = tempfile.mkdtemp(prefix="html_server_")
    
    try:
        # Start the server
        port = start_server(directory=temp_dir)
        
        # Main loop - process commands from stdin
        while True:
            try:
                cmd_line = sys.stdin.readline().strip()
                if not cmd_line:
                    time.sleep(0.1)
                    continue
                    
                # Parse command
                try:
                    cmd = json.loads(cmd_line)
                    action = cmd.get("action")
                    
                    if action == "set_content":
                        content_id = cmd.get("id", "default")
                        html_content = cmd.get("content", "")
                        update_content(content_id, html_content)
                        print(f"CONTENT_UPDATED:{content_id}")
                        sys.stdout.flush()
                        
                    elif action == "save_file":
                        content = cmd.get("content", "")
                        file_id = cmd.get("id", "file")
                        file_path = os.path.join(temp_dir, f"{file_id}.html")
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                            
                        print(f"FILE_SAVED:{file_id}")
                        sys.stdout.flush()
                        
                    elif action == "stop":
                        break
                        
                except json.JSONDecodeError:
                    print("ERROR:Invalid JSON command")
                    sys.stdout.flush()
                    
            except KeyboardInterrupt:
                break
                
    finally:
        # Clean up
        stop_server()
        
        # Remove temporary directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

# Run the main function
if __name__ == "__main__":
    main()
