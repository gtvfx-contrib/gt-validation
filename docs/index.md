# GT Validation

**Asset validation framework for Unreal Engine 5.5.x** — A comprehensive tool for validating game assets against project standards and best practices.

## Key Features

- **Rule-Based Validation** — Extensible rule system with context-aware checks
- **Unreal Engine Integration** — Native support for UE5 asset types and structures
- **Configurable** — JSON-based configuration for custom validation rules
- **Reporting** — Structured reports with multiple output formats

## Quick Start

```python
from gt.validator import ValidationRunner, Config, ValidationReport

runner = ValidationRunner(Config())
report = runner.runAndReport("/path/to/assets")
print(report.summaryLine())
```

## Documentation

| Topic | Description |
|---|---|
| [API Reference](reference/gt/validator.md) | Complete Python API documentation |
