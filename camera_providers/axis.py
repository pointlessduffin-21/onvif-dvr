"""
Axis VAPIX integration
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

from .base import BaseCameraProvider


class AxisProvider(BaseCameraProvider):
    key = "axis"
    display_name = "Axis VAPIX"
    connection_type = "axis-vapix"
    default_port = 80
    supported_features = ["device-info", "rtsp", "snapshot", "ptz"]

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
        info_url = f"{base_url}/axis-cgi/param.cgi?action=list&group=Properties.System"

        auth = HTTPBasicAuth(username, password)

        try:
            response = requests.get(info_url, auth=auth, timeout=timeout, verify=False if use_https else True)
            response.raise_for_status()
        except Exception as exc:
            return {
                'success': False,
                'error': f'Axis connection failed: {exc}'
            }

        device_info = self._parse_device_info(response.text)

        streams = self._build_default_streams(host)
        profiles = self._build_profiles(streams)

        return {
            'success': True,
            'device_info': device_info,
            'profiles': profiles,
            'streams': streams,
            'vendor': 'axis',
            'connection_type': self.connection_type,
            'extra_config': {
                'base_url': base_url,
                'supports_https': use_https,
                'channels': options.get('channels', [1]),
            }
        }

    def _parse_device_info(self, payload: str) -> Dict[str, Any]:
        info = {
            'manufacturer': 'Axis',
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

            if key.endswith('Model'):
                info['model'] = value
            elif key.endswith('SerialNumber'):
                info['serial_number'] = value
            elif key.endswith('Firmware.Version'):
                info['firmware_version'] = value

        return info

    def _build_default_streams(self, host: str):
        """
        Axis RTSP layout follows:
            rtsp://<host>/axis-media/media.amp?camera=<id>
        """
        stream_map = [
            ('axis-camera1-hd', f"rtsp://{host}/axis-media/media.amp?camera=1&videocodec=h264", 'Main Stream'),
            ('axis-camera1-sd', f"rtsp://{host}/axis-media/media.amp?camera=1&resolution=640x360&videocodec=h264", 'Sub Stream'),
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
                'profile_type': 'Axis',
                'vendor': 'axis',
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
                'profile_type': 'Axis',
                'video_encoder': {
                    'encoding': stream.get('codec', ''),
                    'name': stream['name'],
                },
                'video_source': {
                    'token': stream['profile_token'],
                    'name': 'Camera 1',
                    'source_token': stream['profile_token'],
                },
                'audio_encoder': {},
                'ptz': {},
            })
        return profiles
