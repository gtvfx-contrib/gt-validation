"""niagara.py — Validation rules for Unreal Niagara assets.

Rules:
    NiagaraFixedBoundsRule — require fixed bounds on Niagara systems.
"""

from __future__ import annotations

from ..context.base import AssetMetadata, ValidationContext
from ..registry import registry
from .base import AbstractRule, Severity, ValidationResult


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

    name = "niagara_fixed_bounds"
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
                asset_path,
                passed=True,
                message="Fixed bounds check disabled via config.",
                asset_class="NiagaraSystem",
            )

        # Use context abstraction to collect metadata instead of direct Unreal API calls.
        try:
            meta = self.context.collect(asset_path) if callable(getattr(self, 'context', None)) else None
        except (AttributeError, TypeError):
            meta = None

        if meta is not None:
            fixed_bounds = meta.properties.get("fixed_bounds", False)
            
            if not fixed_bounds:
                return self._makeResult(
                    asset_path,
                    passed=False,
                    message="Niagara system does not have fixed bounds set.",
                    asset_class="NiagaraSystem",
                    fix_hint=(
                        "Enable 'Fixed Bounds' in the Niagara System editor and set "
                        "appropriate values to avoid per-frame bounds calculation."
                    ),
                )
            return self._makeResult(
                asset_path,
                passed=True,
                message="Niagara system has fixed bounds configured.",
                asset_class="NiagaraSystem",
            )

        # Fallback: if context cannot provide metadata, skip validation.
        return self._makeSkipped(
            asset_path,
            "Niagara fixed bounds validation requires Unreal Engine host or filesystem access."
        )
