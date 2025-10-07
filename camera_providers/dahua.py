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

        streams = self._build_default_streams(host)
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

    def _build_default_streams(self, host: str):
        """
        Dahua RTSP syntax:
        rtsp://<host>:554/cam/realmonitor?channel=<id>&subtype=<stream>
            subtype 0 = main, 1 = sub
        """
        stream_map = [
            ('dahua-channel1-main', f"rtsp://{host}:554/cam/realmonitor?channel=1&subtype=0", 'Main Stream'),
            ('dahua-channel1-sub', f"rtsp://{host}:554/cam/realmonitor?channel=1&subtype=1", 'Sub Stream'),
        ]

        return [
            {
                'profile_token': token,
                'name': name,
                'stream_uri': uri,
                'stream_type': 'RTP-Unicast',
                'protocol': 'RTSP',
                'codec': 'H.264',
                'resolution': {},
                'profile_type': 'Dahua',
                'vendor': 'dahua',
                'channel': '1'
            }
            for token, uri, name in stream_map
        ]

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
