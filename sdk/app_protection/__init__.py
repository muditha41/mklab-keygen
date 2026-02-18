"""
SWAPS Client SDK — protect your app with license validation.

Usage (3 lines):
    from app_protection import protect

    protect(
        license_key="LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C",
        server_url="https://protection.yourserver.com",
        signing_secret="your-hmac-secret",  # same as server LICENSE_HMAC_SECRET
        on_invalid=lambda: disable_app_features(),
    )
"""

from __future__ import annotations

from typing import Callable

from app_protection.client import validate, validate_with_retry
from app_protection.config import ProtectionConfig
from app_protection.enforcer import Enforcer
from app_protection.exceptions import (
    LicenseError,
    LicenseExpiredError,
    LicenseInvalidError,
    ValidationFailedError,
)
from app_protection.scheduler import schedule_monthly_validation, shutdown_scheduler
from app_protection.storage import get_stored_key, set_stored_key

__version__ = "0.1.0"

__all__ = [
    "protect",
    "validate_now",
    "require_valid",
    "LicenseError",
    "LicenseExpiredError",
    "LicenseInvalidError",
    "ValidationFailedError",
    "ProtectionConfig",
    "get_stored_key",
    "set_stored_key",
]


def require_valid() -> None:
    """
    Raise LicenseInvalidError if the license is not valid and grace period has ended.
    Call at app startup (after protect()) or before sensitive operations to block access.
    """
    if _enforcer is None:
        raise LicenseInvalidError("License has not been validated. Call protect() first.")
    _enforcer.require_valid()

# Global state for scheduled job
_config: ProtectionConfig | None = None
_enforcer: Enforcer | None = None


def _run_validation_and_update_enforcer() -> None:
    """Run validation once and update the global enforcer. Used at startup and by scheduler."""
    global _config, _enforcer
    if not _config or not _enforcer:
        return
    backoff_sec = _config.retry_backoff_minutes * 60
    try:
        data = validate_with_retry(
            _config.server_url,
            _config.license_key,
            _config.app_id,
            _config.signing_secret,
            retry_count=_config.retry_count,
            retry_backoff_seconds=backoff_sec,
        )
        if data.get("valid") is True:
            _enforcer.record_success()
        else:
            _enforcer.record_failure()
    except Exception:  # noqa: BLE001
        _enforcer.record_failure()


def protect(
    license_key: str,
    server_url: str,
    signing_secret: str,
    *,
    app_id: str = "default",
    on_invalid: Callable[[], None] | None = None,
    grace_period_hours: int = 48,
    retry_count: int = 3,
    retry_backoff_minutes: int = 5,
    store_key: bool = True,
) -> None:
    """
    Call at app startup. Validates the license once, then schedules monthly validation
    on the 26th at 00:00 local time. If validation fails (or server unreachable), starts
    a grace period; after grace_period_hours, calls on_invalid() and restricts the app.

    :param license_key: The license key (e.g. LIC-MYAPP-...).
    :param server_url: Base URL of the protection server (e.g. https://protection.example.com).
    :param signing_secret: Secret for signing validation requests (must match server LICENSE_HMAC_SECRET).
    :param app_id: Application identifier sent to the server (default "default").
    :param on_invalid: Callback when license is invalid/expired and grace period has ended.
    :param grace_period_hours: Hours to allow operation when server unreachable before restricting (default 48).
    :param store_key: If True, store the key in keyring/env for validate_now() (default True).
    """
    global _config, _enforcer
    _config = ProtectionConfig(
        server_url=server_url.rstrip("/"),
        license_key=license_key,
        signing_secret=signing_secret,
        app_id=app_id,
        on_invalid=on_invalid,
        grace_period_hours=grace_period_hours,
        retry_count=retry_count,
        retry_backoff_minutes=retry_backoff_minutes,
    )
    _enforcer = Enforcer(
        on_invalid=on_invalid,
        grace_period_hours=grace_period_hours,
    )
    if store_key:
        set_stored_key(license_key, app_id)
    _run_validation_and_update_enforcer()
    schedule_monthly_validation(_run_validation_and_update_enforcer)


def validate_now() -> dict | None:
    """
    Run validation once using the config from a previous protect() call, or from
    environment (SWAPS_SERVER_URL, SWAPS_LICENSE_KEY, SWAPS_SIGNING_SECRET). Updates the
    global enforcer if set. Returns the server response dict or None if no config.
    """
    global _config, _enforcer
    if _config is None:
        _config = ProtectionConfig.from_env()
        if _config is None:
            return None
        if _enforcer is None:
            _enforcer = Enforcer(
                on_invalid=_config.on_invalid,
                grace_period_hours=_config.grace_period_hours,
            )
    backoff_sec = _config.retry_backoff_minutes * 60
    try:
        data = validate_with_retry(
            _config.server_url,
            _config.license_key,
            _config.app_id,
            _config.signing_secret,
            retry_count=_config.retry_count,
            retry_backoff_seconds=backoff_sec,
        )
        if _enforcer:
            if data.get("valid") is True:
                _enforcer.record_success()
            else:
                _enforcer.record_failure()
        return data
    except Exception:  # noqa: BLE001
        if _enforcer:
            _enforcer.record_failure()
        raise
