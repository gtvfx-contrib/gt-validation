"""JSON report exporter for validation results.

Exports validation results as structured JSON files with per-asset details,
summary statistics, and optional metadata fields.

Usage::

    from gt.validator.reporters.json_reporter import JsonReporter

    reporter = JsonReporter(output_path="validation_report.json")
    reporter.export(validation_results)

"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..reporting.models import ValidationReport
from ..rules.base import Severity

logger = logging.getLogger(__name__)


class JsonReporter:
    """Exports validation results as structured JSON files.

    Includes per-asset results with rule details, pass/fail status, severity
    levels, and summary statistics organized by category.

    Attributes:
        output_path: Filesystem path for the JSON report file.

    """

    def __init__(self, output_path: str) -> None:
        """Initialise the JSON reporter with an output file path.

        Args:
            output_path: Absolute or relative filesystem path where the JSON
                report will be written.

        Raises:
            TypeError: If ``output_path`` is not a string.

        """
        if not isinstance(output_path, str):
            raise TypeError(
                f"output_path must be a str, got {type(output_path).__name__}"
            )
        self.output_path = output_path
        self._report: ValidationReport | None = None

    def export(self, report: ValidationReport) -> str:
        """Export validation results to a JSON file.

        Args:
            report: The :class:`~validator.reporting.models.ValidationReport`
                containing the results to serialize.

        Returns:
            The absolute path of the written report file.

        Raises:
            TypeError: If ``report`` is not a :class:`ValidationReport`.

        """
        if not isinstance(report, ValidationReport):
            raise TypeError(
                f"Expected ValidationReport instance, got {type(report).__name__}"
            )

        self._report = report

        # Build the JSON-serializable structure
        data: dict[str, Any] = {}

        # Metadata section
        metadata: dict[str, str] = {}
        metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
        if hasattr(report, "tool_version") and report.tool_version:
            metadata["tool_version"] = report.tool_version
        if hasattr(report, "duration_ms"):
            metadata["duration_ms"] = round(report.duration_ms, 1)

        # Host type detection (best-effort)
        try:
            from gt.runtime import RuntimeDetector as _RuntimeDetector
            host_type = _RuntimeDetector.getCurrentHost()
            if host_type is not None:
                metadata["host_type"] = host_type.value
        except ImportError:
            pass  # Standalone mode has no runtime info

        data["metadata"] = metadata

        # Summary statistics section
        summary = self._build_summary(report)
        data["summary"] = summary

        # Per-asset results grouped by category
        per_asset: dict[str, list[dict]] = {}
        for result in report.results:
            category = getattr(result, "category", "") or "uncategorized"
            per_asset.setdefault(category, []).append(
                self._result_to_dict(result)
            )

        data["results"] = per_asset

        # Write to file with proper error handling
        try:
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(
                "[JsonReporter] Report written to %s (%d results across %d categories)",
                self.output_path,
                len(report.results),
                len(per_asset),
            )
            return os.path.abspath(self.output_path)
        except PermissionError:
            raise OSError(f"Permission denied writing to {self.output_path}")
        except OSError as e:
            logger.error("[JsonReporter] Failed to write report: %s", e)
            raise

    def _build_summary(
        self, report: ValidationReport
    ) -> dict[str, Any]:
        """Build summary statistics from a validation report.

        Args:
            report: The :class:`ValidationReport` containing results.

        Returns:
            A dictionary with summary counts by category and severity.

        """
        total = len(report.results)
        passed = report.passed
        failed = report.failed
        skipped = report.skipped
        errors = report.errors
        warnings = report.warnings

        # Summary by category
        categories: dict[str, dict] = {}
        for result in report.results:
            cat = getattr(result, "category", "") or "uncategorized"
            if cat not in categories:
                categories[cat] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "errors": 0,
                    "warnings": 0,
                }
            categories[cat]["total"] += 1
            if result.passed and not result.skipped:
                categories[cat]["passed"] += 1
            elif not result.passed and not result.skipped:
                categories[cat]["failed"] += 1
            else:
                categories[cat]["skipped"] += 1

        # Count severities per category for failed results
        for result in report.failures():
            cat = getattr(result, "category", "") or "uncategorized"
            if cat not in categories:
                categories.setdefault(cat, {"total": 0})
                categories[cat]["failed"] = 0

        # Build summary dict with counts by category and severity
        summary: dict[str, Any] = {
            "total_assets": report.asset_count,
            "total_results": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "warnings": warnings,
            "categories": categories,
        }

        # Assets with failures grouped by asset path
        assets_with_failures = report.assetsWithFailures()
        if assets_with_failures:
            summary["assets_with_failures"] = {
                path: len(results) for path, results in assets_with_failures.items()
            }

        return summary

    def _result_to_dict(self, result) -> dict[str, Any]:
        """Convert a single :class:`ValidationResult` to a JSON-compatible dict.

        Args:
            result: A :class:`~validator.rules.base.ValidationResult` instance.

        Returns:
            A dictionary representation of the result suitable for JSON export.

        """
        return {
            "asset_path": getattr(result, "asset_path", ""),
            "rule_name": getattr(result, "rule_name", ""),
            "category": getattr(result, "category", ""),
            "severity": getattr(result, "severity", None).value if result.severity else "",
            "passed": result.passed if hasattr(result, "passed") else False,
            "skipped": result.skipped if hasattr(result, "skipped") else False,
            "message": getattr(result, "message", ""),
            "fix_hint": getattr(result, "fix_hint", ""),
            "timestamp": getattr(result, "timestamp", ""),
            "duration_ms": round(getattr(result, "duration_ms", 0.0), 1),
        }
