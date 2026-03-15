#!/usr/bin/env python3
"""
Connection Stability Test Script
Tests Socket.IO connection reliability through various scenarios
"""

import asyncio
import aiohttp
import socketio
import time
import json
from typing import List, Dict
from datetime import datetime

class ConnectionTester:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.results: Dict[str, any] = {}
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_http_connectivity(self):
        """Test basic HTTP connectivity"""
        print("📡 Test 1: HTTP Connectivity")
        try:
            async with self.session.get(f"{self.server_url}/") as response:
                if response.status == 200:
                    print("  ✅ HTTP connectivity: OK")
                    self.results['http_connectivity'] = 'OK'
                    return True
                else:
                    print(f"  ❌ HTTP returned status {response.status}")
                    self.results['http_connectivity'] = f'FAILED ({response.status})'
                    return False
        except Exception as e:
            print(f"  ❌ HTTP connectivity failed: {e}")
            self.results['http_connectivity'] = f'FAILED ({str(e)})'
            return False
    
    async def test_diagnostics_endpoint(self):
        """Test diagnostics endpoint"""
        print("📊 Test 2: Diagnostics Endpoint")
        try:
            async with self.session.get(f"{self.server_url}/api/connection-diagnostics") as response:
                if response.status == 200:
                    data = await response.json()
                    print("  ✅ Diagnostics endpoint responding")
                    print(f"     - Server config: {data.get('server_config', {})}")
                    print(f"     - Active clients: {data.get('socket_io', {}).get('total_clients', 0)}")
                    self.results['diagnostics_endpoint'] = 'OK'
                    return True
                else:
                    print(f"  ❌ Diagnostics returned status {response.status}")
                    self.results['diagnostics_endpoint'] = f'FAILED ({response.status})'
                    return False
        except Exception as e:
            print(f"  ❌ Diagnostics failed: {e}")
            self.results['diagnostics_endpoint'] = f'FAILED ({str(e)})'
            return False
    
    async def test_socketio_connection(self):
        """Test Socket.IO connection stability"""
        print("🔌 Test 3: Socket.IO Connection")
        
        sio = socketio.AsyncClient(
            reconnection=False,  # Don't auto-reconnect for this test
            logger=False,
            engineio_logger=False
        )
        
        connected = False
        connection_transport = None
        
        @sio.event
        async def connect():
            nonlocal connected, connection_transport
            connected = True
            connection_transport = sio.engine.transport.name if hasattr(sio.engine, 'transport') else 'unknown'
            print(f"  ✅ Socket.IO connected using: {connection_transport}")
        
        @sio.event
        async def disconnect():
            nonlocal connected
            connected = False
            print(f"  ❌ Socket.IO disconnected unexpectedly")
        
        try:
            await asyncio.wait_for(sio.connect(self.server_url), timeout=10)
            self.results['socketio_connection'] = f'OK ({connection_transport})'
            await sio.disconnect()
            return True
        except asyncio.TimeoutError:
            print("  ❌ Socket.IO connection timeout")
            self.results['socketio_connection'] = 'FAILED (timeout)'
            return False
        except Exception as e:
            print(f"  ❌ Socket.IO connection failed: {e}")
            self.results['socketio_connection'] = f'FAILED ({str(e)})'
            return False
    
    async def test_connection_persistence(self, duration_seconds: int = 30):
        """Test if connection stays alive for extended period"""
        print(f"⏱️  Test 4: Connection Persistence ({duration_seconds}s)")
        
        sio = socketio.AsyncClient(
            reconnection=False,
            logger=False,
            engineio_logger=False
        )
        
        ping_count = 0
        pong_count = 0
        disconnect_reason = None
        
        @sio.on('ping')
        async def on_ping(data):
            nonlocal ping_count
            ping_count += 1
        
        @sio.on('pong')
        async def on_pong(data):
            nonlocal pong_count
            pong_count += 1
        
        @sio.event
        async def disconnect():
            nonlocal disconnect_reason
            disconnect_reason = 'Server disconnected'
        
        try:
            print(f"  Connecting...")
            await asyncio.wait_for(sio.connect(self.server_url), timeout=10)
            print(f"  Connected, monitoring for {duration_seconds}s...")
            
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                if not sio.connected:
                    print(f"  ❌ Disconnected after {time.time() - start_time:.1f}s: {disconnect_reason}")
                    self.results['connection_persistence'] = f'FAILED ({disconnect_reason})'
                    return False
                
                await asyncio.sleep(1)
            
            await sio.disconnect()
            print(f"  ✅ Connection stable for {duration_seconds}s")
            print(f"     - Pings received: {ping_count}")
            print(f"     - Pongs sent: {pong_count}")
            self.results['connection_persistence'] = 'OK'
            return True
            
        except Exception as e:
            print(f"  ❌ Persistence test failed: {e}")
            self.results['connection_persistence'] = f'FAILED ({str(e)})'
            return False
    
    async def test_rapid_reconnections(self, num_attempts: int = 5):
        """Test rapid connect/disconnect cycles"""
        print(f"🔄 Test 5: Rapid Reconnections ({num_attempts} attempts)")
        
        failures = 0
        times = []
        
        for i in range(num_attempts):
            sio = socketio.AsyncClient(
                reconnection=False,
                logger=False,
                engineio_logger=False
            )
            
            try:
                start = time.time()
                await asyncio.wait_for(sio.connect(self.server_url), timeout=10)
                elapsed = time.time() - start
                times.append(elapsed)
                await sio.disconnect()
                print(f"    Attempt {i+1}: ✅ {elapsed:.2f}s")
            except Exception as e:
                failures += 1
                print(f"    Attempt {i+1}: ❌ {str(e)}")
        
        success_rate = ((num_attempts - failures) / num_attempts) * 100
        if failures == 0:
            avg_time = sum(times) / len(times)
            print(f"  ✅ Success rate: {success_rate:.0f}%, Avg connection time: {avg_time:.2f}s")
            self.results['rapid_reconnections'] = 'OK'
            return True
        else:
            print(f"  ⚠️  Success rate: {success_rate:.0f}%")
            self.results['rapid_reconnections'] = f'PARTIAL ({num_attempts - failures}/{num_attempts})'
            return success_rate >= 80
    
    async def run_all_tests(self):
        """Run all connection tests"""
        print("=" * 60)
        print("🧪 SOCKET.IO CONNECTION STABILITY TEST SUITE")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        tests = [
            ("HTTP Connectivity", self.test_http_connectivity()),
            ("Diagnostics Endpoint", self.test_diagnostics_endpoint()),
            ("Socket.IO Connection", self.test_socketio_connection()),
            ("Connection Persistence (30s)", self.test_connection_persistence(30)),
            ("Rapid Reconnections (5x)", self.test_rapid_reconnections(5)),
        ]
        
        results = []
        for test_name, test_coro in tests:
            try:
                result = await test_coro
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test error: {e}")
                results.append((test_name, False))
            print()
        
        elapsed = time.time() - start_time
        
        # Print summary
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print()
        print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        print(f"Duration: {elapsed:.1f}s")
        print()
        
        # Detailed results
        print("Detailed Results:")
        print(json.dumps(self.results, indent=2))
        
        return passed == total

async def main():
    """Main entry point"""
    import sys
    
    # Check if server is specified
    server_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"Testing server: {server_url}\n")
    
    async with ConnectionTester(server_url) as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n✅ All tests passed! Connection is stable.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. See details above.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
