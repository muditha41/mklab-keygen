"""App lock / restriction: track validity, grace period, and on_invalid callback."""

import time
from typing import Callable

from app_protection.exceptions import LicenseInvalidError


class Enforcer:
    """
    Tracks license validity. On validation failure, starts grace period; when grace
    period expires, calls on_invalid once and marks app as restricted.
    """

    def __init__(
        self,
        on_invalid: Callable[[], None] | None = None,
        grace_period_hours: int = 48,
    ):
        self.on_invalid = on_invalid
        self.grace_period_seconds = grace_period_hours * 3600
        self._valid: bool | None = None  # None = not yet determined
        self._failure_time: float | None = None  # when we first saw invalid/unreachable
        self._invalid_called = False

    @property
    def is_valid(self) -> bool | None:
        """True if license valid, False if invalid/restricted, None if unknown (e.g. not yet checked)."""
        return self._valid

    @property
    def is_restricted(self) -> bool:
        """True if we have determined the app should be restricted (grace period over, on_invalid called)."""
        if self._valid is True:
            return False
        if self._invalid_called:
            return True
        if self._failure_time is None:
            return False
        return time.monotonic() - self._failure_time >= self.grace_period_seconds

    def record_success(self) -> None:
        """Call after a successful validation."""
        self._valid = True
        self._failure_time = None

    def record_failure(self) -> None:
        """
        Call after validation failed (invalid key, expired, or network error).
        Starts grace period; when grace period expires, calls on_invalid once.
        """
        if self._failure_time is None:
            self._failure_time = time.monotonic()
        self._valid = False
        if self._invalid_called:
            return
        if time.monotonic() - self._failure_time >= self.grace_period_seconds:
            self._invalid_called = True
            if self.on_invalid:
                self.on_invalid()

    def check_grace_period(self) -> None:
        """
        Call periodically (e.g. from scheduler or main loop) to see if grace period
        has expired and trigger on_invalid if so.
        """
        if self._valid is True or self._failure_time is None or self._invalid_called:
            return
        if time.monotonic() - self._failure_time >= self.grace_period_seconds:
            self._invalid_called = True
            if self.on_invalid:
                self.on_invalid()

    def require_valid(self) -> None:
        """
        Raise if the license is not valid and grace period has expired (app restricted).
        Call at app startup or before sensitive operations.
        """
        self.check_grace_period()
        if self._invalid_called:
            raise LicenseInvalidError("Application access is restricted (invalid or expired license).")
        if self._valid is False and self.is_restricted:
            raise LicenseInvalidError("Application access is restricted.")
        if self._valid is None:
            raise LicenseInvalidError("License has not been validated yet.")
