"""Tests for context-aware validation rules.

This module contains tests for the context-aware rule system, including:
- HostType detection
- Registry context filtering
- Rule instantiation with context
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # goes to V:\repo\gtvfx-contrib\gt\validation
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from unittest.mock import Mock

from gt.runtime import HostType

from gt.validator.config import Config  # type: ignore
from gt.validator.registry import registry
from gt.validator.rules.base import AbstractRule, Severity


class TestContextAwareRules(unittest.TestCase):
    """Test context-aware rule behavior."""

    def setUp(self) -> None:
        """Clear the registry before each test."""
        registry.clear()
        self.config = Mock()
        self.config.get = Mock(return_value=True)

    def test_rule_with_context_attribute(self) -> None:
        """Test that a rule can have a context attribute."""

        @registry.register
        class TestRule(AbstractRule):
            name = "test_rule"
            category = "test"
            severity = Severity.ERROR
            context = HostType.UNREAL

            def __init__(self, config: Config, context: HostType) -> None:
                super().__init__(config)
                self.context = context

            def validate(self, asset_path: str) -> AbstractRule: ...

        self.assertEqual(TestRule.context, HostType.UNREAL)

    def test_registry_filters_by_context(self) -> None:
        """Test that registry filters rules by context."""

        @registry.register
        class UnrealRule(AbstractRule):
            name = "unreal_rule"
            category = "unreal"
            severity = Severity.ERROR
            context = HostType.UNREAL

            def __init__(self, config: Config, context: HostType) -> None:
                super().__init__(config)
                self.context = context

            def validate(self, asset_path: str) -> AbstractRule: ...

        @registry.register
        class StandaloneRule(AbstractRule):
            name = "standalone_rule"
            category = "standalone"
            severity = Severity.ERROR
            context = HostType.STANDALONE

            def __init__(self, config: Config, context: HostType) -> None:
                super().__init__(config)
                self.context = context

            def validate(self, asset_path: str) -> AbstractRule: ...

        registry.discover()

        # Test UNREAL context
        unreal_rules = registry.getRules(context=HostType.UNREAL)
        self.assertEqual(len(unreal_rules), 1)
        self.assertEqual(unreal_rules[0].name, "unreal_rule")

        # Test STANDALONE context
        standalone_rules = registry.getRules(context=HostType.STANDALONE)
        self.assertEqual(len(standalone_rules), 1)
        self.assertEqual(standalone_rules[0].name, "standalone_rule")

        # Test NONE context (no filter)
        all_rules = registry.getRules()
        self.assertEqual(len(all_rules), 2)

    def test_registry_getRules_accepts_context_parameter(self) -> None:
        """Test that getRules accepts context parameter."""

        @registry.register
        class TestRule(AbstractRule):
            name = "test_rule"
            category = "test"
            severity = Severity.ERROR
            context = HostType.UNREAL

            def __init__(self, config: Config, context: HostType) -> None:
                super().__init__(config)
                self.context = context

            def validate(self, asset_path: str) -> AbstractRule: ...

        registry.discover()

        # Should not raise an error
        rules = registry.getRules(context=HostType.UNREAL)
        self.assertEqual(len(rules), 1)

    def test_rule_instantiation_with_context(self) -> None:
        """Test that rules can be instantiated with context parameter."""

        @registry.register
        class TestRule(AbstractRule):
            name = "test_rule"
            category = "test"
            severity = Severity.ERROR
            context = HostType.UNREAL

            def __init__(self, config: Config, context: HostType) -> None:
                super().__init__(config)
                self.context = context

            def validate(self, asset_path: str) -> AbstractRule: ...

        registry.discover()
        rule = TestRule(self.config, HostType.UNREAL)
        self.assertEqual(rule.context, HostType.UNREAL)


if __name__ == "__main__":
    unittest.main()
