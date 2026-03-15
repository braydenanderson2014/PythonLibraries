# server.py
from flask import Flask, request, redirect
import threading
import webbrowser
import os
from PDFUtility.PDFLogger import Logger

app = Flask(__name__)
payment_system = None  # Will be set by the main application

@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if payment_system and payment_system.process_success(session_id):
        return """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }
                    .success { color: #4CAF50; }
                </style>
            </head>
            <body>
                <h1 class="success">Payment Successful!</h1>
                <p>You can now close this window and enjoy your ad-free experience.</p>
                <script>
                    setTimeout(function() { window.close(); }, 5000);
                </script>
            </body>
        </html>
        """
    return redirect('/cancel')

@app.route('/cancel')
def cancel():
    return """
    <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }
                .error { color: #f44336; }
            </style>
        </head>
        <body>
            <h1 class="error">Payment Cancelled</h1>
            <p>You can close this window and try again later.</p>
            <script>
                setTimeout(function() { window.close(); }, 5000);
            </script>
        </body>
    </html>
    """

def run_server():
    app.run(port=5000)

def start_server(payment_sys):
    logger = Logger()
    logger.info("SERVER","=================================================================")
    logger.info("SERVER"," EVENT: INIT")
    logger.info("SERVER","=================================================================")
    logger.info("SERVER", "Starting server on http://localhost:5000")
    global payment_system
    payment_system = payment_sys
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()