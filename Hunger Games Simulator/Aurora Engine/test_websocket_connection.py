#!/usr/bin/env python3
"""
WebSocket Connection Test for Aurora Engine
Tests both localhost and Cloudflare Tunnel connections
"""

import socketio
import time
import sys

def test_connection(server_url, description):
    """Test WebSocket connection to the given server URL"""
    print(f"\n🧪 Testing connection to: {server_url}")
    print(f"Description: {description}")

    try:
        # Create Socket.IO client with enhanced config for Cloudflare Tunnel
        sio = socketio.Client(
            logger=True,
            engineio_logger=True
        )

        connected = False
        ping_received = False
        pong_received = False
        transport_used = None

        @sio.event
        def connect():
            nonlocal connected, transport_used
            connected = True
            transport_used = sio.transport
            print("✅ Connected successfully!")
            print(f"Socket ID: {sio.sid}")
            print(f"Transport: {transport_used}")

            # Send ping test
            print("🏓 Sending ping...")
            sio.emit('ping')

        @sio.event
        def disconnect():
            print("❌ Disconnected")

        @sio.event
        def pong():
            nonlocal pong_received
            pong_received = True
            print("🏓 Received pong - connection is working!")

        @sio.event
        def connect_error(error):
            print(f"❌ Connection error: {error}")

        # Connect with enhanced options for Cloudflare Tunnel
        connect_kwargs = {
            'transports': ['websocket', 'polling'],
            'wait_timeout': 15
        }

        # Add Cloudflare-specific options for non-localhost
        if 'localhost' not in server_url and '127.0.0.1' not in server_url:
            connect_kwargs.update({
                'extra_headers': {'User-Agent': 'HungerGames-Test/1.0'},
                'force_polling': True  # Start with polling for Cloudflare
            })

        sio.connect(server_url, **connect_kwargs)

        # Wait for connection and ping test
        start_time = time.time()
        while time.time() - start_time < 20:  # 20 second timeout
            if connected and pong_received:
                print("✅ Connection test PASSED")
                print(f"📡 Final transport: {transport_used}")
                sio.disconnect()
                return True
            time.sleep(0.1)

        print("❌ Connection test FAILED - timeout")
        if sio.connected:
            sio.disconnect()
        return False

    except Exception as e:
        print(f"❌ Connection test FAILED - Exception: {e}")
        return False

def main():
    print("🔌 Enhanced Aurora Engine WebSocket Connection Test")
    print("=" * 60)
    print("This test includes Cloudflare Tunnel compatibility improvements:")
    print("• Force polling initially for tunnel connections")
    print("• Enhanced error handling and logging")
    print("• Better transport fallback logic")
    print("=" * 60)

    # Test localhost connection
    localhost_result = test_connection(
        'http://localhost:8000',
        'Local development server'
    )

    # Test Cloudflare Tunnel (if domain is provided as argument)
    tunnel_result = False
    if len(sys.argv) > 1:
        tunnel_domain = sys.argv[1]
        tunnel_url = f'https://{tunnel_domain}'
        tunnel_result = test_connection(
            tunnel_url,
            f'Cloudflare Tunnel ({tunnel_domain})'
        )

    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Localhost: {'✅ PASS' if localhost_result else '❌ FAIL'}")

    if len(sys.argv) > 1:
        print(f"Tunnel: {'✅ PASS' if tunnel_result else '❌ FAIL'}")

    print("\n🔧 Debugging Tips:")
    print("• Check browser console for detailed connection logs")
    print("• Use forceReconnect() in browser console to manually reconnect")
    print("• Use getConnectionStatus() to check current connection state")
    print("• Look for transport upgrade/downgrade messages")

    if localhost_result and (not len(sys.argv) > 1 or tunnel_result):
        print("\n🎉 All tests passed! WebSocket connections are working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check server configuration and network.")
        print("For Cloudflare Tunnel issues, ensure:")
        print("• Tunnel is properly configured to forward WebSocket connections")
        print("• No conflicting proxy settings")
        print("• Firewall allows outbound connections")
        return 1

if __name__ == '__main__':
    sys.exit(main())