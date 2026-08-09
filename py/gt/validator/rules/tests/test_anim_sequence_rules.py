"""Tests for anim_sequence.py validation rules.

AnimSequence rules load assets via the Unreal API (``loadUnrealAsset``);
outside Unreal they must degrade gracefully to a skipped (not crashed, not
failed) result — mirroring the pattern used for StaticMesh rules in
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
from gt.validator.rules.anim_sequence import (  # type: ignore
    AnimSequenceDurationLimitRule,
    AnimSequenceFrameCountRule,
)


class TestAnimSequenceFrameCountRule(unittest.TestCase):
    """Test AnimSequenceFrameCountRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_skips_outside_unreal(self) -> None:
        rule = AnimSequenceFrameCountRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Anims/AS_Run.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)

    def test_rule_metadata(self) -> None:
        self.assertEqual(AnimSequenceFrameCountRule.name, "anim_sequence_frame_count")
        self.assertEqual(AnimSequenceFrameCountRule.category, "anim_sequence")


class TestAnimSequenceDurationLimitRule(unittest.TestCase):
    """Test AnimSequenceDurationLimitRule (Unreal-only; skips outside Unreal)."""

    def setUp(self) -> None:
        self.config = Config()
        self.context = FilesystemContext()

    def test_skips_outside_unreal(self) -> None:
        rule = AnimSequenceDurationLimitRule(self.config, validation_context=self.context)
        result = rule.validate("/Game/Anims/AS_Run.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)

    def test_rule_metadata(self) -> None:
        self.assertEqual(AnimSequenceDurationLimitRule.name, "anim_sequence_duration_limit")
        self.assertEqual(AnimSequenceDurationLimitRule.category, "anim_sequence")


if __name__ == "__main__":
    unittest.main()
