"""Abstract base classes and core data types for all validation rules."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from gt.runtime import HostType


if TYPE_CHECKING:
    from ..config import Config


logger = logging.getLogger(__name__)



class Severity(Enum):
    """Severity level for a validation failure.

    Attributes:
        ERROR: Pipeline should stop; asset is unusable.
        WARNING: Pipeline can continue; asset needs attention.
        INFO: Informational note; no action required.

    """

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationResult:
    """Immutable record of one rule applied to one asset.

    Attributes:
        asset_path: Full content-browser or filesystem path of the inspected asset.
        rule_name: Machine-readable snake_case identifier of the rule.
        category: Logical group this rule belongs to (e.g. ``"naming"``).
        severity: Severity of a failure; irrelevant when ``passed`` is ``True``.
        message: Human-readable explanation of the outcome.
        passed: ``True`` if the asset satisfies this rule.
        skipped: ``True`` if the rule was not applicable in this environment.
        timestamp: ISO-format datetime string of when this result was produced.
        duration_ms: Time taken to run this check, in milliseconds.
        asset_class: Unreal asset class name if known, e.g. ``"StaticMesh"``.
        fix_hint: Brief suggestion for how to resolve a failure.

    """

    asset_path: str
    rule_name: str
    category: str
    severity: Severity
    message: str
    passed: bool
    skipped: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0.0
    asset_class: str = ""
    fix_hint: str = ""

    def __str__(self) -> str:
        """Return a human-readable string representation of the result."""
        if self.skipped:
            return (
                f"[SKIP] - [{self.severity.value:<7}] "
                f"{self.rule_name:<30} {self.asset_path}\n"
                f"         {self.message}"
            )
        status = "PASS" if self.passed else "FAIL"
        icon = "v" if self.passed else "x"
        hint = f"\n         Hint: {self.fix_hint}" if self.fix_hint and not self.passed else ""
        return (
            f"[{status}] {icon} [{self.severity.value:<7}] "
            f"{self.rule_name:<30} {self.asset_path}\n"
            f"         {self.message}{hint}"
        )


class AbstractRule(ABC):
    """Abstract base class for all validation rules.

    Subclasses must implement :meth:`validate`.  Helper methods
    :meth:`_makeResult` and :meth:`_makeSkipped` produce correctly
    structured :class:`ValidationResult` instances.

    Attributes:
        name: Unique snake_case identifier for the rule, e.g. ``"naming_convention"``.
        category: Rule category string used for grouping in reports.
        severity: Default :class:`Severity` for non-passing results.
        context: Required host type for this rule (e.g., ``HostType.UNREAL``).

    """

    name: str = ""
    category: str = ""
    severity: Severity = Severity.ERROR
    context: Optional[HostType] = None  # Type: HostType

    def __init__(self, config: Config, context=None) -> None:  # type: ignore[assignment]
        """Initialise the rule with config and optional validation context.

        Args:
            config: Layered Config object.
            context: A :class:`ValidationContext` instance (with ``.collect()``), a tuple/list
                of acceptable contexts for multi-context support, or ``None`` to skip metadata checks.
                If ``None``, the rule will use fallback logic that doesn't require asset metadata.

        Note:
            For multi-context support, subclasses can pass a tuple or list of ValidationContext instances.
            The framework's :class:`ValidationRunner` handles context injection automatically — rules do not need to call this directly.

        """
        self.config = config
        
        if isinstance(context, (tuple, list)):
            # Multi-context support: store as-is for isEnabled() matching logic
            self.contexts = context  # type: ignore[assignment]
            self.context = None
        elif context is not None and hasattr(context, 'collect'):
            # It's a ValidationContext instance — store it directly so rules can call .collect()
            self.context = context
        else:
            # Default to None (rules will use fallback logic that doesn't require metadata)
            self.context = None  # type: ignore[assignment]

    def isEnabled(self) -> bool:
        """Return whether this rule is enabled in the current config and host.

        Reads ``config[f"require_{self.name}"]``, defaulting to ``True``.
        Any rule can be switched off via config without touching rule code.

        Returns:
            ``True`` if this rule should run; ``False`` to skip it.

        """
        if not self.config.get(f"require_{self.name}", True):
            return False

        from gt.runtime import HostType, getCurrentHost

        # Multi-context support via tuple/list of contexts.
        if self.contexts is not None:
            current_host = getCurrentHost()
            for ctx in self.contexts:
                if isinstance(ctx, str):
                    # String context name (e.g., "UNREAL") — compare case-insensitively.
                    if ctx.lower() == current_host.value.lower():
                        return True
                elif ctx == current_host:
                    return True

        # Single declared context (e.g. HostType.UNREAL).
        rule_ctx = getattr(self, 'context', None)
        if rule_ctx is not None and not isinstance(rule_ctx, type(None)):
            try:
                current_host = getCurrentHost()
                if rule_ctx != current_host:
                    logger.debug(
                        "[Rule] %s skipped — context mismatch "
                        "(rule requires %r, current host is %r).",
                        self.name, rule_ctx, current_host,
                    )
                    return False
            except Exception:  # noqa: BLE001 - runtime may not be available
                pass

        return True

    @abstractmethod
    def validate(self, asset_path: str) -> ValidationResult:
        """Apply this rule to the given asset.

        Args:
            asset_path: Content-browser or filesystem path of the asset to validate.

        Returns:
            A :class:`ValidationResult` with pass, fail, or skip status.

        """
        ...

    def _makeResult(
        self,
        asset_path: str,
        passed: bool,
        message: str,
        duration_ms: float = 0.0,
        asset_class: str = "",
        fix_hint: str = "",
    ) -> ValidationResult:
        """Build a pass or fail :class:`ValidationResult`.

        Args:
            asset_path: Content-browser or filesystem path of the validated asset.
            passed: ``True`` if the asset passes this rule.
            message: Human-readable explanation of the result.
            duration_ms: Wall-clock time taken for this check, in milliseconds.
            asset_class: Unreal asset class name if known, e.g. ``"StaticMesh"``.
            fix_hint: Brief suggestion for resolving a failure.

        Returns:
            A fully populated :class:`ValidationResult`.

        """
        return ValidationResult(
            asset_path=asset_path,
            rule_name=self.name,
            category=self.category,
            severity=self.severity,
            message=message,
            passed=passed,
            skipped=False,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            asset_class=asset_class,
            fix_hint=fix_hint,
        )

    def _makeSkipped(self, asset_path: str, reason: str) -> ValidationResult:
        """Build a skipped :class:`ValidationResult`.

        Args:
            asset_path: Content-browser or filesystem path of the asset.
            reason: Human-readable explanation of why the rule was skipped.

        Returns:
            A :class:`ValidationResult` with ``skipped=True`` and ``passed=True``.

        """
        return ValidationResult(
            asset_path=asset_path,
            rule_name=self.name,
            category=self.category,
            severity=self.severity,
            message=reason,
            passed=True,
            skipped=True,
            timestamp=datetime.now().isoformat(),
        )
