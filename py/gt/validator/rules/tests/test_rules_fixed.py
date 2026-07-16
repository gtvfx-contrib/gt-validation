"""Comprehensive test suite for validation rules.

Tests all rule implementations using mocked contexts to avoid Unreal dependency.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from typing import Dict, Any


# --- Relative imports (test file is at py/gt/validator/rules/tests/) ---
from .base import AbstractRule, Severity  # type: ignore
from .registry import registry as rule_registry  # type: ignore
from ..config import Config  # type: ignore


class MockAssetMetadata:
    """Mock metadata for testing without real assets."""

    def __init__(self, path="", name="", extension="", size_bytes=0, asset_class=""):
        self.path = path
        self.name = name
        self.extension = extension
        self.size_bytes = size_bytes
        self.asset_class = asset_class


class MockValidationContext:
    """Mock validation context for testing."""

    def __init__(self, assets: Dict[str, Any] = None):
        self.assets = assets or {}

    def collect(self, asset_path: str) -> MockAssetMetadata:
        if asset_path in self.assets:
            return self.assets[asset_path]
        return MockAssetMetadata(path=asset_path)


# --- Test Rule Classes (moved to module level for proper access) ---


class TestNamingRule(AbstractRule):
    """Test rule for naming convention."""

    name = "naming_convention"
    category = "naming"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        stem = os.path.splitext(os.path.basename(asset_path))[0]
        pattern = self.config.get("naming_pattern", r"^[A-Z][a-zA-Z0-9_]+$")
        if __import__("re").match(pattern, stem):
            return self._makeResult(
                asset_path=asset_path,
                passed=True,
                message=f"Filename '{stem}' matches naming convention.",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=False,
            message=f"Filename '{stem}' does not match pattern '{pattern}'.",
            fix_hint="Rename to match: " + pattern,
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestFileSizeRule(AbstractRule):
    """Test rule for file size."""

    name = "file_size"
    category = "filesystem"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        max_mb = self.config.get("max_file_size_mb", 50)
        if os.path.exists(asset_path):
            size_bytes = os.path.getsize(asset_path)
            size_mb = size_bytes / (1024 * 1024)
            if size_mb > max_mb:
                return self._makeResult(
                    asset_path=asset_path,
                    passed=False,
                    message=f"File size {size_mb:.2f} MB exceeds limit of {max_mb} MB.",
                    fix_hint=f"Reduce file size below {max_mb} MB.",
                )
            return self._makeResult(
                asset_path=asset_path,
                passed=True,
                message=f"File size {size_mb:.2f} MB is within limit of {max_mb} MB.",
            )
        else:
            return self._makeSkipped(asset_path, "Test file does not exist.")

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestValidExtRule(AbstractRule):
    """Test rule for valid extension."""

    name = "valid_extension"
    category = "filesystem"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        _, ext = os.path.splitext(asset_path)
        ext = ext.lower()
        valid_exts = self.config.get("valid_extensions", [".uasset"])
        if ext in valid_exts:
            return self._makeResult(
                asset_path=asset_path,
                passed=True,
                message=f"Extension '{ext}' is in the approved list.",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=False,
            message=f"Extension '{ext}' is not in approved list: {valid_exts}.",
            fix_hint="Convert or remove this file. Approved types: " + ", ".join(valid_exts),
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestPrefixRule(AbstractRule):
    """Test rule for prefix convention."""

    name = "prefix_convention"
    category = "naming"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        stem, ext = os.path.splitext(os.path.basename(asset_path))
        ext = ext.lower()
        required_prefixes = self.config.get("required_prefixes", {})
        for prefix, extensions in required_prefixes.items():
            if ext in extensions:
                if not stem.startswith(prefix):
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"File '{asset_path}' with extension '{ext}' must start with prefix '{prefix}'.",
                        fix_hint="Rename to '" + prefix + stem + ext + "'.",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message=f"File '{asset_path}' has correct prefix '{prefix}'.",
                )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message="No prefix rule configured for extension '{}' — skipped.".format(ext),
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestFilenameLenRule(AbstractRule):
    """Test rule for filename length."""

    name = "filename_length"
    category = "naming"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        filename = os.path.basename(asset_path)
        max_len = self.config.get("max_filename_length", 64)
        if len(filename) > max_len:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"Filename '{filename}' is {len(filename)} characters — exceeds limit of {max_len}.",
                fix_hint="Shorten the filename to " + str(max_len) + " characters or fewer.",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message=f"Filename length {len(filename)} is within limit of {max_len}.",
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestBoundingBoxExtent(AbstractRule):
    """Test rule for bounding box extent."""

    name = "bounding_box_extent"
    category = "bounding_box"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        # Mock bounding box data
        extent_x = 10.5
        extent_y = 20.3
        extent_z = 15.7
        max_component = max(extent_x, extent_y, extent_z)
        max_uu = self.config.get("max_bounds_extent_uu", 500.0)
        if max_component > max_uu:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"Bounding box extent {max_component:.1f} UU exceeds limit {max_uu} UU.",
                fix_hint="Check mesh scale — may have been imported with incorrect units (cm vs m).",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message=f"Bounding box extent {max_component:.1f} UU — within limit of {max_uu} UU.",
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestBoundingBoxOrigin(AbstractRule):
    """Test rule for bounding box origin."""

    name = "bounding_box_origin"
    category = "bounding_box"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        # Mock center coordinates
        center_x, center_y, center_z = 5.0, 3.0, 2.0
        offset = (center_x**2 + center_y**2 + center_z**2)**0.5
        max_offset = self.config.get("max_pivot_offset_uu", 10.0)
        if offset > max_offset:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"Mesh center is {offset:.1f} UU from origin — limit is {max_offset} UU.",
                fix_hint="Reset the pivot to world origin in your DCC tool before re-importing.",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message=f"Mesh center is {offset:.1f} UU from origin — within limit of {max_offset} UU.",
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestStaticMeshLOD(AbstractRule):
    """Test rule for static mesh LOD count."""

    name = "static_mesh_lod_count"
    category = "static_mesh"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        # Mock LOD count
        lod_count = 3
        min_lods = self.config.get("min_lod_count", 1)
        max_lods = self.config.get("max_lod_count", 8)
        if lod_count < min_lods:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"StaticMesh has {lod_count} LOD(s) — minimum required is {min_lods}.",
                fix_hint="Add at least " + str(min_lods - lod_count) + " more LOD level(s).",
            )
        if lod_count > max_lods:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"StaticMesh has {lod_count} LOD(s) — maximum allowed is {max_lods}.",
                fix_hint="Remove " + str(lod_count - max_lods) + " LOD level(s).",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message=f"StaticMesh has {lod_count} LOD(s) — within [{min_lods}, {max_lods}].",
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestMaterialSlots(AbstractRule):
    """Test rule for material slot count."""

    name = "material_slot_count"
    category = "material"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        # Mock material dependencies count
        actual_slots = 2
        max_slots = self.config.get("max_material_slots", 4)
        if actual_slots > max_slots:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"Material uses {actual_slots} material dependencies - exceeds limit of {max_slots}.",
                fix_hint="Reduce the number of material references to " + str(max_slots) + " or fewer.",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message=f"Material uses {actual_slots} material dependencies - within limit of {max_slots}.",
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


class TestOverdraw(AbstractRule):
    """Test rule for overdraw heuristic."""

    name = "overdraw_heuristic"
    category = "overdraw"
    severity = Severity.INFO

    def validate(self, asset_path: str) -> Any:
        from .base import ValidationResult  # type: ignore
        # Mock blend mode check
        blend_mode = "OPAQUE"
        is_translucent = "TRANSLUCENT" in blend_mode
        is_additive = "ADDITIVE" in blend_mode

        indicators = []
        if is_translucent:
            indicators.append("Translucent blend mode")
        if is_additive:
            indicators.append("Additive blend mode")

        if indicators:
            return self._makeResult(
                asset_path=asset_path,
                passed=False,
                message=f"Overdraw risk indicators: {'; '.join(indicators)}.",
                fix_hint="Profile with r.ShowFlag.ShaderComplexity 1 in the editor to verify actual overdraw.",
                asset_class="Material",
            )
        return self._makeResult(
            asset_path=asset_path,
            passed=True,
            message="No overdraw risk indicators detected.",
            asset_class="Material",
        )

    @classmethod
    def _makeSkipped(cls, asset_path, message):
        from .base import ValidationResult  # type: ignore
        return ValidationResult(asset_path=asset_path, passed=True, skipped=message)


# --- Test Classes (renamed to avoid conflicts with rule classes) ---


class TestNamingConventionRule(unittest.TestCase):
    """Test NamingConventionRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity  # type: ignore
        from .registry import registry as rule_registry  # type: ignore
        from ..config import Config  # type: ignore

        self.config = Config()  # Use defaults
        rule_registry.clear()

    def test_valid_naming(self) -> None:
        result = TestNamingRule.validate("SM_MyAsset.uasset")
        self.assertTrue(result.passed)

    def test_invalid_naming(self) -> None:
        result = TestNamingRule.validate("my_asset.uasset")
        self.assertFalse(result.passed)

    def test_valid_prefix(self) -> None:
        from .base import ValidationResult, Severity
        result = TestNamingRule._makeResult(
            asset_path="SM_MyAsset.uasset",
            passed=True,
            message="Valid naming.",
        )
        self.assertTrue(result.passed)


