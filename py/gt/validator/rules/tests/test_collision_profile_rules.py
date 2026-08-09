"""Tests for collision_profile.py validation rules.

Uses a minimal ``_FakeMetadataContext`` (returning a pre-built
``AssetMetadata``) so these tests can exercise property-driven rule logic
without requiring a real Unreal Engine session, matching the pattern used
in ``test_rules.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # goes to V:\repo\gtvfx-contrib\gt\validation
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest

from gt.validator.config import Config  # type: ignore
from gt.validator.context.base import AssetMetadata, ValidationContext  # type: ignore
from gt.validator.rules.collision_profile import (  # type: ignore
    CollisionLODTransitionSmoothnessRule,
    CollisionProfileValidatorRule,
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


class TestCollisionProfileValidatorRule(unittest.TestCase):
    """Test CollisionProfileValidatorRule."""

    def setUp(self) -> None:
        self.config = Config()

    def test_within_limit(self) -> None:
        meta = AssetMetadata(
            path="/Game/SM_Rock.uasset",
            properties={"collision_profile_complexity": 8},
        )
        rule = CollisionProfileValidatorRule(
            self.config, validation_context=_FakeMetadataContext(meta)
        )
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertTrue(result.passed)

    def test_exceeds_limit(self) -> None:
        meta = AssetMetadata(
            path="/Game/SM_Rock.uasset",
            properties={"collision_profile_complexity": 999},
        )
        rule = CollisionProfileValidatorRule(
            self.config, validation_context=_FakeMetadataContext(meta)
        )
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertFalse(result.passed)

    def test_skips_without_context(self) -> None:
        rule = CollisionProfileValidatorRule(self.config, validation_context=None)
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)


class TestCollisionLODTransitionSmoothnessRule(unittest.TestCase):
    """Test CollisionLODTransitionSmoothnessRule."""

    def setUp(self) -> None:
        self.config = Config()

    def test_smooth_transitions_pass(self) -> None:
        meta = AssetMetadata(
            path="/Game/SM_Rock.uasset",
            properties={"lod_scales": [1.0, 0.9, 0.8]},
        )
        rule = CollisionLODTransitionSmoothnessRule(
            self.config, validation_context=_FakeMetadataContext(meta)
        )
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertTrue(result.passed)

    def test_sudden_jump_fails(self) -> None:
        meta = AssetMetadata(
            path="/Game/SM_Rock.uasset",
            properties={"lod_scales": [1.0, 0.05]},
        )
        rule = CollisionLODTransitionSmoothnessRule(
            self.config, validation_context=_FakeMetadataContext(meta)
        )
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertFalse(result.passed)

    def test_single_lod_level_passes(self) -> None:
        meta = AssetMetadata(
            path="/Game/SM_Rock.uasset",
            properties={"lod_scales": [1.0]},
        )
        rule = CollisionLODTransitionSmoothnessRule(
            self.config, validation_context=_FakeMetadataContext(meta)
        )
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertTrue(result.passed)

    def test_skips_without_context(self) -> None:
        rule = CollisionLODTransitionSmoothnessRule(self.config, validation_context=None)
        result = rule.validate("/Game/SM_Rock.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)


if __name__ == "__main__":
    unittest.main()
