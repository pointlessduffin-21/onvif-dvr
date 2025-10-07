"""
Hikvision ISAPI integration
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPDigestAuth

from .base import BaseCameraProvider


class HikvisionProvider(BaseCameraProvider):
    key = "hikvision"
    display_name = "Hikvision ISAPI"
    connection_type = "hikvision-isapi"
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
        info_url = f"{base_url}/ISAPI/System/deviceInfo"

        auth = HTTPDigestAuth(username, password)

        try:
            response = requests.get(info_url, auth=auth, timeout=timeout, verify=False if use_https else True)
            response.raise_for_status()
        except Exception as exc:
            return {
                'success': False,
                'error': f'Hikvision connection failed: {exc}'
            }

        device_info = self._parse_device_info(response.text)

        streams = self._build_default_streams(host, port)
        profiles = self._build_profiles(streams)

        return {
            'success': True,
            'device_info': device_info,
            'profiles': profiles,
            'streams': streams,
            'vendor': 'hikvision',
            'connection_type': self.connection_type,
            'extra_config': {
                'base_url': base_url,
                'supports_https': use_https,
                'channels': options.get('channels', [1]),
            }
        }

    def _parse_device_info(self, payload: str) -> Dict[str, Any]:
        """Parse XML payload returned by Hikvision ISAPI"""
        info = {
            'manufacturer': 'Hikvision',
            'model': '',
            'serial_number': '',
            'firmware_version': ''
        }

        try:
            root = ET.fromstring(payload)
            info['model'] = root.findtext('model', default='')
            info['serial_number'] = root.findtext('serialNumber', default='')
            info['firmware_version'] = root.findtext('firmwareVersion', default='')
        except ET.ParseError:
            # Keep defaults if parsing fails
            pass

        return info

    def _build_default_streams(self, host: str, port: int):
        """Construct common Hikvision RTSP endpoints"""
        # Hikvision channel naming: 101 main stream, 102 sub stream
        stream_map = [
            ('hikvision-channel1-main', f"rtsp://{host}:554/Streaming/Channels/101"),
            ('hikvision-channel1-sub', f"rtsp://{host}:554/Streaming/Channels/102"),
        ]

        return [
            {
                'profile_token': token,
                'name': 'Main Stream' if 'main' in token else 'Sub Stream',
                'stream_uri': uri,
                'stream_type': 'RTP-Unicast',
                'protocol': 'RTSP',
                'codec': 'H.264',
                'resolution': {},
                'profile_type': 'Hikvision',
                'vendor': 'hikvision',
                'channel': '1'
            }
            for token, uri in stream_map
        ]

    def _build_profiles(self, streams):
        """Convert stream entries to profile metadata"""
        profiles = []
        for stream in streams:
            profiles.append({
                'token': stream['profile_token'],
                'name': stream['name'],
                'profile_type': 'Hikvision',
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
