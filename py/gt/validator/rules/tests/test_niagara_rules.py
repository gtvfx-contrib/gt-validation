"""Tests for niagara.py validation rules.

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
from unittest.mock import patch

from gt.runtime import HostType

from gt.validator.config import Config  # type: ignore
from gt.validator.context.base import AssetMetadata, ValidationContext  # type: ignore
from gt.validator.rules.niagara import (  # type: ignore
    NiagaraEmitterCountRule,
    NiagaraFixedBoundsRule,
    NiagaraGPUSimulationRule,
    NiagaraSpawnRateLimitRule,
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


class TestNiagaraFixedBoundsRule(unittest.TestCase):
    """Test NiagaraFixedBoundsRule."""

    def setUp(self) -> None:
        self.config = Config()
        self._host_patcher = patch("gt.runtime.getCurrentHost", return_value=HostType.UNREAL)
        self._host_patcher.start()

    def tearDown(self) -> None:
        self._host_patcher.stop()

    def test_fixed_bounds_passes(self) -> None:
        meta = AssetMetadata(path="/Game/FX/NS_Explosion.uasset", properties={"fixed_bounds": True})
        rule = NiagaraFixedBoundsRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.passed)

    def test_dynamic_bounds_fails(self) -> None:
        meta = AssetMetadata(
            path="/Game/FX/NS_Explosion.uasset", properties={"fixed_bounds": False}
        )
        rule = NiagaraFixedBoundsRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertFalse(result.passed)

    def test_skips_without_context(self) -> None:
        rule = NiagaraFixedBoundsRule(self.config, validation_context=None)
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.passed)
        self.assertTrue(result.skipped)


class TestNiagaraEmitterCountRule(unittest.TestCase):
    """Test NiagaraEmitterCountRule."""

    def setUp(self) -> None:
        self.config = Config()
        self._host_patcher = patch("gt.runtime.getCurrentHost", return_value=HostType.UNREAL)
        self._host_patcher.start()

    def tearDown(self) -> None:
        self._host_patcher.stop()

    def test_within_limit(self) -> None:
        meta = AssetMetadata(path="/Game/FX/NS_Explosion.uasset", properties={"emitter_count": 3})
        rule = NiagaraEmitterCountRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.passed)

    def test_exceeds_limit(self) -> None:
        meta = AssetMetadata(path="/Game/FX/NS_Explosion.uasset", properties={"emitter_count": 99})
        rule = NiagaraEmitterCountRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertFalse(result.passed)

    def test_skips_without_context(self) -> None:
        rule = NiagaraEmitterCountRule(self.config, validation_context=None)
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.skipped)


class TestNiagaraSpawnRateLimitRule(unittest.TestCase):
    """Test NiagaraSpawnRateLimitRule."""

    def setUp(self) -> None:
        self.config = Config()
        self._host_patcher = patch("gt.runtime.getCurrentHost", return_value=HostType.UNREAL)
        self._host_patcher.start()

    def tearDown(self) -> None:
        self._host_patcher.stop()

    def test_within_limit(self) -> None:
        meta = AssetMetadata(path="/Game/FX/NS_Explosion.uasset", properties={"spawn_rate": 500})
        rule = NiagaraSpawnRateLimitRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.passed)

    def test_exceeds_limit(self) -> None:
        meta = AssetMetadata(path="/Game/FX/NS_Explosion.uasset", properties={"spawn_rate": 999999})
        rule = NiagaraSpawnRateLimitRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertFalse(result.passed)


class TestNiagaraGPUSimulationRule(unittest.TestCase):
    """Test NiagaraGPUSimulationRule."""

    def setUp(self) -> None:
        self.config = Config()
        self._host_patcher = patch("gt.runtime.getCurrentHost", return_value=HostType.UNREAL)
        self._host_patcher.start()

    def tearDown(self) -> None:
        self._host_patcher.stop()

    def test_gpu_allowed_passes(self) -> None:
        meta = AssetMetadata(
            path="/Game/FX/NS_Explosion.uasset", properties={"uses_gpu_simulation": True}
        )
        rule = NiagaraGPUSimulationRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.passed)

    def test_cpu_simulation_passes(self) -> None:
        meta = AssetMetadata(
            path="/Game/FX/NS_Explosion.uasset", properties={"uses_gpu_simulation": False}
        )
        rule = NiagaraGPUSimulationRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertTrue(result.passed)

    def test_gpu_disallowed_fails(self) -> None:
        self.config._data["allow_gpu_simulation"] = False
        meta = AssetMetadata(
            path="/Game/FX/NS_Explosion.uasset", properties={"uses_gpu_simulation": True}
        )
        rule = NiagaraGPUSimulationRule(self.config, validation_context=_FakeMetadataContext(meta))
        result = rule.validate("/Game/FX/NS_Explosion.uasset")
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
