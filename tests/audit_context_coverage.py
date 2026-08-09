"""Audit script to check rule context coverage."""

import importlib
import inspect
from pathlib import Path

# Add py directory to path (validation/py, one level up from this script in
# validation/tests/).
py_dir = Path(__file__).parent.parent / "py"
import sys
sys.path.insert(0, str(py_dir))

from gt.validator.rules.base import AbstractRule
from gt.runtime import HostType


def _check_init_signature(cls) -> str | None:
    """Flag __init__ overrides incompatible with ValidationRunner's instantiation contract.

    ``ValidationRunner`` always instantiates every selected rule class via
    ``R(config, validation_context=ctx)``. A rule that overrides ``__init__``
    without accepting a ``validation_context`` parameter (or **kwargs) will
    raise ``TypeError`` the moment it is selected for instantiation under its
    declared host context — a defect that is invisible to test suites which
    only ever mock a *different* HostType (since the runner's context-filter
    excludes the rule from instantiation entirely in that case). This is
    exactly the bug that shipped in ``MaterialSlotCountRule`` /
    ``MaterialComplexityRule`` / ``MaxTranslucentMaterialsRule`` before their
    broken ``__init__`` overrides were removed.

    Args:
        cls: A rule class (``AbstractRule`` subclass) to inspect.

    Returns:
        A human-readable issue description if the ``__init__`` override is
        incompatible with the base contract, or ``None`` if the class either
        inherits ``AbstractRule.__init__`` unchanged or its override safely
        accepts ``validation_context``.

    """
    if "__init__" not in cls.__dict__:
        return None  # Inherits AbstractRule.__init__ unchanged — always compatible.

    try:
        sig = inspect.signature(cls.__dict__["__init__"])
    except (TypeError, ValueError):
        return None

    params = sig.parameters
    has_var_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    if has_var_kwargs or "validation_context" in params:
        return None

    return (
        "__init__ override does not accept a 'validation_context' parameter — "
        "ValidationRunner always instantiates rules via "
        "R(config, validation_context=ctx), so this will raise TypeError as soon "
        "as this rule's context matches the active host."
    )


def audit_rules():
    """Audit all rule classes for context coverage."""
    rules_dir = py_dir / "gt" / "validator" / "rules"
    
    # Import all rule modules
    rule_modules = []
    for py_file in rules_dir.glob("*.py"):
        if py_file.name.startswith("_") or py_file.name == "base.py":
            continue
        
        module_name = f"gt.validator.rules.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)
            rule_modules.append((module.__name__, module))
        except Exception as e:
            print(f"ERROR importing {module_name}: {e}")
    
    # Find all rule classes
    rule_classes = []
    for mod_name, module in rule_modules:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, AbstractRule) and obj is not AbstractRule:
                rule_classes.append((name, obj, mod_name))
    
    # Audit each rule class
    print(f"Found {len(rule_classes)} rule classes\n")
    print("=" * 80)
    
    issues = []
    for class_name, cls, module_name in sorted(rule_classes):
        context_attr = getattr(cls, 'context', None)
        
        status = "[OK]" if context_attr is not None else "[MISSING]"
        context_str = str(context_attr) if context_attr is not None else "None"
        
        print(f"{status} {class_name:40s} | Context: {context_str}")
        
        # Check for issues
        if context_attr is None:
            issues.append({
                'class': class_name,
                'module': module_name,
                'issue': 'Missing context attribute',
                'severity': 'ERROR'
            })
        elif isinstance(context_attr, HostType):
            # Check if rule is Unreal-only but has STANDALONE context (or vice versa)
            if cls.__name__.startswith(('SkeletalMesh', 'LOD', 'StaticMesh', 'Niagara')):
                if context_attr == HostType.STANDALONE:
                    issues.append({
                        'class': class_name,
                        'module': module_name,
                        'issue': f'Unreal-only rule has STANDALONE context (should be UNREAL)',
                        'severity': 'WARNING'
                    })

        init_issue = _check_init_signature(cls)
        if init_issue is not None:
            issues.append({
                'class': class_name,
                'module': module_name,
                'issue': init_issue,
                'severity': 'ERROR',
            })
    
    print("=" * 80)
    print(f"\nFound {len(issues)} issues:\n")
    
    for issue in sorted(issues, key=lambda x: (-1 if x['severity'] == 'ERROR' else 0, x['class'])):
        print(f"  [{issue['severity']}] {issue['class']:40s} - {issue['issue']}")
        print(f"           Module: {issue['module']}")
    
    return issues


if __name__ == "__main__":
    issues = audit_rules()
    sys.exit(1 if any(i['severity'] == 'ERROR' for i in issues) else 0)
