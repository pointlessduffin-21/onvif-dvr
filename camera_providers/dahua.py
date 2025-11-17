"""
Dahua CGI integration
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPDigestAuth

from .base import BaseCameraProvider


class DahuaProvider(BaseCameraProvider):
    key = "dahua"
    display_name = "Dahua CGI"
    connection_type = "dahua-cgi"
    default_port = 80
    supported_features = ["device-info", "rtsp", "snapshot"]

    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        options: Optional[Dict[str, Any]] = None
    ):
        options = options or {}
        timeout = options.get('timeout', 10)
        use_https = options.get('use_https', False)
        scheme = 'https' if use_https else 'http'

        base_url = f"{scheme}://{host}:{port}"
        info_url = f"{base_url}/cgi-bin/magicBox.cgi?action=getSystemInfo"

        auth = HTTPDigestAuth(username, password)

        try:
            response = requests.get(info_url, auth=auth, timeout=timeout, verify=False if use_https else True)
            response.raise_for_status()
        except Exception as exc:
            return {
                'success': False,
                'error': f'Dahua connection failed: {exc}'
            }

        device_info = self._parse_device_info(response.text)

        # Try to detect number of channels
        channels = self._detect_channels(base_url, auth, timeout)
        if not channels:
            # Fallback to default channel 1 if detection fails
            channels = [1]
        
        streams = self._build_streams(host, channels)
        profiles = self._build_profiles(streams)

        return {
            'success': True,
            'device_info': device_info,
            'profiles': profiles,
            'streams': streams,
            'vendor': 'dahua',
            'connection_type': self.connection_type,
            'extra_config': {
                'base_url': base_url,
                'supports_https': use_https,
                'channels': options.get('channels', [1]),
            }
        }

    def _parse_device_info(self, payload: str) -> Dict[str, Any]:
        """Parse key-value response from Dahua magicBox API"""
        info = {
            'manufacturer': 'Dahua',
            'model': '',
            'serial_number': '',
            'firmware_version': ''
        }

        for line in payload.splitlines():
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key == 'DeviceType':
                info['model'] = value
            elif key == 'HardwareVersion':
                info['firmware_version'] = value
            elif key == 'SerialNumber':
                info['serial_number'] = value

        return info

    def _detect_channels(self, base_url: str, auth: HTTPDigestAuth, timeout: int) -> list:
        """
        Detect available channels on Dahua DVR/NVR
        Tries multiple methods to determine channel count
        """
        channels = []
        
        # Method 1: Try to get channel count from config API
        try:
            config_url = f"{base_url}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelCount"
            response = requests.get(config_url, auth=auth, timeout=timeout, verify=False)
            if response.status_code == 200:
                # Parse response to find channel count
                for line in response.text.splitlines():
                    if 'ChannelCount' in line or 'channelCount' in line.lower():
                        try:
                            # Extract number from response
                            import re
                            numbers = re.findall(r'\d+', line)
                            if numbers:
                                count = int(numbers[0])
                                channels = list(range(1, count + 1))
                                break
                        except:
                            pass
        except:
            pass
        
        # Method 2: Try to probe channels (test channels 1-32)
        if not channels:
            try:
                # Test up to 32 channels (common DVR limit)
                for ch in range(1, 33):
                    test_url = f"{base_url}/cgi-bin/magicBox.cgi?action=getDeviceClass&channel={ch}"
                    try:
                        test_response = requests.get(test_url, auth=auth, timeout=2, verify=False)
                        if test_response.status_code == 200 and 'error' not in test_response.text.lower():
                            channels.append(ch)
                    except:
                        continue
            except:
                pass
        
        # Method 3: Try ONVIF-like channel enumeration
        if not channels:
            try:
                # Some Dahua devices support this
                enum_url = f"{base_url}/cgi-bin/configManager.cgi?action=getConfig&name=VideoInput"
                enum_response = requests.get(enum_url, auth=auth, timeout=timeout, verify=False)
                if enum_response.status_code == 200:
                    import re
                    # Look for channel numbers in response
                    found_channels = re.findall(r'channel[=:](\d+)', enum_response.text, re.IGNORECASE)
                    if found_channels:
                        channels = sorted(set(int(ch) for ch in found_channels))
            except:
                pass
        
        return channels if channels else [1]  # Default to channel 1 if detection fails
    
    def _build_streams(self, host: str, channels: list):
        """
        Build streams for all detected channels
        Dahua RTSP syntax:
        rtsp://<host>:554/cam/realmonitor?channel=<id>&subtype=<stream>
            subtype 0 = main, 1 = sub
        """
        streams = []
        
        for channel_num in channels:
            # Main stream (high quality)
            main_token = f"dahua-channel{channel_num}-main"
            main_uri = f"rtsp://{host}:554/cam/realmonitor?channel={channel_num}&subtype=0"
            streams.append({
                'profile_token': main_token,
                'name': f'Channel {channel_num} - Main Stream',
                'stream_uri': main_uri,
                'stream_type': 'RTP-Unicast',
                'protocol': 'RTSP',
                'codec': 'H.264',
                'resolution': {},
                'profile_type': 'Dahua',
                'vendor': 'dahua',
                'channel': str(channel_num)
            })
            
            # Sub stream (low quality, for remote viewing)
            sub_token = f"dahua-channel{channel_num}-sub"
            sub_uri = f"rtsp://{host}:554/cam/realmonitor?channel={channel_num}&subtype=1"
            streams.append({
                'profile_token': sub_token,
                'name': f'Channel {channel_num} - Sub Stream',
                'stream_uri': sub_uri,
                'stream_type': 'RTP-Unicast',
                'protocol': 'RTSP',
                'codec': 'H.264',
                'resolution': {},
                'profile_type': 'Dahua',
                'vendor': 'dahua',
                'channel': str(channel_num)
            })
        
        return streams

    def _build_profiles(self, streams):
        profiles = []
        for stream in streams:
            profiles.append({
                'token': stream['profile_token'],
                'name': stream['name'],
                'profile_type': 'Dahua',
                'video_encoder': {
                    'encoding': stream.get('codec', ''),
                    'name': stream['name'],
                },
                'video_source': {
                    'token': stream['profile_token'],
                    'name': 'Channel 1',
                    'source_token': stream['profile_token'],
                },
                'audio_encoder': {},
                'ptz': {},
            })
        return profiles
