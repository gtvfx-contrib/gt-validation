# GT Validation

Asset validation framework for Unreal Engine 5.5.x — A comprehensive tool for validating game assets against project standards and best practices.

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
| [Home](docs/index.md) | Overview and getting started guide |
| [API Reference](docs/reference/gt/validator.md) | Complete Python API documentation |
| [Rules Module](docs/reference/gt/validator/rules.md) | Validation rule definitions and implementations |
| [Context Module](docs/reference/gt/validator/context.md) | Context-aware validation utilities |
| [Reporting Module](docs/reference/gt/validator/reporting.md) | Report generation and output formatting |

## Installation

```bash
pip install gt-validator
```

## License

MIT License
