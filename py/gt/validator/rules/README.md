# Context-Aware Validation Rules

## Overview

The validation framework now supports context-aware rules that automatically filter based on the current runtime environment (Unreal, Maya, Max, Houdini, Blender, Krita, or Standalone).

## Key Changes

### 1. Context-Aware Rules

Rules now require a `context` attribute that specifies which host type they support:

```python
from gt.runtime import HostType
from .base import AbstractRule, Severity
from ..registry import registry

@registry.register
class MyRule(AbstractRule):
    name = "my_rule"
    category = "my_category"
    severity = Severity.ERROR
    context = HostType.UNREAL  # Required: only runs in Unreal

    def __init__(self, config: "Config", context: HostType) -> None:
        super().__init__(config)
        self.context = context

    def validate(self, asset_path: str) -> ValidationResult:
        # Context is guaranteed to be HostType.UNREAL
        # No more try/except blocks needed
        ...
```

### 2. Registry Filtering

The registry automatically filters rules based on the current context:

```python
# Get all rules for the current context
rules = registry.getRules(context=HostType.UNREAL)

# Get all rules (no filter)
all_rules = registry.getRules()
```

### 3. Automatic Context Detection

The framework automatically detects the current host and passes it to rules:

```python
# In ValidationRunner.__init__
from gt.runtime import HostType
current_context = HostType.UNREAL
self.rules = [R(config, context=current_context) for R in rule_classes]
```

## HostType Enum

The `HostType` enum defines all supported host types:

- `HostType.STANDALONE` - Standalone Python
- `HostType.UNREAL` - Unreal Engine
- `HostType.MAYA` - Autodesk Maya
- `HostType.MAX` - Autodesk 3ds Max
- `HostType.HOUDINI` - SideFX Houdini
- `HostType.BLENDER` - Blender
- `HostType.KRITA` - Krita

## Migration Guide

### Before (Fragile Context Detection)

```python
from ..env import HAS_UNREAL, loadUnrealAsset
from ..registry import registry

@registry.register
class MyRule(AbstractRule):
    name = "my_rule"
    category = "my_category"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> ValidationResult:
        # Fragile try/except blocks
        try:
            if not HAS_UNREAL:
                return self._makeSkipped(asset_path, "Unreal not available")
            
            asset = loadUnrealAsset(asset_path)
        except UnrealAPIError:
            return self._makeSkipped(asset_path, "Failed to load asset")
        
        # ... validation logic
```

### After (Context-Aware)

```python
from gt.runtime import HostType
from ..registry import registry

@registry.register
class MyRule(AbstractRule):
    name = "my_rule"
    category = "my_category"
    severity = Severity.ERROR
    context = HostType.UNREAL  # Required

    def __init__(self, config: "Config", context: HostType) -> None:
        super().__init__(config)
        self.context = context

    def validate(self, asset_path: str) -> ValidationResult:
        # Context is guaranteed to be HostType.UNREAL
        # No more try/except needed
        asset = loadUnrealAsset(asset_path)
        # ... validation logic
```

## Benefits

1. **No More Fragile Context Detection**: Rules no longer need try/except blocks
2. **Type Safety**: `HostType` enum provides compile-time safety
3. **Better Separation of Concerns**: Registry handles context filtering
4. **Easier Testing**: Context can be mocked in tests
5. **Future-Proof**: Easy to add new host types

## Registry API

### getRules()

```python
def getRules(
    category: str | None = None,
    severity=None,
    context: HostType | None = None,
) -> list[Type]:
    """Return registered rule classes, optionally filtered.

    Args:
        category: If provided, only rules with this category are returned.
        severity: If provided, only rules with this severity are returned.
        context: If provided, only rules with this context are returned.

    Returns:
        A list of rule classes matching the given filters.
    """
```

### Context Filtering

```python
# Filter by context
unreal_rules = registry.getRules(context=HostType.UNREAL)
maya_rules = registry.getRules(context=HostType.MAYA)

# No filter (all rules)
all_rules = registry.getRules()

# Filter by category and context
unreal_naming_rules = registry.getRules(
    category="naming",
    context=HostType.UNREAL
)
```

## ValidationRunner

The `ValidationRunner` automatically gets the current context and passes it to rules:

```python
from gt.runtime import HostType
from .runner import ValidationRunner

# Get current context
current_context = HostType.UNREAL

# Create runner (context is automatically passed to rules)
runner = ValidationRunner(
    config,
    category="texture",
    severity=Severity.ERROR,
    max_workers=4
)
```

## Testing

### Unit Tests

```python
import unittest
from unittest.mock import Mock
from gt.runtime import HostType
from .base import AbstractRule
from .registry import registry

class TestContextAwareRules(unittest.TestCase):
    def setUp(self) -> None:
        registry.clear()
        self.config = Mock()
        self.config.get = Mock(return_value=True)

    def test_rule_with_context(self) -> None:
        @registry.register
        class TestRule(AbstractRule):
            name = "test_rule"
            category = "test"
            severity = Severity.ERROR
            context = HostType.UNREAL

            def __init__(self, config: "Config", context: HostType) -> None:
                super().__init__(config)
                self.context = context

            def validate(self, asset_path: str) -> AbstractRule:
                ...

        registry.discover()
        rule = TestRule(self.config, HostType.UNREAL)
        self.assertEqual(rule.context, HostType.UNREAL)
```

## Migration Checklist

- [ ] Add `context` attribute to all rules
- [ ] Update `__init__` method to accept `context` parameter
- [ ] Remove try/except blocks from rules
- [ ] Remove `import unreal` statements (no longer needed)
- [ ] Update docstrings to reflect context requirement
- [ ] Test rules in different environments (standalone, Unreal, Maya, etc.)

## Troubleshooting

### Rule Not Running

If a rule is not running, check:
1. Does the rule have a `context` attribute?
2. Is the `context` value correct for the current environment?
3. Is the registry filtering by context?

### Context Not Set

If you get a `TypeError` about missing `context` parameter:
1. Ensure the rule has a `context` attribute
2. Verify the `__init__` method accepts `context` as a parameter
3. Check that the registry is passing context to rules

## Future Enhancements

- [ ] Add support for multiple contexts per rule
- [ ] Add context-based enable/disable configuration
- [ ] Add context-aware logging
- [ ] Add context-based performance monitoring
