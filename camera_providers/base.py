"""
Base class for vendor-specific CCTV integrations
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ProviderResult(Dict[str, Any]):
    """Typed alias for provider results"""


class BaseCameraProvider(ABC):
    """Abstract base provider"""

    key: str = "base"
    display_name: str = "Base Provider"
    connection_type: str = "vendor"
    default_port: int = 80
    supported_features: List[str] = []

    @abstractmethod
    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ProviderResult:
        """
        Probe the vendor API and return device metadata, profiles, and streams.
        The returned dictionary should contain:
            success (bool)
            device_info (dict)
            profiles (list)
            streams (list)
            vendor (str)
            connection_type (str)
            extra_config (dict, optional)
            error (str, optional)
        """

    @staticmethod
    def build_stream_entry(
        camera_id: Optional[int],
        profile_token: str,
        stream_uri: str,
        stream_type: str = "RTP-Unicast",
        protocol: str = "RTSP",
        resolution: Optional[Dict[str, Any]] = None,
        codec: Optional[str] = None,
        vendor: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Utility to normalise video stream payloads before DB insertion"""
        return {
            'camera_id': camera_id,
            'profile_token': profile_token,
            'stream_uri': stream_uri,
            'stream_type': stream_type,
            'protocol': protocol,
            'resolution': resolution or {},
            'codec': codec or '',
            'vendor': vendor,
            'channel': channel,
        }
