from onvif import ONVIFCamera  # type: ignore
from onvif.exceptions import ONVIFError  # type: ignore
import socket
import json
from datetime import datetime
from database import get_db_connection

class ONVIFManager:
    """Manager class for ONVIF camera operations"""
    
    def __init__(self):
        self.cameras = {}
    
    def connect_camera(self, host, port, username, password):
        """Connect to an ONVIF camera"""
        try:
            camera = ONVIFCamera(host, port, username, password)
            
            # Get device information
            device_info = self.get_device_info(camera)
            
            # Get supported profiles
            profiles = self.get_profiles(camera)
            
            return {
                'success': True,
                'camera': camera,
                'device_info': device_info,
                'profiles': profiles
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_device_info(self, camera):
        """Get device information"""
        try:
            device_service = camera.create_devicemgmt_service()
            device_info = device_service.GetDeviceInformation()
            
            return {
                'manufacturer': device_info.Manufacturer,
                'model': device_info.Model,
                'firmware_version': device_info.FirmwareVersion,
                'serial_number': device_info.SerialNumber
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def _serialize_profile(self, profile):
        """Convert a raw profile into a serializable dict with safe attribute access"""
        def safe_attr(obj, attr, default=None):
            return getattr(obj, attr, default) if obj is not None else default

        profile_data = {
            'token': getattr(profile, 'token', None),
            'name': getattr(profile, 'Name', None),
            'video_encoder': None,
            'video_source': None,
            'audio_encoder': None,
            'ptz': None
        }

        video_encoder = safe_attr(profile, 'VideoEncoderConfiguration')
        if video_encoder:
            resolution = safe_attr(video_encoder, 'Resolution')
            rate_control = safe_attr(video_encoder, 'RateControl')
            profile_data['video_encoder'] = {
                'token': safe_attr(video_encoder, 'token'),
                'name': safe_attr(video_encoder, 'Name'),
                'encoding': safe_attr(video_encoder, 'Encoding'),
                'resolution': {
                    'width': safe_attr(resolution, 'Width', 0),
                    'height': safe_attr(resolution, 'Height', 0)
                } if resolution else {'width': 0, 'height': 0},
                'quality': safe_attr(video_encoder, 'Quality', 0),
                'framerate_limit': safe_attr(rate_control, 'FrameRateLimit'),
                'bitrate_limit': safe_attr(rate_control, 'BitrateLimit')
            }

        video_source = safe_attr(profile, 'VideoSourceConfiguration')
        if video_source:
            profile_data['video_source'] = {
                'token': safe_attr(video_source, 'token'),
                'name': safe_attr(video_source, 'Name'),
                'source_token': safe_attr(video_source, 'SourceToken')
            }

        audio_encoder = safe_attr(profile, 'AudioEncoderConfiguration')
        if audio_encoder:
            profile_data['audio_encoder'] = {
                'token': safe_attr(audio_encoder, 'token'),
                'name': safe_attr(audio_encoder, 'Name')
            }

        ptz_config = safe_attr(profile, 'PTZConfiguration')
        if ptz_config:
            profile_data['ptz'] = {
                'token': safe_attr(ptz_config, 'token'),
                'name': safe_attr(ptz_config, 'Name')
            }

        return profile_data

    def get_profiles(self, camera):
        """Get media profiles from camera"""
        try:
            media_service = camera.create_media_service()
            profiles = media_service.GetProfiles()

            profile_list = []
            for profile in profiles:
                profile_list.append(self._serialize_profile(profile))

            return profile_list
        except Exception as e:
            return []
    
    def get_stream_uri(self, camera, profile_token, stream_type='RTP-Unicast', protocol='RTSP'):
        """Get stream URI for a profile (Profile S, T)"""
        try:
            media_service = camera.create_media_service()
            
            # Create stream setup
            stream_setup = media_service.create_type('GetStreamUri')
            stream_setup.ProfileToken = profile_token
            stream_setup.StreamSetup = {
                'Stream': stream_type,
                'Transport': {'Protocol': protocol}
            }
            
            stream_uri = media_service.GetStreamUri(stream_setup)
            return stream_uri.Uri
        except Exception as e:
            return None
    
    def get_recordings(self, camera):
        """Get recordings from camera (Profile G)"""
        try:
            recording_service = camera.create_recording_service()
            recordings = recording_service.GetRecordings()
            
            recording_list = []
            for recording in recordings:
                recording_data = {
                    'token': recording.RecordingToken,
                    'configuration': recording.Configuration,
                    'tracks': recording.Tracks
                }
                recording_list.append(recording_data)
            
            return recording_list
        except Exception as e:
            return []
    
    def get_access_control_info(self, camera):
        """Get access control information (Profile C, A)"""
        try:
            # Try to create access control service
            access_control_service = camera.create_accesscontrol_service()
            
            # Get access points
            access_points = access_control_service.GetAccessPointList()
            
            access_point_list = []
            for ap in access_points.AccessPointInfo:
                access_point_data = {
                    'token': ap.token,
                    'name': ap.Name,
                    'description': ap.Description if hasattr(ap, 'Description') else '',
                    'capabilities': ap.Capabilities if hasattr(ap, 'Capabilities') else None
                }
                access_point_list.append(access_point_data)
            
            return access_point_list
        except Exception as e:
            return []
    
    def get_events(self, camera):
        """Get events from camera (Profile M)"""
        try:
            event_service = camera.create_events_service()
            
            # Get event properties
            properties = event_service.GetEventProperties()
            
            return {
                'topics': properties.TopicSet if hasattr(properties, 'TopicSet') else [],
                'message_description': properties.MessageDescription if hasattr(properties, 'MessageDescription') else []
            }
        except Exception as e:
            return {}
    
    def get_analytics_configs(self, camera):
        """Get analytics configurations (Profile M)"""
        try:
            analytics_service = camera.create_analytics_service()
            
            # Get supported analytics modules
            modules = analytics_service.GetSupportedAnalyticsModules()
            
            module_list = []
            for module in modules:
                module_data = {
                    'name': module.Name,
                    'type': module.Type if hasattr(module, 'Type') else None
                }
                module_list.append(module_data)
            
            return module_list
        except Exception as e:
            return []
    
    def get_peripherals(self, camera):
        """Get peripheral device information (Profile D)"""
        try:
            # Try to create door control or other peripheral services
            door_control_service = camera.create_doorcontrol_service()
            
            # Get door info
            door_info = door_control_service.GetDoorInfoList()
            
            peripheral_list = []
            for door in door_info.DoorInfo:
                peripheral_data = {
                    'token': door.token,
                    'name': door.Name,
                    'type': 'Door',
                    'description': door.Description if hasattr(door, 'Description') else ''
                }
                peripheral_list.append(peripheral_data)
            
            return peripheral_list
        except Exception as e:
            return []
    
    def get_ptz_presets(self, camera, profile_token):
        """Get PTZ presets"""
        try:
            ptz_service = camera.create_ptz_service()
            presets = ptz_service.GetPresets({'ProfileToken': profile_token})
            
            preset_list = []
            for preset in presets:
                preset_data = {
                    'token': preset.token,
                    'name': preset.Name,
                    'pan': preset.PTZPosition.PanTilt.x if hasattr(preset, 'PTZPosition') else None,
                    'tilt': preset.PTZPosition.PanTilt.y if hasattr(preset, 'PTZPosition') else None,
                    'zoom': preset.PTZPosition.Zoom.x if hasattr(preset, 'PTZPosition') else None
                }
                preset_list.append(preset_data)
            
            return preset_list
        except Exception as e:
            return []
    
    def discover_cameras(self, timeout=5):
        """Discover ONVIF cameras on the network"""
        try:
            from onvif import ONVIFService  # type: ignore
            
            discovered = []
            # Note: Discovery requires WS-Discovery which may need additional setup
            # This is a placeholder for discovery functionality
            return discovered
        except Exception as e:
            return []
    
    def save_camera_to_db(self, camera_data, device_info, profiles):
        """Save camera configuration to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert camera
            cursor.execute('''
                INSERT INTO cameras (name, host, port, username, password, manufacturer, 
                                    model, firmware_version, serial_number, profiles_supported, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                camera_data['name'],
                camera_data['host'],
                camera_data['port'],
                camera_data['username'],
                camera_data['password'],
                device_info.get('manufacturer', ''),
                device_info.get('model', ''),
                device_info.get('firmware_version', ''),
                device_info.get('serial_number', ''),
                json.dumps(profiles),
                'online'
            ))
            
            camera_id = cursor.lastrowid
            
            # Insert profiles
            for profile in profiles:
                cursor.execute('''
                    INSERT INTO camera_profiles (camera_id, profile_token, profile_name, 
                                                profile_type, video_encoder_config, video_source_config,
                                                audio_encoder_config, ptz_config)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    camera_id,
                    profile['token'],
                    profile['name'],
                    'Media',
                    json.dumps(profile.get('video_encoder', {})),
                    json.dumps(profile.get('video_source', {})),
                    json.dumps(profile.get('audio_encoder', {})),
                    json.dumps(profile.get('ptz', {}))
                ))
            
            conn.commit()
            return camera_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def refresh_camera_profiles(self, camera_row):
        """Refresh profiles and stream information for an existing camera"""
        camera_data = dict(camera_row)
        camera_id = camera_data['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            onvif_camera = ONVIFCamera(
                camera_data['host'],
                camera_data['port'],
                camera_data['username'],
                camera_data['password']
            )

            media_service = onvif_camera.create_media_service()
            profiles = media_service.GetProfiles()

            # Clear existing profile and stream records
            cursor.execute('DELETE FROM camera_profiles WHERE camera_id = ?', (camera_id,))
            cursor.execute('DELETE FROM video_streams WHERE camera_id = ?', (camera_id,))

            profile_payload = []

            for profile in profiles:
                serialized_profile = self._serialize_profile(profile)
                profile_payload.append(serialized_profile)

                cursor.execute('''
                    INSERT INTO camera_profiles (camera_id, profile_token, profile_name,
                                                profile_type, video_encoder_config, video_source_config,
                                                audio_encoder_config, ptz_config)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    camera_id,
                    serialized_profile['token'],
                    serialized_profile['name'],
                    'Media',
                    json.dumps(serialized_profile.get('video_encoder', {})),
                    json.dumps(serialized_profile.get('video_source', {})),
                    json.dumps(serialized_profile.get('audio_encoder', {})),
                    json.dumps(serialized_profile.get('ptz', {}))
                ))

                # Fetch stream URI for the profile
                stream_uri = self.get_stream_uri(onvif_camera, serialized_profile['token'])

                resolution = None
                framerate = None
                bitrate = None
                codec = None

                video_encoder = serialized_profile.get('video_encoder') or {}
                if video_encoder:
                    resolution = json.dumps(video_encoder.get('resolution', {}))
                    framerate = video_encoder.get('framerate_limit')
                    bitrate = video_encoder.get('bitrate_limit')
                    codec = video_encoder.get('encoding')

                cursor.execute('''
                    INSERT INTO video_streams (camera_id, profile_token, stream_uri,
                                              stream_type, protocol, resolution, framerate,
                                              bitrate, codec, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    camera_id,
                    serialized_profile['token'],
                    stream_uri or '',
                    'RTP-Unicast',
                    'RTSP',
                    resolution,
                    framerate,
                    bitrate,
                    codec,
                    0
                ))

            device_info = self.get_device_info(onvif_camera)
            manufacturer = device_info.get('manufacturer') if isinstance(device_info, dict) else camera_data.get('manufacturer')
            model = device_info.get('model') if isinstance(device_info, dict) else camera_data.get('model')
            firmware = device_info.get('firmware_version') if isinstance(device_info, dict) else camera_data.get('firmware_version')
            serial_number = device_info.get('serial_number') if isinstance(device_info, dict) else camera_data.get('serial_number')

            cursor.execute('''
                UPDATE cameras
                SET manufacturer = ?,
                    model = ?,
                    firmware_version = ?,
                    serial_number = ?,
                    profiles_supported = ?,
                    status = 'online',
                    updated_at = ?
                WHERE id = ?
            ''', (
                manufacturer,
                model,
                firmware,
                serial_number,
                json.dumps(profile_payload),
                datetime.now().isoformat(),
                camera_id
            ))

            conn.commit()

            return {
                'camera_id': camera_id,
                'profiles_refreshed': len(profile_payload)
            }
        except Exception as e:
            conn.rollback()
            cursor.execute('''
                UPDATE cameras
                SET status = 'offline',
                    updated_at = ?
                WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                camera_id
            ))
            conn.commit()
            raise e
        finally:
            conn.close()
