"""niagara.py — Validation rules for Unreal Niagara assets.

Rules:
    NiagaraFixedBoundsRule — require fixed bounds on Niagara systems.
"""

from __future__ import annotations

from .base import AbstractRule, Severity, ValidationResult
from ..env import loadUnrealAsset
from ..errors import UnrealAPIError
from ..registry import registry

@registry.register
class NiagaraFixedBoundsRule(AbstractRule):
    """Validates that Niagara systems have fixed bounds set.

    Dynamic bounds force the engine to recompute bounds every frame, which
    is expensive for large particle systems.

    Attributes:
        name: Rule identifier ``"niagara_fixed_bounds"``.
        category: Rule category ``"niagara"``.
        severity: :attr:`Severity.ERROR`.
    
    """
    name     = "niagara_fixed_bounds"
    category = "niagara"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> ValidationResult:
        """Validate that fixed bounds are configured on the given Niagara system.

        Args:
            asset_path: Content-browser path of the asset to validate.

        Returns:
            A :class:`ValidationResult` indicating whether fixed bounds are set,
            or a passing result when the check is disabled via config.
        
        """
        if not self.isEnabled():
            return self._makeResult(
                asset_path, passed=True,
                message="Fixed bounds check disabled via config.",
                asset_class="NiagaraSystem",
            )

        try:
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError as exc:
            return self._makeSkipped(asset_path, str(exc))
        import unreal  # noqa: PLC0415 - deferred Unreal import

        if not isinstance(asset, unreal.NiagaraSystem):
            return self._makeSkipped(
                asset_path, f"Not a NiagaraSystem (got {type(asset).__name__})."
            )

        try:
            fixed_bounds = asset.get_editor_property("fixed_bounds")
            if not fixed_bounds:
                return self._makeResult(
                    asset_path, passed=False,
                    message="Niagara system does not have fixed bounds set.",
                    asset_class="NiagaraSystem",
                    fix_hint=(
                        "Enable 'Fixed Bounds' in the Niagara System editor and set "
                        "appropriate values to avoid per-frame bounds calculation."
                    ),
                )
            return self._makeResult(
                asset_path, passed=True,
                message="Niagara system has fixed bounds configured.",
                asset_class="NiagaraSystem",
            )
        except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
            return self._makeSkipped(asset_path, f"Validation error: {exc}")
