"""Asset Validation Framework for Unreal Engine 5.5.x.

Public API::

    from validator import ValidationRunner, Config, ValidationReport

    runner = ValidationRunner(Config())
    report = runner.runAndReport("/path/to/assets")
    print(report.summaryLine())

"""

from ._version import __version__
from .config import Config
from .reporting.models import ValidationReport
from .runner import ValidationRunner

__author__ = "Technical Artist Course — ELVTR"
__all__ = ["ValidationRunner", "Config", "ValidationReport", "__version__"]
