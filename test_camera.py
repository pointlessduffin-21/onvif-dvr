#!/usr/bin/env python3
"""Test ONVIF camera connection and retrieve all available information"""

from onvif import ONVIFCamera
import sys

def test_camera_connection(host, port, username, password):
    """Test connection to ONVIF camera and display all info"""
    
    print(f"\n{'='*60}")
    print(f"Testing ONVIF Camera: {host}:{port}")
    print(f"{'='*60}\n")
    
    try:
        # Create camera connection
        print("1. Connecting to camera...")
        camera = ONVIFCamera(host, port, username, password)
        print("   ✓ Connection successful!\n")
        
        # Get device information
        print("2. Getting device information...")
        device_service = camera.create_devicemgmt_service()
        device_info = device_service.GetDeviceInformation()
        print(f"   Manufacturer: {device_info.Manufacturer}")
        print(f"   Model: {device_info.Model}")
        print(f"   Firmware: {device_info.FirmwareVersion}")
        print(f"   Serial: {device_info.SerialNumber}")
        print()
        
        # Get capabilities
        print("3. Getting capabilities...")
        capabilities = device_service.GetCapabilities()
        print(f"   Media: {capabilities.Media is not None}")
        print(f"   PTZ: {capabilities.PTZ is not None}")
        print(f"   Events: {capabilities.Events is not None}")
        print()
        
        # Get media profiles
        print("4. Getting media profiles...")
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        print(f"   Found {len(profiles)} profile(s):\n")
        
        for i, profile in enumerate(profiles):
            print(f"   Profile {i+1}:")
            print(f"   - Token: {profile.token}")
            print(f"   - Name: {profile.Name}")
            
            if hasattr(profile, 'VideoEncoderConfiguration') and profile.VideoEncoderConfiguration:
                vec = profile.VideoEncoderConfiguration
                print(f"   - Video Encoding: {vec.Encoding}")
                print(f"   - Resolution: {vec.Resolution.Width}x{vec.Resolution.Height}")
                print(f"   - Framerate: {vec.RateControl.FrameRateLimit}")
                print(f"   - Bitrate: {vec.RateControl.BitrateLimit}")
            
            if hasattr(profile, 'VideoSourceConfiguration') and profile.VideoSourceConfiguration:
                vsc = profile.VideoSourceConfiguration
                print(f"   - Video Source: {vsc.SourceToken}")
            
            # Get stream URI
            try:
                stream_setup = media_service.create_type('GetStreamUri')
                stream_setup.ProfileToken = profile.token
                stream_setup.StreamSetup = {
                    'Stream': 'RTP-Unicast',
                    'Transport': {'Protocol': 'RTSP'}
                }
                stream_uri = media_service.GetStreamUri(stream_setup)
                print(f"   - Stream URI: {stream_uri.Uri}")
            except Exception as e:
                print(f"   - Stream URI: Error - {str(e)}")
            
            print()
        
        # Get video sources
        print("5. Getting video sources...")
        try:
            video_sources = media_service.GetVideoSources()
            print(f"   Found {len(video_sources)} video source(s):\n")
            for i, source in enumerate(video_sources):
                print(f"   Source {i+1}:")
                print(f"   - Token: {source.token}")
                print(f"   - Framerate: {source.Framerate}")
                print(f"   - Resolution: {source.Resolution.Width}x{source.Resolution.Height}")
                print()
        except Exception as e:
            print(f"   Error: {str(e)}\n")
        
        # Try to get PTZ info
        print("6. Checking PTZ support...")
        try:
            ptz_service = camera.create_ptz_service()
            print("   ✓ PTZ service available")
        except Exception as e:
            print(f"   ✗ PTZ not available: {str(e)}")
        print()
        
        # Try to get events
        print("7. Checking events support...")
        try:
            events_service = camera.create_events_service()
            print("   ✓ Events service available")
        except Exception as e:
            print(f"   ✗ Events not available: {str(e)}")
        print()
        
        print(f"{'='*60}")
        print("Test completed successfully!")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print(f"\nException type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Test with your camera
    host = '192.168.1.108'
    port = 80
    username = 'admin'
    password = '1qaz2wsx'
    
    print("\nONVIF Camera Connection Test")
    print(f"Camera: {username}@{host}:{port}")
    
    success = test_camera_connection(host, port, username, password)
    
    sys.exit(0 if success else 1)
