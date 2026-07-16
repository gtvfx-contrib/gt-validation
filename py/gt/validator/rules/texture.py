"""Texture validation rules.

Rules:
    TextureDimensionRule: Validates texture dimensions are power-of-two and within the limit.
    TextureCompressionRule: Validates that textures use appropriate compression settings.
    TextureSampleRule: Validates MIP counts against configured sample limits.

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..config import Config
from ..env import loadUnrealAsset
from .base import AbstractRule, Severity, ValidationResult
from gt.runtime import HostType as _HostType

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from __future__ import annotations


@AbstractRule.register_rule("texture_dimension", "texture", Severity.ERROR)
class TextureDimensionRule(AbstractRule):
    """Validates texture dimensions are power-of-two and within the limit.

    Attributes:
        name: Rule identifier ``"texture_dimension"``.
        category: Rule category ``"texture"``.
        severity: :attr:`Severity.ERROR`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "texture_dimension"
    category = "texture"
    severity = Severity.ERROR
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the dimensions of the given texture asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the texture dimensions
            are power-of-two and within the configured maximum.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")

        if not isinstance(asset, type(self._get_texture_class())):
            return self._makeSkipped(
                asset_path, f"Not a Texture2D (got {type(asset).__name__})."
            )

        try:
            # Use size_x/size_y from the Unreal stub API.
            width = getattr(asset, "size_x", None) or getattr(asset, 'blueprint_get_size_x', lambda: 0)()
            height = getattr(asset, "size_y", None) or getattr(asset, 'blueprint_get_size_y', lambda: 0)()

            if width is None or height is None:
                return self._makeSkipped(
                    asset_path, "Could not read texture dimensions from Unreal API."
                )

            max_dim: int = self.config.get("max_texture_dimension", 4096)

            def isPowerOfTwo(n: int) -> bool:
                return n > 0 and (n & (n - 1)) == 0

            issues = []
            if width > max_dim or height > max_dim:
                issues.append(f"Dimensions {width}x{height} exceed max {max_dim}x{max_dim}.")
            if not isPowerOfTwo(width) or not isPowerOfTwo(height):
                issues.append(f"Dimensions {width}x{height} are not powers of two.")

            if issues:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=" ".join(issues),
                    asset_class="Texture2D",
                    fix_hint=f"Resize texture to a power-of-two dimension <= {max_dim}px.",
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=f"Texture dimensions {width}x{height} are valid.",
                asset_class="Texture2D",
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")

    @staticmethod
    def _get_texture_class():
        """Return the Texture2D class from unreal module."""
        import unreal
        return unreal.Texture2D


@AbstractRule.register_rule("texture_compression", "texture", Severity.WARNING)
class TextureCompressionRule(AbstractRule):
    """Validates that textures use an appropriate compression setting.

    Normal maps must use ``TC_Normalmap`` compression.

    Attributes:
        name: Rule identifier ``"texture_compression"``.
        category: Rule category ``"texture"``.
        severity: :attr:`Severity.WARNING`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "texture_compression"
    category = "texture"
    severity = Severity.WARNING
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the compression settings of the given texture asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the compression setting
            is appropriate for the detected texture type.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")

        if not isinstance(asset, type(self._get_texture_class())):
            return self._makeSkipped(
                asset_path, f"Not a Texture2D (got {type(asset).__name__})."
            )

        try:
            compression = getattr(asset, "compression_settings", None)
            if compression is None:
                try:
                    compression = asset.get_editor_property("compression_settings")
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not read compression settings: {exc}"
                    )

            path_str = str(asset_path)
            is_normal_map = (
                "_N." in path_str
                or "_Normal." in path_str
                or "_NRM." in path_str
                or "Normal" in path_str
            )

            import unreal as _ue  # noqa: PLC0415 - deferred Unreal import

            if is_normal_map and compression != _ue.TextureCompressionSettings.TC_NORMALMAP:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"Normal map texture uses compression '{compression}' — "
                        f"should use TC_Normalmap."
                    ),
                    asset_class="Texture2D",
                    fix_hint=(
                        "Set Compression Settings to 'Normalmap (DXT5, BC5 "
                        "on DX11)' in the Texture Editor."
                    ),
                )

            return self._makeResult(
                asset_path,
                passed=True,
                message=f"Texture compression '{compression}' is acceptable.",
                asset_class="Texture2D",
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")

    @staticmethod
    def _get_texture_class():
        """Return the Texture2D class from unreal module."""
        import unreal
        return unreal.Texture2D


@AbstractRule.register_rule("texture_samples", "texture", Severity.WARNING)
class TextureSampleRule(AbstractRule):
    """Validates MIP counts against configured sample limits.

    Attributes:
        name: Rule identifier ``"texture_samples"``.
        category: Rule category ``"texture"``.
        severity: :attr:`Severity.WARNING`.
        context: Requires Unreal Engine host (HostType.UNREAL).

    """

    name = "texture_samples"
    category = "texture"
    severity = Severity.WARNING
    context = _HostType.UNREAL  # Type hint handled by base.py

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the MIP/sample count of the given texture.

        Args:
            asset_path: Content-browser path of the Texture2D to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the sample/MIP
            count is within the configured limit.

        """
        try:
            asset = loadUnrealAsset(asset_path)
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")

        if not isinstance(asset, type(self._get_texture_class())):
            return self._makeSkipped(
                asset_path, f"Not a Texture2D (got {type(asset).__name__})."
            )

        try:
            max_samples = self.config.get("max_texture_samples", 16)
            # Access MIP count via Unreal API.
            num_mips = getattr(asset, "num_mip_levels", None)
            if num_mips is None:
                try:
                    num_mips = asset.get_editor_property("mip_count") or asset.get_editor_property("num_mip_maps")
                except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
                    return self._makeSkipped(
                        asset_path, f"Could not read MIP count: {exc}"
                    )

            if num_mips is None or (isinstance(num_mips, int) and num_mips <= 0):
                # Fallback: estimate from resolution. A full-resolution texture
                # typically has ~log2(max_dim) + 1 mip levels.
                width = getattr(asset, "size_x", 512) or 512
                max_dim = self.config.get("max_texture_dimension", 4096)
                estimated_mips = min(int(round(max(1, int((width / max_dim).bit_length()))), 8)) + 1
                num_mips = estimated_mips

            if num_mips > max_samples:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message=(
                        f"Texture has {num_mips} sample(s) — exceeds limit of {max_samples}."
                    ),
                    fix_hint=f"Reduce MIP levels to {max_samples} or fewer.",
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message=(
                    f"Texture has {num_mips} sample(s) — within limit of {max_samples}."
                ),
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")

    @staticmethod
    def _get_texture_class():
        """Return the Texture2D class from unreal module."""
        import unreal
        return unreal.Texture2D
