"""Output formatters for :class:`~validator.reporting.models.ValidationReport`.

Three formatters, one interface — ``formatter.format(report)`` returns a string:
- :class:`ConsoleFormatter` — ANSI-colored terminal output with severity icons.
- :class:`JSONFormatter`    — Machine-readable JSON for CI systems and dashboards.
- :class:`HTMLFormatter`    — Self-contained single-file HTML report with
                              collapsible per-asset sections.

Usage::
    report = runner.runAndReport(directory)
    print(ConsoleFormatter().format(report))
    Path("report.json").write_text(JSONFormatter().format(report))
    Path("report.html").write_text(HTMLFormatter().format(report))

"""

from __future__ import annotations

import json
import re

from datetime import datetime

from .models import ValidationReport

from ..rules.base import Severity, ValidationResult

# ── ANSI codes ────────────────────────────────────────────────────────────── #
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_GREEN  = "\033[32m"
_CYAN   = "\033[36m"
_WHITE  = "\033[37m"

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')

_SEV_COLOR: dict[Severity, str] = {
    Severity.ERROR:   _RED,
    Severity.WARNING: _YELLOW,
    Severity.INFO:    _CYAN,
}

_SEV_ICON: dict[Severity, str] = {
    Severity.ERROR:   "✗",
    Severity.WARNING: "⚠",
    Severity.INFO:    "ℹ",
}


def _groupByAsset(results: list[ValidationResult]) -> dict[str, list[ValidationResult]]:
    """Group results by asset path, preserving insertion order.

    Args:
        results: Flat list of ValidationResult objects.
    Returns:
        Ordered dict mapping asset path → list of results for that asset.

    """
    grouped: dict[str, list[ValidationResult]] = {}

    for r in results:
        grouped.setdefault(r.asset_path, []).append(r)

    return grouped


class ConsoleFormatter:
    """ANSI-colored terminal report.

    Output structure::
        ━━━ HEADER (timestamp, counts, duration) ━━━
        Per-asset groups  (failures + skips by default; passes optional)
            Each result: icon  severity  rule_name  message  [fix_hint]
        ━━━ SUMMARY BAR ━━━

    Args:
        show_passing: Include passing results in output (default: ``False``).
        use_color: Emit ANSI color codes. Set to ``False`` when output does not
            support ANSI (e.g. Unreal Output Log). Defaults to ``True``.

    """
    def __init__(self, show_passing: bool = False, use_color: bool = True) -> None:
        self.show_passing = show_passing
        self._use_color = use_color

    def format(self, report: ValidationReport) -> str:
        """Format *report* as a terminal string, with or without ANSI color.

        Args:
            report: The ValidationReport to format.

        Returns:
            A multi-line string ready to pass to ``print()``.

        """
        text = self._renderColored(report)

        if not self._use_color:
            return _ANSI_RE.sub("", text)

        return text

    def _renderColored(self, report: ValidationReport) -> str:
        """Render *report* as an ANSI-colored terminal string.

        Args:
            report: The ValidationReport to render.

        Returns:
            A multi-line ANSI-colored string.

        """
        lines: list[str] = []
        w = 72

        # ── Header ──────────────────────────────────────────────────── #
        lines.append(_BOLD + "━" * w + _RESET)
        lines.append(_BOLD + "  ASSET VALIDATION REPORT" + _RESET)
        lines.append("━" * w)
        lines.append(f"  Run at     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Assets     : {report.asset_count}")
        lines.append(f"  Rules      : {report.rule_count}")
        lines.append(f"  Duration   : {report.duration_ms:.1f} ms")
        lines.append("─" * w)

        # ── Per-asset grouping ───────────────────────────────────────── #

        if not report.results:
            lines.append("  No results to display.")
        else:
            for asset_path, results in _groupByAsset(report.results).items():
                has_failures = any(not r.passed and not r.skipped for r in results)
                has_skips    = any(r.skipped for r in results)

                if not self.show_passing and not has_failures and not has_skips:
                    continue

                lines.append(f"\n  {_BOLD}📁  {asset_path}{_RESET}")

                for r in results:
                    if not self.show_passing and r.passed and not r.skipped:
                        continue

                    lines.append(self._formatResult(r))

        # ── Summary bar ──────────────────────────────────────────────── #
        lines.append("\n" + "━" * w)
        lines.append(_BOLD + "  SUMMARY" + _RESET)
        lines.append("─" * w)

        p  = report.passed
        f  = report.failed
        s  = report.skipped
        e  = report.errors
        wn = report.warnings

        lines.append(
            f"  {_GREEN}✓ Passed{_RESET}  {p:>4}    "
            f"{_RED}✗ Failed{_RESET}  {f:>4}    "
            f"{_DIM}↷ Skipped{_RESET} {s:>4}"
        )

        if e:
            lines.append(f"  {_RED}{_BOLD}  Errors   : {e}{_RESET}")
        if wn:
            lines.append(f"  {_YELLOW}  Warnings : {wn}{_RESET}")

        if f == 0 and e == 0:
            lines.append(f"  {_GREEN}{_BOLD}  All assets passed every check! 🎉{_RESET}")

        lines.append("━" * w + "\n")
        return "\n".join(lines)

    def _formatResult(self, r: ValidationResult) -> str:
        """Format a single ValidationResult as a colored console line.

        Args:
            r: The ValidationResult to format.

        Returns:
            A single string (possibly multi-line if fix_hint is present).

        """
        if r.skipped:
            return (
                f"    {_DIM}↷ [SKIP   ] "
                f"{r.rule_name:<28} {r.message}{_RESET}"
            )

        color = _SEV_COLOR.get(r.severity, _WHITE)
        icon  = _SEV_ICON.get(r.severity, "?")

        if r.passed:
            return (
                f"    {_GREEN}✓ [PASS   ] "
                f"{r.rule_name:<28} {r.message}{_RESET}"
            )

        line = (
            f"    {color}{icon} [{r.severity.value:<7}] "
            f"{r.rule_name:<28} {r.message}{_RESET}"
        )

        if r.fix_hint:
            line += f"\n      {_DIM}💡 {r.fix_hint}{_RESET}"
        return line


