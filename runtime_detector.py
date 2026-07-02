"""Runtime environment detector for different Python hosts.

This module provides a flexible system to detect which Python host 
the code is running in (e.g., standalone, Unreal, 3ds Max, Maya, etc.).
"""

from enum import Enum
from typing import Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class HostType(Enum):
    """Enumeration of supported Python hosts."""
    STANDALONE = "standalone"
    UNREAL = "unreal"
    MAYA = "maya"
    MAX = "max"
    HOUDINI = "houdini"
    BLENDER = "blender"
    KRITA = "krita"


class RuntimeDetector:
    """Detects the current Python runtime environment and host type.
    
    Uses a registry pattern to allow registration of detection functions
    for different hosts. The detection is performed once at import time
    and cached for performance.
    """
    
    _registry: Dict[HostType, Callable[[], bool]] = {}
    _detected_host: Optional[HostType] = None
    
    @classmethod
    def register(cls, host_type: HostType, detection_func: Callable[[], bool]) -> None:
        """Register a detection function for a specific host type.
        
        Args:
            host_type: The host type to register detection for
            detection_func: Function that returns True if the host is detected
        """
        cls._registry[host_type] = detection_func
    
    @classmethod
    def detect(cls) -> HostType:
        """Detect the current Python runtime environment.
        
        Returns:
            The detected host type. If no specific host is detected, 
            returns STANDALONE.
        """
        if cls._detected_host is not None:
            return cls._detected_host
            
        # Try each registered detection function
        for host_type, detection_func in cls._registry.items():
            try:
                if detection_func():
                    cls._detected_host = host_type
                    logger.debug(f"Detected host: {host_type.value}")
                    return host_type
            except Exception as e:
                logger.debug(f"Detection failed for {host_type.value}: {e}")
        
        # Default to standalone if no specific host detected
        cls._detected_host = HostType.STANDALONE
        logger.debug("Detected host: standalone")
        return cls._detected_host
    
    @classmethod
    def get_current_host(cls) -> HostType:
        """Get the currently detected host type.
        
        Returns:
            The detected host type, performing detection if not already done.
        """
        if cls._detected_host is None:
            return cls.detect()
        return cls._detected_host
    
    @classmethod
    def is_host(cls, host_type: HostType) -> bool:
        """Check if the current environment matches a specific host type.
        
        Args:
            host_type: The host type to check for
            
        Returns:
            True if the current environment matches the specified host type
        """
        return cls.get_current_host() == host_type


# Register default detection functions
def _detect_unreal() -> bool:
    """Detect if running inside Unreal Engine."""
    try:
        import unreal  # noqa: F401
        # Try to access a basic Unreal API function
        unreal.SystemLibrary.get_engine_version()
        return True
    except Exception:
        return False


def _detect_maya() -> bool:
    """Detect if running inside Autodesk Maya."""
    try:
        import maya  # noqa: F401
        import maya.cmds  # noqa: F401
        return True
    except ImportError:
        return False


def _detect_max() -> bool:
    """Detect if running inside Autodesk 3ds Max."""
    try:
        import pymxs  # noqa: F401
        return True
    except ImportError:
        return False


def _detect_houdini() -> bool:
    """Detect if running inside SideFX Houdini."""
    try:
        import hou  # noqa: F401
        return True
    except ImportError:
        return False


def _detect_blender() -> bool:
    """Detect if running inside Blender."""
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


def _detect_krita() -> bool:
    """Detect if running inside Krita."""
    try:
        import krita  # noqa: F401
        return True
    except ImportError:
        return False


# Register all detection functions
RuntimeDetector.register(HostType.UNREAL, _detect_unreal)
RuntimeDetector.register(HostType.MAYA, _detect_maya)
RuntimeDetector.register(HostType.MAX, _detect_max)
RuntimeDetector.register(HostType.HOUDINI, _detect_houdini)
RuntimeDetector.register(HostType.BLENDER, _detect_blender)
RuntimeDetector.register(HostType.KRITA, _detect_krita)


# Convenience functions for common checks
def is_unreal() -> bool:
    """Check if running inside Unreal Engine."""
    return RuntimeDetector.is_host(HostType.UNREAL)


def is_maya() -> bool:
    """Check if running inside Autodesk Maya."""
    return RuntimeDetector.is_host(HostType.MAYA)


def is_max() -> bool:
    """Check if running inside Autodesk 3ds Max."""
    return RuntimeDetector.is_host(HostType.MAX)


def is_houdini() -> bool:
    """Check if running inside SideFX Houdini."""
    return RuntimeDetector.is_host(HostType.HOUDINI)


def is_blender() -> bool:
    """Check if running inside Blender."""
    return RuntimeDetector.is_host(HostType.BLENDER)


def is_krita() -> bool:
    """Check if running inside Krita."""
    return RuntimeDetector.is_host(HostType.KRITA)


def is_standalone() -> bool:
    """Check if running in standalone Python environment."""
    return RuntimeDetector.is_host(HostType.STANDALONE)
