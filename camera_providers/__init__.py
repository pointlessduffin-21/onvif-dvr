"""
Vendor-specific camera provider registry
"""
from typing import Dict, List, Optional

from .base import BaseCameraProvider
from .axis import AxisProvider
from .dahua import DahuaProvider
from .hikvision import HikvisionProvider

_PROVIDER_REGISTRY: Dict[str, BaseCameraProvider] = {
    provider.key: provider
    for provider in (
        HikvisionProvider(),
        DahuaProvider(),
        AxisProvider(),
    )
}


def get_camera_provider(key: str) -> Optional[BaseCameraProvider]:
    """Return a provider instance for the given key"""
    if not key:
        return None
    return _PROVIDER_REGISTRY.get(key.lower())


def list_registered_providers() -> List[Dict[str, str]]:
    """List non-ONVIF providers for UI consumption"""
    providers = []
    for provider in _PROVIDER_REGISTRY.values():
        providers.append({
            'key': provider.key,
            'name': provider.display_name,
            'connection_type': provider.connection_type,
            'default_port': provider.default_port,
            'features': provider.supported_features,
        })
    return providers


__all__ = [
    "get_camera_provider",
    "list_registered_providers",
]