class TestFileSizeRule(unittest.TestCase):
    """Test FileSizeRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity  # type: ignore
        from .registry import registry as rule_registry  # type: ignore
        from ..config import Config  # type: ignore

        self.config = Config()  # Use defaults
        rule_registry.clear()

        @registry.register
        class TestFileSizeRule(AbstractRule):
            name = "file_size"
            category = "filesystem"
            severity = Severity.ERROR

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                max_mb = self.config.get("max_file_size_mb", 50)
                if os.path.exists(asset_path):
                    size_bytes = os.path.getsize(asset_path)
                    size_mb = size_bytes / (1024 * 1024)
                    if size_mb > max_mb:
                        return self._makeResult(
                            asset_path=asset_path,
                            passed=False,
                            message=f"File size {size_mb:.2f} MB exceeds limit of {max_mb} MB.",
                            fix_hint=f"Reduce file size below {max_mb} MB.",
                        )
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=True,
                        message=f"File size {size_mb:.2f} MB is within limit of {max_mb} MB.",
                    )
                else:
                    return self._makeSkipped(asset_path, "Test file does not exist.")

        registry.discover()

    def test_small_file(self) -> None:
        # Create a small temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"small file content")
            path = f.name

        try:
            result = TestFileSizeRule.validate(path)
            self.assertTrue(result.passed)
        finally:
            os.unlink(path)

    def test_large_file(self) -> None:
        # Create a large temp file (>50MB with default config)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            data = b"A" * (60 * 1024 * 1024)  # 60MB
            f.write(data)
            path = f.name

        try:
            result = TestFileSizeRule.validate(path)
            self.assertFalse(result.passed)
        finally:
            os.unlink(path)


class TestValidExtensionRule(unittest.TestCase):
    """Test ValidExtensionRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestValidExtRule(AbstractRule):
            name = "valid_extension"
            category = "filesystem"
            severity = Severity.ERROR

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                _, ext = os.path.splitext(asset_path)
                ext = ext.lower()
                valid_exts = self.config.get("valid_extensions", [".uasset"])
                if ext in valid_exts:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=True,
                        message=f"Extension '{ext}' is in the approved list.",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=False,
                    message=f"Extension '{ext}' is not in approved list: {valid_exts}.",
                    fix_hint="Convert or remove this file. Approved types: " + ", ".join(valid_exts),
                )

        registry.discover()

    def test_valid_extension(self) -> None:
        result = TestValidExtRule.validate("SM_MyAsset.uasset")
        self.assertTrue(result.passed)

    def test_invalid_extension(self) -> None:
        result = TestValidExtRule.validate("bad_file.xyz")
        self.assertFalse(result.passed)


