"""Tests for lod.py validation rules.

LOD rules load assets via the Unreal API (``loadUnrealAsset``); outside
Unreal they must degrade gracefully to a skipped (not crashed, not failed)
result — mirroring the pattern used for StaticMesh rules in
``test_rules.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # goes to V:\repo\gtvfx-contrib\gt\validation
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest

from gt.validator.config import Config  # type: ignore
from gt.validator.context.filesystem import FilesystemContext  # type: ignore
from gt.validator.rules.lod import LODCountRule, LODScreenSizeRatioRule  # type: ignore


class TestLODCountRule(unittest.TestCase):
    """Test LODCountRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_skips_outside_unreal(self) -> None:
        rule = LODCountRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Meshes/SM_Rock.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)

    def test_rule_metadata(self) -> None:
        self.assertEqual(LODCountRule.name, "lod_count")
        self.assertEqual(LODCountRule.category, "lod")


class TestLODScreenSizeRatioRule(unittest.TestCase):
    """Test LODScreenSizeRatioRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_skips_outside_unreal(self) -> None:
        rule = LODScreenSizeRatioRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Meshes/SM_Rock.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)

    def test_rule_metadata(self) -> None:
        self.assertEqual(LODScreenSizeRatioRule.name, "lod_screen_size_ratio")
        self.assertEqual(LODScreenSizeRatioRule.category, "lod")


if __name__ == "__main__":
    unittest.main()
