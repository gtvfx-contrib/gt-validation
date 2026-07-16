"""Tests for SkeletalMesh validation rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # goes to V:\repo\gtvfx-contrib\gt\validation
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest


# Absolute imports — this file is at py/gt/validator/rules/, so:
#   gt.validator.rules.skeletal_mesh_test -> gt.validator.rules.*
from gt.validator.config import Config  # type: ignore
from gt.validator.rules.base import AbstractRule, Severity  # type: ignore
from gt.validator.rules.registry import registry as rule_registry  # type: ignore


class TestSkeletalMeshLODCountRule(unittest.TestCase):
    """Test SkeletalMeshLODCountRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_lod_count_within_range(self) -> None:
        result = SkeletalMeshLODCountRule.validate("/Game/ValidSkeletalMesh.uasset")
        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