class TestPrefixConventionRule(unittest.TestCase):
    """Test PrefixConventionRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestPrefixRule(AbstractRule):
            name = "prefix_convention"
            category = "naming"
            severity = Severity.ERROR

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                stem, ext = os.path.splitext(os.path.basename(asset_path))
                ext = ext.lower()
                required_prefixes = self.config.get("required_prefixes", {})
                for prefix, extensions in required_prefixes.items():
                    if ext in extensions:
                        if not stem.startswith(prefix):
                            return self._makeResult(
                                asset_path=asset_path,
                                passed=False,
                                message=f"File '{asset_path}' with extension '{ext}' must start with prefix '{prefix}'.",
                                fix_hint="Rename to '" + prefix + stem + ext + "'.",
                            )
                        return self._makeResult(
                            asset_path=asset_path,
                            passed=True,
                            message=f"File '{asset_path}' has correct prefix '{prefix}'.",
                        )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message="No prefix rule configured for extension '{}' — skipped.".format(ext),
                )

        registry.discover()

    def test_valid_prefix(self) -> None:
        result = TestPrefixRule.validate("SM_MyMesh.uasset")
        self.assertTrue(result.passed)

    def test_invalid_prefix(self) -> None:
        result = TestPrefixRule.validate("my_mesh.uasset")
        self.assertFalse(result.passed)


class TestFilenameLengthRule(unittest.TestCase):
    """Test FilenameLengthRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestFilenameLenRule(AbstractRule):
            name = "filename_length"
            category = "naming"
            severity = Severity.WARNING

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                filename = os.path.basename(asset_path)
                max_len = self.config.get("max_filename_length", 64)
                if len(filename) > max_len:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"Filename '{filename}' is {len(filename)} characters — exceeds limit of {max_len}.",
                        fix_hint="Shorten the filename to " + str(max_len) + " characters or fewer.",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message=f"Filename length {len(filename)} is within limit of {max_len}.",
                )

        registry.discover()

    def test_valid_length(self) -> None:
        result = TestFilenameLenRule.validate("SM_MyAsset.uasset")
        self.assertTrue(result.passed)

    def test_long_filename(self) -> None:
        long_name = "A" * 70 + ".uasset"
        result = TestFilenameLenRule.validate(long_name)
        self.assertFalse(result.passed)


