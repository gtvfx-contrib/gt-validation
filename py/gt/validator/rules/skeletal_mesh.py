"""SkeletalMesh validation rules.

Rules:
    SkeletalMeshLODCountRule: Validates minimum/maximum LOD levels for skeletal meshes.
    SkeletalMeshAnimationLengthRule: Checks animation sequences don't exceed maximum duration.
    SkeletalMeshBoneCountRule: Flags meshes with excessive bone counts (>256 bones).

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..context.base import AssetMetadata, ValidationContext
from ..config import Config
from ..registry import registry
from .base import AbstractRule, Severity, ValidationResult

logger = logging.getLogger(__name__)


@registry.register
class SkeletalMeshLODCountRule(AbstractRule):
    """Validates that a SkeletalMesh has the required number of LOD levels.

    StaticMesh LOD requirements apply to skeletal meshes too — validate
    minimum/maximum LOD levels for consistent asset quality across mesh types.

    Attributes:
        name: Rule identifier ``"skeletal_mesh_lod_count"``.
        category: Rule category ``"skeletal_mesh"``.
        severity: :attr:`Severity.ERROR`.

    """

    name = "skeletal_mesh_lod_count"
    category = "skeletal_mesh"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the LOD count of the given SkeletalMesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the LOD count is within
            the configured minimum and maximum bounds.

        """
        # Use context abstraction to collect metadata instead of direct Unreal API calls.
        try:
            meta = self.context.collect(asset_path) if callable(getattr(self, 'context', None)) else None
        except (AttributeError, TypeError):
            meta = None

        if meta is not None:
            lod_count = meta.properties.get("lod_count", 0)
            min_lods: int = self.config.get("min_lod_count", 1)
            max_lods: int = self.config.get("max_lod_count", 8)

            if lod_count < min_lods:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=f"SkeletalMesh has {lod_count} LOD(s) — minimum required is {min_lods}.",
                    asset_class="SkeletalMesh",
                    fix_hint=(
                        f"Add at least {min_lods - lod_count} more LOD "
                        "level(s) in the Skeletal Mesh Editor."
                    ),
                )
            if lod_count > max_lods:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=f"SkeletalMesh has {lod_count} LOD(s) — maximum allowed is {max_lods}.",
                    asset_class="SkeletalMesh",
                    fix_hint=f"Remove {lod_count - max_lods} LOD level(s) to reduce to {max_lods}.",
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=f"SkeletalMesh has {lod_count} LOD(s) — within [{min_lods}, {max_lods}].",
                asset_class="SkeletalMesh",
            )

        # Fallback: if context cannot provide metadata, skip validation.
        return self._makeSkipped(
            asset_path,
            "LOD count validation requires Unreal Engine host or filesystem access."
        )


@registry.register
class SkeletalMeshAnimationLengthRule(AbstractRule):
    """Validates that animation sequences don't exceed a maximum duration.

    Animations longer than 60 seconds may cause pipeline issues in-game — this rule
    flags them for review to ensure they meet production requirements.

    Attributes:
        name: Rule identifier ``"skeletal_mesh_animation_length"``.
        category: Rule category ``"skeletal_mesh"``.
        severity: :attr:`Severity.WARNING`.

    """

    name = "skeletal_mesh_animation_length"
    category = "skeletal_mesh"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the animation duration of the given SkeletalMesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the animation duration
            is within the configured limit.

        """
        # Use context abstraction to collect metadata instead of direct Unreal API calls.
        try:
            meta = self.context.collect(asset_path) if callable(getattr(self, 'context', None)) else None
        except (AttributeError, TypeError):
            meta = None

        if meta is not None:
            max_duration = self.config.get("max_animation_duration_seconds", 60.0)

            anim_length = meta.properties.get("anim_length", 0)

            if anim_length > max_duration:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"Animation duration {anim_length:.1f}s exceeds maximum "
                        f"{max_duration}s for in-game animations."
                    ),
                    asset_class="SkeletalMesh",
                    fix_hint=f"Trim or loop the animation to fit within {max_duration} seconds.",
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=(
                    f"Animation duration {anim_length:.1f}s — within limit of {max_duration}s."
                ),
                asset_class="SkeletalMesh",
            )

        # Fallback: if context cannot provide metadata, skip validation.
        return self._makeSkipped(
            asset_path,
            "Animation length validation requires Unreal Engine host or filesystem access."
        )


@registry.register
class SkeletalMeshBoneCountRule(AbstractRule):
    """Flags skeletal meshes with excessive bone counts.

    More than 256 bones can cause performance issues and exceed UE limits — this rule
    flags them for review to ensure they meet production requirements.

    Attributes:
        name: Rule identifier ``"skeletal_mesh_bone_count"``.
        category: Rule category ``"skeletal_mesh"``.
        severity: :attr:`Severity.WARNING`.

    """

    name = "skeletal_mesh_bone_count"
    category = "skeletal_mesh"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the bone count of the given SkeletalMesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the bone count is within
            the configured limit.

        """
        # Use context abstraction to collect metadata instead of direct Unreal API calls.
        try:
            meta = self.context.collect(asset_path) if callable(getattr(self, 'context', None)) else None
        except (AttributeError, TypeError):
            meta = None

        if meta is not None:
            max_bones = self.config.get("max_skeletal_mesh_bone_count", 256)

            bone_count = meta.properties.get("bone_count", 0)

            if bone_count > max_bones:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"SkeletalMesh has {bone_count} bones — exceeds maximum of {max_bones}. "
                        f"This may cause performance issues."
                    ),
                    asset_class="SkeletalMesh",
                    fix_hint=f"Reduce bone count to {max_bones} or fewer by simplifying the rig.",
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=(
                    f"SkeletalMesh has {bone_count} bones — within limit of {max_bones}."
                ),
                asset_class="SkeletalMesh",
            )

        # Fallback: if context cannot provide metadata, skip validation.
        return self._makeSkipped(
            asset_path,
            "Bone count validation requires Unreal Engine host or filesystem access."
        )
