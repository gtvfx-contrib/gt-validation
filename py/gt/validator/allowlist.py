"""AllowlistManager: explicit per-asset rule exceptions with expiry.

The allowlist lets Technical Leads grant time-limited exceptions to specific
assets that would otherwise fail a validation rule. Each entry records the
reason, the author who approved it, and an optional expiry date.

Config key: ``allowlist`` (list of dicts in the JSON config).

JSON format::

    {
        "allowlist": [
            {
                "rule": "material_blend_mode",
                "asset": "/Game/Cinematics/Hero/M_HeroSkin",
                "reason": "Approved by TA lead for cinematic use",
                "author": "j.smith",
                "expires": "2026-12-31"
            }
        ]
    }

"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)


class AllowlistEntry:
    """One allowlist entry loaded from config.

    Attributes:
        rule: Name of the validation rule this exception applies to.
        asset: Content-browser or filesystem path of the exempted asset.
        reason: Human-readable justification for the exception.
        author: Username or identifier of the approver.
        created_at: Timestamp when the entry was added.
        expires_at: Optional timestamp when the entry expires.

    """

    def __init__(
        self,
        rule: str,
        asset: str,
        reason: str = "",
        author: str = "",
        created_at: str | None = None,
        expires_at: str | None = None,
    ) -> None:
        """Initialise an allowlist entry.

        Args:
            rule: Name of the validation rule this exception applies to.
            asset: Content-browser or filesystem path of the exempted asset.
            reason: Human-readable justification for the exception.
            author: Username or identifier of the approver.
            created_at: Timestamp when the entry was added.
            expires_at: Optional expiry date string in ``YYYY-MM-DD`` format.
                Entries past this date are treated as expired.

        """
        self.rule = rule
        self.asset = asset
        self.reason = reason
        self.author = author
        self.created_at = created_at or datetime.now().isoformat()
        self.expires_at = expires_at

    def isExpired(self) -> bool:
        """Return True if this entry has passed its expiry date."""
        if not self.expires_at:
            return False

        try:
            expire_date = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expire_date
        except ValueError:
            # Invalid date format, treat as expired
            logger.warning(
                "[Allowlist] Invalid expiry date '%s' for rule=%s asset=%s — treating as expired.",
                self.expires_at,
                self.rule,
                self.asset,
            )
            return True

    def __repr__(self) -> str:
        """Return a string representation of the allowlist entry."""
        return (
            f"AllowlistEntry(rule={self.rule!r}, asset={self.asset!r}, expires={self.expires_at!r})"
        )


class AllowlistManager:
    """Manages a collection of allowlist entries loaded from :class:`Config`.

    Provides rule-plus-asset lookup so that rules can honour approved
    exceptions before raising failures.

    Example::

        from validator.allowlist import AllowlistManager

        manager = AllowlistManager(config)
        if manager.isAllowed("material_blend_mode", "/Game/M_HeroSkin"):
            return self._makeResult(asset_path, passed=True, message="Allowlisted.")

    """

    def __init__(self, config: Config) -> None:
        """Initialise the manager and load entries from config.

        Args:
            config: Loaded :class:`~validator.config.Config` instance.
                The ``allowlist`` key must contain a list of entry dicts.

        """
        self.entries: list[AllowlistEntry] = []
        self.config = config

        # Load allowlist from config
        raw_entries: list[dict] = config.get("allowlist", [])
        for raw in raw_entries:
            if not isinstance(raw, dict):
                logger.warning("[Allowlist] Skipping invalid entry (not a dict): %r", raw)
                continue
            try:
                entry = AllowlistEntry(
                    rule=raw.get("rule", ""),
                    asset=raw.get("asset", ""),
                    reason=raw.get("reason", ""),
                    author=raw.get("author", ""),
                    created_at=raw.get("created_at"),
                    expires_at=raw.get("expires"),
                )
                if entry.isExpired():
                    logger.warning(
                        "[Allowlist] Expired entry skipped: rule=%s asset=%s expired=%s",
                        entry.rule,
                        entry.asset,
                        entry.expires_at,
                    )
                else:
                    self.entries.append(entry)
            except Exception as e:
                logger.warning("[Allowlist] Failed to load entry: %s", e)
                continue

        logger.debug("[Allowlist] Loaded %d active entries.", len(self.entries))

    def isAllowed(self, rule_name: str, asset_path: str) -> bool:
        """Return ``True`` if the combination matches an active allowlist entry.

        Matching is exact on both rule name and asset path.

        Args:
            rule_name: Name of the validation rule.
            asset_path: Content-browser or filesystem path of the asset.

        Returns:
            ``True`` when an active (non-expired) entry matches, ``False``
            otherwise.

        """
        for entry in self.entries:
            if entry.rule == rule_name and entry.asset == asset_path:
                return not entry.isExpired()
        return False

    def getEntry(self, rule_name: str, asset_path: str) -> AllowlistEntry | None:
        """Return the matching :class:`AllowlistEntry`, or ``None``.

        Args:
            rule_name: Name of the validation rule.
            asset_path: Content-browser or filesystem path of the asset.

        Returns:
            The matching entry, or ``None`` if no active entry is found.

        """
        for entry in self.entries:
            if entry.rule == rule_name and entry.asset == asset_path:
                return entry if not entry.isExpired() else None
        return None

    def __len__(self) -> int:
        """Return the number of active allowlist entries."""
        return len(self.entries)

    def __repr__(self) -> str:
        """Return a string representation of the allowlist manager."""
        return f"AllowlistManager(entries={len(self.entries)})"