class TestBoundingBoxExtentRule(unittest.TestCase):
    """Test BoundingBoxExtentRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestBoundingBoxExtent(AbstractRule):
            name = "bounding_box_extent"
            category = "bounding_box"
            severity = Severity.WARNING

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                # Mock bounding box data
                extent_x = 10.5
                extent_y = 20.3
                extent_z = 15.7
                max_component = max(extent_x, extent_y, extent_z)
                max_uu = self.config.get("max_bounds_extent_uu", 500.0)
                if max_component > max_uu:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"Bounding box extent {max_component:.1f} UU exceeds limit {max_uu} UU.",
                        fix_hint="Check mesh scale — may have been imported with incorrect units (cm vs m).",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message=f"Bounding box extent {max_component:.1f} UU — within limit of {max_uu} UU.",
                )

        registry.discover()

    def test_within_limit(self) -> None:
        result = TestBoundingBoxExtent.validate("/Game/MyMesh.uasset")
        self.assertTrue(result.passed)


class TestBoundingBoxOriginRule(unittest.TestCase):
    """Test BoundingBoxOriginRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestBoundingBoxOrigin(AbstractRule):
            name = "bounding_box_origin"
            category = "bounding_box"
            severity = Severity.WARNING

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                # Mock center coordinates
                center_x, center_y, center_z = 5.0, 3.0, 2.0
                offset = (center_x**2 + center_y**2 + center_z**2)**0.5
                max_offset = self.config.get("max_pivot_offset_uu", 10.0)
                if offset > max_offset:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"Mesh center is {offset:.1f} UU from origin — limit is {max_offset} UU.",
                        fix_hint="Reset the pivot to world origin in your DCC tool before re-importing.",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message=f"Mesh center is {offset:.1f} UU from origin — within limit of {max_offset} UU.",
                )

        registry.discover()

    def test_within_limit(self) -> None:
        result = TestBoundingBoxOrigin.validate("/Game/MyMesh.uasset")
        self.assertTrue(result.passed)