class JSONFormatter:
    """Machine-readable JSON report.

    Structure::
        {
          "generated_at": "...",
          "tool_version": "...",
          "duration_ms": 0.0,
          "asset_count": 0,
          "rule_count": 0,
          "summary": {
            "status": "PASS",
            "total": 0, "passed": 0, "failed": 0,
            "errors": 0, "warnings": 0, "infos": 0, "skipped": 0
          },

          "results": [ { ... } ]
        }

    Args:
        show_passing: Include passing results in the ``results`` array
            (default: ``False``).

    """
    def __init__(self, show_passing: bool = False) -> None:
        self.show_passing = show_passing

    def format(self, report: ValidationReport) -> str:
        """Format *report* as a formatted JSON string.

        Args:
            report: The ValidationReport to format.

        Returns:
            A UTF-8 JSON string, indented by 2 spaces.

        """
        results_data = [
            self._resultToDict(r) for r in report.results
            if self.show_passing or not r.passed or r.skipped
        ]

        data = {
            "generated_at": datetime.now().isoformat(),
            "tool_version": report.tool_version,
            "duration_ms":  report.duration_ms,
            "asset_count":  report.asset_count,
            "rule_count":   report.rule_count,

            "summary": {
                "status":   "FAIL" if report.hasErrors() else "PASS",
                "total":    report.total,
                "passed":   report.passed,
                "failed":   report.failed,
                "errors":   report.errors,
                "warnings": report.warnings,
                "infos":    report.infos,
                "skipped":  report.skipped,
            },

            "results": results_data,
        }

        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def _resultToDict(r: ValidationResult) -> dict:
        """Serialise a single ValidationResult to a JSON-friendly dict.

        Args:
            r: The ValidationResult to convert.

        Returns:
            A dict with all public fields, ready for ``json.dumps``.

        """
        return {
            "asset_path":  r.asset_path,
            "rule_name":   r.rule_name,
            "category":    r.category,
            "severity":    r.severity.value,
            "message":     r.message,
            "passed":      r.passed,
            "skipped":     r.skipped,
            "timestamp":   r.timestamp,
            "duration_ms": r.duration_ms,
            "asset_class": r.asset_class,
            "fix_hint":    r.fix_hint,
        }


class HTMLFormatter:
    """Self-contained single-file HTML report.

    Features:
    - Inline CSS only (no CDN, no external dependencies).
    - Color-coded severity rows.
    - Summary table at top.
    - Collapsible per-asset sections (``<details>``/``<summary>``).
    - Severity badge, rule name, message, fix_hint per result row.
    - Footer with tool version and run timestamp.

    Args:
        show_passing: Include passing results in the per-asset tables
            (default: ``False``).

    """
    _SEV_BADGE: dict[str, tuple[str, str]] = {
        "ERROR":   ("ERROR", "sev-error"),
        "WARNING": ("WARN",  "sev-warn"),
        "INFO":    ("INFO",  "sev-info"),
    }

    def __init__(self, show_passing: bool = False) -> None:
        self.show_passing = show_passing

    def format(self, report: ValidationReport) -> str:
        """Format *report* as a self-contained HTML document string.

        Args:
            report: The ValidationReport to format.

        Returns:
            A complete HTML document as a string (UTF-8 safe).

        """
        summary_html = self._renderSummary(report)
        assets_html  = self._renderAssets(report)
        css          = self._css()
        now          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Asset Validation Report</title>
  <style>
{css}
  </style>
