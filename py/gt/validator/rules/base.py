"""Abstract base classes and core data types for all validation rules."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..config import Config


logger = logging.getLogger(__name__)


# Import HostType from the globals runtime detection package.
try:
    from gt.runtime import HostType as _HostType
except ImportError:
    # Fallback if gt.runtime is not available (e.g., in tests).
    _HostType = None  # type: ignore


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
    context: Optional[_HostType] = None  # Type: HostType

    def __init__(self, config: Config, context: Optional[_HostType] = None) -> None:
        """Initialise the rule with config and context.

        Args:
            config: Layered Config object.
            context: Validation context instance (e.g., HostType.UNREAL).

        """
        self.config = config
        if _HostType is not None and context is None:
            # Default to STANDALONE when no explicit context provided.
            self.context = _HostType.STANDALONE
        else:
            self.context = context

    def isEnabled(self) -> bool:
        """Return whether this rule is enabled in the current config and host.

        Reads ``config[f"require_{self.name}"]``, defaulting to ``True``.
        Any rule can be switched off via config without touching rule code.

        Returns:
            ``True`` if this rule should run; ``False`` to skip it.

        """
        if not self.config.get(f"require_{self.name}", True):
            return False

        # If rule has a declared context, check against current runtime.
        if self.context is not None and _HostType is not None:
            from gt.runtime import RuntimeDetector as _RuntimeDetector
            current_host = _RuntimeDetector.getCurrentHost()
            if self.context != current_host:
                logger.debug(
                    "[Rule] %s skipped — requires %s but running in %s.",
                    self.name, self.context.value, current_host.value,
                )
                return False

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

    @classmethod
    def register_rule(cls, name: str, category: str, severity: Severity):
        """Class decorator — registers a rule class with the global registry.

        Usage::

            @AbstractRule.register_rule("my_rule", "my_category", Severity.ERROR)
            class MyRule(AbstractRule):
                ...

        Args:
            name: Unique snake_case identifier for the rule.
            category: Rule category string used for grouping in reports.
            severity: Default :class:`Severity` for non-passing results.

        Returns:
            The decorated class, ready to be registered with ``registry.register``
            after module import.

        """
        def decorator(rule_cls) -> type:
            rule_cls.name = name
            rule_cls.category = category
            rule_cls.severity = severity
            registry.register(rule_cls)
            return rule_cls

        return decorator

    @classmethod
    def register_rule(
        cls, name: str, category: str, severity: Severity
    ):
        """Class decorator — registers a rule class with the global registry.

        Usage::

            @AbstractRule.register_rule("my_rule", "my_category", Severity.ERROR)
            class MyRule(AbstractRule):
                ...

        Args:
            name: Unique snake_case identifier for the rule.
            category: Rule category string used for grouping in reports.
            severity: Default :class:`Severity` for non-passing results.

        Returns:
            The decorated class, ready to be registered with ``registry.register``
            after module import.

        """
        def decorator(rule_cls) -> type:
            rule_cls.name = name
            rule_cls.category = category
            rule_cls.severity = severity
            registry.register(rule_cls)
            return rule_cls

        return decorator
