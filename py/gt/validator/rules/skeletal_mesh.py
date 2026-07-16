"""SkeletalMesh validation rules.

Rules:
    SkeletalMeshLODCountRule: Validates minimum/maximum LOD levels for skeletal meshes.
    SkeletalMeshAnimationLengthRule: Checks animation sequences don't exceed maximum duration.
    SkeletalMeshBoneCountRule: Flags meshes with excessive bone counts (>256 bones).

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..config import Config
from ..env import loadUnrealAsset
from ..errors import UnrealAPIError
from .base import AbstractRule, Severity, ValidationResult
from gt.runtime import HostType as _HostType

logger = logging.getLogger(__name__)


@AbstractRule.register_rule("skeletal_mesh_lod_count", "skeletal_mesh", Severity.ERROR)
class SkeletalMeshLODCountRule(AbstractRule):
    """Validates that a SkeletalMesh has the required number of LOD levels.

    StaticMesh LOD requirements apply to skeletal meshes too — validate
    minimum/maximum LOD levels for consistent asset quality across mesh types.

    Attributes:
        name: Rule identifier ``"skeletal_mesh_lod_count"``.
        category: Rule category ``"skeletal_mesh"``.
        severity: :attr:`Severity.ERROR`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "skeletal_mesh_lod_count"
    category = "skeletal_mesh"
    severity = Severity.ERROR
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the LOD count of the given SkeletalMesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the LOD count is within
            the configured minimum and maximum bounds.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError as exc:
            return self._makeSkipped(asset_path, str(exc))
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, unreal.SkeletalMesh):
            return self._makeSkipped(asset_path, f"Not a SkeletalMesh (got {type(asset).__name__}).")

        try:
            lod_count = asset.get_num_lods()
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
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")


@AbstractRule.register_rule("skeletal_mesh_animation_length", "skeletal_mesh", Severity.WARNING)
class SkeletalMeshAnimationLengthRule(AbstractRule):
    """Validates that animation sequences don't exceed a maximum duration.

    Animations longer than 60 seconds may cause pipeline issues in-game — this rule
    flags them for review to ensure they meet production requirements.

    Attributes:
        name: Rule identifier ``"skeletal_mesh_animation_length"``.
        category: Rule category ``"skeletal_mesh"``.
        severity: :attr:`Severity.WARNING`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "skeletal_mesh_animation_length"
    category = "skeletal_mesh"
    severity = Severity.WARNING
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the animation duration of the given SkeletalMesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the animation duration
            is within the configured limit.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError as exc:
            return self._makeSkipped(asset_path, str(exc))
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, unreal.SkeletalMesh):
            return self._makeSkipped(asset_path, f"Not a SkeletalMesh (got {type(asset).__name__}).")

        try:
            max_duration = self.config.get("max_animation_duration_seconds", 60.0)

            # Access animation length via Unreal API — check for multiple animations
            anim_length = getattr(asset, "anim_length", None)
            if anim_length is None:
                try:
                    anim_length = asset.get_editor_property("animation_sequence") or asset.get_editor_property("anim_length")
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not read animation length: {exc}"
                    )

            if anim_length is None or (isinstance(anim_length, float) and anim_length <= 0):
                # Fallback: estimate from longest animation in the mesh
                try:
                    animations = getattr(asset, "animations", [])
                    if animations:
                        max_anim_len = max(len(a) for a in animations)
                        anim_length = max_anim_len / 30.0  # Convert frames to seconds (24fps default)
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not estimate animation length: {exc}"
                    )

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
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")


@AbstractRule.register_rule("skeletal_mesh_bone_count", "skeletal_mesh", Severity.WARNING)
class SkeletalMeshBoneCountRule(AbstractRule):
    """Flags skeletal meshes with excessive bone counts.

    More than 256 bones can cause performance issues and exceed UE limits — this rule
    flags them for review to ensure they meet production requirements.

    Attributes:
        name: Rule identifier ``"skeletal_mesh_bone_count"``.
        category: Rule category ``"skeletal_mesh"``.
        severity: :attr:`Severity.WARNING`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "skeletal_mesh_bone_count"
    category = "skeletal_mesh"
    severity = Severity.WARNING
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the bone count of the given SkeletalMesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the bone count is within
            the configured limit.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError as exc:
            return self._makeSkipped(asset_path, str(exc))
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, unreal.SkeletalMesh):
            return self._makeSkipped(asset_path, f"Not a SkeletalMesh (got {type(asset).__name__}).")

        try:
            max_bones = self.config.get("max_skeletal_mesh_bone_count", 256)

            # Access bone count via Unreal API
            bone_count = getattr(asset, "num_skeletons", None) or getattr(asset, "bones", None)
            if bone_count is None:
                try:
                    skeleton = asset.get_editor_property("skeleton")
                    if skeleton and hasattr(skeleton, "get_num_bones"):
                        bone_count = skeleton.get_num_bones()
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not read bone count: {exc}"
                    )

            if bone_count is None or (isinstance(bone_count, int) and bone_count <= 0):
                # Fallback: estimate from mesh skeleton structure
                try:
                    skeletons = getattr(asset, "skeletons", [])
                    if skeletons:
                        bone_count = max(len(s) for s in skeletons)
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not estimate bone count: {exc}"
                    )

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
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")