</head>
<body>
  <div class="container">
    <h1>Asset Validation Report</h1>
    <div class="meta">
      <span>Run at: <strong>{self._esc(now)}</strong></span>
      <span>Assets: <strong>{report.asset_count}</strong></span>
      <span>Rules: <strong>{report.rule_count}</strong></span>
      <span>Duration: <strong>{report.duration_ms:.1f} ms</strong></span>
      <span>Version: <strong>{self._esc(report.tool_version)}</strong></span>
    </div>
    {summary_html}
    <h2>Results by Asset</h2>
    {assets_html}
    <footer>
      Generated by Asset Validation Framework v{self._esc(report.tool_version)}
      &nbsp;·&nbsp; {self._esc(now)}
    </footer>
  </div>
</body>
</html>"""
        return re.sub(r"\n{2,}", "\n", html)

    def _renderSummary(self, report: ValidationReport) -> str:
        """Build the summary box HTML fragment.

        Args:
            report: The ValidationReport to summarise.

        Returns:
            An HTML string containing the summary ``<div>`` block.

        """
        p  = report.passed
        f  = report.failed
        e  = report.errors
        wn = report.warnings
        s  = report.skipped
        t  = report.total

        status_class = "status-fail" if report.hasErrors() else "status-pass"
        status_text  = "❌ FAILED" if report.hasErrors() else "✅ PASSED"

        header_row = (
            "<tr><th>Total</th><th>Passed</th><th>Failed</th>"
            "<th>Errors</th><th>Warnings</th><th>Skipped</th></tr>"
        )
        return f"""
    <div class="summary-box {status_class}">
      <div class="status-badge">{status_text}</div>
      <table class="summary-table">
        {header_row}
        <tr>
          <td>{t}</td>
          <td class="cell-pass">{p}</td>
          <td class="{'cell-fail' if f else ''}">{f}</td>
          <td class="{'cell-error' if e else ''}">{e}</td>
          <td class="{'cell-warn' if wn else ''}">{wn}</td>
          <td class="cell-skip">{s}</td>
        </tr>
      </table>
    </div>"""

    def _renderAssets(self, report: ValidationReport) -> str:
        """Build the collapsible per-asset section HTML.

        Args:
            report: The ValidationReport to render.

        Returns:
            An HTML string containing one ``<details>`` block per asset.

        """
        if not report.results:
            return "<p><em>No results to display.</em></p>"

        parts: list[str] = []

        for asset_path, results in _groupByAsset(report.results).items():
            failures  = [r for r in results if not r.passed and not r.skipped]
            has_error = any(r.severity is Severity.ERROR for r in failures)
            label_cls = "asset-error" if has_error else ("asset-warn" if failures else "asset-pass")
            icon      = "❌" if has_error else ("⚠️" if failures else "✅")
            display = (
                results
                if self.show_passing
                else [r for r in results if not r.passed or r.skipped]
            )
            rows      = "".join(self._renderRow(r) for r in display)

            if not rows:
                rows = '<tr><td colspan="5" class="no-issues">All checks passed.</td></tr>'

            parts.append(f"""
    <details class="asset-block {label_cls}">
      <summary>{icon} <code>{self._esc(asset_path)}</code>
        <span class="asset-counts">
          {len([r for r in results if r.passed and not r.skipped])} pass &nbsp;
          {len(failures)} fail &nbsp;
          {len([r for r in results if r.skipped])} skip
        </span>
      </summary>
      <table class="results-table">
        <thead><tr>
          <th>Severity</th><th>Rule</th><th>Status</th>
          <th>Message</th><th>Fix Hint</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </details>""")
        return "\n".join(parts)

    def _renderRow(self, r: ValidationResult) -> str:
        """Render a single result as an HTML ``<tr>`` row.

        Args:
            r: The ValidationResult to render.

        Returns:
            An HTML string for a single ``<tr>`` element.

        """
        if r.skipped:
            badge   = '<span class="badge sev-skip">SKIP</span>'
            row_cls = "row-skip"
        elif r.passed:
            badge   = '<span class="badge sev-pass">PASS</span>'
            row_cls = "row-pass"
        else:
            sev_name, sev_cls = self._SEV_BADGE.get(r.severity.value, ("?", "sev-info"))
            badge   = f'<span class="badge {sev_cls}">{sev_name}</span>'
            row_cls = f"row-{sev_cls.split('-')[1]}"

        status_icon = "↷" if r.skipped else ("✓" if r.passed else "✗")
        fix_cell    = self._esc(r.fix_hint) if r.fix_hint else ""

        if fix_cell:
            fix_cell = f'<span class="fix-hint">💡 {fix_cell}</span>'

        return f"""<tr class="{row_cls}">
          <td>{badge}</td>
          <td><code>{self._esc(r.rule_name)}</code></td>
          <td class="status-icon">{status_icon}</td>
          <td>{self._esc(r.message)}</td>
          <td>{fix_cell}</td>
        </tr>"""

    @staticmethod
    def _esc(text: str) -> str:
        """HTML-escape a string, coercing non-strings first."""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    @staticmethod
    def _css() -> str:
        """Return the inline CSS stylesheet string for the HTML report."""
        return """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           background: #0d1117; color: #c9d1d9; font-size: 14px; line-height: 1.5; }
    .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
    h1 { font-size: 1.5rem; margin-bottom: 4px; color: #58a6ff; }
    h2 { font-size: 1rem; margin: 24px 0 12px; color: #8b949e;
         text-transform: uppercase; letter-spacing: .05em; }
    .meta { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;
            font-size: 0.85rem; color: #8b949e; }
    .meta span { background: #161b22; border: 1px solid #30363d; border-radius: 4px;
                 padding: 4px 10px; }
    /* Summary box */
    .summary-box { background: #161b22; border: 2px solid #30363d; border-radius: 8px;
                   padding: 16px; margin-bottom: 24px; }
    .summary-box.status-fail { border-color: #f85149; }
    .summary-box.status-pass { border-color: #3fb950; }
    .status-badge { font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; }
    .summary-table { width: 100%; border-collapse: collapse; }
    .summary-table th, .summary-table td { padding: 6px 12px; text-align: center;
                                            border: 1px solid #30363d; }
    .summary-table th { background: #21262d; font-weight: 600; color: #8b949e; }
    .cell-pass { color: #3fb950; font-weight: bold; }
    .cell-fail, .cell-error { color: #f85149; font-weight: bold; }
    .cell-warn { color: #d29922; font-weight: bold; }
    .cell-skip { color: #8b949e; }
    /* Asset blocks */
    .asset-block { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
                   margin-bottom: 8px; overflow: hidden; }
    .asset-block summary { padding: 10px 14px; cursor: pointer; font-weight: 500;
                            list-style: none; display: flex; align-items: baseline; gap: 8px; }
    .asset-block summary::-webkit-details-marker { display: none; }
    .asset-block[open] > summary { border-bottom: 1px solid #30363d; }
    .asset-block.asset-error > summary { border-left: 4px solid #f85149; }
    .asset-block.asset-warn  > summary { border-left: 4px solid #d29922; }
    .asset-block.asset-pass  > summary { border-left: 4px solid #3fb950; }
    .asset-block code { font-family: "Menlo", "Consolas", monospace;
                        font-size: 13px; color: #79c0ff; }
    .asset-counts { margin-left: auto; font-size: 0.8rem; color: #8b949e; }
    /* Results table */
    .results-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .results-table thead tr { background: #21262d; }
    .results-table th { padding: 6px 10px; text-align: left; border-bottom: 2px solid #30363d;
                        font-weight: 600; color: #8b949e; }
    .results-table td { padding: 6px 10px; border-bottom: 1px solid #21262d; vertical-align: top; }
    .results-table code { font-family: "Menlo", "Consolas", monospace; font-size: 0.82rem; }
    .no-issues { color: #3fb950; font-style: italic; padding: 8px 10px; }
    .row-pass   { }
    .row-error  { background: rgba(248,81,73,0.06); }
    .row-warn   { background: rgba(210,153,34,0.06); }
    .row-info   { background: rgba(88,166,255,0.06); }
    .row-skip   { color: #8b949e; }
    .status-icon { text-align: center; font-size: 1rem; }
    /* Badges */
    .badge { display: inline-block; padding: 2px 6px; border-radius: 3px;
             font-size: 0.75rem; font-weight: bold; letter-spacing: 0.03em; }
    .sev-error { background: #3d1a1a; color: #f85149; border: 1px solid #f85149; }
    .sev-warn  { background: #3d2e0a; color: #d29922; border: 1px solid #d29922; }
    .sev-info  { background: #0d2a4a; color: #58a6ff; border: 1px solid #58a6ff; }
    .sev-pass  { background: #0a2a1a; color: #3fb950; border: 1px solid #3fb950; }
    .sev-skip  { background: #1c1c1c; color: #8b949e; border: 1px solid #30363d; }
    /* Fix hint */
    .fix-hint { color: #8b949e; font-style: italic; font-size: 0.82rem; }
    /* Footer */
    footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #30363d;
             font-size: 0.8rem; color: #8b949e; text-align: center; }"""
