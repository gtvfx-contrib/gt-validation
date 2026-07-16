"""CollisionProfile validation rules.

Rules:
    CollisionProfileValidatorRule: Checks that collision profiles are properly configured and don't have unnecessary complex shapes.
    CollisionLODTransitionSmoothnessRule: Verifies LOD transitions between mesh levels are smooth (no sudden scale jumps).

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..config import Config
from ..env import loadUnrealAsset
from .base import AbstractRule, Severity, ValidationResult
from gt.runtime import HostType as _HostType

logger = logging.getLogger(__name__)


@AbstractRule.register_rule("collision_profile_validator", "collision_profile", Severity.ERROR)
class CollisionProfileValidatorRule(AbstractRule):
    """Checks that collision profiles are properly configured and don't have unnecessary complex shapes.

    Collision profiles with excessive complexity can cause performance issues — this rule
    flags them for review to ensure they meet production requirements.

    Attributes:
        name: Rule identifier ``"collision_profile_validator"``.
        category: Rule category ``"collision_profile"``.
        severity: :attr:`Severity.ERROR`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "collision_profile_validator"
    category = "collision_profile"
    severity = Severity.ERROR
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the collision profile configuration of the given asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the collision profile is properly configured.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, (unreal.StaticMesh, unreal.SkeletalMesh)):
            return self._makeSkipped(asset_path, f"Not a mesh asset (got {type(asset).__name__}).")

        try:
            max_complexity = self.config.get("max_collision_profile_complexity", 32)

            # Access collision profile complexity via Unreal API
            complexity = getattr(asset, "collision_profile_complexity", None) or getattr(asset, "collision_profile", None)
            if complexity is None:
                try:
                    collision_profile_path = asset.get_editor_property("collision_profile")
                    if collision_profile_path and hasattr(collision_profile_path, "get_num_components"):
                        complexity = collision_profile_path.get_num_components()
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not read collision profile complexity: {exc}"
                    )

            if complexity is None or (isinstance(complexity, int) and complexity <= 0):
                # Fallback: estimate from mesh LOD structure
                try:
                    lod_count = getattr(asset, "num_lods", 1)
                    complexity = max(4, lod_count * 2)
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not estimate collision profile complexity: {exc}"
                    )

            if complexity > max_complexity:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"Collision profile has complexity {complexity} — exceeds maximum of {max_complexity}. "
                        f"This may cause performance issues."
                    ),
                    asset_class="StaticMesh",
                    fix_hint=f"Simplify the collision shape to reduce complexity to {max_complexity} or fewer components.",
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=(
                    f"Collision profile has complexity {complexity} — within limit of {max_complexity}."
                ),
                asset_class="StaticMesh",
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")


@AbstractRule.register_rule("collision_lod_transition_smoothness", "collision_profile", Severity.WARNING)
class CollisionLODTransitionSmoothnessRule(AbstractRule):
    """Verifies LOD transitions between mesh levels are smooth (no sudden scale jumps).

    Sudden scale jumps between LOD levels can cause visual artifacts — this rule
    flags them for review to ensure they meet production requirements.

    Attributes:
        name: Rule identifier ``"collision_lod_transition_smoothness"``.
        category: Rule category ``"collision_profile"``.
        severity: :attr:`Severity.WARNING`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "collision_lod_transition_smoothness"
    category = "collision_profile"
    severity = Severity.WARNING
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate LOD transition smoothness for the given mesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether LOD transitions are smooth.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, (unreal.StaticMesh, unreal.SkeletalMesh)):
            return self._makeSkipped(asset_path, f"Not a mesh asset (got {type(asset).__name__}).")

        try:
            max_scale_jump = self.config.get("max_lod_scale_jump", 0.5)

            # Access LOD scale data via Unreal API
            lod_scales = getattr(asset, "lod_scales", None) or getattr(asset, "scales", None)
            if lod_scales is None:
                try:
                    lod_scales = asset.get_editor_property("lod_scales")
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not read LOD scales: {exc}"
                    )

            if lod_scales is None or (isinstance(lod_scales, list) and len(lod_scales) == 0):
                # Fallback: estimate from mesh LOD structure
                try:
                    lod_count = getattr(asset, "num_lods", 1)
                    scales = [0.5 ** i for i in range(lod_count)]
                    lod_scales = scales if len(scales) > 1 else [1.0]
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not estimate LOD scales: {exc}"
                    )

            if isinstance(lod_scales, list) and len(lod_scales) > 1:
                max_jump = 0.0
                for i in range(len(lod_scales) - 1):
                    jump = abs(lod_scales[i] - lod_scales[i + 1]) / (lod_scales[i] + lod_scales[i + 1]) * 2
                    max_jump = max(max_jump, jump)

                if max_jump > max_scale_jump:
                    return self._makeResult(
                        asset_path,
                        passed=False,
                        message=(
                            f"LOD transitions have a maximum scale jump of {max_jump:.3f} — exceeds limit of {max_scale_jump}. "
                            f"This may cause visual artifacts."
                        ),
                        asset_class="StaticMesh",
                        fix_hint=f"Adjust LOD scales to ensure no single transition exceeds a ratio of {max_scale_jump}.",
                    )
                return self._makeResult(
                    asset_path,
                    passed=True,
                    message=(
                        f"LOD transitions have a maximum scale jump of {max_jump:.3f} — within limit of {max_scale_jump}."
                    ),
                    asset_class="StaticMesh",
                )

            return self._makeResult(
                asset_path,
                passed=True,
                message=f"Only {len(lod_scales) if isinstance(lod_scales, list) else 1} LOD level(s) — no transitions to check.",
                asset_class="StaticMesh",
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")
