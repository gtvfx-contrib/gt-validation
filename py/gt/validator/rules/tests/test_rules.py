"""Comprehensive test suite for validation rules.

Tests all rule implementations using mocked contexts to avoid Unreal dependency.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from typing import Dict, Any


# --- Absolute imports (test file is at py/gt/validator/rules/tests/) ---
# tests -> rules -> validation -> gt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from gt.validator.config import Config  # type: ignore
from gt.validator.rules.base import AbstractRule, Severity, ValidationResult  # type: ignore
from gt.validator.rules.registry import registry as rule_registry  # type: ignore


class TestNamingConventionRule(unittest.TestCase):
    """Test NamingConventionRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_naming(self) -> None:
        result = NamingConventionRule.validate("SM_MyAsset.uasset")
        self.assertTrue(result.passed)

    def test_invalid_naming(self) -> None:
        result = NamingConventionRule.validate("my_asset.uasset")
        self.assertFalse(result.passed)


class TestFileSizeRule(unittest.TestCase):
    """Test FileSizeRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_small_file(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"small file content")
            path = f.name

        try:
            result = FileSizeRule.validate(path)
            self.assertTrue(result.passed)
        finally:
            os.unlink(path)

    def test_large_file(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            data = b"A" * (60 * 1024 * 1024)  # 60MB
            f.write(data)
            path = f.name

        try:
            result = FileSizeRule.validate(path)
            self.assertFalse(result.passed)
        finally:
            os.unlink(path)


class TestValidExtensionRule(unittest.TestCase):
    """Test ValidExtensionRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_extension(self) -> None:
        result = ValidExtensionRule.validate("SM_MyAsset.uasset")
        self.assertTrue(result.passed)

    def test_invalid_extension(self) -> None:
        result = ValidExtensionRule.validate("bad_file.xyz")
        self.assertFalse(result.passed)


class TestPrefixConventionRule(unittest.TestCase):
    """Test PrefixConventionRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_prefix(self) -> None:
        result = PrefixConventionRule.validate("SM_MyMesh.uasset")
        self.assertTrue(result.passed)

    def test_invalid_prefix(self) -> None:
        result = PrefixConventionRule.validate("my_mesh.uasset")
        self.assertFalse(result.passed)


class TestFilenameLengthRule(unittest.TestCase):
    """Test FilenameLengthRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_length(self) -> None:
        result = FilenameLengthRule.validate("SM_MyAsset.uasset")
        self.assertTrue(result.passed)

    def test_long_filename(self) -> None:
        long_name = "A" * 70 + ".uasset"
        result = FilenameLengthRule.validate(long_name)
        self.assertFalse(result.passed)


class TestBoundingBoxExtentRule(unittest.TestCase):
    """Test BoundingBoxExtentRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_within_limit(self) -> None:
        result = BoundingBoxExtentRule.validate("/Game/MyMesh.uasset")
        self.assertTrue(result.passed)


class TestBoundingBoxOriginRule(unittest.TestCase):
    """Test BoundingBoxOriginRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_within_limit(self) -> None:
        result = BoundingBoxOriginRule.validate("/Game/MyMesh.uasset")
        self.assertTrue(result.passed)


class TestStaticMeshLODCountRule(unittest.TestCase):
    """Test StaticMeshLODCountRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_lod_count(self) -> None:
        result = StaticMeshLODCountRule.validate("/Game/MyMesh.uasset")
        self.assertTrue(result.passed)


class TestMaterialSlotCountRule(unittest.TestCase):
    """Test MaterialSlotCountRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_within_limit(self) -> None:
        result = StaticMeshMaterialSlotRule.validate("/Game/MyMaterial.uasset")
        self.assertTrue(result.passed)


class TestOverdrawHeuristicRule(unittest.TestCase):
    """Test OverdrawHeuristicRule."""

    def setUp(self) -> None:
        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_opaque_material(self) -> None:
        result = OverdrawHeuristicRule.validate("/Game/MyMaterial.uasset")
        self.assertTrue(result.passed)


class TestValidationRunnerIntegration(unittest.TestCase):
    """Test ValidationRunner integration with mocked assets."""

    def setUp(self) -> None:
        from gt.validator.runner import ValidationRunner  # type: ignore

        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_runner_with_mocked_assets(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".uasset") as f1:
            f1.write(b"small asset 1")
            path1 = f1.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".uasset") as f2:
            data = b"A" * (60 * 1024 * 1024)  # 60MB file
            f2.write(data)
            path2 = f2.name

        try:
            runner = ValidationRunner(self.config, max_workers=1)
            results = runner.validateAssets([path1, path2])

            self.assertEqual(len(results.results), 2)
            first_result = [r for r in results.results if r.asset_path == path1][0]
            self.assertTrue(first_result.passed)
            second_result = [r for r in results.results if r.asset_path == path2][0]
        finally:
            os.unlink(path1)
            os.unlink(path2)


# Production rule classes — import here to avoid circular imports during collection.
from gt.validator.rules.naming import (  # noqa: E402,F401  # type: ignore
    NamingConventionRule,
    PrefixConventionRule,
    FilenameLengthRule,
)
from gt.validator.rules.filesystem import FileSizeRule, ValidExtensionRule  # noqa: F401  # type: ignore
from gt.validator.rules.bounding_box import (  # noqa: F401  # type: ignore
    BoundingBoxExtentRule,
    BoundingBoxOriginRule,
)
from gt.validator.rules.static_mesh import (  # noqa: F401  # type: ignore
    StaticMeshLODCountRule,
    StaticMeshMaterialSlotRule,
)
from gt.validator.rules.overdraw import OverdrawHeuristicRule  # noqa: F401  # type: ignore


if __name__ == "__main__":
    unittest.main()
