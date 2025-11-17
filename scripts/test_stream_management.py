#!/usr/bin/env python3
"""
Test script for improved stream management
"""
import requests
import time
import json

BASE_URL = "http://localhost:8821"

def test_rapid_play_clicks():
    """Test that rapid play clicks don't cause errors"""
    print("Test 1: Rapid Play Clicks")
    print("-" * 50)
    
    # Start stream 5 times rapidly
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/api/streams/start",
            json={
                "camera_id": 1,
                "profile_token": "MediaProfile00000"
            }
        )
        
        print(f"Attempt {i+1}: Status {response.status_code}")
        data = response.json()
        print(f"  - Success: {data.get('success')}")
        print(f"  - Already running: {data.get('already_running', False)}")
        if 'uptime' in data:
            print(f"  - Uptime: {data.get('uptime'):.2f}s")
        
        time.sleep(0.2)  # Small delay between requests
    
    print("\n✅ Test 1 passed if all returned status 200 with success=True\n")


def test_stream_info():
    """Test getting stream info"""
    print("Test 2: Get Stream Info")
    print("-" * 50)
    
    stream_id = "camera1_MediaProfile00000"
    response = requests.get(f"{BASE_URL}/api/streams/status/{stream_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Stream ID: {data.get('stream_id')}")
        print(f"Active: {data.get('is_active')}")
        print(f"Uptime: {data.get('uptime', 0):.2f}s")
        print(f"Playlist URL: {data.get('playlist_url')}")
        print("\n✅ Test 2 passed\n")
    else:
        print(f"❌ Test 2 failed: Status {response.status_code}\n")


def test_all_streams():
    """Test getting all active streams"""
    print("Test 3: Get All Active Streams")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/api/streams/all")
    
    if response.status_code == 200:
        streams = response.json()
        print(f"Active streams: {len(streams)}")
        for stream_id, info in streams.items():
            print(f"\n  {stream_id}:")
            print(f"    - Active: {info.get('is_active')}")
            print(f"    - Uptime: {info.get('uptime', 0):.2f}s")
        print("\n✅ Test 3 passed\n")
    else:
        print(f"❌ Test 3 failed: Status {response.status_code}\n")


def test_cleanup():
    """Test manual cleanup"""
    print("Test 4: Manual Cleanup")
    print("-" * 50)
    
    response = requests.post(f"{BASE_URL}/api/streams/cleanup")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Cleanup result: {data.get('message')}")
        print(f"Streams cleaned: {data.get('cleaned_up')}")
        print("\n✅ Test 4 passed\n")
    else:
        print(f"❌ Test 4 failed: Status {response.status_code}\n")


def test_stop_stream():
    """Test stopping a stream"""
    print("Test 5: Stop Stream")
    print("-" * 50)
    
    stream_id = "camera1_MediaProfile00000"
    response = requests.post(
        f"{BASE_URL}/api/streams/stop",
        json={"stream_id": stream_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Stop result: Success = {data.get('success')}")
        print("\n✅ Test 5 passed\n")
    else:
        print(f"❌ Test 5 failed: Status {response.status_code}\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Stream Management Tests")
    print("=" * 50)
    print()
    
    try:
        # Test 1: Rapid clicks
        test_rapid_play_clicks()
        time.sleep(1)
        
        # Test 2: Get stream info
        test_stream_info()
        time.sleep(1)
        
        # Test 3: List all streams
        test_all_streams()
        time.sleep(1)
        
        # Test 4: Manual cleanup
        test_cleanup()
        time.sleep(1)
        
        # Test 5: Stop stream
        test_stop_stream()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server")
        print("Make sure the server is running on http://localhost:8821")
    except Exception as e:
        print(f"\n❌ Error: {e}")
