"""Tests for material.py validation rules.

These rules load assets via the Unreal API (``loadUnrealAsset`` / direct
``unreal`` import) so they must degrade gracefully to a skipped result
outside Unreal — mirroring the pattern used for StaticMesh rules in
``test_rules.py``.

Also regression-proofs the ``__init__`` signature fix: these rule classes
previously overrode ``__init__`` with an incompatible ``context: HostType``
parameter that did not accept the ``validation_context=`` keyword
``ValidationRunner`` always passes, causing a ``TypeError`` that crashed
the entire runner under ``HostType.UNREAL``. Constructing each rule here
via ``validation_context=`` (as the runner does) guards against that
regression recurring.
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
from gt.validator.rules.material import (  # type: ignore
    MaterialComplexityRule,
    MaterialSlotCountRule,
    MaxTranslucentMaterialsRule,
)


class TestMaterialSlotCountRule(unittest.TestCase):
    """Test MaterialSlotCountRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_constructs_with_validation_context_keyword(self) -> None:
        """Regression: must accept validation_context= as ValidationRunner passes it."""
        rule = MaterialSlotCountRule(self.config, validation_context=self.context)
        self.assertIsInstance(rule, MaterialSlotCountRule)

    def test_class_level_context_not_shadowed(self) -> None:
        """Regression: __init__ must not shadow the class-level context attribute."""
        rule = MaterialSlotCountRule(self.config, validation_context=self.context)
        self.assertEqual(type(rule).context, rule.context)

    def test_skips_outside_unreal(self) -> None:
        rule = MaterialSlotCountRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Materials/M_Hero.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)


class TestMaterialComplexityRule(unittest.TestCase):
    """Test MaterialComplexityRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_constructs_with_validation_context_keyword(self) -> None:
        """Regression: must accept validation_context= as ValidationRunner passes it."""
        rule = MaterialComplexityRule(self.config, validation_context=self.context)
        self.assertIsInstance(rule, MaterialComplexityRule)

    def test_class_level_context_not_shadowed(self) -> None:
        """Regression: __init__ must not shadow the class-level context attribute."""
        rule = MaterialComplexityRule(self.config, validation_context=self.context)
        self.assertEqual(type(rule).context, rule.context)

    def test_skips_outside_unreal(self) -> None:
        rule = MaterialComplexityRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Materials/M_Hero.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)


class TestMaxTranslucentMaterialsRule(unittest.TestCase):
    """Test MaxTranslucentMaterialsRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_constructs_with_validation_context_keyword(self) -> None:
        """Regression: must accept validation_context= as ValidationRunner passes it."""
        rule = MaxTranslucentMaterialsRule(self.config, validation_context=self.context)
        self.assertIsInstance(rule, MaxTranslucentMaterialsRule)

    def test_class_level_context_not_shadowed(self) -> None:
        """Regression: __init__ must not shadow the class-level context attribute."""
        rule = MaxTranslucentMaterialsRule(self.config, validation_context=self.context)
        self.assertEqual(type(rule).context, rule.context)

    def test_skips_outside_unreal(self) -> None:
        rule = MaxTranslucentMaterialsRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Levels/L_Hangar")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)


if __name__ == "__main__":
    unittest.main()
