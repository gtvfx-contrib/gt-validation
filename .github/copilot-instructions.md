CRITICAL:

Every response must begin with: [INSTRUCTIONS LOADED]

Target Environment:
You are operating in a Windows environment. Assume Windows 11.

Command Language: 
Always generate PowerShell or standard Windows Command Prompt (cmd) scripts. NEVER generate Linux Bash scripts.

Tool Replacement: 
Use Windows-native CLI alternatives. For example, use 'Select-String' instead of 'grep', 'Get-ChildItem' instead of 'ls', and 'winget' or 'Invoke-WebRequest' instead of 'curl/wget'.

Syntax Enforcement:
Use Windows backslashes (\\) for paths and PowerShell execution policies. Do not use POSIX forward slashes (/) for local file paths.

# GitHub Copilot Instructions for gtvfx-contrib repos.

This file contains coding standards and guidelines that GitHub Copilot should follow when providing code suggestions for this repository.

## Style Guide

Generally, we follow the **PEP 8 style guide** with the following specific modifications and additions:

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Package and Module Names | `snake_case` | `my_module` |
| Class Names | `UpperCamel` | `MyClass` |
| Function Names | `camelCase` | `myFunction` |
| Property Names (`@property`) | `snake_case` | `my_property` |
| Variable Names | `snake_case` | `my_variable` |
| Global Variable Names | `UPPER_SNAKE` | `MY_GLOBAL` |
| Class Variable Names | `snake_case` | `class_variable` |
| Constant Class Variable Names | `UPPER_SNAKE` | `CLASS_CONSTANT` |

**Important:** We use `camelCase` for function names to differentiate functions from variables at a glance. This also applies to stored lambda and partial functions.

**Properties use `snake_case`** because they are accessed without parentheses, making them syntactically indistinguishable from attributes. Using `snake_case` signals "read me like data" and matches Python's own stdlib conventions (`Path.parent`, `Popen.returncode`, etc.).

### Never Override Python Built-ins

**CRITICAL RULE:** Never use variable names that shadow Python built-in functions or types. This causes bugs and makes code confusing.

**Common built-ins to avoid as variable names:**

```python
# Built-in functions - NEVER use as variable names:
id, type, list, dict, set, str, int, float, bool, tuple, range, object
input, open, file, filter, map, next, sum, min, max, abs, all, any
bytes, chr, ord, dir, exit, help, quit, print, format, hash, len
pow, round, sorted, zip, vars, repr, eval, exec, compile
globals, locals, iter, reversed, slice, super, property
staticmethod, classmethod

# BAD - Overrides built-ins:
type = "Window"
dir = "C:/temp"
exit = exit_node
id = node.id
list = []
filter = "*.max"

# GOOD - Use descriptive names instead:
asset_type = "Window"
directory = "C:/temp"
save_directory = mxs.maxFilePath
exit_point = exit_node
node_id = node.id
items = []
file_filter = "*.max"
```

**Why this matters:**
- Shadowing built-ins prevents you from using those functions later in the same scope
- Makes debugging extremely difficult
- Can cause subtle bugs that are hard to track down
- Confuses code readers who expect built-in behavior

**Always check:** Before using short, common variable names, verify they're not Python built-ins by checking if they're syntax-highlighted differently in your editor.

### Line Length

Follow these line length guidelines:

- **Target**: Keep lines under **80 characters** when possible
- **Maximum**: Hard limit of **100 characters** per line
- **Line Breaking Rule**: Only break lines when they approach or exceed 80 characters. Do NOT break lines unnecessarily if they fit comfortably within the limits
- **Long lines**: Break long lines using parentheses, backslashes, or logical break points

```python
# Preferred - under 80 characters (keep on single line)
result = someFunction(arg1, arg2, arg3)

# Acceptable - under 100 characters (keep on single line)
button.clicked.connect(self.someMethodName)

# Only break when approaching/exceeding 80 characters
result = someFunction(
    arg1, arg2, arg3, arg4, arg5, arg6, arg7
)

# Break long strings
message = (
    "This is a very long string that exceeds the line length "
    "limit and should be broken into multiple lines"
)
```

### Protected vs Private Variables

```python
# Preferred - Protected (single underscore)
_member

# Avoid - Private (double underscore, causes name mangling)
__member
```

### Keyword Arguments

Always use long keyword arguments when available:

```python
# Preferred
cmds.ls(selection=True)

# Avoid
cmds.ls(sl=1)

# Use actual boolean values, not integers
selection=True  # Not selection=1
```

### Imports

Use explicit imports and avoid wildcards:

```python
# Preferred
from module import (
    SpecificClass,
    specificFunction,
)

# Avoid
from module import *
```

## Docstring Standards

