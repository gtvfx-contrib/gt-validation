"""material.py — Validation rules for Unreal Material assets.

Rules:
    MaterialBlendModeRule — flag translucent materials.
    MaterialTwoSidedRule — flag two-sided materials.
    MaterialShadingModelRule — flag complex shading models.

"""
from __future__ import annotations

from .base import AbstractRule, Severity, ValidationResult
from ..config import Config
from ..env import loadUnrealAsset
from ..errors import UnrealAPIError
from ..registry import registry
from gt.runtime import HostType


@registry.register
class MaterialBlendModeRule(AbstractRule):
    """Flags materials with translucent blend modes.

    Translucent materials incur extra rendering overhead.  This rule warns
    when a material uses translucent, additive, or modulate blending.

    Attributes:
        name: Rule identifier ``"material_blend_mode"``.
        category: Rule category ``"material"``.
        severity: :attr:`Severity.WARNING`.
        context: Required host type for this rule (HostType.UNREAL).

    """
    name = "material_blend_mode"
    category = "material"
    severity = Severity.WARNING
    context = HostType.UNREAL

    def __init__(self, config: "Config", context: HostType) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the blend mode of the given material asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether the material uses an
            acceptable blend mode.

        """
        asset = loadUnrealAsset(asset_path)

        if not isinstance(asset, unreal.Material):
            return self._makeSkipped(asset_path, f"Not a Material (got {type(asset).__name__}).")

        try:
            blend_mode = asset.get_editor_property("blend_mode")
        except Exception:  # noqa: BLE001 - Unreal bridge safety
            blend_mode = asset.blend_mode

        is_translucent = blend_mode in (
            unreal.BlendMode.BLEND_TRANSLUCENT,
            unreal.BlendMode.BLEND_ADDITIVE,
            unreal.BlendMode.BLEND_MODULATE,
        )

        if is_translucent:
            return self._makeResult(
                asset_path, passed=False,
                message=(
                    f"Material uses translucent blend mode '{blend_mode}'. "
                    f"Translucent materials are expensive — use with caution."
                ),
                asset_class="Material",
                fix_hint=(
                    "Consider using Masked or Opaque blend mode if "
                    "transparency is not essential."
                ),
            )
        return self._makeResult(
            asset_path, passed=True,
            message=f"Material blend mode '{blend_mode}' is acceptable.",
            asset_class="Material",
        )


@registry.register
class MaterialTwoSidedRule(AbstractRule):
    """Flags materials with two-sided rendering enabled.

    Two-sided rendering doubles the number of fragments to shade.

    Attributes:
        name: Rule identifier ``"material_two_sided"``.
        category: Rule category ``"material"``.
        severity: :attr:`Severity.INFO`.
        context: Required host type for this rule (HostType.UNREAL).

    """
    name = "material_two_sided"
    category = "material"
    severity = Severity.INFO
    context = HostType.UNREAL

    def __init__(self, config: "Config", context: HostType) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate the two-sided setting of the given material asset.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether two-sided rendering
            is disabled on the material.

        """
        asset = loadUnrealAsset(asset_path)

        if not isinstance(asset, unreal.Material):
            return self._makeSkipped(asset_path, f"Not a Material (got {type(asset).__name__}).")

        try:
            if asset.get_editor_property("two_sided"):
                return self._makeResult(
                    asset_path, passed=False,
                    message="Material has Two-Sided rendering enabled — increases draw call cost.",
                    asset_class="Material",
                    fix_hint=(
                        "Disable Two-Sided unless required (e.g. "
                        "foliage). Consider geometry normals instead."
                    ),
                )
            return self._makeResult(
                asset_path, passed=True,
                message="Material Two-Sided is disabled.",
                asset_class="Material",
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")


@registry.register
class MaterialShadingModelRule(AbstractRule):
    """Warns when a material uses a complex or unusual shading model.

    Complex shading models (Subsurface, SubsurfaceProfile,
    TwoSidedFoliage, Hair, Cloth, Eye) add GPU cost and are appropriate
    for specific asset types. This rule flags them so they are used
    intentionally.

    Config key: allowed_shading_models (list[str]).
    Default allowlist: DefaultLit, Unlit, ClearCoat.

    Attributes:
        name: Rule identifier ``"material_shading_model"``.
        category: Rule category ``"material"``.
        severity: :attr:`Severity.WARNING`.
        context: Required host type for this rule (HostType.UNREAL).

    """
    name = "material_shading_model"
    category = "material"
    severity = Severity.WARNING
    context = HostType.UNREAL

    _COMPLEX: tuple[str, ...] = (
        "Subsurface",
        "SubsurfaceProfile",
        "TwoSidedFoliage",
        "Hair",
        "Cloth",
        "Eye",
        "SingleLayerWater",
        "ThinTranslucent",
    )

    def __init__(self, config: "Config", context: HostType) -> None:
        super().__init__(config, context)

    def validate(self, asset_path: str) -> ValidationResult:
        """Check that the material does not use a complex shading model.

        Args:
            asset_path: Unreal content path of the Material asset to inspect.

        Returns:
            A :class:`ValidationResult` describing the check outcome.

        """
        import unreal as _ue  # noqa: PLC0415

        try:
            asset = _ue.EditorAssetLibrary.load_asset(asset_path)
        except Exception as exc:  # noqa: BLE001 - Unreal C++ bridge raises undocumented exceptions
            return self._makeSkipped(asset_path, f"Failed to load asset: {exc}")
        if asset is None or not isinstance(asset, _ue.Material):
            return self._makeSkipped(asset_path, "Asset is not a Material.")

        try:
            shading_model = str(asset.get_editor_property("shading_model"))
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(
                asset_path,
                f"Could not read material shading model: {exc}",
            )
        complex_match = next(
            (name for name in self._COMPLEX if name.lower() in shading_model.lower()),
            None,
        )

        if complex_match:
            return self._makeResult(
                asset_path,
                passed=False,
                message=(
                    f"Material uses complex shading model '{complex_match}' — "
                    "verify this is intentional."
                ),
                fix_hint=(
                    "Use DefaultLit unless the asset specifically requires a "
                    "complex shading model (e.g. character skin to "
                    "SubsurfaceProfile)."
                ),
                asset_class="Material",
            )

        return self._makeResult(
            asset_path,
            passed=True,
            message=f"Shading model '{shading_model}' is acceptable.",
            asset_class="Material",
        )
