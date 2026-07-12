"""Bounding box validation rules.

Rules:
    BoundingBoxExtentRule: Validates the world bounding box extent is within the limit.
    BoundingBoxOriginRule: Validates the pivot offset from the world origin is within the limit.

"""

from __future__ import annotations

from ..env import loadUnrealAsset
from ..errors import UnrealAPIError
from ..registry import registry
from .base import AbstractRule, Severity, ValidationResult


def _readMeshBoundsMetrics(asset, unreal_module) -> tuple[float, float, float, float, float, float]:
    """Return mesh extents and center components from supported Unreal APIs.

    Args:
        asset: Loaded ``unreal.StaticMesh`` or ``unreal.SkeletalMesh`` asset.
        unreal_module: Imported ``unreal`` module.

    Returns:
        Tuple in the form ``(extent_x, extent_y, extent_z, center_x, center_y, center_z)``.

    """
    if isinstance(asset, unreal_module.StaticMesh):
        bounds = asset.get_bounding_box()
        min_corner = bounds.min
        max_corner = bounds.max
        extent_x = abs(max_corner.x - min_corner.x) * 0.5
        extent_y = abs(max_corner.y - min_corner.y) * 0.5
        extent_z = abs(max_corner.z - min_corner.z) * 0.5
        center_x = (min_corner.x + max_corner.x) * 0.5
        center_y = (min_corner.y + max_corner.y) * 0.5
        center_z = (min_corner.z + max_corner.z) * 0.5
        return extent_x, extent_y, extent_z, center_x, center_y, center_z

    # SkeletalMesh exposes get_bounds() (BoxSphereBounds) in the stub API.
    bounds = asset.get_bounds()
    box_extent = bounds.box_extent
    origin = bounds.origin
    extent_x = abs(box_extent.x)
    extent_y = abs(box_extent.y)
    extent_z = abs(box_extent.z)
    center_x = origin.x
    center_y = origin.y
    center_z = origin.z
    return extent_x, extent_y, extent_z, center_x, center_y, center_z


@registry.register
class BoundingBoxExtentRule(AbstractRule):
    """Validates that a mesh's bounding box extent does not exceed the limit.

    Attributes:
        name: Rule identifier ``"bounding_box_extent"``.
        category: Rule category ``"bounding_box"``.
        severity: :attr:`Severity.WARNING`.

    """

    name = "bounding_box_extent"
    category = "bounding_box"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the bounding box extent of the given mesh asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the bounding box extent
            is within the configured limit.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError as exc:
            return self._makeSkipped(asset_path, str(exc))
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, (unreal.StaticMesh, unreal.SkeletalMesh)):
            return self._makeSkipped(
                asset_path,
                f"Bounding box check only applies to mesh assets (got {type(asset).__name__}).",
            )

        try:
            extent_x, extent_y, extent_z, _, _, _ = _readMeshBoundsMetrics(asset, unreal)
            max_component = max(extent_x, extent_y, extent_z)
            max_uu: float = self.config.get("max_bounds_extent_uu", 500.0)
            asset_class = type(asset).__name__

            if max_component > max_uu:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"Bounding box extent {max_component:.1f} UU exceeds limit {max_uu} UU "
                        f"(X={extent_x:.1f}, Y={extent_y:.1f}, Z={extent_z:.1f})."
                    ),
                    asset_class=asset_class,
                    fix_hint=(
                        "Check mesh scale — may have been imported with incorrect units (cm vs m)."
                    ),
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=(
                    f"Bounding box extent {max_component:.1f} UU — within limit of {max_uu} UU."
                ),
                asset_class=asset_class,
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")


@registry.register
class BoundingBoxOriginRule(AbstractRule):
    """Validates that the mesh pivot is close to the world origin.

    A pivot far from the origin causes floating-point precision issues in large worlds.

    Attributes:
        name: Rule identifier ``"bounding_box_origin"``.
        category: Rule category ``"bounding_box"``.
        severity: :attr:`Severity.WARNING`.

    """

    name = "bounding_box_origin"
    category = "bounding_box"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate that the mesh pivot is close to the world origin.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the mesh center
            is within the configured offset limit from the world origin.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError as exc:
            return self._makeSkipped(asset_path, str(exc))
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, (unreal.StaticMesh, unreal.SkeletalMesh)):
            return self._makeSkipped(
                asset_path,
                f"Origin check only applies to mesh assets (got {type(asset).__name__}).",
            )

        try:
            _, _, _, center_x, center_y, center_z = _readMeshBoundsMetrics(asset, unreal)
            offset = (center_x**2 + center_y**2 + center_z**2) ** 0.5
            max_offset: float = self.config.get("max_pivot_offset_uu", 10.0)
            asset_class = type(asset).__name__

            if offset > max_offset:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"Mesh center is {offset:.1f} UU from origin "
                        f"(X={center_x:.1f}, Y={center_y:.1f}, Z={center_z:.1f}) — "
                        f"limit is {max_offset} UU."
                    ),
                    asset_class=asset_class,
                    fix_hint=(
                        "Reset the pivot to world origin in your DCC tool before re-importing."
                    ),
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=(
                    f"Mesh center is {offset:.1f} UU from origin — within limit of {max_offset} UU."
                ),
                asset_class=asset_class,
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")
