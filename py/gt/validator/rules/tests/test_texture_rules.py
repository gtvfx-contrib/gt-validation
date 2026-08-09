"""Tests for texture.py validation rules.

TextureDimensionRule works on any host (STANDALONE) and uses metadata via
the injected ``ValidationContext``. TextureCompressionRule and
TextureSampleRule are Unreal-gated, so ``isEnabled()``/host-context checks
are exercised where relevant.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # goes to V:\repo\gtvfx-contrib\gt\validation
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from unittest.mock import patch

from gt.runtime import HostType

from gt.validator.config import Config  # type: ignore
from gt.validator.context.base import AssetMetadata, ValidationContext  # type: ignore
from gt.validator.rules.texture import (  # type: ignore
    TextureCompressionRule,
    TextureDimensionRule,
    TextureSampleRule,
)


class _FakeMetadataContext(ValidationContext):
    """Minimal ValidationContext stub returning one pre-built AssetMetadata."""

    def __init__(self, metadata: AssetMetadata) -> None:
        self._metadata = metadata

    def isAvailable(self) -> bool:
        """Return True; this stub is always usable in tests."""
        return True

    def collect(self, asset_path: str) -> AssetMetadata:
        """Return the pre-built metadata regardless of asset_path."""
        return self._metadata


class TestTextureDimensionRule(unittest.TestCase):
    """Test TextureDimensionRule (STANDALONE-context)."""

    def setUp(self) -> None:
        self.config = Config()

    def test_valid_power_of_two_passes(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={"width": 1024, "height": 1024})
        rule = TextureDimensionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertTrue(result.passed)

    def test_exceeds_max_dimension_fails(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={"width": 8192, "height": 8192})
        rule = TextureDimensionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertFalse(result.passed)

    def test_non_power_of_two_fails(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={"width": 1000, "height": 1000})
        rule = TextureDimensionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertFalse(result.passed)

    def test_skips_without_dimensions(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={})
        rule = TextureDimensionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertTrue(result.skipped)

    def test_skips_without_context(self) -> None:
        rule = TextureDimensionRule(self.config, validation_context=None)
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertTrue(result.skipped)


class TestTextureCompressionRule(unittest.TestCase):
    """Test TextureCompressionRule (Unreal-gated)."""

    def setUp(self) -> None:
        self.config = Config()
        self._host_patcher = patch("gt.runtime.getCurrentHost", return_value=HostType.UNREAL)
        self._host_patcher.start()

    def tearDown(self) -> None:
        self._host_patcher.stop()

    def test_normal_map_wrong_compression_fails(self) -> None:
        meta = AssetMetadata(
            path="/Game/T_Wall_N.uasset",
            properties={"compression_settings": "TC_Default"},
        )
        rule = TextureCompressionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall_N.uasset")
        self.assertFalse(result.passed)

    def test_normal_map_correct_compression_passes(self) -> None:
        meta = AssetMetadata(
            path="/Game/T_Wall_N.uasset",
            properties={"compression_settings": "TC_Normalmap"},
        )
        rule = TextureCompressionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall_N.uasset")
        self.assertTrue(result.passed)

    def test_non_normal_map_passes(self) -> None:
        meta = AssetMetadata(
            path="/Game/T_Wall_D.uasset",
            properties={"compression_settings": "TC_Default"},
        )
        rule = TextureCompressionRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall_D.uasset")
        self.assertTrue(result.passed)


class TestTextureSampleRule(unittest.TestCase):
    """Test TextureSampleRule (Unreal-gated)."""

    def setUp(self) -> None:
        self.config = Config()
        self._host_patcher = patch("gt.runtime.getCurrentHost", return_value=HostType.UNREAL)
        self._host_patcher.start()

    def tearDown(self) -> None:
        self._host_patcher.stop()

    def test_within_limit(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={"mip_count": 10})
        rule = TextureSampleRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertTrue(result.passed)

    def test_exceeds_limit(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={"mip_count": 99})
        rule = TextureSampleRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertFalse(result.passed)

    def test_skips_without_metadata(self) -> None:
        meta = AssetMetadata(path="/Game/T_Wall.uasset", properties={})
        rule = TextureSampleRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/T_Wall.uasset")
        self.assertTrue(result.skipped)


if __name__ == "__main__":
    unittest.main()
