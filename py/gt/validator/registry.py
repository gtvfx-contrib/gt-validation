"""Rule registry: auto-discovery and decorator-based registration.

Provides a global registry that rules can register themselves with using the
``@registry.register`` decorator.  The registry supports auto-discovery of
rules from the rules subpackage.

Usage::

    from validator.registry import registry

    @registry.register
    class MyRule(AbstractRule):
        name = "my_rule"
        ...

"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .rules.base import AbstractRule, Severity

logger = logging.getLogger(__name__)


class RuleRegistry:
    """Singleton registry for AbstractRule subclasses.

    State is stored as **class attributes** so that repeated calls to
    ``RuleRegistry()`` — which Python always routes through ``__init__``
    after ``__new__`` — can never reset an already-populated registry.

    Lifecycle inside a running process:
        1. ``import validator.registry`` → singleton created (empty).
        2. ``runner.discover()`` called → rule modules imported.
        3. Each module-level ``@registry.register`` fires → rules added.
        4. ``runner.get_rules(...)`` returns the filtered class list.
        5. Runner instantiates each class with the shared Config.

    This is the **plugin pattern**: the core framework knows nothing about
    specific rules; rules know about the framework (registry) and register
    themselves.  New rules are dropped in without touching existing code.

    """

    _instance: "RuleRegistry | None" = None
    _rules: "dict[str, Type]" = {}
    _discovered: bool = False

    def __new__(cls) -> "RuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, cls: "Type") -> "Type":
        """Class decorator — registers a rule class.

        Reads ``name``, ``category``, and ``severity`` directly from the class.
        The class is the single source of truth for its metadata; the decorator
        simply announces it to the registry.

        """
        name = getattr(cls, "name", None) or cls.__name__
        if not getattr(cls, "category", ""):
            raise ValueError(
                f"Rule class {cls.__name__} must declare a non-empty "
                f"`category` class attribute before being registered."
            )
        if name in self._rules:
            logger.warning(
                "[Registry] Rule '%s' already registered — overwriting with %s.",
                name, cls.__name__,
            )
        self._rules[name] = cls
        logger.debug("[Registry] Registered rule '%s' (%s).", name, cls.__name__)
        return cls

    def discover(self) -> None:
        """Auto-discover and import all rule modules in the rules subpackage.

        Triggers module-level ``@registry.register`` decorators, populating
        the registry without requiring explicit imports.  Subsequent calls are
        no-ops (discovery runs at most once per process).
        
        """
        if self._discovered:
            return
        type(self)._discovered = True

        from . import rules as rules_pkg
        for _finder, module_name, _is_pkg in pkgutil.iter_modules(rules_pkg.__path__):
            if module_name == "base":
                continue
            full_name = f"{rules_pkg.__name__}.{module_name}"
            try:
                importlib.import_module(full_name)
                logger.debug("[Registry] Discovered module: %s", full_name)
            except ImportError as exc:
                logger.warning(
                    "[Registry] Could not import '%s': %s", full_name, exc
                )

    def getRules(
        self,
        category: str | None = None,
        severity=None,
    ) -> list[Type]:
        """Return registered rule classes, optionally filtered.

        Args:
            category: If provided, only rules with this category are returned.
            severity: If provided, only rules with this severity are returned.

        Returns:
            A list of rule classes matching the given filters.
        
        """
        rules = list(self._rules.values())
        if category:
            cat_lower = category.lower()
            rules = [r for r in rules if r.category.lower() == cat_lower]
        if severity is not None:
            rules = [r for r in rules if r.severity == severity]
        return rules

    def listRules(self) -> dict[str, Type]:
        """Return a copy of the rules dict {name: class}."""
        return dict(self._rules)

    def clear(self) -> None:
        """Clear all registered rules (useful in tests)."""
        self._rules.clear()
        type(self)._discovered = False

    def __len__(self) -> int:
        return len(self._rules)

    def __repr__(self) -> str:
        return f"RuleRegistry(rules={list(self._rules.keys())})"


registry = RuleRegistry()