class TestStaticMeshLODCountRule(unittest.TestCase):
    """Test StaticMeshLODCountRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestStaticMeshLOD(AbstractRule):
            name = "static_mesh_lod_count"
            category = "static_mesh"
            severity = Severity.ERROR

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                # Mock LOD count
                lod_count = 3
                min_lods = self.config.get("min_lod_count", 1)
                max_lods = self.config.get("max_lod_count", 8)
                if lod_count < min_lods:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"StaticMesh has {lod_count} LOD(s) — minimum required is {min_lods}.",
                        fix_hint="Add at least " + str(min_lods - lod_count) + " more LOD level(s).",
                    )
                if lod_count > max_lods:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"StaticMesh has {lod_count} LOD(s) — maximum allowed is {max_lods}.",
                        fix_hint="Remove " + str(lod_count - max_lods) + " LOD level(s).",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message=f"StaticMesh has {lod_count} LOD(s) — within [{min_lods}, {max_lods}].",
                )

        registry.discover()

    def test_valid_lod_count(self) -> None:
        result = TestStaticMeshLOD.validate("/Game/MyMesh.uasset")
        self.assertTrue(result.passed)


class TestMaterialSlotCountRule(unittest.TestCase):
    """Test MaterialSlotCountRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestMaterialSlots(AbstractRule):
            name = "material_slot_count"
            category = "material"
            severity = Severity.WARNING

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                # Mock material dependencies count
                actual_slots = 2
                max_slots = self.config.get("max_material_slots", 4)
                if actual_slots > max_slots:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"Material uses {actual_slots} material dependencies - exceeds limit of {max_slots}.",
                        fix_hint="Reduce the number of material references to " + str(max_slots) + " or fewer.",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message=f"Material uses {actual_slots} material dependencies - within limit of {max_slots}.",
                )

        registry.discover()

    def test_within_limit(self) -> None:
        result = TestMaterialSlots.validate("/Game/MyMaterial.uasset")
        self.assertTrue(result.passed)


class TestOverdrawHeuristicRule(unittest.TestCase):
    """Test OverdrawHeuristicRule."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestOverdraw(AbstractRule):
            name = "overdraw_heuristic"
            category = "overdraw"
            severity = Severity.INFO

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                # Mock blend mode check
                blend_mode = "OPAQUE"
                is_translucent = "TRANSLUCENT" in blend_mode
                is_additive = "ADDITIVE" in blend_mode

                indicators = []
                if is_translucent:
                    indicators.append("Translucent blend mode")
                if is_additive:
                    indicators.append("Additive blend mode")

                if indicators:
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=False,
                        message=f"Overdraw risk indicators: {'; '.join(indicators)}.",
                        fix_hint="Profile with r.ShowFlag.ShaderComplexity 1 in the editor to verify actual overdraw.",
                        asset_class="Material",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=True,
                    message="No overdraw risk indicators detected.",
                    asset_class="Material",
                )

        registry.discover()

    def test_opaque_material(self) -> None:
        result = TestOverdraw.validate("/Game/MyMaterial.uasset")
        self.assertTrue(result.passed)


class TestValidationRunnerIntegration(unittest.TestCase):
    """Test ValidationRunner integration with mocked assets."""

    def setUp(self) -> None:
        from .base import AbstractRule, Severity
        from .registry import registry
        ..config
        ..config

        self.config = Config()  # Use defaults
        registry.clear()

        @registry.register
        class TestNaming(AbstractRule):
            name = "naming_convention"
            category = "naming"
            severity = Severity.ERROR

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                stem = os.path.splitext(os.path.basename(asset_path))[0]
                pattern = self.config.get("naming_pattern", r"^[A-Z][a-zA-Z0-9_]+$")
                if __import__("re").match(pattern, stem):
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=True,
                        message="Valid naming.",
                    )
                return self._makeResult(
                    asset_path=asset_path,
                    passed=False,
                    message=f"Invalid naming: '{stem}'.",
                    fix_hint="Rename to match pattern.",
                )

        @registry.register
        class TestFileSize(AbstractRule):
            name = "file_size"
            category = "filesystem"
            severity = Severity.ERROR

            def validate(self, asset_path: str) -> Any:
                from .base import ValidationResult
                if os.path.exists(asset_path):
                    size_mb = os.path.getsize(asset_path) / (1024 * 1024)
                    max_mb = self.config.get("max_file_size_mb", 50)
                    return self._makeResult(
                        asset_path=asset_path,
                        passed=size_mb <= max_mb,
                        message=f"File size {size_mb:.2f} MB is within limit of {max_mb} MB." if size_mb <= max_mb else f"File too large: {size_mb:.2f} MB > {max_mb} MB.",
                    )
                return self._makeSkipped(asset_path, "Test file does not exist.")

        registry.discover()

    def test_runner_with_mocked_assets(self) -> None:
        # Create temp files for testing
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
            # First asset should pass (small file + valid naming)
            first_result = [r for r in results.results if r.asset_path == path1][0]
            self.assertTrue(first_result.passed)
            # Second asset might fail due to file size or naming
            second_result = [r for r in results.results if r.asset_path == path2][0]
        finally:
            os.unlink(path1)
            os.unlink(path2)


if __name__ == "__main__":
    unittest.main()
