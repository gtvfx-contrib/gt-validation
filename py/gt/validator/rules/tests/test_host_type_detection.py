"""Tests for HostType detection.

This module contains tests for the HostType enum and RuntimeDetector.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from gt.runtime import HostType, RuntimeDetector


class TestHostTypeDetection(unittest.TestCase):
    """Test HostType detection and RuntimeDetector."""

    def test_runtime_detector_detect_standalone(self) -> None:
        """Test that RuntimeDetector detects standalone when appropriate."""
        with patch.object(RuntimeDetector, 'detect', return_value=HostType.STANDALONE):
            result = RuntimeDetector.detect()
            self.assertEqual(result, HostType.STANDALONE)

    def test_runtime_detector_detect_unreal(self) -> None:
        """Test that RuntimeDetector detects Unreal when appropriate."""
        with patch.object(RuntimeDetector, 'detect', return_value=HostType.UNREAL):
            result = RuntimeDetector.detect()
            self.assertEqual(result, HostType.UNREAL)

    def test_runtime_detector_get_current_host(self) -> None:
        """Test that getCurrentHost() returns the detected host."""
        with patch.object(RuntimeDetector, 'detect', return_value=HostType.UNREAL):
            result = RuntimeDetector.getCurrentHost()
            self.assertEqual(result, HostType.UNREAL)

    def test_runtime_detector_is_host(self) -> None:
        """Test that isHost() checks if current host matches."""
        with patch.object(RuntimeDetector, 'detect', return_value=HostType.UNREAL):
            self.assertTrue(RuntimeDetector.isHost(HostType.UNREAL))
            self.assertFalse(RuntimeDetector.isHost(HostType.STANDALONE))

    def test_host_type_comparison(self) -> None:
        """Test HostType comparison with string and HostType."""
        # Test comparison with string
        self.assertEqual(HostType.UNREAL, "unreal")
        self.assertEqual(HostType.UNREAL, HostType.UNREAL)

        # Test hash
        self.assertEqual(hash(HostType.UNREAL), hash("unreal"))

    def test_host_type_str(self) -> None:
        """Test that HostType can be converted to string."""
        self.assertEqual(str(HostType.UNREAL), "unreal")
        self.assertEqual(str(HostType.STANDALONE), "standalone")


if __name__ == "__main__":
    unittest.main()
