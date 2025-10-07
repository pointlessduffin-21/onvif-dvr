#!/usr/bin/env python3
"""Refresh camera profiles and streams in database"""

from onvif import ONVIFCamera
import sqlite3
import json
from database import get_db_connection

def refresh_camera_profiles(camera_id):
    """Refresh profiles and streams for a camera"""
    
    conn = get_db_connection()
    
    # Get camera details
    camera = conn.execute('SELECT * FROM cameras WHERE id = ?', (camera_id,)).fetchone()
    
    if not camera:
        print(f"Camera with ID {camera_id} not found!")
        return False
    
    print(f"\n{'='*60}")
    print(f"Refreshing profiles for: {camera['name']}")
    print(f"Host: {camera['host']}:{camera['port']}")
    print(f"{'='*60}\n")
    
    try:
        # Connect to camera
        print("1. Connecting to camera...")
        onvif_camera = ONVIFCamera(camera['host'], camera['port'], 
                                   camera['username'], camera['password'])
        print("   ✓ Connected\n")
        
        # Get media profiles
        print("2. Getting media profiles...")
        media_service = onvif_camera.create_media_service()
        profiles = media_service.GetProfiles()
        print(f"   ✓ Found {len(profiles)} profiles\n")
        
        # Clear existing profiles and streams
        print("3. Clearing existing profiles and streams...")
        conn.execute('DELETE FROM camera_profiles WHERE camera_id = ?', (camera_id,))
        conn.execute('DELETE FROM video_streams WHERE camera_id = ?', (camera_id,))
        print("   ✓ Cleared\n")
        
        # Insert new profiles
        print("4. Inserting profiles...")
        profile_list = []
        
        for i, profile in enumerate(profiles):
            print(f"   Processing profile {i+1}/{len(profiles)}: {profile.Name}")
            
            # Extract profile data
            profile_data = {
                'token': profile.token,
                'name': profile.Name,
                'video_encoder': None,
                'video_source': None,
                'audio_encoder': None,
                'ptz': None
            }
            
            if hasattr(profile, 'VideoEncoderConfiguration') and profile.VideoEncoderConfiguration:
                vec = profile.VideoEncoderConfiguration
                profile_data['video_encoder'] = {
                    'token': vec.token if hasattr(vec, 'token') else None,
                    'name': vec.Name if hasattr(vec, 'Name') else None,
                    'encoding': vec.Encoding if hasattr(vec, 'Encoding') else None,
                    'resolution': {
                        'width': vec.Resolution.Width if vec.Resolution else 0,
                        'height': vec.Resolution.Height if vec.Resolution else 0
                    } if hasattr(vec, 'Resolution') and vec.Resolution else {'width': 0, 'height': 0},
                    'quality': vec.Quality if hasattr(vec, 'Quality') else 0,
                    'framerate_limit': vec.RateControl.FrameRateLimit if hasattr(vec, 'RateControl') and vec.RateControl else 0,
                    'bitrate_limit': vec.RateControl.BitrateLimit if hasattr(vec, 'RateControl') and vec.RateControl else 0
                }
            
            if hasattr(profile, 'VideoSourceConfiguration') and profile.VideoSourceConfiguration:
                vsc = profile.VideoSourceConfiguration
                profile_data['video_source'] = {
                    'token': vsc.token,
                    'name': vsc.Name,
                    'source_token': vsc.SourceToken
                }
            
            if hasattr(profile, 'AudioEncoderConfiguration') and profile.AudioEncoderConfiguration:
                profile_data['audio_encoder'] = {
                    'token': profile.AudioEncoderConfiguration.token,
                    'name': profile.AudioEncoderConfiguration.Name
                }
            
            if hasattr(profile, 'PTZConfiguration') and profile.PTZConfiguration:
                profile_data['ptz'] = {
                    'token': profile.PTZConfiguration.token,
                    'name': profile.PTZConfiguration.Name
                }
            
            profile_list.append(profile_data)
            
            # Insert profile
            conn.execute('''
                INSERT INTO camera_profiles (camera_id, profile_token, profile_name, 
                                            profile_type, video_encoder_config, video_source_config,
                                            audio_encoder_config, ptz_config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                camera_id,
                profile_data['token'],
                profile_data['name'],
                'Media',
                json.dumps(profile_data.get('video_encoder', {})),
                json.dumps(profile_data.get('video_source', {})),
                json.dumps(profile_data.get('audio_encoder', {})),
                json.dumps(profile_data.get('ptz', {}))
            ))
            
            # Get stream URI
            try:
                stream_setup = media_service.create_type('GetStreamUri')
                stream_setup.ProfileToken = profile.token
                stream_setup.StreamSetup = {
                    'Stream': 'RTP-Unicast',
                    'Transport': {'Protocol': 'RTSP'}
                }
                stream_uri = media_service.GetStreamUri(stream_setup)
                
                # Extract resolution and codec
                resolution = None
                codec = None
                framerate = None
                bitrate = None
                
                if profile_data['video_encoder']:
                    resolution = json.dumps(profile_data['video_encoder']['resolution'])
                    codec = profile_data['video_encoder']['encoding']
                    framerate = profile_data['video_encoder']['framerate_limit']
                    bitrate = profile_data['video_encoder']['bitrate_limit']
                
                # Insert stream
                conn.execute('''
                    INSERT INTO video_streams (camera_id, profile_token, stream_uri, 
                                              stream_type, protocol, resolution, framerate,
                                              bitrate, codec, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    camera_id,
                    profile.token,
                    stream_uri.Uri,
                    'RTP-Unicast',
                    'RTSP',
                    resolution,
                    framerate,
                    bitrate,
                    codec,
                    0
                ))
                
                print(f"      ✓ Stream URI: {stream_uri.Uri[:60]}...")
                
            except Exception as e:
                print(f"      ✗ Could not get stream URI: {str(e)}")
        
        # Update camera with profiles_supported
        conn.execute('''
            UPDATE cameras 
            SET profiles_supported = ?, status = 'online'
            WHERE id = ?
        ''', (json.dumps(profile_list), camera_id))
        
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"✓ Successfully refreshed {len(profiles)} profiles!")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # Refresh camera ID 1
    refresh_camera_profiles(1)
