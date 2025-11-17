#!/usr/bin/env python3
"""Test Dahua DVR connection with provided credentials"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera_providers.dahua import DahuaProvider
from onvif_manager import ONVIFManager
import requests
from requests.auth import HTTPDigestAuth

# Test credentials
HOST = "10.65.52.7"
PORT = 80
USERNAME = "cubeworks"
PASSWORD = "Cub3w0rks"

print("=" * 60)
print("Testing Dahua DVR Connection")
print("=" * 60)
print(f"Host: {HOST}")
print(f"Port: {PORT}")
print(f"Username: {USERNAME}")
print()

# Test 1: Direct HTTP connection
print("Test 1: Testing HTTP connectivity...")
try:
    response = requests.get(f"http://{HOST}:{PORT}", timeout=5)
    print(f"✓ HTTP connection successful (Status: {response.status_code})")
except Exception as e:
    print(f"✗ HTTP connection failed: {e}")

# Test 2: Dahua CGI API
print("\nTest 2: Testing Dahua CGI API...")
try:
    base_url = f"http://{HOST}:{PORT}"
    info_url = f"{base_url}/cgi-bin/magicBox.cgi?action=getSystemInfo"
    auth = HTTPDigestAuth(USERNAME, PASSWORD)
    
    response = requests.get(info_url, auth=auth, timeout=10, verify=False)
    response.raise_for_status()
    print(f"✓ Dahua CGI API connection successful")
    print(f"  Response: {response.text[:200]}...")
except Exception as e:
    print(f"✗ Dahua CGI API failed: {e}")

# Test 3: Dahua Provider
print("\nTest 3: Testing Dahua Provider...")
try:
    provider = DahuaProvider()
    result = provider.connect(HOST, PORT, USERNAME, PASSWORD)
    if result.get('success'):
        print("✓ Dahua Provider connection successful")
        print(f"  Device Info: {result.get('device_info', {})}")
        print(f"  Profiles: {len(result.get('profiles', []))} profiles found")
        print(f"  Streams: {len(result.get('streams', []))} streams found")
    else:
        print(f"✗ Dahua Provider failed: {result.get('error')}")
except Exception as e:
    print(f"✗ Dahua Provider exception: {e}")
    import traceback
    traceback.print_exc()

# Test 4: ONVIF Connection
print("\nTest 4: Testing ONVIF connection...")
try:
    from onvif import ONVIFCamera
    camera = ONVIFCamera(HOST, PORT, USERNAME, PASSWORD)
    device_service = camera.create_devicemgmt_service()
    device_info = device_service.GetDeviceInformation()
    print("✓ ONVIF connection successful")
    print(f"  Manufacturer: {device_info.Manufacturer}")
    print(f"  Model: {device_info.Model}")
    print(f"  Firmware: {device_info.FirmwareVersion}")
except Exception as e:
    print(f"✗ ONVIF connection failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: ONVIF Manager
print("\nTest 5: Testing ONVIF Manager...")
try:
    manager = ONVIFManager()
    result = manager.connect_camera(HOST, PORT, USERNAME, PASSWORD)
    if result.get('success'):
        print("✓ ONVIF Manager connection successful")
        print(f"  Device Info: {result.get('device_info', {})}")
        print(f"  Profiles: {len(result.get('profiles', []))} profiles found")
    else:
        print(f"✗ ONVIF Manager failed: {result.get('error')}")
except Exception as e:
    print(f"✗ ONVIF Manager exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)

