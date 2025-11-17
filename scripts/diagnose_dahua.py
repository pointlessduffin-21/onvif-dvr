#!/usr/bin/env python3
"""Diagnose Dahua XVR ONVIF connection and retrieve channel information"""

from onvif import ONVIFCamera
import json

def diagnose_dahua_camera(host, port, username, password):
    """Diagnose Dahua camera and retrieve all available information"""
    
    print(f"\n{'='*70}")
    print(f"Diagnosing Dahua XVR: {host}:{port}")
    print(f"{'='*70}\n")
    
    try:
        # Create camera connection
        print("✓ Connecting to camera...")
        camera = ONVIFCamera(host, port, username, password)
        print("  Connection successful!\n")
        
        # Get device information
        print("✓ Device Information:")
        device_service = camera.create_devicemgmt_service()
        device_info = device_service.GetDeviceInformation()
        print(f"  Manufacturer: {device_info.Manufacturer}")
        print(f"  Model: {device_info.Model}")
        print(f"  Firmware: {device_info.FirmwareVersion}")
        print(f"  Serial: {device_info.SerialNumber}\n")
        
        # Get media service
        print("✓ Creating media service...")
        media_service = camera.create_media_service()
        print("  Media service created\n")
        
        # Method 1: Try GetProfiles
        print("✓ Method 1: Getting profiles via GetProfiles()...")
        try:
            profiles = media_service.GetProfiles()
            print(f"  Found {len(profiles)} profile(s)")
            
            if len(profiles) == 0:
                print("  WARNING: GetProfiles() returned empty list!")
                print("  This is common with Dahua XVRs - trying alternative methods...\n")
            else:
                for i, profile in enumerate(profiles):
                    print(f"\n  Profile {i+1}:")
                    print(f"  - Token: {profile.token}")
                    print(f"  - Name: {profile.Name}")
        except Exception as e:
            print(f"  ERROR: {str(e)}\n")
        
        # Method 2: Try GetVideoSources
        print("\n✓ Method 2: Getting video sources via GetVideoSources()...")
        try:
            video_sources = media_service.GetVideoSources()
            print(f"  Found {len(video_sources)} video source(s)")
            
            for i, source in enumerate(video_sources):
                print(f"\n  Video Source {i+1}:")
                print(f"  - Token: {source.token}")
                if hasattr(source, 'Framerate'):
                    print(f"  - Framerate: {source.Framerate}")
                if hasattr(source, 'Resolution'):
                    print(f"  - Resolution: {source.Resolution.Width}x{source.Resolution.Height}")
                
                # Try to create a profile for this source
                print(f"\n  Attempting to get stream URI for source: {source.token}")
                try:
                    # Method A: Try with source token directly
                    stream_setup = media_service.create_type('GetStreamUri')
                    stream_setup.ProfileToken = source.token
                    stream_setup.StreamSetup = {
                        'Stream': 'RTP-Unicast',
                        'Transport': {'Protocol': 'RTSP'}
                    }
                    stream_uri = media_service.GetStreamUri(stream_setup)
                    print(f"  ✓ Stream URI: {stream_uri.Uri}")
                except Exception as e:
                    print(f"  ✗ Could not get stream URI: {str(e)}")
                    
        except Exception as e:
            print(f"  ERROR: {str(e)}\n")
        
        # Method 3: Try GetStreamUri with different profile tokens
        print("\n✓ Method 3: Trying common Dahua profile tokens...")
        common_tokens = [
            'Profile_1', 'Profile_2', 'Profile_3', 'Profile_4',
            'MainStream', 'SubStream', 
            'Channel1MainStream', 'Channel1SubStream',
            'Profile000', 'Profile001', 'Profile002', 'Profile003'
        ]
        
        for token in common_tokens:
            try:
                stream_setup = media_service.create_type('GetStreamUri')
                stream_setup.ProfileToken = token
                stream_setup.StreamSetup = {
                    'Stream': 'RTP-Unicast',
                    'Transport': {'Protocol': 'RTSP'}
                }
                stream_uri = media_service.GetStreamUri(stream_setup)
                print(f"  ✓ Found stream with token '{token}':")
                print(f"    URI: {stream_uri.Uri}")
            except:
                pass
        
        # Method 4: Get capabilities
        print("\n✓ Method 4: Checking device capabilities...")
        try:
            capabilities = device_service.GetCapabilities()
            
            if capabilities.Media:
                print(f"  Media XAddr: {capabilities.Media.XAddr}")
                
                # Try to get streaming capabilities
                if hasattr(capabilities.Media, 'StreamingCapabilities'):
                    print(f"  Streaming Capabilities: {capabilities.Media.StreamingCapabilities}")
            
            if capabilities.PTZ:
                print(f"  PTZ XAddr: {capabilities.PTZ.XAddr}")
                
        except Exception as e:
            print(f"  ERROR: {str(e)}")
        
        # Method 5: Try GetServiceCapabilities
        print("\n✓ Method 5: Getting service capabilities...")
        try:
            service_caps = media_service.GetServiceCapabilities()
            print(f"  Service Capabilities: {service_caps}")
        except Exception as e:
            print(f"  ERROR: {str(e)}")
        
        print(f"\n{'='*70}")
        print("Diagnosis Complete!")
        print(f"{'='*70}\n")
        
        print("RECOMMENDATIONS:")
        print("1. If video sources were found, the XVR has channels available")
        print("2. If no profiles found, this is normal for some Dahua XVRs")
        print("3. You may need to access channels directly using video source tokens")
        print("4. Check if you can access the RTSP stream directly:")
        print(f"   rtsp://{username}:{password}@{host}:554/cam/realmonitor?channel=1&subtype=0")
        print()
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Your camera details
    host = '192.168.1.108'
    port = 80
    username = 'admin'
    password = '1qaz2wsx'
    
    diagnose_dahua_camera(host, port, username, password)
