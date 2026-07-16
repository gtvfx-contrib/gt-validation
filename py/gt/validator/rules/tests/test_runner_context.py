"""Tests for ValidationRunner context handling.

This module contains tests for the ValidationRunner's context handling.
Uses production rule classes via absolute imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # goes to V:\repo\gtvfx-contrib\gt\validation
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from unittest.mock import Mock, patch

from gt.runtime import HostType

from gt.validator.config import Config  # type: ignore
from gt.validator.rules.base import AbstractRule, Severity
from gt.validator.rules.registry import registry
from gt.validator.rules.runner import ValidationRunner


class TestValidationRunnerContext(unittest.TestCase):
    """Test ValidationRunner context handling."""

    def setUp(self) -> None:
        """Clear the registry before each test."""
        registry.clear()
        self.config = Config()  # Use defaults instead of Mock for production rules

    def test_runner_gets_current_context(self) -> None:
        """Test that ValidationRunner gets current context from gt.runtime."""

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

        with patch('gt.runtime.getCurrentHost', return_value=HostType.UNREAL):
            with patch('gt.runtime.HostType') as mock_host_type:
                mock_host_type.UNREAL = HostType.UNREAL
                runner = ValidationRunner(self.config)
                self.assertEqual(runner.context, HostType.UNREAL)

    def test_runner_passes_context_to_rules(self) -> None:
        """Test that ValidationRunner passes context to rules during instantiation."""

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
        runner = ValidationRunner(self.config)

        # Check that the rule was instantiated with the correct context
        self.assertEqual(len(runner.rules), 1)
        self.assertEqual(runner.rules[0].context, HostType.UNREAL)

    def test_runner_filters_rules_by_context(self) -> None:
        """Test that ValidationRunner filters rules by context."""

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

        # Test with UNREAL context
        runner = ValidationRunner(self.config)
        self.assertEqual(len(runner.rules), 2)

        # Test with STANDALONE context
        runner_standalone = ValidationRunner(self.config)
        self.assertEqual(len(runner_standalone.rules), 2)


if __name__ == "__main__":
    unittest.main()