We follow **Google Style Python docstrings** as documented at:
https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

### Critical Rule: Empty Line at End
**ALWAYS include 1 empty line at the end of docstrings** (unless it's a single-line docstring):

```python
# Single-line docstring - NO empty line needed
def simpleFunction(self):
    """Brief description of the function."""
    return "result"

# Multi-line docstring - empty line required at end
def myFunction(arg1: str, arg2: int) -> str:
    """Brief description of the function.

    Args:
        arg1: Description of first argument.
        arg2: Description of second argument.

    Returns:
        Description of return value.

    """
    return "result"
```

### Google Style Sections
Use these standard sections in order (only include sections that are relevant):

1. **Summary line**: One-line summary that fits on one line
2. **Extended description** (optional): More details after a blank line
3. **Args**: Function/method parameters
4. **Returns**: Return value description
5. **Yields**: For generators (instead of Returns)
6. **Raises**: Exceptions that may be raised
7. **Note** or **Notes**: Additional notes
8. **Example** or **Examples**: Usage examples
9. **Attributes**: For classes, document public attributes
10. **Todo**: Future improvements

### Args Section Format
```python
def exampleFunction(param1, param2=None, *args, **kwargs):
    """Function with various parameter types.

    Args:
        param1 (int): The first parameter.
        param2 (str, optional): The second parameter. Defaults to None.
            Second line of description should be indented.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        bool: True if successful, False otherwise.

    """
```

### Args Section with Type Hints
When using PEP 484 type hints, types are optional in docstring:

```python
def exampleFunction(param1: int, param2: str = None) -> bool:
    """Function with type hints.

    Args:
        param1: The first parameter (type from annotation).
        param2: The second parameter (type from annotation). Defaults to None.

    Returns:
        True if successful, False otherwise.

    """
```

### Returns Section Format
```python
def getResult():
    """Get a result value.

    Returns:
        dict: Dictionary containing:
            - 'success' (bool): Whether operation succeeded
            - 'message' (str): Status message
            - 'data' (list): Result data

    """
```

### Raises Section Format
```python
def validateInput(value):
    """Validate input value.

    Args:
        value: The value to validate.

    Raises:
        ValueError: If value is negative.
        TypeError: If value is not a number.

    """
```

### Class Docstrings
```python
class ExampleClass:
    """Summary line for the class.

    Extended description of the class purpose and usage.

    Attributes:
        attr1 (str): Description of attr1.
        attr2 (int, optional): Description of attr2.

    """

    def __init__(self, param1, param2):
        """Initialize the ExampleClass.

        Note:
            Do not include the `self` parameter in Args section.

        Args:
            param1 (str): Description of param1.
            param2 (int): Description of param2.

        """
        self.attr1 = param1
        self.attr2 = param2
```

### Method Docstrings
```python
class ExampleClass:
    def exampleMethod(self, param1):
        """Brief description of the method.

        Note:
            Do not include the `self` parameter in Args section.

        Args:
            param1: The first parameter.

        Returns:
            True if successful, False otherwise.

        """
        return True
```

### Property Docstrings
```python
@property
def my_property(self):
    """str: Properties should be documented in their getter method.

    The type can be specified at the start of the summary line.

    """
    return self._my_property
```

### Function Overrides
Indicate function overrides in docstrings:

```python
def someMethod(self, param1):
    """Override: Method description.

    This overrides the parent class method to provide custom behavior.

    Args:
        param1: Description of parameter.

    Returns:
        Description of return value.

    """
```

### Examples Section

Use pure Google Style doctest examples within docstrings.
This format works with Sphinx and VS Code IntelliSense.

```python
def exampleFunction(n):
    """Generate numbers from 0 to n-1.

    Args:
        n (int): The upper limit of the range to generate.

    Yields:
        int: The next number in the range of 0 to n-1.

    Examples:
    - Basic usage:
        >>> print([i for i in exampleFunction(4)])
        [0, 1, 2, 3]

    """
    for i in range(n):
        yield i
```

**Multiple Examples with Doctest Formatting:**

Use bullet points (`-`) with doctest examples.

```python
class DatabaseInterface(metaclass=ABCSingleton):
    """Thread-safe singleton with abstract methods.

    Examples:
    - Basic usage:
        >>> db1 = MySQLDatabase()
        >>> db1.query_count = 5
        
        >>> db2 = MySQLDatabase()
        >>> print(db2.query_count)  # 5 (same instance)
        5
        >>> print(db1 is db2)
        True
    
    - Force re-initialization:
        >>> db3 = MySQLDatabase(_reinit=True)
        >>> print(db3.query_count)  # 0 (fresh instance)
        0

    """
```

**Why this format:**
- Works with Sphinx and standard docstring tooling
- Keeps examples readable in VS Code IntelliSense
- Uses one consistent format across the repository

When editing existing docstrings that use plain `>>>` doctest format,
keep them in doctest format and do not leave mixed example formats within
a single docstring.

Do not combine reStructuredText `::` directives with Markdown fenced code
blocks. Pick one format per repository and apply it consistently.

### Note Section
```python
def complexFunction(data):
    """Process complex data.

    Args:
        data: The data to process.

    Returns:
        Processed data.

    Note:
        This function modifies the input data in-place for performance.
        Make a copy if you need to preserve the original.

    """
```

## Type Hints

- Since moving to Python 3, we use type hints following PEP 484
- **Do NOT add partial hints!** Either fully type a function or don't type it at all

```python
# Wrong - partial hints
def someFunction(arg1, arg2: str, arg3):
    ...

# Right - fully typed
def someFunction(arg1: int, arg2: str, arg3: bool) -> str:
    ...

# Right - no hints
def someFunction(arg1, arg2, arg3):
    ...
```

### Avoiding Circular Imports with Type Hints

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module import Type
```

## Required Modules and Patterns



### Exception Standards
**Try to catch specific exceptions rather than using a broad `Exception` catch.**

### DRY Principle (Don't Repeat Yourself)
**Prioritize code reuse and avoid duplication whenever possible:**

```python
# BAD - Duplicated logic in multiple methods
def processInTabAssets(self, data):
    for item in data:
        tree_item = QtWidgets.QTreeWidgetItem(self.tree)
        tree_item.setText(0, item.name)
        tree_item.setExpanded(True)
        # ... 20 lines of setup logic

def processFromFile(self, data):
    for item in data:
        tree_item = QtWidgets.QTreeWidgetItem(self.tree)
        tree_item.setText(0, item.name)
        tree_item.setExpanded(True)
        # ... same 20 lines of setup logic (DUPLICATED!)

# GOOD - Extract common logic into reusable helper method
def _createTreeItem(self, tree_widget, item_data):
    """Helper method to create and configure tree items."""
    tree_item = QtWidgets.QTreeWidgetItem(tree_widget)
    tree_item.setText(0, item_data.name)
    tree_item.setExpanded(True)
    # ... setup logic in one place
    return tree_item

def processInTabAssets(self, data):
    for item in data:
        self._createTreeItem(self.tree, item)

def processFromFile(self, data):
    for item in data:
        self._createTreeItem(self.tree, item)
```

**Code Reuse Strategy:**
1. **Look for existing functions first** - Before writing new code, search for similar functionality
2. **Extract common patterns** - If you see repeated code, create a helper method
3. **Update existing code** - When creating new reusable functions, update older sections to use them
4. **Prefer composition over copy-paste** - Call existing methods rather than duplicating logic

## Code Quality Guidelines

1. **Don't Repeat Yourself (DRY)** - Always prioritize code reuse over duplication
2. **Never override Python built-ins** - Never use `type`, `id`, `list`, `dir`, `exit`, `filter`, etc. as variable names
3. **Follow PEP 8** for general Python style - this takes precedence over existing code style
4. **Use meaningful variable names** that clearly indicate purpose
5. **Write clear, concise docstrings** with the required empty line at the end
6. **Use type hints consistently** - either fully type functions or don't type them
7. **Prefer explicit imports** over wildcard imports
8. **Use camelCase for functions** to distinguish from variables
9. **Use protected variables** (`_variable`) over private ones (`__variable`)
10. **Always use long-form keyword arguments** when available
11. **Try to catch specific exceptions** rather than using a broad `Exception` catch

## Common Patterns to Follow

When suggesting code, consider these repository-specific patterns:

- Package structure follows the `gt/package_name` pattern
- Follow the Qt shim pattern for UI code
- **Prioritize our coding standards** over matching existing inconsistent code style
- **Always improve code quality** - don't perpetuate poor patterns just for consistency

## Important Reminders for Copilot

- **NEVER duplicate code** - Always look for existing functions to reuse or create new ones
- **NEVER override Python built-ins** - Never use `type`, `id`, `list`, `dir`, `exit`, `filter`, etc. as variable names
- **ALWAYS add an empty line at the end of docstrings** (except for single-line docstrings)
- **Follow PEP 8 and our standards** - Don't match poor existing code style
- Try to catch specific exceptions if able over `Exception as e`
- Use `camelCase` for function names (not `snake_case`)
- Follow the specific naming conventions outlined above
- Use explicit imports and avoid wildcards
- Prefer protected over private variables
- Use full keyword argument names
- Include proper type hints (all or nothing)
- **Extract and reuse common logic** instead of copy-pasting code
